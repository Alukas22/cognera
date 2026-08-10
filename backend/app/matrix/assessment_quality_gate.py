"""Assessment quality gate for expert-grade matrix puzzle release."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .blind_solver import BlindSolver
from .figure_components import component_distance, derive_components
from .models import Figure, MatrixPuzzle, RuleType
from .rules import BaseRule


def _sentence_count(text: str) -> int:
    trimmed = text.strip()
    if not trimmed:
        return 0
    count = 0
    for marker in (".", "?", "!"):
        count += trimmed.count(marker)
    return max(1, count)


def _option_complexity(figure: Figure) -> float:
    components = derive_components(figure)
    return (
        float(components.corners) * 0.42
        + float(components.repeated_count) * 1.0
        + float(components.nested_depth) * 0.65
    )


@dataclass(frozen=True)
class AssessmentQualityReview:
    passed: bool
    checks: dict[str, bool]
    diagnostics: dict[str, object]


class AssessmentQualityGate:
    """Reject mediocre puzzles before they reach the user."""

    _REQUIRED_SECTION_ORDER = [
        "Översikt",
        "Steg 1",
        "Steg 2",
        "Kontroll",
        "Rätt svar",
        "Alternativ A",
        "Alternativ B",
        "Alternativ C",
        "Alternativ D",
        "Alternativ E",
        "Alternativ F",
    ]

    _REQUIRED_BULLET_PREFIX = {
        "Översikt": "- Vad är huvudidén?",
        "Steg 1": "- Vad händer i raderna?",
        "Steg 2": "- Vad händer i kolumnerna?",
        "Kontroll": "- Varför fungerar båda samtidigt?",
        "Rätt svar": "- Varför är detta korrekt?",
        "Alternativ A": "- Varför är detta fel?",
        "Alternativ B": "- Varför är detta fel?",
        "Alternativ C": "- Varför är detta fel?",
        "Alternativ D": "- Varför är detta fel?",
        "Alternativ E": "- Varför är detta fel?",
        "Alternativ F": "- Varför är detta fel?",
    }

    _CRITICAL_ACCEPTANCE_CHECKS = (
        "assessment_explanation_sections_present",
        "assessment_explanation_only_bullets_no_paragraphs",
        "assessment_explanation_required_prompts_present",
        "assessment_explanation_max_two_sentences_per_bullet",
        "assessment_dominant_reasoning_blind_solver_agrees",
        "assessment_distractors_violate_exactly_one_rule",
    )

    def __init__(self) -> None:
        self.blind_solver = BlindSolver()

    def evaluate(
        self,
        puzzle: MatrixPuzzle,
        selected_rules: list[BaseRule],
        human_checks: dict[str, bool],
        human_diagnostics: dict[str, object],
    ) -> AssessmentQualityReview:
        readability_checks, readability_diag = self._human_readability_checks(puzzle)
        dominant_checks, dominant_diag = self._dominant_reasoning_checks(
            puzzle,
            human_checks,
            human_diagnostics,
        )
        distractor_checks, distractor_diag = self._distractor_quality_checks(puzzle, selected_rules)
        balance_checks, balance_diag = self._visual_balance_checks(puzzle)
        explanation_checks, explanation_diag = self._explanation_quality_checks(puzzle)

        checks = {
            **readability_checks,
            **dominant_checks,
            **distractor_checks,
            **balance_checks,
            **explanation_checks,
        }

        diagnostics = {
            "human_readability": readability_diag,
            "dominant_reasoning": dominant_diag,
            "distractor_quality": distractor_diag,
            "visual_balance": balance_diag,
            "explanation_quality": explanation_diag,
        }

        passed = all(checks.get(name, False) for name in self._CRITICAL_ACCEPTANCE_CHECKS)

        return AssessmentQualityReview(
            passed=passed,
            checks=checks,
            diagnostics=diagnostics,
        )

    def _human_readability_checks(self, puzzle: MatrixPuzzle) -> tuple[dict[str, bool], dict[str, object]]:
        visible = [cell for row in puzzle.grid for cell in row if cell is not None]
        components = [derive_components(cell) for cell in visible]

        if not components:
            checks = {
                "assessment_readability_not_cluttered": False,
                "assessment_readability_structure_distinguishable": False,
                "assessment_readability_not_detail_dominated": False,
                "assessment_readability_elegant_not_confusing": False,
            }
            return checks, {"reason": "no_visible_cells"}

        avg_corners = sum(component.corners for component in components) / len(components)
        avg_repeat = sum(component.repeated_count for component in components) / len(components)
        rotation_variety = len({component.orientation for component in components})
        shape_variety = len({cell.shape for cell in visible})

        clutter_index = 0.44 * (avg_corners / 6.0) + 0.36 * (avg_repeat / 3.0) + 0.20 * (rotation_variety / 4.0)
        visual_complexity = puzzle.difficulty_profile.visual_complexity if puzzle.difficulty_profile else 1.0

        checks = {
            "assessment_readability_not_cluttered": clutter_index <= 0.76 and visual_complexity <= 0.88,
            "assessment_readability_structure_distinguishable": shape_variety >= 2 and rotation_variety >= 2,
            "assessment_readability_not_detail_dominated": max(component.repeated_count for component in components) <= 3,
            "assessment_readability_elegant_not_confusing": visual_complexity <= 0.82,
        }

        diagnostics = {
            "avg_corners": round(avg_corners, 4),
            "avg_repeated_detail": round(avg_repeat, 4),
            "shape_variety": shape_variety,
            "rotation_variety": rotation_variety,
            "clutter_index": round(clutter_index, 4),
            "visual_complexity": round(visual_complexity, 4),
        }
        return checks, diagnostics

    def _dominant_reasoning_checks(
        self,
        puzzle: MatrixPuzzle,
        human_checks: dict[str, bool],
        human_diagnostics: dict[str, object],
    ) -> tuple[dict[str, bool], dict[str, object]]:
        blind = self.blind_solver.choose(puzzle.grid, puzzle.options, puzzle.missing_position)
        alternative_rule_set_count = int(human_diagnostics.get("alternative_rule_set_count", 1))

        checks = {
            "assessment_dominant_reasoning_blind_solver_agrees": blind.selected_index == puzzle.correct_index,
            "assessment_dominant_reasoning_gap_is_clear": blind.score_gap >= 0.05,
            "assessment_dominant_reasoning_no_viable_alternative_rules": alternative_rule_set_count == 0,
            "assessment_dominant_reasoning_human_unambiguous": bool(human_checks.get("human_reasoning_unambiguous")),
        }

        diagnostics = {
            "blind_solver_selected_index": blind.selected_index,
            "blind_solver_score_gap": round(blind.score_gap, 4),
            "correct_index": puzzle.correct_index,
            "alternative_rule_set_count": alternative_rule_set_count,
        }
        return checks, diagnostics

    def _distractor_quality_checks(
        self,
        puzzle: MatrixPuzzle,
        selected_rules: list[BaseRule],
    ) -> tuple[dict[str, bool], dict[str, object]]:
        wrong_options = [option for option in puzzle.options if not option.is_correct]
        violation_counts: dict[str, int] = {}
        violation_map: dict[str, list[str]] = {}
        reason_present = True
        plausible = True

        for option in wrong_options:
            changed_attributes = self._changed_attributes(puzzle.correct_answer, option.figure)
            violation_counts[option.label] = len(changed_attributes)
            violation_map[option.label] = changed_attributes
            if option.reason is None or option.origin_rule is None:
                reason_present = False
            if not 1 <= component_distance(option.figure, puzzle.correct_answer) <= 3:
                plausible = False

        pairwise_distances = {}
        near_duplicates = 0
        for left, right in combinations(wrong_options, 2):
            distance = component_distance(left.figure, right.figure)
            pairwise_distances[f"{left.label}-{right.label}"] = distance
            if distance <= 1:
                near_duplicates += 1

        exactly_one = all(count == 1 for count in violation_counts.values()) and len(violation_counts) == 5

        checks = {
            "assessment_distractors_violate_exactly_one_rule": exactly_one,
            "assessment_distractors_not_near_duplicate": near_duplicates == 0,
            "assessment_distractors_plausible_not_obvious": plausible,
            "assessment_distractors_have_explicit_reason": reason_present,
        }

        diagnostics = {
            "violation_counts": violation_counts,
            "violated_rule_types": violation_map,
            "pairwise_component_distances": pairwise_distances,
            "near_duplicate_pairs": near_duplicates,
        }
        return checks, diagnostics

    def _changed_attributes(self, correct: Figure, candidate: Figure) -> list[str]:
        changed: list[str] = []
        if candidate.shape != correct.shape:
            changed.append("shape")
        if candidate.rotation != correct.rotation:
            changed.append("rotation")
        if candidate.size != correct.size:
            changed.append("size")
        if candidate.color != correct.color:
            changed.append("color")
        return changed

    def _visual_balance_checks(self, puzzle: MatrixPuzzle) -> tuple[dict[str, bool], dict[str, object]]:
        complexities = [_option_complexity(option.figure) for option in puzzle.options]
        spread = max(complexities) - min(complexities) if complexities else 0.0
        avg = sum(complexities) / len(complexities) if complexities else 0.0

        outlier_count = 0
        for value in complexities:
            if abs(value - avg) > 2.4:
                outlier_count += 1

        size_counts: dict[str, int] = {}
        for option in puzzle.options:
            size_counts[option.figure.size] = size_counts.get(option.figure.size, 0) + 1
        correct_size = puzzle.options[puzzle.correct_index].figure.size

        checks = {
            "assessment_visual_balance_no_unique_outlier": outlier_count == 0,
            "assessment_visual_balance_detail_spread_limited": spread <= 4.6,
            "assessment_visual_balance_correct_not_unique_size": size_counts.get(correct_size, 0) >= 2,
            "assessment_visual_balance_uniform_styling": True,
        }

        diagnostics = {
            "option_complexities": [round(value, 4) for value in complexities],
            "complexity_spread": round(spread, 4),
            "complexity_mean": round(avg, 4),
            "outlier_count": outlier_count,
            "size_distribution": size_counts,
            "correct_option_size": correct_size,
        }
        return checks, diagnostics

    def _explanation_quality_checks(self, puzzle: MatrixPuzzle) -> tuple[dict[str, bool], dict[str, object]]:
        explanation = puzzle.explanation or ""
        lines = [line.strip() for line in explanation.splitlines()]
        non_empty = [line for line in lines if line]

        section_positions: dict[str, int] = {}
        for index, line in enumerate(non_empty):
            if line in self._REQUIRED_SECTION_ORDER:
                section_positions[line] = index

        ordered_sections_present = all(section in section_positions for section in self._REQUIRED_SECTION_ORDER)
        ordered = False
        if ordered_sections_present:
            ordered = [section_positions[section] for section in self._REQUIRED_SECTION_ORDER] == sorted(
                section_positions[section] for section in self._REQUIRED_SECTION_ORDER
            )

        no_paragraphs = all(line in self._REQUIRED_SECTION_ORDER or line.startswith("- ") for line in non_empty)

        section_bullets: dict[str, str] = {}
        if ordered_sections_present and ordered:
            for index, section in enumerate(self._REQUIRED_SECTION_ORDER):
                start = section_positions[section] + 1
                end = (
                    section_positions[self._REQUIRED_SECTION_ORDER[index + 1]]
                    if index + 1 < len(self._REQUIRED_SECTION_ORDER)
                    else len(non_empty)
                )
                bullets = [line for line in non_empty[start:end] if line.startswith("- ")]
                if bullets:
                    section_bullets[section] = bullets[0]

        prefixes_ok = True
        bullets_short = True
        for section, prefix in self._REQUIRED_BULLET_PREFIX.items():
            bullet = section_bullets.get(section, "")
            if not bullet.startswith(prefix):
                prefixes_ok = False
                continue
            if _sentence_count(bullet) > 2:
                bullets_short = False

        checks = {
            "assessment_explanation_sections_present": ordered_sections_present and ordered,
            "assessment_explanation_only_bullets_no_paragraphs": no_paragraphs,
            "assessment_explanation_required_prompts_present": prefixes_ok,
            "assessment_explanation_max_two_sentences_per_bullet": bullets_short,
        }

        diagnostics = {
            "section_positions": section_positions,
            "captured_section_bullets": section_bullets,
            "non_empty_line_count": len(non_empty),
        }
        return checks, diagnostics

    def _failed_rule_types(
        self,
        puzzle: MatrixPuzzle,
        candidate: Figure,
        selected_rules: list[BaseRule],
    ) -> list[str]:
        grid = self._with_candidate(puzzle, candidate)
        failed: list[str] = []
        for rule in selected_rules:
            if not rule.validate(grid):
                failed.append(rule.rule_type.value)
        return failed

    def _with_candidate(self, puzzle: MatrixPuzzle, candidate: Figure) -> tuple[tuple[Figure, ...], ...]:
        row, col = puzzle.missing_position
        built: list[tuple[Figure, ...]] = []
        for row_index in range(3):
            row_cells: list[Figure] = []
            for col_index in range(3):
                cell = puzzle.grid[row_index][col_index]
                if cell is None:
                    if (row_index, col_index) != (row, col):
                        raise ValueError("Matrix contains unexpected empty cell.")
                    row_cells.append(candidate)
                else:
                    row_cells.append(cell)
            built.append(tuple(row_cells))
        return tuple(built)
