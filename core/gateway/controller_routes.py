"""Controller-related API routes."""

from __future__ import annotations

import os
import tempfile
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from core.controller import VBoxManageClient
from core.gateway.api_models import (
    SnapshotRequest,
    StandardResponse,
    VMControlRequest,
    VMInfoRequest,
    VMStartRequest,
)
from core.modules.vbox_output_parser import (
    parse_list_vms,
    parse_showvminfo,
    parse_guest_net_properties,
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


def _action_response(result, *, dry_run: bool) -> dict:
    """Build a response for action endpoints (start, poweroff, etc.)."""
    data: dict = {
        "success": result.returncode == 0,
        "message": result.stdout.strip() or result.stderr.strip() or "OK",
    }
    if dry_run:
        data["debug"] = result.to_dict()
    return data


@router.get("", response_model=StandardResponse)
def list_vms(dry_run: bool = False, raise_on_error: bool = True) -> StandardResponse:
    try:
        client = _client(dry_run=dry_run, raise_on_error=raise_on_error)
        result = client.list_vms()
        data: dict = {"vms": parse_list_vms(result.stdout)}
        if dry_run:
            data["debug"] = result.to_dict()
        return _ok(data)
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
        data: dict = {"vms": parse_list_vms(result.stdout)}
        if dry_run:
            data["debug"] = result.to_dict()
        return _ok(data)
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


@router.get("/ip", response_model=StandardResponse)
def vm_ip_addresses(
    vm: str, dry_run: bool = False, raise_on_error: bool = True
) -> StandardResponse:
    """Return all network interface IPs for a given VM via Guest Additions.

    Requires VirtualBox Guest Additions to be installed and running inside the VM.
    """
    try:
        client = _client(dry_run=dry_run, raise_on_error=raise_on_error)
        result = client.get_vm_ip_addresses(vm)
        interfaces = parse_guest_net_properties(result.stdout)
        data: dict = {"vm": vm, "interfaces": interfaces}
        if dry_run:
            data["debug"] = result.to_dict()
        return _ok(data)
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
        if payload.machinereadable:
            parsed = parse_showvminfo(result.stdout)
        else:
            parsed = {"raw_text": result.stdout}
        data: dict = {"info": parsed}
        if payload.dry_run:
            data["debug"] = result.to_dict()
        return _ok(data)
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
        return _ok(_action_response(result, dry_run=payload.dry_run))
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
        return _ok(_action_response(result, dry_run=payload.dry_run))
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
        return _ok(_action_response(result, dry_run=payload.dry_run))
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
        return _ok(_action_response(result, dry_run=payload.dry_run))
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
        return _ok(_action_response(result, dry_run=payload.dry_run))
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
        return _ok(_action_response(result, dry_run=payload.dry_run))
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
        return _ok(_action_response(result, dry_run=payload.dry_run))
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
        return _ok(_action_response(result, dry_run=payload.dry_run))
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
        return _ok(_action_response(result, dry_run=payload.dry_run))
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
        return _ok(_action_response(result, dry_run=payload.dry_run))
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )


# ─── Live VM screenshot ─────────────────────────────────────────────────

# Reusable temp file for the live screenshot (avoids creating many temp files)
_SCREEN_TMP = os.path.join(tempfile.gettempdir(), "isolens_live_screen.png")


@router.get("/screen")
def vm_live_screenshot(vm: str = "WindowsSandbox"):
    """Capture and serve a live PNG screenshot of the VM display.

    Returns the raw PNG image with proper content-type headers and
    cache-control to prevent stale frames.
    """
    try:
        client = _client(dry_run=False, raise_on_error=True)
        result = client.screenshot_vm(vm, _SCREEN_TMP)
        if result.returncode != 0:
            return JSONResponse(
                status_code=500,
                content=_error(
                    "Screenshot failed",
                    result.stderr.strip() or result.stdout.strip(),
                ).model_dump(),
            )
        if not os.path.isfile(_SCREEN_TMP):
            return JSONResponse(
                status_code=500,
                content=_error("Screenshot file not created").model_dump(),
            )
        return FileResponse(
            _SCREEN_TMP,
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=_error("VBoxManage failed", str(exc)).model_dump(),
        )
