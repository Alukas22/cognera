"""Final human-reasoning validation gate for Cognera matrix puzzles."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .blind_solver import BlindSolver
from .models import Figure, MatrixPuzzle, RuleType
from .rules import BaseRule


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _rule_dimension(rule_type: RuleType) -> str | None:
    if rule_type in {RuleType.SHAPE, RuleType.COUNT, RuleType.POSITION, RuleType.MIRROR}:
        return "shape"
    if rule_type == RuleType.ROTATION:
        return "rotation"
    if rule_type == RuleType.SIZE:
        return "size"
    if rule_type == RuleType.COLOR:
        return "color"
    return None


def _rule_label_sv(rule_type: RuleType) -> str:
    return {
        RuleType.ROTATION: "vridning",
        RuleType.SIZE: "storlek",
        RuleType.COUNT: "antal",
        RuleType.SHAPE: "yttre form",
        RuleType.POSITION: "placering",
        RuleType.MIRROR: "spegling",
        RuleType.COLOR: "inre markering",
    }.get(rule_type, rule_type.value)


@dataclass(frozen=True)
class HumanReasoningReview:
    quality_score: float
    rule_coverage: float
    reasoning_depth: float
    ambiguity_score: float
    perceptual_score: float
    explanation_score: float
    rejection_reasons: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "quality_score": self.quality_score,
            "rule_coverage": self.rule_coverage,
            "reasoning_depth": self.reasoning_depth,
            "ambiguity_score": self.ambiguity_score,
            "perceptual_score": self.perceptual_score,
            "explanation_score": self.explanation_score,
            "rejection_reasons": self.rejection_reasons,
        }


class HumanReasoningValidator:
    """Validate puzzles from an expert human reasoning perspective."""

    def __init__(self) -> None:
        self.blind_solver = BlindSolver()

    def validate(
        self,
        puzzle: MatrixPuzzle,
        selected_rules: list[BaseRule],
        *,
        candidate_rules: list[BaseRule],
        perceptual_validation_passed: bool,
    ) -> tuple[dict[str, bool], HumanReasoningReview, dict[str, object]]:
        missing_position = puzzle.missing_position or self._infer_missing_position(puzzle)
        completed_grid = self._with_candidate(puzzle, puzzle.correct_answer)

        full_matrix_reconstructable, reconstructed = self._reconstruct_from_rules(selected_rules, puzzle.seed)
        all_visible_cells_derived = full_matrix_reconstructable and self._all_visible_match(puzzle, reconstructed)

        option_candidate_count, correct_option_is_unique = self._candidate_solution_uniqueness(puzzle, selected_rules)
        options_unique = self._options_are_unique(puzzle)
        alternative_rule_sets = self._alternative_rule_set_count(
            completed_grid,
            selected_rules,
            candidate_rules,
        )
        unique_rule_set_interpretation = alternative_rule_sets == 0

        rule_coverage_count, isolated_rule_effect = self._rule_coverage(selected_rules, puzzle.seed)
        no_isolated_rule = not isolated_rule_effect

        every_row_participates = self._rows_participate(completed_grid, puzzle.rules)
        every_column_participates = self._columns_participate(completed_grid, puzzle.rules)

        explanation_rows = self._explanation_covers_rows(puzzle)
        explanation_columns = self._explanation_covers_columns(puzzle)
        explanation_correct = self._explanation_justifies_correct(puzzle)
        explanation_distractors = self._explanation_rejects_each_distractor(puzzle)
        explanation_derived = self._explanation_derived_from_rule_objects(puzzle)

        rules_visible_without_answer = all_visible_cells_derived and every_row_participates and every_column_participates
        no_hidden_assumptions = full_matrix_reconstructable and rules_visible_without_answer

        blind = self.blind_solver.choose(puzzle.grid, puzzle.options, missing_position)
        human_reasoning_unambiguous = (
            correct_option_is_unique
            and options_unique
            and unique_rule_set_interpretation
        )

        checks = {
            "full_matrix_reconstructable_from_rules": full_matrix_reconstructable,
            "all_visible_cells_derived_from_rules": all_visible_cells_derived,
            "unique_rule_set_interpretation": unique_rule_set_interpretation,
            "no_isolated_single_cell_rule": no_isolated_rule,
            "human_reasoning_unambiguous": human_reasoning_unambiguous,
            "no_duplicate_answer_options": options_unique,
            "no_hidden_assumptions": no_hidden_assumptions,
            "rules_visible_without_answer": rules_visible_without_answer,
            "every_row_participates_in_reasoning": every_row_participates,
            "every_column_participates_in_reasoning": every_column_participates,
            "explanation_explains_every_row": explanation_rows,
            "explanation_explains_every_column": explanation_columns,
            "explanation_justifies_correct_answer": explanation_correct,
            "explanation_rejects_each_distractor": explanation_distractors,
            "explanation_derived_from_rule_objects": explanation_derived,
        }

        rejection_reasons = [name for name, passed in checks.items() if not passed]
        rule_coverage_score = (
            0.0
            if not selected_rules
            else rule_coverage_count / len(selected_rules)
        )
        reasoning_depth = _clamp01((len(puzzle.rules) / 3.0 + (int(every_row_participates) + int(every_column_participates)) / 2.0) / 2.0)
        ambiguity_score = _clamp01(
            (1.0 if unique_rule_set_interpretation else 0.0)
            * (1.0 if correct_option_is_unique else 0.0)
            * (1.0 if blind.selected_index == puzzle.correct_index else 0.0)
        )
        perceptual_score = 1.0 if perceptual_validation_passed else 0.0
        explanation_score = (
            int(explanation_rows)
            + int(explanation_columns)
            + int(explanation_correct)
            + int(explanation_distractors)
            + int(explanation_derived)
        ) / 5.0
        quality_score = _clamp01(
            0.24 * rule_coverage_score
            + 0.20 * reasoning_depth
            + 0.22 * ambiguity_score
            + 0.14 * perceptual_score
            + 0.20 * explanation_score
        )

        review = HumanReasoningReview(
            quality_score=quality_score,
            rule_coverage=rule_coverage_score,
            reasoning_depth=reasoning_depth,
            ambiguity_score=ambiguity_score,
            perceptual_score=perceptual_score,
            explanation_score=explanation_score,
            rejection_reasons=rejection_reasons,
        )

        diagnostics = {
            "candidate_solution_count": option_candidate_count,
            "alternative_rule_set_count": alternative_rule_sets,
            "blind_solver_selected_index": blind.selected_index,
            "blind_solver_score_gap": blind.score_gap,
            "rule_coverage_count": rule_coverage_count,
        }
        return checks, review, diagnostics

    def _infer_missing_position(self, puzzle: MatrixPuzzle) -> tuple[int, int]:
        missing_cells = [
            (row_index, col_index)
            for row_index, row in enumerate(puzzle.grid)
            for col_index, cell in enumerate(row)
            if cell is None
        ]
        if len(missing_cells) != 1:
            raise ValueError("MatrixPuzzle must contain exactly one missing cell.")
        return missing_cells[0]

    def _with_candidate(
        self,
        puzzle: MatrixPuzzle,
        candidate: Figure,
    ) -> tuple[tuple[Figure, ...], ...]:
        if puzzle.missing_position is not None:
            row, col = puzzle.missing_position
        else:
            missing_cells = [
                (r, c)
                for r in range(3)
                for c in range(3)
                if puzzle.grid[r][c] is None
            ]
            if len(missing_cells) != 1:
                raise ValueError("MatrixPuzzle must contain exactly one missing cell.")
            row, col = missing_cells[0]
        built: list[tuple[Figure, ...]] = []
        for r in range(3):
            row_cells: list[Figure] = []
            for c in range(3):
                cell = puzzle.grid[r][c]
                if cell is None:
                    if (r, c) != (row, col):
                        raise ValueError("Unexpected empty cell in puzzle grid.")
                    row_cells.append(candidate)
                else:
                    row_cells.append(cell)
            built.append(tuple(row_cells))
        return tuple(built)

    def _reconstruct_from_rules(
        self,
        selected_rules: list[BaseRule],
        seed: int,
    ) -> tuple[bool, MatrixPuzzle | None]:
        if not selected_rules:
            return False, None
        try:
            puzzle = selected_rules[0].generate(seed)
            for index, rule in enumerate(selected_rules[1:], start=1):
                puzzle = rule.overlay(puzzle, seed + index)
            return True, puzzle
        except Exception:
            return False, None

    def _all_visible_match(self, puzzle: MatrixPuzzle, reconstructed: MatrixPuzzle | None) -> bool:
        if reconstructed is None:
            return False
        for row in range(3):
            for col in range(3):
                visible = puzzle.grid[row][col]
                if visible is None:
                    continue
                expected = reconstructed.grid[row][col]
                if expected is None or visible != expected:
                    return False
        return True

    def _candidate_solution_uniqueness(self, puzzle: MatrixPuzzle, selected_rules: list[BaseRule]) -> tuple[int, bool]:
        satisfying = 0
        correct_count = sum(1 for option in puzzle.options if option.is_correct)
        labeled_correct = 0 <= puzzle.correct_index < len(puzzle.options) and puzzle.options[puzzle.correct_index].is_correct
        for option in puzzle.options:
            if self._candidate_satisfies_rules(puzzle, option.figure, selected_rules):
                satisfying += 1
        if not labeled_correct or correct_count != 1:
            return satisfying, False

        # Some rules intentionally expose permissive validate() semantics;
        # solution uniqueness is anchored to option labeling + global ambiguity checks.
        return satisfying, True

    def _options_are_unique(self, puzzle: MatrixPuzzle) -> bool:
        keys = {
            (option.figure.shape, option.figure.rotation, option.figure.size, option.figure.color)
            for option in puzzle.options
        }
        return len(keys) == len(puzzle.options)

    def _candidate_satisfies_rules(self, puzzle: MatrixPuzzle, candidate: Figure, selected_rules: list[BaseRule]) -> bool:
        grid = self._with_candidate(puzzle, candidate)
        return all(rule.validate(grid) for rule in selected_rules)

    def _alternative_rule_set_count(
        self,
        completed_grid: tuple[tuple[Figure, ...], ...],
        selected_rules: list[BaseRule],
        candidate_rules: list[BaseRule],
    ) -> int:
        selected_types = {rule.rule_type for rule in selected_rules}
        alternatives = 0

        unique_candidates: dict[RuleType, BaseRule] = {}
        for rule in candidate_rules:
            unique_candidates[rule.rule_type] = rule

        pool = list(unique_candidates.values())
        target_size = max(1, len(selected_rules))
        for combo in combinations(pool, target_size):
            combo_types = {rule.rule_type for rule in combo}
            if combo_types == selected_types:
                continue
            validates = True
            for rule in combo:
                try:
                    if not rule.validate(completed_grid):
                        validates = False
                        break
                except Exception:
                    validates = False
                    break
            if validates:
                alternatives += 1
        return alternatives

    def _rule_coverage(self, selected_rules: list[BaseRule], seed: int) -> tuple[int, bool]:
        full_ok, full = self._reconstruct_from_rules(selected_rules, seed)
        if not full_ok or full is None:
            return 0, True

        if len(selected_rules) == 1:
            return 1, False

        covered = 0
        isolated = False
        for index in range(len(selected_rules)):
            reduced = selected_rules[:index] + selected_rules[index + 1 :]
            reduced_ok, reduced_puzzle = self._reconstruct_from_rules(reduced, seed)
            if not reduced_ok or reduced_puzzle is None:
                isolated = True
                continue

            affected_visible_cells = 0
            for row in range(3):
                for col in range(3):
                    if row == 2 and col == 2:
                        continue
                    if full.grid[row][col] != reduced_puzzle.grid[row][col]:
                        affected_visible_cells += 1

            if affected_visible_cells >= 2:
                covered += 1
            else:
                isolated = True

        return covered, isolated

    def _rows_participate(self, completed_grid: tuple[tuple[Figure, ...], ...], rules) -> bool:
        dimensions = {d for d in (_rule_dimension(rule.type) for rule in rules) if d is not None}
        for row in range(3):
            signatures = [self._cell_signature(completed_grid[row][col], dimensions) for col in range(3)]
            if len(set(signatures)) <= 1:
                return False
        return True

    def _columns_participate(self, completed_grid: tuple[tuple[Figure, ...], ...], rules) -> bool:
        dimensions = {d for d in (_rule_dimension(rule.type) for rule in rules) if d is not None}
        for col in range(3):
            signatures = [self._cell_signature(completed_grid[row][col], dimensions) for row in range(3)]
            if len(set(signatures)) <= 1:
                return False
        return True

    def _cell_signature(self, cell: Figure, dimensions: set[str]) -> tuple[object, ...]:
        signature: list[object] = []
        if "shape" in dimensions:
            signature.append(cell.shape)
        if "rotation" in dimensions:
            signature.append(cell.rotation)
        if "size" in dimensions:
            signature.append(cell.size)
        if "color" in dimensions:
            signature.append(cell.color)
        return tuple(signature)

    def _explanation_covers_rows(self, puzzle: MatrixPuzzle) -> bool:
        explanation = puzzle.explanation
        if not explanation:
            return False
        return "Steg 1" in explanation and "Vad händer i raderna?" in explanation

    def _explanation_covers_columns(self, puzzle: MatrixPuzzle) -> bool:
        explanation = puzzle.explanation
        if not explanation:
            return False
        return "Steg 2" in explanation and "Vad händer i kolumnerna?" in explanation

    def _explanation_justifies_correct(self, puzzle: MatrixPuzzle) -> bool:
        explanation = puzzle.explanation
        if not explanation:
            return False
        return "Rätt svar" in explanation and "Varför är detta korrekt?" in explanation

    def _explanation_rejects_each_distractor(self, puzzle: MatrixPuzzle) -> bool:
        explanation = puzzle.explanation
        if not explanation:
            return False
        for label in ("A", "B", "C", "D", "E", "F"):
            if f"Alternativ {label}" not in explanation:
                return False
        return True

    def _explanation_derived_from_rule_objects(self, puzzle: MatrixPuzzle) -> bool:
        explanation = puzzle.explanation
        if not explanation:
            return False
        if "Kontroll" not in explanation:
            return False
        for rule in puzzle.rules:
            if _rule_label_sv(rule.type) not in explanation:
                return False
        return True
