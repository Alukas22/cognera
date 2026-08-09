# Sprint 7.2 Architecture: Known Failure Pattern System

Status: Implementation blueprint  
Scope: Permanent failure pattern detection, rejection, regression protection, and reporting

## 1. Problem

Manual puzzle review repeatedly finds recurring failure classes that may pass isolated logical checks.

Without a permanent failure-pattern system, these defects can regress into production.

## 2. Architectural Goal

Add a first-class failure pattern layer that:

1. Codifies known quality failures as stable IDs.
2. Detects patterns deterministically during generation.
3. Rejects any candidate puzzle matching any known pattern.
4. Emits machine-readable pattern metadata for analytics.
5. Protects against regressions with one test per pattern.

## 3. Design

### 3.1 Failure Pattern Registry

A dedicated module provides:

1. Canonical pattern IDs (`FP-001` ... `FP-012`).
2. Pattern descriptors (id, name, reason).
3. Detection function returning all matched patterns for a puzzle snapshot.

### 3.2 Integration Point

The registry is invoked in final puzzle validation after existing quality/human checks.

Acceptance requires:

1. Existing strict logical gate pass.
2. Existing quality gate pass.
3. Existing expert reviewer pass.
4. Existing human reasoning validator pass.
5. No detected failure patterns.

### 3.3 Reporting

Each detected pattern is emitted to metadata and rejection events with:

1. rejection reason
2. failure pattern ID
3. frequency counters
4. trend classification

## 4. Data Structures

### 4.1 Pattern Match

A pattern match record includes:

1. `id`
2. `name`
3. `reason`

### 4.2 Metadata Extension

Puzzle quality metadata gains:

1. `failure_patterns_detected`
2. `known_failure_pattern_passed`

Report output gains:

1. `failure_pattern_report.rejection_reason`
2. `failure_pattern_report.failure_pattern_frequency`
3. `failure_pattern_report.failure_pattern_trend`

## 5. Regression Strategy

Add one explicit regression test per seeded failure pattern:

1. FP-001 Invisible Rotation
2. FP-002 Invisible Mirror Symmetry
3. FP-003 Duplicate Answer Options
4. FP-004 Explanation Does Not Explain Whole Matrix
5. FP-005 Puzzle Solvable Without Discovering Intended Rule
6. FP-006 Multiple Plausible Solutions
7. FP-007 Only One Row Or Column Contains Rule
8. FP-008 Trivial Puzzle
9. FP-009 Distractors Too Similar
10. FP-010 Distractors Too Easy
11. FP-011 Rule Only Justifies Final Cell
12. FP-012 Symmetric Shape Uses Rotation

## 6. Quality Constraints

1. Deterministic detection for the same puzzle input.
2. No generator redesign; only validation architecture extension.
3. Backward-compatible metadata extension.
4. Explicit, auditable rejection reasons.

## 7. Out of Scope

1. New puzzle rule generators.
2. UI updates.
3. API schema changes.
4. Deployment pipeline redesign.
