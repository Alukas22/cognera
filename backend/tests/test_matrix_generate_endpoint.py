"""API tests for the matrix generation endpoint."""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_matrix_generate_endpoint_returns_full_six_option_payload() -> None:
    client = TestClient(app)
    response = client.post("/api/matrix/generate", json={"seed": 123})

    assert response.status_code == 200
    payload = response.json()

    assert payload["seed"] == 123
    assert len(payload["grid"]) == 3
    assert len(payload["grid"][0]) == 3
    assert payload["grid"][2][2] is None
    assert payload["missing_position"] == [2, 2]
    assert len(payload["options"]) == 6
    assert 0 <= payload["correct_index"] < 6
    assert payload["options"][payload["correct_index"]]["is_correct"] is True
    assert all(option["label"] in {"A", "B", "C", "D", "E", "F"} for option in payload["options"])
    assert "explanation" in payload
    assert isinstance(payload["difficulty"], float)
    assert payload["difficulty_profile"]["overall"] == payload["difficulty"]


def test_matrix_generate_endpoint_localizes_swedish_explanation() -> None:
    client = TestClient(app)

    payload = client.post("/api/matrix/generate", json={"seed": 123, "language": "sv"}).json()

    explanation = payload["explanation"]

    for section in [
        "Översikt",
        "Steg 1",
        "Steg 2",
        "Kontroll",
        "Rätt svar",
        "Alternativ A",
        "Alternativ B",
        "Alternativ C",
        "Alternativ D",
        "Alternativ E",
        "Alternativ F",
    ]:
        assert section in explanation

    assert "Rule 1" not in explanation
    assert "Vad händer i raderna?" in explanation
    assert "Vad händer i kolumnerna?" in explanation
    assert "Varför är detta korrekt?" in explanation
    assert explanation.count("\n-") >= 11

    forbidden_words = ["blå", "röd", "grön", "gul", "orange", "lila", "färg", "färgen"]
    assert not any(word in explanation.lower() for word in forbidden_words)


def test_matrix_generate_endpoint_is_deterministic_for_seed() -> None:
    client = TestClient(app)

    first = client.post("/api/matrix/generate", json={"seed": 2024}).json()
    second = client.post("/api/matrix/generate", json={"seed": 2024}).json()

    assert first == second


def test_matrix_generate_endpoint_supports_beginner_target_difficulty() -> None:
    client = TestClient(app)

    payload = client.post(
        "/api/matrix/generate",
        json={"seed": 123, "language": "sv", "target_difficulty": 0.14, "puzzle_number": 1},
    ).json()

    assert 0.06 <= payload["difficulty"] <= 0.22
    assert "raw_difficulty" in payload
    assert payload["difficulty"] != payload["raw_difficulty"]


def test_legacy_matrix_generate_endpoint_still_works() -> None:
    client = TestClient(app)

    response = client.post("/matrix/generate", json={"seed": 321})

    assert response.status_code == 200
    assert response.json()["seed"] == 321