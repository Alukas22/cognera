"""Unit tests for the Cognera plugin rule engine."""

from dataclasses import replace

from backend.app.matrix import MatrixGenerator, RuleRegistry, RuleType
from backend.app.matrix.models import Figure, MatrixPuzzle, Rule, SkillProfile, CognitiveSkill
from backend.app.matrix.rule_engine import CompositeRule
from backend.app.matrix.rules import BaseRule, RotationRule
import pytest


def test_rotation_rule_is_subclass_of_base_rule() -> None:
    assert issubclass(RotationRule, BaseRule)


def test_rule_registry_discovers_rotation_rule() -> None:
    registry = RuleRegistry()

    assert RuleType.ROTATION in registry.available()
    rule = registry.get(RuleType.ROTATION)

    assert isinstance(rule, RotationRule)


def test_matrix_generator_delegates_to_rule() -> None:
    registry = RuleRegistry()
    rule = registry.get(RuleType.ROTATION)
    puzzle = MatrixGenerator(rule).generate(seed=101)

    assert puzzle.seed == 101
    assert puzzle.rules[0].type == RuleType.ROTATION


def test_rotation_rule_validate_and_explain() -> None:
    rule = RotationRule()
    puzzle = rule.generate(seed=77)

    assert rule.validate(puzzle.grid)
    assert "rotates" in rule.explain().lower()
    assert "clockwise" in rule.explain().lower()


def test_rotation_rule_produces_skill_profile() -> None:
    rule = RotationRule()
    puzzle = rule.generate(seed=77)

    assert puzzle.skill_profile is not None
    skills = puzzle.skill_profile.as_dict()
    assert skills["MENTAL_ROTATION"] == 0.95
    assert skills["VISUAL_PATTERN_RECOGNITION"] == 0.8
    assert all(0.0 <= value <= 1.0 for value in skills.values())


def test_matrix_generator_composes_multiple_rules() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)

    assert 2 <= len(puzzle.rules) <= 3
    assert puzzle.skill_profile is not None
    assert len(puzzle.skill_profile.skills) >= 1
    assert puzzle.correct_answer is not None
    assert 0.0 <= puzzle.difficulty <= 1.0
    assert puzzle.difficulty_label in {"Easy", "Medium", "Hard", "Expert"}
    assert puzzle.explanation
    assert "Rule 1" in puzzle.explanation
    assert len(puzzle.options) == 6
    assert 0 <= puzzle.correct_index < 6
    assert all(cell is None or isinstance(cell, type(puzzle.correct_answer)) for row in puzzle.grid for cell in row)
    assert puzzle.quality_metadata is not None
    assert puzzle.quality_score >= 0.62


def test_matrix_generator_explanation_covers_incorrect_options() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)

    assert "Incorrect options:" in puzzle.explanation
    for option in puzzle.options:
        if option.is_correct:
            continue
        assert f"Option {option.label}" in puzzle.explanation


def test_composite_generation_is_deterministic() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)

    first = generator.generate(seed=2024)
    second = generator.generate(seed=2024)

    assert first == second


def test_matrix_generator_different_seeds_produce_different_puzzles() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)

    first = generator.generate(seed=2024)
    second = generator.generate(seed=2025)

    assert (
        first.grid != second.grid
        or first.solution != second.solution
        or first.rules != second.rules
    )


def test_matrix_generator_has_exactly_one_missing_cell() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)

    assert puzzle.missing_position == (2, 2)
    assert sum(1 for row in puzzle.grid for cell in row if cell is None) == 1
    assert puzzle.grid[2][2] is None


def test_matrix_generator_has_exactly_six_options_and_one_correct_answer() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)

    assert len(puzzle.options) == 6
    assert sum(1 for option in puzzle.options if option.is_correct) == 1
    assert puzzle.options[puzzle.correct_index].is_correct is True


def test_matrix_generator_options_are_unique() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)

    figures = {
        (option.figure.shape, option.figure.rotation, option.figure.size, option.figure.color)
        for option in puzzle.options
    }

    assert len(figures) == 6


def test_matrix_generator_same_seed_produces_same_options() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)

    first = generator.generate(seed=2024)
    second = generator.generate(seed=2024)

    assert first.options == second.options
    assert first.correct_index == second.correct_index


def test_matrix_generator_different_seeds_produce_different_options() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)

    first = generator.generate(seed=2024)
    second = generator.generate(seed=2025)

    assert first.options != second.options or first.correct_index != second.correct_index


def test_matrix_generator_correct_index_tracks_shuffled_option() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=3030)

    assert puzzle.options[puzzle.correct_index].is_correct is True
    assert sum(1 for option in puzzle.options if option.is_correct) == 1


def test_matrix_generator_option_order_varies_across_seeds() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)

    option_orders = {
        tuple(
            (option.figure.shape, option.figure.rotation, option.figure.size, option.figure.color)
            for option in generator.generate(seed=seed).options
        )
        for seed in range(100, 140)
    }

    assert len(option_orders) > 1


def test_matrix_generator_correct_position_distribution_is_approximately_uniform() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)

    samples = 600
    counts = [0, 0, 0, 0, 0, 0]
    for seed in range(samples):
        puzzle = generator.generate(seed=10_000 + seed)
        counts[puzzle.correct_index] += 1

    expected = samples / 6
    tolerance = expected * 0.35

    for count in counts:
        assert abs(count - expected) <= tolerance


