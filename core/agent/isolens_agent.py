"""IsoLens Guest Agent — Sandbox VM Service.

A single-file HTTP agent that runs inside the isolated analysis VM.
Receives commands from the host controller, manages sample execution,
collects behavioral artifacts, and exports results via the shared folder.

Uses only Python standard library — no pip dependencies required.
Designed for Windows 7+ (compatible with Python 3.8+).

API Endpoints
─────────────
  GET  /api/status      Health check and current agent state
  GET  /api/collectors  List available artifact collectors
  GET  /api/artifacts   List collected artifact files
  POST /api/execute     Execute a sample  {"filename": "sample.exe", "timeout": 60}
  POST /api/collect     Run all collectors without executing a sample
  POST /api/cleanup     Remove all collected artifacts
  POST /api/shutdown    Graceful agent shutdown

Communication
─────────────
  HTTP API runs on the VM's host-only network adapter for commands.
  VirtualBox Shared Folder is used for file transfers:
    - Host places samples into SandboxShare/
    - Agent copies sample locally, executes, collects artifacts
    - Agent packages results as a .zip and copies to SandboxShare/

Usage
─────
  python isolens_agent.py [options]

  --host HOST    Bind address           (default: 0.0.0.0)
  --port PORT    Bind port              (default: 9090)
  --share PATH   Shared folder path     (default: \\\\VBOXSVR\\SandboxShare)
  --workdir DIR  Working directory      (default: C:\\IsoLens)
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════════════════════

LOG_FMT = "[%(asctime)s] %(levelname)-7s %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
log = logging.getLogger("isolens-agent")

AGENT_VERSION = "1.1.0"


# ═══════════════════════════════════════════════════════════════════════════
# Agent State
# ═══════════════════════════════════════════════════════════════════════════

class AgentState:
    """Thread-safe status tracker for the agent lifecycle."""

    IDLE = "idle"
    EXECUTING = "executing"
    COLLECTING = "collecting"
    ERROR = "error"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status: str = self.IDLE
        self._current_sample: Optional[str] = None
        self._last_error: Optional[str] = None
        self._started_at: str = datetime.datetime.utcnow().isoformat() + "Z"
        self._execution_count: int = 0

    # -- read / write helpers --

    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    @status.setter
    def status(self, value: str) -> None:
        with self._lock:
            self._status = value

    def set_executing(self, sample: str) -> None:
        with self._lock:
            self._status = self.EXECUTING
            self._current_sample = sample

    def set_collecting(self) -> None:
        with self._lock:
            self._status = self.COLLECTING

    def set_error(self, error: str) -> None:
        with self._lock:
            self._status = self.ERROR
            self._last_error = error

    def set_idle(self) -> None:
        with self._lock:
            self._status = self.IDLE
            self._current_sample = None
            self._execution_count += 1

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self._status,
                "current_sample": self._current_sample,
                "last_error": self._last_error,
                "started_at": self._started_at,
                "execution_count": self._execution_count,
            }


# ═══════════════════════════════════════════════════════════════════════════
# Artifact Collectors
# ═══════════════════════════════════════════════════════════════════════════
#
# Each collector gathers a specific kind of behavioral data.
# Collectors report their availability at runtime so the agent works
# gracefully even if some tools haven't been installed yet.
# ═══════════════════════════════════════════════════════════════════════════

class BaseCollector:
    """Abstract base for artifact collectors."""

    name: str = "base"

    def __init__(self, workdir: str) -> None:
        self.workdir = workdir
        self.output_dir = os.path.join(workdir, "artifacts", self.name)
        os.makedirs(self.output_dir, exist_ok=True)

    def is_available(self) -> bool:
        """Return True if the underlying tool is installed/accessible."""
        return False

    def collect(self) -> Dict[str, Any]:
        """Run collection and return metadata about what was collected."""
        return {
            "collector": self.name,
            "status": "not_implemented",
            "files": [],
        }


class SysmonCollector(BaseCollector):
    """Export Sysmon event logs via ``wevtutil``.

    Sysmon must be installed and running inside the VM.
    Logs are exported as XML from the Windows Event Log channel
    ``Microsoft-Windows-Sysmon/Operational``.
    """

    name = "sysmon"

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["wevtutil", "gl", "Microsoft-Windows-Sysmon/Operational"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    def collect(self) -> Dict[str, Any]:
        if not self.is_available():
            log.warning("Sysmon not available — skipping")
            return {"collector": self.name, "status": "unavailable", "files": []}

        output_file = os.path.join(self.output_dir, "sysmon_events.xml")
        try:
            result = subprocess.run(
                [
                    "wevtutil", "qe",
                    "Microsoft-Windows-Sysmon/Operational",
                    "/f:xml",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                with open(output_file, "w", encoding="utf-8") as fh:
                    fh.write("<Events>\n")
                    fh.write(result.stdout)
                    fh.write("\n</Events>\n")
                log.info("Sysmon events → %s", output_file)
                return {
                    "collector": self.name,
                    "status": "ok",
                    "files": [output_file],
                }
            log.error("wevtutil failed: %s", result.stderr.strip())
            return {
                "collector": self.name,
                "status": "error",
                "error": result.stderr.strip(),
                "files": [],
            }
        except Exception as exc:
            log.error("Sysmon collection failed: %s", exc)
            return {
                "collector": self.name,
                "status": "error",
                "error": str(exc),
                "files": [],
            }


class ProcmonCollector(BaseCollector):
    """Collect Process Monitor CSV logs.

    Expects Procmon (or Procmon64) in one of the standard tool paths.
    When collection is triggered, Procmon is terminated to flush its
    backing file, then the PML log is converted to CSV.
    """

    name = "procmon"

    _SEARCH_PATHS = [
        r"C:\Tools\Procmon64.exe",
        r"C:\Tools\Procmon.exe",
        r"C:\SysinternalsSuite\Procmon64.exe",
        r"C:\SysinternalsSuite\Procmon.exe",
    ]

    def _find_exe(self) -> Optional[str]:
        for p in self._SEARCH_PATHS:
            if os.path.isfile(p):
                return p
        return None

    def is_available(self) -> bool:
        return self._find_exe() is not None

    def collect(self) -> Dict[str, Any]:
        exe = self._find_exe()
        if not exe:
            log.warning("Procmon not found — skipping")
            return {"collector": self.name, "status": "unavailable", "files": []}

        pml_file = os.path.join(self.output_dir, "procmon.pml")
        csv_file = os.path.join(self.output_dir, "procmon.csv")

        try:
            # Terminate Procmon to flush buffered data
            subprocess.run(
                [exe, "/Terminate"],
                capture_output=True,
                timeout=30,
            )
            time.sleep(2)

            # Convert PML → CSV
            if os.path.isfile(pml_file):
                subprocess.run(
                    [exe, "/OpenLog", pml_file, "/SaveAs", csv_file],
                    capture_output=True,
                    timeout=120,
                )
                if os.path.isfile(csv_file):
                    log.info("Procmon CSV → %s", csv_file)
                    return {
                        "collector": self.name,
                        "status": "ok",
                        "files": [csv_file],
                    }

            log.warning("No Procmon log file at %s", pml_file)
            return {"collector": self.name, "status": "no_data", "files": []}
        except Exception as exc:
            log.error("Procmon collection failed: %s", exc)
            return {
                "collector": self.name,
                "status": "error",
                "error": str(exc),
                "files": [],
            }


class NetworkCollector(BaseCollector):
    """Collect network capture (pcap / tshark JSON).

    Expects ``tshark`` on PATH.  In a real analysis run, tshark would be
    started *before* execution and stopped *after*.  This collector looks
    for an existing capture file and converts it if tshark is available.
    """

    name = "network"

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["tshark", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    def collect(self) -> Dict[str, Any]:
        pcap_file = os.path.join(self.output_dir, "capture.pcap")

        if not os.path.isfile(pcap_file):
            if not self.is_available():
                log.warning("tshark not available — skipping network collection")
                return {
                    "collector": self.name,
                    "status": "unavailable",
                    "files": [],
                }
            log.warning("No capture file at %s", pcap_file)
            return {"collector": self.name, "status": "no_data", "files": []}

        log.info("Network capture → %s", pcap_file)
        return {"collector": self.name, "status": "ok", "files": [pcap_file]}


class FakeNetCollector(BaseCollector):
    """Collect FakeNet-NG logs and PCAP.

    FakeNet-NG is expected to be started *before* sample execution and
    stopped *after*.  This collector terminates the FakeNet process (if
    running), then gathers every log file and PCAP it produced.

    Expected install path: C:\\Tools\\fakenet\\
    FakeNet is launched externally (e.g. by the analysis pre-flight
    script) so that it is ready before the sample runs.
    """

    name = "fakenet"

    _FAKENET_DIR = r"C:\Tools\fakenet"
    _FAKENET_SCRIPT = r"C:\Tools\fakenet\fakenet.py"
    _FAKENET_EXE = r"C:\Tools\fakenet\fakenet.exe"

    def _python_exe(self) -> Optional[str]:
        for p in [r"C:\Tools\python\python.exe", "python", "python3"]:
            try:
                result = subprocess.run(
                    [p, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return p
            except (FileNotFoundError, OSError):
                continue
        return None

    def is_available(self) -> bool:
        return (
            os.path.isfile(self._FAKENET_SCRIPT)
            or os.path.isfile(self._FAKENET_EXE)
        )

    def collect(self) -> Dict[str, Any]:
        if not self.is_available():
            log.warning("FakeNet-NG not found — skipping")
            return {"collector": self.name, "status": "unavailable", "files": []}

        collected: List[str] = []

        # Stop any running FakeNet process to flush its output
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "fakenet.exe"],
                capture_output=True,
                timeout=10,
            )
            subprocess.run(
                ["taskkill", "/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq fakenet*"],
                capture_output=True,
                timeout=10,
            )
            time.sleep(1)
        except Exception:
            pass

        # FakeNet writes logs to its own directory — collect all relevant files
        log_extensions = (".log", ".txt", ".pcap", ".pcapng")
        try:
            for fname in os.listdir(self._FAKENET_DIR):
                if fname.lower().endswith(log_extensions):
                    src = os.path.join(self._FAKENET_DIR, fname)
                    dst = os.path.join(self.output_dir, fname)
                    try:
                        shutil.copy2(src, dst)
                        collected.append(dst)
                        log.info("FakeNet artifact copied: %s", fname)
                    except OSError as exc:
                        log.warning("Could not copy %s: %s", fname, exc)
        except FileNotFoundError:
            log.warning("FakeNet directory not found: %s", self._FAKENET_DIR)
            return {"collector": self.name, "status": "no_data", "files": []}

        if not collected:
            log.info("No FakeNet logs found (was FakeNet started before execution?)")
            return {"collector": self.name, "status": "no_data", "files": []}

        log.info("Collected %d FakeNet artifact(s)", len(collected))
        return {"collector": self.name, "status": "ok", "files": collected}


class ScreenshotCollector(BaseCollector):
    """Gather screenshots taken during sample execution.

    Screenshots are expected to be placed in the output directory by a
    separate capture mechanism (e.g. screenshot_loop.ps1 from setup_vm_tools.ps1).
    This collector simply enumerates image files already present.
    """

    name = "screenshots"

    def is_available(self) -> bool:
        # Always "available" — it just looks for existing image files.
        return True

    def collect(self) -> Dict[str, Any]:
        image_exts = (".png", ".jpg", ".jpeg", ".bmp")
        try:
            files = [
                os.path.join(self.output_dir, f)
                for f in os.listdir(self.output_dir)
                if f.lower().endswith(image_exts)
            ]
        except FileNotFoundError:
            files = []

        if files:
            log.info("Found %d screenshot(s)", len(files))
            return {"collector": self.name, "status": "ok", "files": files}

        log.info("No screenshots found")
        return {"collector": self.name, "status": "no_data", "files": []}


# ═══════════════════════════════════════════════════════════════════════════
# Agent Core
# ═══════════════════════════════════════════════════════════════════════════

class IsoLensAgent:
    """Orchestrates sample execution and artifact collection.

    Parameters
    ----------
    share_path : str
        Path to the VirtualBox shared folder (e.g. ``\\\\VBOXSVR\\SandboxShare``).
    workdir : str
        Local directory for storing samples and collected artifacts.
    """

    def __init__(self, share_path: str, workdir: str) -> None:
        self.share_path = share_path
        self.workdir = workdir
        self.artifacts_dir = os.path.join(workdir, "artifacts")
        self.samples_dir = os.path.join(workdir, "samples")
        self.state = AgentState()

        os.makedirs(self.artifacts_dir, exist_ok=True)
        os.makedirs(self.samples_dir, exist_ok=True)

        # Initialise collectors
        self.collectors: List[BaseCollector] = [
            SysmonCollector(workdir),
            ProcmonCollector(workdir),
            NetworkCollector(workdir),
            FakeNetCollector(workdir),
            ScreenshotCollector(workdir),
        ]

        log.info("Agent initialised  share=%s  workdir=%s", share_path, workdir)
        log.info(
            "Collectors: %s",
            ", ".join(c.name for c in self.collectors),
        )

    # -- introspection --

    def get_collector_info(self) -> List[Dict[str, Any]]:
        """Return name + availability of each collector."""
        return [
            {"name": c.name, "available": c.is_available()}
            for c in self.collectors
        ]

    def list_artifacts(self) -> List[str]:
        """Enumerate all files under the artifacts directory."""
        result: List[str] = []
        if not os.path.isdir(self.artifacts_dir):
            return result
        for root, _dirs, files in os.walk(self.artifacts_dir):
            for fname in files:
                rel = os.path.relpath(
                    os.path.join(root, fname), self.artifacts_dir
                )
                result.append(rel)
        return result

    # -- execution --

    def execute_sample(
        self, filename: str, timeout: int = 60
    ) -> Dict[str, Any]:
        """Execute a sample from the shared folder.

        Workflow:
          1. Copy sample from shared folder to local samples dir
          2. Execute the sample  (STUB — real logic added later)
          3. Wait for the configured timeout
          4. Run all artifact collectors
          5. Package and export results back to the shared folder
        """
        if self.state.status == AgentState.EXECUTING:
            return {"error": "Already executing a sample", "status": "busy"}

        sample_src = os.path.join(self.share_path, filename)
        if not os.path.isfile(sample_src):
            return {
                "error": "Sample not found in shared folder: " + filename,
                "status": "not_found",
            }

        self.state.set_executing(filename)
        log.info("── Execution start: %s (timeout=%ds) ──", filename, timeout)

        try:
            # 1. Copy sample locally
            sample_dst = os.path.join(self.samples_dir, filename)
            shutil.copy2(sample_src, sample_dst)
            log.info("Sample copied → %s", sample_dst)

            # 2. Execute sample (STUB)
            log.info(
                "[STUB] Sample execution not yet implemented. "
                "Would run: %s",
                sample_dst,
            )
            # In the future:
            #   subprocess.Popen(sample_dst, ...)
            # For now simulate a short wait
            stub_wait = min(timeout, 3)
            log.info("[STUB] Simulating %ds wait …", stub_wait)
            time.sleep(stub_wait)

            # 3. Collect artifacts
            self.state.set_collecting()
            collection = self._run_collectors()

            # 4. Package & export
            package = self._package_results(filename, collection)

            self.state.set_idle()
            log.info("── Execution complete: %s ──", filename)

            return {
                "status": "complete",
                "sample": filename,
                "timeout": timeout,
                "collection": collection,
                "package": package,
            }

        except Exception as exc:
            self.state.set_error(str(exc))
            log.error("Execution failed: %s", exc)
            return {"status": "failed", "error": str(exc)}

    # -- collection (without execution) --

    def collect_only(self) -> Dict[str, Any]:
        """Run all collectors without executing any sample."""
        if self.state.status == AgentState.EXECUTING:
            return {"error": "Cannot collect while executing"}

        self.state.set_collecting()
        results = self._run_collectors()
        self.state.set_idle()
        return {"collection": results}

    # -- cleanup --

    def cleanup(self) -> None:
        """Remove all collected artifacts."""
        if os.path.isdir(self.artifacts_dir):
            shutil.rmtree(self.artifacts_dir)
            os.makedirs(self.artifacts_dir, exist_ok=True)
        log.info("Artifacts cleaned up")

    # -- internal helpers --

    def _run_collectors(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for collector in self.collectors:
            log.info("Running collector: %s", collector.name)
            try:
                results.append(collector.collect())
            except Exception as exc:
                log.error("Collector %s failed: %s", collector.name, exc)
                results.append({
                    "collector": collector.name,
                    "status": "error",
                    "error": str(exc),
                    "files": [],
                })
        return results

    def _package_results(
        self,
        sample_name: str,
        collection: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Zip collected artifacts and copy the archive to the shared folder."""
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base = os.path.splitext(sample_name)[0]
        zip_name = "results_{base}_{ts}.zip".format(base=base, ts=ts)
        zip_path = os.path.join(self.workdir, zip_name)

        # Gather every file the collectors reported
        all_files: List[str] = []
        for entry in collection:
            all_files.extend(entry.get("files", []))

        # Write a metadata sidecar
        meta_path = os.path.join(self.artifacts_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "sample": sample_name,
                    "timestamp": ts,
                    "agent_version": AGENT_VERSION,
                    "collectors": collection,
                },
                fh,
                indent=2,
            )
        all_files.append(meta_path)

        if not all_files:
            log.info("No artifacts to package")
            return None

        # Build zip
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fpath in all_files:
                if os.path.isfile(fpath):
                    arcname = os.path.relpath(fpath, self.workdir)
                    zf.write(fpath, arcname)

        # Copy to shared folder
        share_dest = os.path.join(self.share_path, zip_name)
        try:
            shutil.copy2(zip_path, share_dest)
            log.info("Results package → %s", share_dest)
        except OSError as exc:
            log.error("Failed to copy package to share: %s", exc)

        return zip_name


