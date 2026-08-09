"""Plugin-based rule engine for Cognera matrix puzzles."""

from __future__ import annotations

import inspect
import random
from dataclasses import replace
from itertools import combinations, permutations
from typing import Iterable

from .answer_options import AnswerOptionEngine
from .explainer import explain_puzzle
from .models import Figure, MatrixPuzzle, Rule, SkillProfile
from .rules import BaseRule, MISSING_COL, MISSING_ROW, RuleType


SHAPE_RULE_TYPES = {
    RuleType.SHAPE,
    RuleType.COUNT,
    RuleType.POSITION,
    RuleType.MIRROR,
}


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


class DifficultyEngine:
    """Deterministic difficulty scoring for generated puzzles."""

    MAX_INTERACTION_BONUS = 0.25
    BASE_PAIR_BONUS = 0.04

    @classmethod
    def score(cls, puzzle: MatrixPuzzle) -> float:
        if not puzzle.rules:
            return 0.0

        base_score = sum(rule.difficulty for rule in puzzle.rules) / len(puzzle.rules)
        interaction_score = cls._interaction_bonus(puzzle.rules)
        return min(1.0, max(0.0, base_score + interaction_score))

    @classmethod
    def _interaction_bonus(cls, rules: tuple[Rule, ...]) -> float:
        if len(rules) < 2:
            return 0.0

        bonus = 0.0
        for first, second in combinations(rules, 2):
            bonus += cls._pair_bonus(first, second)
        return min(cls.MAX_INTERACTION_BONUS, bonus)

    @classmethod
    def _pair_bonus(cls, first: Rule, second: Rule) -> float:
        bonus = cls.BASE_PAIR_BONUS
        if first.type == RuleType.ROTATION or second.type == RuleType.ROTATION:
            bonus += 0.01
        if first.type in SHAPE_RULE_TYPES and second.type in SHAPE_RULE_TYPES:
            bonus += 0.01
        if {first.type, second.type} == {RuleType.POSITION, RuleType.COUNT}:
            bonus += 0.02
        if {first.type, second.type} == {RuleType.POSITION, RuleType.MIRROR}:
            bonus += 0.02
        return bonus


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

    def generate(self, seed: int) -> MatrixPuzzle:
        if self.rule is not None:
            puzzle = self.rule.generate(seed)
            return self._finalize_puzzle(puzzle)

        selected_rules = self._select_rules(seed)
        if len(selected_rules) == 1:
            puzzle = selected_rules[0].generate(seed)
        else:
            puzzle = CompositeRule(selected_rules).generate(seed)

        return self._finalize_puzzle(puzzle)

    def _select_rules(self, seed: int) -> list[BaseRule]:
        available_rules = sorted(self.registry.available(), key=lambda rule_type: rule_type.value)
        compatible_rules: list[list[BaseRule]] = []

        for selection_count in range(1, min(3, len(available_rules)) + 1):
            for rule_types in combinations(available_rules, selection_count):
                selected_rules = [self.registry.get(rule_type) for rule_type in rule_types]
                if self.constraint_engine.validate_rules(selected_rules):
                    compatible_rules.append(list(self.constraint_engine.validated_rules))

        if not compatible_rules:
            raise ValueError(
                "No valid rule combination could be found from available rules."
            )

        rng = random.Random(seed)
        return compatible_rules[rng.randrange(len(compatible_rules))]

    def _finalize_puzzle(self, puzzle: MatrixPuzzle) -> MatrixPuzzle:
        difficulty = DifficultyEngine.score(puzzle)
        explanation = explain_puzzle(puzzle)
        base_puzzle = replace(
            puzzle,
            missing_position=(MISSING_ROW, MISSING_COL),
            difficulty=difficulty,
            explanation=explanation,
        )
        options, correct_index, distractors = self.answer_option_engine.build(base_puzzle)

        return replace(
            base_puzzle,
            distractors=distractors,
            options=options,
            correct_index=correct_index,
        )


def discover_rules() -> Iterable[type[BaseRule]]:
    """Discover available rule plugin subclasses in the matrix package."""
    from . import rules as rules_module

    for _name, obj in inspect.getmembers(rules_module, inspect.isclass):
        if inspect.isclass(obj) and issubclass(obj, BaseRule) and obj is not BaseRule:
            yield obj
