# COGNERA Puzzle Standard

Version: Sprint 7.0  
Status: Canonical Specification  
Applies to: Puzzle generation, validation, explanations, and quality gates

## 1. Purpose

Cognera exists to generate matrix reasoning puzzles that measure human reasoning quality, not random pattern completion.

The target quality bar is psychometric validity comparable to professional cognitive ability assessments.

This standard defines required constraints for puzzle construction, answer options, explanations, and acceptance gates.

## 2. Core Design Principles

All accepted Cognera puzzles MUST satisfy the following principles:

1. Every puzzle measures reasoning.
2. No guessing is required for a trained solver.
3. No ambiguity is permitted.
4. Exactly one logically valid solution exists.
5. Reasoning must be human-understandable.
6. Visual clarity takes priority over decorative complexity.
7. Explanations must reconstruct the entire puzzle, not only the final answer.

## 3. Puzzle Validity Requirements

A puzzle is valid only if all requirements below are true:

1. Exactly one answer option is correct.
2. Every distractor is logically incorrect under the true rule set.
3. All visible matrix cells are necessary.
4. No redundant information exists.
5. Every rule contributes unique information.
6. Removing any visible cell reduces solvability.

If any single requirement fails, the puzzle MUST be rejected.

## 4. Rule Requirements

Every rule used in a puzzle MUST:

1. Generate the complete matrix behavior (not only one position).
2. Explain every visible cell.
3. Explain the missing target cell.
4. Be deterministic.
5. Be internally consistent.

Rules that only justify the final answer while failing to explain visible cells are forbidden and MUST be rejected.

## 5. Visual Requirements

Visual transformations are valid only when clearly observable by a human solver.

### 5.1 Rotation Constraints

Rotation MAY be used only when visually observable.

Rotation MUST NOT be used for:

1. Circles.
2. Squares rotated by 90° or 180°.
3. Any symmetric figure where rotation is visually indistinguishable.

### 5.2 Reflection Constraints

Mirror operations MAY be used only when reflection is visually detectable in the rendered figures.

### 5.3 Color and Size Constraints

1. Color changes MUST be clearly distinguishable.
2. Size differences MUST be visually obvious.
3. Tiny visual differences that require pixel-level inspection are forbidden.
4. Any transformation that is not reliably perceivable by typical users MUST be rejected.

## 6. Distractor Requirements

Distractors MUST:

1. Be plausible under common but incorrect reasoning paths.
2. Reflect realistic solver mistakes.
3. Never duplicate each other.
4. Never duplicate the correct answer.
5. Differ by meaningful logical properties, not superficial noise.

Random distractors are forbidden.

## 7. Explanation Requirements

Every puzzle explanation MUST:

1. Describe each rule separately.
2. Reconstruct the complete matrix from the rule set.
3. Explain why each distractor is wrong.
4. Use concrete, non-vague language.

### 7.1 Language Quality

Vague explanation language is forbidden.

Bad example:

> "Mirror symmetry."

Good example:

> Rule 1: Each row mirrors around the central column.  
> Rule 2: Shape changes follow a fixed sequence from left to right.  
> Rule 3: Rotation increases by 90° per step.

## 8. Human Expert Validation

Human Expert Rule:

A puzzle MUST pass the following thought experiment:

A trained psychometric expert should be able to derive every visible cell from the stated rule set without seeing answer options.

If this cannot be done, REJECT the puzzle.

## 9. Quality Checklist

A puzzle passes only when all items are checked:

- ☐ Unique solution
- ☐ No duplicated answers
- ☐ All rules visible in the matrix
- ☐ All rules necessary (no redundant rules)
- ☐ Every visible cell justified by rules
- ☐ Removing a visible cell reduces solvability
- ☐ Visual transformations are observable
- ☐ Distractors are plausible and logically distinct
- ☐ Explanation reconstructs the entire matrix
- ☐ Explanation rejects each distractor explicitly
- ☐ Human expert validation passes

## 10. Future Extensions

This section reserves future-standard rule families and reasoning layers.

### 10.1 Reserved Rule Types

1. Color
2. Number
3. Position
4. Count
5. Rotation
6. Reflection
7. Boolean logic
8. XOR
9. AND
10. OR
11. Progression
12. Nested rules
13. Multi-dimensional reasoning
14. Analogical reasoning

### 10.2 Extension Policy

Future rule families MUST be added without weakening Sections 2 through 9.

Any new rule type MUST preserve:

1. Unique solvability.
2. Full rule explainability.
3. Human-observable transformations.
4. Psychometric intent.

## 11. Compliance Scope

This document is the canonical puzzle quality specification for Cognera Sprint 7.0.

All generation, validation, explanation, and quality-gate logic MUST conform to this standard.

No exceptions are allowed without an explicit future revision of this document.
