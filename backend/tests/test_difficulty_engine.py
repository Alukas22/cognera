from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.matrix import DifficultyEngine, MatrixGenerator, RuleRegistry, RuleType
from backend.app.matrix.rules import RotationRule, CountRule, ShapeRule, PositionRule


def test_difficulty_engine_scores_single_rule_between_zero_and_one() -> None:
    rule = RotationRule()
    puzzle = rule.generate(seed=10)

    score = DifficultyEngine.score(puzzle)

    assert 0.0 <= score <= 1.0
    assert score == rule.difficulty()


def test_difficulty_engine_scores_composite_with_interaction_bonus() -> None:
    registry = RuleRegistry()
    rules = [registry.get(RuleType.POSITION), registry.get(RuleType.COUNT)]
    composite = MatrixGenerator(registry).constraint_engine
    assert composite.validate_rules(rules)

    # Create a composite puzzle deterministically using the validated rules.
    from backend.app.matrix.rule_engine import CompositeRule
    puzzle = CompositeRule(composite.validated_rules).generate(seed=7)

    score = DifficultyEngine.score(puzzle)

    assert 0.0 <= score <= 1.0
    assert score > sum(rule.difficulty for rule in puzzle.rules) / len(puzzle.rules)


def test_matrix_demo_endpoint_includes_difficulty() -> None:
    client = TestClient(app)
    response = client.get("/matrix/demo")
    payload = response.json()

    assert response.status_code == 200
    assert "difficulty" in payload
    assert isinstance(payload["difficulty"], float)
    assert 0.0 <= payload["difficulty"] <= 1.0
