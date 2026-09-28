"""Unit tests for fallback_service."""

import pytest

from app.schemas.analysis import AnalysisSource, UrgenceLevel
from app.services.fallback_service import (
    DEMO_RESPONSES,
    build_fallback_response,
    get_demo_response,
)


def test_fallback_marks_used_fallback() -> None:
    """Fallback responses are explicitly flagged."""
    response = build_fallback_response(AnalysisSource.CAPTOR)
    assert response.used_fallback is True
    assert response.source == AnalysisSource.CAPTOR


def test_fallback_is_conservative() -> None:
    """Fallback uses attention urgency and no invented OCR."""
    response = build_fallback_response(AnalysisSource.MOBILE)
    assert response.urgence == UrgenceLevel.ATTENTION
    assert response.texte_detecte is None
    assert response.objet_principal == "inconnu"
    assert len(response.message_court) > 0


def test_demo_responses_contains_five_scenes() -> None:
    """Curated demo catalogue covers jury scenarios."""
    assert len(DEMO_RESPONSES) == 5
    assert "escalier_danger" in DEMO_RESPONSES
    assert "vehicule_proche" in DEMO_RESPONSES


def test_get_demo_response_known_scene() -> None:
    """Known scene id returns typed AnalyzeResponse."""
    response = get_demo_response("panneau_texte", source=AnalysisSource.MOBILE)
    assert response.urgence == UrgenceLevel.ATTENTION
    assert response.texte_detecte == "SORTIE"
    assert response.used_fallback is False


def test_get_demo_response_random() -> None:
    """Random scene id resolves to one of the curated templates."""
    response = get_demo_response("random", source=AnalysisSource.CAPTOR)
    assert response.source == AnalysisSource.CAPTOR
    assert response.urgence in (
        UrgenceLevel.DANGER,
        UrgenceLevel.ATTENTION,
        UrgenceLevel.NORMAL,
    )


def test_get_demo_response_unknown_raises() -> None:
    """Unknown ids raise KeyError for route layer to map to HTTP 404."""
    with pytest.raises(KeyError):
        get_demo_response("scene_inconnue")
