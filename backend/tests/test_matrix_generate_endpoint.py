"""API tests for the vertical-slice matrix generation endpoint."""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_matrix_generate_endpoint_returns_vertical_slice_payload() -> None:
    client = TestClient(app)
    response = client.post("/api/matrix/generate", json={"seed": 123})

    assert response.status_code == 200
    payload = response.json()

    assert payload["seed"] == 123
    assert len(payload["grid"]) == 3
    assert len(payload["grid"][0]) == 3
    assert payload["grid"][2][2] is None
    assert payload["missing_position"] == [2, 2]
    assert len(payload["options"]) == 4
    assert 0 <= payload["correct_index"] < 4
    assert payload["options"][payload["correct_index"]]["is_correct"] is True
    assert all(option["label"] in {"A", "B", "C", "D"} for option in payload["options"])
    assert "explanation" in payload
    assert isinstance(payload["difficulty"], float)
    assert payload["difficulty_profile"]["overall"] == payload["difficulty"]


def test_matrix_generate_endpoint_is_deterministic_for_seed() -> None:
    client = TestClient(app)

    first = client.post("/api/matrix/generate", json={"seed": 2024}).json()
    second = client.post("/api/matrix/generate", json={"seed": 2024}).json()

    assert first == second


def test_legacy_matrix_generate_endpoint_still_works() -> None:
    client = TestClient(app)

    response = client.post("/matrix/generate", json={"seed": 321})

    assert response.status_code == 200
    assert response.json()["seed"] == 321