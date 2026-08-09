"""Intelligent answer option generation for matrix puzzles."""

from __future__ import annotations

import random

from .models import AnswerOption, Distractor, DistractorReason, Figure, MatrixPuzzle, Rule, RuleType
from .rules import COLORS, ROTATIONS, SHAPES, SIZES


OPTION_LABELS = ("A", "B", "C", "D", "E", "F")


class AnswerOptionEngine:
    """Generate deterministic production answer options from a solved puzzle."""

    def build(self, puzzle: MatrixPuzzle) -> tuple[tuple[AnswerOption, ...], int, tuple[Distractor, ...]]:
        for attempt in range(4):
            candidates = self._collect_candidates(puzzle, attempt)
            distractors: list[Distractor] = []
            seen_figures: set[tuple[str, int, str, str]] = set()
            correct_key = self._figure_key(puzzle.correct_answer)

            for distractor in candidates:
                key = self._figure_key(distractor.figure)
                if key == correct_key or key in seen_figures:
                    continue
                seen_figures.add(key)
                distractors.append(distractor)
                if len(distractors) == 5:
                    break

            if len(distractors) < 5:
                continue

            options = [
                AnswerOption(
                    label="",
                    figure=puzzle.correct_answer,
                    is_correct=True,
                    explanation="Correct answer.",
                    difficulty=puzzle.difficulty,
                )
            ]
            options.extend(
                AnswerOption(
                    label="",
                    figure=distractor.figure,
                    is_correct=False,
                    reason=distractor.reason,
                    explanation=distractor.explanation,
                    origin_rule=distractor.origin_rule,
                    difficulty=distractor.difficulty,
                )
                for distractor in distractors
            )

            rng = random.Random(puzzle.seed ^ 0xA05E ^ (attempt * 0x9E37))
            rng.shuffle(options)

            labeled_options: list[AnswerOption] = []
            correct_index = 0
            for index, option in enumerate(options):
                labeled = AnswerOption(
                    label=OPTION_LABELS[index],
                    figure=option.figure,
                    is_correct=option.is_correct,
                    reason=option.reason,
                    explanation=option.explanation,
                    origin_rule=option.origin_rule,
                    difficulty=option.difficulty,
                )
                if labeled.is_correct:
                    correct_index = index
                labeled_options.append(labeled)

            if self._options_are_unique(tuple(labeled_options)):
                return tuple(labeled_options), correct_index, tuple(distractors)

        raise ValueError("Unable to generate six unique answer options.")

    def _collect_candidates(self, puzzle: MatrixPuzzle, attempt: int = 0) -> list[Distractor]:
        candidates: list[Distractor] = []

        for rule in puzzle.rules:
            candidates.extend(self._candidates_for_rule(puzzle, rule))

        candidates.extend(self._generic_fallbacks(puzzle))

        if attempt > 0:
            rng = random.Random(puzzle.seed ^ 0x51A7 ^ attempt)
            rng.shuffle(candidates)

        return candidates

    def _options_are_unique(self, options: tuple[AnswerOption, ...]) -> bool:
        keys = {
            self._figure_key(option.figure)
            for option in options
        }
        return len(keys) == len(options)

    def _candidates_for_rule(self, puzzle: MatrixPuzzle, rule: Rule) -> list[Distractor]:
        difficulty = self._rule_difficulty(puzzle, rule.type)
        if rule.type == RuleType.ROTATION:
            rotations = [value for value in ROTATIONS if value != puzzle.correct_answer.rotation]
            return [
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, rotation=rotation),
                    reason=DistractorReason.WRONG_ROTATION,
                    explanation="This option uses the wrong rotation for the matrix progression.",
                    origin_rule=RuleType.ROTATION,
                    difficulty=difficulty,
                )
                for rotation in rotations
            ]

        if rule.type == RuleType.SIZE:
            sizes = self._ordered_values(SIZES, puzzle.correct_answer.size)
            return [
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, size=size),
                    reason=DistractorReason.PARTIAL_PATTERN,
                    explanation="This option changes the size progression while preserving the other attributes.",
                    origin_rule=RuleType.SIZE,
                    difficulty=difficulty,
                )
                for size in sizes
            ]

        if rule.type in {RuleType.SHAPE, RuleType.COUNT, RuleType.POSITION, RuleType.MIRROR}:
            shapes = self._shape_candidates(puzzle)
            reason = {
                RuleType.SHAPE: DistractorReason.WRONG_SHAPE,
                RuleType.COUNT: DistractorReason.WRONG_COUNT,
                RuleType.POSITION: DistractorReason.WRONG_POSITION,
                RuleType.MIRROR: DistractorReason.PARTIAL_PATTERN,
            }[rule.type]
            explanation = {
                RuleType.SHAPE: "This option uses a visually similar but incorrect shape.",
                RuleType.COUNT: "This option breaks the count progression for the target shape.",
                RuleType.POSITION: "This option preserves the figure style but breaks the positional pattern.",
                RuleType.MIRROR: "This option breaks the mirror symmetry while preserving the other attributes.",
            }[rule.type]
            return [
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, shape=shape),
                    reason=reason,
                    explanation=explanation,
                    origin_rule=rule.type,
                    difficulty=difficulty,
                )
                for shape in shapes
            ]

        if rule.type == RuleType.COLOR:
            colors = self._ordered_values(COLORS, puzzle.correct_answer.color)
            return [
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, color=color),
                    reason=DistractorReason.WRONG_COLOR,
                    explanation="This option changes only the color and leaves the other rule effects intact.",
                    origin_rule=RuleType.COLOR,
                    difficulty=difficulty,
                )
                for color in colors
            ]

        return []

    def _generic_fallbacks(self, puzzle: MatrixPuzzle) -> list[Distractor]:
        fallback_rule = puzzle.rules[0].type if puzzle.rules else RuleType.SHAPE
        difficulty = max(0.1, puzzle.difficulty * 0.9)

        candidates: list[Distractor] = []
        for shape in self._ordered_values(SHAPES, puzzle.correct_answer.shape):
            candidates.append(
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, shape=shape),
                    reason=DistractorReason.PARTIAL_PATTERN,
                    explanation="This option is close to the correct answer but breaks part of the pattern.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )
        for rotation in self._ordered_values(list(ROTATIONS), puzzle.correct_answer.rotation):
            candidates.append(
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, rotation=rotation),
                    reason=DistractorReason.PARTIAL_PATTERN,
                    explanation="This option preserves most of the pattern but rotates the figure incorrectly.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )
        for size in self._ordered_values(SIZES, puzzle.correct_answer.size):
            candidates.append(
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, size=size),
                    reason=DistractorReason.PARTIAL_PATTERN,
                    explanation="This option preserves the shape but changes the size progression.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )
        for color in self._ordered_values(COLORS, puzzle.correct_answer.color):
            candidates.append(
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, color=color),
                    reason=DistractorReason.PARTIAL_PATTERN,
                    explanation="This option changes a superficial attribute while leaving the rest intact.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )
        return candidates

    def _shape_candidates(self, puzzle: MatrixPuzzle) -> list[str]:
        visible_shapes = []
        for row in puzzle.grid:
            for cell in row:
                if cell is not None and cell.shape != puzzle.correct_answer.shape and cell.shape not in visible_shapes:
                    visible_shapes.append(cell.shape)

        remaining = [shape for shape in SHAPES if shape != puzzle.correct_answer.shape and shape not in visible_shapes]
        return visible_shapes + remaining

    def _ordered_values(self, values: list[str] | tuple[int, ...] | tuple[str, ...], correct_value: str | int) -> list[str | int]:
        ordered = [value for value in values if value != correct_value]
        if correct_value in values:
            index = list(values).index(correct_value)
            ordered.sort(key=lambda value: (abs(list(values).index(value) - index), list(values).index(value)))
        return ordered

    def _rule_difficulty(self, puzzle: MatrixPuzzle, rule_type: RuleType) -> float:
        for rule in puzzle.rules:
            if rule.type == rule_type:
                return rule.difficulty
        return puzzle.difficulty

    def _make_distractor(
        self,
        figure: Figure,
        reason: DistractorReason,
        explanation: str,
        origin_rule: RuleType,
        difficulty: float,
    ) -> Distractor:
        return Distractor(
            figure=figure,
            reason=reason,
            explanation=explanation,
            origin_rule=origin_rule,
            difficulty=difficulty,
        )

    def _replace(
        self,
        figure: Figure,
        *,
        shape: str | None = None,
        rotation: int | None = None,
        size: str | None = None,
        color: str | None = None,
    ) -> Figure:
        return Figure(
            shape=figure.shape if shape is None else shape,
            rotation=figure.rotation if rotation is None else rotation,
            size=figure.size if size is None else size,
            color=figure.color if color is None else color,
        )

    def _figure_key(self, figure: Figure) -> tuple[str, int, str, str]:
        return (figure.shape, figure.rotation, figure.size, figure.color)