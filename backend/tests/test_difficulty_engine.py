from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.matrix import CognitiveDifficultyEngine, DifficultyEngine, MatrixGenerator, RuleRegistry, RuleType
from backend.app.matrix.rules import RotationRule, CountRule, ShapeRule, PositionRule


def test_cognitive_difficulty_profile_scores_are_normalized() -> None:
    rule = RotationRule()
    puzzle = MatrixGenerator(rule).generate(seed=10)
    profile = puzzle.difficulty_profile

    assert profile is not None
    assert 0.0 <= profile.overall <= 1.0
    assert 0.0 <= profile.working_memory <= 1.0
    assert 0.0 <= profile.pattern_complexity <= 1.0
    assert 0.0 <= profile.visual_complexity <= 1.0
    assert 0.0 <= profile.rule_complexity <= 1.0
    assert 0.0 <= profile.abstraction <= 1.0
    assert 0.0 <= profile.distractor_strength <= 1.0
    assert DifficultyEngine.score(puzzle) == profile.overall


def test_cognitive_difficulty_overall_matches_weighted_formula() -> None:
    registry = RuleRegistry()
    rules = [registry.get(RuleType.POSITION), registry.get(RuleType.COUNT)]
    composite = MatrixGenerator(registry).constraint_engine
    assert composite.validate_rules(rules)

    from backend.app.matrix.rule_engine import CompositeRule
    raw_puzzle = CompositeRule(composite.validated_rules).generate(seed=7)
    puzzle = MatrixGenerator(registry)._finalize_puzzle(raw_puzzle)
    profile = puzzle.difficulty_profile

    assert profile is not None
    expected = min(
        1.0,
        max(
            0.0,
            0.25 * profile.working_memory
            + 0.20 * profile.rule_complexity
            + 0.15 * profile.abstraction
            + 0.15 * profile.pattern_complexity
            + 0.15 * profile.visual_complexity
            + 0.10 * profile.distractor_strength,
        ),
    )

    assert profile.overall == expected


def test_cognitive_difficulty_is_reproducible() -> None:
    registry = RuleRegistry()
    generator = MatrixGenerator(registry)

    first = generator.generate(seed=2024).difficulty_profile
    second = generator.generate(seed=2024).difficulty_profile

    assert first == second


def test_cognitive_difficulty_engine_evaluates_raw_puzzle_deterministically() -> None:
    engine = CognitiveDifficultyEngine()
    rule = RotationRule()
    puzzle = rule.generate(seed=10)

    first = engine.evaluate(puzzle)
    second = engine.evaluate(puzzle)

    assert first == second


def test_matrix_demo_endpoint_includes_difficulty() -> None:
    client = TestClient(app)
    response = client.get("/matrix/demo")
    payload = response.json()

    assert response.status_code == 200
    assert "difficulty" in payload
    assert "difficulty_profile" in payload
    assert isinstance(payload["difficulty"], float)
    assert 0.0 <= payload["difficulty"] <= 1.0
    assert payload["difficulty_profile"]["overall"] == payload["difficulty"]
