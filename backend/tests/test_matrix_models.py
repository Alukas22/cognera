"""Unit tests for the Cognera matrix engine foundation."""

import pytest

from backend.app.matrix.models import (
    AnswerOption,
    CognitiveSkill,
    ContractViolationError,
    DifficultyProfile,
    Figure,
    MatrixPuzzle,
    Rule,
    RuleType,
    SkillProfile,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _skill_profile() -> SkillProfile:
    return SkillProfile(
        skills={skill: 0.5 for skill in CognitiveSkill}
    )


def _figure(shape: str = "triangle", rotation: int = 0, size: str = "medium", color: str = "red") -> Figure:
    return Figure(shape=shape, rotation=rotation, size=size, color=color)


def _answer_options(correct: Figure) -> tuple[AnswerOption, ...]:
    return (
        AnswerOption(label="A", figure=correct, is_correct=True, explanation="Correct."),
        AnswerOption(label="B", figure=_figure(rotation=90), is_correct=False, explanation="Wrong rotation."),
        AnswerOption(label="C", figure=_figure(rotation=180), is_correct=False, explanation="Wrong rotation."),
        AnswerOption(label="D", figure=_figure(rotation=270), is_correct=False, explanation="Wrong rotation."),
        AnswerOption(label="E", figure=_figure(shape="square"), is_correct=False, explanation="Wrong shape."),
        AnswerOption(label="F", figure=_figure(size="small"), is_correct=False, explanation="Wrong size."),
    )


def _difficulty_profile() -> DifficultyProfile:
    return DifficultyProfile(
        overall=0.5,
        working_memory=0.4,
        pattern_complexity=0.5,
        visual_complexity=0.3,
        rule_complexity=0.6,
        abstraction=0.5,
        distractor_strength=0.7,
    )


def _valid_puzzle() -> MatrixPuzzle:
    correct = _figure()
    grid = (
        (_figure("square", 0, "small", "black"), _figure("square", 90, "small", "black"), _figure("square", 180, "small", "black")),
        (_figure("square", 90, "medium", "black"), _figure("square", 180, "medium", "black"), _figure("square", 270, "medium", "black")),
        (_figure("square", 180, "large", "black"), _figure("square", 270, "large", "black"), None),
    )
    return MatrixPuzzle(
        seed=1,
        rules=(Rule(type=RuleType.ROTATION, value="90° clockwise", difficulty=0.6),),
        grid=grid,
        correct_answer=correct,
        distractors=(),
        skill_profile=_skill_profile(),
        options=_answer_options(correct),
        correct_index=0,
        explanation="Rule 1: rotation rule -> 90° clockwise.\nCorrect answer: medium red triangle at 0°.",
        missing_position=(2, 2),
        quality_score=0.75,
        quality_metadata={"validation_results": {}},
        difficulty=0.5,
        difficulty_label="Medium",
        difficulty_profile=_difficulty_profile(),
    )


# ---------------------------------------------------------------------------
# Pre-existing tests (backward compatibility guardrails)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# MatrixPuzzle canonical contract field presence and defaults
# ---------------------------------------------------------------------------

def test_matrix_puzzle_canonical_fields_default_to_none_or_empty() -> None:
    puzzle = MatrixPuzzle(
        seed=1,
        rules=(),
        grid=(),
        correct_answer=_figure(),
        distractors=(),
        skill_profile=_skill_profile(),
    )
    assert puzzle.options is None
    assert puzzle.correct_index == -1
    assert puzzle.explanation == ""
    assert puzzle.missing_position is None
    assert puzzle.quality_score is None
    assert puzzle.quality_metadata is None
    assert puzzle.difficulty is None
    assert puzzle.difficulty_label is None
    assert puzzle.difficulty_profile is None


def test_matrix_puzzle_solution_property_aliases_correct_answer() -> None:
    correct = _figure()
    puzzle = MatrixPuzzle(
        seed=1,
        rules=(),
        grid=(),
        correct_answer=correct,
        distractors=(),
        skill_profile=_skill_profile(),
    )
    assert puzzle.solution is correct


# ---------------------------------------------------------------------------
# MatrixPuzzle construction with full canonical contract
# ---------------------------------------------------------------------------

def test_matrix_puzzle_canonical_fields_are_assigned_when_provided() -> None:
    puzzle = _valid_puzzle()

    assert puzzle.options is not None
    assert len(puzzle.options) == 6
    assert puzzle.correct_index == 0
    assert puzzle.explanation.startswith("Rule 1:")
    assert puzzle.missing_position == (2, 2)
    assert puzzle.quality_score == 0.75
    assert puzzle.quality_metadata == {"validation_results": {}}
    assert puzzle.difficulty == 0.5
    assert puzzle.difficulty_label == "Medium"
    assert puzzle.difficulty_profile is not None
    assert puzzle.difficulty_profile.overall == 0.5


# ---------------------------------------------------------------------------
# validate_contract() — invariant enforcement
# ---------------------------------------------------------------------------

def test_validate_contract_passes_for_complete_valid_puzzle() -> None:
    _valid_puzzle().validate_contract()  # must not raise


def test_validate_contract_raises_when_options_missing() -> None:
    puzzle = _valid_puzzle()
    incomplete = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=None,
        correct_index=0,
        explanation=puzzle.explanation,
        missing_position=puzzle.missing_position,
        quality_score=puzzle.quality_score,
        quality_metadata=puzzle.quality_metadata,
        difficulty=puzzle.difficulty,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError):
        incomplete.validate_contract()


