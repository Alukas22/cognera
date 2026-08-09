"""Matrix engine models for rules and puzzles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RuleType(str, Enum):
    """Supported rule categories for Cognera matrix puzzles."""

    ROTATION = "rotation"
    COUNT = "count"
    SHAPE = "shape"
    SIZE = "size"
    POSITION = "position"
    MIRROR = "mirror"
    COLOR = "color"


class DistractorReason(str, Enum):
    """Reason categories for generated distractors."""

    WRONG_ROTATION = "WRONG_ROTATION"
    WRONG_COUNT = "WRONG_COUNT"
    WRONG_POSITION = "WRONG_POSITION"
    WRONG_COLOR = "WRONG_COLOR"
    WRONG_SHAPE = "WRONG_SHAPE"
    PARTIAL_PATTERN = "PARTIAL_PATTERN"
    MIRROR_INSTEAD_OF_ROTATION = "MIRROR_INSTEAD_OF_ROTATION"


class CognitiveSkill(str, Enum):
    """Cognitive skill categories associated with each puzzle."""

    VISUAL_PATTERN_RECOGNITION = "VISUAL_PATTERN_RECOGNITION"
    MENTAL_ROTATION = "MENTAL_ROTATION"
    WORKING_MEMORY = "WORKING_MEMORY"
    ATTENTION = "ATTENTION"
    PROCESSING_SPEED = "PROCESSING_SPEED"
    ABSTRACT_REASONING = "ABSTRACT_REASONING"
    EXECUTIVE_FUNCTION = "EXECUTIVE_FUNCTION"


@dataclass(frozen=True)
class SkillProfile:
    """Quantified cognitive skill profile for a generated puzzle."""

    skills: dict[CognitiveSkill, float]

    def as_dict(self) -> dict[str, float]:
        return {skill.value: value for skill, value in self.skills.items()}

    @classmethod
    def combine(cls, profiles: list["SkillProfile"]) -> "SkillProfile":
        combined: dict[CognitiveSkill, float] = {}
        counts: dict[CognitiveSkill, int] = {}
        for profile in profiles:
            for skill, value in profile.skills.items():
                combined[skill] = combined.get(skill, 0.0) + value
                counts[skill] = counts.get(skill, 0) + 1

        averaged = {
            skill: combined[skill] / counts[skill]
            for skill in combined
        }
        return cls(skills=averaged)


@dataclass(frozen=True)
class Rule:
    """A reasoning rule used to generate or explain a matrix puzzle."""

    type: RuleType
    value: Any
    difficulty: float


@dataclass(frozen=True)
class Distractor:
    """An incorrect answer option with its reasoning metadata."""

    figure: Figure
    reason: DistractorReason
    explanation: str
    origin_rule: RuleType
    difficulty: float = 0.0


@dataclass(frozen=True)
class AnswerOption:
    """A labeled answer option for a generated matrix puzzle."""

    label: str
    figure: Figure
    is_correct: bool
    reason: DistractorReason | None = None
    explanation: str = ""
    origin_rule: RuleType | None = None
    difficulty: float = 0.0


@dataclass(frozen=True)
class Figure:
    """A structured figure representation for Raven-style matrix generation."""

    shape: str
    rotation: int
    size: str
    color: str


@dataclass(frozen=True)
class MatrixPuzzle:
    """Canonical representation of a generated Raven-style matrix puzzle."""

    seed: int
    rules: tuple[Rule, ...]
    grid: tuple[tuple[Figure | None, ...], ...]
    correct_answer: Figure
    distractors: tuple[Distractor, ...]
    skill_profile: SkillProfile
    missing_position: tuple[int, int] = (2, 2)
    difficulty: float = 0.0
    explanation: str = ""
    options: tuple[AnswerOption, ...] = ()
    correct_index: int = 0

    @property
    def solution(self) -> Figure:
        return self.correct_answer
