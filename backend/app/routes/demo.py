"""Demo scene endpoints for jury rehearsals."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.analysis import AnalysisLanguage, AnalysisSource, AnalyzeResponse
from app.services.fallback_service import DEMO_RESPONSES, get_demo_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get(
    "/scene/{scene_id}",
    response_model=AnalyzeResponse,
    summary="Get a curated demo analysis response",
)
async def get_demo_scene(
    scene_id: str,
    source: AnalysisSource = Query(
        default=AnalysisSource.MOBILE,
        description="Frame source label returned to clients.",
    ),
    langue: AnalysisLanguage = Query(
        default="en",
        description="Language for the demo analysis text.",
    ),
) -> AnalyzeResponse:
    """
    Return a deterministic demo analysis for rehearsals.

    Use ``scene_id=random`` to sample one of the curated scenes.
    """
    if not scene_id or len(scene_id) > 64:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid scene_id",
        )

    if scene_id != "random" and scene_id not in DEMO_RESPONSES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown demo scene: {scene_id}",
        )

    try:
        response = get_demo_response(scene_id, source=source, langue=langue)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown demo scene: {exc.args[0]}",
        ) from exc

    logger.info(
        "demo_scene_served",
        extra={
            "scene_id": scene_id,
            "urgence": response.urgence.value,
            "source": response.source.value,
        },
    )
    return response
