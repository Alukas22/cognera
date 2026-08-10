# Human Solvability Gate Specification

Status: Approved for implementation
Scope: Matrix puzzle generation and validation only
Non-goals: UI redesign, infrastructure changes, feature expansion

## 1. Objective

Cognera must reject puzzles that are internally valid but not confidently solvable by a human from visible evidence alone.

The Human Solvability Gate enforces psychometric quality by prioritizing human-discoverable reasoning over generator-valid pattern consistency.

## 2. Acceptance Policy

A puzzle is releasable only if all Human Solvability checks pass.

If any check fails:

1. The puzzle is rejected.
2. A machine-readable rejection reason is recorded.
3. Generation continues with a new candidate.

No fallback puzzle may bypass this gate.

## 3. Required Solvability Checks

The puzzle must be rejected unless all requirements below are true.

### 3.1 Dominant primary rule exists

Requirement:

1. A human can identify one dominant primary rule without access to generator internals.

Validation intent:

1. Rule effects on visible cells must show one clearly strongest signal.

### 3.2 Primary rule is visually discoverable

Requirement:

1. The primary rule must be discoverable directly from the matrix.

Validation intent:

1. The dominant signal must affect broad visible structure, not only subtle or local artifacts.

### 3.3 Secondary rules only refine

Requirement:

1. Remaining rules may verify/refine but must not be necessary before the primary rule is found.

Validation intent:

1. Secondary effects must be weaker than the primary effect.
2. Secondary rules cannot compete as alternative dominant first-step interpretations.

### 3.4 Expert explainability without hidden state

Requirement:

1. An expert can explain the complete solution step-by-step without hidden generator state.

Validation intent:

1. Full-matrix derivation must be visible in explanation and validation signals.

### 3.5 Distractors represent realistic mistakes

Requirement:

1. Every distractor must correspond to a realistic human reasoning mistake.
2. Distractors must not exist merely because they are different.

Validation intent:

1. Distractors should map to single-rule confusion patterns with explicit rationale.

### 3.6 Solver consensus likelihood

Requirement:

1. If experienced human solvers are likely to disagree on the answer, reject the puzzle.

Validation intent:

1. Ambiguity proxies must indicate strong consensus for the labeled correct option.

## 4. Integration Contract

The Human Solvability Gate is executed during generator finalization after:

1. Core puzzle construction
2. Option generation
3. Explanation generation
4. Existing perceptual/quality/human reasoning checks

The gate contributes:

1. Validation keys under `validation_results`
2. Detailed diagnostics under `generation_diagnostics`
3. A required aggregate acceptance flag `human_solvability_gate_acceptance`

## 5. Generation Behavior

Generator behavior must be aggressive:

1. Reject candidates immediately on failed solvability checks.
2. Continue sampling until all active gates pass.
3. Record rejection reason frequencies and representative rejection events.

## 6. Reporting Requirements

Validation output for at least 1,000 generated puzzles must include:

1. Rejection rate
2. Acceptance rate
3. Most common rejection reasons
4. Examples of rejected puzzles
5. Examples of accepted puzzles

The report must include both statistical summary and manual expert review notes.

## 7. Success Criterion

The gate is successful only if accepted puzzles consistently support a human "Aha" reasoning moment:

1. Clear first-step rule discovery
2. Stable solver consensus
3. Distractors that reveal meaningful human error patterns
4. Step-by-step explanation fidelity from visible matrix evidence