"""Pydantic models for vision analysis requests and responses."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class UrgenceLevel(str, Enum):
    """Priority tier returned by the vision model."""

    DANGER = "danger"
    ATTENTION = "attention"
    NORMAL = "normal"


class AnalysisSource(str, Enum):
    """Origin of the frame being analyzed."""

    CAPTOR = "captor"
    MOBILE = "mobile"


AnalysisLanguage = Literal["ar", "en"]


class NvidiaAnalysisPayload(BaseModel):
    """Strict JSON shape expected from the NVIDIA model."""

    urgence: UrgenceLevel = Field(description="Safety priority tier.")
    message_court: str = Field(
        max_length=120,
        description="Short spoken message, about 10 words.",
    )
    objet_principal: str = Field(description="Main object detected in the scene.")
    texte_detecte: str | None = Field(
        default=None,
        description="OCR text if readable, otherwise null.",
    )


class AnalyzeRequest(BaseModel):
    """Incoming analyze request (JSON body with base64 image)."""

    image_base64: str = Field(
        min_length=16,
        description="Base64-encoded image bytes (JPEG or PNG).",
    )
    source: AnalysisSource = Field(
        description="Whether the image came from a Pi captor or the mobile app.",
    )
    captor_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Required when source is captor.",
    )
    langue: AnalysisLanguage = Field(
        default="en",
        description="Language for generated analysis text.",
    )

    @model_validator(mode="after")
    def captor_id_required_for_captor(self) -> "AnalyzeRequest":
        """Ensure captor_id is present for captor-sourced frames."""
        if self.source == AnalysisSource.CAPTOR and not self.captor_id:
            raise ValueError("captor_id is required when source is captor")
        return self


class OnDemandAnalyzeRequest(BaseModel):
    """Mobile on-demand capture: source is always mobile."""

    image_base64: str = Field(
        min_length=16,
        description="Base64-encoded image from the mobile camera.",
    )
    langue: AnalysisLanguage = Field(
        default="en",
        description="Language for generated analysis text.",
    )


class AnalyzeResponse(BaseModel):
    """Typed API response for all analyze endpoints."""

    urgence: UrgenceLevel = Field(description="Priority tier for voice output.")
    message_court: str = Field(description="Short message to speak.")
    objet_principal: str = Field(description="Primary object in the scene.")
    texte_detecte: str | None = Field(description="Detected text or null.")
    source: AnalysisSource = Field(
        description="Origin of the analyzed frame (captor or mobile).",
    )
    used_fallback: bool = Field(
        default=False,
        description="True when NVIDIA failed and a safe fallback was returned.",
    )


class HealthResponse(BaseModel):
    """Health check payload."""

    status: Literal["ok"] = "ok"


class DemoSceneResponse(BaseModel):
    """Demo scene metadata and optional expected analysis."""

    scene_id: str = Field(description="Scene identifier.")
    image_available: bool = Field(description="Whether an image file exists on disk.")
    expected: dict | None = Field(
        default=None,
        description="Expected analysis from demo/expected_responses.json if present.",
    )
