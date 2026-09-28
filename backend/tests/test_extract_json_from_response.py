"""Tests for NVIDIA model JSON extraction."""

import json

import pytest

from app.services.nvidia_service import (
    NvidiaServiceError,
    _normalize_model_payload,
    extract_json_from_response,
)


def test_extract_json_plain_object() -> None:
    """Direct JSON string parses unchanged."""
    raw = '{"urgence": "normal", "message_court": "ok", "objet_principal": "table"}'
    assert extract_json_from_response(raw)["urgence"] == "normal"


def test_extract_json_with_natural_language_wrapper() -> None:
    """Preamble and suffix around JSON are ignored."""
    raw = (
        "Voici l'analyse : {\"urgence\": \"attention\", "
        '"message_court": "Chaise devant", "objet_principal": "chaise"} merci.'
    )
    parsed = extract_json_from_response(raw)
    assert parsed["urgence"] == "attention"
    assert parsed["objet_principal"] == "chaise"


def test_extract_json_from_markdown_fence() -> None:
    """Markdown code fences are stripped before parsing."""
    raw = """```json
{"urgence": "danger", "message_court": "Stop", "objet_principal": "voiture"}
```"""
    assert extract_json_from_response(raw)["urgence"] == "danger"


def test_extract_json_raises_when_no_object() -> None:
    """Missing JSON object raises JSONDecodeError."""
    with pytest.raises(json.JSONDecodeError):
        extract_json_from_response("Aucune analyse disponible.")


def test_normalize_missing_required_keys_raises_service_error() -> None:
    """Missing urgence or message_court becomes NvidiaServiceError."""
    with pytest.raises(NvidiaServiceError):
        _normalize_model_payload({"urgence": "normal"})

    with pytest.raises(NvidiaServiceError):
        _normalize_model_payload({"message_court": "hello"})


def test_normalize_invalid_urgence_coerced_to_normal() -> None:
    """Unknown urgency values are forced to normal."""
    result = _normalize_model_payload(
        {
            "urgence": "critique",
            "message_court": "test",
            "objet_principal": "objet",
        }
    )
    assert result["urgence"] == "normal"
