"""Tests for Sprint 7.2 human reasoning validator and regressions."""

from dataclasses import replace

from backend.app.matrix import HumanReasoningValidator, MatrixGenerator, RuleRegistry, RuleType
from backend.app.matrix.models import (
    AnswerOption,
    CognitiveSkill,
    Figure,
    MatrixPuzzle,
    Rule,
    SkillProfile,
)
from backend.app.matrix.perceptual_validation import PerceptualValidationEngine
from backend.app.matrix.rules import BaseRule


def _skill_profile() -> SkillProfile:
    return SkillProfile(
        skills={
            CognitiveSkill.MENTAL_ROTATION: 0.4,
            CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.4,
            CognitiveSkill.WORKING_MEMORY: 0.4,
            CognitiveSkill.ATTENTION: 0.4,
            CognitiveSkill.PROCESSING_SPEED: 0.4,
            CognitiveSkill.ABSTRACT_REASONING: 0.4,
            CognitiveSkill.EXECUTIVE_FUNCTION: 0.4,
        }
    )


def _options(correct: Figure) -> tuple[AnswerOption, ...]:
    return (
        AnswerOption(label="A", figure=correct, is_correct=True, origin_rule=RuleType.ROTATION),
        AnswerOption(label="B", figure=Figure("triangle", 90, "small", "red"), is_correct=False, origin_rule=RuleType.ROTATION, explanation="wrong rotation"),
        AnswerOption(label="C", figure=Figure("triangle", 180, "small", "red"), is_correct=False, origin_rule=RuleType.ROTATION, explanation="wrong rotation"),
        AnswerOption(label="D", figure=Figure("triangle", 270, "small", "red"), is_correct=False, origin_rule=RuleType.ROTATION, explanation="wrong rotation"),
        AnswerOption(label="E", figure=Figure("square", 0, "small", "red"), is_correct=False, origin_rule=RuleType.SHAPE, explanation="wrong shape"),
        AnswerOption(label="F", figure=Figure("triangle", 0, "medium", "red"), is_correct=False, origin_rule=RuleType.SIZE, explanation="wrong size"),
    )


class AlwaysTrueRule(BaseRule):
    _register = False
    rule_type = RuleType.SHAPE

    def generate(self, seed: int) -> MatrixPuzzle:
        del seed
        grid = (
            (Figure("circle", 0, "small", "black"), Figure("circle", 0, "small", "black"), Figure("circle", 0, "small", "black")),
            (Figure("circle", 0, "small", "black"), Figure("circle", 0, "small", "black"), Figure("circle", 0, "small", "black")),
            (Figure("circle", 0, "small", "black"), Figure("circle", 0, "small", "black"), None),
        )
        correct = Figure("circle", 0, "small", "black")
        return MatrixPuzzle(
            seed=1,
            rules=(Rule(type=RuleType.SHAPE, value="All cells remain the same", difficulty=0.1),),
            grid=grid,
            correct_answer=correct,
            distractors=(),
            skill_profile=_skill_profile(),
            options=_options(correct),
            correct_index=0,
            explanation=(
                "Rule 1: Shape progression rule -> All cells remain the same.\n"
                "Correct answer: The missing figure is a small black circle rotated to 0 degrees.\n"
                "Row 1: small black circle at 0° | small black circle at 0° | small black circle at 0°\n"
                "Row 2: small black circle at 0° | small black circle at 0° | small black circle at 0°\n"
                "Row 3: small black circle at 0° | small black circle at 0° | missing target cell\n"
                "Column 1: small black circle at 0° | small black circle at 0° | small black circle at 0°\n"
                "Column 2: small black circle at 0° | small black circle at 0° | small black circle at 0°\n"
                "Column 3: small black circle at 0° | small black circle at 0° | missing target cell\n"
                "Option B is incorrect because wrong rotation\n"
                "Option C is incorrect because wrong rotation\n"
                "Option D is incorrect because wrong rotation\n"
                "Option E is incorrect because wrong shape\n"
                "Option F is incorrect because wrong size"
            ),
        )

    def validate(self, grid):
        del grid
        return True

    def explain(self) -> str:
        return "All cells remain the same"

    def difficulty(self) -> float:
        return 0.1

    def overlay(self, puzzle: MatrixPuzzle, seed: int) -> MatrixPuzzle:
        del seed
        return puzzle


def test_matrix_generator_includes_human_reasoning_review_metadata() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2055)

    assert puzzle.quality_metadata is not None
    assert "human_reasoning_review" in puzzle.quality_metadata
    review = puzzle.quality_metadata["human_reasoning_review"]
    assert set(review).issuperset(
        {
            "quality_score",
            "rule_coverage",
            "reasoning_depth",
            "ambiguity_score",
            "perceptual_score",
            "explanation_score",
            "rejection_reasons",
        }
    )
    acceptance = puzzle.quality_metadata["validation_results"]["human_reasoning_validator_acceptance"]
    assert isinstance(acceptance, bool)
    if not acceptance:
        assert review["rejection_reasons"]


