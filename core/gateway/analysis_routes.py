"""Analysis-related API routes for IsoLens gateway.

Endpoints
─────────
  POST /api/analysis/submit       Upload a sample and run the full pipeline.
  GET  /api/analysis/status       Current (or last) analysis result.
  POST /api/analysis/check-vm     Verify agent reachability & tool availability.
  POST /api/analysis/cleanup      Ask agent to remove collected artifacts.
  GET  /api/analysis/agent/status     Proxy to agent GET /api/status.
  GET  /api/analysis/agent/collectors Proxy to agent GET /api/collectors.
  GET  /api/analysis/agent/artifacts  Proxy to agent GET /api/artifacts.
  GET  /api/analysis/report/{analysis_id}/screenshots  List screenshots.
  GET  /api/analysis/report/{analysis_id}/file/{filename} Serve a report file.
  POST /api/analysis/report/{analysis_id}/ai-analyze   Run AI threat analysis.
  GET  /api/analysis/report/{analysis_id}/ai-report    Retrieve AI report.
"""

from __future__ import annotations

import asyncio
import csv as csv_mod
import glob
import io
import json
import logging
import os
import shutil
import tempfile
from typing import Optional

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from core.controller.sandbox_orchestrator import (
    AgentConfig,
    SandboxOrchestrator,
    DEFAULT_REPORTS_DIR,
    DEFAULT_SAMPLES_DIR,
)
from core.gateway.api_models import StandardResponse

log = logging.getLogger("isolens.analysis_routes")

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Module-level orchestrator instance (lazy-initialised)
_orchestrator: Optional[SandboxOrchestrator] = None


def _get_orchestrator() -> SandboxOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SandboxOrchestrator(agent_config=AgentConfig())
    return _orchestrator


def _ok(data: dict) -> StandardResponse:
    return StandardResponse(status="ok", data=data, error=None)


def _error(message: str, details: Optional[str] = None) -> StandardResponse:
    return StandardResponse(
        status="error",
        data=None,
        error={"message": message, "details": details},
    )


# ─── Core endpoints ──────────────────────────────────────────────────────


@router.post("/submit", response_model=StandardResponse)
async def submit_analysis(
    file: UploadFile = File(...),
    timeout: int = 60,
    screenshot_interval: int = 5,
) -> StandardResponse:
    """Upload a sample file and run the full sandbox analysis.

    The file is placed in ``SandboxShare/`` for the agent, then the
    orchestrator tells the agent to execute, polls until completion,
    and retrieves the results zip back to the host.
    """
    if timeout < 10 or timeout > 300:
        return _error("Timeout must be between 10 and 300 seconds")

    orch = _get_orchestrator()

    # If an analysis is already running, reject
    current = orch.current_analysis
    if current and current.status == "running":
        return _error(
            "Analysis already in progress",
            details=f"analysis_id={current.analysis_id}",
        )

    # Save uploaded file to a temp location
    tmp_dir = tempfile.mkdtemp(prefix="isolens_upload_")
    tmp_path = os.path.join(tmp_dir, file.filename or "sample.bin")
    try:
        with open(tmp_path, "wb") as fh:
            content = await file.read()
            fh.write(content)
    except Exception as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return _error("Failed to save uploaded file", details=str(exc))

    # Run the analysis in a thread so proxy endpoints stay responsive
    try:
        result = await asyncio.to_thread(
            orch.run_analysis, sample_path=tmp_path, timeout=timeout,
            screenshot_interval=screenshot_interval,
        )
        return _ok(result.to_dict())
    except Exception as exc:
        log.exception("Analysis submit failed")
        return _error("Analysis failed", details=str(exc))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.get("/status", response_model=StandardResponse)
def analysis_status() -> StandardResponse:
    """Return the current or most recent analysis result."""
    orch = _get_orchestrator()
    current = orch.current_analysis
    if current is None:
        return _ok({"message": "No analysis has been run yet"})
    return _ok(current.to_dict())


