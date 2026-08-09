# Cognera Engineering Principles

Version: Sprint 7.1  
Status: Permanent Engineering Constitution  
Scope: All product, research, architecture, implementation, validation, and release workflows

## 1. Vision

Cognera aims to become the world's leading cognitive assessment platform.

The project mission is to deliver psychometrically rigorous matrix reasoning systems that are trustworthy, explainable, and production-grade.

## 2. Engineering Philosophy

Cognera engineering is principle-driven, not speed-driven.

Human reasoning quality is always more important than implementation speed.

All work must prioritize:

1. Psychometric validity
2. Clear reasoning semantics
3. Reliable user interpretation
4. Long-term maintainability
5. Production reliability

## 3. Architecture First

Architecture must be defined before implementation.

For every non-trivial feature:

1. Create or update a design document in `docs/`.
2. Define the intended architecture and interfaces.
3. Identify quality risks and validation strategy.
4. Obtain architectural alignment before coding.

No implementation should begin before architecture is documented.

## 4. Documentation Before Code

Every sprint follows this mandatory sequence:

1. Define the problem.
2. Design the architecture.
3. Describe data structures.
4. Describe algorithms.
5. Describe quality constraints.
6. Implement.
7. Test.
8. Deploy.

Every sprint starts with specification, then architecture, then implementation.

## 5. Puzzle Quality Standards

Cognera is not a demo project.

Every released puzzle must satisfy these standards:

1. Exactly one logically derivable solution exists.
2. Duplicate answer options are forbidden.
3. Distractors are intentionally designed.
4. Random or low-signal distractors are forbidden.
5. Puzzle behavior is rule-grounded and internally consistent.

## 6. Human Reasoning Standards

Puzzles must evaluate reasoning, not guessing.

Human reasoning constraints:

1. Rules must be understandable to trained human solvers.
2. Visible evidence in the matrix must support every rule.
3. Solvability must not depend on hidden assumptions.
4. Reasoning pathways should be explainable in plain language.

## 7. Validation Rules

A puzzle may be released only after passing all required validation gates.

Mandatory gates:

1. Structural validation
2. Logical validation
3. Human-expert validation

Validation outcomes are binary:

1. Pass all gates -> eligible for release
2. Fail any gate -> reject

## 8. Explainability Requirements

Explainability is mandatory for all generated puzzles.

Each puzzle explanation must:

1. State each rule separately.
2. Reconstruct the matrix logic end to end.
3. Justify the correct answer.
4. Explain why each distractor is incorrect.
5. Avoid vague or non-operational wording.

## 9. Code Quality Requirements

Code must support correctness, auditability, and evolution.

Required quality characteristics:

1. Clear module boundaries and explicit responsibilities.
2. Deterministic behavior for generation and validation logic.
3. Comprehensive automated tests for critical reasoning paths.
4. Backward-compatible evolution of interfaces where feasible.
5. Documentation updates bundled with behavior changes.
6. No shortcuts that weaken puzzle validity guarantees.

## 10. Long-Term Design Principles

Cognera must be optimized for long-horizon quality.

Primary optimization targets:

1. Maintainability
2. Psychometric validity
3. Scalability
4. Extensibility
5. Production quality

Long-term engineering rule:

If a requested implementation introduces technical debt or violates Cognera architecture, stop implementation, explain the risk, and propose an architecturally sound alternative before coding.

## Enforcement

This document is mandatory policy for the Cognera project.

All future work must conform unless explicitly superseded by a newer approved constitutional revision in `docs/`.
