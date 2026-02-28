"""FastAPI gateway for IsoLens controller operations."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.gateway.analysis_routes import router as analysis_router
from core.gateway.controller_routes import router as controller_router
from core.gateway.system_routes import router as system_router
from core.gateway.version import VERSION

app = FastAPI(title="IsoLens Gateway", version=VERSION)

# Allow the Next.js dev server (and any localhost origin) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(controller_router)
app.include_router(analysis_router)
