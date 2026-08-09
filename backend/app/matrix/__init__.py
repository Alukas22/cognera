"""Cognera matrix engine package.

This package contains core datatypes and utilities for generating Raven-style
matrices, applying rule definitions, and explaining generated puzzles.
"""

from .models import MatrixPuzzle, Rule, RuleType
from .generator import generate_matrix_puzzle
from .explainer import explain_puzzle

__all__ = [
    "RuleType",
    "Rule",
    "MatrixPuzzle",
    "generate_matrix_puzzle",
    "explain_puzzle",
]
