"""Cognera matrix engine package.

This package contains core datatypes and utilities for generating Raven-style
matrices, applying rule definitions, and explaining generated puzzles.
"""

from .models import (
    CognitiveSkill,
    Distractor,
    DistractorReason,
    Figure,
    MatrixPuzzle,
    Rule,
    RuleType,
    SkillProfile,
)
from .rule_engine import DifficultyEngine, MatrixGenerator, RuleRegistry, RuleConstraintEngine, BaseRule
from .explainer import explain_puzzle

__all__ = [
    "CognitiveSkill",
    "Distractor",
    "DistractorReason",
    "Figure",
    "MatrixPuzzle",
    "Rule",
    "RuleType",
    "SkillProfile",
    "BaseRule",
    "MatrixGenerator",
    "RuleRegistry",
    "RuleConstraintEngine",
    "DifficultyEngine",
    "explain_puzzle",
]