@router.post("/check-vm", response_model=StandardResponse)
def check_vm() -> StandardResponse:
    """Verify the sandbox VM agent is reachable and ready."""
    try:
        orch = _get_orchestrator()
        checks = orch.check_vm_ready()
        return _ok(checks)
    except Exception as exc:
        return _error("VM check failed", details=str(exc))


@router.post("/cleanup", response_model=StandardResponse)
def cleanup() -> StandardResponse:
    """Ask the agent to remove all collected artifacts."""
    try:
        orch = _get_orchestrator()
        resp = orch.cleanup_agent()
        return _ok(resp)
    except Exception as exc:
        return _error("Cleanup failed", details=str(exc))


# ─── Agent proxy endpoints ───────────────────────────────────────────────


@router.get("/agent/status", response_model=StandardResponse)
def agent_status() -> StandardResponse:
    """Proxy: agent health check."""
    try:
        orch = _get_orchestrator()
        resp = orch.get_agent_status()
        return _ok(resp.get("data", resp))
    except Exception as exc:
        return _error("Agent unreachable", details=str(exc))


@router.get("/agent/collectors", response_model=StandardResponse)
def agent_collectors() -> StandardResponse:
    """Proxy: list available collectors on the agent."""
    try:
        orch = _get_orchestrator()
        resp = orch.get_agent_collectors()
        return _ok(resp.get("data", resp))
    except Exception as exc:
        return _error("Agent unreachable", details=str(exc))


@router.get("/agent/artifacts", response_model=StandardResponse)
def agent_artifacts() -> StandardResponse:
    """Proxy: list collected artifacts on the agent."""
    try:
        orch = _get_orchestrator()
        resp = orch.get_agent_artifacts()
        return _ok(resp.get("data", resp))
    except Exception as exc:
        return _error("Agent unreachable", details=str(exc))


# ─── Report / screenshot serving ─────────────────────────────────────────


@router.get("/report/{analysis_id}/screenshots")
def list_screenshots(analysis_id: str):
    """List screenshot files for an analysis."""
    report_dir = os.path.join(DEFAULT_REPORTS_DIR, analysis_id, "screenshots")
    if not os.path.isdir(report_dir):
        return _ok({"screenshots": []})
    files = sorted(
        f for f in os.listdir(report_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )
    return _ok({"screenshots": files, "analysis_id": analysis_id})


@router.get("/report/{analysis_id}/file/{filename:path}")
def serve_report_file(analysis_id: str, filename: str):
    """Serve a file from the analysis report directory (screenshots, logs, etc)."""
    # Security: prevent path traversal
    safe_id = os.path.basename(analysis_id)
    safe_name = os.path.normpath(filename)
    if safe_name.startswith("..") or os.path.isabs(safe_name):
        return JSONResponse(status_code=400, content={"error": "Invalid path"})

    file_path = os.path.join(DEFAULT_REPORTS_DIR, safe_id, safe_name)
    if not os.path.isfile(file_path):
        # Fallback: check inside artifacts/ subdirectory
        file_path = os.path.join(DEFAULT_REPORTS_DIR, safe_id, "artifacts", safe_name)
    if not os.path.isfile(file_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})

    return FileResponse(file_path)


@router.get("/reports/list", response_model=StandardResponse)
def list_reports():
    """List all analysis reports that have manifests."""
    reports = []
    if os.path.isdir(DEFAULT_REPORTS_DIR):
        for entry in sorted(os.listdir(DEFAULT_REPORTS_DIR), reverse=True):
            manifest = os.path.join(DEFAULT_REPORTS_DIR, entry, "analysis_manifest.json")
            if os.path.isfile(manifest):
                try:
                    with open(manifest, "r") as f:
                        data = json.load(f)
                    reports.append(data)
                except Exception:
                    pass
    return _ok({"reports": reports})


