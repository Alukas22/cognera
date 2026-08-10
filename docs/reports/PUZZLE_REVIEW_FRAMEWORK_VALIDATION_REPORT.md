# Puzzle Review Framework Validation Report

## Scope

This milestone runs an internal puzzle assessment framework focused only on puzzle quality validation.

Excluded by design:

- No UI changes
- No explanation-format improvements
- No infrastructure work

## Run Configuration

- Command: `python -m backend.app.matrix.quality_tools review-framework --count 1000 --start-seed 70000 --generation-max-attempts 1 --max-seed-attempts 5000 --output backend/reports/puzzle_review_framework_report.json --po-output backend/reports/product_owner_review_set.json`
- Target reviews: 1000 generated puzzles
- Start seed: 70000

## Structured Review Criteria

Each puzzle review includes:

1. Unique solution: Pass/Fail
2. Human solvability: 1-10
3. Rule clarity: 1-10
4. Visual clarity: 1-10
5. Distractor quality: 1-10
6. Raven similarity: 1-10
7. Overall assessment quality: 1-10

Acceptance rule:

- Reject all puzzles with overall score < 8.0
- Reject if unique solution fails

## Aggregate Results

Source: `backend/reports/puzzle_review_framework_report.json`

- reviews_generated: 1000
- accepted_count: 237
- rejected_count: 763
- acceptance_rate: 0.237
- average_score: 7.5369
- median_score: 7.59
- most_common_rejection_reason: low_rule_clarity
- most_common_rule_ambiguity: no_dominant_primary_rule
- most_common_distractor_problem: near_duplicate_distractors

### Rejection Distribution

- low_rule_clarity: 464
- low_visual_clarity: 170
- low_human_solvability: 129

### Rule Ambiguity Distribution

- no_dominant_primary_rule: 770
- weak_gap_between_primary_and_alternatives: 49

### Distractor Problem Distribution

- near_duplicate_distractors: 828

## Best Examples

Top examples (by overall assessment quality):

1. seed 70644, overall 9.54
2. seed 70846, overall 9.51
3. seed 70646, overall 9.50
4. seed 70764, overall 9.50
5. seed 70918, overall 9.50

## Worst Examples

Lowest examples:

1. seed 70352, overall 5.80, rejection low_visual_clarity
2. seed 70716, overall 5.80, rejection low_visual_clarity
3. seed 70001, overall 5.95, rejection low_human_solvability
4. seed 70060, overall 5.95, rejection low_human_solvability
5. seed 70604, overall 5.95, rejection low_human_solvability

## Product Owner Review Set

Source: `backend/reports/product_owner_review_set.json`

- count: 100
- selection: highest overall assessment quality, psychometric quality tie-break

This set represents the best currently generated puzzles under the implemented internal review framework and current generator behavior.
