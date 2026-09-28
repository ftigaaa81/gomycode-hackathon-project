"""Validation and routing of frames from Raspberry Pi captors."""

from __future__ import annotations

import base64
import binascii
import logging
import re

from app.schemas.analysis import AnalysisLanguage, AnalysisSource, NvidiaAnalysisPayload
from app.services.nvidia_service import NvidiaVisionService, get_nvidia_service

logger = logging.getLogger(__name__)

MIN_FRAME_BYTES = 512
MAX_FRAME_BYTES = 5 * 1024 * 1024
CAPTOR_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _decode_frame(image_base64: str) -> bytes:
    """Decode and validate base64 image payload."""
    try:
        frame_bytes = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 image data") from exc

    if len(frame_bytes) < MIN_FRAME_BYTES:
        raise ValueError("Image too small to be a valid frame")
    if len(frame_bytes) > MAX_FRAME_BYTES:
        raise ValueError("Image exceeds maximum allowed size")

    if not (
        frame_bytes.startswith(JPEG_MAGIC) or frame_bytes.startswith(PNG_MAGIC)
    ):
        raise ValueError("Unsupported image format; expected JPEG or PNG")

    return frame_bytes


def _validate_captor_id(captor_id: str) -> None:
    """Ensure captor identifier matches expected pattern."""
    if not CAPTOR_ID_PATTERN.match(captor_id):
        raise ValueError("Invalid captor_id format")


async def handle_captor_frame(
    frame_bytes: bytes,
    captor_id: str,
    *,
    nvidia_service: NvidiaVisionService | None = None,
    langue: AnalysisLanguage = "en",
) -> NvidiaAnalysisPayload:
    """
    Validate a captor frame and forward it to NVIDIA for analysis.

    This function is the explicit bridge between the physical Raspberry Pi captor
    and the NVIDIA vision model.
    """
    if len(frame_bytes) < MIN_FRAME_BYTES:
        raise ValueError("Frame too small")
    if len(frame_bytes) > MAX_FRAME_BYTES:
        raise ValueError("Frame exceeds maximum size")
    if not (
        frame_bytes.startswith(JPEG_MAGIC) or frame_bytes.startswith(PNG_MAGIC)
    ):
        raise ValueError("Unsupported frame format")

    _validate_captor_id(captor_id)

    service = nvidia_service or get_nvidia_service()
    logger.info(
        "captor_frame_received",
        extra={"captor_id": captor_id, "frame_bytes": len(frame_bytes)},
    )
    return await service.analyze_frame(
        frame_bytes,
        source=AnalysisSource.CAPTOR,
        captor_id=captor_id,
        langue=langue,
    )


async def handle_captor_frame_base64(
    image_base64: str,
    captor_id: str,
    *,
    nvidia_service: NvidiaVisionService | None = None,
    langue: AnalysisLanguage = "en",
) -> NvidiaAnalysisPayload:
    """Decode base64 captor payload then run handle_captor_frame."""
    frame_bytes = _decode_frame(image_base64)
    return await handle_captor_frame(
        frame_bytes,
        captor_id,
        nvidia_service=nvidia_service,
        langue=langue,
    )
