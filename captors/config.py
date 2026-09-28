"""Captor configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

_CAPTORS_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _CAPTORS_ROOT.parent


class CaptorSettings(BaseSettings):
    """Settings for the Raspberry Pi captor client."""

    model_config = SettingsConfigDict(
        env_file=(
            _CAPTORS_ROOT / ".env",
            _REPO_ROOT / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_url: HttpUrl = Field(
        description="Base URL of the EyE C backend (e.g. http://192.168.1.10:8000).",
    )
    captor_api_key: str = Field(
        default="",
        description="Shared secret sent as X-Captor-API-Key.",
    )
    captor_id: str = Field(
        min_length=1,
        max_length=64,
        description="Unique identifier for this Raspberry Pi device.",
    )
    use_mock_camera: bool = Field(
        default=False,
        description="Use synthetic frames when picamera2 is unavailable (dev/CI).",
    )
    camera_width: int = Field(default=640, ge=320, le=1920)
    camera_height: int = Field(default=480, ge=240, le=1080)
    jpeg_quality: int = Field(default=85, ge=50, le=95)


@lru_cache
def get_settings() -> CaptorSettings:
    """Return cached settings."""
    return CaptorSettings()
