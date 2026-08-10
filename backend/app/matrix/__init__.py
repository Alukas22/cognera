"""Cognera matrix engine package.

This package contains core datatypes and utilities for generating Raven-style
matrices, applying rule definitions, and explaining generated puzzles.
"""

from .models import (
    CognitiveSkill,
    ContractViolationError,
    Figure,
    MatrixPuzzle,
    Rule,
    RuleType,
    SkillProfile,
)
from .difficulty_engine import CognitiveDifficultyEngine, DifficultyEngine
from .human_reasoning_validator import HumanReasoningValidator
from .perceptual_validation import PerceptualValidationEngine
from .rule_engine import BaseRule, MatrixGenerator, RuleConstraintEngine, RuleRegistry
from .explainer import explain_puzzle

__all__ = [
    "CognitiveSkill",
    "ContractViolationError",
    "Figure",
    "MatrixPuzzle",
    "Rule",
    "RuleType",
    "SkillProfile",
    "BaseRule",
    "CognitiveDifficultyEngine",
    "DifficultyEngine",
    "HumanReasoningValidator",
    "MatrixGenerator",
    "PerceptualValidationEngine",
    "RuleConstraintEngine",
    "RuleRegistry",
    "explain_puzzle",
]
