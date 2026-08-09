"""Tests for puzzle quality CLI tooling."""

from pathlib import Path

from backend.app.matrix.quality_tools import export_review_package, run_statistical_validation


def test_statistical_validation_report_shape() -> None:
    report = run_statistical_validation(samples=40, start_seed=20_000)

    assert report["samples_requested"] == 40
    assert report["samples_generated"] + report["generation_failures"] == 40
    assert 0.0 <= report["validation_pass_rate"] <= 1.0
    assert 0.0 <= report["unique_option_rate"] <= 1.0
    assert 0.0 <= report["unique_distractor_rate"] <= 1.0
    assert 0.0 <= report["explanation_generated_rate"] <= 1.0
    assert set(report["difficulty_distribution"]).issubset({"Easy", "Medium", "Hard", "Expert"})


def test_export_review_package_writes_expected_file(tmp_path: Path) -> None:
    output = tmp_path / "review.json"
    summary = export_review_package(count=5, output=output, seed=2026)

    assert summary["count"] == 5
    assert output.exists()

    content = output.read_text(encoding="utf-8")
    assert '"puzzles"' in content
    assert '"quality_score"' in content
    assert '"validation_status"' in content
