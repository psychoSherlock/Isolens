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
