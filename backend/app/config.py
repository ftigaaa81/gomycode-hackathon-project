"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Central configuration; only this module reads process environment."""

    model_config = SettingsConfigDict(
        env_file=(
            _BACKEND_ROOT / ".env",
            _REPO_ROOT / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", description="Runtime environment name.")
    log_level: str = Field(default="INFO", description="Root log level.")

    gemini_api_key: str = Field(default="", description="Google Gemini API key.")
    captor_api_key: str = Field(
        default="",
        description="Shared secret for Raspberry Pi captor clients.",
    )
    demo_root: Path = Field(
        default=_REPO_ROOT / "demo",
        description="Path to demo scenes and expected responses.",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