def test_validate_contract_raises_when_options_empty() -> None:
    puzzle = _valid_puzzle()
    incomplete = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=(),
        correct_index=0,
        explanation=puzzle.explanation,
        missing_position=puzzle.missing_position,
        quality_score=puzzle.quality_score,
        quality_metadata=puzzle.quality_metadata,
        difficulty=puzzle.difficulty,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError):
        incomplete.validate_contract()


def test_validate_contract_raises_for_out_of_range_correct_index() -> None:
    puzzle = _valid_puzzle()
    bad_index = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=puzzle.options,
        correct_index=99,
        explanation=puzzle.explanation,
        missing_position=puzzle.missing_position,
        quality_score=puzzle.quality_score,
        quality_metadata=puzzle.quality_metadata,
        difficulty=puzzle.difficulty,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError):
        bad_index.validate_contract()


def test_validate_contract_raises_for_negative_correct_index() -> None:
    puzzle = _valid_puzzle()
    bad_index = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=puzzle.options,
        correct_index=-1,
        explanation=puzzle.explanation,
        missing_position=puzzle.missing_position,
        quality_score=puzzle.quality_score,
        quality_metadata=puzzle.quality_metadata,
        difficulty=puzzle.difficulty,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError):
        bad_index.validate_contract()


def test_validate_contract_raises_when_explanation_missing() -> None:
    puzzle = _valid_puzzle()
    no_explanation = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=puzzle.options,
        correct_index=puzzle.correct_index,
        explanation="",
        missing_position=puzzle.missing_position,
        quality_score=puzzle.quality_score,
        quality_metadata=puzzle.quality_metadata,
        difficulty=puzzle.difficulty,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError):
        no_explanation.validate_contract()


def test_validate_contract_raises_when_missing_position_missing() -> None:
    puzzle = _valid_puzzle()
    no_missing_position = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=puzzle.options,
        correct_index=puzzle.correct_index,
        explanation=puzzle.explanation,
        missing_position=None,
        quality_score=puzzle.quality_score,
        quality_metadata=puzzle.quality_metadata,
        difficulty=puzzle.difficulty,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError):
        no_missing_position.validate_contract()


def test_validate_contract_raises_when_missing_position_is_not_empty_cell() -> None:
    puzzle = _valid_puzzle()
    invalid_missing_position = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=puzzle.options,
        correct_index=puzzle.correct_index,
        explanation=puzzle.explanation,
        missing_position=(0, 0),
        quality_score=puzzle.quality_score,
        quality_metadata=puzzle.quality_metadata,
        difficulty=puzzle.difficulty,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError):
        invalid_missing_position.validate_contract()


def test_validate_contract_raises_when_quality_score_missing() -> None:
    puzzle = _valid_puzzle()
    no_quality_score = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=puzzle.options,
        correct_index=puzzle.correct_index,
        explanation=puzzle.explanation,
        missing_position=puzzle.missing_position,
        quality_score=None,
        quality_metadata=puzzle.quality_metadata,
        difficulty=puzzle.difficulty,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError):
        no_quality_score.validate_contract()


def test_validate_contract_raises_when_quality_metadata_missing() -> None:
    puzzle = _valid_puzzle()
    no_metadata = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=puzzle.options,
        correct_index=puzzle.correct_index,
        explanation=puzzle.explanation,
        missing_position=puzzle.missing_position,
        quality_score=puzzle.quality_score,
        quality_metadata=None,
        difficulty=puzzle.difficulty,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError):
        no_metadata.validate_contract()


def test_validate_contract_raises_when_difficulty_fields_partially_set() -> None:
    puzzle = _valid_puzzle()
    # difficulty set, but not difficulty_label or difficulty_profile
    partial = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=puzzle.options,
        correct_index=puzzle.correct_index,
        explanation=puzzle.explanation,
        missing_position=puzzle.missing_position,
        quality_score=puzzle.quality_score,
        quality_metadata=puzzle.quality_metadata,
        difficulty=0.5,
        difficulty_label=None,
        difficulty_profile=None,
    )
    with pytest.raises(ContractViolationError):
        partial.validate_contract()


