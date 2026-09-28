"""Vision analysis endpoints."""

from __future__ import annotations

import base64
import binascii
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config import Settings, get_settings
from app.schemas.analysis import (
    AnalysisSource,
    AnalysisLanguage,
    AnalyzeRequest,
    AnalyzeResponse,
    NvidiaAnalysisPayload,
    OnDemandAnalyzeRequest,
)
from app.services import captor_service
from app.services.fallback_service import build_fallback_response
from app.services.nvidia_service import NvidiaServiceError, get_nvidia_service
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analyze"])


def _to_response(
    payload: NvidiaAnalysisPayload,
    source: AnalysisSource,
    *,
    used_fallback: bool = False,
) -> AnalyzeResponse:
    """Map NVIDIA payload to API response."""
    return AnalyzeResponse(
        urgence=payload.urgence,
        message_court=payload.message_court,
        objet_principal=payload.objet_principal,
        texte_detecte=payload.texte_detecte,
        source=source,
        used_fallback=used_fallback,
    )


def _verify_captor_api_key(
    settings: Settings,
    x_captor_api_key: str | None,
    source: AnalysisSource,
) -> None:
    """Validate captor shared secret when configured."""
    if source != AnalysisSource.CAPTOR:
        return
    if not settings.captor_api_key:
        return
    if x_captor_api_key != settings.captor_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid captor API key",
        )


async def _run_analysis(
    image_base64: str,
    source: AnalysisSource,
    captor_id: str | None,
    langue: AnalysisLanguage = "en",
) -> AnalyzeResponse:
    """Run NVIDIA analysis with automatic fallback on service errors."""
    try:
        if source == AnalysisSource.CAPTOR:
            assert captor_id is not None
            payload = await captor_service.handle_captor_frame_base64(
                image_base64,
                captor_id,
                langue=langue,
            )
        else:
            try:
                frame_bytes = base64.b64decode(image_base64, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid base64 image data",
                ) from exc
            payload = await get_nvidia_service().analyze_frame(
                frame_bytes,
                source=AnalysisSource.MOBILE,
                langue=langue,
            )
        return _to_response(payload, source)
    except NvidiaServiceError as exc:
        logger.warning(
            "analysis_fallback",
            extra={"source": source.value, "reason": str(exc)[:200]},
        )
        return build_fallback_response(source, langue)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze a frame from captor or mobile",
)
async def analyze_frame(
    body: AnalyzeRequest,
    settings: Settings = Depends(get_settings),
    x_captor_api_key: str | None = Header(default=None, alias="X-Captor-API-Key"),
) -> AnalyzeResponse:
    """Analyze an image; captor frames are validated then forwarded to NVIDIA."""
    _verify_captor_api_key(settings, x_captor_api_key, body.source)
    try:
        return await _run_analysis(
            body.image_base64,
            body.source,
            body.captor_id,
            body.langue,
        )
    except NvidiaServiceError as exc:
        logger.warning(
            "analyze_route_fallback",
            extra={"source": body.source.value, "reason": str(exc)[:200]},
        )
        return build_fallback_response(body.source, body.langue)


@router.post(
    "/analyze/on-demand",
    response_model=AnalyzeResponse,
    summary="On-demand mobile camera analysis",
)
async def analyze_on_demand(body: OnDemandAnalyzeRequest) -> AnalyzeResponse:
    """Analyze a single mobile capture (source is always mobile)."""
    try:
        return await _run_analysis(
            body.image_base64,
            AnalysisSource.MOBILE,
            captor_id=None,
            langue=body.langue,
        )
    except NvidiaServiceError as exc:
        logger.warning(
            "analyze_on_demand_fallback",
            extra={"reason": str(exc)[:200]},
        )
        return build_fallback_response(AnalysisSource.MOBILE, body.langue)
