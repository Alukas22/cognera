# Architecture Index

## Purpose

This index defines the canonical entry points to Cognera architecture knowledge. It provides a structured reading path, maps key architectural layers to their governing documents, and identifies ownership and versioning expectations for ongoing architecture governance.

The objective is to make architectural intent discoverable, auditable, and actionable for engineers, reviewers, and AI agents operating in this repository.

## Level 1 Governing Documents

The following are Level 1 governing documents for the Cognera project:

1. [docs/COGNERA_QUALITY_STANDARD.md](docs/COGNERA_QUALITY_STANDARD.md)
2. [docs/architecture/SYSTEM_ARCHITECTURE.md](docs/architecture/SYSTEM_ARCHITECTURE.md)
3. [docs/ENGINEERING_PRINCIPLES.md](docs/ENGINEERING_PRINCIPLES.md)

The Quality Standard is the highest-level product specification and takes precedence for product-direction decisions unless an approved ADR explicitly states otherwise.

## Reading Order

Read documents in the following order to build context from system-wide concepts to implementation constraints and quality rules:

1. [docs/architecture/SYSTEM_ARCHITECTURE.md](docs/architecture/SYSTEM_ARCHITECTURE.md)
2. [docs/ENGINEERING_PRINCIPLES.md](docs/ENGINEERING_PRINCIPLES.md)
3. [docs/COGNERA_QUALITY_STANDARD.md](docs/COGNERA_QUALITY_STANDARD.md)
4. [docs/COGNERA_PUZZLE_STANDARD.md](docs/COGNERA_PUZZLE_STANDARD.md)
5. [docs/COGNERA_VISUAL_GRAMMAR.md](docs/COGNERA_VISUAL_GRAMMAR.md)
6. [docs/FIGURE_LIBRARY.md](docs/FIGURE_LIBRARY.md)
7. [docs/REASONING_GRAPH.md](docs/REASONING_GRAPH.md)
8. [docs/KNOWN_FAILURE_PATTERNS.md](docs/KNOWN_FAILURE_PATTERNS.md)
9. [docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md](docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md)
10. [docs/SPRINT_7_2_KNOWN_FAILURE_PATTERN_SYSTEM_ARCHITECTURE.md](docs/SPRINT_7_2_KNOWN_FAILURE_PATTERN_SYSTEM_ARCHITECTURE.md)
11. [docs/adr/ADR-001.md](docs/adr/ADR-001.md) through [docs/adr/ADR-005.md](docs/adr/ADR-005.md)

## Layered Architecture Overview

Cognera architecture is organized into layered concerns. The documents below establish authority by layer:

1. Platform and system layer:
	- [docs/architecture/SYSTEM_ARCHITECTURE.md](docs/architecture/SYSTEM_ARCHITECTURE.md)
2. Domain and puzzle logic layer:
	- [docs/COGNERA_QUALITY_STANDARD.md](docs/COGNERA_QUALITY_STANDARD.md)
	- [docs/COGNERA_PUZZLE_STANDARD.md](docs/COGNERA_PUZZLE_STANDARD.md)
	- [docs/COGNERA_VISUAL_GRAMMAR.md](docs/COGNERA_VISUAL_GRAMMAR.md)
	- [docs/REASONING_GRAPH.md](docs/REASONING_GRAPH.md)
3. Content primitives and representation layer:
	- [docs/FIGURE_LIBRARY.md](docs/FIGURE_LIBRARY.md)
4. Quality assurance and failure analysis layer:
	- [docs/KNOWN_FAILURE_PATTERNS.md](docs/KNOWN_FAILURE_PATTERNS.md)
	- [docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md](docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md)
	- [docs/SPRINT_7_2_KNOWN_FAILURE_PATTERN_SYSTEM_ARCHITECTURE.md](docs/SPRINT_7_2_KNOWN_FAILURE_PATTERN_SYSTEM_ARCHITECTURE.md)
5. Cross-cutting engineering governance layer:
	- [docs/ENGINEERING_PRINCIPLES.md](docs/ENGINEERING_PRINCIPLES.md)
	- [docs/AI_AGENT_RULES.md](docs/AI_AGENT_RULES.md)

