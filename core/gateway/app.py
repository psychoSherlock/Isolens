"""FastAPI gateway for IsoLens controller operations."""

from __future__ import annotations

from fastapi import FastAPI

from core.gateway.controller_routes import router as controller_router
from core.gateway.system_routes import router as system_router
from core.gateway.version import VERSION

app = FastAPI(title="IsoLens Gateway", version=VERSION)
app.include_router(system_router)
app.include_router(controller_router)
