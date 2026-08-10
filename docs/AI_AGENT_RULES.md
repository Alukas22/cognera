# AI Agent Rules

## Purpose

This document defines mandatory governance rules for all AI agents that analyze, generate, or modify assets in the Cognera repository. Its purpose is to ensure architectural integrity, puzzle-quality standards, engineering consistency, test reliability, and safe operational behavior across all contributor workflows.

The rules in this document are normative. The keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are used in their standard requirements sense.

## Guiding Principles

1. Architecture first: Non-trivial work MUST begin from architecture intent, not ad hoc code changes.
2. Documentation before implementation: Design rationale and constraints MUST be recorded before or with implementation.
3. Puzzle quality first: Human-reasonable, explainable, and visually meaningful puzzle behavior takes precedence over raw generation speed.
4. Deterministic reasoning over opaque behavior: Rule-driven and inspectable logic is preferred over non-explainable transformations.
5. Minimal, reversible change sets: Changes SHOULD be narrow, auditable, and easy to roll back.
6. Safety and non-destructiveness: Agents MUST avoid destructive actions unless explicitly requested and approved.
7. Long-term maintainability: Agents MUST optimize for extensibility, clarity, and operational reliability.

## Architecture Authority

1. Architectural authority resides in the repository architecture documentation and accepted ADRs.
2. When implementation conflicts with architecture documents, architecture documents are the source of truth unless superseded by an approved ADR.
3. AI agents MUST treat the following as authoritative inputs:
	- docs architecture documents under docs/architecture
	- accepted records under docs/adr
	- engineering principles and standards under docs/
4. Agents MUST NOT silently introduce behavior that violates established boundaries, invariants, or domain constraints.
5. Any deliberate architecture deviation MUST be explicitly documented through a new or updated ADR before merge.

## Coding Rules

1. Agents MUST make the smallest viable change that satisfies requirements.
2. Agents MUST preserve public interfaces unless change is explicitly requested and documented.
3. Agents MUST avoid unrelated refactors in the same change set.
4. Agents SHOULD add concise comments only where logic is non-obvious.
5. Agents MUST follow existing project language, style, and module conventions.
6. Agents MUST NOT introduce hidden transformations, implicit puzzle state mutation, or non-deterministic side effects that weaken explainability.
7. Agents MUST prefer explicit domain models and validation over loosely structured ad hoc data handling.

## Documentation Rules

1. For non-trivial changes, agents MUST create or update relevant documentation in docs/.
2. Documentation MUST describe intent, constraints, assumptions, and impact.
3. If behavior changes, docs MUST reflect the new behavior in the same pull request.
4. ADRs MUST be used for architectural decisions, trade-offs, and boundary changes.
5. Documentation SHOULD be specific, testable, and free of ambiguous language.

## Testing Rules

1. Every behavior change MUST be validated by relevant automated tests.
2. New logic MUST include tests for success paths, edge cases, and known failure patterns.
3. Regressions MUST be reproduced with a test before or alongside a fix whenever practical.
4. Agents MUST NOT claim successful validation without running or clearly reporting unavailable test execution.
5. Tests SHOULD preserve determinism and avoid flaky timing-dependent behavior.

## Commit Rules

1. Commits MUST be focused and logically atomic.
2. Commit messages MUST be descriptive, imperative, and scoped to the actual change.
3. Commits MUST NOT include unrelated file modifications.
4. Generated artifacts or local outputs MUST NOT be committed unless explicitly required.
5. If a commit contains architectural impact, the message SHOULD reference the associated ADR identifier.

## Pull Request Rules

1. Pull requests MUST explain what changed, why it changed, and how it was validated.
2. Pull requests MUST list architecture or documentation impacts.
3. Pull requests with architecture impact MUST reference corresponding ADRs.
4. Pull requests SHOULD be scoped to a coherent objective and avoid mixed concerns.
5. Review comments related to correctness, architecture, or safety MUST be resolved before merge.

## Safety Rules

1. Agents MUST avoid destructive repository operations unless explicitly directed.
2. Agents MUST NOT expose secrets, credentials, or sensitive data.
3. Agents MUST report uncertainty, assumptions, and unresolved risks.
4. Agents MUST avoid unsafe automation patterns that bypass review gates.
5. Agents MUST prioritize correctness and domain integrity over speed.

## Rules For Modifying Architecture

1. Any change affecting module boundaries, data flow, domain invariants, or system responsibilities is an architecture change.
2. Architecture changes MUST be preceded by one of:
	- a new ADR, or
	- an update to an existing ADR with explicit supersession rationale.
3. The architecture update MUST include problem statement, alternatives considered, decision, consequences, and migration impact.
4. Implementation MUST remain aligned with the approved architecture record.
5. If architecture and implementation diverge during execution, work MUST pause until the divergence is resolved through documentation and approval.

## Rules For Adding New Features

1. New features MUST map to documented user value and domain intent.
2. Non-trivial features MUST include design documentation before substantial code changes.
3. Feature design MUST identify:
	- affected components
	- data contracts
	- validation approach
	- failure modes and mitigation
4. Features MUST include tests and documentation updates in the same delivery cycle.
5. Feature additions MUST NOT degrade puzzle explainability, visual coherence, or reasoning quality constraints.

## Rules For Handling Conflicts Between Implementation And Architecture

1. On detecting a conflict, agents MUST explicitly flag the conflict and stop silent progression.
2. Agents MUST classify the conflict as one of:
	- implementation bug relative to architecture
	- architecture obsolete relative to validated product needs
	- ambiguous specification requiring clarification
3. Resolution path:
	- if implementation is wrong, correct implementation and add regression coverage
	- if architecture is outdated, propose ADR change before implementation proceeds
	- if ambiguous, request clarifying decision and document assumption boundaries
4. Agents MUST NOT merge unresolved architecture-implementation conflicts.

## Definition Of Done

A task is Done only when all of the following are true:

1. Requirements are fully implemented within agreed scope.
2. Architecture alignment is verified or formally updated via ADR.
3. Relevant documentation is updated.
4. Automated tests are added or updated and pass in the target environment, or limitations are explicitly reported.
5. No known critical regressions remain.
6. Changes are reviewable, focused, and traceable via commit and pull request metadata.
7. Safety and quality constraints in this document are satisfied.

## Future AI Agent Compatibility

1. Rules in this document are tool-agnostic and apply to current and future AI agents.
2. Future agents MUST support:
	- architecture-aware planning
	- deterministic change tracking
	- explicit assumption reporting
	- test and documentation co-evolution
3. Repository governance artifacts SHOULD remain machine-readable where practical to enable automated policy enforcement.
4. When introducing new agent platforms, maintainers SHOULD validate parity against these rules before enabling write permissions.
5. If future automation introduces stronger controls, this document SHOULD be revised to keep governance explicit and current.

## Scope

These rules apply to all AI-assisted activities in this repository, including analysis, planning, documentation, code modifications, test updates, and pull request preparation.

Any narrower task-specific instructions MAY add constraints but MUST NOT weaken this baseline governance framework.