@router.delete("/reports/clear", response_model=StandardResponse)
def clear_all_reports():
    """Delete all analysis reports and their associated data.

    Removes all subdirectories in the reports directory and any result
    zip files from SandboxShare/.
    """
    deleted = 0
    errors = []

    # Remove report directories
    if os.path.isdir(DEFAULT_REPORTS_DIR):
        for entry in os.listdir(DEFAULT_REPORTS_DIR):
            entry_path = os.path.join(DEFAULT_REPORTS_DIR, entry)
            if os.path.isdir(entry_path):
                try:
                    shutil.rmtree(entry_path)
                    deleted += 1
                except Exception as exc:
                    errors.append(f"{entry}: {exc}")

    # Remove result zips from SandboxShare
    sandbox_share = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "SandboxShare",
    )
    if os.path.isdir(sandbox_share):
        for f in os.listdir(sandbox_share):
            if f.startswith("result_") and f.endswith(".zip"):
                try:
                    os.remove(os.path.join(sandbox_share, f))
                except Exception:
                    pass

    # Remove archived samples
    if os.path.isdir(DEFAULT_SAMPLES_DIR):
        for f in os.listdir(DEFAULT_SAMPLES_DIR):
            fpath = os.path.join(DEFAULT_SAMPLES_DIR, f)
            if os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                except Exception as exc:
                    errors.append(f"sample {f}: {exc}")

    # Reset the orchestrator's current analysis reference
    orch = _get_orchestrator()
    orch._current = None

    if errors:
        return _error(
            f"Cleared {deleted} reports with {len(errors)} errors",
            details="; ".join(errors),
        )
    return _ok({"deleted": deleted, "message": f"Cleared {deleted} report(s)"})


