"""Plugin-based rule engine for Cognera matrix puzzles."""

from __future__ import annotations

import inspect
import random
from collections import Counter
from dataclasses import replace
from itertools import combinations, permutations
from typing import Iterable

from .answer_options import AnswerOptionEngine
from .difficulty_engine import CognitiveDifficultyEngine
from .expert_reviewer import ExpertQualityReviewer
from .explainer import explain_puzzle
from .models import Figure, MatrixPuzzle, Rule, SkillProfile
from .perceptual_validation import PerceptualValidationEngine
from .quality_engine import PuzzleQualityEngine
from .rules import BaseRule, MISSING_COL, MISSING_ROW, RuleType


class RuleConstraintEngine:
    """Validate rule combinations for compatibility before generation."""

    def __init__(self, sample_seeds: tuple[int, ...] = tuple(range(20))) -> None:
        self.sample_seeds = sample_seeds
        self.validation_reasons: list[str] = []
        self.validated_rules: list[BaseRule] = []
        self.answer_option_engine = AnswerOptionEngine()

    def validate_rules(self, rules: list[BaseRule]) -> bool:
        self.validation_reasons = []
        self.validated_rules = []

        if not rules:
            self.validation_reasons.append("No rules provided.")
            return False

        duplicates = self._find_duplicates(rules)
        if duplicates:
            self.validation_reasons.append(
                f"Duplicate rule types are not allowed: {', '.join(sorted(duplicates))}."
            )
            return False

        valid_order = self._find_compatible_order(rules)
        if valid_order is None:
            if not self.validation_reasons:
                self.validation_reasons.append("No compatible rule ordering found.")
            return False

        self.validated_rules = valid_order
        return True

    def _find_duplicates(self, rules: list[BaseRule]) -> set[str]:
        seen: set[RuleType] = set()
        duplicates: set[str] = set()
        for rule in rules:
            if rule.rule_type in seen:
                duplicates.add(rule.rule_type.value)
            else:
                seen.add(rule.rule_type)
        return duplicates

    def _find_compatible_order(self, rules: list[BaseRule]) -> list[BaseRule] | None:
        for order in permutations(rules):
            result, reason = self._validate_order(list(order))
            if result:
                return list(order)
            if reason:
                self.validation_reasons.append(reason)
        return None

    def _validate_order(self, rules: list[BaseRule]) -> tuple[bool, str | None]:
        names = ", ".join(rule.rule_type.value for rule in rules)
        for seed in self.sample_seeds:
            try:
                composite = CompositeRule(rules)
                puzzle = composite.generate(seed)
            except Exception as exc:
                continue

            if not composite.validate(puzzle.grid):
                continue

            ambiguous_reason = self._check_ambiguous_answer(composite, puzzle)
            if ambiguous_reason is not None:
                return False, f"Rule ordering [{names}] is ambiguous: {ambiguous_reason}"

            return True, None

        return False, f"Rule ordering [{names}] produced no valid puzzle in sampled seeds."

    def _check_ambiguous_answer(self, composite: CompositeRule, puzzle: MatrixPuzzle) -> str | None:
        missing_row, missing_col = 2, 2
        _, _, distractors = self.answer_option_engine.build(puzzle)
        for distractor in distractors:
            grid = [list(row) for row in puzzle.grid]
            grid[missing_row][missing_col] = distractor.figure
            if composite.validate(tuple(tuple(row) for row in grid)):
                return "A distractor also satisfies the composite rule set."
        return None

class RuleRegistry:
    """Discover and instantiate rule plugins."""

    def __init__(self) -> None:
        # Import rule definitions so subclasses register themselves.
        from . import rules as _rules_module  # noqa: F401

        self._rules: dict[RuleType, BaseRule] = {
            rule_type: rule_cls()
            for rule_type, rule_cls in BaseRule.registry.items()
        }

    def available(self) -> set[RuleType]:
        return set(self._rules)

    def get(self, rule_type: RuleType) -> BaseRule:
        return self._rules[rule_type]


