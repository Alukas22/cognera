"""Internal puzzle review framework for assessment-quality validation."""

from __future__ import annotations

from collections import Counter
import random
from statistics import median

from .rule_engine import CompositeRule, MatrixGenerator, RuleRegistry


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _score_from_ratio(ratio: float) -> float:
    bounded = _clamp(ratio, 0.0, 1.0)
    return round(1.0 + (9.0 * bounded), 2)


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)


def _to_bool(value: object) -> bool:
    return bool(value)


def _puzzle_payload(puzzle) -> dict[str, object]:
    return {
        "seed": puzzle.seed,
        "rules": [{"type": rule.type.value, "value": rule.value} for rule in puzzle.rules],
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
        "options": [
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
        "correct_index": puzzle.correct_index,
        "quality_score": puzzle.quality_score,
        "difficulty": {
            "score": puzzle.difficulty,
            "label": puzzle.difficulty_label,
        },
        "validation_status": (puzzle.quality_metadata or {}).get("validation_results", {}),
    }


def _rule_ambiguity_tag(validation: dict[str, bool], human_reasoning_diag: dict[str, object]) -> str | None:
    alternatives = int(human_reasoning_diag.get("alternative_rule_set_count", 0))
    if alternatives > 1:
        return "multiple_viable_rule_sets"
    if not _to_bool(validation.get("human_solvability_primary_rule_dominant", True)):
        return "no_dominant_primary_rule"
    if not _to_bool(validation.get("human_solvability_primary_rule_visually_discoverable", True)):
        return "primary_rule_not_visually_discoverable"
    if not _to_bool(validation.get("assessment_dominant_reasoning_gap_is_clear", True)):
        return "weak_gap_between_primary_and_alternatives"
    if not _to_bool(validation.get("human_solvability_secondary_rules_refine_only", True)):
        return "secondary_rules_compete_with_primary"
    return None


def _distractor_problem_tag(validation: dict[str, bool]) -> str | None:
    if not _to_bool(validation.get("assessment_distractors_not_near_duplicate", True)):
        return "near_duplicate_distractors"
    if not _to_bool(validation.get("assessment_distractors_violate_exactly_one_rule", True)):
        return "multi_rule_violation_distractors"
    if not _to_bool(validation.get("human_solvability_distractors_are_realistic_mistakes", True)):
        return "distractors_not_human_realistic"
    if not _to_bool(validation.get("assessment_distractors_plausible_not_obvious", True)):
        return "distractors_too_obvious"
    return None


def _criterion_scores(puzzle) -> dict[str, object]:
    metadata = puzzle.quality_metadata or {}
    validation: dict[str, bool] = metadata.get("validation_results", {})
    expert_scores: dict[str, float] = metadata.get("expert_reviewer_scores", {})
    diagnostics: dict[str, object] = metadata.get("generation_diagnostics", {})
    human_reasoning_diag: dict[str, object] = diagnostics.get("human_reasoning", {})

    unique_solution_pass = all(
        [
            _to_bool(validation.get("exactly_one_correct_answer", False)),
            _to_bool(validation.get("puzzle_is_unambiguous", False)),
            _to_bool(validation.get("human_reasoning_unambiguous", False)),
            _to_bool(validation.get("unique_rule_set_interpretation", False)),
        ]
    )

    alternative_rule_sets = int(human_reasoning_diag.get("alternative_rule_set_count", 0))

    human_solvability_signals = [
        _to_bool(validation.get("human_solvability_likely_solver_consensus", False)),
        _to_bool(validation.get("human_solvability_expert_step_by_step_explainable", False)),
        _to_bool(validation.get("no_hidden_assumptions", False)),
        _to_bool(validation.get("explanation_derived_from_rule_objects", False)),
        _to_bool(validation.get("rules_visible_without_answer", False)),
        _to_bool(validation.get("human_reasoning_unambiguous", False)),
    ]
    human_solvability_ratio = _mean([1.0 if item else 0.0 for item in human_solvability_signals])
    human_solvability_ratio = _clamp(human_solvability_ratio - min(0.4, alternative_rule_sets * 0.1), 0.0, 1.0)
    human_solvability = _score_from_ratio(human_solvability_ratio)

    rule_clarity_signals = [
        _to_bool(validation.get("human_solvability_primary_rule_dominant", False)),
        _to_bool(validation.get("human_solvability_primary_rule_visually_discoverable", False)),
        _to_bool(validation.get("human_solvability_secondary_rules_refine_only", False)),
        _to_bool(validation.get("assessment_dominant_reasoning_gap_is_clear", False)),
        _to_bool(validation.get("assessment_dominant_reasoning_blind_solver_agrees", False)),
    ]
    rule_clarity_ratio = _mean([1.0 if item else 0.0 for item in rule_clarity_signals])
    rule_clarity_ratio = _clamp(rule_clarity_ratio - min(0.4, alternative_rule_sets * 0.1), 0.0, 1.0)
    rule_clarity = _score_from_ratio(rule_clarity_ratio)

    visual_clarity_signals = [
        _to_bool(validation.get("perceptual_validation_passed", False)),
        _to_bool(validation.get("assessment_readability_not_cluttered", False)),
        _to_bool(validation.get("assessment_readability_structure_distinguishable", False)),
        _to_bool(validation.get("assessment_readability_elegant_not_confusing", False)),
        _to_bool(validation.get("assessment_visual_balance_no_unique_outlier", False)),
        _to_bool(validation.get("assessment_visual_balance_detail_spread_limited", False)),
        _to_bool(validation.get("assessment_visual_balance_uniform_styling", False)),
    ]
    visual_clarity = _score_from_ratio(_mean([1.0 if item else 0.0 for item in visual_clarity_signals]))

    distractor_signals = [
        _to_bool(validation.get("assessment_distractors_violate_exactly_one_rule", False)),
        _to_bool(validation.get("assessment_distractors_not_near_duplicate", False)),
        _to_bool(validation.get("assessment_distractors_plausible_not_obvious", False)),
        _to_bool(validation.get("human_solvability_distractors_are_realistic_mistakes", False)),
    ]
    expert_distractor = float(expert_scores.get("distractor_quality", 0.0))
    distractor_ratio = (
        sum(1.0 if item else 0.0 for item in distractor_signals) + _clamp(expert_distractor / 10.0, 0.0, 1.0)
    ) / (len(distractor_signals) + 1)
    distractor_quality = _score_from_ratio(distractor_ratio)

    expert_overall = float(expert_scores.get("overall_psychometric_quality", 0.0))
    quality_score = float(puzzle.quality_score or 0.0)
    raven_binary_signals = [
        _to_bool(validation.get("minimum_reasoning_depth", False)),
        _to_bool(validation.get("requires_entire_matrix_observation", False)),
        _to_bool(validation.get("rejects_trivial_single_dimension", False)),
        _to_bool(validation.get("no_redundant_rules", False)),
    ]
    raven_ratio = (
        0.35 * _clamp(expert_overall / 10.0, 0.0, 1.0)
        + 0.25 * _clamp(quality_score, 0.0, 1.0)
        + 0.40 * _mean([1.0 if item else 0.0 for item in raven_binary_signals])
    )
    raven_similarity = _score_from_ratio(raven_ratio)

    overall = round(
        (0.25 * human_solvability)
        + (0.20 * rule_clarity)
        + (0.20 * visual_clarity)
        + (0.20 * distractor_quality)
        + (0.15 * raven_similarity),
        2,
    )
    if not unique_solution_pass:
        overall = min(overall, 4.0)

    accepted_for_product = unique_solution_pass and overall >= 8.0

    rule_ambiguity_tag = _rule_ambiguity_tag(validation, human_reasoning_diag)
    distractor_problem_tag = _distractor_problem_tag(validation)

    rejection_reason = None
    if not accepted_for_product:
        if not unique_solution_pass:
            rejection_reason = "unique_solution_failed"
        else:
            criterion_pairs = [
                ("human_solvability", human_solvability),
                ("rule_clarity", rule_clarity),
                ("visual_clarity", visual_clarity),
                ("distractor_quality", distractor_quality),
                ("raven_similarity", raven_similarity),
            ]
            lowest = min(criterion_pairs, key=lambda item: item[1])
            rejection_reason = f"low_{lowest[0]}"

    return {
        "unique_solution": "Pass" if unique_solution_pass else "Fail",
        "human_solvability": human_solvability,
        "rule_clarity": rule_clarity,
        "visual_clarity": visual_clarity,
        "distractor_quality": distractor_quality,
        "raven_similarity": raven_similarity,
        "overall_assessment_quality": overall,
        "accepted_for_product": accepted_for_product,
        "rejection_reason": rejection_reason,
        "rule_ambiguity_tag": rule_ambiguity_tag,
        "distractor_problem_tag": distractor_problem_tag,
        "quality_score": quality_score,
        "psychometric_quality_score": expert_overall,
        "validation_snapshot": validation,
    }


def run_puzzle_review_framework(
    target_reviews: int,
    start_seed: int = 100_000,
    generation_max_attempts: int = 1,
    max_seed_attempts: int | None = None,
) -> dict[str, object]:
    if target_reviews < 1:
        raise ValueError("target_reviews must be >= 1")

    generator = MatrixGenerator(RuleRegistry())
    reviews: list[dict[str, object]] = []
    attempted_seeds = 0
    generation_failures = 0

    seed = start_seed
    hard_limit = max_seed_attempts if max_seed_attempts is not None else target_reviews * 60

    available_rules = sorted(generator.registry.available(), key=lambda rule_type: rule_type.value)
    candidate_rules = [generator.registry.get(rule_type) for rule_type in available_rules]

    while len(reviews) < target_reviews and attempted_seeds < hard_limit:
        attempted_seeds += 1
        try:
            puzzle = _generate_candidate_puzzle(
                generator,
                seed,
                available_rules,
                candidate_rules,
                generation_max_attempts,
            )
        except Exception:
            generation_failures += 1
            seed += 1
            continue

        scorecard = _criterion_scores(puzzle)
        review = {
            "seed": puzzle.seed,
            "rules": [rule.type.value for rule in puzzle.rules],
            **scorecard,
            "puzzle": _puzzle_payload(puzzle),
        }
        reviews.append(review)
        seed += 1

    if len(reviews) < target_reviews:
        raise ValueError(
            "Unable to collect enough puzzle reviews "
            f"(requested={target_reviews}, collected={len(reviews)}, seed_attempts={attempted_seeds})."
        )

    overall_scores = [float(review["overall_assessment_quality"]) for review in reviews]
    accepted = [review for review in reviews if bool(review["accepted_for_product"])]
    rejected = [review for review in reviews if not bool(review["accepted_for_product"])]

    rejection_reason_counter: Counter[str] = Counter(
        str(review["rejection_reason"])
        for review in rejected
        if review["rejection_reason"] is not None
    )
    ambiguity_counter: Counter[str] = Counter(
        str(review["rule_ambiguity_tag"])
        for review in reviews
        if review["rule_ambiguity_tag"] is not None
    )
    distractor_counter: Counter[str] = Counter(
        str(review["distractor_problem_tag"])
        for review in reviews
        if review["distractor_problem_tag"] is not None
    )

    ordered_best = sorted(
        reviews,
        key=lambda item: (
            float(item["overall_assessment_quality"]),
            float(item["psychometric_quality_score"]),
            float(item["quality_score"]),
        ),
        reverse=True,
    )
    ordered_worst = sorted(
        reviews,
        key=lambda item: (
            float(item["overall_assessment_quality"]),
            float(item["psychometric_quality_score"]),
            float(item["quality_score"]),
        ),
    )

    best_examples = ordered_best[:20]
    worst_examples = ordered_worst[:20]

    po_candidates = accepted if len(accepted) >= 100 else ordered_best
    product_owner_set = sorted(
        po_candidates,
        key=lambda item: (
            float(item["overall_assessment_quality"]),
            float(item["psychometric_quality_score"]),
            float(item["quality_score"]),
        ),
        reverse=True,
    )[:100]

    summary = {
        "target_reviews": target_reviews,
        "reviews_generated": len(reviews),
        "seed_range": {
            "start_seed": start_seed,
            "end_seed_inclusive": seed - 1,
            "seed_attempts": attempted_seeds,
            "generation_failures": generation_failures,
            "generation_max_attempts": generation_max_attempts,
        },
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "acceptance_rate": len(accepted) / max(len(reviews), 1),
        "average_score": round(_mean(overall_scores), 4),
        "median_score": round(float(median(overall_scores)), 4),
        "most_common_rejection_reason": (
            rejection_reason_counter.most_common(1)[0][0] if rejection_reason_counter else None
        ),
        "most_common_rule_ambiguity": (
            ambiguity_counter.most_common(1)[0][0] if ambiguity_counter else None
        ),
        "most_common_distractor_problem": (
            distractor_counter.most_common(1)[0][0] if distractor_counter else None
        ),
        "rejection_reason_counts": dict(rejection_reason_counter),
        "rule_ambiguity_counts": dict(ambiguity_counter),
        "distractor_problem_counts": dict(distractor_counter),
    }

    framework_report = {
        "summary": summary,
        "best_examples": best_examples,
        "worst_examples": worst_examples,
        "reviews": reviews,
    }

    po_review_set = {
        "count": len(product_owner_set),
        "selection_method": "top_overall_assessment_quality_with_psychometric_tiebreak",
        "minimum_target_score": 8.0,
        "puzzles": product_owner_set,
    }

    return {
        "framework_report": framework_report,
        "product_owner_review_set": po_review_set,
    }


def _generate_candidate_puzzle(
    generator: MatrixGenerator,
    seed: int,
    available_rules: list,
    candidate_rules: list,
    generation_max_attempts: int,
):
    max_attempts = max(1, generation_max_attempts)
    for attempt in range(max_attempts):
        attempt_seed = seed + (attempt * 7919)
        rng = random.Random(attempt_seed)
        selected_types = generator._select_rule_types(rng, available_rules)
        selected_rules = [generator.registry.get(rule_type) for rule_type in selected_types]
        composite = CompositeRule(selected_rules)
        raw_puzzle = composite.generate(attempt_seed)
        return generator._finalize_puzzle(raw_puzzle, selected_rules, candidate_rules)

    raise ValueError(f"Unable to generate candidate puzzle for seed={seed}")
