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
from .blind_solver import BlindSolver
from .difficulty_engine import CognitiveDifficultyEngine, DifficultyEngine
from .expert_reviewer import ExpertQualityReviewer
from .human_reasoning_validator import HumanReasoningValidator
from .perceptual_validation import PerceptualValidationEngine
from .quality_engine import PuzzleQualityEngine
from .rule_engine import MatrixGenerator, RuleRegistry, RuleConstraintEngine, BaseRule
from .explainer import explain_puzzle

__all__ = [
    "AnswerOption",
    "AnswerOptionEngine",
    "BlindSolver",
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
    "ExpertQualityReviewer",
    "HumanReasoningValidator",
    "RuleRegistry",
    "RuleConstraintEngine",
    "DifficultyEngine",
    "PerceptualValidationEngine",
    "PuzzleQualityEngine",
    "explain_puzzle",
]
