"""CLI tools for large-scale matrix quality validation and human review exports."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from .puzzle_review_framework import run_puzzle_review_framework
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


def run_statistical_validation(
    samples: int,
    start_seed: int = 10_000,
    generation_max_attempts: int = 64,
) -> dict:
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
    accepted_examples: list[dict[str, object]] = []
    rejected_examples: list[dict[str, object]] = []
    total_generation_attempts = 0
    total_candidate_puzzles = 0
    duplicate_distractor_rejections = 0
    ambiguity_rejection_events = 0

    for offset in range(samples):
        seed = start_seed + offset
        try:
            puzzle = generator.generate(seed=seed, max_attempts=generation_max_attempts)
        except Exception:
            failure_count += 1
            continue

        valid_count += 1
        generated_puzzles.append(puzzle)
        if len(accepted_examples) < 12:
            accepted_examples.append(
                {
                    "seed": puzzle.seed,
                    "rules": [rule.type.value for rule in puzzle.rules],
                    "quality_score": puzzle.quality_score,
                    "difficulty": puzzle.difficulty,
                    "difficulty_label": puzzle.difficulty_label,
                    "validation_status": (puzzle.quality_metadata or {}).get("validation_results", {}),
                    "matrix": [
                        [
                            None
                            if cell is None
                            else {
                                "shape": cell.shape,
                                "rotation": cell.rotation,
                                "size": cell.size,
                                "color": cell.color,
                            }
                            for cell in row
                        ]
                        for row in puzzle.grid
                    ],
                    "correct_index": puzzle.correct_index,
                    "answer_options": [
                        {
                            "label": option.label,
                            "shape": option.figure.shape,
                            "rotation": option.figure.rotation,
                            "size": option.figure.size,
                            "color": option.figure.color,
                            "is_correct": option.is_correct,
                            "reason": option.reason.value if option.reason is not None else None,
                            "origin_rule": option.origin_rule.value if option.origin_rule is not None else None,
                        }
                        for option in puzzle.options
                    ],
                }
            )
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
            (
                getattr(distractor, "figure", distractor).shape,
                getattr(distractor, "figure", distractor).rotation,
                getattr(distractor, "figure", distractor).size,
                getattr(distractor, "figure", distractor).color,
            )
            for distractor in puzzle.distractors
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
        attempts = int(diagnostics.get("attempts", 1))
        total_generation_attempts += attempts
        total_candidate_puzzles += attempts

        rejected_candidates += int(diagnostics.get("rejected_candidates", 0))
        reasons = diagnostics.get("rejection_reasons", {})
        for reason, count in reasons.items():
            rejection_rule_counter[str(reason)] += int(count)
        ambiguity_rejections += int(reasons.get("puzzle_is_unambiguous", 0))
        perceptual_rejections += int(reasons.get("perceptual_validation_passed", 0))
        duplicate_distractor_rejections += int(reasons.get("assessment_distractors_not_near_duplicate", 0))
        ambiguity_rejection_events += (
            int(reasons.get("puzzle_is_unambiguous", 0))
            + int(reasons.get("human_reasoning_unambiguous", 0))
            + int(reasons.get("assessment_dominant_reasoning_blind_solver_agrees", 0))
            + int(reasons.get("assessment_dominant_reasoning_gap_is_clear", 0))
            + int(reasons.get("assessment_dominant_reasoning_no_viable_alternative_rules", 0))
            + int(reasons.get("assessment_dominant_reasoning_human_unambiguous", 0))
        )

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
            if len(rejected_examples) < 20:
                rejected_examples.append(event)

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

    acceptance_rate = valid_count / max(valid_count + rejected_candidates, 1)
    rejection_rate = rejected_candidates / max(total_candidate_puzzles, 1)
    average_generation_attempts = total_generation_attempts / max(valid_count, 1)
    most_common_rejection_reasons = rejection_rule_counter.most_common(10)
    ambiguity_rate = ambiguity_rejection_events / max(rejected_candidates, 1)
    duplicate_distractor_rate = duplicate_distractor_rejections / max(rejected_candidates, 1)

    return {
        "samples_requested": samples,
        "generation_max_attempts": generation_max_attempts,
        "samples_generated": valid_count,
        "generation_failures": failure_count,
        "acceptance_rate": acceptance_rate,
        "rejection_rate": rejection_rate,
        "average_generation_attempts": average_generation_attempts,
        "candidate_puzzles_evaluated": total_candidate_puzzles,
        "duplicated_answers": duplicated_answers,
        "rejected_puzzles": rejected_candidates,
        "rejected_by_perceptual_validation": perceptual_rejections,
        "ambiguity_rate": ambiguity_rate,
        "duplicate_distractor_rate": duplicate_distractor_rate,
        "most_common_rejection_reasons": [
            {"reason": reason, "count": count}
            for reason, count in most_common_rejection_reasons
        ],
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
            "rejected_puzzle_examples": rejected_examples,
            "accepted_puzzle_examples": accepted_examples,
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

    required_sections = ["Översikt", "Steg 1", "Steg 2", "Kontroll", "Rätt svar"]
    rule_hits = sum(1 for section in required_sections if section in explanation)
    rule_coverage = rule_hits / len(required_sections)

    incorrect = [option for option in puzzle.options if not option.is_correct]
    incorrect_hits = sum(1 for option in incorrect if f"Alternativ {option.label}" in explanation)
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


def export_review_package(
    count: int,
    output: Path,
    seed: int = 2026,
    generation_max_attempts: int = 96,
) -> dict:
    rng = random.Random(seed)
    generator = MatrixGenerator(RuleRegistry())

    records = []
    attempts = 0
    max_attempts = max(count * 20, count + 1)
    while len(records) < count and attempts < max_attempts:
        attempts += 1
        puzzle_seed = rng.randrange(1, 2**31 - 1)
        try:
            puzzle = generator.generate(seed=puzzle_seed, max_attempts=generation_max_attempts)
        except ValueError:
            continue
        records.append(_puzzle_payload(puzzle))

    if len(records) < count:
        raise ValueError(
            "Unable to export requested number of review puzzles "
            f"(requested={count}, generated={len(records)}, attempts={attempts})."
        )

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
        "attempts": attempts,
        "generation_max_attempts": generation_max_attempts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Cognera puzzle quality tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Run statistical quality validation")
    validate_parser.add_argument("--samples", type=int, default=10_000)
    validate_parser.add_argument("--start-seed", type=int, default=10_000)
    validate_parser.add_argument("--generation-max-attempts", type=int, default=64)
    validate_parser.add_argument("--output", type=Path, default=Path("backend/reports/puzzle_quality_report.json"))
    validate_parser.add_argument("--top-output", type=Path, default=Path("backend/reports/top_100_quality_puzzles.json"))

    export_parser = subparsers.add_parser("export-review", help="Export puzzles for human quality review")
    export_parser.add_argument("--count", type=int, default=100)
    export_parser.add_argument("--seed", type=int, default=2026)
    export_parser.add_argument("--generation-max-attempts", type=int, default=96)
    export_parser.add_argument("--output", type=Path, default=Path("backend/reports/human_review_package.json"))

    framework_parser = subparsers.add_parser("review-framework", help="Run puzzle review framework")
    framework_parser.add_argument("--count", type=int, default=1000)
    framework_parser.add_argument("--start-seed", type=int, default=100_000)
    framework_parser.add_argument("--generation-max-attempts", type=int, default=96)
    framework_parser.add_argument("--max-seed-attempts", type=int, default=0)
    framework_parser.add_argument(
        "--output",
        type=Path,
        default=Path("backend/reports/puzzle_review_framework_report.json"),
    )
    framework_parser.add_argument(
        "--po-output",
        type=Path,
        default=Path("backend/reports/product_owner_review_set.json"),
    )

    args = parser.parse_args()

    if args.command == "validate":
        report = run_statistical_validation(
            samples=args.samples,
            start_seed=args.start_seed,
            generation_max_attempts=args.generation_max_attempts,
        )
        top_puzzles = report.pop("top_100_puzzles", [])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        args.top_output.parent.mkdir(parents=True, exist_ok=True)
        args.top_output.write_text(json.dumps({"count": len(top_puzzles), "puzzles": top_puzzles}, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return

    if args.command == "export-review":
        summary = export_review_package(
            count=args.count,
            output=args.output,
            seed=args.seed,
            generation_max_attempts=args.generation_max_attempts,
        )
        print(json.dumps(summary, indent=2))
        return

    if args.command == "review-framework":
        result = run_puzzle_review_framework(
            target_reviews=args.count,
            start_seed=args.start_seed,
            generation_max_attempts=args.generation_max_attempts,
            max_seed_attempts=(None if args.max_seed_attempts <= 0 else args.max_seed_attempts),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result["framework_report"], indent=2), encoding="utf-8")
        args.po_output.parent.mkdir(parents=True, exist_ok=True)
        args.po_output.write_text(json.dumps(result["product_owner_review_set"], indent=2), encoding="utf-8")
        print(json.dumps(result["framework_report"]["summary"], indent=2))
        return


if __name__ == "__main__":
    main()