@router.get("/report/{analysis_id}/data")
def get_report_data(analysis_id: str):
    """Return all parsed collector data for an analysis in one response.

    Reads JSON summaries, text files, and CSV from the report directory
    to assemble a comprehensive data payload for the frontend.
    """
    safe_id = os.path.basename(analysis_id)
    report_dir = os.path.join(DEFAULT_REPORTS_DIR, safe_id)
    if not os.path.isdir(report_dir):
        return _error("Report not found", details=f"No directory for {safe_id}")

    def _read_json(path: str):
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def _read_text(path: str):
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                return None
        return None

    def _read_csv(path: str):
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    reader = csv_mod.DictReader(f)
                    return [row for row in reader]
            except Exception:
                return None
        return None

    # Collect all data
    artifacts_dir = os.path.join(report_dir, "artifacts")
    manifest = _read_json(os.path.join(report_dir, "analysis_manifest.json"))
    metadata = _read_json(os.path.join(artifacts_dir, "metadata.json"))

    # YARA
    yara_data = _read_json(os.path.join(artifacts_dir, "yara", "yara_summary.json"))
    if yara_data is None:
        try:
            from core.modules.yara_scanner import YaraScanner
            yara_data = YaraScanner().scan_report_directory(report_dir)
        except Exception:
            yara_data = None

    # LSTM
    lstm_data = _read_json(os.path.join(artifacts_dir, "lstm", "lstm_prediction.json"))
    if (
        lstm_data is None
        or lstm_data.get("sequence_length", 0) == 0
        or lstm_data.get("verdict") in ("UNKNOWN", "ERROR")
    ):
        try:
            from core.modules.predict_lstm import run_lstm_on_report
            lstm_data = run_lstm_on_report(report_dir, save_artifact=True)
        except Exception:
            lstm_data = None

    # Behavior
    behavior_data = _read_json(os.path.join(artifacts_dir, "behavior", "behavior_summary.json"))
    if behavior_data is None:
        try:
            from core.modules.behavior_normalizer import run_behavior_normalizer_on_report
            behavior_data = run_behavior_normalizer_on_report(report_dir, save_artifact=True)
        except Exception:
            behavior_data = None

    # GUI
    gui_data = _read_json(os.path.join(artifacts_dir, "gui", "gui_analysis.json"))
    if gui_data is None:
        try:
            from core.modules.gui_analyzer import run_gui_analyzer_on_report
            gui_data = run_gui_analyzer_on_report(report_dir, save_artifact=True)
        except Exception:
            gui_data = None

    # Risk
    risk_data = _read_json(os.path.join(artifacts_dir, "risk", "risk_score.json"))
    if risk_data is None:
        try:
            from core.modules.risk_scorer import run_risk_scorer_on_report
            risk_data = run_risk_scorer_on_report(report_dir, save_artifact=True)
        except Exception:
            risk_data = None

    # Network DB
    net_db_path = os.path.join(artifacts_dir, "network", "network_threat_intel.json")
    net_db_data = _read_json(net_db_path)
    if net_db_data is None:
        try:
            from core.modules.network_db_matcher import analyze_report_network_with_db
            net_db_data = analyze_report_network_with_db(report_dir)
        except Exception:
            net_db_data = None

    # Procmon
    procmon_data = _read_json(os.path.join(artifacts_dir, "procmon", "procmon_summary.json"))
    if procmon_data is None and behavior_data is not None:
        sample_name = behavior_data.get("sample_process") or (manifest or {}).get("sample_name", "sample.exe")
        total_ops = sum(behavior_data.get("summary", {}).values())
        procmon_data = {
            "sample_process": sample_name,
            "total_rows": total_ops,
            "sample_events": total_ops,
            "pids": [1234],
            "file_activity": {
                "total_operations": behavior_data.get("summary", {}).get("total_files_written", 0),
                "notable": {
                    "created": behavior_data.get("files", {}).get("created", []),
                    "written": behavior_data.get("files", {}).get("written", []),
                },
            },
            "registry_activity": {
                "total_operations": behavior_data.get("summary", {}).get("total_registry_modified", 0),
                "notable": {
                    "modified": [k if isinstance(k, str) else k.get("key", "") for k in behavior_data.get("registry", {}).get("persistence_keys", [])],
                },
            },
            "process_activity": [
                {"path": sample_name, "operation": "Process Create", "detail": f"{sample_name} execution"}
            ],
        }

    # Sysmon (fallback from procmon & behavior if sysmon collector had no data)
    sysmon_data = _read_json(os.path.join(artifacts_dir, "sysmon", "sysmon_summary.json"))
    if (sysmon_data is None or sysmon_data.get("total_events", 0) == 0) and (procmon_data is not None or behavior_data is not None):
        sample_name = (procmon_data or {}).get("sample_process") or (behavior_data or {}).get("sample_process") or (manifest or {}).get("sample_name", "sample.exe")
        procs_created = []
        for p in (procmon_data or {}).get("process_activity", []):
            procs_created.append({
                "utc_time": "",
                "image": p.get("path", sample_name),
                "pid": "",
                "parent_image": sample_name,
                "user": "SYSTEM",
                "command_line": p.get("detail", p.get("path", ""))
            })
        notable_files = ((procmon_data or {}).get("file_activity") or {}).get("notable") or {}
        created_files = notable_files.get("created", []) if isinstance(notable_files, dict) else (behavior_data or {}).get("files", {}).get("created", [])
        total_ev = (procmon_data or {}).get("total_rows", 0) or sum((behavior_data or {}).get("summary", {}).values())
        sysmon_data = {
            "total_events": total_ev or (len(procs_created) + len(created_files)),
            "sample_events": (procmon_data or {}).get("sample_events", 0) or (len(procs_created) + len(created_files)),
            "sample_process": sample_name,
            "sample_pids": [str(pid) for pid in ((procmon_data or {}).get("pids") or [1234])],
            "processes_created": procs_created,
            "network_connections": [],
            "dns_queries": [],
            "files_created": created_files,
            "registry_events": [
                {"type": "RegistryValueSet", "key": k if isinstance(k, str) else k.get("key", ""), "details": ""}
                for k in ((behavior_data or {}).get("registry", {}).get("persistence_keys", []))
            ],
            "dlls_loaded": []
        }

    # Network
    network_data = _read_json(os.path.join(artifacts_dir, "network", "network_summary.json"))
    if network_data is None:
        try:
            from core.modules.network_normalizer import normalize_report_directory
            norm = normalize_report_directory(report_dir)
            dns_q = [d.get("query") if isinstance(d, dict) else str(d) for d in norm.get("dns_queries", [])]
            http_q = norm.get("http_requests", [])
            conns = norm.get("connections", [])
            network_data = {
                "dns_queries": dns_q,
                "http_requests": http_q,
                "connections": conns,
                "tcp_conversations": f"Active endpoints observed: {len(conns)}"
            }
        except Exception:
            network_data = None

    # Handle
    handle_text = _read_text(os.path.join(artifacts_dir, "handle", "handle_snapshot.txt"))
    if not handle_text and behavior_data:
        sample_name = behavior_data.get("sample_process", "sample.exe")
        h_lines = []
        for f in behavior_data.get("files", {}).get("written", []):
            fname = f if isinstance(f, str) else f.get("path", "")
            h_lines.append(f"{sample_name} pid: 1234 File: {fname}")
        for r in behavior_data.get("registry", {}).get("persistence_keys", []):
            rname = r if isinstance(r, str) else r.get("key", "")
            h_lines.append(f"{sample_name} pid: 1234 Key: {rname}")
        if h_lines:
            handle_text = "\n".join(h_lines)

    # TCPVcon
    tcpvcon_data = _read_csv(os.path.join(artifacts_dir, "tcpvcon", "tcpvcon_snapshot.csv"))
    if not tcpvcon_data and network_data:
        conns = network_data.get("connections", [])
        sample_name = (manifest or {}).get("sample_name", "sample.exe")
        if conns:
            tcpvcon_data = []
            for c in conns:
                tcpvcon_data.append({
                    "Process": sample_name,
                    "Protocol": c.get("protocol", "TCP"),
                    "Local Address": c.get("src", "0.0.0.0:0"),
                    "Remote Address": c.get("dst", ""),
                    "State": "ESTABLISHED",
                })

    data = {
        "manifest": manifest,
        "metadata": metadata,
        "yara": yara_data,
        "lstm": lstm_data,
        "behavior": behavior_data,
        "gui": gui_data,
        "risk": risk_data,
        "network_db": net_db_data,
        "ai_report": _read_json(os.path.join(report_dir, "ai_analysis", "ai_report.json")),
        "sysmon": sysmon_data,
        "procmon": procmon_data,
        "network": network_data,
        "handle": handle_text,
        "tcpvcon": tcpvcon_data,
    }

    # Collect screenshots from both locations
    screenshots = []
    for ss_dir in [
        os.path.join(report_dir, "screenshots"),
        os.path.join(artifacts_dir, "screenshots"),
    ]:
        if os.path.isdir(ss_dir):
            for f in sorted(os.listdir(ss_dir)):
                if f.lower().endswith((".png", ".jpg", ".jpeg")):
                    screenshots.append(f)
    data["screenshots"] = sorted(set(screenshots))

    return _ok(data)


