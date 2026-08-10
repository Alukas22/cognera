# Epic 3 Implementation Plan: Reasoning Engine

Date: 2026-08-10
Source baseline: docs/reports/REASONING_ENGINE_COMPLIANCE.md
Review applied: docs/reports/EPIC_3_ARCHITECT_REVIEW.md
Scope: Convert identified architecture gaps into an independently implementable backlog with explicit phase gates, clarified dependencies, and lower-risk execution slices.

## Planning assumptions

1. This backlog targets architecture alignment, not rule-family expansion.
2. No generator redesign outside required orchestration, contracts, and traceability boundaries.
3. Existing behavior should remain deterministic for identical seeds.
4. New metadata is backward-compatible where practical and explicitly versioned where necessary.
5. Architecture boundary changes require ADR alignment before runtime rollout.

## Priority model

- P0: Critical architecture contract blocker
- P1: Required for Epic 3 acceptance
- P2: Important hardening and traceability

## Risk model

- Low: Localized change, low blast radius
- Medium: Multi-module coordination, moderate regression risk
- High: Core contract/pipeline touchpoints, high regression risk

## Roadmap adjustments applied from architect review

1. Introduce Phase 0 for architecture stabilization before pipeline implementation.
2. Keep RE-001 and RE-002 as separate tracking IDs, but execute them as one contract-model stream.
3. Split RE-005 into RE-005A and RE-005B.
4. Split RE-009 into RE-009A and RE-009B, with RE-009A moved earlier as a smoke suite.
5. Split RE-013 into RE-013A and RE-013B.
6. Execute RE-006 and RE-007 as one gate-integration stream.
7. Add explicit backlog items RE-015 through RE-018 for migration, telemetry, performance, and rollout governance.
8. Apply dependency corrections for RE-010, RE-011, RE-012, and RE-014.

---

## Phase 0: Architecture Stabilization

Goal: Stabilize the canonical puzzle contract, metadata schema, compatibility strategy, and contract guardrails before orchestration work begins.

Execution streams:

1. Contract-model stream: RE-001 and RE-002 execute together while retaining separate tracking IDs.
2. Metadata-schema stream: RE-003 establishes the versioned quality metadata contract consumed by downstream validators and reporters.
3. Guardrail and migration stream: RE-004 and RE-015 lock the transition path and prevent silent drift.

Phase exit criteria:

1. Canonical MatrixPuzzle contract is defined, documented, and covered by guardrail tests.
2. Required model primitives and enums are available with stable typing and serialization behavior.
3. quality_metadata and validation_results have a versioned schema with deterministic key expectations.
4. Compatibility and migration strategy is documented and test-enforced for legacy consumers.

### RE-001
- ID: RE-001
- Title: Canonical MatrixPuzzle Contract Expansion
- Description: Expand MatrixPuzzle into the canonical validated puzzle contract consumed by generators, validators, reviewers, quality tools, and API serialization. Include required fields currently assumed by downstream modules.
- Architecture reference:
  - docs/architecture/SYSTEM_ARCHITECTURE.md (validated puzzle payload with explanation and metadata)
  - docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md (integration and metadata persistence)
- Dependencies: None
- Output artifact:
  - Canonical MatrixPuzzle contract table covering required fields, defaults, and legacy compatibility notes
- Files expected to change:
  - backend/app/matrix/models.py
  - backend/tests/test_matrix_models.py
- Required tests:
  - Contract test: complete MatrixPuzzle field presence and defaults
  - Backward-compatibility test for legacy generation attributes
- Acceptance criteria:
  - MatrixPuzzle declares and validates fields required by matrix modules: options, correct_index, explanation, missing_position, quality_score, quality_metadata, difficulty, difficulty_label, difficulty_profile
  - Existing tests compile against unified contract
  - New contract tests pass
- Estimated effort: Large
- Risk: High
- Priority: P0

### RE-002
- ID: RE-002
- Title: Add Missing Model Classes and Enums
- Description: Define missing model-level primitives used across matrix pipeline, including AnswerOption, Distractor, DistractorReason, and DifficultyProfile with strict typing and serialization helpers.
- Architecture reference:
  - docs/architecture/SYSTEM_ARCHITECTURE.md (option validity and quality layers)
  - docs/COGNERA_PUZZLE_STANDARD.md (distractor quality and explanation requirements)
