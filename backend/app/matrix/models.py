"""Matrix engine models for rules and puzzles."""

from __future__ import annotations

from math import isclose
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
class Figure:
    """A structured figure representation for Raven-style matrix generation."""

    shape: str
    rotation: int
    size: str
    color: str


class DistractorReason(str, Enum):
    """Semantic reason a distractor option is incorrect."""

    WRONG_ROTATION = "WRONG_ROTATION"
    WRONG_SIZE = "WRONG_SIZE"
    WRONG_SHAPE = "WRONG_SHAPE"
    WRONG_COUNT = "WRONG_COUNT"
    WRONG_POSITION = "WRONG_POSITION"
    WRONG_COLOR = "WRONG_COLOR"
    WRONG_PROGRESSION = "WRONG_PROGRESSION"
    OMISSION_OF_RULE = "OMISSION_OF_RULE"
    PARTIAL_REASONING = "PARTIAL_REASONING"
    PERCEPTUAL_SIMILARITY = "PERCEPTUAL_SIMILARITY"
    PARTIAL_PATTERN = "PARTIAL_PATTERN"
    MIRROR_INSTEAD_OF_ROTATION = "MIRROR_INSTEAD_OF_ROTATION"


@dataclass(frozen=True)
class Distractor:
    """A single candidate distractor figure with diagnostic metadata."""

    figure: Figure
    reason: DistractorReason
    explanation: str
    origin_rule: RuleType | None = None
    difficulty: float = 0.0


@dataclass(frozen=True)
class AnswerOption:
    """A labelled answer option presented to the solver."""

    label: str
    figure: Figure
    is_correct: bool
    explanation: str = ""
    reason: DistractorReason | None = None
    origin_rule: RuleType | None = None
    difficulty: float = 0.0


@dataclass(frozen=True)
class DifficultyProfile:
    """Multi-dimensional cognitive difficulty breakdown for a puzzle."""

    overall: float
    working_memory: float
    pattern_complexity: float
    visual_complexity: float
    rule_complexity: float
    abstraction: float
    distractor_strength: float


class ContractViolationError(ValueError):
    """Raised when a MatrixPuzzle fails its canonical contract invariants."""


@dataclass(frozen=True)
class MatrixPuzzle:
    """Canonical validated puzzle aggregate for the Cognera matrix pipeline.

    Fields are partitioned into two lifecycle categories:
    - Core generation fields (always present): seed, rules, grid, correct_answer,
      distractors, skill_profile.
    - Validated contract fields (required before leaving finalization boundary):
      options, correct_index, explanation, missing_position, quality_score,
      quality_metadata, difficulty, difficulty_label, difficulty_profile.

    Call validate_contract() to assert all validated fields satisfy invariants.
    """

    # --- Core generation fields ---
    seed: int
    rules: tuple[Rule, ...]
    grid: tuple[tuple[Figure | None, ...], ...]
    correct_answer: Figure
    distractors: tuple[Figure, ...]
    skill_profile: SkillProfile

    # --- Canonical contract fields (RE-001) ---
    options: tuple[AnswerOption, ...] | None = None
    correct_index: int = -1
    explanation: str = ""
    missing_position: tuple[int, int] | None = None
    quality_score: float | None = None
    quality_metadata: dict[str, Any] | None = None
    difficulty: float | None = None
    difficulty_label: str | None = None
    difficulty_profile: DifficultyProfile | None = None

    @property
    def solution(self) -> Figure:
        """Alias for correct_answer; consumed by the difficulty engine."""
        return self.correct_answer

    def validate_contract(self) -> None:
        """Assert all canonical contract invariants. Raises ContractViolationError on failure."""
        violations: list[str] = []

        if not self.options:
            violations.append("options must be present and non-empty for a validated puzzle")

        if self.options is not None:
            if self.correct_index < 0 or self.correct_index >= len(self.options):
                violations.append(
                    f"correct_index {self.correct_index} does not reference an existing option"
                )

        if not self.explanation:
            violations.append("explanation must be present for a validated puzzle")

        if self.missing_position is None:
            violations.append("missing_position must be present for a validated puzzle")
        else:
            row, col = self.missing_position
            if row < 0 or col < 0 or row >= len(self.grid):
                violations.append("missing_position must reference a valid matrix location")
            elif col >= len(self.grid[row]):
                violations.append("missing_position must reference a valid matrix location")
            elif self.grid[row][col] is not None:
                violations.append("missing_position must identify the empty matrix cell")

        if self.quality_score is None:
            violations.append("quality_score must be present for a validated puzzle")

        if self.quality_metadata is None:
            violations.append("quality_metadata container must be present for a validated puzzle")

        difficulty_present = [
            self.difficulty is not None,
            self.difficulty_label is not None,
            self.difficulty_profile is not None,
        ]
        if any(difficulty_present) and not all(difficulty_present):
            violations.append(
                "difficulty, difficulty_label, and difficulty_profile must all be set or all be absent"
            )
        elif all(difficulty_present):
            if self.difficulty_label == "":
                violations.append("difficulty_label must not be empty for a validated puzzle")
            if not isclose(self.difficulty_profile.overall, self.difficulty):
                violations.append(
                    "difficulty and difficulty_profile.overall must describe the same difficulty state"
                )

        if violations:
            raise ContractViolationError(
                "MatrixPuzzle contract violated: " + "; ".join(violations)
            )
