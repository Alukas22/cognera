"""Tests for assessment-quality gate enforcement."""

from dataclasses import replace

from backend.app.matrix.assessment_quality_gate import AssessmentQualityGate
from backend.app.matrix.human_reasoning_validator import HumanReasoningValidator
from backend.app.matrix.models import AnswerOption, Figure
from backend.app.matrix.rule_engine import MatrixGenerator, RuleRegistry


def _selected_rules(registry: RuleRegistry, puzzle):
    return [registry.get(rule.type) for rule in puzzle.rules]


def test_generated_puzzle_passes_assessment_quality_gate() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)

    validation = puzzle.quality_metadata["validation_results"]
    assert validation["assessment_quality_gate_acceptance"] is True
    assert validation["assessment_explanation_sections_present"] is True
    assert validation["assessment_dominant_reasoning_blind_solver_agrees"] is True
    assert validation["assessment_distractors_violate_exactly_one_rule"] is True


def test_gate_rejects_non_conforming_explanation_format() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2031)
    selected_rules = _selected_rules(registry, puzzle)

    mutated = replace(
        puzzle,
        explanation="Detta ar ett langt stycke utan sektioner eller punktlistor.",
    )

    human_checks, _human_review, human_diagnostics = HumanReasoningValidator().validate(
        mutated,
        selected_rules,
        candidate_rules=[registry.get(rule_type) for rule_type in registry.available()],
        perceptual_validation_passed=True,
    )
    review = AssessmentQualityGate().evaluate(mutated, selected_rules, human_checks, human_diagnostics)

    assert review.passed is False
    assert review.checks["assessment_explanation_sections_present"] is False
    assert review.checks["assessment_explanation_only_bullets_no_paragraphs"] is False


def test_gate_rejects_distractor_violating_multiple_rules() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2040)
    selected_rules = _selected_rules(registry, puzzle)

    wrong_index = next(index for index, option in enumerate(puzzle.options) if not option.is_correct)
    wrong = puzzle.options[wrong_index]
    mutated_figure = Figure(shape="hexagon", rotation=180, size="large", color="blue")
    mutated_option = AnswerOption(
        label=wrong.label,
        figure=mutated_figure,
        is_correct=False,
        reason=wrong.reason,
        explanation=wrong.explanation,
        origin_rule=wrong.origin_rule,
        difficulty=wrong.difficulty,
    )
    options = list(puzzle.options)
    options[wrong_index] = mutated_option
    mutated = replace(puzzle, options=tuple(options))

    human_checks, _human_review, human_diagnostics = HumanReasoningValidator().validate(
        mutated,
        selected_rules,
        candidate_rules=[registry.get(rule_type) for rule_type in registry.available()],
        perceptual_validation_passed=True,
    )
    review = AssessmentQualityGate().evaluate(mutated, selected_rules, human_checks, human_diagnostics)

    assert review.passed is False
    assert review.checks["assessment_distractors_violate_exactly_one_rule"] is False