- Dependencies:
  - RE-001
- Files expected to change:
  - backend/app/matrix/models.py
  - backend/app/matrix/__init__.py
  - backend/tests/test_matrix_models.py
- Required tests:
  - Unit tests for object construction and validation rules
  - Enum stability tests for DistractorReason values
  - DifficultyProfile bounds tests
- Acceptance criteria:
  - All current imports from models resolve without ad hoc patching
  - New classes are immutable and typed consistently with existing model style
  - Tests confirm required fields used by validators and reviewers are available
- Estimated effort: Medium
- Risk: Medium
- Priority: P0

### RE-003
- ID: RE-003
- Title: Define Quality Metadata Schema Interface
- Description: Introduce typed schema for quality_metadata and validation_results so all quality gates publish to one stable structure.
- Architecture reference:
  - docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md (merge checks into validation_results)
  - docs/SPRINT_7_2_KNOWN_FAILURE_PATTERN_SYSTEM_ARCHITECTURE.md (metadata extension)
- Dependencies:
  - RE-001
  - RE-002
- Output artifact:
  - Versioned quality_metadata schema document and deterministic validation_results key registry
- Files expected to change:
  - backend/app/matrix/models.py
  - backend/app/matrix/quality_engine.py
  - backend/app/matrix/expert_reviewer.py
  - backend/app/matrix/human_reasoning_validator.py
  - backend/app/matrix/failure_patterns.py
- Required tests:
  - Metadata schema validation tests
  - Serialization key stability tests
- Acceptance criteria:
  - quality_metadata has explicit typed structure for validation outcomes, reviewer scores, human reasoning review, failure patterns, and diagnostics
  - validation_results key set is deterministic and documented in tests
- Estimated effort: Medium
- Risk: Medium
- Priority: P0

### RE-004
- ID: RE-004
- Title: Establish Contract Guardrail Test Suite
- Description: Add dedicated tests that fail fast when any module relies on undeclared puzzle attributes or metadata keys.
- Architecture reference:
  - docs/AI_AGENT_RULES.md (testing discipline and regression prevention)
  - docs/architecture/SYSTEM_ARCHITECTURE.md (reliability through layered validation)
- Dependencies:
  - RE-001
  - RE-002
  - RE-003
- Files expected to change:
  - backend/tests/test_matrix_models.py
  - backend/tests/test_quality_tools.py
  - backend/tests/test_rule_engine.py
- Required tests:
  - Interface contract tests for generator output object shape
  - Metadata key continuity tests used by quality_tools
- Acceptance criteria:
  - Any contract drift in core puzzle or metadata shape causes clear test failure
  - Contract tests run in default backend test workflow
- Estimated effort: Small
- Risk: Low
- Priority: P1

### RE-015
- ID: RE-015
- Title: Contract Migration and Compatibility Layer
- Description: Define transition strategy for expanded MatrixPuzzle contract, including compatibility adapters and deprecation timeline.
- Architecture reference:
  - docs/AI_AGENT_RULES.md
  - docs/architecture/SYSTEM_ARCHITECTURE.md
- Dependencies:
  - RE-001
  - RE-002
- Files expected to change:
  - backend/app/matrix/models.py
  - backend/app/matrix/rule_engine.py
  - backend/tests/test_matrix_models.py
  - backend/tests/test_matrix_demo_endpoint.py
- Required tests:
  - Compatibility tests for legacy field access
  - Deprecation behavior tests
- Acceptance criteria:
  - Existing consumers remain functional during migration window
  - Contract transition path is documented and test-enforced
- Estimated effort: Medium
- Risk: Medium
- Priority: P1

---

## Phase 1: Finalization Pipeline Stabilization

Goal: Establish the authoritative finalization path, add early integrated feedback, and harden gate orchestration before broad consumer alignment.

Execution streams:

1. Orchestrator stream: RE-005A establishes the finalization skeleton, then RE-005B completes metadata consolidation and deterministic diagnostics.
2. Gate-integration stream: RE-006 and RE-007 execute together to wire mandatory acceptance gates and shared rejection behavior.
3. Hardening stream: RE-009A provides early smoke coverage, RE-008 formalizes interfaces after behavior stabilizes, and RE-016 plus RE-017 add observability and retry-budget guardrails.

