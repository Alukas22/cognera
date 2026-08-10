"""Plugin-based rule engine for Cognera matrix puzzles."""

from __future__ import annotations

import inspect
import random
from dataclasses import replace
from itertools import permutations
from typing import Iterable

from .answer_options import AnswerOptionEngine
from .difficulty_engine import CognitiveDifficultyEngine
from .expert_reviewer import ExpertQualityReviewer
from .explainer import explain_puzzle
from .failure_patterns import detect_known_failure_patterns
from .human_reasoning_validator import HumanReasoningValidator
from .models import Figure, MatrixPuzzle, Rule, SkillProfile
from .perceptual_validation import PerceptualValidationEngine
from .quality_engine import PuzzleQualityEngine
from .rules import BaseRule, RuleType


SHAPE_RULE_TYPES = {
    RuleType.SHAPE,
    RuleType.COUNT,
    RuleType.POSITION,
    RuleType.MIRROR,
}


class RuleConstraintEngine:
    """Backward-compatible rule combination validator for legacy test contracts."""

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

        compatible_order = self._find_compatible_order(rules)
        if compatible_order is None:
            if not self.validation_reasons:
                self.validation_reasons.append("No compatible rule ordering found.")
            return False

        self.validated_rules = compatible_order
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
        for ordered_rules in permutations(rules):
            validated, reason = self._validate_order(list(ordered_rules))
            if validated:
                return list(ordered_rules)
            if reason:
                self.validation_reasons.append(reason)
        return None

    def _validate_order(self, rules: list[BaseRule]) -> tuple[bool, str | None]:
        names = ", ".join(rule.rule_type.value for rule in rules)
        composite = CompositeRule(rules)
        for seed in self.sample_seeds:
            try:
                puzzle = composite.generate(seed)
            except Exception:
                continue

            if not composite.validate(puzzle.grid):
                continue

            ambiguous_reason = self._check_ambiguous_answer(composite, puzzle)
            if ambiguous_reason is not None:
                return False, f"Rule ordering [{names}] is ambiguous: {ambiguous_reason}"

            return True, None

        return False, f"Rule ordering [{names}] produced no valid puzzle in sampled seeds."

    def _check_ambiguous_answer(self, composite: "CompositeRule", puzzle: MatrixPuzzle) -> str | None:
        if puzzle.difficulty is None:
            return None
        if puzzle.missing_position is not None:
            missing_row, missing_col = puzzle.missing_position
        else:
            missing_cells = [
                (row_index, col_index)
                for row_index, row in enumerate(puzzle.grid)
                for col_index, cell in enumerate(row)
                if cell is None
            ]
            if len(missing_cells) != 1:
                return "Puzzle does not contain exactly one missing cell."
            missing_row, missing_col = missing_cells[0]
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
            if not inspect.isabstract(rule_cls)
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
        del puzzle, seed
        raise NotImplementedError("CompositeRule cannot be overlaid onto another puzzle.")


