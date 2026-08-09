"""Unit tests for Cognera core rule plugins."""

from pytest import mark

from backend.app.matrix import MatrixGenerator, RuleRegistry, RuleType
from backend.app.matrix.rules import CountRule, MirrorRule, PositionRule, ShapeRule, SizeRule


NEW_RULES = [
    (CountRule, RuleType.COUNT, "count"),
    (ShapeRule, RuleType.SHAPE, "shape"),
    (SizeRule, RuleType.SIZE, "size"),
    (PositionRule, RuleType.POSITION, "position"),
    (MirrorRule, RuleType.MIRROR, "mirror"),
]


@mark.parametrize("rule_cls, rule_type, keyword", NEW_RULES)
def test_rule_is_subclass_of_base_rule(rule_cls, rule_type, keyword) -> None:
    assert issubclass(rule_cls, object)


@mark.parametrize("rule_cls, rule_type, keyword", NEW_RULES)
def test_rule_registry_discovers_rule(rule_cls, rule_type, keyword) -> None:
    registry = RuleRegistry()

    assert rule_type in registry.available()
    rule = registry.get(rule_type)

    assert type(rule) is rule_cls


@mark.parametrize("rule_cls, rule_type, keyword", NEW_RULES)
def test_rule_generate_is_deterministic(rule_cls, rule_type, keyword) -> None:
    rule = rule_cls()
    first = rule.generate(seed=42)
    second = rule.generate(seed=42)

    assert first == second


@mark.parametrize("rule_cls, rule_type, keyword", NEW_RULES)
def test_rule_generates_complete_puzzle(rule_cls, rule_type, keyword) -> None:
    rule = rule_cls()
    puzzle = rule.generate(seed=123)

    assert puzzle.seed == 123
    assert puzzle.rules[0].type == rule_type
    assert len(puzzle.grid) == 3
    assert all(len(row) == 3 for row in puzzle.grid)
    assert sum(1 for row in puzzle.grid for cell in row if cell is None) == 1
    assert sum(1 for row in puzzle.grid for cell in row if cell is not None) == 8
    assert len(puzzle.distractors) == 3
    assert puzzle.correct_answer not in puzzle.distractors


@mark.parametrize("rule_cls, rule_type, keyword", NEW_RULES)
def test_rule_validate_generated_grid(rule_cls, rule_type, keyword) -> None:
    rule = rule_cls()
    puzzle = rule.generate(seed=321)

    assert rule.validate(puzzle.grid)


@mark.parametrize("rule_cls, rule_type, keyword", NEW_RULES)
def test_rule_explanation_contains_keyword(rule_cls, rule_type, keyword) -> None:
    rule = rule_cls()
    explanation = rule.explain().lower()

    assert keyword in explanation
