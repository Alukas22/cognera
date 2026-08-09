"""Cognera matrix engine package.

This package contains core datatypes and utilities for generating Raven-style
matrices, applying rule definitions, and explaining generated puzzles.
"""

from .models import (
    AnswerOption,
    CognitiveSkill,
    DifficultyProfile,
    Distractor,
    DistractorReason,
    Figure,
    MatrixPuzzle,
    Rule,
    RuleType,
    SkillProfile,
)
from .answer_options import AnswerOptionEngine
from .difficulty_engine import CognitiveDifficultyEngine, DifficultyEngine
from .rule_engine import MatrixGenerator, RuleRegistry, RuleConstraintEngine, BaseRule
from .explainer import explain_puzzle

__all__ = [
    "AnswerOption",
    "AnswerOptionEngine",
    "CognitiveSkill",
    "CognitiveDifficultyEngine",
    "DifficultyProfile",
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
