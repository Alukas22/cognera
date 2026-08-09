"""Perceptual validation for observable puzzle transformations."""

from __future__ import annotations

import re

from .models import Figure, MatrixPuzzle, RuleType


ROTATIONALLY_SYMMETRIC_SHAPES = {"circle", "square", "diamond"}
MIRROR_SYMMETRIC_SHAPES = {"circle", "square", "diamond"}
SIZE_ORDER = {"small": 0, "medium": 1, "large": 2}
COLOR_LUMINANCE = {
    "black": 0.05,
    "blue": 0.18,
    "red": 0.45,
    "white": 0.95,
}


class PerceptualValidationEngine:
    """Reject puzzles whose intended transformation is not visually observable."""

    def validate(self, puzzle: MatrixPuzzle) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        visible = [cell for row in puzzle.grid for cell in row if cell is not None]

        for rule in puzzle.rules:
            if rule.type == RuleType.ROTATION and not self._rotation_is_observable(visible, str(rule.value)):
                reasons.append("invisible_rotation")
            if rule.type == RuleType.MIRROR and not self._mirror_is_observable(puzzle, str(rule.value)):
                reasons.append("invisible_mirror")
            if rule.type == RuleType.SIZE and not self._size_is_observable(visible):
                reasons.append("imperceptible_size_change")
            if rule.type == RuleType.COLOR and not self._color_is_observable(visible):
                reasons.append("imperceptible_color_change")

        if not self._rules_inferable_from_visible_evidence(puzzle):
            reasons.append("rule_not_inferable_from_visible_evidence")

        return (len(reasons) == 0), reasons

    def _rotation_is_observable(self, visible: list[Figure], rule_value: str) -> bool:
        step = self._extract_rotation_step(rule_value)
        if step is None:
            return False

        shapes = {cell.shape for cell in visible}
        if not shapes:
            return False

        if shapes.issubset(ROTATIONALLY_SYMMETRIC_SHAPES):
            return False

        rotations = {cell.rotation for cell in visible}
        if len(rotations) <= 1:
            return False

        if step in {90, 180, 270} and any(shape in ROTATIONALLY_SYMMETRIC_SHAPES for shape in shapes):
            # At least one asymmetrical shape must carry the rotation signal.
            asymmetrical_rotations = {
                cell.rotation
                for cell in visible
                if cell.shape not in ROTATIONALLY_SYMMETRIC_SHAPES
            }
            return len(asymmetrical_rotations) > 1

        return True

    def _mirror_is_observable(self, puzzle: MatrixPuzzle, rule_value: str) -> bool:
        axis = "vertical" if "vertical" in rule_value.lower() else "horizontal"
        visible = [cell for row in puzzle.grid for cell in row if cell is not None]
        if not visible:
            return False

        if {cell.shape for cell in visible}.issubset(MIRROR_SYMMETRIC_SHAPES):
            return False

        evidence_pairs = 0
        for row in range(3):
            for col in range(3):
                if puzzle.grid[row][col] is None:
                    continue
                mirror = (row, 2 - col) if axis == "vertical" else (2 - row, col)
                mirror_cell = puzzle.grid[mirror[0]][mirror[1]]
                if mirror_cell is None:
                    continue
                if puzzle.grid[row][col].shape == mirror_cell.shape:
                    evidence_pairs += 1

        return evidence_pairs >= 2

    def _size_is_observable(self, visible: list[Figure]) -> bool:
        if not visible:
            return False
        sizes = {cell.size for cell in visible if cell.size in SIZE_ORDER}
        if len(sizes) <= 1:
            return False
        spread = max(SIZE_ORDER[size] for size in sizes) - min(SIZE_ORDER[size] for size in sizes)
        return spread >= 2

    def _color_is_observable(self, visible: list[Figure]) -> bool:
        if not visible:
            return False
        colors = {cell.color for cell in visible if cell.color in COLOR_LUMINANCE}
        if len(colors) <= 1:
            return False
        spread = max(COLOR_LUMINANCE[color] for color in colors) - min(COLOR_LUMINANCE[color] for color in colors)
        return spread >= 0.35

    def _rules_inferable_from_visible_evidence(self, puzzle: MatrixPuzzle) -> bool:
        visible = [cell for row in puzzle.grid for cell in row if cell is not None]
        if not visible:
            return False

        for rule in puzzle.rules:
            if rule.type == RuleType.ROTATION:
                if not self._rotation_is_observable(visible, str(rule.value)):
                    return False
            elif rule.type == RuleType.MIRROR:
                if not self._mirror_is_observable(puzzle, str(rule.value)):
                    return False
            elif rule.type == RuleType.SIZE:
                if not self._size_is_observable(visible):
                    return False
            elif rule.type == RuleType.COLOR:
                if not self._color_is_observable(visible):
                    return False

        return True

    def _extract_rotation_step(self, rule_value: str) -> int | None:
        match = re.search(r"(\d+)", rule_value)
        if not match:
            return None
        return int(match.group(1))
