"""Definitions and plugins for Cognera matrix rules."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from .models import CognitiveSkill, Figure, MatrixPuzzle, Rule, RuleType, SkillProfile


SHAPES = ["triangle", "square", "circle", "diamond"]
SIZES = ["small", "medium", "large"]
COLORS = ["black", "white", "red", "blue"]
ROTATIONS = (0, 90, 180, 270)
ANSWER_ALTERNATIVES = 4
MISSING_ROW = 2
MISSING_COL = 2


class BaseRule(ABC):
    """Abstract base class for a puzzle reasoning rule."""

    registry: ClassVar[dict[RuleType, type["BaseRule"]]] = {}
    _register: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "_register", True):
            return
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

    @abstractmethod
    def overlay(self, puzzle: MatrixPuzzle, seed: int) -> MatrixPuzzle:
        """Apply this rule on top of an existing puzzle state."""


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

    def overlay(self, puzzle: MatrixPuzzle, seed: int) -> MatrixPuzzle:
        generated = self.generate(seed)
        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if puzzle.grid[row][col] is None:
                    row_cells.append(None)
                    continue
                row_cells.append(
                    Figure(
                        shape=puzzle.grid[row][col].shape,
                        rotation=generated.grid[row][col].rotation,
                        size=puzzle.grid[row][col].size,
                        color=puzzle.grid[row][col].color,
                    )
                )
            grid.append(row_cells)

        distractors = tuple(
            Figure(
                shape=puzzle.correct_answer.shape,
                rotation=distractor.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            )
            for distractor in generated.distractors
        )

        return MatrixPuzzle(
            seed=puzzle.seed,
            rules=puzzle.rules,
            grid=tuple(tuple(cell for cell in row) for row in grid),
            correct_answer=Figure(
                shape=puzzle.correct_answer.shape,
                rotation=generated.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            ),
            distractors=distractors,
            skill_profile=puzzle.skill_profile,
        )


class CountRule(BaseRule):
    """Count rule plugin implementation."""

    rule_type = RuleType.COUNT

    def generate(self, seed: int) -> MatrixPuzzle:
        rng = random.Random(seed)
        target_shape = rng.choice(SHAPES)
        filler_shapes = [shape for shape in SHAPES if shape != target_shape]
        base_size = rng.choice(SIZES)
        base_color = rng.choice(COLORS)
        base_rotation = rng.choice(ROTATIONS)

        rule = Rule(
            type=RuleType.COUNT,
            value=f"Count the number of {target_shape} figures in each row.",
            difficulty=self.difficulty(),
        )

        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if row == MISSING_ROW and col == MISSING_COL:
                    row_cells.append(None)
                    continue
                if row == 0:
                    shape = filler_shapes[col % len(filler_shapes)]
                elif row == 1:
                    shape = target_shape if col == 0 else filler_shapes[col - 1]
                else:
                    shape = target_shape if col in (0, 1) else filler_shapes[0]
                row_cells.append(
                    Figure(
                        shape=shape,
                        rotation=base_rotation,
                        size=base_size,
                        color=base_color,
                    )
                )
            grid.append(row_cells)

        correct_answer = Figure(
            shape=target_shape,
            rotation=base_rotation,
            size=base_size,
            color=base_color,
        )

        distractors = tuple(
            Figure(
                shape=shape,
                rotation=base_rotation,
                size=base_size,
                color=base_color,
            )
            for shape in filler_shapes[:ANSWER_ALTERNATIVES - 1]
        )

        skill_profile = SkillProfile(
            skills={
                CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.75,
                CognitiveSkill.WORKING_MEMORY: 0.55,
                CognitiveSkill.ATTENTION: 0.7,
                CognitiveSkill.PROCESSING_SPEED: 0.4,
                CognitiveSkill.ABSTRACT_REASONING: 0.5,
                CognitiveSkill.EXECUTIVE_FUNCTION: 0.45,
                CognitiveSkill.MENTAL_ROTATION: 0.15,
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

        if len({cell.size for cell in visible}) != 1 or len({cell.color for cell in visible}) != 1 or len({cell.rotation for cell in visible}) != 1:
            return False

        def row_counts(shape: str) -> list[int]:
            return [sum(1 for cell in row if cell is not None and cell.shape == shape) for row in grid]

        for shape in SHAPES:
            if row_counts(shape) == [0, 1, 2]:
                return True

        return False

    def explain(self) -> str:
        return (
            "The number of the target shape increases by one in each row from top to "
            "bottom, so the missing cell completes that count progression."
        )

    def difficulty(self) -> float:
        return 0.8

    def overlay(self, puzzle: MatrixPuzzle, seed: int) -> MatrixPuzzle:
        generated = self.generate(seed)
        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if puzzle.grid[row][col] is None:
                    row_cells.append(None)
                    continue
                row_cells.append(
                    Figure(
                        shape=generated.grid[row][col].shape,
                        rotation=puzzle.grid[row][col].rotation,
                        size=puzzle.grid[row][col].size,
                        color=puzzle.grid[row][col].color,
                    )
                )
            grid.append(row_cells)

        distractors = tuple(
            Figure(
                shape=distractor.shape,
                rotation=puzzle.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            )
            for distractor in generated.distractors
        )

        return MatrixPuzzle(
            seed=puzzle.seed,
            rules=puzzle.rules,
            grid=tuple(tuple(cell for cell in row) for row in grid),
            correct_answer=Figure(
                shape=generated.correct_answer.shape,
                rotation=puzzle.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            ),
            distractors=distractors,
            skill_profile=puzzle.skill_profile,
        )


class ShapeRule(BaseRule):
    """Shape rule plugin implementation."""

    rule_type = RuleType.SHAPE

    def generate(self, seed: int) -> MatrixPuzzle:
        rng = random.Random(seed)
        offset = rng.randrange(len(SHAPES))
        base_size = rng.choice(SIZES)
        base_color = rng.choice(COLORS)
        base_rotation = rng.choice(ROTATIONS)

        rule = Rule(
            type=RuleType.SHAPE,
            value="Shapes follow a diagonal progression across the matrix.",
            difficulty=self.difficulty(),
        )

        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if row == MISSING_ROW and col == MISSING_COL:
                    row_cells.append(None)
                    continue
                shape = SHAPES[(offset + row + col) % len(SHAPES)]
                row_cells.append(
                    Figure(
                        shape=shape,
                        rotation=base_rotation,
                        size=base_size,
                        color=base_color,
                    )
                )
            grid.append(row_cells)

        correct_answer = Figure(
            shape=SHAPES[(offset + MISSING_ROW + MISSING_COL) % len(SHAPES)],
            rotation=base_rotation,
            size=base_size,
            color=base_color,
        )

        distractors = tuple(
            Figure(
                shape=shape,
                rotation=base_rotation,
                size=base_size,
                color=base_color,
            )
            for shape in SHAPES
            if shape != correct_answer.shape
        )[:ANSWER_ALTERNATIVES - 1]

        skill_profile = SkillProfile(
            skills={
                CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.95,
                CognitiveSkill.WORKING_MEMORY: 0.3,
                CognitiveSkill.ATTENTION: 0.5,
                CognitiveSkill.PROCESSING_SPEED: 0.4,
                CognitiveSkill.ABSTRACT_REASONING: 0.6,
                CognitiveSkill.EXECUTIVE_FUNCTION: 0.35,
                CognitiveSkill.MENTAL_ROTATION: 0.2,
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

        if len({cell.size for cell in visible}) != 1 or len({cell.color for cell in visible}) != 1 or len({cell.rotation for cell in visible}) != 1:
            return False

        for offset in range(len(SHAPES)):
            if all(
                grid[row][col] is None or grid[row][col].shape == SHAPES[(offset + row + col) % len(SHAPES)]
                for row in range(3)
                for col in range(3)
            ):
                return True

        return False

    def explain(self) -> str:
        return (
            "Shapes rotate through a fixed sequence across the matrix, advancing by "
            "one position with each cell. The missing cell continues that shape sequence."
        )

    def difficulty(self) -> float:
        return 0.7

    def overlay(self, puzzle: MatrixPuzzle, seed: int) -> MatrixPuzzle:
        generated = self.generate(seed)
        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if puzzle.grid[row][col] is None:
                    row_cells.append(None)
                    continue
                row_cells.append(
                    Figure(
                        shape=generated.grid[row][col].shape,
                        rotation=puzzle.grid[row][col].rotation,
                        size=puzzle.grid[row][col].size,
                        color=puzzle.grid[row][col].color,
                    )
                )
            grid.append(row_cells)

        distractors = tuple(
            Figure(
                shape=distractor.shape,
                rotation=puzzle.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            )
            for distractor in generated.distractors
        )

        return MatrixPuzzle(
            seed=puzzle.seed,
            rules=puzzle.rules,
            grid=tuple(tuple(cell for cell in row) for row in grid),
            correct_answer=Figure(
                shape=generated.correct_answer.shape,
                rotation=puzzle.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            ),
            distractors=distractors,
            skill_profile=puzzle.skill_profile,
        )


class SizeRule(BaseRule):
    """Size rule plugin implementation."""

    rule_type = RuleType.SIZE

    def generate(self, seed: int) -> MatrixPuzzle:
        rng = random.Random(seed)
        offset = rng.randrange(len(SIZES))
        base_shape = rng.choice(SHAPES)
        base_color = rng.choice(COLORS)
        base_rotation = rng.choice(ROTATIONS)

        rule = Rule(
            type=RuleType.SIZE,
            value="Sizes progress systematically across each column.",
            difficulty=self.difficulty(),
        )

        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if row == MISSING_ROW and col == MISSING_COL:
                    row_cells.append(None)
                    continue
                size = SIZES[(offset + col) % len(SIZES)]
                row_cells.append(
                    Figure(
                        shape=base_shape,
                        rotation=base_rotation,
                        size=size,
                        color=base_color,
                    )
                )
            grid.append(row_cells)

        correct_answer = Figure(
            shape=base_shape,
            rotation=base_rotation,
            size=SIZES[(offset + MISSING_COL) % len(SIZES)],
            color=base_color,
        )

        available_sizes = [size for size in SIZES if size != correct_answer.size]
        distractor_sizes = (available_sizes * 2)[:ANSWER_ALTERNATIVES - 1]
        distractors = tuple(
            Figure(
                shape=base_shape,
                rotation=base_rotation,
                size=size,
                color=base_color,
            )
            for size in distractor_sizes
        )

        skill_profile = SkillProfile(
            skills={
                CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.85,
                CognitiveSkill.WORKING_MEMORY: 0.35,
                CognitiveSkill.ATTENTION: 0.55,
                CognitiveSkill.PROCESSING_SPEED: 0.45,
                CognitiveSkill.ABSTRACT_REASONING: 0.5,
                CognitiveSkill.EXECUTIVE_FUNCTION: 0.3,
                CognitiveSkill.MENTAL_ROTATION: 0.2,
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

        if len({cell.shape for cell in visible}) != 1 or len({cell.color for cell in visible}) != 1 or len({cell.rotation for cell in visible}) != 1:
            return False

        for offset in range(len(SIZES)):
            if all(
                grid[row][col] is None or grid[row][col].size == SIZES[(offset + col) % len(SIZES)]
                for row in range(3)
                for col in range(3)
            ):
                return True

        return False

    def explain(self) -> str:
        return (
            "The matrix grows in size from left to right across every row, and the "
            "missing cell follows that same column progression."
        )

    def difficulty(self) -> float:
        return 0.75

    def overlay(self, puzzle: MatrixPuzzle, seed: int) -> MatrixPuzzle:
        generated = self.generate(seed)
        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if puzzle.grid[row][col] is None:
                    row_cells.append(None)
                    continue
                row_cells.append(
                    Figure(
                        shape=generated.grid[row][col].shape,
                        rotation=puzzle.grid[row][col].rotation,
                        size=puzzle.grid[row][col].size,
                        color=puzzle.grid[row][col].color,
                    )
                )
            grid.append(row_cells)

        distractors = tuple(
            Figure(
                shape=distractor.shape,
                rotation=puzzle.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            )
            for distractor in generated.distractors
        )

        return MatrixPuzzle(
            seed=puzzle.seed,
            rules=puzzle.rules,
            grid=tuple(tuple(cell for cell in row) for row in grid),
            correct_answer=Figure(
                shape=generated.correct_answer.shape,
                rotation=puzzle.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            ),
            distractors=distractors,
            skill_profile=puzzle.skill_profile,
        )


class PositionRule(BaseRule):
    """Position rule plugin implementation."""

    rule_type = RuleType.POSITION

    def generate(self, seed: int) -> MatrixPuzzle:
        rng = random.Random(seed)
        target_shape = rng.choice(SHAPES)
        filler_shape = rng.choice([shape for shape in SHAPES if shape != target_shape])
        base_size = rng.choice(SIZES)
        base_color = rng.choice(COLORS)
        base_rotation = rng.choice(ROTATIONS)

        rule = Rule(
            type=RuleType.POSITION,
            value="A special shape appears along the main diagonal positions.",
            difficulty=self.difficulty(),
        )

        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if row == MISSING_ROW and col == MISSING_COL:
                    row_cells.append(None)
                    continue
                shape = target_shape if row == col else filler_shape
                row_cells.append(
                    Figure(
                        shape=shape,
                        rotation=base_rotation,
                        size=base_size,
                        color=base_color,
                    )
                )
            grid.append(row_cells)

        correct_answer = Figure(
            shape=target_shape,
            rotation=base_rotation,
            size=base_size,
            color=base_color,
        )

        distractors = tuple(
            Figure(
                shape=filler_shape,
                rotation=base_rotation,
                size=base_size,
                color=base_color,
            )
            for _ in range(ANSWER_ALTERNATIVES - 1)
        )

        skill_profile = SkillProfile(
            skills={
                CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.9,
                CognitiveSkill.WORKING_MEMORY: 0.4,
                CognitiveSkill.ATTENTION: 0.5,
                CognitiveSkill.PROCESSING_SPEED: 0.35,
                CognitiveSkill.ABSTRACT_REASONING: 0.55,
                CognitiveSkill.EXECUTIVE_FUNCTION: 0.3,
                CognitiveSkill.MENTAL_ROTATION: 0.25,
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

        if len({cell.size for cell in visible}) != 1 or len({cell.color for cell in visible}) != 1 or len({cell.rotation for cell in visible}) != 1:
            return False

        for shape in SHAPES:
            positions = [
                (row_index, col_index)
                for row_index, row in enumerate(grid)
                for col_index, cell in enumerate(row)
                if cell is not None and cell.shape == shape
            ]
            if positions == [(0, 0), (1, 1)]:
                return True

        return False

    def explain(self) -> str:
        return (
            "A special figure occupies the diagonal positions, and the missing cell "
            "continues that diagonal positioning."
        )

    def difficulty(self) -> float:
        return 0.85

    def overlay(self, puzzle: MatrixPuzzle, seed: int) -> MatrixPuzzle:
        generated = self.generate(seed)
        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if puzzle.grid[row][col] is None:
                    row_cells.append(None)
                    continue
                row_cells.append(
                    Figure(
                        shape=generated.grid[row][col].shape,
                        rotation=puzzle.grid[row][col].rotation,
                        size=puzzle.grid[row][col].size,
                        color=puzzle.grid[row][col].color,
                    )
                )
            grid.append(row_cells)

        distractors = tuple(
            Figure(
                shape=distractor.shape,
                rotation=puzzle.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            )
            for distractor in generated.distractors
        )

        return MatrixPuzzle(
            seed=puzzle.seed,
            rules=puzzle.rules,
            grid=tuple(tuple(cell for cell in row) for row in grid),
            correct_answer=Figure(
                shape=generated.correct_answer.shape,
                rotation=puzzle.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            ),
            distractors=distractors,
            skill_profile=puzzle.skill_profile,
        )


class MirrorRule(BaseRule):
    """Mirror rule plugin implementation."""

    rule_type = RuleType.MIRROR

    def generate(self, seed: int) -> MatrixPuzzle:
        rng = random.Random(seed)
        axis = rng.choice(["vertical", "horizontal"])
        base_size = rng.choice(SIZES)
        base_color = rng.choice(COLORS)
        base_rotation = rng.choice(ROTATIONS)

        if axis == "vertical":
            left_shapes = [rng.choice(SHAPES) for _ in range(3)]
            middle_shapes = [rng.choice(SHAPES) for _ in range(3)]
        else:
            top_shapes = [rng.choice(SHAPES) for _ in range(3)]
            middle_shapes = [rng.choice(SHAPES) for _ in range(3)]

        rule = Rule(
            type=RuleType.MIRROR,
            value=f"Mirror symmetry across the {axis} axis.",
            difficulty=self.difficulty(),
        )

        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if row == MISSING_ROW and col == MISSING_COL:
                    row_cells.append(None)
                    continue
                if axis == "vertical":
                    if col == 0:
                        shape = left_shapes[row]
                    elif col == 1:
                        shape = middle_shapes[row]
                    else:
                        shape = left_shapes[row]
                else:
                    if row == 0:
                        shape = top_shapes[col]
                    elif row == 1:
                        shape = middle_shapes[col]
                    else:
                        shape = top_shapes[col]
                row_cells.append(
                    Figure(
                        shape=shape,
                        rotation=base_rotation,
                        size=base_size,
                        color=base_color,
                    )
                )
            grid.append(row_cells)

        if axis == "vertical":
            correct_answer = Figure(
                shape=left_shapes[MISSING_ROW],
                rotation=base_rotation,
                size=base_size,
                color=base_color,
            )
        else:
            correct_answer = Figure(
                shape=top_shapes[MISSING_COL],
                rotation=base_rotation,
                size=base_size,
                color=base_color,
            )

        distractors = tuple(
            Figure(
                shape=rng.choice([shape for shape in SHAPES if shape != correct_answer.shape]),
                rotation=base_rotation,
                size=base_size,
                color=base_color,
            )
            for _ in range(ANSWER_ALTERNATIVES - 1)
        )

        skill_profile = SkillProfile(
            skills={
                CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.92,
                CognitiveSkill.WORKING_MEMORY: 0.4,
                CognitiveSkill.ATTENTION: 0.6,
                CognitiveSkill.PROCESSING_SPEED: 0.5,
                CognitiveSkill.ABSTRACT_REASONING: 0.6,
                CognitiveSkill.EXECUTIVE_FUNCTION: 0.35,
                CognitiveSkill.MENTAL_ROTATION: 0.25,
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

        if len({cell.size for cell in visible}) != 1 or len({cell.color for cell in visible}) != 1 or len({cell.rotation for cell in visible}) != 1:
            return False

        def check_axis(axis: str) -> bool:
            for row in range(3):
                for col in range(3):
                    if row == MISSING_ROW and col == MISSING_COL:
                        continue
                    mirror = (row, 2 - col) if axis == "vertical" else (2 - row, col)
                    if mirror == (MISSING_ROW, MISSING_COL):
                        continue
                    cell = grid[row][col]
                    mirror_cell = grid[mirror[0]][mirror[1]]
                    if cell is None or mirror_cell is None:
                        return False
                    if (
                        cell.shape != mirror_cell.shape
                        or cell.size != mirror_cell.size
                        or cell.color != mirror_cell.color
                        or cell.rotation != mirror_cell.rotation
                    ):
                        return False
            return True

        return check_axis("vertical") or check_axis("horizontal")

    def explain(self) -> str:
        return (
            "The grid follows a mirror symmetry rule, reflecting shapes across an axis, "
            "and the missing cell completes that mirrored layout."
        )

    def difficulty(self) -> float:
        return 0.9

    def overlay(self, puzzle: MatrixPuzzle, seed: int) -> MatrixPuzzle:
        generated = self.generate(seed)
        grid: list[list[Figure | None]] = []
        for row in range(3):
            row_cells: list[Figure | None] = []
            for col in range(3):
                if puzzle.grid[row][col] is None:
                    row_cells.append(None)
                    continue
                row_cells.append(
                    Figure(
                        shape=generated.grid[row][col].shape,
                        rotation=puzzle.grid[row][col].rotation,
                        size=puzzle.grid[row][col].size,
                        color=puzzle.grid[row][col].color,
                    )
                )
            grid.append(row_cells)

        distractors = tuple(
            Figure(
                shape=distractor.shape,
                rotation=puzzle.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            )
            for distractor in generated.distractors
        )

        return MatrixPuzzle(
            seed=puzzle.seed,
            rules=puzzle.rules,
            grid=tuple(tuple(cell for cell in row) for row in grid),
            correct_answer=Figure(
                shape=generated.correct_answer.shape,
                rotation=puzzle.correct_answer.rotation,
                size=puzzle.correct_answer.size,
                color=puzzle.correct_answer.color,
            ),
            distractors=distractors,
            skill_profile=puzzle.skill_profile,
        )


class ColorRule(BaseRule):
    """Placeholder for future color rule implementation."""

    _register = False
    rule_type = RuleType.COLOR

    def generate(self, seed: int) -> MatrixPuzzle:
        raise NotImplementedError

    def validate(self, grid: tuple[tuple[Figure | None, ...], ...]) -> bool:
        raise NotImplementedError

    def explain(self) -> str:
        return "Color rule placeholder."

    def difficulty(self) -> float:
        return 0.0