Phase exit criteria:

1. MatrixGenerator finalization is the authoritative return path for accepted puzzles.
2. Human reasoning and failure pattern gates are mandatory and persist deterministic acceptance diagnostics.
3. Smoke end-to-end orchestration tests pass against the stabilized finalization path.
4. Retry ceilings, diagnostics shape, and gate-level telemetry are defined and machine-readable.

### RE-005A
- ID: RE-005A
- Title: Implement Finalization Pipeline Skeleton and Deterministic Retry Ordering
- Description: Add the explicit finalization stage in MatrixGenerator, define ordered gate sequencing, and establish deterministic candidate retry behavior before metadata enrichment work.
- Architecture reference:
  - docs/architecture/SYSTEM_ARCHITECTURE.md (generation retries and gate orchestration)
  - docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md (MatrixGenerator._finalize_puzzle integration)
- Dependencies:
  - RE-001
  - RE-003
- Output artifact:
  - Finalization pipeline sequence diagram covering ordering, retry points, and gate invocation contract
- Files expected to change:
  - backend/app/matrix/rule_engine.py
  - backend/app/matrix/generator.py
  - backend/tests/test_rule_engine.py
- Required tests:
  - End-to-end finalize invocation test in generator flow
  - Determinism test for finalized retry ordering at fixed seed
- Acceptance criteria:
  - MatrixGenerator uses explicit finalize path before return
  - Finalize path has deterministic ordering for option generation, explanation, and validation gates
  - Candidate retry loop is explicit, bounded by configuration hooks, and deterministic for fixed seeds
- Estimated effort: Large
- Risk: High
- Priority: P0

### RE-009A
- ID: RE-009A
- Title: Build Smoke End-to-End Orchestration Test Suite
- Description: Add a thin integration suite that exercises the finalization skeleton early and verifies that orchestrated generation fails or succeeds through explicit gate sequencing rather than implicit behavior.
- Architecture reference:
  - docs/architecture/SYSTEM_ARCHITECTURE.md (layered reliability and gate sequencing)
  - docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md (regression strategy)
- Dependencies:
  - RE-005A
- Optional coordination:
  - RE-008
- Files expected to change:
  - backend/tests/test_rule_engine.py
  - backend/tests/test_human_reasoning_validator.py
  - backend/tests/test_failure_patterns.py
- Required tests:
  - Smoke positive flow: finalized puzzle emitted through explicit finalize path
  - Smoke negative flow: candidate rejection surfaces deterministic gate status
- Acceptance criteria:
  - Earliest orchestration path is protected by executable integration coverage
  - Failures identify gate order and retry outcome explicitly in assertions
- Estimated effort: Small
- Risk: Medium
- Priority: P1

### RE-006
- ID: RE-006
- Title: Integrate Human Reasoning Validator as Final Gate
- Description: Wire HumanReasoningValidator into the finalization stage with strict acceptance behavior and persisted review payload.
- Architecture reference:
  - docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md (pipeline order, review payload, integration plan)
- Dependencies:
  - RE-005A
  - RE-003
- Files expected to change:
  - backend/app/matrix/rule_engine.py
  - backend/app/matrix/human_reasoning_validator.py
  - backend/tests/test_human_reasoning_validator.py
  - backend/tests/test_rule_engine.py
- Required tests:
  - Integration test: gate called for each candidate
  - Rejection test for human_reasoning_unambiguous failure
  - Metadata persistence test for human_reasoning_review
- Acceptance criteria:
  - Acceptance requires human reasoning validator pass
  - validation_results includes human_reasoning_validator_acceptance
  - human_reasoning_review persisted with complete score keys
- Estimated effort: Medium
- Risk: High
- Priority: P0

### RE-007
- ID: RE-007
- Title: Integrate Known Failure Pattern Rejection Gate
- Description: Invoke failure pattern detector after quality and human checks, reject any candidate with matched FP ID, and persist detected patterns in metadata and diagnostics.
- Architecture reference:
  - docs/SPRINT_7_2_KNOWN_FAILURE_PATTERN_SYSTEM_ARCHITECTURE.md (integration point and metadata extension)
  - docs/KNOWN_FAILURE_PATTERNS.md (FP-001 through FP-012 policy)
