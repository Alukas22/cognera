"""Unit tests for the Cognera matrix engine foundation."""

from backend.app.matrix.models import MatrixPuzzle, Rule, RuleType


def test_rule_type_enum_contains_expected_values() -> None:
    assert RuleType.ROTATION.value == "rotation"
    assert RuleType.COUNT.value == "count"
    assert RuleType.SHAPE.value == "shape"
    assert RuleType.SIZE.value == "size"
    assert RuleType.POSITION.value == "position"
    assert RuleType.COLOR.value == "color"


def test_rule_dataclass_fields_are_assigned() -> None:
    rule = Rule(type=RuleType.SHAPE, value="circle", difficulty=1.5)

    assert rule.type == RuleType.SHAPE
    assert rule.value == "circle"
    assert rule.difficulty == 1.5


def test_matrix_puzzle_dataclass_fields_are_assigned() -> None:
    rule = Rule(type=RuleType.COUNT, value=3, difficulty=1.0)
    grid = (("A", "B", "C"), ("D", "A", "B"), ("C", "D", "A"))
    distractors = ("B", "C", "D", "A", "B")
    puzzle = MatrixPuzzle(
        seed=42,
        rules=(rule,),
        grid=grid,
        correct_answer="A",
        distractors=distractors,
    )

    assert puzzle.seed == 42
    assert puzzle.rules == (rule,)
    assert puzzle.grid == grid
    assert puzzle.correct_answer == "A"
    assert puzzle.distractors == distractors
