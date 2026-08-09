"""Cognera matrix engine package.

This package contains core datatypes and utilities for generating Raven-style
matrices, applying rule definitions, and explaining generated puzzles.
"""

from .models import Figure, MatrixPuzzle, Rule, RuleType
from .generator import RotationGenerator
from .explainer import explain_puzzle

__all__ = [
    "Figure",
    "RuleType",
    "Rule",
    "MatrixPuzzle",
    "RotationGenerator",
    "explain_puzzle",
]
