# Human Solvability Gate Validation Report

## Scope

This report documents the first large-scale validation run after integrating the Human Solvability Gate into matrix generation acceptance.

- Goal: aggressively reject puzzles that are unlikely to be solvable by human reasoning.
- Constraint: no product/UI/infra feature changes.
- Sample target: evaluate at least 1000 seeds.

## Run Configuration

- Command: `python -m backend.app.matrix.quality_tools validate --samples 1000 --start-seed 70000 --generation-max-attempts 24 --output backend/reports/puzzle_quality_report_human_solvability_gate.json --top-output backend/reports/top_100_quality_puzzles_human_solvability_gate.json`
- Samples requested: 1000
- Start seed: 70000
- Per-seed generation attempt cap: 24

## Statistical Results

Source: `backend/reports/puzzle_quality_report_human_solvability_gate.json`

- samples_requested: 1000
- samples_generated: 314
- generation_failures: 686
- candidate_puzzles_evaluated: 3698
- acceptance_rate: 0.0849
- rejection_rate: 0.9151
- average_generation_attempts: 11.7771

Interpretation:

- The gate stack is currently very strict: 91.51% of candidate puzzles are rejected.
- This aligns with the objective of aggressive unsolvable-puzzle filtering.
- Throughput is reduced significantly; most seeds do not produce an accepted puzzle within 24 attempts.

## Most Common Rejection Reasons

Top reasons from `most_common_rejection_reasons`:

1. human_solvability_gate_acceptance: 5824
2. human_solvability_expert_step_by_step_explainable: 5345
3. expert_reviewer_acceptance: 5313
4. assessment_distractors_not_near_duplicate: 5283
5. human_solvability_primary_rule_dominant: 4661
6. human_solvability_primary_rule_visually_discoverable: 4647
7. perceptual_validation_passed: 3884
8. quality_engine_acceptance: 3826
9. assessment_readability_elegant_not_confusing: 3317
10. assessment_dominant_reasoning_blind_solver_agrees: 2973

Interpretation:

- The dominant rejection cluster is solvability/explainability (human_solvability_* + expert_reviewer).
- Distractor quality remains a major bottleneck.
- Perceptual and reasoning-dominance checks still eliminate many candidates before final acceptance.

## Accepted Puzzle Examples (Manual Spot Check)

Accepted examples (from `logical_validation_report.accepted_puzzle_examples`):

1. seed 70000, rules [size, count, rotation, position], quality_score 0.9250, difficulty Expert
2. seed 70002, rules [shape, rotation, mirror, position], quality_score 0.9090, difficulty Expert
3. seed 70003, rules [size, rotation, position, mirror], quality_score 0.9565, difficulty Expert
4. seed 70007, rules [size, shape, rotation, count], quality_score 0.9460, difficulty Expert
5. seed 70009, rules [rotation, count, position, mirror], quality_score 0.9255, difficulty Expert

Manual review outcome:

- Accepted samples consistently show all six human_solvability checks marked true.
- Primary rule appears visually dominant while secondary rules refine, not replace, the reasoning path.
- Distractors are plausible and generally map to common single-step errors.

## Rejected Puzzle Examples (Manual Spot Check)

Rejected examples (from `logical_validation_report.rejected_puzzle_examples`):

1. seed 70000, rules [count, rotation, shape, position], violated perceptual_validation_passed
2. seed 77919, rules [position, rotation, mirror, shape], violated assessment_readability_elegant_not_confusing
3. seed 85838, rules [mirror, rotation, count], violated assessment_readability_elegant_not_confusing

Observed failed validation flags in these rejected candidates include:

- perceptual_validation_passed
- assessment_distractors_not_near_duplicate
- human_solvability_primary_rule_dominant
- human_solvability_primary_rule_visually_discoverable
- human_solvability_expert_step_by_step_explainable
- assessment_dominant_reasoning_blind_solver_agrees

Manual review outcome:

- Rejected candidates frequently combine weak dominant-pattern salience with ambiguous distractor sets.
- The rejection pattern is aligned with the gate objective: prevent puzzles where a human solver can reasonably branch into multiple interpretations.

## Deliverables Produced

- Statistical report JSON: `backend/reports/puzzle_quality_report_human_solvability_gate.json`
- Top accepted set JSON: `backend/reports/top_100_quality_puzzles_human_solvability_gate.json`

## Conclusion

The Human Solvability Gate is now integrated and materially increases filtering pressure toward human-solvable puzzles. The first 1000-seed run demonstrates aggressive rejection behavior and provides explicit diagnostics, rejection reasons, and accepted/rejected examples for continuous tuning.