"""Matrix engine models for rules and puzzles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RuleType(str, Enum):
    """Supported rule categories for Cognera matrix puzzles."""

    ROTATION = "rotation"
    COUNT = "count"
    SHAPE = "shape"
    SIZE = "size"
    POSITION = "position"
    COLOR = "color"


@dataclass(frozen=True)
class Rule:
    """A reasoning rule used to generate or explain a matrix puzzle."""

    type: RuleType
    value: Any
    difficulty: float


@dataclass(frozen=True)
class Figure:
    """A structured figure representation for Raven-style matrix generation."""

    shape: str
    rotation: int
    size: str
    color: str


@dataclass(frozen=True)
class MatrixPuzzle:
    """Canonical representation of a generated Raven-style matrix puzzle."""

    seed: int
    rules: tuple[Rule, ...]
    grid: tuple[tuple[Figure | None, ...], ...]
    correct_answer: Figure
    distractors: tuple[Figure, ...]
