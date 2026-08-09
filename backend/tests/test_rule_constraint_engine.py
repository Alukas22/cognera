from backend.app.matrix import RuleConstraintEngine, RuleRegistry, RuleType
from backend.app.matrix.rules import RotationRule, CountRule, PositionRule


def test_validate_rules_rejects_duplicates() -> None:
    engine = RuleConstraintEngine()
    rule_one = RotationRule()
    rule_two = RotationRule()

    assert not engine.validate_rules([rule_one, rule_two])
    assert "Duplicate rule types" in engine.validation_reasons[0]


def test_validate_rules_rejects_impossible_combinations() -> None:
    engine = RuleConstraintEngine(sample_seeds=(0, 1, 2, 3))
    count_rule = CountRule()
    rotation_rule = RotationRule()

    assert not engine.validate_rules([count_rule, rotation_rule])
    assert any("produced no valid puzzle" in reason for reason in engine.validation_reasons)


def test_rule_registry_available_rules_are_validated() -> None:
    registry = RuleRegistry()
    engine = RuleConstraintEngine()
    rules = [registry.get(RuleType.POSITION), registry.get(RuleType.COUNT)]

    assert engine.validate_rules(rules)
    assert engine.validated_rules == rules


def test_validate_rules_rejects_ambiguous_answer() -> None:
    engine = RuleConstraintEngine(sample_seeds=(0, 1, 2, 3))
    rules = [PositionRule(), CountRule()]

    assert engine.validate_rules(rules)
    assert engine.validated_rules == rules
