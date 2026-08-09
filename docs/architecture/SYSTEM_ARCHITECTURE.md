# Cognera System Architecture

## Purpose

This document defines the current architecture of Cognera as implemented in this repository. It explains the major subsystems, their responsibilities, and how requests move through generation, validation, and user interaction paths.

## System Overview

Cognera is a full-stack cognitive puzzle platform composed of two runtime surfaces:

- A FastAPI backend that generates and validates matrix puzzles.
- A Vite-based frontend that renders gameplay, submits generation requests, and displays explanations and session metrics.

The backend is the system of record for puzzle correctness and quality. The frontend is a consumer of backend puzzle contracts and is intentionally thin in puzzle logic.

## Top-Level Architecture

### Backend

The backend is organized around a matrix engine under `backend/app/matrix`.

Core responsibilities:

- Construct puzzle candidates from rule-driven transformations.
- Build distractor options while preserving answer uniqueness.
- Enforce quality, perceptual, expert, and failure-pattern checks before returning a puzzle.
- Expose HTTP endpoints for generation and health/version diagnostics.

Key backend modules and roles:

- `main.py`: FastAPI app lifecycle and endpoint registration.
- `config.py`: Runtime configuration via environment-backed settings.
- `matrix/generator.py`: Candidate matrix and rule application workflow.
- `matrix/rule_engine.py`: Orchestration of generation retries and gating.
- `matrix/quality_engine.py`: Quality scoring and pass/fail thresholds.
- `matrix/perceptual_validation.py`: Human-perception-aligned checks.
- `matrix/expert_reviewer.py`: Additional structured review heuristics.
- `matrix/failure_patterns.py`: Known failure detection and regression protection.
- `matrix/answer_options.py`: Distractor generation and uniqueness guarantees.
- `matrix/explainer.py`: Rule-grounded explanation construction.

### Frontend

The frontend is a Vite application under `frontend/src`.

Core responsibilities:

- Request puzzles from backend endpoints.
- Render puzzle figures and answer options.
- Collect and display user answers, correctness feedback, and explanation text.
- Track gameplay session statistics.
- Provide health diagnostics UX for frontend-backend connectivity.

Key frontend modules and roles:

- `api.js`: Backend request and fallback handling.
- `game.js`: Gameplay state transitions and round flow.
- `ui.js`: DOM rendering and interaction binding.
- `figureSvg.js`: Visual figure rendering helpers.
- `logger.js`: Structured frontend diagnostics logging.

## Request and Data Flow

### Puzzle Generation Flow

1. Frontend issues a generation request to the backend matrix API.
2. Backend generation engine builds candidate puzzle states from rule combinations.
3. Distractor logic creates answer options and enforces uniqueness.
4. Rule engine applies validation gates and retries when candidates fail strict criteria.
5. Quality and perceptual evaluators score and validate the candidate.
6. Failure-pattern checks reject known bad puzzle constructions.
7. Backend returns a validated puzzle payload with explanation and metadata.
8. Frontend renders puzzle, options, and explanation pathways.

### Diagnostics Flow

- Frontend health diagnostics page checks backend reachability and version metadata.
- Backend exposes health and version endpoints for runtime verification.

## Quality and Reliability Architecture

Cognera reliability depends on layered validation rather than single-pass generation.

Validation layers:

- Structural validity: matrix composition and rule consistency.
- Option validity: answer uniqueness and plausible distractors.
- Quality validity: threshold-based quality scoring.
- Perceptual validity: human-salient distinguishability and clarity.
- Failure-pattern validity: explicit rejection of historically observed defects.

This layered approach reduces regressions by preventing low-quality or ambiguous puzzles from being emitted even when generation succeeds syntactically.

## Testing Architecture

Backend and frontend are tested independently and as part of CI:

- Backend tests validate engines, validators, models, and API behavior.
- Frontend unit tests validate rendering and gameplay logic.
- Playwright E2E tests validate end-to-end gameplay behavior.

The intended release posture is green CI across all three layers before deployment acceptance.

## Deployment Architecture

Cognera deploys through GitHub Actions and Railway integration.

Deployment sequence:

1. Changes are merged to `main`.
2. CI executes backend tests, frontend tests/build, and E2E coverage.
3. Railway deploys the validated revision.
4. Post-deploy verification confirms backend health/version and browser gameplay behavior.

## Documentation and Governance Boundaries

Architecture in this document aligns with repository governance references:

- Puzzle standard for generation and validation expectations.
- Visual grammar for figure and rendering semantics.
- Engineering principles for implementation and release discipline.
- Known failure pattern catalogue for regression prevention.

Changes that affect generation correctness, visual semantics, or release criteria should be reflected in this architecture document to keep system intent and implementation aligned.