- Dependencies:
  - RE-005A
  - RE-003
- Files expected to change:
  - backend/app/matrix/rule_engine.py
  - backend/app/matrix/failure_patterns.py
  - backend/tests/test_failure_patterns.py
  - backend/tests/test_rule_engine.py
- Required tests:
  - Integration test: detected pattern causes rejection
  - Metadata test: failure_patterns_detected and known_failure_pattern_passed keys
  - Determinism test for failure pattern output on fixed seed input
- Acceptance criteria:
  - Candidate is rejected when any failure pattern is detected
  - Pattern IDs and reasons are attached to diagnostics
  - validation_results includes known_failure_pattern_passed
- Estimated effort: Medium
- Risk: Medium
- Priority: P1

### RE-005B
- ID: RE-005B
- Title: Consolidate Finalization Metadata and Rejection Diagnostics
- Description: Complete the finalization stage by assembling canonical metadata, consolidating validation outputs, and enriching deterministic rejection diagnostics for downstream consumers.
- Architecture reference:
  - docs/architecture/SYSTEM_ARCHITECTURE.md (validated payload and diagnostics)
  - docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md (metadata persistence expectations)
- Dependencies:
  - RE-005A
  - RE-006
  - RE-007
- Output artifact:
  - Finalized gate API usage contract and diagnostic field map for accepted and rejected candidates
- Files expected to change:
  - backend/app/matrix/rule_engine.py
  - backend/app/matrix/generator.py
  - backend/app/matrix/quality_engine.py
  - backend/tests/test_rule_engine.py
- Required tests:
  - Metadata merge coherence test across all final gates
  - Deterministic rejection diagnostics test for fixed seed failures
- Acceptance criteria:
  - Finalize path assembles canonical metadata through one authoritative merge path
  - Candidate rejection and retry reasons are recorded deterministically
  - Downstream consumers can rely on one diagnostics structure for acceptance and rejection outcomes
- Estimated effort: Medium
- Risk: High
- Priority: P0

### RE-008
- ID: RE-008
- Title: Introduce ValidationGate and PuzzleFinalization Interfaces
- Description: Define explicit interfaces or protocols for gate inputs and outputs and for the finalization flow to reduce implicit coupling and enforce consistent composition.
- Architecture reference:
  - docs/AI_AGENT_RULES.md (explicit domain models and maintainability)
  - docs/reports/REASONING_ENGINE_COMPLIANCE.md (missing interfaces section)
- Dependencies:
  - RE-003
  - RE-005A
- Files expected to change:
  - backend/app/matrix/rule_engine.py
  - backend/app/matrix/quality_engine.py
  - backend/app/matrix/perceptual_validation.py
  - backend/app/matrix/expert_reviewer.py
  - backend/app/matrix/human_reasoning_validator.py
- Required tests:
  - Interface conformance tests for each gate adapter
  - Finalization pipeline composition test with mocked gates
- Acceptance criteria:
  - Every gate conforms to a shared interface contract
  - Finalization orchestrator uses interface-based composition rather than implicit field coupling
- Estimated effort: Medium
- Risk: Medium
- Priority: P1

### RE-016
- ID: RE-016
- Title: Validation Pipeline Observability and Failure Telemetry
- Description: Add structured counters and logging for gate pass or fail rates, retry counts, and failure pattern frequencies in runtime diagnostics.
- Architecture reference:
  - docs/architecture/SYSTEM_ARCHITECTURE.md
  - docs/SPRINT_7_2_KNOWN_FAILURE_PATTERN_SYSTEM_ARCHITECTURE.md
- Dependencies:
  - RE-005B
  - RE-006
  - RE-007
- Files expected to change:
  - backend/app/matrix/rule_engine.py
  - backend/app/main.py
  - backend/app/matrix/quality_tools.py
  - backend/tests/test_quality_tools.py
- Required tests:
  - Telemetry field presence and consistency tests
  - Deterministic retry diagnostics tests
- Acceptance criteria:
  - Gate-level observability is available and machine-readable
  - Metrics align with rejection event reports
- Estimated effort: Small to Medium
- Risk: Low
- Priority: P1

