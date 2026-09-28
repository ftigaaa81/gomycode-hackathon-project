"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.logging_config import configure_logging
from app.routes import analyze, demo
from app.schemas.analysis import HealthResponse
from app.services.fallback_service import build_fallback_response
from app.services.nvidia_service import NvidiaServiceError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Configure logging on startup."""
    settings = get_settings()
    configure_logging(settings)
    logger.info("backend_started", extra={"app_env": settings.app_env})
    yield


app = FastAPI(
    title="EyE C Backend",
    description="API for EyE C — vocal assistant for visually impaired users.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(demo.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """Simple liveness probe for demo rehearsals."""
    return HealthResponse()


@app.exception_handler(NvidiaServiceError)
async def nvidia_service_error_handler(
    request: Request,
    exc: NvidiaServiceError,
) -> JSONResponse:
    """
    Central fallback for uncaught NVIDIA failures on analyze paths.

    Routes should catch NvidiaServiceError first; this handler avoids raw 500s
    if a handler regresses.
    """
    logger.warning(
        "nvidia_exception_handler",
        extra={"path": request.url.path, "reason": str(exc)[:200]},
    )
    if request.url.path.startswith("/api/analyze"):
        payload = build_fallback_response(source=_source_from_request(request))
        return JSONResponse(
            status_code=200,
            content=payload.model_dump(mode="json"),
        )
    return JSONResponse(
        status_code=503,
        content={"detail": "Vision service temporarily unavailable"},
    )


def _source_from_request(request: Request) -> "AnalysisSource":
    from app.schemas.analysis import AnalysisSource

    if "on-demand" in request.url.path:
        return AnalysisSource.MOBILE
    return AnalysisSource.MOBILE

