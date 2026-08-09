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
    assert len(payload["options"]) == 4
    assert isinstance(payload["correct"], int)
    assert payload["correct"] == 1
    assert "explanation" in payload


def test_matrix_demo_endpoint_is_deterministic() -> None:
    client = TestClient(app)
    first = client.get("/matrix/demo").json()
    second = client.get("/matrix/demo").json()

    assert first == second
