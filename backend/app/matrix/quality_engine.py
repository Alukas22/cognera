"""Puzzle quality validation and scoring for assessment-grade matrices."""

from __future__ import annotations

from typing import Callable

from .figure_components import component_distance
from .models import Figure, MatrixPuzzle, RuleType


_RULE_KEYWORDS: dict[RuleType, tuple[str, ...]] = {
    RuleType.ROTATION: ("rotation", "vridning"),
    RuleType.SHAPE: ("shape", "yttre form"),
    RuleType.COLOR: ("color", "inre markering"),
    RuleType.SIZE: ("size", "storlek"),
    RuleType.COUNT: ("count", "antal"),
    RuleType.POSITION: ("position", "rad", "kolumn", "placering"),
    RuleType.MIRROR: ("mirror", "symmetry", "spegling"),
}


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


class PuzzleQualityEngine:
    """Validate puzzle integrity and assign quality score components."""

    def __init__(self, quality_threshold: float = 0.62) -> None:
        self.quality_threshold = quality_threshold

    def assess(
        self,
        puzzle: MatrixPuzzle,
        *,
        is_logically_solved: bool,
        has_unambiguous_solution: bool,
        has_no_redundant_rules: bool,
        every_active_rule_contributes: bool,
        has_reasoning_depth: bool,
        requires_entire_matrix_observation: bool,
        rejects_trivial_single_dimension: bool,
        perceptual_validation_passed: bool,
    ) -> tuple[bool, float, dict[str, float], dict[str, bool]]:
        checks = self._validation_checks(
            puzzle,
            is_logically_solved=is_logically_solved,
            has_unambiguous_solution=has_unambiguous_solution,
            has_no_redundant_rules=has_no_redundant_rules,
            every_active_rule_contributes=every_active_rule_contributes,
            has_reasoning_depth=has_reasoning_depth,
            requires_entire_matrix_observation=requires_entire_matrix_observation,
            rejects_trivial_single_dimension=rejects_trivial_single_dimension,
            perceptual_validation_passed=perceptual_validation_passed,
        )
        components = self._quality_components(puzzle, checks)
        quality_score = _clamp(
            0.22 * components["uniqueness"]
            + 0.22 * components["logical_clarity"]
            + 0.20 * components["distractor_quality"]
            + 0.14 * components["explanation_quality"]
            + 0.12 * components["visual_diversity"]
            + 0.10 * components["reasoning_depth"]
        )
        accepted = all(checks.values()) and quality_score >= self.quality_threshold
        return accepted, quality_score, components, checks

    def difficulty_label(self, score: float, rule_count: int = 1) -> str:
        adjusted = _clamp(score + 0.09 * max(rule_count - 1, 0))
        if adjusted < 0.43:
            return "Easy"
        if adjusted < 0.49:
            return "Medium"
        if adjusted < 0.53:
            return "Hard"
        return "Expert"

    def _validation_checks(
        self,
        puzzle: MatrixPuzzle,
        *,
        is_logically_solved: bool,
        has_unambiguous_solution: bool,
        has_no_redundant_rules: bool,
        every_active_rule_contributes: bool,
        has_reasoning_depth: bool,
        requires_entire_matrix_observation: bool,
        rejects_trivial_single_dimension: bool,
        perceptual_validation_passed: bool,
    ) -> dict[str, bool]:
        option_keys = [self._figure_key(option.figure) for option in puzzle.options]
        distractor_keys = [self._figure_key(getattr(distractor, "figure", distractor)) for distractor in puzzle.distractors]

        correct_count = sum(1 for option in puzzle.options if option.is_correct)
        one_correct = correct_count == 1 and 0 <= puzzle.correct_index < len(puzzle.options)
        if one_correct:
            one_correct = puzzle.options[puzzle.correct_index].is_correct

        explanation_lower = puzzle.explanation.lower().strip()
        explanation_matches = bool(explanation_lower)
        if explanation_matches:
            for rule in puzzle.rules:
                keywords = _RULE_KEYWORDS.get(rule.type, (rule.type.value,))
                if not any(keyword in explanation_lower for keyword in keywords):
                    explanation_matches = False
                    break
        if explanation_matches:
            required_sections = [
                "översikt",
                "steg 1",
                "steg 2",
                "kontroll",
                "rätt svar",
                "alternativ a",
                "alternativ b",
                "alternativ c",
                "alternativ d",
                "alternativ e",
                "alternativ f",
            ]
            explanation_matches = all(section in explanation_lower for section in required_sections)

        active_rule_types = {rule.type for rule in puzzle.rules}
        distractor_options = [option for option in puzzle.options if not option.is_correct]
        distractor_reasons_ok = all(
            option.origin_rule in active_rule_types
            and option.figure != puzzle.correct_answer
            for option in distractor_options
        )

        return {
            "exactly_one_correct_answer": one_correct,
            "all_six_options_are_visually_unique": len(puzzle.options) == 6 and len(set(option_keys)) == 6,
            "no_duplicate_figures": len(distractor_keys) == len(set(distractor_keys)),
            "every_active_rule_contributes_to_solution": every_active_rule_contributes,
            "no_redundant_rules": has_no_redundant_rules,
            "puzzle_is_logically_solvable": is_logically_solved,
            "puzzle_is_unambiguous": has_unambiguous_solution,
            "minimum_reasoning_depth": has_reasoning_depth,
            "requires_entire_matrix_observation": requires_entire_matrix_observation,
            "rejects_trivial_single_dimension": rejects_trivial_single_dimension,
            "perceptual_validation_passed": perceptual_validation_passed,
            "explanation_matches_applied_rules": explanation_matches,
            "distractors_are_unique_and_meaningful": distractor_reasons_ok and len(distractor_options) == len(set(option_keys)) - 1,
        }

    def _quality_components(self, puzzle: MatrixPuzzle, checks: dict[str, bool]) -> dict[str, float]:
        uniqueness = 1.0 if (
            checks["all_six_options_are_visually_unique"] and checks["no_duplicate_figures"]
        ) else 0.0

        logical_clarity = (
            float(checks["puzzle_is_logically_solvable"])
            + float(checks["puzzle_is_unambiguous"])
            + float(checks["no_redundant_rules"])
            + float(checks["every_active_rule_contributes_to_solution"])
            + float(checks["minimum_reasoning_depth"])
            + float(checks["requires_entire_matrix_observation"])
            + float(checks["rejects_trivial_single_dimension"])
            + float(checks["perceptual_validation_passed"])
        ) / 8.0

        distractor_quality = self._distractor_quality(puzzle)

        explanation_quality = 0.0
        if checks["explanation_matches_applied_rules"]:
            lower = puzzle.explanation.lower()
            rule_steps = lower.count("steg ") + lower.count("kontroll")
            incorrect_steps = lower.count("alternativ ")
            expected_incorrect = max(0, len([option for option in puzzle.options if not option.is_correct]))
            coverage = 1.0 if expected_incorrect == 0 else min(1.0, incorrect_steps / expected_incorrect)
            explanation_quality = _clamp(0.5 + min(0.3, rule_steps * 0.15) + 0.2 * coverage)

        visual_diversity = self._visual_diversity(puzzle)
        reasoning_depth = self._reasoning_depth(puzzle)

        return {
            "uniqueness": uniqueness,
            "logical_clarity": logical_clarity,
            "distractor_quality": distractor_quality,
            "explanation_quality": explanation_quality,
            "visual_diversity": visual_diversity,
            "reasoning_depth": reasoning_depth,
        }

    def _distractor_quality(self, puzzle: MatrixPuzzle) -> float:
        distractors = [option for option in puzzle.options if not option.is_correct]
        if not distractors:
            return 0.0

        active_rules = {rule.type for rule in puzzle.rules}
        one_step_mistakes = 0
        plausible = 0
        for option in distractors:
            if option.origin_rule in active_rules:
                plausible += 1
            distance = component_distance(option.figure, puzzle.correct_answer)
            if distance == 1:
                one_step_mistakes += 1

        return _clamp(0.55 * (plausible / len(distractors)) + 0.45 * (one_step_mistakes / len(distractors)))

    def _visual_diversity(self, puzzle: MatrixPuzzle) -> float:
        visible = [cell for row in puzzle.grid for cell in row if cell is not None]
        if not visible:
            return 0.0
        shapes = len({cell.shape for cell in visible}) / 4.0
        colors = len({cell.color for cell in visible}) / 4.0
        sizes = len({cell.size for cell in visible}) / 3.0
        rotations = len({cell.rotation for cell in visible}) / 4.0
        return _clamp(0.35 * shapes + 0.2 * colors + 0.2 * sizes + 0.25 * rotations)

    def _reasoning_depth(self, puzzle: MatrixPuzzle) -> float:
        count = len(puzzle.rules)
        if count == 0:
            return 0.0
        depth = count / 3.0
        diversity = len({rule.type for rule in puzzle.rules}) / 3.0
        interaction = (count - 1) / 2.0 if count > 1 else 0.0
        return _clamp(0.45 * depth + 0.30 * diversity + 0.25 * interaction)

    def _attribute_distance(self, first: Figure, second: Figure) -> int:
        return component_distance(first, second)

    def _figure_key(self, figure: Figure) -> tuple[str, int, str, str]:
        return (figure.shape, figure.rotation, figure.size, figure.color)


def apply_candidate(
    puzzle: MatrixPuzzle,
    figure: Figure,
    validate: Callable[[tuple[tuple[Figure | None, ...], ...]], bool],
) -> bool:
    """Return whether replacing the missing cell with a candidate satisfies validation."""

    row, col = puzzle.missing_position
    working = [list(grid_row) for grid_row in puzzle.grid]
    working[row][col] = figure
    return validate(tuple(tuple(grid_row) for grid_row in working))
