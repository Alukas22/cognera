# Sprint 7.2 Architecture: Human Reasoning Validator

Status: Approved implementation blueprint  
Scope: Final validation stage for matrix puzzle acceptance

## 1. Problem Definition

Current validation catches many logical failures, but some puzzles still pass automation while being rejected by human experts.

Gap categories:

1. Rules that justify only the missing cell, not all visible cells.
2. Ambiguous reasoning where multiple interpretations remain plausible.
3. Weak rule coverage where a rule affects too little visible evidence.
4. Explanations that are structurally present but incomplete for rows, columns, or distractors.

## 2. Architecture Overview

Add a final gate: `HumanReasoningValidator`.

Pipeline order:

1. Structural checks
2. Logical checks
3. Perceptual checks
4. Existing quality scoring
5. Existing expert reviewer
6. Human reasoning validator (new final gate)

Acceptance decision MUST require the new gate to pass.

## 3. Data Structures

### 3.1 Human Reasoning Review Object

Internal review payload includes:

1. `quality_score`
2. `rule_coverage`
3. `reasoning_depth`
4. `ambiguity_score`
5. `perceptual_score`
6. `explanation_score`
7. `rejection_reasons`

### 3.2 Validation Checks

Validator emits booleans for:

1. Full matrix reconstructability from rule set.
2. All visible cells derivable.
3. Unique rule-set interpretation.
4. No isolated one-cell rule effects.
5. Human reasoning unambiguous.
6. No hidden assumptions.
7. Rules visible before seeing answer options.
8. Every row participates.
9. Every column participates.
10. Explanation covers rows.
11. Explanation covers columns.
12. Explanation justifies correct answer.
13. Explanation rejects each distractor.
14. Explanation is derived from rule objects.

## 4. Algorithms

### 4.1 Full Matrix Validation

1. Reconstruct expected puzzle from selected rule objects and generation seed.
2. Compare each of the eight visible cells with reconstructed cells.
3. Reject on any mismatch.
4. Detect alternative plausible rule sets by testing other rule combinations against completed matrix.

### 4.2 Human Reasoning Validation

1. Estimate ambiguity using alternative rule-set matches and blind-solver confidence.
2. Reject if ambiguity remains high.
3. Reject if reasoning depends on answer-only signal.
4. Reject if plausible interpretation multiplicity is detected.

### 4.3 Rule Coverage Validation

1. For each active rule, compare full reconstruction with reconstruction omitting that rule.
2. Count visible-cell differences attributable to that rule.
3. Require at least two affected visible cells per active rule.
4. Require participation signal in every row and every column.

### 4.4 Explanation Validation

1. Enforce row-level explanation markers for all rows.
2. Enforce column-level explanation markers for all columns.
3. Require explicit correct-answer justification.
4. Require explicit rejection statement for each distractor option.
5. Require explanation references to rule objects (`Rule n` and rule values).

## 5. Quality Constraints

1. Deterministic outcomes for same seed and rule set.
2. No generator redesign in Sprint 7.2.
3. Validation logic must be modular and testable.
4. Rejections must provide machine-readable reasons.
5. Existing quality metadata must be extended, not broken.

## 6. Regression Strategy

Add regression tests for previously observed human-reject patterns:

1. Invisible rotations
2. Symmetric mirrors
3. Duplicate answers
4. Explanations fitting only final cell
5. Trivial puzzles
6. Puzzles requiring guessing

All such cases must fail the final gate.

## 7. Integration Plan

1. Add `human_reasoning_validator.py` in matrix module.
2. Integrate validator in `MatrixGenerator._finalize_puzzle`.
3. Merge validator checks into `validation_results`.
4. Persist review object in puzzle metadata.
5. Add unit and regression tests.

## 8. Out of Scope

1. New rule generators.
2. UI changes.
3. API contract changes.
4. Deployment automation changes.
