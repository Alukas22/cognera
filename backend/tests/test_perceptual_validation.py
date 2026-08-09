"""Tests for perceptual validation of observable puzzle transformations."""

from backend.app.matrix import PerceptualValidationEngine, RuleType
from backend.app.matrix.models import (
    AnswerOption,
    CognitiveSkill,
    Figure,
    MatrixPuzzle,
    Rule,
    SkillProfile,
)


def _skill_profile() -> SkillProfile:
    return SkillProfile(
        skills={
            CognitiveSkill.MENTAL_ROTATION: 0.5,
            CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.5,
            CognitiveSkill.WORKING_MEMORY: 0.5,
            CognitiveSkill.ATTENTION: 0.5,
            CognitiveSkill.PROCESSING_SPEED: 0.5,
            CognitiveSkill.ABSTRACT_REASONING: 0.5,
            CognitiveSkill.EXECUTIVE_FUNCTION: 0.5,
        }
    )


def _options(correct: Figure) -> tuple[AnswerOption, ...]:
    return (
        AnswerOption(label="A", figure=correct, is_correct=True),
        AnswerOption(label="B", figure=Figure("triangle", 90, "small", "red"), is_correct=False),
        AnswerOption(label="C", figure=Figure("triangle", 180, "small", "red"), is_correct=False),
        AnswerOption(label="D", figure=Figure("triangle", 270, "small", "red"), is_correct=False),
        AnswerOption(label="E", figure=Figure("square", 0, "small", "red"), is_correct=False),
        AnswerOption(label="F", figure=Figure("triangle", 0, "medium", "red"), is_correct=False),
    )


def _puzzle(rule: Rule, grid: tuple[tuple[Figure | None, ...], ...], answer: Figure) -> MatrixPuzzle:
    return MatrixPuzzle(
        seed=1,
        rules=(rule,),
        grid=grid,
        correct_answer=answer,
        distractors=(),
        skill_profile=_skill_profile(),
        options=_options(answer),
        correct_index=0,
        explanation="Rule 1: test.",
    )


def test_rejects_invisible_rotation_with_symmetric_shape() -> None:
    engine = PerceptualValidationEngine()
    rule = Rule(type=RuleType.ROTATION, value="90° clockwise", difficulty=1.0)
    grid = (
        (Figure("square", 0, "small", "red"), Figure("square", 90, "small", "red"), Figure("square", 180, "small", "red")),
        (Figure("square", 270, "small", "red"), Figure("square", 0, "small", "red"), Figure("square", 90, "small", "red")),
        (Figure("square", 180, "small", "red"), Figure("square", 270, "small", "red"), None),
    )
    puzzle = _puzzle(rule, grid, Figure("square", 0, "small", "red"))

    valid, reasons = engine.validate(puzzle)
    assert valid is False
    assert "invisible_rotation" in reasons


def test_rejects_invisible_mirror_when_all_shapes_are_mirror_symmetric() -> None:
    engine = PerceptualValidationEngine()
    rule = Rule(type=RuleType.MIRROR, value="Mirror symmetry across the vertical axis.", difficulty=1.0)
    grid = (
        (Figure("circle", 0, "small", "red"), Figure("square", 0, "small", "red"), Figure("circle", 0, "small", "red")),
        (Figure("diamond", 0, "small", "red"), Figure("circle", 0, "small", "red"), Figure("diamond", 0, "small", "red")),
        (Figure("square", 0, "small", "red"), Figure("diamond", 0, "small", "red"), None),
    )
    puzzle = _puzzle(rule, grid, Figure("square", 0, "small", "red"))

    valid, reasons = engine.validate(puzzle)
    assert valid is False
    assert "invisible_mirror" in reasons


def test_rejects_imperceptible_size_changes() -> None:
    engine = PerceptualValidationEngine()
    rule = Rule(type=RuleType.SIZE, value="Sizes progress across columns.", difficulty=1.0)
    grid = (
        (Figure("triangle", 0, "medium", "red"), Figure("triangle", 90, "medium", "red"), Figure("triangle", 180, "medium", "red")),
        (Figure("triangle", 270, "medium", "red"), Figure("triangle", 0, "medium", "red"), Figure("triangle", 90, "medium", "red")),
        (Figure("triangle", 180, "medium", "red"), Figure("triangle", 270, "medium", "red"), None),
    )
    puzzle = _puzzle(rule, grid, Figure("triangle", 0, "medium", "red"))

    valid, reasons = engine.validate(puzzle)
    assert valid is False
    assert "imperceptible_size_change" in reasons


def test_rejects_imperceptible_color_changes() -> None:
    engine = PerceptualValidationEngine()
    rule = Rule(type=RuleType.COLOR, value="Color alternates by row.", difficulty=1.0)
    grid = (
        (Figure("triangle", 0, "small", "black"), Figure("triangle", 90, "small", "blue"), Figure("triangle", 180, "small", "black")),
        (Figure("triangle", 270, "small", "blue"), Figure("triangle", 0, "small", "black"), Figure("triangle", 90, "small", "blue")),
        (Figure("triangle", 180, "small", "black"), Figure("triangle", 270, "small", "blue"), None),
    )
    puzzle = _puzzle(rule, grid, Figure("triangle", 0, "small", "black"))

    valid, reasons = engine.validate(puzzle)
    assert valid is False
    assert "imperceptible_color_change" in reasons


def test_rejects_non_observable_transformations_inferability_gap() -> None:
    engine = PerceptualValidationEngine()
    rule = Rule(type=RuleType.ROTATION, value="180° clockwise", difficulty=1.0)
    grid = (
        (Figure("circle", 0, "small", "red"), Figure("circle", 0, "small", "red"), Figure("circle", 0, "small", "red")),
        (Figure("circle", 0, "small", "red"), Figure("circle", 0, "small", "red"), Figure("circle", 0, "small", "red")),
        (Figure("circle", 0, "small", "red"), Figure("circle", 0, "small", "red"), None),
    )
    puzzle = _puzzle(rule, grid, Figure("circle", 0, "small", "red"))

    valid, reasons = engine.validate(puzzle)
    assert valid is False
    assert "rule_not_inferable_from_visible_evidence" in reasons
