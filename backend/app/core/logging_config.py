"""Structured logging setup for development and production."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.config import Settings


class _JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in payload:
                continue
            if key in ("msg", "args", "levelname", "levelno", "pathname", "filename"):
                continue
            if key in ("module", "funcName", "created", "msecs", "relativeCreated"):
                continue
            if key in ("thread", "threadName", "processName", "process", "exc_info"):
                continue
            if key in ("exc_text", "stack_info", "lineno", "name", "message"):
                continue
            payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings) -> None:
    """Configure root logger: human-readable in dev, JSON in production."""
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    use_json = settings.app_env.lower() in ("production", "prod")
    if use_json:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)
    handler.setLevel(level)
    root.addHandler(handler)
