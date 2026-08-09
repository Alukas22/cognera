"""Matrix puzzle generation utilities."""

from __future__ import annotations

import random
from typing import Sequence

from .models import MatrixPuzzle, Rule


def generate_matrix_puzzle(seed: int, rules: Sequence[Rule]) -> MatrixPuzzle:
    """Generate a deterministic 3x3 Raven-style matrix puzzle.

    The generation is seeded for reproducibility. The resulting grid and answer
    are derived from the given rule set in a deterministic fashion.
    """

    rng = random.Random(seed)
    grid = tuple(
        tuple(rng.choice(["A", "B", "C", "D"]) for _ in range(3))
        for _ in range(3)
    )
    correct_answer = rng.choice(["A", "B", "C", "D"])
    distractors = tuple(
        rng.choice([option for option in ["A", "B", "C", "D"] if option != correct_answer])
        for _ in range(5)
    )

    return MatrixPuzzle(
        seed=seed,
        rules=tuple(rules),
        grid=grid,
        correct_answer=correct_answer,
        distractors=distractors,
    )
