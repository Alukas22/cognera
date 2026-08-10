"""Unit tests for matrix model primitives outside the RE-001 contract slice."""

import pytest

from backend.app.matrix.models import (
    AnswerOption,
    DifficultyProfile,
    Distractor,
    DistractorReason,
    Figure,
    RuleType,
)


def _figure(shape: str = "triangle", rotation: int = 0, size: str = "medium", color: str = "red") -> Figure:
    return Figure(shape=shape, rotation=rotation, size=size, color=color)


def test_distractor_reason_enum_has_all_expected_values() -> None:
    expected = {
        "WRONG_ROTATION", "WRONG_SIZE", "WRONG_SHAPE", "WRONG_COUNT",
        "WRONG_POSITION", "WRONG_COLOR", "WRONG_PROGRESSION", "OMISSION_OF_RULE",
        "PARTIAL_REASONING", "PERCEPTUAL_SIMILARITY", "PARTIAL_PATTERN",
        "MIRROR_INSTEAD_OF_ROTATION",
    }
    assert {reason.value for reason in DistractorReason} == expected


def test_distractor_reason_is_string_enum() -> None:
    assert DistractorReason.WRONG_ROTATION == "WRONG_ROTATION"


def test_distractor_fields_are_assigned() -> None:
    figure = _figure()
    distractor = Distractor(
        figure=figure,
        reason=DistractorReason.WRONG_ROTATION,
        explanation="Rotation differs.",
        origin_rule=RuleType.ROTATION,
        difficulty=0.6,
    )
    assert distractor.figure == figure
    assert distractor.reason == DistractorReason.WRONG_ROTATION
    assert distractor.explanation == "Rotation differs."
    assert distractor.origin_rule == RuleType.ROTATION
    assert distractor.difficulty == 0.6


def test_distractor_optional_fields_default_to_none_and_zero() -> None:
    distractor = Distractor(
        figure=_figure(),
        reason=DistractorReason.WRONG_SHAPE,
        explanation="Wrong.",
    )
    assert distractor.origin_rule is None
    assert distractor.difficulty == 0.0


def test_distractor_is_frozen() -> None:
    distractor = Distractor(
        figure=_figure(),
        reason=DistractorReason.WRONG_COLOR,
        explanation="Wrong color.",
    )
    with pytest.raises((AttributeError, TypeError)):
        distractor.difficulty = 1.0  # type: ignore[misc]


def test_answer_option_fields_are_assigned() -> None:
    figure = _figure()
    option = AnswerOption(
        label="A",
        figure=figure,
        is_correct=True,
        explanation="Correct.",
        reason=None,
        origin_rule=RuleType.ROTATION,
        difficulty=0.5,
    )
    assert option.label == "A"
    assert option.figure == figure
    assert option.is_correct is True
    assert option.explanation == "Correct."
    assert option.reason is None
    assert option.origin_rule == RuleType.ROTATION
    assert option.difficulty == 0.5


def test_answer_option_optional_fields_have_defaults() -> None:
    option = AnswerOption(label="B", figure=_figure(), is_correct=False)
    assert option.explanation == ""
    assert option.reason is None
    assert option.origin_rule is None
    assert option.difficulty == 0.0


def test_answer_option_is_frozen() -> None:
    option = AnswerOption(label="A", figure=_figure(), is_correct=True)
    with pytest.raises((AttributeError, TypeError)):
        option.label = "Z"  # type: ignore[misc]


def test_difficulty_profile_fields_are_assigned() -> None:
    profile = DifficultyProfile(
        overall=0.5,
        working_memory=0.4,
        pattern_complexity=0.5,
        visual_complexity=0.3,
        rule_complexity=0.6,
        abstraction=0.5,
        distractor_strength=0.7,
    )
    assert profile.overall == 0.5
    assert profile.working_memory == 0.4
    assert profile.pattern_complexity == 0.5
    assert profile.visual_complexity == 0.3
    assert profile.rule_complexity == 0.6
    assert profile.abstraction == 0.5
    assert profile.distractor_strength == 0.7


def test_difficulty_profile_is_frozen() -> None:
    profile = DifficultyProfile(
        overall=0.5,
        working_memory=0.4,
        pattern_complexity=0.5,
        visual_complexity=0.3,
        rule_complexity=0.6,
        abstraction=0.5,
        distractor_strength=0.7,
    )
    with pytest.raises((AttributeError, TypeError)):
        profile.overall = 1.0  # type: ignore[misc]