### RE-017
- ID: RE-017
- Title: Performance and Retry Budget Guardrails
- Description: Define and enforce maximum retry attempts and latency budgets for the finalized generation pipeline.
- Architecture reference:
  - docs/architecture/SYSTEM_ARCHITECTURE.md
  - docs/AI_AGENT_RULES.md
- Dependencies:
  - RE-005A
  - RE-006
  - RE-007
- Files expected to change:
  - backend/app/matrix/rule_engine.py
  - backend/tests/test_rule_engine.py
- Required tests:
  - Max retry boundary tests
  - Deterministic timeout and budget adherence tests
- Acceptance criteria:
  - Generator enforces configured retry ceilings
  - Pipeline remains within documented budget envelope for reference seeds
- Estimated effort: Medium
- Risk: Medium
- Priority: P1

---

## Phase 2: Integration Safety Net and Consumer Alignment

Goal: Expand end-to-end regression protection and stabilize report and API contracts against real integrated gate outcomes.

Execution streams:

1. Integration-test stream: RE-009B completes the full positive and negative acceptance matrix.
2. Reporting-contract stream: RE-010 locks report and analytics schema against integrated rejection events.
3. Consumer-alignment stream: RE-011 aligns serialized API payloads only after stabilized end-to-end semantics exist.

Phase exit criteria:

1. Full acceptance and rejection matrix is covered by deterministic integration tests.
2. quality_tools reports consume only canonical metadata fields with stable required keys.
3. API payload contract aligns to the finalized validated puzzle shape without breaking documented compatibility.

### RE-009B
- ID: RE-009B
- Title: Build Full End-to-End Acceptance and Rejection Test Matrix
- Description: Add the complete integration suite for generator flow, covering acceptance behavior, rejection paths, retry logic, and deterministic outcomes across the major gate failure taxonomy.
- Architecture reference:
  - docs/architecture/SYSTEM_ARCHITECTURE.md (layered reliability and gate sequencing)
  - docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md (regression strategy)
- Dependencies:
  - RE-006
  - RE-007
- Optional coordination:
  - RE-008
  - RE-017
- Files expected to change:
  - backend/tests/test_rule_engine.py
  - backend/tests/test_human_reasoning_validator.py
  - backend/tests/test_failure_patterns.py
  - backend/tests/test_quality_tools.py
- Required tests:
  - Positive flow: all gates pass and puzzle accepted
  - Negative flows: one test per major gate failure class
  - Retry behavior test with bounded attempts and deterministic diagnostics
- Acceptance criteria:
  - Generator integration tests verify full gate sequence and output metadata coherence
  - Failure reasons and gate statuses are asserted, not inferred
- Estimated effort: Medium
- Risk: Medium
- Priority: P1

### RE-010
- ID: RE-010
- Title: Stabilize Quality Tools and Report Contracts
- Description: Align quality_tools consumers with canonical metadata schema and ensure report output keys remain stable for analytics pipelines.
- Architecture reference:
  - docs/SPRINT_7_2_KNOWN_FAILURE_PATTERN_SYSTEM_ARCHITECTURE.md (reporting requirements)
  - docs/architecture/SYSTEM_ARCHITECTURE.md (diagnostics and reliability posture)
- Dependencies:
  - RE-003
  - RE-005B
  - RE-007
  - RE-009B
- Files expected to change:
  - backend/app/matrix/quality_tools.py
  - backend/tests/test_quality_tools.py
- Required tests:
  - Report schema snapshot and stability test
  - Failure pattern report population test
  - Logical rejection report consistency test
- Acceptance criteria:
  - Statistical and export reports use canonical metadata fields only
  - Required keys (failure_pattern_report and logical_validation_report structures) are always present
- Estimated effort: Small
- Risk: Low
- Priority: P1

### RE-011
- ID: RE-011
- Title: API Serialization Contract Alignment for Validated Puzzle Payload
- Description: Align backend API puzzle serialization with finalized puzzle contract, including explanation, options, and selected metadata without breaking existing clients.
- Architecture reference:
  - docs/architecture/SYSTEM_ARCHITECTURE.md (validated payload with explanation and metadata)
- Dependencies:
  - RE-001
  - RE-005B
  - RE-009B
  - RE-010
- Files expected to change:
  - backend/app/main.py
  - backend/tests/test_matrix_demo_endpoint.py
