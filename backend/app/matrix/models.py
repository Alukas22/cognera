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


@dataclass(frozen=True)
class Rule:
    """A reasoning rule used to generate or explain a matrix puzzle."""

    type: RuleType
    value: Any
    difficulty: float


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
    distractors: tuple[Figure, ...]
    skill_profile: SkillProfile
