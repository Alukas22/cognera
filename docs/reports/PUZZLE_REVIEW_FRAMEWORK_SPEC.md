# Puzzle Review Framework Specification

## Objective

Create an internal review framework that evaluates whether generated Cognera puzzles are assessment-quality enough for product release decisions.

This framework is analysis-only. It does not change UI, infrastructure, or explanation formatting.

## Scope

Given generated puzzles, produce:

1. A structured review per puzzle.
2. Aggregate quality statistics.
3. A Product Owner Review Set containing the 100 highest-quality puzzles.

## Input

- Puzzle generator: `MatrixGenerator(RuleRegistry())`.
- Target review count: at least 1000 generated puzzles.
- Generation strategy: deterministic seeded generation with retry support.

## Per-Puzzle Review Contract

Each review record must contain:

- `seed`
- `rules`
- `unique_solution`: `"Pass" | "Fail"`
- `human_solvability`: score 1-10
- `rule_clarity`: score 1-10
- `visual_clarity`: score 1-10
- `distractor_quality`: score 1-10
- `raven_similarity`: score 1-10
- `overall_assessment_quality`: score 1-10
- `accepted_for_product`: boolean (`overall_assessment_quality >= 8` and unique solution pass)
- `rejection_reason` when rejected
- `rule_ambiguity_tag` (if present)
- `distractor_problem_tag` (if present)
- `validation_snapshot`

## Scoring Criteria

### 1) Unique solution

Pass if all of the following are true:

- exactly one correct option
- puzzle unambiguous
- human reasoning unambiguous
- unique rule-set interpretation

Else Fail.

### 2) Human solvability (1-10)

Estimate from:

- human solvability gate consensus checks
- explainability and hidden-assumption checks
- candidate alternative rule-set pressure

### 3) Rule clarity (1-10)

Estimate from:

- dominant primary-rule checks
- rule discoverability checks
- ambiguity diagnostics and alternative rule sets

### 4) Visual clarity (1-10)

Estimate from:

- perceptual validation
- readability checks
- visual balance checks

### 5) Distractor quality (1-10)

Estimate from:

- exactly-one-rule violation checks
- near-duplicate checks
- plausibility checks
- realistic mistake checks
- expert distractor-quality score

### 6) Raven similarity (1-10)

Estimate from:

- psychometric quality score
- reasoning depth requirements
- non-triviality and full-matrix observation checks
- rule coherence constraints

### 7) Overall assessment quality (1-10)

Weighted aggregate of criteria (2)-(6), with unique-solution fail penalty.

Reject if below 8.

## Aggregate Outputs

Framework must compute:

- average overall score
- median overall score
- worst examples
- best examples
- most common rejection reason
- most common rule ambiguity
- most common distractor problem

## Product Owner Review Set

Select the top 100 by `overall_assessment_quality` (tie-breakers: psychometric score, quality score).

Output must include puzzle payload and review metadata for manual PO inspection.

## Artifacts

- Full framework output JSON (`1000+` structured reviews + aggregate stats).
- Product Owner top-100 JSON.
- Summary markdown report for milestone review.
