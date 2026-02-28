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
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
from typing import Optional

from fastapi import APIRouter, File, UploadFile

from core.controller.sandbox_orchestrator import (
    AgentConfig,
    SandboxOrchestrator,
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
