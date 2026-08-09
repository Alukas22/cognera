"""Known failure pattern detection for Cognera puzzle quality gates."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Figure, MatrixPuzzle, RuleType


_ROTATIONALLY_SYMMETRIC_SHAPES = {"circle", "square", "diamond"}


@dataclass(frozen=True)
class FailurePatternMatch:
    pattern_id: str
    name: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.pattern_id,
            "name": self.name,
            "reason": self.reason,
        }


def detect_known_failure_patterns(
    puzzle: MatrixPuzzle,
    *,
    validation_checks: dict[str, bool],
    perceptual_reasons: list[str],
    quality_components: dict[str, float] | None = None,
) -> list[FailurePatternMatch]:
    """Return all known failure patterns detected for a puzzle candidate."""

    failures: list[FailurePatternMatch] = []

    if "invisible_rotation" in perceptual_reasons:
        failures.append(_match("FP-001", "Invisible Rotation", "Rotation is not visually observable."))

    if "invisible_mirror" in perceptual_reasons:
        failures.append(_match("FP-002", "Invisible Mirror Symmetry", "Mirror transformation is not visually observable."))

    if not validation_checks.get("all_six_options_are_visually_unique", True) or not validation_checks.get("no_duplicate_figures", True):
        failures.append(_match("FP-003", "Duplicate Answer Options", "Answer options contain duplicate figures."))

    if not validation_checks.get("explanation_covers_all_visible_cells", True) or not validation_checks.get("explanation_explains_every_row", True) or not validation_checks.get("explanation_explains_every_column", True):
        failures.append(_match("FP-004", "Explanation Does Not Explain Whole Matrix", "Explanation does not reconstruct all visible rows and columns."))

    if not validation_checks.get("requires_entire_matrix_observation", True) or not validation_checks.get("no_redundant_rules", True):
        failures.append(_match("FP-005", "Puzzle Solvable Without Discovering The Intended Rule", "Puzzle can be solved without full intended rule discovery."))

    if not validation_checks.get("puzzle_is_unambiguous", True) or not validation_checks.get("unique_solution_implied_by_visible_matrix", True) or not validation_checks.get("human_reasoning_unambiguous", True):
        failures.append(_match("FP-006", "Multiple Plausible Solutions", "More than one plausible interpretation or answer exists."))

    if not validation_checks.get("every_row_participates_in_reasoning", True) or not validation_checks.get("every_column_participates_in_reasoning", True):
        failures.append(_match("FP-007", "Only One Row Or Column Contains The Rule", "Reasoning signal is not distributed across all rows and columns."))

    if not validation_checks.get("minimum_reasoning_depth", True):
        failures.append(_match("FP-008", "Trivial Puzzle", "Puzzle reasoning depth is below required threshold."))

    if not validation_checks.get("distractors_are_unique_and_meaningful", True) or _distractors_too_similar(puzzle):
        failures.append(_match("FP-009", "Distractors Too Similar", "Distractors are overly similar and weakly distinguishable."))

    distractor_quality = (quality_components or {}).get("distractor_quality", 1.0)
    if distractor_quality < 0.62:
        failures.append(_match("FP-010", "Distractors Too Easy", "Distractors are too weak to provide psychometric challenge."))

    if not validation_checks.get("all_visible_cells_derived_from_generation_rules", True) or not validation_checks.get("full_matrix_reconstructable_from_rules", True):
        failures.append(_match("FP-011", "Rule Only Justifies Final Cell", "Rule set does not reconstruct all visible cells."))

    if _symmetric_rotation_used(puzzle):
        failures.append(_match("FP-012", "Symmetric Shape Uses Rotation", "Rotation rule relies on rotationally symmetric shapes."))

    deduped: dict[str, FailurePatternMatch] = {}
    for failure in failures:
        deduped[failure.pattern_id] = failure
    return [deduped[key] for key in sorted(deduped)]


def _match(pattern_id: str, name: str, reason: str) -> FailurePatternMatch:
    return FailurePatternMatch(pattern_id=pattern_id, name=name, reason=reason)


def _distractors_too_similar(puzzle: MatrixPuzzle) -> bool:
    distractors = [option for option in puzzle.options if not option.is_correct]
    if len(distractors) < 2:
        return True

    distances_to_answer = [_attribute_distance(option.figure, puzzle.correct_answer) for option in distractors]
    average_distance = sum(distances_to_answer) / len(distances_to_answer)
    near_miss_ratio = sum(1 for distance in distances_to_answer if distance <= 1) / len(distances_to_answer)

    pairwise_distances: list[int] = []
    for idx, left in enumerate(distractors):
        for right in distractors[idx + 1 :]:
            pairwise_distances.append(_attribute_distance(left.figure, right.figure))

    pairwise_near_ratio = 0.0
    if pairwise_distances:
        pairwise_near_ratio = sum(1 for distance in pairwise_distances if distance <= 1) / len(pairwise_distances)

    return average_distance < 1.0 or (near_miss_ratio >= 0.95 and pairwise_near_ratio >= 0.75)


def _symmetric_rotation_used(puzzle: MatrixPuzzle) -> bool:
    if not any(rule.type == RuleType.ROTATION for rule in puzzle.rules):
        return False

    visible = [cell for row in puzzle.grid for cell in row if cell is not None]
    if not visible:
        return False
    return {cell.shape for cell in visible}.issubset(_ROTATIONALLY_SYMMETRIC_SHAPES)


def _attribute_distance(first: Figure, second: Figure) -> int:
    return sum(
        [
            first.shape != second.shape,
            first.rotation != second.rotation,
            first.size != second.size,
            first.color != second.color,
        ]
    )
