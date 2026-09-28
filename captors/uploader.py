# Ce module envoie chaque frame du Raspberry Pi vers POST /api/analyze du backend.
# C'est le maillon physique du pipeline EyE C : captor (Pi) → backend/captor_service.py
# → nvidia_service.py (NVIDIA Build).

"""HTTP client to upload captor frames to the EyE C backend."""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from config import CaptorSettings

logger = logging.getLogger(__name__)

UPLOAD_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class UploadResult:
    """Outcome of a single upload attempt."""

    ok: bool
    status_code: int | None = None
    detail: str | None = None
    response_json: dict[str, Any] | None = None


class FrameUploader:
    """Posts JPEG frames to the backend analyze endpoint."""

    def __init__(self, settings: CaptorSettings) -> None:
        self._settings = settings
        self._analyze_url = f"{str(settings.backend_url).rstrip('/')}/api/analyze"

    def upload_frame(self, frame_jpeg: bytes) -> UploadResult:
        """
        Send one frame to the backend.

        Network failures are logged and surfaced as UploadResult(ok=False) without raising.
        """
        image_b64 = base64.standard_b64encode(frame_jpeg).decode("ascii")
        payload = {
            "image_base64": image_b64,
            "source": "captor",
            "captor_id": self._settings.captor_id,
        }
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._settings.captor_api_key:
            headers["X-Captor-API-Key"] = self._settings.captor_api_key

        try:
            with httpx.Client(timeout=UPLOAD_TIMEOUT_SECONDS) as client:
                response = client.post(self._analyze_url, json=payload, headers=headers)
        except httpx.TimeoutException:
            logger.error(
                "upload_timeout",
                extra={"url": self._analyze_url, "captor_id": self._settings.captor_id},
            )
            return UploadResult(ok=False, detail="timeout")
        except httpx.TransportError as exc:
            logger.error(
                "upload_network_error",
                extra={
                    "url": self._analyze_url,
                    "captor_id": self._settings.captor_id,
                    "error": type(exc).__name__,
                },
            )
            return UploadResult(ok=False, detail=str(exc))

        if response.status_code >= 400:
            logger.error(
                "upload_http_error",
                extra={
                    "status_code": response.status_code,
                    "body": response.text[:300],
                },
            )
            return UploadResult(
                ok=False,
                status_code=response.status_code,
                detail=response.text[:300],
            )

        try:
            body = response.json()
        except ValueError:
            logger.error("upload_invalid_json_response")
            return UploadResult(ok=False, status_code=response.status_code, detail="invalid json")

        logger.info(
            "upload_ok",
            extra={
                "captor_id": self._settings.captor_id,
                "urgence": body.get("urgence"),
                "used_fallback": body.get("used_fallback"),
            },
        )
        return UploadResult(ok=True, status_code=response.status_code, response_json=body)