def test_regression_rejects_duplicate_answers() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)
    validator = HumanReasoningValidator()

    puzzle = generator.generate(seed=2056)
    selected_rules = [registry.get(rule.type) for rule in puzzle.rules]

    duplicate_option = AnswerOption(
        label=puzzle.options[1].label,
        figure=puzzle.options[puzzle.correct_index].figure,
        is_correct=False,
        reason=puzzle.options[1].reason,
        explanation=puzzle.options[1].explanation,
        origin_rule=puzzle.options[1].origin_rule,
    )
    options = list(puzzle.options)
    options[1] = duplicate_option
    mutated = replace(puzzle, options=tuple(options))

    checks, review, _ = validator.validate(
        mutated,
        selected_rules,
        candidate_rules=[registry.get(rule_type) for rule_type in registry.available()],
        perceptual_validation_passed=True,
    )

    assert checks["human_reasoning_unambiguous"] is False
    assert review.rejection_reasons


def test_regression_rejects_explanation_only_final_cell() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)
    validator = HumanReasoningValidator()

    puzzle = generator.generate(seed=2057)
    selected_rules = [registry.get(rule.type) for rule in puzzle.rules]
    short_explanation = (
        "Rule 1: rotation rule -> 90° clockwise.\n"
        "Correct answer: The missing figure is determined by the rule."
    )
    mutated = replace(puzzle, explanation=short_explanation)

    checks, review, _ = validator.validate(
        mutated,
        selected_rules,
        candidate_rules=[registry.get(rule_type) for rule_type in registry.available()],
        perceptual_validation_passed=True,
    )

    assert checks["explanation_explains_every_row"] is False
    assert checks["explanation_explains_every_column"] is False
    assert review.rejection_reasons


def test_regression_rejects_trivial_puzzle() -> None:
    validator = HumanReasoningValidator()
    rule = AlwaysTrueRule()
    puzzle = rule.generate(seed=1)

    checks, review, diagnostics = validator.validate(
        puzzle,
        [rule],
        candidate_rules=[rule],
        perceptual_validation_passed=True,
    )

    assert checks["every_row_participates_in_reasoning"] is False
    assert checks["every_column_participates_in_reasoning"] is False
    assert diagnostics["candidate_solution_count"] > 1
    assert review.rejection_reasons


def test_regression_rejects_guessing_multiple_valid_options() -> None:
    validator = HumanReasoningValidator()
    rule = AlwaysTrueRule()
    puzzle = rule.generate(seed=2)

    checks, review, diagnostics = validator.validate(
        puzzle,
        [rule],
        candidate_rules=[rule],
        perceptual_validation_passed=True,
    )

    assert diagnostics["candidate_solution_count"] > 1
    assert checks["every_row_participates_in_reasoning"] is False
    assert review.rejection_reasons


def test_regression_rejects_invisible_rotation() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)
    validator = HumanReasoningValidator()

    puzzle = generator.generate(seed=2058)
    selected_rules = [registry.get(rule.type) for rule in puzzle.rules]

    # Mutate visible figures into a rotationally symmetric shape to model the old failure class.
    mutated_grid = [list(row) for row in puzzle.grid]
    for row in range(3):
        for col in range(3):
            cell = mutated_grid[row][col]
            if cell is None:
                continue
            mutated_grid[row][col] = replace(cell, shape="circle")
    mutated = replace(puzzle, grid=tuple(tuple(cell for cell in row) for row in mutated_grid))

    perceptual_ok, _ = PerceptualValidationEngine().validate(mutated)
    checks, review, _ = validator.validate(
        mutated,
        selected_rules,
        candidate_rules=[registry.get(rule_type) for rule_type in registry.available()],
        perceptual_validation_passed=perceptual_ok,
    )

    assert perceptual_ok is False
    assert checks["human_reasoning_unambiguous"] is False or checks["no_hidden_assumptions"] is False
    assert review.rejection_reasons


def test_regression_rejects_symmetric_mirror() -> None:
    validator = HumanReasoningValidator()
    rule = AlwaysTrueRule()
    puzzle = rule.generate(seed=3)

    perceptual_ok, _ = PerceptualValidationEngine().validate(puzzle)
    checks, review, _ = validator.validate(
        puzzle,
        [rule],
        candidate_rules=[rule],
        perceptual_validation_passed=perceptual_ok,
    )

    assert checks["no_hidden_assumptions"] is False or checks["human_reasoning_unambiguous"] is False
    assert review.rejection_reasons
