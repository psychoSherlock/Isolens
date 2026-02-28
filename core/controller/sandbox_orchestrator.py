"""Sandbox Orchestrator — HTTP + Shared Folder workflow for IsoLens.

Communicates with the IsoLens agent running inside the VM over HTTP and
uses the VirtualBox shared folder for file transfer.

Workflow
───────
  1. Copy sample to the host-side shared folder (SandboxShare/)
  2. POST /api/execute on the agent → agent copies from share, runs sample,
     waits timeout, collects artifacts, packages zip to share
  3. Poll GET /api/status until the agent reports idle
  4. Pick up the results zip from SandboxShare/
  5. Unpack into core/storage/reports/<analysis_id>/
  6. Return structured AnalysisResult

The agent handles everything inside the VM (execution, Sysmon clear,
artifact collection, packaging).  This orchestrator is the host-side
coordinator.
"""

from __future__ import annotations

import datetime
import glob
import json
import logging
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger("isolens.orchestrator")

# ─── Default paths ────────────────────────────────────────────────────────

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
DEFAULT_SAMPLES_DIR = os.path.join(_PROJECT_ROOT, "core", "storage", "samples")
DEFAULT_REPORTS_DIR = os.path.join(_PROJECT_ROOT, "core", "storage", "reports")
DEFAULT_LOGS_DIR = os.path.join(_PROJECT_ROOT, "core", "storage", "logs")
DEFAULT_SHARE_DIR = os.path.join(_PROJECT_ROOT, "SandboxShare")


# ─── Data classes ─────────────────────────────────────────────────────────

@dataclass
class AgentConfig:
    """Connection details for the IsoLens agent HTTP API."""

    host: str = "192.168.56.105"
    port: int = 9090
    timeout: int = 15  # HTTP request timeout (seconds)
    vm_name: str = "WindowsSandbox"  # VirtualBox VM name for screenshots

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class AnalysisResult:
    """Stores the result of a complete analysis run."""

    analysis_id: str
    sample_name: str
    status: str = "pending"           # pending | running | complete | failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    timeout: int = 60
    error: Optional[str] = None
    report_dir: Optional[str] = None
    sysmon_events: int = 0
    files_collected: List[str] = field(default_factory=list)
    agent_package: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "sample_name": self.sample_name,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "timeout": self.timeout,
            "error": self.error,
            "report_dir": self.report_dir,
            "sysmon_events": self.sysmon_events,
            "files_collected": self.files_collected,
            "agent_package": self.agent_package,
        }


# ─── Orchestrator ─────────────────────────────────────────────────────────

