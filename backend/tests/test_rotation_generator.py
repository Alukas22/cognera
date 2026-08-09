"""Unit tests for the Cognera rotation rule plugin."""

from backend.app.matrix import MatrixGenerator, RuleType
from backend.app.matrix.rules import RotationRule


def test_rotation_rule_is_deterministic() -> None:
    rule = RotationRule()
    first = rule.generate(seed=1234)
    second = rule.generate(seed=1234)

    assert first == second


def test_rotation_rule_creates_3x3_grid_with_missing_cell() -> None:
    rule = RotationRule()
    puzzle = rule.generate(seed=42)

    assert len(puzzle.grid) == 3
    assert all(len(row) == 3 for row in puzzle.grid)
    assert sum(1 for row in puzzle.grid for cell in row if cell is None) == 1
    assert sum(1 for row in puzzle.grid for cell in row if cell is not None) == 8


def test_rotation_rule_creates_correct_answer_and_distractors() -> None:
    rule = RotationRule()
    puzzle = rule.generate(seed=42)

    assert len(puzzle.distractors) == 3
    assert puzzle.correct_answer not in puzzle.distractors


def test_matrix_generator_uses_rotation_rule() -> None:
    rule = RotationRule()
    puzzle = MatrixGenerator(rule).generate(seed=99)

    assert puzzle.seed == 99
    assert puzzle.rules[0].type == RuleType.ROTATION


def test_rotation_rule_explanation_includes_clockwise() -> None:
    rule = RotationRule()

    assert "rotates" in rule.explain().lower()
    assert "clockwise" in rule.explain().lower()