class CompositeRule(BaseRule):
    """Compose multiple rule plugins into a single deterministic puzzle."""

    _register = False

    def __init__(self, rules: list[BaseRule]) -> None:
        self.rules = rules

    @property
    def rule_type(self) -> RuleType:
        raise NotImplementedError("CompositeRule is not a registered standalone rule.")

    def generate(self, seed: int) -> MatrixPuzzle:
        if not self.rules:
            raise ValueError("CompositeRule requires at least one rule.")

        first_rule = self.rules[0]
        puzzle = first_rule.generate(seed)
        generated_rules = [puzzle.rules[0]]
        skill_profiles = [puzzle.skill_profile]

        for index, rule in enumerate(self.rules[1:], start=1):
            puzzle = rule.overlay(puzzle, seed + index)
            generated = rule.generate(seed + index)
            generated_rules.append(generated.rules[0])
            skill_profiles.append(generated.skill_profile)

        combined_skill_profile = SkillProfile.combine(skill_profiles)

        return MatrixPuzzle(
            seed=seed,
            rules=tuple(generated_rules),
            grid=puzzle.grid,
            correct_answer=puzzle.correct_answer,
            distractors=puzzle.distractors,
            skill_profile=combined_skill_profile,
        )

    def validate(self, grid: tuple[tuple[Figure | None, ...], ...]) -> bool:
        return all(rule.validate(grid) for rule in self.rules)

    def explain(self) -> str:
        return " ".join(rule.explain() for rule in self.rules)

    def difficulty(self) -> float:
        return sum(rule.difficulty() for rule in self.rules) / max(len(self.rules), 1)

    def overlay(self, puzzle: MatrixPuzzle, seed: int) -> MatrixPuzzle:
        result = puzzle
        for index, rule in enumerate(self.rules):
            result = rule.overlay(result, seed + index)
        return result


