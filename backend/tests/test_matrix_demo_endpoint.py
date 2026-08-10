"""API tests for the Cognera matrix demo endpoint."""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_matrix_demo_endpoint_returns_playable_puzzle() -> None:
    client = TestClient(app)
    response = client.get("/matrix/demo")

    assert response.status_code == 200
    payload = response.json()

    assert payload["missing"] == [2, 2]
    assert len(payload["grid"]) == 3
    assert len(payload["grid"][0]) == 3
    assert payload["grid"][2][2] is None
    assert len(payload["options"]) == 6
    assert isinstance(payload["correct"], int)
    assert 0 <= payload["correct"] < len(payload["options"])
    assert "explanation" in payload
    assert "skills" in payload
    assert "difficulty" in payload
    assert "difficulty_profile" in payload
    assert payload["skills"]["MENTAL_ROTATION"] == 0.95
    assert payload["skills"]["VISUAL_PATTERN_RECOGNITION"] == 0.8


def test_matrix_demo_endpoint_is_deterministic() -> None:
    client = TestClient(app)
    first = client.get("/matrix/demo").json()
    second = client.get("/matrix/demo").json()

    assert first == second
