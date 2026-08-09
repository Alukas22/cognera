"""Matrix puzzle generation utilities."""

from __future__ import annotations

import random
from typing import Iterable

from .models import Figure, MatrixPuzzle, Rule, RuleType


SHAPES = ["triangle", "square", "circle", "diamond"]
SIZES = ["small", "medium", "large"]
COLORS = ["black", "white", "red", "blue"]
ROTATIONS = (0, 90, 180, 270)
ANSWER_ALTERNATIVES = 4
MISSING_ROW = 2
MISSING_COL = 2


class RotationGenerator:
    """Deterministic Raven-style rotation puzzle generator."""

    def generate(self, seed: int) -> MatrixPuzzle:
        """Generate a deterministic 3x3 rotation matrix puzzle.

        The last cell is hidden and must be inferred from the rotation rule.
        """

        rng = random.Random(seed)
        base_shape = rng.choice(SHAPES)
        base_size = rng.choice(SIZES)
        base_color = rng.choice(COLORS)
        step = rng.choice([90, 180, 270])
        base_rotation = rng.choice(ROTATIONS)
        rule = Rule(
            type=RuleType.ROTATION,
            value=f"{step}° clockwise",
            difficulty=1.0,
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

        wrong_rotations = [rotation for rotation in ROTATIONS if rotation != correct_rotation]
        distractors = tuple(
            Figure(
                shape=base_shape,
                rotation=rotation,
                size=base_size,
                color=base_color,
            )
            for rotation in self._select_distractor_rotations(rng, wrong_rotations)
        )

        return MatrixPuzzle(
            seed=seed,
            rules=(rule,),
            grid=tuple(tuple(cell for cell in row) for row in grid),
            correct_answer=correct_answer,
            distractors=distractors,
        )

    def validate(self, puzzle: MatrixPuzzle) -> bool:
        """Validate that a generated matrix puzzle follows the rotation rule."""

        visible_cells = [cell for row in puzzle.grid for cell in row if cell is not None]
        if len(visible_cells) != 8:
            return False

        shapes = {cell.shape for cell in visible_cells}
        sizes = {cell.size for cell in visible_cells}
        colors = {cell.color for cell in visible_cells}
        if len(shapes) != 1 or len(sizes) != 1 or len(colors) != 1:
            return False

        if puzzle.rules != tuple(puzzle.rules):
            return False

        rule = puzzle.rules[0] if puzzle.rules else None
        if rule is None or rule.type != RuleType.ROTATION:
            return False

        expected_rotation = self._infer_expected_rotation(visible_cells, rule.value)
        if expected_rotation is None:
            return False

        if puzzle.correct_answer.rotation != expected_rotation:
            return False

        if len(puzzle.distractors) != ANSWER_ALTERNATIVES - 1:
            return False

        unique_choices = {puzzle.correct_answer, *puzzle.distractors}
        if len(unique_choices) != ANSWER_ALTERNATIVES:
            return False

        return True

    def _select_distractor_rotations(self, rng: random.Random, options: list[int]) -> list[int]:
        rng.shuffle(options)
        return options[:ANSWER_ALTERNATIVES - 1]

    def _infer_expected_rotation(self, visible_cells: Iterable[Figure], rule_value: str) -> int | None:
        try:
            step = int(rule_value.split("°")[0])
        except ValueError:
            return None

        first_rotation = visible_cells[0].rotation
        # The puzzle uses an incremental rotation pattern in reading order.
        return (first_rotation + step * 8) % 360