class SandboxOrchestrator:
    """Drives the end-to-end analysis workflow via the in-VM agent.

    Parameters
    ----------
    agent_config : AgentConfig
        HTTP connection details for the IsoLens agent.
    share_dir : str
        Host-side path to the VirtualBox shared folder (SandboxShare/).
    samples_dir : str
        Host directory where uploaded samples are archived.
    reports_dir : str
        Host directory where unpacked analysis reports live.
    dry_run : bool
        If True, log actions without actually executing them.
    """

    def __init__(
        self,
        agent_config: Optional[AgentConfig] = None,
        share_dir: str = DEFAULT_SHARE_DIR,
        samples_dir: str = DEFAULT_SAMPLES_DIR,
        reports_dir: str = DEFAULT_REPORTS_DIR,
        dry_run: bool = False,
    ) -> None:
        self.agent = agent_config or AgentConfig()
        self.share_dir = share_dir
        self.samples_dir = samples_dir
        self.reports_dir = reports_dir
        self.dry_run = dry_run

        # Ensure host directories exist
        for d in (self.samples_dir, self.reports_dir, self.share_dir):
            os.makedirs(d, exist_ok=True)

        # Track current analysis
        self._current: Optional[AnalysisResult] = None

    # ─── Public API ───────────────────────────────────────────────────

    @property
    def current_analysis(self) -> Optional[AnalysisResult]:
        return self._current

    def run_analysis(
        self,
        sample_path: str,
        timeout: int = 60,
        screenshot_interval: int = 5,
    ) -> AnalysisResult:
        """Execute the full analysis workflow.

        Parameters
        ----------
        sample_path : str
            Absolute path to the sample file on the host.
        timeout : int
            Seconds the agent waits after execution for behaviour collection.

        Returns
        -------
        AnalysisResult
            The completed analysis result with paths to collected data.
        """
        sample_name = os.path.basename(sample_path)
        analysis_id = (
            datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            + "_"
            + uuid.uuid4().hex[:8]
        )

        result = AnalysisResult(
            analysis_id=analysis_id,
            sample_name=sample_name,
            timeout=timeout,
            started_at=datetime.datetime.utcnow().isoformat() + "Z",
        )
        self._current = result

        # Create analysis report directory
        report_dir = os.path.join(self.reports_dir, analysis_id)
        os.makedirs(report_dir, exist_ok=True)
        result.report_dir = report_dir

        try:
            result.status = "running"

            # Step 1: Archive sample locally
            stored = os.path.join(
                self.samples_dir, f"{analysis_id}_{sample_name}"
            )
            shutil.copy2(sample_path, stored)
            log.info("[1/5] Sample archived: %s", stored)

            # Step 2: Copy sample to shared folder so the agent can see it
            share_dest = os.path.join(self.share_dir, sample_name)
            shutil.copy2(sample_path, share_dest)
            log.info("[2/5] Sample placed in shared folder: %s", share_dest)

            # Step 3: Tell the agent to execute
            log.info(
                "[3/5] Requesting agent to execute '%s' (timeout=%ds)...",
                sample_name, timeout,
            )
            resp = self._agent_post("/api/execute", {
                "filename": sample_name,
                "timeout": timeout,
                "screenshot_interval": screenshot_interval,
            })
            if resp.get("status") == "error":
                raise RuntimeError(
                    f"Agent rejected execute: {resp.get('error')}"
                )

            # Step 4: Poll agent status until idle or error,
            #         taking VBoxManage screenshots in parallel
            log.info("[4/5] Polling agent status...")

            screenshot_dir = os.path.join(report_dir, "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            stop_screenshots = threading.Event()
            screenshot_thread = threading.Thread(
                target=self._screenshot_loop,
                args=(screenshot_dir, screenshot_interval, stop_screenshots),
                daemon=True,
            )
            screenshot_thread.start()

            self._poll_agent_until_done(
                poll_interval=5,
                # Agent takes ~timeout + collection time — generous max.
                max_wait=timeout + 300,
            )
            log.info("[4/5] Agent finished execution + collection")

            # Stop screenshot capture
            stop_screenshots.set()
            screenshot_thread.join(timeout=15)
            screenshot_files = sorted(
                glob.glob(os.path.join(screenshot_dir, "*.png"))
            )

            # Step 5: Pick up results from shared folder
            log.info("[5/5] Retrieving results from shared folder...")
            collected = self._retrieve_results(sample_name, report_dir)
            result.files_collected = collected
            result.agent_package = self._find_result_zip(sample_name)
            result.sysmon_events = self._count_sysmon_events(report_dir)

            # Add host-captured screenshots to the file list
            for sf in screenshot_files:
                rel = os.path.relpath(sf, report_dir)
                if rel not in result.files_collected:
                    result.files_collected.append(rel)
            log.info(
                "Host screenshots: %d captured",
                len(screenshot_files),
            )

            result.status = "complete"
            result.completed_at = (
                datetime.datetime.utcnow().isoformat() + "Z"
            )
            log.info(
                "Analysis complete: %s (%d files collected)",
                analysis_id, len(collected),
            )

        except Exception as exc:
            result.status = "failed"
            result.error = str(exc)
            result.completed_at = (
                datetime.datetime.utcnow().isoformat() + "Z"
            )
            log.error("Analysis failed: %s", exc)

        # Write result manifest
        manifest_path = os.path.join(report_dir, "analysis_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(result.to_dict(), fh, indent=2)

        self._current = result
        return result

    def check_vm_ready(self) -> Dict[str, Any]:
        """Verify the agent is reachable and tools are available."""
        checks: Dict[str, Any] = {}

        # Agent HTTP connectivity
        try:
            resp = self._agent_get("/api/status")
            checks["agent_reachable"] = resp.get("status") == "ok"
            data = resp.get("data", {})
            checks["agent_status"] = data.get("status", "unknown")
            checks["agent_version"] = data.get("agent_version", "unknown")

            # Collector availability
            collectors = data.get("collectors", [])
            for c in collectors:
                checks[f"collector_{c['name']}"] = c.get("available", False)

        except Exception as exc:
            checks["agent_reachable"] = False
            checks["agent_error"] = str(exc)

        # Shared folder accessible on host
        checks["share_folder"] = os.path.isdir(self.share_dir)

        checks["ready"] = (
            checks.get("agent_reachable", False)
            and checks.get("share_folder", False)
        )
        return checks

    def cleanup_agent(self) -> Dict[str, Any]:
        """Ask the agent to clean up all artifacts."""
        return self._agent_post("/api/cleanup", {})

    def get_agent_status(self) -> Dict[str, Any]:
        """Get the agent's current status."""
        return self._agent_get("/api/status")

    def get_agent_collectors(self) -> Dict[str, Any]:
        """Get the agent's collector list."""
        return self._agent_get("/api/collectors")

    def get_agent_artifacts(self) -> Dict[str, Any]:
        """Get the agent's collected artifact list."""
        return self._agent_get("/api/artifacts")

    # ─── Internal helpers ─────────────────────────────────────────────

    def _screenshot_loop(
        self,
        screenshot_dir: str,
        interval: int,
        stop_event: threading.Event,
    ) -> None:
        """Background thread: capture VBoxManage screenshots at *interval*."""
        idx = 0
        while not stop_event.is_set():
            self._take_screenshot(screenshot_dir, idx)
            idx += 1
            stop_event.wait(timeout=interval)

    def _take_screenshot(self, screenshot_dir: str, idx: int) -> None:
        """Take a single VM screenshot using VBoxManage."""
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{idx:03d}_{ts}.png"
        filepath = os.path.join(screenshot_dir, filename)
        try:
            result = subprocess.run(
                [
                    "VBoxManage", "controlvm",
                    self.agent.vm_name,
                    "screenshotpng", filepath,
                ],
                capture_output=True, timeout=15,
            )
            if result.returncode == 0:
                log.info("Screenshot %d → %s", idx, filename)
            else:
                log.warning(
                    "VBoxManage screenshot %d failed (rc=%d)",
                    idx, result.returncode,
                )
        except Exception as exc:
            log.warning("Screenshot %d error: %s", idx, exc)

    def _poll_agent_until_done(
        self,
        poll_interval: int = 5,
        max_wait: int = 360,
    ) -> None:
        """Poll ``/api/status`` until the agent is no longer executing."""
        elapsed = 0
        while elapsed < max_wait:
            try:
                resp = self._agent_get("/api/status")
                data = resp.get("data", {})
                status = data.get("status", "unknown")
                log.info(
                    "  Agent status: %s (elapsed=%ds)", status, elapsed
                )

                if status in ("idle", "error"):
                    if status == "error":
                        last_err = data.get("last_error", "unknown")
                        log.warning("Agent reported error: %s", last_err)
                    return

            except Exception as exc:
                log.warning("  Status poll failed: %s (retrying)", exc)

            time.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(
            f"Agent did not finish within {max_wait}s"
        )

    def _retrieve_results(
        self,
        sample_name: str,
        report_dir: str,
    ) -> List[str]:
        """Find and unpack the result zip from the shared folder."""
        collected: List[str] = []

        zip_file = self._find_result_zip(sample_name)
        if not zip_file:
            log.warning(
                "No result zip found in shared folder for '%s'",
                sample_name,
            )
            return collected

        zip_path = os.path.join(self.share_dir, zip_file)
        log.info("Found result package: %s", zip_file)

        # Unpack into report dir
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(report_dir)
                collected = zf.namelist()
            log.info(
                "Extracted %d files to %s", len(collected), report_dir
            )
        except Exception as exc:
            log.error("Failed to unpack results: %s", exc)

        return collected

    def _find_result_zip(self, sample_name: str) -> Optional[str]:
        """Find the newest results zip matching the sample in the share."""
        base = os.path.splitext(sample_name)[0]
        pattern = os.path.join(self.share_dir, f"results_{base}_*.zip")
        matches = sorted(
            glob.glob(pattern), key=os.path.getmtime, reverse=True
        )
        if matches:
            return os.path.basename(matches[0])
        return None

    def _count_sysmon_events(self, report_dir: str) -> int:
        """Count Sysmon events from collected text file."""
        for root, _dirs, files in os.walk(report_dir):
            for fname in files:
                if fname == "sysmon_events.txt":
                    fpath = os.path.join(root, fname)
                    count = 0
                    with open(
                        fpath, "r", encoding="utf-8", errors="replace"
                    ) as fh:
                        for line in fh:
                            if "Event ID:" in line:
                                count += 1
                    return count
        return 0

    # ─── HTTP helpers (stdlib only) ───────────────────────────────────

    def _agent_get(self, path: str) -> Dict[str, Any]:
        """HTTP GET to the agent, return parsed JSON."""
        url = self.agent.base_url + path
        if self.dry_run:
            log.info("[DRY RUN] GET %s", url)
            return {"status": "ok", "data": {}}
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(
                req, timeout=self.agent.timeout
            ) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise ConnectionError(
                f"Agent unreachable at {url}: {exc}"
            ) from exc

    def _agent_post(
        self, path: str, body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """HTTP POST JSON to the agent, return parsed JSON."""
        url = self.agent.base_url + path
        if self.dry_run:
            log.info("[DRY RUN] POST %s %s", url, json.dumps(body))
            return {"status": "ok", "data": {}}
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(
                req, timeout=self.agent.timeout
            ) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise ConnectionError(
                f"Agent unreachable at {url}: {exc}"
            ) from exc
