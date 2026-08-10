"""Explanation utilities for Cognera matrix puzzles."""

from __future__ import annotations

from .figure_components import describe_component_change, structure_summary
from .models import Figure, MatrixPuzzle


def _describe_figure(figure: Figure) -> str:
    return f"{figure.size} {figure.color} {figure.shape} at {figure.rotation}\N{DEGREE SIGN} ({structure_summary(figure)})"


def _format_cell(cell: Figure | None) -> str:
    if cell is None:
        return "missing target cell"
    return _describe_figure(cell)


def explain_puzzle(puzzle: MatrixPuzzle) -> str:
    """Produce a plain-English explanation for the generated puzzle."""

    if not puzzle.rules:
        return "No rules are available for this puzzle."

    lines: list[str] = []

    for index, rule in enumerate(puzzle.rules, start=1):
        lines.append(
            f"Rule {index}: {rule.type.value.capitalize()} rule -> {rule.value}; this {describe_component_change(rule.type.value)}"
        )

    lines.append(
        "Correct answer: "
        f"The missing figure is {_describe_figure(puzzle.correct_answer)}."
    )

    for row_index, row in enumerate(puzzle.grid, start=1):
        rendered = " | ".join(_format_cell(cell) for cell in row)
        lines.append(f"Row {row_index}: {rendered}")

    for col_index in range(3):
        col_cells = [puzzle.grid[row_index][col_index] for row_index in range(3)]
        rendered = " | ".join(_format_cell(cell) for cell in col_cells)
        lines.append(f"Column {col_index + 1}: {rendered}")

    for option in puzzle.options or ():
        if option.is_correct:
            continue
        reason = option.explanation.strip() or "it violates at least one active rule"
        lines.append(f"Option {option.label} is incorrect because {reason}")

    return "\n".join(lines)
