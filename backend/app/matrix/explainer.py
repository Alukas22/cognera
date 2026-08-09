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


def _rule_explanation(rule_type: RuleType, value: str) -> str:
    label = RULE_LABELS.get(rule_type, rule_type.value)
    return f"{label.capitalize()} rule: {value}."


def explain_puzzle(puzzle: MatrixPuzzle) -> str:
    """Produce a plain-English explanation for the generated puzzle."""

    if not puzzle.rules:
        return "No rules are available for this puzzle."

    rule_lines = [_rule_explanation(rule.type, str(rule.value)) for rule in puzzle.rules]
    figure_summary = (
        f"Therefore, the missing figure is a {puzzle.correct_answer.size} "
        f"{puzzle.correct_answer.color} {puzzle.correct_answer.shape} "
        f"rotated to {puzzle.correct_answer.rotation} degrees."
    )

    if len(rule_lines) == 1:
        return f"{rule_lines[0]} {figure_summary}"

    return f"Applied rules: {' '.join(rule_lines)} {figure_summary}"