# ═══════════════════════════════════════════════════════════════════════════
# HTTP Handler
# ═══════════════════════════════════════════════════════════════════════════

class AgentHTTPHandler(BaseHTTPRequestHandler):
    """Minimal JSON API handler for the agent."""

    # These class attributes are set dynamically by create_server()
    agent: IsoLensAgent
    shutdown_event: threading.Event

    # Redirect default logging into our logger
    def log_message(self, fmt: str, *args: Any) -> None:
        log.info("HTTP  %s", fmt % args)

    # -- helpers --

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def _ok(self, data: Any) -> None:
        self._send_json({"status": "ok", "data": data})

    def _err(self, msg: str, code: int = 400) -> None:
        self._send_json({"status": "error", "error": msg}, code)

    # -- routing --

    def do_GET(self) -> None:  # noqa: N802
        routes: Dict[str, Any] = {
            "/api/status": self._get_status,
            "/api/collectors": self._get_collectors,
            "/api/artifacts": self._get_artifacts,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self._err("Not found", 404)

    def do_POST(self) -> None:  # noqa: N802
        routes: Dict[str, Any] = {
            "/api/execute": self._post_execute,
            "/api/collect": self._post_collect,
            "/api/cleanup": self._post_cleanup,
            "/api/shutdown": self._post_shutdown,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self._err("Not found", 404)

    # -- GET handlers --

    def _get_status(self) -> None:
        data = self.agent.state.to_dict()
        data["agent_version"] = AGENT_VERSION
        data["platform"] = platform.platform()
        data["collectors"] = self.agent.get_collector_info()
        self._ok(data)

    def _get_collectors(self) -> None:
        self._ok({"collectors": self.agent.get_collector_info()})

    def _get_artifacts(self) -> None:
        arts = self.agent.list_artifacts()
        self._ok({"artifacts": arts, "count": len(arts)})

    # -- POST handlers --

    def _post_execute(self) -> None:
        if self.agent.state.status == AgentState.EXECUTING:
            self._err("Agent is already executing a sample", 409)
            return

        body = self._read_body()
        filename = body.get("filename")
        timeout = body.get("timeout", 60)

        if not filename:
            self._err("Missing required field: 'filename'")
            return

        # Execute in background thread so the HTTP server stays responsive
        def _bg() -> None:
            result = self.agent.execute_sample(filename, timeout=timeout)
            log.info(
                "Background execution finished: %s",
                json.dumps(result, indent=2, default=str),
            )

        threading.Thread(target=_bg, daemon=True).start()

        self._ok({
            "message": "Execution started for '{f}'".format(f=filename),
            "timeout": timeout,
        })

    def _post_collect(self) -> None:
        if self.agent.state.status == AgentState.EXECUTING:
            self._err("Cannot collect while executing", 409)
            return
        result = self.agent.collect_only()
        self._ok(result)

    def _post_cleanup(self) -> None:
        self.agent.cleanup()
        self._ok({"message": "Artifacts cleaned up"})

    def _post_shutdown(self) -> None:
        self._ok({"message": "Agent shutting down"})
        self.shutdown_event.set()


# ═══════════════════════════════════════════════════════════════════════════
# Server Factory
# ═══════════════════════════════════════════════════════════════════════════

def create_server(
    agent: IsoLensAgent,
    host: str = "0.0.0.0",
    port: int = 9090,
) -> HTTPServer:
    """Build an HTTPServer bound to *host:port* with the given agent."""
    shutdown_event = threading.Event()

    # Dynamically create a handler subclass with agent & event attached
    handler = type(
        "BoundAgentHandler",
        (AgentHTTPHandler,),
        {"agent": agent, "shutdown_event": shutdown_event},
    )

    server = HTTPServer((host, port), handler)
    server.shutdown_event = shutdown_event  # type: ignore[attr-defined]
    return server


# ═══════════════════════════════════════════════════════════════════════════
# CLI & Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="IsoLens Guest Agent — sandbox VM HTTP service",
    )
    p.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind address (default: 0.0.0.0)",
    )
    p.add_argument(
        "--port",
        type=int,
        default=9090,
        help="Bind port (default: 9090)",
    )
    p.add_argument(
        "--share",
        default=r"\\VBOXSVR\SandboxShare",
        help=r"VirtualBox shared folder UNC path "
             r"(default: \\VBOXSVR\SandboxShare)",
    )
    p.add_argument(
        "--workdir",
        default=r"C:\IsoLens",
        help=r"Local working directory (default: C:\IsoLens)",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    # Validate shared folder
    if not os.path.isdir(args.share):
        log.error("Shared folder not accessible: %s", args.share)
        log.error(
            "Ensure VirtualBox shared folders are configured and "
            "auto-mounted or manually mapped."
        )
        return 1

    os.makedirs(args.workdir, exist_ok=True)

    agent = IsoLensAgent(share_path=args.share, workdir=args.workdir)
    server = create_server(agent, host=args.host, port=args.port)

    log.info("=" * 60)
    log.info("  IsoLens Agent v%s", AGENT_VERSION)
    log.info("  Listening on  http://%s:%d", args.host, args.port)
    log.info("  Shared folder %s", args.share)
    log.info("  Working dir   %s", args.workdir)
    log.info("=" * 60)

    # Run in a thread so we can monitor the shutdown event
    srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
    srv_thread.start()

    try:
        while not server.shutdown_event.is_set():  # type: ignore[attr-defined]
            time.sleep(0.5)
    except KeyboardInterrupt:
        log.info("Interrupted — shutting down")

    server.shutdown()
    log.info("Agent stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
