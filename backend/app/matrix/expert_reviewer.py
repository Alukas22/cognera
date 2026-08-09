"""Expert quality reviewer for psychometric matrix item screening."""

from __future__ import annotations

from .blind_solver import BlindSolver
from .models import MatrixPuzzle


def _clamp_10(value: float) -> float:
    return max(0.0, min(10.0, value))


class ExpertQualityReviewer:
    """Second-layer reviewer scoring items as an expert psychometrician proxy."""

    def __init__(self) -> None:
        self.blind_solver = BlindSolver()

    def review(
        self,
        puzzle: MatrixPuzzle,
        quality_components: dict[str, float],
        validation_results: dict[str, bool],
    ) -> tuple[dict[str, float], bool, dict[str, bool], dict[str, object]]:
        blind = self.blind_solver.choose(puzzle.grid, puzzle.options, puzzle.missing_position)

        scores = {
            "rule_visibility": _clamp_10(10.0 * quality_components.get("visual_diversity", 0.0)),
            "logical_consistency": _clamp_10(10.0 * quality_components.get("logical_clarity", 0.0)),
            "uniqueness_of_solution": self._uniqueness_score(puzzle, blind),
            "distractor_quality": _clamp_10(10.0 * quality_components.get("distractor_quality", 0.0)),
            "reasoning_depth": _clamp_10(10.0 * quality_components.get("reasoning_depth", 0.0)),
            "human_interpretability": self._human_interpretability_score(puzzle, blind),
            "explanation_quality": self._explanation_quality_score(puzzle),
            "overall_psychometric_quality": 0.0,
        }

        overall = (
            0.14 * scores["rule_visibility"]
            + 0.14 * scores["logical_consistency"]
            + 0.14 * scores["uniqueness_of_solution"]
            + 0.14 * scores["distractor_quality"]
            + 0.12 * scores["reasoning_depth"]
            + 0.12 * scores["human_interpretability"]
            + 0.20 * scores["explanation_quality"]
        )
        scores["overall_psychometric_quality"] = _clamp_10(overall)

        checks = {
            "multiple_reasonable_solutions_exist": blind.selected_index is None,
            "explanation_not_directly_derived": not self._explanation_directly_derived(puzzle),
            "reasoning_is_trivial": len(puzzle.rules) < 2,
            "single_row_or_column_sufficient": not validation_results.get("requires_entire_matrix_observation", False),
            "non_observable_transformation": not validation_results.get("perceptual_validation_passed", False),
            "weak_distractors": scores["distractor_quality"] < 8.0,
            "blind_solver_disagrees_with_generator": blind.selected_index is not None and blind.selected_index != puzzle.correct_index,
            "psychometric_score_below_threshold": scores["overall_psychometric_quality"] < 8.5,
        }

        accepted = not any(checks.values())
        diagnostics = {
            "blind_solver_selected_index": blind.selected_index,
            "blind_solver_score_gap": blind.score_gap,
        }
        return scores, accepted, checks, diagnostics

    def _uniqueness_score(self, puzzle: MatrixPuzzle, blind) -> float:
        if blind.selected_index is None:
            return 4.0
        if blind.selected_index == puzzle.correct_index:
            return 9.5
        return 5.0

    def _human_interpretability_score(self, puzzle: MatrixPuzzle, blind) -> float:
        base = 7.0
        if blind.selected_index == puzzle.correct_index:
            base += 2.0
        if blind.score_gap >= 0.05:
            base += 1.0
        return _clamp_10(base)

    def _explanation_quality_score(self, puzzle: MatrixPuzzle) -> float:
        lines = [line.strip() for line in puzzle.explanation.splitlines() if line.strip()]
        if not lines:
            return 0.0

        rule_lines = [line for line in lines if line.startswith("Rule ")]
        option_lines = [line for line in lines if line.startswith("Option ")]

        expected_options = len([option for option in puzzle.options if not option.is_correct])
        rule_coverage = min(1.0, len(rule_lines) / max(len(puzzle.rules), 1))
        option_coverage = min(1.0, len(option_lines) / max(expected_options, 1))

        return _clamp_10(10.0 * (0.6 * rule_coverage + 0.4 * option_coverage))

    def _explanation_directly_derived(self, puzzle: MatrixPuzzle) -> bool:
        explanation = puzzle.explanation
        if not explanation:
            return False
        for index, rule in enumerate(puzzle.rules, start=1):
            if f"Rule {index}:" not in explanation:
                return False
            if str(rule.value) not in explanation:
                return False
        return True
