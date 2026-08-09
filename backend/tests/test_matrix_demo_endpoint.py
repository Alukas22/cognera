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
    assert isinstance(payload["correct_index"], int)
    assert payload["correct"] == payload["correct_index"]
    assert payload["options"][payload["correct_index"]]["is_correct"] is True
    assert "explanation" in payload
    assert "skills" in payload
    assert payload["skills"]["MENTAL_ROTATION"] == 0.95
    assert payload["skills"]["VISUAL_PATTERN_RECOGNITION"] == 0.8
    assert "difficulty_profile" in payload
    assert payload["difficulty_profile"]["overall"] == payload["difficulty"]


def test_matrix_demo_endpoint_is_deterministic() -> None:
    client = TestClient(app)
    first = client.get("/matrix/demo").json()
    second = client.get("/matrix/demo").json()

    assert first == second


def test_matrix_generate_endpoint_returns_http_200() -> None:
    client = TestClient(app)
    response = client.post("/matrix/generate", json={"seed": 12345})

    assert response.status_code == 200


def test_matrix_generate_endpoint_returns_expected_schema() -> None:
    client = TestClient(app)
    response = client.post("/matrix/generate", json={"seed": 12345})

    assert response.status_code == 200
    payload = response.json()

    assert payload["seed"] == 12345
    assert len(payload["grid"]) == 3
    assert all(len(row) == 3 for row in payload["grid"])
    assert payload["grid"][2][2] is None
    assert payload["missing_position"] == [2, 2]
    assert set(payload["solution"]) == {"shape", "rotation", "size", "color"}
    assert len(payload["options"]) == 6
    assert isinstance(payload["correct_index"], int)
    assert 0 <= payload["correct_index"] < 6
    assert payload["options"][payload["correct_index"]]["is_correct"] is True
    assert 1 <= len(payload["rules"]) <= 3
    assert all(set(rule) == {"type", "value", "difficulty"} for rule in payload["rules"])
    assert isinstance(payload["difficulty"], float)
    assert 0.0 <= payload["difficulty"] <= 1.0
    assert set(payload["difficulty_profile"]) == {
        "overall",
        "working_memory",
        "pattern_complexity",
        "visual_complexity",
        "rule_complexity",
        "abstraction",
        "distractor_strength",
    }
    assert payload["difficulty_profile"]["overall"] == payload["difficulty"]
    assert isinstance(payload["explanation"], str)
    assert payload["explanation"]
    assert any(rule["type"] in payload["explanation"].lower() for rule in payload["rules"])


def test_matrix_generate_endpoint_is_deterministic_for_same_seed() -> None:
    client = TestClient(app)
    first = client.post("/matrix/generate", json={"seed": 12345}).json()
    second = client.post("/matrix/generate", json={"seed": 12345}).json()

    assert first == second