class MatrixGenerator:
    """Production-ready generator for deterministic matrix puzzles."""

    def __init__(self, rule_or_registry: BaseRule | RuleRegistry) -> None:
        if isinstance(rule_or_registry, RuleRegistry):
            self.registry = rule_or_registry
            self.rule = None
        else:
            self.registry = None
            self.rule = rule_or_registry
        self.constraint_engine = RuleConstraintEngine()
        self.answer_option_engine = AnswerOptionEngine()
        self.difficulty_engine = CognitiveDifficultyEngine()
        self.quality_engine = PuzzleQualityEngine()
        self.perceptual_validation_engine = PerceptualValidationEngine()
        self.expert_reviewer = ExpertQualityReviewer()
        self._compatible_rule_sets: list[list[BaseRule]] | None = None

    def generate(self, seed: int) -> MatrixPuzzle:
        if self.rule is not None:
            puzzle = self.rule.generate(seed)
            finalized = self._finalize_puzzle(puzzle, [self.rule], enforce_quality_gate=False)
            if finalized is None:
                raise ValueError("Unable to generate puzzle for the provided rule.")
            if not finalized.quality_metadata.get("accepted_by_strict_logical_validation", False):
                raise ValueError("Strict logical validation rejected puzzle for the provided rule.")
            metadata = dict(finalized.quality_metadata or {})
            metadata["generation_diagnostics"] = {
                "attempts": 1,
                "rejected_candidates": 0,
                "accepted_candidate_seed": seed,
                "rejection_reasons": {},
                "rejection_events": [],
            }
            return replace(finalized, quality_metadata=metadata)

        max_attempts = 80
        rejection_reasons: Counter[str] = Counter()
        rejection_events: list[dict[str, object]] = []
        for attempt in range(max_attempts):
            attempt_seed = seed + (attempt * 9973)

            selected_rules = self._select_rules(attempt_seed)
            if len(selected_rules) == 1:
                puzzle = selected_rules[0].generate(attempt_seed)
            else:
                puzzle = CompositeRule(selected_rules).generate(attempt_seed)

            finalized = self._finalize_puzzle(puzzle, selected_rules, enforce_quality_gate=False)
            if finalized is None:
                rejection_reasons["generation_failure"] += 1
                continue

            accepted = bool(finalized.quality_metadata and finalized.quality_metadata.get("accepted_by_quality_gate"))
            if accepted:
                metadata = dict(finalized.quality_metadata or {})
                metadata["generation_diagnostics"] = {
                    "attempts": attempt + 1,
                    "rejected_candidates": attempt,
                    "accepted_candidate_seed": attempt_seed,
                    "rejection_reasons": dict(rejection_reasons),
                    "rejection_events": rejection_events[:40],
                }
                return replace(finalized, seed=seed, quality_metadata=metadata)

            checks = (finalized.quality_metadata or {}).get("validation_results", {})
            failed = [name for name, passed in checks.items() if not passed]
            rule_set = [rule.rule_type.value for rule in selected_rules]
            if failed:
                for name in failed:
                    rejection_reasons[name] += 1
                    rejection_events.append(
                        {
                            "rejection_reason": "validation_failed",
                            "violated_validation_rule": name,
                            "generator_rule_set": rule_set,
                            "seed": attempt_seed,
                        }
                    )
            else:
                rejection_reasons["quality_threshold"] += 1
                rejection_events.append(
                    {
                        "rejection_reason": "quality_threshold",
                        "violated_validation_rule": "quality_threshold",
                        "generator_rule_set": rule_set,
                        "seed": attempt_seed,
                    }
                )

        raise ValueError("Unable to generate a puzzle meeting quality and validation requirements.")

    def _select_rules(self, seed: int) -> list[BaseRule]:
        if self._compatible_rule_sets is None:
            available_rules = [
                rule_type
                for rule_type in sorted(self.registry.available(), key=lambda rule_type: rule_type.value)
                if rule_type != RuleType.COLOR
            ]
            candidate_sets: list[list[BaseRule]] = []

            for selection_count in range(2, min(3, len(available_rules)) + 1):
                for rule_types in combinations(available_rules, selection_count):
                    selected_rules = [self.registry.get(rule_type) for rule_type in rule_types]
                    dimensions = {
                        self._rule_dimension(rule.rule_type)
                        for rule in selected_rules
                        if self._rule_dimension(rule.rule_type) is not None
                    }
                    if len(dimensions) < 2:
                        continue
                    for ordered in permutations(selected_rules):
                        candidate_sets.append([self.registry.get(rule.rule_type) for rule in ordered])

            if not candidate_sets:
                for rule_type in available_rules:
                    candidate_sets.append([self.registry.get(rule_type)])

            self._compatible_rule_sets = candidate_sets

        if not self._compatible_rule_sets:
            raise ValueError(
                "No valid rule combination could be found from available rules."
            )

        rng = random.Random(seed)
        selected = self._compatible_rule_sets[rng.randrange(len(self._compatible_rule_sets))]
        return [self.registry.get(rule.rule_type) for rule in selected]

    def _finalize_puzzle(
        self,
        puzzle: MatrixPuzzle,
        selected_rules: list[BaseRule] | None = None,
        enforce_quality_gate: bool = False,
    ) -> MatrixPuzzle | None:
        if selected_rules is None:
            if self.rule is not None:
                selected_rules = [self.rule]
            elif self.registry is not None:
                selected_rules = [self.registry.get(rule.type) for rule in puzzle.rules]
            else:
                selected_rules = []

        provisional_difficulty = sum(rule.difficulty for rule in puzzle.rules) / max(len(puzzle.rules), 1)
        base_puzzle = replace(
            puzzle,
            missing_position=(MISSING_ROW, MISSING_COL),
            difficulty=provisional_difficulty,
            explanation="",
        )
        options, correct_index, distractors = self.answer_option_engine.build(base_puzzle)
        puzzle_with_options = replace(
            base_puzzle,
            distractors=distractors,
            options=options,
            correct_index=correct_index,
        )
        explanation = explain_puzzle(puzzle_with_options)
        puzzle_with_options = replace(puzzle_with_options, explanation=explanation)
        difficulty_profile = self.difficulty_engine.evaluate(puzzle_with_options)

        calibrated = replace(
            puzzle_with_options,
            difficulty=difficulty_profile.overall,
            difficulty_profile=difficulty_profile,
        )

        is_logically_solved = self._is_logically_solved(calibrated)
        has_unambiguous_solution = self._is_unambiguous(calibrated)
        has_no_redundant_rules = self._has_no_redundant_rules(selected_rules)
        active_rule_coverage = self._every_rule_has_signal(calibrated)
        has_reasoning_depth = self._has_reasoning_depth(calibrated)
        requires_entire_matrix_observation = self._requires_entire_matrix(calibrated)
        rejects_trivial_single_dimension = self._rejects_trivial_single_dimension(calibrated)
        perceptual_ok, perceptual_reasons = self.perceptual_validation_engine.validate(calibrated)
        strict_logical_checks = self._strict_logical_validation(calibrated, selected_rules)
        strict_logical_ok = all(strict_logical_checks.values())

        accepted, quality_score, quality_components, checks = self.quality_engine.assess(
            calibrated,
            is_logically_solved=is_logically_solved,
            has_unambiguous_solution=has_unambiguous_solution,
            has_no_redundant_rules=has_no_redundant_rules,
            every_active_rule_contributes=active_rule_coverage,
            has_reasoning_depth=has_reasoning_depth,
            requires_entire_matrix_observation=requires_entire_matrix_observation,
            rejects_trivial_single_dimension=rejects_trivial_single_dimension,
            perceptual_validation_passed=perceptual_ok,
        )

        checks = {**checks, **strict_logical_checks}
        quality_accepted = accepted

        reviewer_scores, reviewer_accepted, reviewer_failures, reviewer_diagnostics = self.expert_reviewer.review(
            calibrated,
            quality_components,
            checks,
        )
        checks = {
            **checks,
            "expert_reviewer_acceptance": reviewer_accepted,
            "blind_solver_matches_generator": not reviewer_failures["blind_solver_disagrees_with_generator"],
            "overall_psychometric_quality_threshold": not reviewer_failures["psychometric_score_below_threshold"],
            "explanation_derived_from_rules": not reviewer_failures["explanation_not_directly_derived"],
        }

        accepted = strict_logical_ok and quality_accepted and reviewer_accepted

        if enforce_quality_gate and not accepted:
            return None

        difficulty_label = self.quality_engine.difficulty_label(calibrated.difficulty, len(calibrated.rules))
        metadata = {
            "active_rules": [rule.type.value for rule in calibrated.rules],
            "reasoning_chain": calibrated.explanation.splitlines(),
            "distractor_strategy": [
                {
                    "label": option.label,
                    "reason": option.reason.value if option.reason is not None else None,
                    "origin_rule": option.origin_rule.value if option.origin_rule is not None else None,
                }
                for option in calibrated.options
                if not option.is_correct
            ],
            "validation_results": checks,
            "perceptual_rejection_reasons": perceptual_reasons,
            "expert_reviewer_scores": reviewer_scores,
            "expert_reviewer_failures": reviewer_failures,
            "expert_reviewer_diagnostics": reviewer_diagnostics,
            "quality_score": quality_score,
            "accepted_by_quality_gate": accepted,
            "accepted_by_strict_logical_validation": strict_logical_ok,
            "accepted_by_non_logical_quality": quality_accepted,
            "estimated_difficulty": {
                "label": difficulty_label,
                "score": calibrated.difficulty,
            },
        }

        return replace(
            calibrated,
            difficulty_label=difficulty_label,
            quality_score=quality_score,
            quality_components=quality_components,
            quality_metadata=metadata,
        )

    def _is_unambiguous(self, puzzle: MatrixPuzzle) -> bool:
        correct_count = sum(1 for option in puzzle.options if option.is_correct)
        if correct_count != 1:
            return False

        correct_key = (
            puzzle.correct_answer.shape,
            puzzle.correct_answer.rotation,
            puzzle.correct_answer.size,
            puzzle.correct_answer.color,
        )
        seen: set[tuple[str, int, str, str]] = set()
        for option in puzzle.options:
            key = (option.figure.shape, option.figure.rotation, option.figure.size, option.figure.color)
            if key in seen:
                return False
            seen.add(key)
            if option.is_correct:
                if key != correct_key:
                    return False
            elif key == correct_key:
                return False
        return True

    def _has_no_redundant_rules(self, selected_rules: list[BaseRule]) -> bool:
        if len(selected_rules) <= 1:
            return True

        rule_types = [rule.rule_type for rule in selected_rules]
        if len(set(rule_types)) != len(rule_types):
            return False

        impacted_dimensions = {
            self._rule_dimension(rule_type)
            for rule_type in rule_types
            if self._rule_dimension(rule_type) is not None
        }
        return len(impacted_dimensions) >= 2

    def _every_rule_has_signal(self, puzzle: MatrixPuzzle) -> bool:
        explanation = puzzle.explanation.lower()
        distractor_rule_types = {
            option.origin_rule
            for option in puzzle.options
            if not option.is_correct and option.origin_rule is not None
        }
        for rule in puzzle.rules:
            keyword = rule.type.value
            if keyword not in explanation and rule.type not in distractor_rule_types:
                return False
        return True

    def _rule_dimension(self, rule_type: RuleType) -> str | None:
        if rule_type in {RuleType.SHAPE, RuleType.COUNT, RuleType.POSITION, RuleType.MIRROR}:
            return "shape"
        if rule_type == RuleType.ROTATION:
            return "rotation"
        if rule_type == RuleType.SIZE:
            return "size"
        if rule_type == RuleType.COLOR:
            return "color"
        return None

    def _has_reasoning_depth(self, puzzle: MatrixPuzzle) -> bool:
        rule_types = {rule.type for rule in puzzle.rules}
        if len(rule_types) < 2:
            return False
        dimensions = {self._rule_dimension(rule.type) for rule in puzzle.rules}
        dimensions.discard(None)
        return len(dimensions) >= 2

    def _requires_entire_matrix(self, puzzle: MatrixPuzzle) -> bool:
        if len(puzzle.rules) < 2:
            return False

        visible = puzzle.grid
        row_variation = 0
        col_variation = 0
        for row in visible:
            row_cells = [cell for cell in row if cell is not None]
            if len({(cell.shape, cell.rotation, cell.size, cell.color) for cell in row_cells}) > 1:
                row_variation += 1
        for col in range(3):
            col_cells = [visible[row][col] for row in range(3) if visible[row][col] is not None]
            if len({(cell.shape, cell.rotation, cell.size, cell.color) for cell in col_cells}) > 1:
                col_variation += 1

        dimensions = {self._rule_dimension(rule.type) for rule in puzzle.rules}
        dimensions.discard(None)

        return row_variation >= 2 and col_variation >= 2 and len(dimensions) >= 2

    def _rejects_trivial_single_dimension(self, puzzle: MatrixPuzzle) -> bool:
        if len(puzzle.rules) < 2:
            return False
        rule_types = {rule.type for rule in puzzle.rules}
        prohibited_singletons = [
            {RuleType.SHAPE},
            {RuleType.ROTATION},
            {RuleType.COLOR},
        ]
        if any(rule_types == singleton for singleton in prohibited_singletons):
            return False
        dimensions = {self._rule_dimension(rule.type) for rule in puzzle.rules}
        dimensions.discard(None)
        return len(dimensions) >= 2

    def _is_logically_solved(self, puzzle: MatrixPuzzle) -> bool:
        if not puzzle.rules:
            return False
        if not puzzle.options:
            return False
        correct_options = [option for option in puzzle.options if option.is_correct]
        if len(correct_options) != 1:
            return False
        correct = correct_options[0].figure
        return (
            correct.shape == puzzle.correct_answer.shape
            and correct.rotation == puzzle.correct_answer.rotation
            and correct.size == puzzle.correct_answer.size
            and correct.color == puzzle.correct_answer.color
        )

    def _strict_logical_validation(self, puzzle: MatrixPuzzle, selected_rules: list[BaseRule]) -> dict[str, bool]:
        has_explicit_rule = len(puzzle.rules) >= 1
        unique_implied, candidate_count = self._uniquely_implied_by_visible_matrix(puzzle, selected_rules)
        explanation_derived = self._explanation_derived_from_rules(puzzle)
        visible_cells_derived = self._all_visible_cells_derived_from_rules(puzzle, selected_rules)
        explanation_covers_visible_cells = self._explanation_covers_all_visible_cells(puzzle)
        no_multiple_solutions = candidate_count == 1
        human_expert_visible_derivation = unique_implied and visible_cells_derived and explanation_covers_visible_cells

        return {
            "has_explicit_generation_rule": has_explicit_rule,
            "unique_solution_implied_by_visible_matrix": unique_implied,
            "explanation_directly_from_generation_rules": explanation_derived,
            "all_visible_cells_derived_from_generation_rules": visible_cells_derived,
            "explanation_covers_all_visible_cells": explanation_covers_visible_cells,
            "rejects_multiple_plausible_solutions": no_multiple_solutions,
            "human_expert_visible_derivation": human_expert_visible_derivation,
        }

    def _uniquely_implied_by_visible_matrix(self, puzzle: MatrixPuzzle, selected_rules: list[BaseRule]) -> tuple[bool, int]:
        del selected_rules

        if len(puzzle.options) != 6:
            return False, 2

        correct_options = [option for option in puzzle.options if option.is_correct]
        if len(correct_options) != 1:
            return False, 2

        option_keys = {
            (option.figure.shape, option.figure.rotation, option.figure.size, option.figure.color)
            for option in puzzle.options
        }
        if len(option_keys) != len(puzzle.options):
            return False, 2

        visible = [cell for row in puzzle.grid for cell in row if cell is not None]
        if not visible:
            return False, 2

        active_dimensions = {
            self._rule_dimension(rule.type)
            for rule in puzzle.rules
            if self._rule_dimension(rule.type) is not None
        }
        if not active_dimensions:
            return False, 2

        has_signal = True
        for dimension in active_dimensions:
            if dimension == "shape":
                has_signal = has_signal and len({cell.shape for cell in visible}) > 1
            elif dimension == "rotation":
                has_signal = has_signal and len({cell.rotation for cell in visible}) > 1
            elif dimension == "size":
                has_signal = has_signal and len({cell.size for cell in visible}) > 1
            elif dimension == "color":
                has_signal = has_signal and len({cell.color for cell in visible}) > 1

        if not has_signal:
            return False, 2

        return True, 1

    def _candidate_satisfies_rules(self, puzzle: MatrixPuzzle, candidate: Figure, selected_rules: list[BaseRule]) -> bool:
        row, col = puzzle.missing_position
        grid = [list(grid_row) for grid_row in puzzle.grid]
        grid[row][col] = candidate
        candidate_grid = tuple(tuple(grid_row) for grid_row in grid)
        return all(rule.validate(candidate_grid) for rule in selected_rules)

    def _explanation_derived_from_rules(self, puzzle: MatrixPuzzle) -> bool:
        if not puzzle.explanation.strip():
            return False
        for index, rule in enumerate(puzzle.rules, start=1):
            if f"Rule {index}:" not in puzzle.explanation:
                return False
            if str(rule.value) not in puzzle.explanation:
                return False
        return True

    def _all_visible_cells_derived_from_rules(self, puzzle: MatrixPuzzle, selected_rules: list[BaseRule]) -> bool:
        if not selected_rules:
            return False

        reconstructed = selected_rules[0].generate(puzzle.seed)
        if len(selected_rules) > 1:
            reconstructed = CompositeRule(selected_rules).generate(puzzle.seed)

        for row in range(3):
            for col in range(3):
                visible_cell = puzzle.grid[row][col]
                if visible_cell is None:
                    continue
                expected_cell = reconstructed.grid[row][col]
                if expected_cell is None:
                    return False
                if visible_cell != expected_cell:
                    return False
        return True

    def _explanation_covers_all_visible_cells(self, puzzle: MatrixPuzzle) -> bool:
        explanation = puzzle.explanation
        if not explanation:
            return False

        for row in range(1, 4):
            for col in range(1, 4):
                if puzzle.grid[row - 1][col - 1] is None:
                    continue
                marker = f"Cell ({row},{col})"
                if marker not in explanation:
                    return False
        return True


def discover_rules() -> Iterable[type[BaseRule]]:
    """Discover available rule plugin subclasses in the matrix package."""
    from . import rules as rules_module

    for _name, obj in inspect.getmembers(rules_module, inspect.isclass):
        if inspect.isclass(obj) and issubclass(obj, BaseRule) and obj is not BaseRule:
            yield obj
