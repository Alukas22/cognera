"""Regression tests for permanent known failure patterns."""

from dataclasses import replace

from backend.app.matrix.failure_patterns import detect_known_failure_patterns
from backend.app.matrix.models import AnswerOption, CognitiveSkill, Figure, MatrixPuzzle, Rule, RuleType, SkillProfile


def _skill_profile() -> SkillProfile:
    return SkillProfile(
        skills={
            CognitiveSkill.MENTAL_ROTATION: 0.5,
            CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.5,
            CognitiveSkill.WORKING_MEMORY: 0.5,
            CognitiveSkill.ATTENTION: 0.5,
            CognitiveSkill.PROCESSING_SPEED: 0.5,
            CognitiveSkill.ABSTRACT_REASONING: 0.5,
            CognitiveSkill.EXECUTIVE_FUNCTION: 0.5,
        }
    )


def _base_puzzle() -> MatrixPuzzle:
    correct = Figure("triangle", 0, "medium", "red")
    return MatrixPuzzle(
        seed=99,
        rules=(
            Rule(type=RuleType.ROTATION, value="90° clockwise", difficulty=0.8),
            Rule(type=RuleType.SHAPE, value="shape progression", difficulty=0.7),
        ),
        grid=(
            (Figure("triangle", 0, "small", "red"), Figure("square", 90, "small", "red"), Figure("diamond", 180, "small", "red")),
            (Figure("square", 90, "medium", "black"), Figure("diamond", 180, "medium", "black"), Figure("triangle", 270, "medium", "black")),
            (Figure("diamond", 180, "large", "blue"), Figure("triangle", 270, "large", "blue"), None),
        ),
        correct_answer=correct,
        distractors=(),
        skill_profile=_skill_profile(),
        options=(
            AnswerOption(label="A", figure=correct, is_correct=True, explanation="Correct answer.", origin_rule=RuleType.ROTATION),
            AnswerOption(label="B", figure=Figure("triangle", 90, "medium", "red"), is_correct=False, explanation="wrong rotation", origin_rule=RuleType.ROTATION),
            AnswerOption(label="C", figure=Figure("square", 0, "medium", "red"), is_correct=False, explanation="wrong shape", origin_rule=RuleType.SHAPE),
            AnswerOption(label="D", figure=Figure("triangle", 0, "small", "red"), is_correct=False, explanation="wrong size", origin_rule=RuleType.SIZE),
            AnswerOption(label="E", figure=Figure("triangle", 0, "medium", "blue"), is_correct=False, explanation="wrong color", origin_rule=RuleType.COLOR),
            AnswerOption(label="F", figure=Figure("diamond", 180, "large", "black"), is_correct=False, explanation="wrong combination", origin_rule=RuleType.SHAPE),
        ),
        correct_index=0,
        explanation=(
            "Rule 1: rotation rule -> 90° clockwise.\n"
            "Rule 2: shape progression rule -> shape progression.\n"
            "Correct answer: The missing figure is a medium red triangle rotated to 0 degrees.\n"
            "Row 1: ...\n"
            "Row 2: ...\n"
            "Row 3: ...\n"
            "Column 1: ...\n"
            "Column 2: ...\n"
            "Column 3: ...\n"
            "Option B is incorrect because wrong rotation\n"
            "Option C is incorrect because wrong shape\n"
            "Option D is incorrect because wrong size\n"
            "Option E is incorrect because wrong color\n"
            "Option F is incorrect because wrong combination"
        ),
    )


def _base_checks() -> dict[str, bool]:
    return {
        "all_six_options_are_visually_unique": True,
        "no_duplicate_figures": True,
        "explanation_covers_all_visible_cells": True,
        "explanation_explains_every_row": True,
        "explanation_explains_every_column": True,
        "requires_entire_matrix_observation": True,
        "no_redundant_rules": True,
        "puzzle_is_unambiguous": True,
        "unique_solution_implied_by_visible_matrix": True,
        "human_reasoning_unambiguous": True,
        "every_row_participates_in_reasoning": True,
        "every_column_participates_in_reasoning": True,
        "minimum_reasoning_depth": True,
        "distractors_are_unique_and_meaningful": True,
        "all_visible_cells_derived_from_generation_rules": True,
        "full_matrix_reconstructable_from_rules": True,
    }


def _detected_ids(puzzle: MatrixPuzzle, checks: dict[str, bool], perceptual_reasons: list[str], quality: dict[str, float] | None = None) -> set[str]:
    matches = detect_known_failure_patterns(
        puzzle,
        validation_checks=checks,
        perceptual_reasons=perceptual_reasons,
        quality_components=quality,
    )
    return {match.pattern_id for match in matches}


def test_fp_001_invisible_rotation_detected() -> None:
    ids = _detected_ids(_base_puzzle(), _base_checks(), ["invisible_rotation"])
    assert "FP-001" in ids


def test_fp_002_invisible_mirror_detected() -> None:
    ids = _detected_ids(_base_puzzle(), _base_checks(), ["invisible_mirror"])
    assert "FP-002" in ids


def test_fp_003_duplicate_answer_options_detected() -> None:
    checks = _base_checks()
    checks["all_six_options_are_visually_unique"] = False
    ids = _detected_ids(_base_puzzle(), checks, [])
    assert "FP-003" in ids


def test_fp_004_incomplete_explanation_detected() -> None:
    checks = _base_checks()
    checks["explanation_explains_every_row"] = False
    ids = _detected_ids(_base_puzzle(), checks, [])
    assert "FP-004" in ids


def test_fp_005_solved_without_intended_rule_detected() -> None:
    checks = _base_checks()
    checks["requires_entire_matrix_observation"] = False
    ids = _detected_ids(_base_puzzle(), checks, [])
    assert "FP-005" in ids


def test_fp_006_multiple_plausible_solutions_detected() -> None:
    checks = _base_checks()
    checks["human_reasoning_unambiguous"] = False
    ids = _detected_ids(_base_puzzle(), checks, [])
    assert "FP-006" in ids


def test_fp_007_single_row_or_column_rule_detected() -> None:
    checks = _base_checks()
    checks["every_column_participates_in_reasoning"] = False
    ids = _detected_ids(_base_puzzle(), checks, [])
    assert "FP-007" in ids


def test_fp_008_trivial_puzzle_detected() -> None:
    checks = _base_checks()
    checks["minimum_reasoning_depth"] = False
    ids = _detected_ids(_base_puzzle(), checks, [])
    assert "FP-008" in ids


def test_fp_009_distractors_too_similar_detected() -> None:
    checks = _base_checks()
    checks["distractors_are_unique_and_meaningful"] = False
    ids = _detected_ids(_base_puzzle(), checks, [])
    assert "FP-009" in ids


def test_fp_010_distractors_too_easy_detected() -> None:
    ids = _detected_ids(_base_puzzle(), _base_checks(), [], {"distractor_quality": 0.4})
    assert "FP-010" in ids


def test_fp_011_rule_only_justifies_final_cell_detected() -> None:
    checks = _base_checks()
    checks["all_visible_cells_derived_from_generation_rules"] = False
    ids = _detected_ids(_base_puzzle(), checks, [])
    assert "FP-011" in ids


def test_fp_012_symmetric_shape_rotation_detected() -> None:
    puzzle = _base_puzzle()
    symmetric_grid = tuple(
        tuple(None if cell is None else replace(cell, shape="circle") for cell in row)
        for row in puzzle.grid
    )
    ids = _detected_ids(replace(puzzle, grid=symmetric_grid), _base_checks(), [])
    assert "FP-012" in ids
