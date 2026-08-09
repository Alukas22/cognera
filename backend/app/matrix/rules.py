"""Definitions and plugins for Cognera matrix rules."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from .models import CognitiveSkill, Figure, MatrixPuzzle, Rule, SkillProfile


SHAPES = ["triangle", "square", "circle", "diamond"]
SIZES = ["small", "medium", "large"]
COLORS = ["black", "white", "red", "blue"]
ROTATIONS = (0, 90, 180, 270)
ANSWER_ALTERNATIVES = 4
MISSING_ROW = 2
MISSING_COL = 2


class RuleType(str, Enum):
    """Supported rule categories for Cognera matrix puzzles."""

    ROTATION = "rotation"
    COUNT = "count"
    SHAPE = "shape"
    SIZE = "size"
    POSITION = "position"
    COLOR = "color"


@dataclass(frozen=True)
class Rule:
    """A reasoning rule used to generate or explain a matrix puzzle."""

    type: RuleType
    value: Any
    difficulty: float


class BaseRule(ABC):
    """Abstract base class for a puzzle reasoning rule."""

    registry: ClassVar[dict[RuleType, type["BaseRule"]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        rule_type = getattr(cls, "rule_type", None)
        if rule_type is not None:
            cls.registry[rule_type] = cls

    @property
    @abstractmethod
    def rule_type(self) -> RuleType:
        """The type of reasoning rule implemented by this class."""

    @abstractmethod
    def generate(self, seed: int) -> MatrixPuzzle:
        """Generate a deterministic puzzle with this rule."""

    @abstractmethod
    def validate(self, grid: tuple[tuple[Figure | None, ...], ...]) -> bool:
        """Validate that a grid follows this rule."""

    @abstractmethod
    def explain(self) -> str:
        """Return a plain-English explanation of the rule."""

    @abstractmethod
    def difficulty(self) -> float:
        """Return the difficulty rating for this rule."""


class RotationRule(BaseRule):
    """Rotation rule plugin implementation."""

    rule_type = RuleType.ROTATION

    def generate(self, seed: int) -> MatrixPuzzle:
        rng = random.Random(seed)
        base_shape = rng.choice(SHAPES)
        base_size = rng.choice(SIZES)
        base_color = rng.choice(COLORS)
        step = rng.choice([90, 180, 270])
        base_rotation = rng.choice(ROTATIONS)
        rule = Rule(
            type=RuleType.ROTATION,
            value=f"{step}° clockwise",
            difficulty=self.difficulty(),
        )

        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if row == MISSING_ROW and col == MISSING_COL:
                    row_cells.append(None)
                    continue
                index = row * 3 + col
                rotation = (base_rotation + step * index) % 360
                row_cells.append(
                    Figure(
                        shape=base_shape,
                        rotation=rotation,
                        size=base_size,
                        color=base_color,
                    )
                )
            grid.append(row_cells)

        correct_rotation = (base_rotation + step * (MISSING_ROW * 3 + MISSING_COL)) % 360
        correct_answer = Figure(
            shape=base_shape,
            rotation=correct_rotation,
            size=base_size,
            color=base_color,
        )

        distractor_rotations = [rotation for rotation in ROTATIONS if rotation != correct_rotation]
        rng.shuffle(distractor_rotations)
        distractors = tuple(
            Figure(
                shape=base_shape,
                rotation=rotation,
                size=base_size,
                color=base_color,
            )
            for rotation in distractor_rotations[:ANSWER_ALTERNATIVES - 1]
        )

        skill_profile = SkillProfile(
            skills={
                CognitiveSkill.MENTAL_ROTATION: 0.95,
                CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.8,
                CognitiveSkill.WORKING_MEMORY: 0.3,
                CognitiveSkill.ATTENTION: 0.4,
                CognitiveSkill.PROCESSING_SPEED: 0.35,
                CognitiveSkill.ABSTRACT_REASONING: 0.5,
                CognitiveSkill.EXECUTIVE_FUNCTION: 0.25,
            }
        )

        return MatrixPuzzle(
            seed=seed,
            rules=(rule,),
            grid=tuple(tuple(cell for cell in row) for row in grid),
            correct_answer=correct_answer,
            distractors=distractors,
            skill_profile=skill_profile,
        )

    def validate(self, grid: tuple[tuple[Figure | None, ...], ...]) -> bool:
        visible = [cell for row in grid for cell in row if cell is not None]
        if len(visible) != 8:
            return False

        shapes = {cell.shape for cell in visible}
        sizes = {cell.size for cell in visible}
        colors = {cell.color for cell in visible}
        if len(shapes) != 1 or len(sizes) != 1 or len(colors) != 1:
            return False

        rotations = [cell.rotation for cell in visible]
        if len(rotations) != 8:
            return False

        step = (rotations[1] - rotations[0]) % 360
        if step not in {90, 180, 270}:
            return False

        expected = rotations[0]
        for rotation in rotations:
            if rotation != expected:
                return False
            expected = (expected + step) % 360

        return True

    def explain(self) -> str:
        return (
            "The triangle rotates 90 degrees clockwise in every step "
            "from left to right, top to bottom. The missing cell continues "
            "that rotation progression."
        )

    def difficulty(self) -> float:
        return 1.0


class CountRule(BaseRule):
    """Placeholder for future count rule implementation."""

    rule_type = RuleType.COUNT

    def generate(self, seed: int) -> MatrixPuzzle:
        raise NotImplementedError

    def validate(self, grid: tuple[tuple[Figure | None, ...], ...]) -> bool:
        raise NotImplementedError

    def explain(self) -> str:
        return "Count rule placeholder."

    def difficulty(self) -> float:
        return 0.0


class ShapeRule(BaseRule):
    """Placeholder for future shape rule implementation."""

    rule_type = RuleType.SHAPE

    def generate(self, seed: int) -> MatrixPuzzle:
        raise NotImplementedError

    def validate(self, grid: tuple[tuple[Figure | None, ...], ...]) -> bool:
        raise NotImplementedError

    def explain(self) -> str:
        return "Shape rule placeholder."

    def difficulty(self) -> float:
        return 0.0


class SizeRule(BaseRule):
    """Placeholder for future size rule implementation."""

    rule_type = RuleType.SIZE

    def generate(self, seed: int) -> MatrixPuzzle:
        raise NotImplementedError

    def validate(self, grid: tuple[tuple[Figure | None, ...], ...]) -> bool:
        raise NotImplementedError

    def explain(self) -> str:
        return "Size rule placeholder."

    def difficulty(self) -> float:
        return 0.0


class PositionRule(BaseRule):
    """Placeholder for future position rule implementation."""

    rule_type = RuleType.POSITION

    def generate(self, seed: int) -> MatrixPuzzle:
        raise NotImplementedError

    def validate(self, grid: tuple[tuple[Figure | None, ...], ...]) -> bool:
        raise NotImplementedError

    def explain(self) -> str:
        return "Position rule placeholder."

    def difficulty(self) -> float:
        return 0.0


class ColorRule(BaseRule):
    """Placeholder for future color rule implementation."""

    rule_type = RuleType.COLOR

    def generate(self, seed: int) -> MatrixPuzzle:
        raise NotImplementedError

    def validate(self, grid: tuple[tuple[Figure | None, ...], ...]) -> bool:
        raise NotImplementedError

    def explain(self) -> str:
        return "Color rule placeholder."

    def difficulty(self) -> float:
        return 0.0