- Required tests:
  - Endpoint contract tests for payload keys and types
  - Determinism test for demo endpoint output
  - Backward-compatibility assertion for currently consumed fields
- Acceptance criteria:
  - API payload contains validated contract fields needed by consumers
  - Existing endpoint behavior remains deterministic
- Estimated effort: Small to Medium
- Risk: Medium
- Priority: P2

---

## Phase 3: Reasoning Trace Operationalization

Goal: Introduce runtime reasoning trace artifacts behind an architecture-approved rollout path and validate explanation-trace consistency.

Execution streams:

1. Trace-contract stream: RE-012 defines the trace builder boundary and artifact schema.
2. Runtime-trace stream: RE-013A builds the trace artifact and RE-013B attaches it to finalized puzzle outputs.
3. Governance and consistency stream: RE-018 adds ADR and rollout control, and RE-014 enforces explanation-trace consistency once the trace is attached.

Phase exit criteria:

1. Reasoning trace builder contract and artifact schema are explicit, documented, and type-checked.
2. Accepted puzzles can emit a valid runtime reasoning trace or stable reference through the finalized contract.
3. Trace rollout is architecture-approved and controllable through a feature flag or equivalent rollout guard.
4. Explanation text and reasoning trace remain consistent under automated validation when the trace path is enabled.

### RE-012
- ID: RE-012
- Title: Define ReasoningTraceBuilder Interface and Artifact Schema
- Description: Define a formal interface and schema for building reasoning graph artifacts from puzzle evidence, rules, constraints, hypotheses, and conclusions.
- Architecture reference:
  - docs/REASONING_GRAPH.md (graph lifecycle and rationale)
  - docs/reports/REASONING_ENGINE_COMPLIANCE.md (missing reasoning integration)
- Dependencies:
  - RE-003
- Optional coordination:
  - RE-008
- Output artifact:
  - Reasoning trace schema and storage decision covering inline attachment versus stable reference semantics
- Files expected to change:
  - backend/app/reasoning/__init__.py
  - backend/app/reasoning/models.py
  - backend/app/reasoning/graph.py
  - backend/app/matrix/models.py
- Required tests:
  - Interface conformance tests
  - Artifact schema serialization tests
- Acceptance criteria:
  - Trace builder contract is documented and type-checked
  - Trace artifact can be attached or referenced from quality_metadata without ambiguity
- Estimated effort: Medium
- Risk: Medium
- Priority: P2

### RE-018
- ID: RE-018
- Title: ADR and Feature-Flag Plan for Reasoning Trace Rollout
- Description: Create or update an ADR documenting reasoning graph runtime integration boundaries and add a rollout guard for controlled enablement.
- Architecture reference:
  - docs/AI_AGENT_RULES.md (architecture change governance)
  - docs/REASONING_GRAPH.md
- Dependencies:
  - RE-012
- Files expected to change:
  - docs/adr/ADR-006.md (or update an existing ADR)
  - backend/app/config.py
  - backend/app/matrix/rule_engine.py
  - backend/tests/test_rule_engine.py
- Required tests:
  - Feature-flag behavior tests (enabled versus disabled)
- Acceptance criteria:
  - Runtime trace integration is architecture-approved via ADR
  - Rollout can be toggled safely without code churn
- Estimated effort: Small to Medium
- Risk: Medium
- Priority: P2

### RE-013A
- ID: RE-013A
- Title: Build Runtime Reasoning Trace Artifact
- Description: Implement reasoning graph construction in the finalization pipeline using applied rules, visible evidence, option hypotheses, and selected conclusion.
- Architecture reference:
  - docs/REASONING_GRAPH.md (node and edge semantics, provenance, dependencies)
  - docs/architecture/SYSTEM_ARCHITECTURE.md (explainability and validation responsibility)
- Dependencies:
  - RE-005B
  - RE-012
- Files expected to change:
  - backend/app/matrix/rule_engine.py
  - backend/app/reasoning/graph.py
  - backend/app/reasoning/models.py
  - backend/tests/test_reasoning_graph.py
  - backend/tests/test_rule_engine.py
- Required tests:
  - DAG validity test for runtime-generated traces
  - Consistency test: provenance includes observation lineage for conclusion node
- Acceptance criteria:
  - Runtime trace artifact can be built deterministically from finalized puzzle evidence
  - Trace passes GraphValidator and supports provenance and dependency queries