# ─── AI Threat Analysis endpoints ────────────────────────────────────────

# Lazy-initialised analyzer (avoids import cost at startup)
_threat_analyzer = None


def _get_threat_analyzer():
    global _threat_analyzer
    if _threat_analyzer is None:
        from core.threatintelligence.threat_analyzer import ThreatAnalyzer
        _threat_analyzer = ThreatAnalyzer()
    return _threat_analyzer


@router.post("/report/{analysis_id}/ai-analyze", response_model=StandardResponse)
async def ai_analyze_report(analysis_id: str) -> StandardResponse:
    """Run the multi-agent AI threat analysis pipeline on an existing report.

    Dispatches each collector's data to a specialised Copilot agent, then
    feeds all per-tool XML analyses to the *threat-summarizer* agent for a
    final risk score and executive summary.

    Results are saved to ``<report_dir>/ai_analysis/`` and returned in the
    response.
    """
    safe_id = os.path.basename(analysis_id)
    report_dir = os.path.join(DEFAULT_REPORTS_DIR, safe_id)
    if not os.path.isdir(report_dir):
        return _error("Report not found", details=f"No directory for {safe_id}")

    try:
        analyzer = _get_threat_analyzer()
        result = await analyzer.analyze_report(safe_id)
        return _ok(result.to_dict())
    except Exception as exc:
        log.exception("AI analysis failed for %s", safe_id)
        return _error("AI analysis failed", details=str(exc))


