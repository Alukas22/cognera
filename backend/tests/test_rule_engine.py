"""Unit tests for the Cognera plugin rule engine."""

from backend.app.matrix import MatrixGenerator, RuleRegistry, RuleType
from backend.app.matrix.rule_engine import CompositeRule
from backend.app.matrix.rules import BaseRule, RotationRule


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

    assert 1 <= len(puzzle.rules) <= 3
    assert puzzle.skill_profile is not None
    assert len(puzzle.skill_profile.skills) >= 1
    assert puzzle.correct_answer is not None
    assert 0.0 <= puzzle.difficulty <= 1.0
    assert puzzle.explanation
    assert len(puzzle.options) == 6
    assert 0 <= puzzle.correct_index < 6
    assert all(cell is None or isinstance(cell, type(puzzle.correct_answer)) for row in puzzle.grid for cell in row)


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


def test_matrix_generator_solution_matches_rule_engine() -> None:
    registry = RuleRegistry()
    puzzle = MatrixGenerator(registry).generate(seed=2024)
    rules = [registry.get(rule.type) for rule in puzzle.rules]
    expected = CompositeRule(rules).generate(seed=2024)

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
