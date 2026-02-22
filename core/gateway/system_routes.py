"""System-level API routes."""

from __future__ import annotations

from fastapi import APIRouter

from core.gateway.api_models import StandardResponse
from core.gateway.version import VERSION

router = APIRouter(prefix="/api", tags=["system"])


def _ok(data: dict) -> StandardResponse:
    return StandardResponse(status="ok", data=data, error=None)


@router.get("/ping", response_model=StandardResponse)
def ping() -> StandardResponse:
    return _ok({"message": "pong"})


@router.get("/version", response_model=StandardResponse)
def version() -> StandardResponse:
    return _ok({"version": VERSION})
