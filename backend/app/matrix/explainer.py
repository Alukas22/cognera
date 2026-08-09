"""Explanation utilities for Cognera matrix puzzles."""

from __future__ import annotations

from .models import MatrixPuzzle, RuleType


RULE_LABELS = {
    RuleType.ROTATION: "rotation",
    RuleType.SHAPE: "shape progression",
    RuleType.COLOR: "color progression",
    RuleType.SIZE: "size progression",
    RuleType.COUNT: "count pattern",
    RuleType.POSITION: "row/column transformation",
    RuleType.MIRROR: "mirror symmetry",
}


def _rule_explanation(index: int, rule_type: RuleType, value: str) -> str:
    label = RULE_LABELS.get(rule_type, rule_type.value)
    return f"Rule {index}: {label.capitalize()} rule -> {value}."


def _option_explanations(puzzle: MatrixPuzzle) -> list[str]:
    lines: list[str] = []
    for option in puzzle.options:
        if option.is_correct:
            continue
        reason = option.explanation or "it violates at least one active rule."
        lines.append(f"Option {option.label} is incorrect because {reason}")
    return lines


def explain_puzzle(puzzle: MatrixPuzzle) -> str:
    """Produce a plain-English explanation for the generated puzzle."""

    if not puzzle.rules:
        return "No rules are available for this puzzle."

    rule_lines = [_rule_explanation(index, rule.type, str(rule.value)) for index, rule in enumerate(puzzle.rules, start=1)]
    figure_summary = (
        "Correct answer: "
        f"The missing figure is a {puzzle.correct_answer.size} "
        f"{puzzle.correct_answer.color} {puzzle.correct_answer.shape} "
        f"rotated to {puzzle.correct_answer.rotation} degrees."
    )

    lines = [*rule_lines, figure_summary]
    lines.append("Row reasoning:")
    for row_index, row in enumerate(puzzle.grid, start=1):
        described = [
            "missing target cell"
            if cell is None
            else f"{cell.size} {cell.color} {cell.shape} at {cell.rotation}°"
            for cell in row
        ]
        lines.append(f"Row {row_index}: {' | '.join(described)}")

    lines.append("Column reasoning:")
    for col_index in range(3):
        described = []
        for row_index in range(3):
            cell = puzzle.grid[row_index][col_index]
            described.append(
                "missing target cell"
                if cell is None
                else f"{cell.size} {cell.color} {cell.shape} at {cell.rotation}°"
            )
        lines.append(f"Column {col_index + 1}: {' | '.join(described)}")

    lines.append("Visible cell derivation:")
    for row_index, row in enumerate(puzzle.grid, start=1):
        for col_index, cell in enumerate(row, start=1):
            if cell is None:
                continue
            lines.append(
                f"Cell ({row_index},{col_index}) is a {cell.size} {cell.color} {cell.shape} "
                f"at {cell.rotation} degrees under the active rules."
            )

    option_lines = _option_explanations(puzzle)
    if option_lines:
        lines.append("Incorrect options:")
        lines.extend(option_lines)

    return "\n".join(lines)
