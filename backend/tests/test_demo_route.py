"""Tests for demo scene API route."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_scene_random_returns_analyze_shape() -> None:
    """GET /api/demo/scene/random returns AnalyzeResponse fields."""
    response = client.get("/api/demo/scene/random")
    assert response.status_code == 200
    body = response.json()
    assert body["urgence"] in {"danger", "attention", "normal"}
    assert "message_court" in body
    assert body["source"] == "mobile"


def test_demo_scene_known_id() -> None:
    """Known demo scene is deterministic."""
    response = client.get("/api/demo/scene/escalier_danger")
    assert response.status_code == 200
    assert response.json()["urgence"] == "danger"


def test_demo_scene_unknown_404() -> None:
    """Unknown demo scene returns 404."""
    response = client.get("/api/demo/scene/not-a-scene")
    assert response.status_code == 404
