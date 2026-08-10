"""Tests for internal puzzle review framework."""

from backend.app.matrix.puzzle_review_framework import run_puzzle_review_framework


def test_review_framework_generates_requested_reviews() -> None:
    result = run_puzzle_review_framework(
        target_reviews=6,
        start_seed=120_000,
        generation_max_attempts=96,
        max_seed_attempts=1_200,
    )

    framework_report = result["framework_report"]
    summary = framework_report["summary"]

    assert summary["target_reviews"] == 6
    assert summary["reviews_generated"] == 6
    assert summary["accepted_count"] + summary["rejected_count"] == 6
    assert isinstance(framework_report["reviews"], list)
    assert len(framework_report["reviews"]) == 6


def test_review_framework_scores_are_bounded() -> None:
    result = run_puzzle_review_framework(
        target_reviews=4,
        start_seed=130_000,
        generation_max_attempts=96,
        max_seed_attempts=1_000,
    )
    review = result["framework_report"]["reviews"][0]

    assert review["unique_solution"] in {"Pass", "Fail"}
    assert 1.0 <= review["human_solvability"] <= 10.0
    assert 1.0 <= review["rule_clarity"] <= 10.0
    assert 1.0 <= review["visual_clarity"] <= 10.0
    assert 1.0 <= review["distractor_quality"] <= 10.0
    assert 1.0 <= review["raven_similarity"] <= 10.0
    assert 1.0 <= review["overall_assessment_quality"] <= 10.0

    po_set = result["product_owner_review_set"]
    assert po_set["count"] <= 100
    assert isinstance(po_set["puzzles"], list)