- Estimated effort: Medium
- Risk: Medium
- Priority: P2

### RE-013B
- ID: RE-013B
- Title: Attach Runtime Reasoning Trace to Finalized Puzzle Contract
- Description: Attach the generated reasoning trace artifact or stable reference to finalized puzzle metadata and downstream serialization surfaces.
- Architecture reference:
  - docs/REASONING_GRAPH.md (provenance and query surfaces)
  - docs/architecture/SYSTEM_ARCHITECTURE.md (validated payload responsibilities)
- Dependencies:
  - RE-013A
  - RE-018
- Files expected to change:
  - backend/app/matrix/rule_engine.py
  - backend/app/reasoning/graph.py
  - backend/app/reasoning/models.py
  - backend/tests/test_reasoning_graph.py
  - backend/tests/test_rule_engine.py
- Required tests:
  - Integration test: finalized puzzle contains reasoning trace artifact or stable reference
  - Serialization test for trace attachment behavior under rollout guard
- Acceptance criteria:
  - Every accepted puzzle can expose a valid reasoning trace when rollout is enabled
  - Trace attachment path is consistent with the storage decision defined in RE-012
- Estimated effort: Small to Medium
- Risk: Medium
- Priority: P2

### RE-014
- ID: RE-014
- Title: Reasoning Trace Validation and Explainability Consistency Checks
- Description: Add validation that explanation text and reasoning graph do not diverge on applied rules and conclusion rationale.
- Architecture reference:
  - docs/COGNERA_PUZZLE_STANDARD.md (explanation must reconstruct complete reasoning)
  - docs/REASONING_GRAPH.md (explicit dependency and provenance tracking)
- Dependencies:
  - RE-013B
  - RE-009B
  - RE-010
- Files expected to change:
  - backend/app/matrix/human_reasoning_validator.py
  - backend/app/matrix/explainer.py
  - backend/tests/test_human_reasoning_validator.py
  - backend/tests/test_reasoning_graph.py
- Required tests:
  - Cross-check test: rule references in explanation align with rule, hypothesis, and conclusion nodes
  - Rejection test for trace and explanation inconsistency
- Acceptance criteria:
  - Validator detects and reports trace or explanation drift
  - Acceptance requires consistency check pass when trace is enabled
- Estimated effort: Small to Medium
- Risk: Medium
- Priority: P2

---

## Phase dependency summary

Phase 0 dependencies:

- None (architecture foundation)

Phase 1 depends on:

- RE-001
- RE-002
- RE-003
- RE-004
- RE-015

Phase 2 depends on:

- RE-005A
- RE-005B
- RE-006
- RE-007
- RE-008
- RE-009A
- RE-016
- RE-017

Phase 3 depends on:

- RE-003
- RE-005B
- RE-009B
- RE-010
- RE-012
- RE-018

## Architectural milestones and release gates

1. End Phase 0: Contract and schema stability established.
2. End Phase 1: Deterministic acceptance pipeline established.
3. End Phase 2: Regression protection and reporting stability established.
4. End Phase 3: Traceability and provenance architecture realized under controlled rollout.

## Suggested delivery checkpoints

Checkpoint A (end Phase 1):
- Contract is unified and test-guarded.
- No implicit puzzle fields remain.

Checkpoint B (end Phase 2):
- Finalization and all acceptance gates are wired and deterministic.
- Human reasoning and failure pattern outcomes are persisted.

Checkpoint C (end Phase 3):
- End-to-end test matrix protects acceptance/rejection behavior.
- Quality reports are schema-stable.

Checkpoint D (end Phase 4):
- Runtime reasoning trace exists and is validated for consistency.
- Provenance-based explainability is auditable.

## Independent implementation rule

Each backlog item above is designed to be independently implementable if its dependencies are already complete. Each item includes explicit scope, touchpoints, and acceptance tests so implementation can proceed in parallel where dependency graph allows.

## Definition of done for Epic 3

1. All P0 and P1 items completed and passing tests.
2. Finalized puzzle output is contract-stable across generator, validator, API, and quality tooling.
3. Acceptance/rejection decisions are deterministic, machine-readable, and fully test-covered.
4. Reasoning traceability (Phase 4 scope) is implemented and validated if included in release target.