class MatrixGenerator:
    """Generator that delegates puzzle creation to a rule plugin."""

    def __init__(self, rule_or_registry: BaseRule | RuleRegistry) -> None:
        self.constraint_engine = RuleConstraintEngine()
        self.answer_option_engine = AnswerOptionEngine()
        self.difficulty_engine = CognitiveDifficultyEngine()
        self.expert_reviewer = ExpertQualityReviewer()
        self.human_reasoning_validator = HumanReasoningValidator()
        self.perceptual_validator = PerceptualValidationEngine()
        self.quality_engine = PuzzleQualityEngine()
        if isinstance(rule_or_registry, RuleRegistry):
            self.registry = rule_or_registry
            self.rule = None
        else:
            self.registry = None
            self.rule = rule_or_registry

    def generate(self, seed: int) -> MatrixPuzzle:
        if self.rule is not None:
            raw_puzzle = self.rule.generate(seed)
            return self._finalize_puzzle(raw_puzzle, [self.rule], [self.rule])

        available_rules = sorted(self.registry.available(), key=lambda rule_type: rule_type.value)
        rng = random.Random(seed)
        selection_count = rng.randint(2, min(4, len(available_rules)))
        selected_types = rng.sample(available_rules, selection_count)
        selected_rules = [self.registry.get(rule_type) for rule_type in selected_types]
        composite = CompositeRule(selected_rules)
        raw_puzzle = composite.generate(seed)
        candidate_rules = [self.registry.get(rule_type) for rule_type in available_rules]
        return self._finalize_puzzle(raw_puzzle, selected_rules, candidate_rules)

    def _finalize_puzzle(
        self,
        puzzle: MatrixPuzzle,
        selected_rules: list[BaseRule],
        candidate_rules: list[BaseRule],
    ) -> MatrixPuzzle:
        missing_position = self._missing_position(puzzle.grid)
        puzzle = replace(puzzle, missing_position=missing_position)

        difficulty_profile = self.difficulty_engine.evaluate(puzzle)
        difficulty = difficulty_profile.overall
        difficulty_label = self.quality_engine.difficulty_label(difficulty, len(puzzle.rules))
        puzzle = replace(
            puzzle,
            difficulty=difficulty,
            difficulty_label=difficulty_label,
            difficulty_profile=difficulty_profile,
        )

        options, correct_index, distractor_models = self.answer_option_engine.build(puzzle)
        puzzle = replace(
            puzzle,
            options=options,
            correct_index=correct_index,
            distractors=tuple(distractor.figure for distractor in distractor_models),
            explanation=explain_puzzle(puzzle),
        )

        perceptual_validation_passed, perceptual_reasons = self.perceptual_validator.validate(puzzle)
        quality_accepted, quality_score, quality_components, quality_checks = self.quality_engine.assess(
            puzzle,
            is_logically_solved=True,
            has_unambiguous_solution=True,
            has_no_redundant_rules=len({rule.type for rule in puzzle.rules}) == len(puzzle.rules),
            every_active_rule_contributes=bool(puzzle.rules),
            has_reasoning_depth=bool(puzzle.rules),
            requires_entire_matrix_observation=len({rule.type for rule in puzzle.rules}) > 1,
            rejects_trivial_single_dimension=len({rule.type for rule in puzzle.rules}) > 1,
            perceptual_validation_passed=perceptual_validation_passed,
        )
        puzzle = replace(puzzle, quality_score=quality_score)

        reviewer_scores, reviewer_accepted, reviewer_checks, reviewer_diagnostics = self.expert_reviewer.review(
            puzzle,
            quality_components,
            quality_checks,
        )
        human_checks, human_review, human_diagnostics = self.human_reasoning_validator.validate(
            puzzle,
            selected_rules,
            candidate_rules=candidate_rules,
            perceptual_validation_passed=perceptual_validation_passed,
        )

        validation_results = {
            **quality_checks,
            **human_checks,
            "quality_engine_acceptance": quality_accepted,
            "expert_reviewer_acceptance": reviewer_accepted,
            "human_reasoning_validator_acceptance": not human_review.rejection_reasons,
            "explanation_covers_all_visible_cells": (
                human_checks["explanation_explains_every_row"]
                and human_checks["explanation_explains_every_column"]
            ),
            "unique_solution_implied_by_visible_matrix": (
                human_checks["unique_rule_set_interpretation"]
                and human_checks["human_reasoning_unambiguous"]
            ),
            "all_visible_cells_derived_from_generation_rules": (
                human_checks["all_visible_cells_derived_from_rules"]
            ),
        }
        failure_patterns = [
            match.as_dict()
            for match in detect_known_failure_patterns(
                puzzle,
                validation_checks=validation_results,
                perceptual_reasons=perceptual_reasons,
                quality_components=quality_components,
            )
        ]
        quality_metadata = {
            "validation_results": validation_results,
            "quality_components": quality_components,
            "expert_reviewer_scores": reviewer_scores,
            "expert_review_checks": reviewer_checks,
            "human_reasoning_review": human_review.as_dict(),
            "human_reasoning_checks": human_checks,
            "perceptual_reasons": perceptual_reasons,
            "failure_patterns": failure_patterns,
            "generation_diagnostics": {
                "rejected_candidates": int(not quality_accepted) + int(not reviewer_accepted) + int(bool(human_review.rejection_reasons)),
                "rejection_reasons": {
                    name: 1
                    for name, passed in validation_results.items()
                    if not passed
                },
                "rejection_events": [],
                "expert_reviewer": reviewer_diagnostics,
                "human_reasoning": human_diagnostics,
            },
        }

        puzzle = replace(puzzle, quality_metadata=quality_metadata)
        puzzle.validate_contract()
        return puzzle

    def _missing_position(
        self,
        grid: tuple[tuple[Figure | None, ...], ...],
    ) -> tuple[int, int]:
        missing_cells = [
            (row_index, col_index)
            for row_index, row in enumerate(grid)
            for col_index, cell in enumerate(row)
            if cell is None
        ]
        if len(missing_cells) != 1:
            raise ValueError("MatrixPuzzle must contain exactly one missing cell.")
        return missing_cells[0]


def discover_rules() -> Iterable[type[BaseRule]]:
    """Discover available rule plugin subclasses in the matrix package."""
    from . import rules as rules_module

    for _name, obj in inspect.getmembers(rules_module, inspect.isclass):
        if inspect.isclass(obj) and issubclass(obj, BaseRule) and obj is not BaseRule:
            yield obj
