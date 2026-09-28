"""Google Gemini vision client for frame analysis."""

from __future__ import annotations

import asyncio
from io import BytesIO
import json
import logging
import re
import time
from typing import Any

import google.generativeai as genai
from PIL import Image, ImageOps
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.schemas.analysis import (
    AnalysisLanguage,
    AnalysisSource,
    NvidiaAnalysisPayload,
    UrgenceLevel,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Tu es EyE C, un assistant vocal pour une personne malvoyante. Analyse cette image de sa "
    "caméra. Cherche en priorité : véhicules (voiture, vélo, moto, bus) en mouvement ou "
    "approchant, obstacles au sol (marches, trous, objets bas), panneaux ou texte visible, "
    "personnes proches. Si un véhicule est visible même partiellement ou flou, mentionne-le "
    "comme objet_principal. Réponds UNIQUEMENT en JSON valide avec les clés : urgence "
    "(danger|attention|normal), message_court (10 mots max), objet_principal, texte_detecte "
    "(ou null). Priorité absolue : sécurité physique immédiate. Ne décris qu'une seule chose "
    "à la fois. Sois bref."
)
SYSTEM_PROMPT_AR = (
    "أنت EyE C، مساعد صوتي لشخص ضعيف البصر. حلل هذه الصورة من كاميرته. ابحث أولاً عن: "
    "المركبات القريبة أو المتحركة، العوائق الأرضية (درجات، حفر، أشياء منخفضة)، اللافتات أو "
    "النصوص المرئية، الأشخاص القريبين. أجب فقط بصيغة JSON صالحة بالمفاتيح التالية: urgence "
    "(danger|attention|normal)، message_court (10 كلمات كحد أقصى، بالعربية الفصحى)، "
    "objet_principal، texte_detecte (أو null). الأولوية القصوى: السلامة الجسدية الفورية. "
    "صف شيئاً واحداً فقط في كل مرة. كن مختصراً."
)

REQUEST_TIMEOUT_SECONDS = 4.0
RETRY_BACKOFF_SECONDS = 0.25
MAX_ATTEMPTS = 2

_ALLOWED_URGENCE = {level.value for level in UrgenceLevel}


class NvidiaServiceError(Exception):
    """Raised when the Gemini API fails after retries."""


def extract_json_from_response(text: str) -> dict[str, Any]:
    """
    Isolate and parse a JSON object from model output.

    Tolerates markdown fences and natural-language wrappers such as
    ``Voici l'analyse : {...}``.
    """
    stripped = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", stripped, re.IGNORECASE)
    if fence_match:
        stripped = fence_match.group(1).strip()

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    object_match = re.search(r"\{[\s\S]*\}", stripped)
    if not object_match:
        raise json.JSONDecodeError("No JSON object found in model response", stripped, 0)

    parsed = json.loads(object_match.group(0))
    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("Expected a JSON object", object_match.group(0), 0)
    return parsed


