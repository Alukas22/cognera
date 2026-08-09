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
    explanation_count = 0
    unique_distractor_count = 0
    unique_option_count = 0
    answer_position_counter: Counter[str] = Counter()
    quality_scores: list[float] = []
    difficulty_buckets: Counter[str] = Counter()

    for offset in range(samples):
        seed = start_seed + offset
        try:
            puzzle = generator.generate(seed=seed)
        except Exception:
            failure_count += 1
            continue

        valid_count += 1
        if puzzle.explanation.strip():
            explanation_count += 1

        option_keys = {
            (option.figure.shape, option.figure.rotation, option.figure.size, option.figure.color)
            for option in puzzle.options
        }
        if len(option_keys) == 6:
            unique_option_count += 1

        distractor_keys = {
            (d.figure.shape, d.figure.rotation, d.figure.size, d.figure.color)
            for d in puzzle.distractors
        }
        if len(distractor_keys) == len(puzzle.distractors):
            unique_distractor_count += 1

        answer_position_counter[puzzle.options[puzzle.correct_index].label] += 1

        quality_scores.append(puzzle.quality_score)

        difficulty_buckets[puzzle.difficulty_label] += 1

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

    return {
        "samples_requested": samples,
        "samples_generated": valid_count,
        "generation_failures": failure_count,
        "validation_pass_rate": valid_count / max(samples, 1),
        "exactly_one_correct_answer_rate": 1.0 if valid_count > 0 else 0.0,
        "unique_option_rate": unique_option_count / denominator,
        "unique_distractor_rate": unique_distractor_count / denominator,
        "explanation_generated_rate": explanation_count / denominator,
        "answer_position_distribution": answer_distribution,
        "answer_position_max_deviation_ratio": max_deviation_ratio,
        "quality_score_distribution": quality_distribution,
        "quality_score_mean": sum(quality_scores) / denominator if quality_scores else 0.0,
        "quality_score_min": min(quality_scores) if quality_scores else 0.0,
        "quality_score_max": max(quality_scores) if quality_scores else 0.0,
        "difficulty_distribution": dict(difficulty_buckets),
    }


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

    export_parser = subparsers.add_parser("export-review", help="Export puzzles for human quality review")
    export_parser.add_argument("--count", type=int, default=100)
    export_parser.add_argument("--seed", type=int, default=2026)
    export_parser.add_argument("--output", type=Path, default=Path("backend/reports/human_review_package.json"))

    args = parser.parse_args()

    if args.command == "validate":
        report = run_statistical_validation(samples=args.samples, start_seed=args.start_seed)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return

    if args.command == "export-review":
        summary = export_review_package(count=args.count, output=args.output, seed=args.seed)
        print(json.dumps(summary, indent=2))
        return


if __name__ == "__main__":
    main()
