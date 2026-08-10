"""Tests for human solvability gate enforcement."""

from dataclasses import replace

from backend.app.matrix.human_reasoning_validator import HumanReasoningValidator
from backend.app.matrix.human_solvability_gate import HumanSolvabilityGate
from backend.app.matrix.models import AnswerOption, Figure
from backend.app.matrix.rule_engine import MatrixGenerator, RuleRegistry


def _selected_rules(registry: RuleRegistry, puzzle):
    return [registry.get(rule.type) for rule in puzzle.rules]


def test_generated_puzzle_passes_human_solvability_gate() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2000)

    validation = puzzle.quality_metadata["validation_results"]
    assert validation["human_solvability_gate_acceptance"] is True
    assert validation["human_solvability_primary_rule_dominant"] is True
    assert validation["human_solvability_likely_solver_consensus"] is True


def test_gate_rejects_when_expert_explainability_fails() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2001)
    selected_rules = _selected_rules(registry, puzzle)

    human_checks, _human_review, human_diagnostics = HumanReasoningValidator().validate(
        puzzle,
        selected_rules,
        candidate_rules=[registry.get(rule_type) for rule_type in registry.available()],
        perceptual_validation_passed=True,
    )
    review = HumanSolvabilityGate().evaluate(
        puzzle,
        selected_rules,
        human_checks=human_checks,
        human_diagnostics=human_diagnostics,
        reviewer_accepted=False,
        reviewer_checks={},
    )

    assert review.passed is False
    assert review.checks["human_solvability_expert_step_by_step_explainable"] is False


def test_gate_rejects_unrealistic_distractor() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2002)
    selected_rules = _selected_rules(registry, puzzle)

    wrong_indices = [index for index, option in enumerate(puzzle.options) if not option.is_correct][:2]
    mutated = replace(
        puzzle,
        options=tuple(
            AnswerOption(
                label=option.label,
                figure=(
                    Figure(shape="hexagon", rotation=180, size="large", color="blue")
                    if index in wrong_indices
                    else option.figure
                ),
                is_correct=option.is_correct,
                reason=(None if index in wrong_indices else option.reason),
                explanation=option.explanation,
                origin_rule=(None if index in wrong_indices else option.origin_rule),
                difficulty=option.difficulty,
            )
            for index, option in enumerate(puzzle.options)
        ),
    )

    human_checks, _human_review, human_diagnostics = HumanReasoningValidator().validate(
        mutated,
        selected_rules,
        candidate_rules=[registry.get(rule_type) for rule_type in registry.available()],
        perceptual_validation_passed=True,
    )
    review = HumanSolvabilityGate().evaluate(
        mutated,
        selected_rules,
        human_checks=human_checks,
        human_diagnostics=human_diagnostics,
        reviewer_accepted=True,
        reviewer_checks={"explanation_is_concrete": True},
    )

    assert review.passed is False
    assert review.checks["human_solvability_distractors_are_realistic_mistakes"] is False