"""Unit tests for the Cognera rotation puzzle generator."""

from backend.app.matrix import RotationGenerator, Figure, RuleType


def test_rotation_generator_is_deterministic() -> None:
    generator = RotationGenerator()
    first = generator.generate(seed=1234)
    second = generator.generate(seed=1234)

    assert first == second


def test_rotation_generator_creates_3x3_grid_with_missing_cell() -> None:
    generator = RotationGenerator()
    puzzle = generator.generate(seed=42)

    assert len(puzzle.grid) == 3
    assert all(len(row) == 3 for row in puzzle.grid)
    assert sum(1 for row in puzzle.grid for cell in row if cell is None) == 1
    assert sum(1 for row in puzzle.grid for cell in row if cell is not None) == 8


def test_rotation_generator_creates_correct_answer_and_distractors() -> None:
    generator = RotationGenerator()
    puzzle = generator.generate(seed=42)

    assert isinstance(puzzle.correct_answer, Figure)
    assert len(puzzle.distractors) == 3
    assert puzzle.correct_answer not in puzzle.distractors


def test_rotation_generator_validate_returns_true_for_valid_puzzle() -> None:
    generator = RotationGenerator()
    puzzle = generator.generate(seed=99)

    assert generator.validate(puzzle)


def test_explain_puzzle_returns_rotation_description() -> None:
    generator = RotationGenerator()
    puzzle = generator.generate(seed=7)
    explanation = __import__("backend.app.matrix.explainer", fromlist=["explain_puzzle"]).explain_puzzle(puzzle)

    assert "rotates" in explanation
    assert str(puzzle.correct_answer.rotation) in explanation