## Core Architecture Documents

The following documents define core architecture scope and constraints:

1. [docs/architecture/SYSTEM_ARCHITECTURE.md](docs/architecture/SYSTEM_ARCHITECTURE.md): System boundaries, responsibilities, and major component interactions.
2. [docs/REASONING_GRAPH.md](docs/REASONING_GRAPH.md): Reasoning structure and explainability model.
3. [docs/FIGURE_LIBRARY.md](docs/FIGURE_LIBRARY.md): Figure semantics and reusable visual primitives.
4. [docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md](docs/SPRINT_7_2_HUMAN_REASONING_VALIDATOR_ARCHITECTURE.md): Human reasoning validation architecture.
5. [docs/SPRINT_7_2_KNOWN_FAILURE_PATTERN_SYSTEM_ARCHITECTURE.md](docs/SPRINT_7_2_KNOWN_FAILURE_PATTERN_SYSTEM_ARCHITECTURE.md): Failure-pattern architecture and detection model.

## Architecture Decision Records (ADR)

Architecture decisions are tracked under [docs/adr](docs/adr) as ADR documents.

Current ADR set:

1. [docs/adr/ADR-001.md](docs/adr/ADR-001.md)
2. [docs/adr/ADR-002.md](docs/adr/ADR-002.md)
3. [docs/adr/ADR-003.md](docs/adr/ADR-003.md)
4. [docs/adr/ADR-004.md](docs/adr/ADR-004.md)
5. [docs/adr/ADR-005.md](docs/adr/ADR-005.md)

ADR usage policy:

1. Any non-trivial architecture change must be represented by a new or updated ADR.
2. Superseded decisions must remain documented to preserve decision lineage.
3. Implementation and pull requests must reference relevant ADR identifiers when applicable.

## Engineering Standards

The following standards constrain implementation quality and architectural consistency:

1. [docs/ENGINEERING_PRINCIPLES.md](docs/ENGINEERING_PRINCIPLES.md): Core engineering rules and quality expectations.
2. [docs/COGNERA_QUALITY_STANDARD.md](docs/COGNERA_QUALITY_STANDARD.md): Governing product quality standard and cognitive-development constraints.
3. [docs/COGNERA_PUZZLE_STANDARD.md](docs/COGNERA_PUZZLE_STANDARD.md): Puzzle-quality constraints and design requirements.
4. [docs/COGNERA_VISUAL_GRAMMAR.md](docs/COGNERA_VISUAL_GRAMMAR.md): Visual consistency and transformation grammar.
5. [docs/KNOWN_FAILURE_PATTERNS.md](docs/KNOWN_FAILURE_PATTERNS.md): Catalog of known failure modes and guardrails.
6. [docs/AI_AGENT_RULES.md](docs/AI_AGENT_RULES.md): AI contribution governance and architecture protection rules.

## Future Documentation

Future architecture documentation should extend this index in a controlled manner. Recommended future additions include:

1. End-to-end data flow and contract maps across backend and frontend boundaries.
2. Deployment and runtime operations architecture references.
3. Observability, telemetry, and quality-monitoring architecture.
4. Explicit API architecture references and versioning policy artifacts.
5. Security and risk architecture documentation aligned with platform maturity.

All new architecture documents should be linked from this index and positioned in the reading order where they become authoritative.

## Ownership

Architecture documentation ownership is shared across repository maintainers and principal technical contributors.

Ownership responsibilities:

1. Maintain coherence between implementation and architecture documents.
2. Ensure ADR lifecycle discipline for architecture-impacting changes.
3. Keep this index current as new architecture artifacts are added.
4. Enforce alignment with engineering and puzzle-quality standards.

## Versioning

Architecture documentation is versioned through repository history.

Versioning rules:

1. Architecture-impacting pull requests must update relevant docs in the same change set.
2. ADRs are append-only records; updates should preserve historical context.
3. Significant architectural shifts should include explicit migration or transition notes.
4. This index should be revised whenever authoritative architecture sources are added, removed, or superseded.