def test_validate_contract_accepts_all_difficulty_fields_absent() -> None:
    puzzle = _valid_puzzle()
    no_difficulty = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=puzzle.options,
        correct_index=puzzle.correct_index,
        explanation=puzzle.explanation,
        missing_position=puzzle.missing_position,
        quality_score=puzzle.quality_score,
        quality_metadata=puzzle.quality_metadata,
        difficulty=None,
        difficulty_label=None,
        difficulty_profile=None,
    )
    no_difficulty.validate_contract()  # must not raise


def test_validate_contract_raises_when_difficulty_overall_mismatch_exists() -> None:
    puzzle = _valid_puzzle()
    mismatch = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=puzzle.options,
        correct_index=puzzle.correct_index,
        explanation=puzzle.explanation,
        missing_position=puzzle.missing_position,
        quality_score=puzzle.quality_score,
        quality_metadata=puzzle.quality_metadata,
        difficulty=0.7,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError):
        mismatch.validate_contract()


def test_validate_contract_error_message_identifies_violated_invariants() -> None:
    puzzle = _valid_puzzle()
    incomplete = MatrixPuzzle(
        seed=puzzle.seed,
        rules=puzzle.rules,
        grid=puzzle.grid,
        correct_answer=puzzle.correct_answer,
        distractors=puzzle.distractors,
        skill_profile=puzzle.skill_profile,
        options=None,
        correct_index=puzzle.correct_index,
        explanation="",
        missing_position=puzzle.missing_position,
        quality_score=puzzle.quality_score,
        quality_metadata=None,
        difficulty=puzzle.difficulty,
        difficulty_label=puzzle.difficulty_label,
        difficulty_profile=puzzle.difficulty_profile,
    )
    with pytest.raises(ContractViolationError) as exc_info:
        incomplete.validate_contract()
    message = str(exc_info.value)
    assert "options" in message
    assert "explanation" in message
    assert "quality_metadata" in message


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------

def test_validate_contract_is_deterministic_for_identical_inputs() -> None:
    puzzle = _valid_puzzle()
    puzzle.validate_contract()
    puzzle.validate_contract()


def test_validate_contract_rejection_is_deterministic() -> None:
    puzzle = MatrixPuzzle(
        seed=1,
        rules=(),
        grid=(),
        correct_answer=_figure(),
        distractors=(),
        skill_profile=_skill_profile(),
    )
    for _ in range(3):
        with pytest.raises(ContractViolationError):
            puzzle.validate_contract()


# ---------------------------------------------------------------------------
# Backward-compatibility tests
# ---------------------------------------------------------------------------

def test_legacy_puzzle_construction_without_contract_fields_is_valid() -> None:
    rule = Rule(type=RuleType.ROTATION, value="90", difficulty=0.5)
    puzzle = MatrixPuzzle(
        seed=7,
        rules=(rule,),
        grid=(),
        correct_answer=_figure(),
        distractors=(),
        skill_profile=_skill_profile(),
    )
    assert puzzle.seed == 7
    assert puzzle.correct_answer == _figure()


def test_legacy_correct_answer_field_still_accessible() -> None:
    correct = _figure("circle", 0, "small", "blue")
    puzzle = MatrixPuzzle(
        seed=5,
        rules=(),
        grid=(),
        correct_answer=correct,
        distractors=(),
        skill_profile=_skill_profile(),
    )
    assert puzzle.correct_answer == correct
    assert puzzle.solution == correct


# ---------------------------------------------------------------------------
# Serialization-shape tests (canonical field surface)
# ---------------------------------------------------------------------------

def test_canonical_field_surface_is_fully_accessible() -> None:
    puzzle = _valid_puzzle()
    # Every field in the canonical contract table must be directly accessible.
    _ = puzzle.grid
    _ = puzzle.missing_position
    _ = puzzle.options
    _ = puzzle.correct_index
    _ = puzzle.explanation
    _ = puzzle.quality_score
    _ = puzzle.quality_metadata
    _ = puzzle.difficulty
    _ = puzzle.difficulty_label
    _ = puzzle.difficulty_profile


def test_answer_option_figure_attributes_are_accessible_through_options() -> None:
    puzzle = _valid_puzzle()
    assert puzzle.options is not None
    correct_opt = puzzle.options[puzzle.correct_index]
    assert correct_opt.is_correct is True
    assert correct_opt.figure.shape == "triangle"