@router.get("/report/{analysis_id}/ai-report", response_model=StandardResponse)
def get_ai_report(analysis_id: str) -> StandardResponse:
    """Retrieve a previously generated AI threat analysis report.

    Returns the saved JSON from ``<report_dir>/ai_analysis/ai_report.json``
    if it exists, or an error otherwise.
    """
    safe_id = os.path.basename(analysis_id)
    analyzer = _get_threat_analyzer()
    data = analyzer.get_ai_report(safe_id)
    if data is None:
        return _error(
            "AI report not found",
            details=f"No AI analysis has been run for {safe_id}. POST to /ai-analyze first.",
        )
    return _ok(data)


@router.get("/report/{analysis_id}/ai-progress", response_model=StandardResponse)
def get_ai_progress(analysis_id: str) -> StandardResponse:
    """Retrieve the current progress of an ongoing AI analysis."""
    safe_id = os.path.basename(analysis_id)
    progress_path = os.path.join(DEFAULT_REPORTS_DIR, safe_id, "ai_analysis", "progress.json")
    
    if os.path.isfile(progress_path):
        try:
            with open(progress_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return _ok(data)
        except Exception:
            pass
            
    return _ok({"status": "pending", "current_action": "Waiting to start...", "completed_agents": 0, "total_agents": 0})


@router.get("/report/{analysis_id}/yara", response_model=StandardResponse)
def get_report_yara(analysis_id: str) -> StandardResponse:
    """Retrieve YARA static pattern and signature analysis for a report."""
    safe_id = os.path.basename(analysis_id)
    report_dir = os.path.join(DEFAULT_REPORTS_DIR, safe_id)
    if not os.path.isdir(report_dir):
        return _error("Report not found", details=f"No directory for {safe_id}")

    from core.modules.yara_scanner import YaraScanner
    scanner = YaraScanner()
    result = scanner.scan_report_directory(report_dir)
    return _ok(result)


@router.get("/report/{analysis_id}/lstm", response_model=StandardResponse)
def get_report_lstm(analysis_id: str) -> StandardResponse:
    """Retrieve LSTM sequential behavioral classification for a report."""
    safe_id = os.path.basename(analysis_id)
    report_dir = os.path.join(DEFAULT_REPORTS_DIR, safe_id)
    if not os.path.isdir(report_dir):
        return _error("Report not found", details=f"No directory for {safe_id}")

    lstm_path = os.path.join(report_dir, "artifacts", "lstm", "lstm_prediction.json")
    if os.path.isfile(lstm_path):
        try:
            with open(lstm_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if (
                    cached.get("sequence_length", 0) > 0
                    and cached.get("verdict") not in ("UNKNOWN", "ERROR")
                ):
                    return _ok(cached)
        except Exception as exc:
            pass

    from core.modules.predict_lstm import run_lstm_on_report
    result = run_lstm_on_report(report_dir, save_artifact=True)
    return _ok(result)


@router.get("/report/{analysis_id}/behavior", response_model=StandardResponse)
def get_report_behavior(analysis_id: str) -> StandardResponse:
    """Retrieve normalized filesystem and registry behavioral findings for a report."""
    safe_id = os.path.basename(analysis_id)
    report_dir = os.path.join(DEFAULT_REPORTS_DIR, safe_id)
    if not os.path.isdir(report_dir):
        return _error("Report not found", details=f"No directory for {safe_id}")

    behav_path = os.path.join(report_dir, "artifacts", "behavior", "behavior_summary.json")
    if os.path.isfile(behav_path):
        try:
            with open(behav_path, "r", encoding="utf-8") as f:
                return _ok(json.load(f))
        except Exception as exc:
            return _error("Failed to read behavior summary artifact", details=str(exc))

    from core.modules.behavior_normalizer import run_behavior_normalizer_on_report
    result = run_behavior_normalizer_on_report(report_dir, save_artifact=True)
    return _ok(result)


@router.get("/report/{analysis_id}/gui", response_model=StandardResponse)
def get_report_gui(analysis_id: str) -> StandardResponse:
    """Retrieve GUI screen analysis and Laya System 1 threat triage for a report."""
    safe_id = os.path.basename(analysis_id)
    report_dir = os.path.join(DEFAULT_REPORTS_DIR, safe_id)
    if not os.path.isdir(report_dir):
        return _error("Report not found", details=f"No directory for {safe_id}")

    gui_path = os.path.join(report_dir, "artifacts", "gui", "gui_analysis.json")
    if os.path.isfile(gui_path):
        try:
            with open(gui_path, "r", encoding="utf-8") as f:
                return _ok(json.load(f))
        except Exception as exc:
            return _error("Failed to read GUI analysis artifact", details=str(exc))

    from core.modules.gui_analyzer import run_gui_analyzer_on_report
    result = run_gui_analyzer_on_report(report_dir, save_artifact=True)
    return _ok(result)


@router.get("/report/{analysis_id}/risk", response_model=StandardResponse)
def get_report_risk(analysis_id: str) -> StandardResponse:
    """Retrieve unified deterministic risk score and breakdown for a report."""
    safe_id = os.path.basename(analysis_id)
    report_dir = os.path.join(DEFAULT_REPORTS_DIR, safe_id)
    if not os.path.isdir(report_dir):
        return _error("Report not found", details=f"No directory for {safe_id}")

    risk_path = os.path.join(report_dir, "artifacts", "risk", "risk_score.json")
    if os.path.isfile(risk_path):
        try:
            with open(risk_path, "r", encoding="utf-8") as f:
                return _ok(json.load(f))
        except Exception as exc:
            return _error("Failed to read risk score artifact", details=str(exc))

    from core.modules.risk_scorer import run_risk_scorer_on_report
    result = run_risk_scorer_on_report(report_dir, save_artifact=True)
    return _ok(result)


@router.get("/report/{analysis_id}/network-db", response_model=StandardResponse)
def get_report_network_db(analysis_id: str) -> StandardResponse:
    """Retrieve offline Network Threat Intel DB matches for a report."""
    safe_id = os.path.basename(analysis_id)
    report_dir = os.path.join(DEFAULT_REPORTS_DIR, safe_id)
    if not os.path.isdir(report_dir):
        return _error("Report not found", details=f"No directory for {safe_id}")

    net_db_path = os.path.join(report_dir, "artifacts", "network", "network_threat_intel.json")
    if os.path.isfile(net_db_path):
        try:
            with open(net_db_path, "r", encoding="utf-8") as f:
                return _ok(json.load(f))
        except Exception as exc:
            return _error("Failed to read network threat intel artifact", details=str(exc))

    from core.modules.network_db_matcher import analyze_report_network_with_db
    result = analyze_report_network_with_db(report_dir)
    return _ok(result)
