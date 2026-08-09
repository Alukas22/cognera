"""Plugin-based rule engine for Cognera matrix puzzles."""

from __future__ import annotations

import inspect
import random
from typing import Iterable

from .models import Figure, MatrixPuzzle, Rule, SkillProfile
from .rules import BaseRule, RuleType


SHAPE_RULE_TYPES = {
    RuleType.SHAPE,
    RuleType.COUNT,
    RuleType.POSITION,
    RuleType.MIRROR,
}


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
        puzzles = [rule.generate(seed=seed + index + 1) for index, rule in enumerate(self.rules)]
        combined_grid: list[list[Figure | None]] = [list(row) for row in puzzles[0].grid]

        def apply_rule_to_grid(rule: BaseRule, puzzle: MatrixPuzzle) -> None:
            for row in range(3):
                for col in range(3):
                    if combined_grid[row][col] is None:
                        continue
                    if rule.rule_type == RuleType.ROTATION:
                        combined_grid[row][col] = Figure(
                            shape=combined_grid[row][col].shape,
                            rotation=puzzle.grid[row][col].rotation,
                            size=combined_grid[row][col].size,
                            color=combined_grid[row][col].color,
                        )
                    elif rule.rule_type == RuleType.SIZE:
                        combined_grid[row][col] = Figure(
                            shape=combined_grid[row][col].shape,
                            rotation=combined_grid[row][col].rotation,
                            size=puzzle.grid[row][col].size,
                            color=combined_grid[row][col].color,
                        )
                    elif rule.rule_type in {RuleType.SHAPE, RuleType.COUNT, RuleType.POSITION, RuleType.MIRROR}:
                        combined_grid[row][col] = Figure(
                            shape=puzzle.grid[row][col].shape,
                            rotation=combined_grid[row][col].rotation,
                            size=combined_grid[row][col].size,
                            color=combined_grid[row][col].color,
                        )

        for rule, puzzle in zip(self.rules[1:], puzzles[1:]):
            apply_rule_to_grid(rule, puzzle)

        final_correct_answer = puzzles[0].correct_answer
        for rule, puzzle in zip(self.rules[1:], puzzles[1:]):
            if rule.rule_type == RuleType.ROTATION:
                final_correct_answer = Figure(
                    shape=final_correct_answer.shape,
                    rotation=puzzle.correct_answer.rotation,
                    size=final_correct_answer.size,
                    color=final_correct_answer.color,
                )
            elif rule.rule_type == RuleType.SIZE:
                final_correct_answer = Figure(
                    shape=final_correct_answer.shape,
                    rotation=final_correct_answer.rotation,
                    size=puzzle.correct_answer.size,
                    color=final_correct_answer.color,
                )
            elif rule.rule_type in {RuleType.SHAPE, RuleType.COUNT, RuleType.POSITION, RuleType.MIRROR}:
                final_correct_answer = Figure(
                    shape=puzzle.correct_answer.shape,
                    rotation=final_correct_answer.rotation,
                    size=final_correct_answer.size,
                    color=final_correct_answer.color,
                )

        distractor_pool: list[Figure] = []
        for puzzle in puzzles:
            distractor_pool.extend(puzzle.distractors)
        unique_distractors = []
        seen = set()
        for distractor in distractor_pool:
            key = (distractor.shape, distractor.rotation, distractor.size, distractor.color)
            if key not in seen and distractor != final_correct_answer:
                seen.add(key)
                unique_distractors.append(distractor)
        while len(unique_distractors) < 3:
            unique_distractors.append(
                Figure(
                    shape=final_correct_answer.shape,
                    rotation=(final_correct_answer.rotation + 90 * len(unique_distractors)) % 360,
                    size=final_correct_answer.size,
                    color=final_correct_answer.color,
                )
            )

        combined_skill_profile = SkillProfile.combine([p.skill_profile for p in puzzles])
        combined_rules = tuple(p.rules[0] for p in puzzles)

        return MatrixPuzzle(
            seed=seed,
            rules=combined_rules,
            grid=tuple(tuple(cell for cell in row) for row in combined_grid),
            correct_answer=final_correct_answer,
            distractors=tuple(unique_distractors[:3]),
            skill_profile=combined_skill_profile,
        )

    def validate(self, grid: tuple[tuple[Figure | None, ...], ...]) -> bool:
        return all(rule.validate(grid) for rule in self.rules)

    def explain(self) -> str:
        return " ".join(rule.explain() for rule in self.rules)

    def difficulty(self) -> float:
        return sum(rule.difficulty() for rule in self.rules) / max(len(self.rules), 1)


class MatrixGenerator:
    """Generator that delegates puzzle creation to a rule plugin."""

    def __init__(self, rule_or_registry: BaseRule | RuleRegistry) -> None:
        if isinstance(rule_or_registry, RuleRegistry):
            self.registry = rule_or_registry
            self.rule = None
        else:
            self.registry = None
            self.rule = rule_or_registry

    def generate(self, seed: int) -> MatrixPuzzle:
        if self.rule is not None:
            return self.rule.generate(seed)

        available_rules = sorted(self.registry.available(), key=lambda rule_type: rule_type.value)
        rng = random.Random(seed)
        selection_count = rng.randint(2, min(4, len(available_rules)))
        selected_types = rng.sample(available_rules, selection_count)
        selected_rules = [self.registry.get(rule_type) for rule_type in selected_types]
        composite = CompositeRule(selected_rules)
        return composite.generate(seed)


def discover_rules() -> Iterable[type[BaseRule]]:
    """Discover available rule plugin subclasses in the matrix package."""
    from . import rules as rules_module

    for _name, obj in inspect.getmembers(rules_module, inspect.isclass):
        if inspect.isclass(obj) and issubclass(obj, BaseRule) and obj is not BaseRule:
            yield obj
