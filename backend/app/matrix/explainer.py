"""Explanation utilities for Cognera matrix puzzles."""

from __future__ import annotations

from .models import MatrixPuzzle


def explain_puzzle(puzzle: MatrixPuzzle) -> str:
    """Produce a simple explanation for the generated puzzle."""

    rule_descriptions = []
    for rule in puzzle.rules:
        rule_descriptions.append(
            f"{rule.type.value.title()}: {rule.value} (difficulty {rule.difficulty:.1f})"
        )

    return (
        "This puzzle was generated with the following rules:\n"
        f"{chr(10).join(rule_descriptions)}\n"
        "The correct answer follows the rule combination and matches the generated matrix pattern."
    )
