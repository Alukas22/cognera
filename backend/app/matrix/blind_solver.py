"""Rule-agnostic blind solver for matrix answer selection."""

from __future__ import annotations

from dataclasses import dataclass

from .models import AnswerOption, Figure


@dataclass(frozen=True)
class BlindSolverResult:
    """Decision made by the blind solver."""

    selected_index: int | None
    score_gap: float


class BlindSolver:
    """Select an answer by visual regularity only, without generator rule access."""

    def choose(
        self,
        grid: tuple[tuple[Figure | None, ...], ...],
        options: tuple[AnswerOption, ...],
        missing_position: tuple[int, int],
    ) -> BlindSolverResult:
        candidate_scores: list[tuple[int, float]] = []
        for index, option in enumerate(options):
            completed = self._with_candidate(grid, missing_position, option.figure)
            candidate_scores.append((index, self._regularity_score(completed)))

        candidate_scores.sort(key=lambda item: item[1], reverse=True)
        if not candidate_scores:
            return BlindSolverResult(selected_index=None, score_gap=0.0)

        best_index, best_score = candidate_scores[0]
        second_score = candidate_scores[1][1] if len(candidate_scores) > 1 else best_score
        score_gap = best_score - second_score

        # If top candidates are essentially tied, treat as ambiguous and reject.
        if score_gap < 0.02:
            return BlindSolverResult(selected_index=None, score_gap=score_gap)

        return BlindSolverResult(selected_index=best_index, score_gap=score_gap)

    def _with_candidate(
        self,
        grid: tuple[tuple[Figure | None, ...], ...],
        missing_position: tuple[int, int],
        candidate: Figure,
    ) -> tuple[tuple[Figure, ...], ...]:
        row, col = missing_position
        built: list[tuple[Figure, ...]] = []
        for r in range(3):
            row_cells: list[Figure] = []
            for c in range(3):
                cell = grid[r][c]
                if cell is None:
                    if (r, c) != (row, col):
                        raise ValueError("Grid contains unexpected empty cell.")
                    row_cells.append(candidate)
                else:
                    row_cells.append(cell)
            built.append(tuple(row_cells))
        return tuple(built)

    def _regularity_score(self, grid: tuple[tuple[Figure, ...], ...]) -> float:
        score = 0.0
        score += self._feature_pattern_score(grid, "shape")
        score += self._feature_pattern_score(grid, "rotation")
        score += self._feature_pattern_score(grid, "size")
        score += self._feature_pattern_score(grid, "color")
        score += self._mirror_score(grid)
        score += self._diagonal_consistency_score(grid)
        return score

    def _feature_pattern_score(self, grid: tuple[tuple[Figure, ...], ...], feature: str) -> float:
        line_scores: list[float] = []
        for row in grid:
            values = [getattr(cell, feature) for cell in row]
            line_scores.append(self._sequence_score(values, feature))
        for col in range(3):
            values = [getattr(grid[row][col], feature) for row in range(3)]
            line_scores.append(self._sequence_score(values, feature))
        return sum(line_scores) / len(line_scores)

    def _sequence_score(self, values: list[object], feature: str) -> float:
        unique = len(set(values))
        if unique == 1:
            return 0.8

        if feature == "rotation":
            ints = [int(v) for v in values]
            step_a = (ints[1] - ints[0]) % 360
            step_b = (ints[2] - ints[1]) % 360
            return 0.7 if step_a == step_b else 0.25

        order_map = {
            "size": {"small": 0, "medium": 1, "large": 2},
            "shape": {"triangle": 0, "square": 1, "circle": 2, "diamond": 3},
            "color": {"black": 0, "red": 1, "blue": 2, "white": 3},
        }.get(feature)

        if order_map is None:
            return 0.3

        numeric = [order_map.get(v, -99) for v in values]
        if -99 in numeric:
            return 0.2

        diffs = [numeric[1] - numeric[0], numeric[2] - numeric[1]]
        if diffs[0] == diffs[1]:
            return 0.65
        if abs(diffs[0] - diffs[1]) == 1:
            return 0.45
        return 0.2

    def _mirror_score(self, grid: tuple[tuple[Figure, ...], ...]) -> float:
        vertical_matches = 0
        horizontal_matches = 0
        total = 0
        for row in range(3):
            for col in range(3):
                mirror_v = (row, 2 - col)
                mirror_h = (2 - row, col)
                total += 1
                vertical_matches += int(self._figure_equal(grid[row][col], grid[mirror_v[0]][mirror_v[1]]))
                horizontal_matches += int(self._figure_equal(grid[row][col], grid[mirror_h[0]][mirror_h[1]]))

        best = max(vertical_matches, horizontal_matches)
        return best / max(total, 1)

    def _diagonal_consistency_score(self, grid: tuple[tuple[Figure, ...], ...]) -> float:
        major = [grid[0][0], grid[1][1], grid[2][2]]
        minor = [grid[0][2], grid[1][1], grid[2][0]]
        major_equal = self._figure_equal(major[0], major[1]) and self._figure_equal(major[1], major[2])
        minor_equal = self._figure_equal(minor[0], minor[1]) and self._figure_equal(minor[1], minor[2])
        if major_equal or minor_equal:
            return 0.7
        return 0.3

    def _figure_equal(self, first: Figure, second: Figure) -> bool:
        return (
            first.shape == second.shape
            and first.rotation == second.rotation
            and first.size == second.size
            and first.color == second.color
        )
