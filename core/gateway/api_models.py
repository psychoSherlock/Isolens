"""Shared API models for IsoLens gateway."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    message: str
    details: Optional[str] = None


class StandardResponse(BaseModel):
    status: str = Field(..., description="ok or error")
    data: Optional[dict] = None
    error: Optional[ErrorPayload] = None


class VMStartRequest(BaseModel):
    vm: str
    headless: bool = False
    dry_run: bool = False
    raise_on_error: bool = True


class VMInfoRequest(BaseModel):
    vm: str
    machinereadable: bool = False
    dry_run: bool = False
    raise_on_error: bool = True


class VMControlRequest(BaseModel):
    vm: str
    dry_run: bool = False
    raise_on_error: bool = True


class SnapshotRequest(BaseModel):
    vm: str
    name: str
    dry_run: bool = False
    raise_on_error: bool = True


# ── Analysis models ──────────────────────────────────────────────────

class AnalysisSubmitRequest(BaseModel):
    """Request body for /api/analysis/submit."""

    timeout: int = Field(60, ge=10, le=300, description="Behavior monitoring timeout in seconds")


class AnalysisStatusResponse(BaseModel):
    """Wrapper returned by /api/analysis/status."""

    analysis_id: Optional[str] = None
    sample_name: Optional[str] = None
    status: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    timeout: Optional[int] = None
    error: Optional[str] = None
    report_dir: Optional[str] = None
    sysmon_events: Optional[int] = None
    files_collected: Optional[list] = None
