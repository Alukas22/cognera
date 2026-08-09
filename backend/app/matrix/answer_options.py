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
            candidates.sort(
                key=lambda candidate: (
                    self._attribute_distance(candidate.figure, puzzle.correct_answer),
                    self._reason_priority(candidate.reason),
                )
            )
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

        candidates.extend(self._strategy_candidates(puzzle))

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
                    explanation="This option preserves shape, size and color but violates the rotation rule.",
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
                    reason=DistractorReason.WRONG_SIZE,
                    explanation="This option preserves other attributes but violates the size progression.",
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
                RuleType.MIRROR: DistractorReason.PARTIAL_REASONING,
            }[rule.type]
            explanation = {
                RuleType.SHAPE: "This option uses a visually similar but incorrect shape.",
                RuleType.COUNT: "This option violates the shape-count progression while keeping other traits fixed.",
                RuleType.POSITION: "This option preserves the figure style but breaks the positional pattern.",
                RuleType.MIRROR: "This option breaks mirror symmetry while preserving color, size and rotation.",
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
                    explanation="This option changes only color and violates the color regularity.",
                    origin_rule=RuleType.COLOR,
                    difficulty=difficulty,
                )
                for color in colors
            ]

        return []

    def _strategy_candidates(self, puzzle: MatrixPuzzle) -> list[Distractor]:
        fallback_rule = puzzle.rules[0].type if puzzle.rules else RuleType.SHAPE
        difficulty = max(0.1, puzzle.difficulty * 0.9)
        visible_cells = [cell for row in puzzle.grid for cell in row if cell is not None]

        candidates: list[Distractor] = []
        if visible_cells:
            donor = min(visible_cells, key=lambda cell: self._attribute_distance(cell, puzzle.correct_answer))
            candidates.append(
                self._make_distractor(
                    figure=donor,
                    reason=DistractorReason.WRONG_PROGRESSION,
                    explanation="This option copies a nearby pattern state but fails to continue the final progression step.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )

        for rule in puzzle.rules:
            omitted = self._candidate_for_omitted_rule(puzzle, rule.type)
            if omitted is not None:
                candidates.append(
                    self._make_distractor(
                        figure=omitted,
                        reason=DistractorReason.OMISSION_OF_RULE,
                        explanation="This option matches some rule constraints but omits one active rule.",
                        origin_rule=rule.type,
                        difficulty=self._rule_difficulty(puzzle, rule.type),
                    )
                )

        similar_rotation = self._pick_alternative(list(ROTATIONS), puzzle.correct_answer.rotation)
        if similar_rotation is not None:
            candidates.append(
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, rotation=similar_rotation),
                    reason=DistractorReason.PERCEPTUAL_SIMILARITY,
                    explanation="This option is visually similar but fails one logical constraint.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )

        similar_size = self._pick_alternative(list(SIZES), puzzle.correct_answer.size)
        if similar_size is not None:
            candidates.append(
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, size=similar_size),
                    reason=DistractorReason.PARTIAL_REASONING,
                    explanation="This option keeps the major pattern but misapplies one reasoning step.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )

        # Keep a broad but deterministic pool so every puzzle can produce six unique options.
        for shape in self._ordered_values(SHAPES, puzzle.correct_answer.shape):
            candidates.append(
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, shape=shape),
                    reason=DistractorReason.PARTIAL_REASONING,
                    explanation="This option uses an incorrect shape while preserving other inferred attributes.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )
        for rotation in self._ordered_values(list(ROTATIONS), puzzle.correct_answer.rotation):
            candidates.append(
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, rotation=rotation),
                    reason=DistractorReason.PERCEPTUAL_SIMILARITY,
                    explanation="This option is visually close but applies the wrong terminal transformation.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )
        for size in self._ordered_values(SIZES, puzzle.correct_answer.size):
            candidates.append(
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, size=size),
                    reason=DistractorReason.PARTIAL_REASONING,
                    explanation="This option keeps the pattern frame but changes one interpreted feature.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )
        for color in self._ordered_values(COLORS, puzzle.correct_answer.color):
            candidates.append(
                self._make_distractor(
                    figure=self._replace(puzzle.correct_answer, color=color),
                    reason=DistractorReason.PERCEPTUAL_SIMILARITY,
                    explanation="This option changes a low-salience visual feature without fitting all rules.",
                    origin_rule=fallback_rule,
                    difficulty=difficulty,
                )
            )

        return candidates

    def _candidate_for_omitted_rule(self, puzzle: MatrixPuzzle, rule_type: RuleType) -> Figure | None:
        if rule_type == RuleType.ROTATION:
            value = self._pick_alternative(list(ROTATIONS), puzzle.correct_answer.rotation)
            return None if value is None else self._replace(puzzle.correct_answer, rotation=value)
        if rule_type == RuleType.SIZE:
            value = self._pick_alternative(list(SIZES), puzzle.correct_answer.size)
            return None if value is None else self._replace(puzzle.correct_answer, size=value)
        if rule_type == RuleType.COLOR:
            value = self._pick_alternative(list(COLORS), puzzle.correct_answer.color)
            return None if value is None else self._replace(puzzle.correct_answer, color=value)
        if rule_type in {RuleType.SHAPE, RuleType.COUNT, RuleType.POSITION, RuleType.MIRROR}:
            value = self._pick_alternative(list(SHAPES), puzzle.correct_answer.shape)
            return None if value is None else self._replace(puzzle.correct_answer, shape=value)
        return None

    def _shape_candidates(self, puzzle: MatrixPuzzle) -> list[str]:
        visible_shapes = []
        for row in puzzle.grid:
            for cell in row:
                if cell is not None and cell.shape != puzzle.correct_answer.shape and cell.shape not in visible_shapes:
                    visible_shapes.append(cell.shape)

        remaining = [shape for shape in SHAPES if shape != puzzle.correct_answer.shape and shape not in visible_shapes]
        return visible_shapes + remaining

    def _reason_priority(self, reason: DistractorReason) -> int:
        order = [
            DistractorReason.WRONG_ROTATION,
            DistractorReason.WRONG_SHAPE,
            DistractorReason.WRONG_COLOR,
            DistractorReason.WRONG_SIZE,
            DistractorReason.WRONG_COUNT,
            DistractorReason.WRONG_POSITION,
            DistractorReason.WRONG_PROGRESSION,
            DistractorReason.OMISSION_OF_RULE,
            DistractorReason.PARTIAL_REASONING,
            DistractorReason.PERCEPTUAL_SIMILARITY,
            DistractorReason.PARTIAL_PATTERN,
            DistractorReason.MIRROR_INSTEAD_OF_ROTATION,
        ]
        try:
            return order.index(reason)
        except ValueError:
            return len(order)

    def _attribute_distance(self, first: Figure, second: Figure) -> int:
        return sum(
            [
                first.shape != second.shape,
                first.rotation != second.rotation,
                first.size != second.size,
                first.color != second.color,
            ]
        )

    def _pick_alternative(self, values: list[str] | list[int], correct: str | int) -> str | int | None:
        ordered = self._ordered_values(values, correct)
        if not ordered:
            return None
        return ordered[0]

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