"""CLI tools for large-scale matrix quality validation and human review exports."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from .rule_engine import MatrixGenerator, RuleRegistry


def _serialize_option(option: dict) -> dict:
    return {
        "label": option["label"],
        "shape": option["shape"],
        "rotation": option["rotation"],
        "size": option["size"],
        "color": option["color"],
        "is_correct": option["is_correct"],
        "reason": option.get("reason"),
        "origin_rule": option.get("origin_rule"),
        "explanation": option.get("explanation"),
    }


def _puzzle_payload(puzzle) -> dict:
    options = [
        {
            "label": option.label,
            "shape": option.figure.shape,
            "rotation": option.figure.rotation,
            "size": option.figure.size,
            "color": option.figure.color,
            "is_correct": option.is_correct,
            "reason": option.reason.value if option.reason is not None else None,
            "origin_rule": option.origin_rule.value if option.origin_rule is not None else None,
            "explanation": option.explanation,
        }
        for option in puzzle.options
    ]

    return {
        "seed": puzzle.seed,
        "matrix": [
            [None if cell is None else {
                "shape": cell.shape,
                "rotation": cell.rotation,
                "size": cell.size,
                "color": cell.color,
            } for cell in row]
            for row in puzzle.grid
        ],
        "answer_options": [_serialize_option(option) for option in options],
        "correct_answer": puzzle.correct_index,
        "explanation": puzzle.explanation,
        "applied_rules": [{"type": rule.type.value, "value": rule.value} for rule in puzzle.rules],
        "quality_score": puzzle.quality_score,
        "psychometric_quality_score": (puzzle.quality_metadata or {}).get("expert_reviewer_scores", {}).get("overall_psychometric_quality"),
        "difficulty": {
            "label": puzzle.difficulty_label,
            "score": puzzle.difficulty,
        },
        "validation_status": puzzle.quality_metadata.get("validation_results", {}) if puzzle.quality_metadata else {},
        "metadata": puzzle.quality_metadata,
    }


def run_statistical_validation(samples: int, start_seed: int = 10_000) -> dict:
    generator = MatrixGenerator(RuleRegistry())

    valid_count = 0
    failure_count = 0
    duplicated_answers = 0
    rejected_candidates = 0
    ambiguity_rejections = 0
    perceptual_rejections = 0
    explanation_count = 0
    explanation_coverage_sum = 0.0
    unique_distractor_count = 0
    unique_option_count = 0
    answer_position_counter: Counter[str] = Counter()
    quality_scores: list[float] = []
    expert_quality_scores: list[float] = []
    reasoning_depth_scores: list[float] = []
    distractor_scores: list[float] = []
    explanation_scores: list[float] = []
    difficulty_scores: list[float] = []
    difficulty_buckets: Counter[str] = Counter()
    rule_frequency: Counter[str] = Counter()
    rejection_rule_counter: Counter[str] = Counter()
    rejection_ruleset_counter: Counter[str] = Counter()
    failure_pattern_counter: Counter[str] = Counter()
    failure_pattern_reason_counter: Counter[str] = Counter()
    failure_pattern_timeline: list[str] = []
    rejection_events_sample: list[dict[str, object]] = []
    generated_puzzles: list = []

    for offset in range(samples):
        seed = start_seed + offset
        try:
            puzzle = generator.generate(seed=seed)
        except Exception:
            failure_count += 1
            continue

        valid_count += 1
        generated_puzzles.append(puzzle)
        if puzzle.explanation.strip():
            explanation_count += 1
        explanation_coverage_sum += _explanation_coverage(puzzle)

        option_keys = {
            (option.figure.shape, option.figure.rotation, option.figure.size, option.figure.color)
            for option in puzzle.options
        }
        if len(option_keys) == 6:
            unique_option_count += 1
        else:
            duplicated_answers += 1

        distractor_keys = {
            (d.figure.shape, d.figure.rotation, d.figure.size, d.figure.color)
            for d in puzzle.distractors
        }
        if len(distractor_keys) == len(puzzle.distractors):
            unique_distractor_count += 1

        answer_position_counter[puzzle.options[puzzle.correct_index].label] += 1

        quality_scores.append(puzzle.quality_score)
        difficulty_scores.append(puzzle.difficulty)

        reviewer_scores = (puzzle.quality_metadata or {}).get("expert_reviewer_scores", {})
        if reviewer_scores:
            expert_quality_scores.append(float(reviewer_scores.get("overall_psychometric_quality", 0.0)))
            reasoning_depth_scores.append(float(reviewer_scores.get("reasoning_depth", 0.0)))
            distractor_scores.append(float(reviewer_scores.get("distractor_quality", 0.0)))
            explanation_scores.append(float(reviewer_scores.get("explanation_quality", 0.0)))

        difficulty_buckets[puzzle.difficulty_label] += 1
        for rule in puzzle.rules:
            rule_frequency[rule.type.value] += 1

        diagnostics = (puzzle.quality_metadata or {}).get("generation_diagnostics", {})
        rejected_candidates += int(diagnostics.get("rejected_candidates", 0))
        reasons = diagnostics.get("rejection_reasons", {})
        ambiguity_rejections += int(reasons.get("puzzle_is_unambiguous", 0))
        perceptual_rejections += int(reasons.get("perceptual_validation_passed", 0))

        for event in diagnostics.get("rejection_events", []):
            violated = str(event.get("violated_validation_rule", "unknown"))
            rule_set = event.get("generator_rule_set", [])
            rule_set_key = "+".join(rule_set) if isinstance(rule_set, list) else str(rule_set)
            rejection_rule_counter[violated] += 1
            rejection_ruleset_counter[rule_set_key] += 1
            pattern_id = event.get("failure_pattern_id")
            if pattern_id:
                pattern = str(pattern_id)
                failure_pattern_counter[pattern] += 1
                failure_pattern_reason_counter[str(event.get("rejection_reason", "validation_failed"))] += 1
                failure_pattern_timeline.append(pattern)
            if len(rejection_events_sample) < 40:
                rejection_events_sample.append(event)

    denominator = max(valid_count, 1)
    quality_distribution = _quality_distribution(quality_scores)
    answer_distribution = dict(answer_position_counter)

    expected_position = valid_count / 6 if valid_count else 0.0
    max_deviation_ratio = 0.0
    if expected_position:
        max_deviation_ratio = max(
            abs(count - expected_position) / expected_position
            for count in answer_position_counter.values()
        )

    ambiguity_rate = 0.0
    if rejected_candidates:
        ambiguity_rate = ambiguity_rejections / rejected_candidates

    acceptance_rate = valid_count / max(valid_count + rejected_candidates, 1)

    return {
        "samples_requested": samples,
        "samples_generated": valid_count,
        "generation_failures": failure_count,
        "acceptance_rate": acceptance_rate,
        "duplicated_answers": duplicated_answers,
        "rejected_puzzles": rejected_candidates,
        "rejected_by_perceptual_validation": perceptual_rejections,
        "ambiguity_rate": ambiguity_rate,
        "validation_pass_rate": valid_count / max(samples, 1),
        "exactly_one_correct_answer_rate": 1.0 if valid_count > 0 else 0.0,
        "unique_option_rate": unique_option_count / denominator,
        "unique_distractor_rate": unique_distractor_count / denominator,
        "explanation_generated_rate": explanation_count / denominator,
        "explanation_coverage": explanation_coverage_sum / denominator,
        "rule_frequency": dict(rule_frequency),
        "average_difficulty": sum(difficulty_scores) / denominator if difficulty_scores else 0.0,
        "logical_validation_report": {
            "rejection_reason_by_validation_rule": dict(rejection_rule_counter),
            "rejection_reason_by_generator_rule_set": dict(rejection_ruleset_counter),
            "sample_rejection_events": rejection_events_sample,
        },
        "failure_pattern_report": {
            "rejection_reason": dict(failure_pattern_reason_counter),
            "failure_pattern_frequency": dict(failure_pattern_counter),
            "failure_pattern_trend": _failure_pattern_trend(failure_pattern_timeline),
        },
        "answer_position_distribution": answer_distribution,
        "answer_position_max_deviation_ratio": max_deviation_ratio,
        "quality_score_distribution": quality_distribution,
        "quality_score_mean": sum(quality_scores) / denominator if quality_scores else 0.0,
        "quality_score_min": min(quality_scores) if quality_scores else 0.0,
        "quality_score_max": max(quality_scores) if quality_scores else 0.0,
        "expert_quality_score_distribution": _expert_quality_distribution(expert_quality_scores),
        "average_reasoning_depth": sum(reasoning_depth_scores) / max(len(reasoning_depth_scores), 1),
        "average_distractor_score": sum(distractor_scores) / max(len(distractor_scores), 1),
        "average_explanation_score": sum(explanation_scores) / max(len(explanation_scores), 1),
        "difficulty_distribution": dict(difficulty_buckets),
        "top_100_puzzles": [
            _puzzle_payload(puzzle)
            for puzzle in sorted(
                generated_puzzles,
                key=lambda item: (item.quality_metadata or {}).get("expert_reviewer_scores", {}).get("overall_psychometric_quality", 0.0),
                reverse=True,
            )[:100]
        ],
    }


def _explanation_coverage(puzzle) -> float:
    explanation = puzzle.explanation
    if not explanation:
        return 0.0

    rule_hits = 0
    for index, _rule in enumerate(puzzle.rules, start=1):
        if f"Rule {index}" in explanation:
            rule_hits += 1
    rule_coverage = rule_hits / max(len(puzzle.rules), 1)

    incorrect = [option for option in puzzle.options if not option.is_correct]
    incorrect_hits = sum(1 for option in incorrect if f"Option {option.label}" in explanation)
    incorrect_coverage = incorrect_hits / max(len(incorrect), 1)

    return 0.6 * rule_coverage + 0.4 * incorrect_coverage


def _quality_distribution(scores: list[float]) -> dict[str, int]:
    if not scores:
        return {"low": 0, "medium": 0, "high": 0}

    ordered = sorted(scores)
    lower_index = len(ordered) // 3
    upper_index = (2 * len(ordered)) // 3
    lower_cut = ordered[lower_index]
    upper_cut = ordered[upper_index]

    buckets: Counter[str] = Counter()
    for score in scores:
        if score < lower_cut:
            buckets["low"] += 1
        elif score < upper_cut:
            buckets["medium"] += 1
        else:
            buckets["high"] += 1
    return dict(buckets)


def _expert_quality_distribution(scores: list[float]) -> dict[str, int]:
    buckets = {"<8.5": 0, "8.5-9.0": 0, "9.0-9.5": 0, "9.5-10": 0}
    for score in scores:
        if score < 8.5:
            buckets["<8.5"] += 1
        elif score < 9.0:
            buckets["8.5-9.0"] += 1
        elif score < 9.5:
            buckets["9.0-9.5"] += 1
        else:
            buckets["9.5-10"] += 1
    return buckets


def _failure_pattern_trend(pattern_timeline: list[str]) -> dict[str, str]:
    if not pattern_timeline:
        return {}

    midpoint = max(1, len(pattern_timeline) // 2)
    first_half = pattern_timeline[:midpoint]
    second_half = pattern_timeline[midpoint:]

    first_counter = Counter(first_half)
    second_counter = Counter(second_half)
    all_ids = sorted(set(first_counter) | set(second_counter))

    trend: dict[str, str] = {}
    for pattern_id in all_ids:
        before = first_counter.get(pattern_id, 0)
        after = second_counter.get(pattern_id, 0)
        if before == 0 and after > 0:
            trend[pattern_id] = "increasing"
            continue
        if before > 0 and after == 0:
            trend[pattern_id] = "decreasing"
            continue
        if after > before:
            trend[pattern_id] = "increasing"
        elif after < before:
            trend[pattern_id] = "decreasing"
        else:
            trend[pattern_id] = "stable"
    return trend


def export_review_package(count: int, output: Path, seed: int = 2026) -> dict:
    rng = random.Random(seed)
    generator = MatrixGenerator(RuleRegistry())

    records = []
    for _ in range(count):
        puzzle_seed = rng.randrange(1, 2**31 - 1)
        puzzle = generator.generate(seed=puzzle_seed)
        records.append(_puzzle_payload(puzzle))

    package = {
        "count": count,
        "seed": seed,
        "puzzles": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, indent=2), encoding="utf-8")

    return {
        "output": str(output),
        "count": count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Cognera puzzle quality tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Run statistical quality validation")
    validate_parser.add_argument("--samples", type=int, default=10_000)
    validate_parser.add_argument("--start-seed", type=int, default=10_000)
    validate_parser.add_argument("--output", type=Path, default=Path("backend/reports/puzzle_quality_report.json"))
    validate_parser.add_argument("--top-output", type=Path, default=Path("backend/reports/top_100_quality_puzzles.json"))

    export_parser = subparsers.add_parser("export-review", help="Export puzzles for human quality review")
    export_parser.add_argument("--count", type=int, default=100)
    export_parser.add_argument("--seed", type=int, default=2026)
    export_parser.add_argument("--output", type=Path, default=Path("backend/reports/human_review_package.json"))

    args = parser.parse_args()

    if args.command == "validate":
        report = run_statistical_validation(samples=args.samples, start_seed=args.start_seed)
        top_puzzles = report.pop("top_100_puzzles", [])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        args.top_output.parent.mkdir(parents=True, exist_ok=True)
        args.top_output.write_text(json.dumps({"count": len(top_puzzles), "puzzles": top_puzzles}, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return

    if args.command == "export-review":
        summary = export_review_package(count=args.count, output=args.output, seed=args.seed)
        print(json.dumps(summary, indent=2))
        return


if __name__ == "__main__":
    main()
