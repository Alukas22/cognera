"""Unit tests for the Cognera matrix engine foundation."""

from backend.app.matrix.models import AnswerOption, CognitiveSkill, MatrixPuzzle, Rule, RuleType, SkillProfile


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
    skill_profile = SkillProfile(
        skills={
            CognitiveSkill.MENTAL_ROTATION: 0.0,
            CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.0,
            CognitiveSkill.WORKING_MEMORY: 0.0,
            CognitiveSkill.ATTENTION: 0.0,
            CognitiveSkill.PROCESSING_SPEED: 0.0,
            CognitiveSkill.ABSTRACT_REASONING: 0.0,
            CognitiveSkill.EXECUTIVE_FUNCTION: 0.0,
        }
    )
    puzzle = MatrixPuzzle(
        seed=42,
        rules=(rule,),
        grid=grid,
        correct_answer="A",
        distractors=distractors,
        skill_profile=skill_profile,
    )

    assert puzzle.seed == 42
    assert puzzle.rules == (rule,)
    assert puzzle.grid == grid
    assert puzzle.correct_answer == "A"
    assert puzzle.distractors == distractors
    assert puzzle.skill_profile == skill_profile


def test_answer_option_dataclass_fields_are_assigned() -> None:
    option = AnswerOption(label="A", figure="figure", is_correct=True, difficulty=0.5)

    assert option.label == "A"
    assert option.figure == "figure"
    assert option.is_correct is True
    assert option.difficulty == 0.5