def _normalize_model_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate required keys and coerce unsafe urgency values."""
    if "urgence" not in raw or "message_court" not in raw:
        raise NvidiaServiceError(
            "Gemini JSON missing required keys: urgence, message_court",
        )

    data = dict(raw)
    urgence_raw = data["urgence"]
    urgence = urgence_raw.strip().lower() if isinstance(urgence_raw, str) else urgence_raw
    if urgence not in _ALLOWED_URGENCE:
        logger.warning(
            "gemini_invalid_urgence_coerced",
            extra={"received": urgence_raw, "coerced_to": UrgenceLevel.NORMAL.value},
        )
        data["urgence"] = UrgenceLevel.NORMAL.value
    else:
        data["urgence"] = urgence

    return data


def _prepare_image(frame_bytes: bytes) -> bytes:
    """Resize an image to at most 768px and encode it as JPEG quality 70."""
    with Image.open(BytesIO(frame_bytes)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((768, 768), Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format="JPEG", quality=70)
    return output.getvalue()


class NvidiaVisionService:
    """Client wrapper for Gemini vision inference."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def analyze_frame(
        self,
        frame_bytes: bytes,
        *,
        source: AnalysisSource,
        captor_id: str | None = None,
        langue: AnalysisLanguage = "en",
    ) -> NvidiaAnalysisPayload:
        """Send a frame to Gemini and return a validated analysis payload."""
        if not self._settings.gemini_api_key:
            raise NvidiaServiceError("Gemini API key not configured")

        try:
            image_bytes = _prepare_image(frame_bytes)
        except Exception as exc:
            raise NvidiaServiceError("Failed to prepare image for Gemini") from exc

        source_hint = f"source={source.value}"
        if captor_id:
            source_hint += f", captor_id={captor_id}"

        try:
            genai.configure(api_key=self._settings.gemini_api_key)
            model = genai.GenerativeModel(
                "gemini-2.0-flash-lite",
                system_instruction=(
                    SYSTEM_PROMPT_AR if langue == "ar" else SYSTEM_PROMPT
                ),
                generation_config={
                    "max_output_tokens": 80,
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "OBJECT",
                        "properties": {
                            "urgence": {
                                "type": "STRING",
                                "enum": ["danger", "attention", "normal"],
                            },
                            "message_court": {"type": "STRING"},
                            "objet_principal": {"type": "STRING"},
                            "texte_detecte": {
                                "type": "STRING",
                                "nullable": True,
                            },
                        },
                        "required": [
                            "urgence",
                            "message_court",
                            "objet_principal",
                            "texte_detecte",
                        ],
                    },
                    "temperature": 0,
                },
            )
        except Exception as exc:
            raise NvidiaServiceError("Failed to configure Gemini client") from exc

        request_parts = [
            (
                f"حلل هذه الصورة ({source_hint})."
                if langue == "ar"
                else f"Analyse cette image ({source_hint})."
            ),
            {"mime_type": "image/jpeg", "data": image_bytes},
        ]

        last_error: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            started = time.perf_counter()
            try:
                response = await asyncio.to_thread(
                    model.generate_content,
                    request_parts,
                    request_options={"timeout": REQUEST_TIMEOUT_SECONDS},
                )
                duration_ms = (time.perf_counter() - started) * 1000

                payload = self._parse_response(response.text)
                logger.info(
                    "gemini_call_ok",
                    extra={
                        "attempt": attempt,
                        "duration_ms": round(duration_ms, 2),
                        "success": True,
                        "urgence": payload.urgence.value,
                    },
                )
                return payload

            except Exception as exc:
                duration_ms = (time.perf_counter() - started) * 1000
                last_error = exc
                logger.warning(
                    "gemini_call_failed",
                    extra={
                        "attempt": attempt,
                        "duration_ms": round(duration_ms, 2),
                        "success": False,
                        "error_type": type(exc).__name__,
                    },
                )
                if attempt < MAX_ATTEMPTS:
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS)
                    continue
                if isinstance(exc, NvidiaServiceError):
                    raise
                raise NvidiaServiceError("Gemini request failed or timed out") from exc

        raise NvidiaServiceError("Gemini request failed") from last_error

    def _parse_response(self, content: str) -> NvidiaAnalysisPayload:
        """Extract and validate JSON returned by Gemini."""
        if not isinstance(content, str):
            raise NvidiaServiceError("Gemini response missing text content")
        try:
            parsed = extract_json_from_response(content)
            normalized = _normalize_model_payload(parsed)
            return NvidiaAnalysisPayload.model_validate(normalized)
        except json.JSONDecodeError as exc:
            raise NvidiaServiceError("Failed to extract JSON from Gemini content") from exc
        except ValidationError as exc:
            raise NvidiaServiceError("Gemini JSON failed schema validation") from exc


_nvidia_service: NvidiaVisionService | None = None


def get_nvidia_service() -> NvidiaVisionService:
    """Return singleton NVIDIA service."""
    global _nvidia_service
    if _nvidia_service is None:
        _nvidia_service = NvidiaVisionService()
    return _nvidia_service
