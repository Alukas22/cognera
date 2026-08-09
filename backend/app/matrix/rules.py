"""Definitions and helpers for Cognera matrix rules."""

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
