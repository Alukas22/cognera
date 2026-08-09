"""Plugin-based rule engine for Cognera matrix puzzles."""

from __future__ import annotations

import inspect
import random
from dataclasses import replace
from itertools import combinations, permutations
from typing import Iterable

from .answer_options import AnswerOptionEngine
from .difficulty_engine import CognitiveDifficultyEngine
from .explainer import explain_puzzle
from .models import Figure, MatrixPuzzle, Rule, SkillProfile
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
        self._compatible_rule_sets: list[list[BaseRule]] | None = None

    def generate(self, seed: int) -> MatrixPuzzle:
        max_attempts = 40
        for attempt in range(max_attempts):
            attempt_seed = seed + (attempt * 9973)

            if self.rule is not None:
                selected_rules = [self.rule]
                puzzle = self.rule.generate(attempt_seed)
            else:
                selected_rules = self._select_rules(attempt_seed)
                if len(selected_rules) == 1:
                    puzzle = selected_rules[0].generate(attempt_seed)
                else:
                    puzzle = CompositeRule(selected_rules).generate(attempt_seed)

            finalized = self._finalize_puzzle(puzzle, selected_rules, enforce_quality_gate=True)
            if finalized is not None:
                return finalized

        raise ValueError("Unable to generate a puzzle meeting quality and validation requirements.")

    def _select_rules(self, seed: int) -> list[BaseRule]:
        if self._compatible_rule_sets is None:
            available_rules = sorted(self.registry.available(), key=lambda rule_type: rule_type.value)
            compatible_rules: list[list[BaseRule]] = []

            for selection_count in range(1, min(3, len(available_rules)) + 1):
                for rule_types in combinations(available_rules, selection_count):
                    selected_rules = [self.registry.get(rule_type) for rule_type in rule_types]
                    if self.constraint_engine.validate_rules(selected_rules):
                        compatible_rules.append(list(self.constraint_engine.validated_rules))

            self._compatible_rule_sets = compatible_rules

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

        explanation = explain_puzzle(puzzle)
        provisional_difficulty = sum(rule.difficulty for rule in puzzle.rules) / max(len(puzzle.rules), 1)
        base_puzzle = replace(
            puzzle,
            missing_position=(MISSING_ROW, MISSING_COL),
            difficulty=provisional_difficulty,
            explanation=explanation,
        )
        options, correct_index, distractors = self.answer_option_engine.build(base_puzzle)
        puzzle_with_options = replace(
            base_puzzle,
            distractors=distractors,
            options=options,
            correct_index=correct_index,
        )
        difficulty_profile = self.difficulty_engine.evaluate(puzzle_with_options)

        calibrated = replace(
            puzzle_with_options,
            difficulty=difficulty_profile.overall,
            difficulty_profile=difficulty_profile,
        )

        is_logically_solved = all(rule.validate(calibrated.grid) for rule in selected_rules)
        has_unambiguous_solution = self._is_unambiguous(calibrated)
        has_no_redundant_rules = self._has_no_redundant_rules(selected_rules)
        active_rule_coverage = self._every_rule_has_signal(calibrated)

        accepted, quality_score, quality_components, checks = self.quality_engine.assess(
            calibrated,
            is_logically_solved=is_logically_solved,
            has_unambiguous_solution=has_unambiguous_solution,
            has_no_redundant_rules=has_no_redundant_rules,
            every_active_rule_contributes=active_rule_coverage,
        )

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
            "quality_score": quality_score,
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


def discover_rules() -> Iterable[type[BaseRule]]:
    """Discover available rule plugin subclasses in the matrix package."""
    from . import rules as rules_module

    for _name, obj in inspect.getmembers(rules_module, inspect.isclass):
        if inspect.isclass(obj) and issubclass(obj, BaseRule) and obj is not BaseRule:
            yield obj