def test_matrix_generator_options_are_unique_across_many_seeds() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)

    for seed in range(4000, 4100):
        puzzle = generator.generate(seed=seed)
        figure_keys = {
            (option.figure.shape, option.figure.rotation, option.figure.size, option.figure.color)
            for option in puzzle.options
        }
        assert len(figure_keys) == 6


def test_matrix_generator_explanation_is_rule_based_and_non_empty() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)

    assert puzzle.explanation.strip()

    rule_terms = {
        "rotation": "rotation",
        "shape": "shape",
        "color": "color",
        "size": "size",
        "count": "count",
        "position": "row/column",
        "mirror": "mirror",
    }

    explanation = puzzle.explanation.lower()
    assert any(rule_terms[rule.type.value] in explanation for rule in puzzle.rules)


def test_matrix_generator_explanation_references_at_least_one_applied_rule() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)

    for seed in range(2024, 2040):
        puzzle = generator.generate(seed=seed)
        explanation = puzzle.explanation.lower()
        assert explanation
        assert any(rule.type.value in explanation or (rule.type == RuleType.POSITION and "row/column" in explanation) for rule in puzzle.rules)


def test_matrix_generator_validation_results_are_all_true() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2027)

    assert puzzle.quality_metadata is not None
    results = puzzle.quality_metadata["validation_results"]
    assert all(results.values())
    assert results["minimum_reasoning_depth"] is True
    assert results["requires_entire_matrix_observation"] is True
    assert results["rejects_trivial_single_dimension"] is True


def test_matrix_generator_solution_matches_rule_engine() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)
    rules = [registry.get(rule.type) for rule in puzzle.rules]
    diagnostics = puzzle.quality_metadata["generation_diagnostics"]
    candidate_seed = diagnostics.get("accepted_candidate_seed", puzzle.seed)
    expected = CompositeRule(rules).generate(seed=candidate_seed)

    assert puzzle.grid == expected.grid
    assert puzzle.solution == expected.correct_answer


def test_composite_rule_distractors_preserve_other_dimensions_when_possible() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)

    if len(puzzle.rules) < 2:
        puzzle = MatrixGenerator(registry).generate(seed=2028)

    assert len(puzzle.options) == 6
    distractors = [option for option in puzzle.options if not option.is_correct]
    assert distractors

    assert any(
        sum(
            [
                option.figure.shape != puzzle.solution.shape,
                option.figure.rotation != puzzle.solution.rotation,
                option.figure.size != puzzle.solution.size,
                option.figure.color != puzzle.solution.color,
            ]
        ) == 1
        for option in distractors
    )


def test_matrix_generator_rejects_ambiguous_rule_puzzles() -> None:
    class AmbiguousRule(BaseRule):
        _register = False
        rule_type = RuleType.SHAPE

        def generate(self, seed: int) -> MatrixPuzzle:
            del seed
            grid = (
                (Figure("circle", 0, "small", "red"), Figure("circle", 0, "small", "red"), Figure("circle", 0, "small", "red")),
                (Figure("circle", 0, "small", "red"), Figure("circle", 0, "small", "red"), Figure("circle", 0, "small", "red")),
                (Figure("circle", 0, "small", "red"), Figure("circle", 0, "small", "red"), None),
            )
            return MatrixPuzzle(
                seed=1,
                rules=(Rule(type=RuleType.SHAPE, value="Ambiguous test rule", difficulty=0.1),),
                grid=grid,
                correct_answer=Figure("circle", 0, "small", "red"),
                distractors=(),
                skill_profile=SkillProfile(
                    skills={
                        CognitiveSkill.MENTAL_ROTATION: 0.1,
                        CognitiveSkill.VISUAL_PATTERN_RECOGNITION: 0.1,
                        CognitiveSkill.WORKING_MEMORY: 0.1,
                        CognitiveSkill.ATTENTION: 0.1,
                        CognitiveSkill.PROCESSING_SPEED: 0.1,
                        CognitiveSkill.ABSTRACT_REASONING: 0.1,
                        CognitiveSkill.EXECUTIVE_FUNCTION: 0.1,
                    }
                ),
            )

        def validate(self, grid):
            del grid
            return True

        def explain(self) -> str:
            return "Ambiguous rule for testing."

        def difficulty(self) -> float:
            return 0.1

        def overlay(self, puzzle: MatrixPuzzle, seed: int) -> MatrixPuzzle:
            del seed
            return puzzle

    with pytest.raises(ValueError, match="Strict logical validation"):
        MatrixGenerator(AmbiguousRule()).generate(seed=99)


def test_explanation_rejected_if_only_final_cell_is_explained() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)
    puzzle = generator.generate(seed=2024)

    shortened = replace(
        puzzle,
        explanation=(
            "Rule 1: Rotation rule -> 90° clockwise.\n"
            "Therefore, the missing figure is explained."
        ),
    )

    assert generator._explanation_covers_all_visible_cells(shortened) is False


def test_visible_cells_must_match_rule_reconstruction() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)
    puzzle = generator.generate(seed=2024)
    selected_rules = [registry.get(rule.type) for rule in puzzle.rules]

    mutated_grid = [list(row) for row in puzzle.grid]
    for row in range(3):
        for col in range(3):
            cell = mutated_grid[row][col]
            if cell is not None:
                mutated_grid[row][col] = replace(cell, rotation=(cell.rotation + 90) % 360)
                break
        else:
            continue
        break

    mutated = replace(
        puzzle,
        grid=tuple(tuple(cell for cell in row) for row in mutated_grid),
    )

    assert generator._all_visible_cells_derived_from_rules(mutated, selected_rules) is False
