"""Human solvability gate for psychometric puzzle acceptance."""

from __future__ import annotations

from dataclasses import dataclass

from .blind_solver import BlindSolver
from .figure_components import component_distance
from .models import Figure, MatrixPuzzle, RuleType
from .rules import BaseRule


_RULE_ATTRIBUTE_MAP: dict[RuleType, set[str]] = {
    RuleType.ROTATION: {"rotation"},
    RuleType.SIZE: {"size"},
    RuleType.COLOR: {"color"},
    RuleType.SHAPE: {"shape"},
    RuleType.COUNT: {"shape"},
    RuleType.POSITION: {"shape"},
    RuleType.MIRROR: {"shape"},
}


@dataclass(frozen=True)
class HumanSolvabilityReview:
    passed: bool
    checks: dict[str, bool]
    diagnostics: dict[str, object]


class HumanSolvabilityGate:
    """Reject puzzles that are not confidently solvable by humans."""

    _CRITICAL_CHECKS = (
        "human_solvability_primary_rule_dominant",
        "human_solvability_primary_rule_visually_discoverable",
        "human_solvability_secondary_rules_refine_only",
        "human_solvability_expert_step_by_step_explainable",
        "human_solvability_distractors_are_realistic_mistakes",
        "human_solvability_likely_solver_consensus",
    )

    def __init__(self) -> None:
        self.blind_solver = BlindSolver()

    def evaluate(
        self,
        puzzle: MatrixPuzzle,
        selected_rules: list[BaseRule],
        *,
        human_checks: dict[str, bool],
        human_diagnostics: dict[str, object],
        reviewer_accepted: bool,
        reviewer_checks: dict[str, bool],
    ) -> HumanSolvabilityReview:
        primary_checks, primary_diag = self._primary_rule_checks(selected_rules, puzzle.seed)
        explainable_checks = self._expert_explainability_checks(human_checks, reviewer_accepted, reviewer_checks)
        distractor_checks, distractor_diag = self._distractor_realism_checks(puzzle, selected_rules)
        consensus_checks, consensus_diag = self._solver_consensus_checks(puzzle, human_checks, human_diagnostics)

        checks = {
            **primary_checks,
            **explainable_checks,
            **distractor_checks,
            **consensus_checks,
        }
        diagnostics = {
            "primary_rule_analysis": primary_diag,
            "expert_explainability": {
                "reviewer_accepted": reviewer_accepted,
                "reviewer_checks": reviewer_checks,
            },
            "distractor_realism": distractor_diag,
            "solver_consensus": consensus_diag,
        }

        passed = all(checks.get(name, False) for name in self._CRITICAL_CHECKS)
        return HumanSolvabilityReview(passed=passed, checks=checks, diagnostics=diagnostics)

    def _primary_rule_checks(
        self,
        selected_rules: list[BaseRule],
        seed: int,
    ) -> tuple[dict[str, bool], dict[str, object]]:
        impacts = self._rule_visible_impacts(selected_rules, seed)
        if not impacts:
            checks = {
                "human_solvability_primary_rule_dominant": False,
                "human_solvability_primary_rule_visually_discoverable": False,
                "human_solvability_secondary_rules_refine_only": False,
            }
            return checks, {"reason": "unable_to_compute_rule_impacts"}

        ordered = sorted(impacts, key=lambda item: item["changed_visible_cells"], reverse=True)
        primary = ordered[0]
        primary_count = int(primary["changed_visible_cells"])
        secondary_counts = [int(item["changed_visible_cells"]) for item in ordered[1:]]
        second_count = secondary_counts[0] if secondary_counts else 0

        dominant = primary_count >= 3 and (not secondary_counts or primary_count >= second_count + 1)
        discoverable = (
            dominant
            and primary_count >= 3
            and int(primary["rows_affected"]) >= 2
            and int(primary["cols_affected"]) >= 1
        )
        secondary_refine = (
            len(ordered) == 1
            or (
                max(secondary_counts, default=0) <= primary_count
            )
        )

        checks = {
            "human_solvability_primary_rule_dominant": dominant,
            "human_solvability_primary_rule_visually_discoverable": discoverable,
            "human_solvability_secondary_rules_refine_only": secondary_refine,
        }
        diagnostics = {
            "rule_impacts": ordered,
            "primary_rule_type": primary["rule_type"],
            "primary_visible_impact": primary_count,
            "secondary_visible_impacts": secondary_counts,
        }
        return checks, diagnostics

    def _expert_explainability_checks(
        self,
        human_checks: dict[str, bool],
        reviewer_accepted: bool,
        reviewer_checks: dict[str, bool],
    ) -> dict[str, bool]:
        return {
            "human_solvability_expert_step_by_step_explainable": (
                reviewer_accepted
                and bool(human_checks.get("full_matrix_reconstructable_from_rules"))
                and bool(human_checks.get("no_hidden_assumptions"))
                and bool(human_checks.get("explanation_derived_from_rule_objects"))
                and bool(human_checks.get("explanation_explains_every_row"))
                and bool(human_checks.get("explanation_explains_every_column"))
                and bool(reviewer_checks.get("explanation_is_concrete", True))
            )
        }

    def _distractor_realism_checks(
        self,
        puzzle: MatrixPuzzle,
        selected_rules: list[BaseRule],
    ) -> tuple[dict[str, bool], dict[str, object]]:
        selected_types = {rule.rule_type for rule in selected_rules}
        wrong_options = [option for option in puzzle.options if not option.is_correct]

        realistic_count = 0
        distractor_diagnostics: list[dict[str, object]] = []
        for option in wrong_options:
            changed = self._changed_attributes(puzzle.correct_answer, option.figure)
            violates_single = self._violates_exactly_one_rule(puzzle, option.figure, selected_rules)
            has_metadata = option.reason is not None and option.origin_rule is not None
            origin_is_active = option.origin_rule in selected_types if option.origin_rule is not None else False
            origin_attribute_match = (
                option.origin_rule is not None
                and bool(_RULE_ATTRIBUTE_MAP.get(option.origin_rule, set()) & set(changed))
            )
            distance = component_distance(option.figure, puzzle.correct_answer)
            plausible_distance = 1 <= distance <= 4
            bounded_change = 1 <= len(changed) <= 2
            rule_consistent = violates_single or (has_metadata and origin_is_active and origin_attribute_match)

            realistic = rule_consistent and plausible_distance and bounded_change
            if realistic:
                realistic_count += 1
            distractor_diagnostics.append(
                {
                    "label": option.label,
                    "changed_attributes": changed,
                    "violates_exactly_one_rule": violates_single,
                    "has_reason_metadata": has_metadata,
                    "origin_is_active_rule": origin_is_active,
                    "origin_matches_changed_attribute": origin_attribute_match,
                    "component_distance": distance,
                    "bounded_attribute_change": bounded_change,
                    "rule_consistent": rule_consistent,
                    "is_realistic": realistic,
                }
            )

        checks = {
            "human_solvability_distractors_are_realistic_mistakes": realistic_count >= 4 and len(wrong_options) == 5,
        }
        diagnostics = {
            "distractors": distractor_diagnostics,
            "realistic_count": realistic_count,
        }
        return checks, diagnostics

    def _solver_consensus_checks(
        self,
        puzzle: MatrixPuzzle,
        human_checks: dict[str, bool],
        human_diagnostics: dict[str, object],
    ) -> tuple[dict[str, bool], dict[str, object]]:
        blind = self.blind_solver.choose(puzzle.grid, puzzle.options, puzzle.missing_position)
        alternative_rule_sets = int(human_diagnostics.get("alternative_rule_set_count", 1))
        candidate_solution_count = int(human_diagnostics.get("candidate_solution_count", 2))

        likely_consensus = (
            blind.selected_index == puzzle.correct_index
            and blind.score_gap >= 0.05
            and bool(human_checks.get("human_reasoning_unambiguous"))
            and alternative_rule_sets <= 1
            and candidate_solution_count <= 2
        )
        checks = {
            "human_solvability_likely_solver_consensus": likely_consensus,
        }
        diagnostics = {
            "blind_solver_selected_index": blind.selected_index,
            "correct_index": puzzle.correct_index,
            "blind_solver_score_gap": round(blind.score_gap, 4),
            "alternative_rule_set_count": alternative_rule_sets,
            "candidate_solution_count": candidate_solution_count,
        }
        return checks, diagnostics

    def _rule_visible_impacts(self, selected_rules: list[BaseRule], seed: int) -> list[dict[str, object]]:
        full = self._reconstruct_from_rules(selected_rules, seed)
        if full is None:
            return []

        impacts: list[dict[str, object]] = []
        for index, rule in enumerate(selected_rules):
            reduced_rules = selected_rules[:index] + selected_rules[index + 1 :]
            reduced = self._reconstruct_from_rules(reduced_rules, seed)
            if reduced is None:
                continue

            changed = 0
            rows: set[int] = set()
            cols: set[int] = set()
            for row in range(3):
                for col in range(3):
                    if full.grid[row][col] is None:
                        continue
                    if full.grid[row][col] != reduced.grid[row][col]:
                        changed += 1
                        rows.add(row)
                        cols.add(col)

            impacts.append(
                {
                    "rule_type": rule.rule_type.value,
                    "changed_visible_cells": changed,
                    "rows_affected": len(rows),
                    "cols_affected": len(cols),
                }
            )
        return impacts

    def _reconstruct_from_rules(self, selected_rules: list[BaseRule], seed: int) -> MatrixPuzzle | None:
        if not selected_rules:
            return None
        try:
            puzzle = selected_rules[0].generate(seed)
            for index, rule in enumerate(selected_rules[1:], start=1):
                puzzle = rule.overlay(puzzle, seed + index)
            return puzzle
        except Exception:
            return None

    def _violates_exactly_one_rule(
        self,
        puzzle: MatrixPuzzle,
        candidate: Figure,
        selected_rules: list[BaseRule],
    ) -> bool:
        failed = 0
        grid = self._with_candidate(puzzle, candidate)
        for rule in selected_rules:
            if not rule.validate(grid):
                failed += 1
                if failed > 1:
                    return False
        return failed == 1

    def _with_candidate(self, puzzle: MatrixPuzzle, candidate: Figure) -> tuple[tuple[Figure, ...], ...]:
        row, col = puzzle.missing_position
        built: list[tuple[Figure, ...]] = []
        for row_index in range(3):
            row_cells: list[Figure] = []
            for col_index in range(3):
                cell = puzzle.grid[row_index][col_index]
                if cell is None:
                    if (row_index, col_index) != (row, col):
                        raise ValueError("Unexpected empty cell in puzzle grid.")
                    row_cells.append(candidate)
                else:
                    row_cells.append(cell)
            built.append(tuple(row_cells))
        return tuple(built)

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