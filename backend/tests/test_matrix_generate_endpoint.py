"""API tests for the vertical-slice matrix generation endpoint."""

from fastapi.testclient import TestClient

from backend.app.main import app, _project_vertical_slice_options
from backend.app.matrix.models import AnswerOption, DistractorReason, Figure


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


def test_vertical_slice_projection_prefers_stronger_and_more_diverse_distractors() -> None:
    puzzle = type("Puzzle", (), {})()
    puzzle.correct_index = 0
    puzzle.options = (
        AnswerOption(
            label="A",
            figure=Figure("circle", 0, "small", "black"),
            is_correct=True,
            difficulty=0.0,
        ),
        AnswerOption(
            label="B",
            figure=Figure("circle", 90, "small", "black"),
            is_correct=False,
            difficulty=0.2,
            reason=DistractorReason.WRONG_ROTATION,
        ),
        AnswerOption(
            label="C",
            figure=Figure("square", 0, "small", "black"),
            is_correct=False,
            difficulty=0.9,
            reason=DistractorReason.WRONG_SHAPE,
        ),
        AnswerOption(
            label="D",
            figure=Figure("circle", 180, "small", "black"),
            is_correct=False,
            difficulty=0.8,
            reason=DistractorReason.WRONG_ROTATION,
        ),
        AnswerOption(
            label="E",
            figure=Figure("circle", 0, "medium", "black"),
            is_correct=False,
            difficulty=0.85,
            reason=DistractorReason.WRONG_SIZE,
        ),
        AnswerOption(
            label="F",
            figure=Figure("circle", 0, "small", "red"),
            is_correct=False,
            difficulty=0.7,
            reason=DistractorReason.WRONG_COLOR,
        ),
    )

    options, correct_index = _project_vertical_slice_options(puzzle)

    assert correct_index == 0
    assert len(options) == 4
    assert options[0]["is_correct"] is True
    assert [option["reason"] for option in options[1:]] == [
        "WRONG_SHAPE",
        "WRONG_SIZE",
        "WRONG_ROTATION",
    ]
    assert [option["difficulty"] for option in options[1:]] == [0.9, 0.85, 0.8]