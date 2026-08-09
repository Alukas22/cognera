"""Cognera matrix engine package.

This package contains core datatypes and utilities for generating Raven-style
matrices, applying rule definitions, and explaining generated puzzles.
"""

from .models import CognitiveSkill, Figure, MatrixPuzzle, Rule, RuleType, SkillProfile
from .rule_engine import MatrixGenerator, RuleRegistry, BaseRule
from .explainer import explain_puzzle

__all__ = [
    "CognitiveSkill",
    "Figure",
    "MatrixPuzzle",
    "Rule",
    "RuleType",
    "SkillProfile",
    "BaseRule",
    "MatrixGenerator",
    "RuleRegistry",
    "explain_puzzle",
]
