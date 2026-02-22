"""Controller-related API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.controller import VBoxManageClient
from core.gateway.api_models import (
    SnapshotRequest,
    StandardResponse,
    VMControlRequest,
    VMInfoRequest,
    VMStartRequest,
)

router = APIRouter(prefix="/api/vms", tags=["vms"])


def _ok(data: dict) -> StandardResponse:
    return StandardResponse(status="ok", data=data, error=None)


def _error(message: str, details: Optional[str] = None) -> StandardResponse:
    return StandardResponse(
        status="error",
        data=None,
        error={"message": message, "details": details},
    )


def _client(dry_run: bool, raise_on_error: bool) -> VBoxManageClient:
    return VBoxManageClient(dry_run=dry_run, raise_on_error=raise_on_error)


@router.get("", response_model=StandardResponse)
def list_vms(dry_run: bool = False, raise_on_error: bool = True) -> StandardResponse:
    try:
        client = _client(dry_run=dry_run, raise_on_error=raise_on_error)
        result = client.list_vms()
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.get("/running", response_model=StandardResponse)
def list_running_vms(
    dry_run: bool = False, raise_on_error: bool = True
) -> StandardResponse:
    try:
        client = _client(dry_run=dry_run, raise_on_error=raise_on_error)
        result = client.list_running_vms()
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/info", response_model=StandardResponse)
def vm_info(payload: VMInfoRequest) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.show_vm_info(payload.vm, machinereadable=payload.machinereadable)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/start", response_model=StandardResponse)
def vm_start(payload: VMStartRequest) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.start_vm(payload.vm, headless=payload.headless)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/poweroff", response_model=StandardResponse)
def vm_poweroff(payload: VMControlRequest) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.poweroff_vm(payload.vm)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/savestate", response_model=StandardResponse)
def vm_savestate(payload: VMControlRequest) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.savestate_vm(payload.vm)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/pause", response_model=StandardResponse)
def vm_pause(payload: VMControlRequest) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.pause_vm(payload.vm)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/resume", response_model=StandardResponse)
def vm_resume(payload: VMControlRequest) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.resume_vm(payload.vm)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/reset", response_model=StandardResponse)
def vm_reset(payload: VMControlRequest) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.reset_vm(payload.vm)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/shutdown", response_model=StandardResponse)
def vm_shutdown(payload: VMControlRequest, force: bool = False) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.shutdown_vm(payload.vm, force=force)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/snapshot/take", response_model=StandardResponse)
def snapshot_take(payload: SnapshotRequest) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.snapshot_take(payload.vm, payload.name)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/snapshot/restore", response_model=StandardResponse)
def snapshot_restore(payload: SnapshotRequest) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.snapshot_restore(payload.vm, payload.name)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.post("/snapshot/restore-current", response_model=StandardResponse)
def snapshot_restore_current(payload: VMControlRequest) -> StandardResponse:
    try:
        client = _client(dry_run=payload.dry_run, raise_on_error=payload.raise_on_error)
        result = client.snapshot_restore_current(payload.vm)
        return _ok(result.to_dict())
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )
