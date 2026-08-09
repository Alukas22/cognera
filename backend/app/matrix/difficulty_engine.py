"""Cognitive difficulty estimation for matrix puzzles."""

from __future__ import annotations

import math

from .models import DifficultyProfile, Figure, MatrixPuzzle, RuleType


NON_LOCAL_RULE_TYPES = {RuleType.COUNT, RuleType.POSITION, RuleType.MIRROR, RuleType.SHAPE}
RELATIONAL_RULE_TYPES = {RuleType.COUNT, RuleType.POSITION, RuleType.MIRROR}


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


class CognitiveDifficultyEngine:
    """Estimate psychometric-style multi-dimensional puzzle difficulty."""

    def evaluate(self, puzzle: MatrixPuzzle) -> DifficultyProfile:
        working_memory = self._working_memory(puzzle)
        pattern_complexity = self._pattern_complexity(puzzle)
        visual_complexity = self._visual_complexity(puzzle)
        rule_complexity = self._rule_complexity(puzzle)
        abstraction = self._abstraction(puzzle)
        distractor_strength = self._distractor_strength(puzzle)

        overall = _clamp(
            0.25 * working_memory
            + 0.20 * rule_complexity
            + 0.15 * abstraction
            + 0.15 * pattern_complexity
            + 0.15 * visual_complexity
            + 0.10 * distractor_strength
        )

        return DifficultyProfile(
            overall=overall,
            working_memory=working_memory,
            pattern_complexity=pattern_complexity,
            visual_complexity=visual_complexity,
            rule_complexity=rule_complexity,
            abstraction=abstraction,
            distractor_strength=distractor_strength,
        )

    def _working_memory(self, puzzle: MatrixPuzzle) -> float:
        visible = self._visible_cells(puzzle)
        rule_count = len(puzzle.rules)
        rule_load = rule_count / 3.0
        interaction_load = (rule_count - 1) / 2.0 if rule_count > 1 else 0.0
        object_load = len(visible) / 8.0
        transformation_load = len(self._active_dimensions(puzzle)) / 4.0
        return _clamp(
            0.35 * rule_load
            + 0.25 * interaction_load
            + 0.20 * object_load
            + 0.20 * transformation_load
        )

    def _pattern_complexity(self, puzzle: MatrixPuzzle) -> float:
        rule_depth = len(puzzle.rules) / 3.0
        composition = (len(puzzle.rules) - 1) / 2.0 if len(puzzle.rules) > 1 else 0.0
        repeated_transformations = len(self._active_dimensions(puzzle)) / 4.0
        dependency_graph = self._dependency_density(puzzle)
        return _clamp(
            0.30 * rule_depth
            + 0.25 * composition
            + 0.20 * repeated_transformations
            + 0.25 * dependency_graph
        )

    def _visual_complexity(self, puzzle: MatrixPuzzle) -> float:
        visible = self._visible_cells(puzzle)
        object_count = len(visible) / 8.0
        shape_diversity = len({cell.shape for cell in visible}) / 4.0
        color_diversity = len({cell.color for cell in visible}) / 4.0
        position_entropy = self._position_entropy(puzzle)
        return _clamp(
            0.30 * object_count
            + 0.25 * shape_diversity
            + 0.15 * color_diversity
            + 0.30 * position_entropy
        )

    def _rule_complexity(self, puzzle: MatrixPuzzle) -> float:
        if not puzzle.rules:
            return 0.0
        base = sum(rule.difficulty for rule in puzzle.rules) / len(puzzle.rules)
        interaction = self._dependency_density(puzzle)
        diversity = len({rule.type for rule in puzzle.rules}) / 3.0
        return _clamp(0.55 * base + 0.25 * interaction + 0.20 * diversity)

    def _abstraction(self, puzzle: MatrixPuzzle) -> float:
        rule_count = len(puzzle.rules)
        independent_rules = len({rule.type for rule in puzzle.rules}) / 3.0
        hidden_dependencies = self._dependency_density(puzzle)
        relational_reasoning = sum(1 for rule in puzzle.rules if rule.type in RELATIONAL_RULE_TYPES) / max(rule_count, 1)
        non_local_reasoning = sum(1 for rule in puzzle.rules if rule.type in NON_LOCAL_RULE_TYPES) / max(rule_count, 1)
        return _clamp(
            0.25 * independent_rules
            + 0.25 * hidden_dependencies
            + 0.25 * relational_reasoning
            + 0.25 * non_local_reasoning
        )

    def _distractor_strength(self, puzzle: MatrixPuzzle) -> float:
        distractors = [option for option in puzzle.options if not option.is_correct]
        if not distractors:
            distractors = []
            for distractor in puzzle.distractors:
                distractors.append(distractor)
        if not distractors:
            return 0.0

        scores = []
        for distractor in distractors:
            figure = distractor.figure
            similarity = self._figure_similarity(figure, puzzle.solution)
            rule_overlap = 1.0 if getattr(distractor, "origin_rule", None) in {rule.type for rule in puzzle.rules} else 0.5
            visual_similarity = self._visual_similarity(figure, puzzle.solution)
            cognitive_plausibility = self._cognitive_plausibility(distractor, puzzle)
            scores.append(
                _clamp(
                    0.35 * similarity
                    + 0.25 * rule_overlap
                    + 0.20 * visual_similarity
                    + 0.20 * cognitive_plausibility
                )
            )
        return _clamp(sum(scores) / len(scores))

    def _visible_cells(self, puzzle: MatrixPuzzle) -> list[Figure]:
        return [cell for row in puzzle.grid for cell in row if cell is not None]

    def _active_dimensions(self, puzzle: MatrixPuzzle) -> list[str]:
        visible = self._visible_cells(puzzle)
        dimensions = []
        if len({cell.shape for cell in visible}) > 1 or any(rule.type in {RuleType.SHAPE, RuleType.COUNT, RuleType.POSITION, RuleType.MIRROR} for rule in puzzle.rules):
            dimensions.append("shape")
        if len({cell.rotation for cell in visible}) > 1 or any(rule.type == RuleType.ROTATION for rule in puzzle.rules):
            dimensions.append("rotation")
        if len({cell.size for cell in visible}) > 1 or any(rule.type == RuleType.SIZE for rule in puzzle.rules):
            dimensions.append("size")
        if len({cell.color for cell in visible}) > 1 or any(rule.type == RuleType.COLOR for rule in puzzle.rules):
            dimensions.append("color")
        return dimensions

    def _dependency_density(self, puzzle: MatrixPuzzle) -> float:
        rule_count = len(puzzle.rules)
        if rule_count <= 1:
            return 0.15 if puzzle.rules and puzzle.rules[0].type in NON_LOCAL_RULE_TYPES else 0.05

        cross_family_bonus = len({rule.type for rule in puzzle.rules}) / 3.0
        relational_bonus = sum(1 for rule in puzzle.rules if rule.type in RELATIONAL_RULE_TYPES) / rule_count
        active_dimensions = len(self._active_dimensions(puzzle)) / 4.0
        return _clamp(0.35 * cross_family_bonus + 0.35 * relational_bonus + 0.30 * active_dimensions)

    def _position_entropy(self, puzzle: MatrixPuzzle) -> float:
        visible = self._visible_cells(puzzle)
        if not visible:
            return 0.0
        counts = {}
        for cell in visible:
            counts[cell.shape] = counts.get(cell.shape, 0) + 1
        total = len(visible)
        entropy = 0.0
        for count in counts.values():
            probability = count / total
            entropy -= probability * math.log2(probability)
        max_entropy = math.log2(min(4, total)) if total > 1 else 1.0
        return _clamp(entropy / max_entropy if max_entropy else 0.0)

    def _figure_similarity(self, first: Figure, second: Figure) -> float:
        score = 0.0
        score += 0.30 if first.shape == second.shape else 0.0
        score += 0.20 if first.size == second.size else 0.0
        score += 0.20 if first.color == second.color else 0.0
        score += 0.30 * self._rotation_similarity(first.rotation, second.rotation)
        return _clamp(score)

    def _visual_similarity(self, first: Figure, second: Figure) -> float:
        matches = [first.shape == second.shape, first.rotation == second.rotation, first.size == second.size, first.color == second.color]
        return sum(1.0 for matched in matches if matched) / 4.0

    def _rotation_similarity(self, first: int, second: int) -> float:
        distance = min((first - second) % 360, (second - first) % 360)
        if distance == 0:
            return 1.0
        if distance == 90:
            return 0.66
        if distance == 180:
            return 0.33
        return 0.15

    def _cognitive_plausibility(self, distractor, puzzle: MatrixPuzzle) -> float:
        reason = getattr(distractor, "reason", None)
        origin_rule = getattr(distractor, "origin_rule", None)
        if origin_rule is None:
            return 0.4
        base = 0.7 if origin_rule in {rule.type for rule in puzzle.rules} else 0.4
        if reason is None:
            return _clamp(base)
        if reason.value.startswith("WRONG_"):
            base += 0.15
        if reason.value == "PARTIAL_PATTERN":
            base += 0.1
        return _clamp(base)


class DifficultyEngine:
    """Backward-compatible facade returning the overall difficulty score."""

    @classmethod
    def score(cls, puzzle: MatrixPuzzle) -> float:
        return CognitiveDifficultyEngine().evaluate(puzzle).overall