"""Explanation utilities for Cognera matrix puzzles."""

from __future__ import annotations

from .models import MatrixPuzzle, RuleType


def explain_puzzle(puzzle: MatrixPuzzle) -> str:
    """Produce a plain-English explanation for the generated puzzle."""

    if not puzzle.rules:
        return "No rules are available for this puzzle."

    rule = puzzle.rules[0]
    if rule.type == RuleType.ROTATION:
        return (
            f"The figure rotates {rule.value} in each step from left to right, "
            "top to bottom. The missing cell continues the same rotation pattern "
            f"to become {puzzle.correct_answer.rotation} degrees."
        )

    return (
        "This puzzle follows the configured rules. "
        "The correct answer matches the pattern of the visible cells."
    )
