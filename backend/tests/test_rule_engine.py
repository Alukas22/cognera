"""Unit tests for the Cognera plugin rule engine."""

from backend.app.matrix import MatrixGenerator, RuleRegistry, RuleType
from backend.app.matrix.rules import BaseRule, RotationRule


def test_rotation_rule_is_subclass_of_base_rule() -> None:
    assert issubclass(RotationRule, BaseRule)


def test_rule_registry_discovers_rotation_rule() -> None:
    registry = RuleRegistry()

    assert RuleType.ROTATION in registry.available()
    rule = registry.get(RuleType.ROTATION)

    assert isinstance(rule, RotationRule)


def test_matrix_generator_delegates_to_rule() -> None:
    registry = RuleRegistry()
    rule = registry.get(RuleType.ROTATION)
    puzzle = MatrixGenerator(rule).generate(seed=101)

    assert puzzle.seed == 101
    assert puzzle.rules[0].type == RuleType.ROTATION


def test_rotation_rule_validate_and_explain() -> None:
    rule = RotationRule()
    puzzle = rule.generate(seed=77)

    assert rule.validate(puzzle.grid)
    assert "rotates" in rule.explain().lower()
    assert "clockwise" in rule.explain().lower()


def test_rotation_rule_produces_skill_profile() -> None:
    rule = RotationRule()
    puzzle = rule.generate(seed=77)

    assert puzzle.skill_profile is not None
    skills = puzzle.skill_profile.as_dict()
    assert skills["MENTAL_ROTATION"] == 0.95
    assert skills["VISUAL_PATTERN_RECOGNITION"] == 0.8
    assert all(0.0 <= value <= 1.0 for value in skills.values())


def test_matrix_generator_composes_multiple_rules() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)

    assert 2 <= len(puzzle.rules) <= 4
    assert puzzle.skill_profile is not None
    assert len(puzzle.skill_profile.skills) >= 1
    assert puzzle.correct_answer is not None
    assert all(cell is None or isinstance(cell, type(puzzle.correct_answer)) for row in puzzle.grid for cell in row)


def test_composite_generation_is_deterministic() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)

    first = generator.generate(seed=2024)
    second = generator.generate(seed=2024)

    assert first == second
