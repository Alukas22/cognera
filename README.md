# Cognera

The future of cognitive performance.

## Product Vision

Cognera builds reasoning-first puzzle experiences that improve users' cognitive development through clear, explainable, and psychometrically meaningful challenge design.

Product quality is governed by [docs/COGNERA_QUALITY_STANDARD.md](docs/COGNERA_QUALITY_STANDARD.md).

## Project structure

- `backend/` - Python backend app and tests
- `frontend/` - Frontend source and public assets
- `.github/workflows/` - CI workflows
- `docs/` - Project documentation

## Puzzle standard

Cognera puzzle quality is governed by the canonical specification in
`docs/COGNERA_PUZZLE_STANDARD.md`.

All future puzzle generation, validation, explanations, and quality gates
must comply with this standard.

## Visual grammar

Cognera visual object architecture is governed by
`docs/COGNERA_VISUAL_GRAMMAR.md`.

All future visual primitives, symbol composition, transformations, and
rendering logic must comply with this grammar.

## Engineering policy

Cognera mandatory development policy is defined in
`docs/ENGINEERING_PRINCIPLES.md`.

All architecture, implementation, validation, and release work must follow
this engineering constitution.

## Known failure patterns

Cognera maintains a permanent failure catalogue in
`docs/KNOWN_FAILURE_PATTERNS.md`.

When adding a new failure pattern:

1. Add a new `FP-###` entry in `docs/KNOWN_FAILURE_PATTERNS.md`.
2. Add detector logic in `backend/app/matrix/failure_patterns.py`.
3. Add a dedicated regression test in `backend/tests/test_failure_patterns.py`.
4. Verify quality reports include frequency and trend for the new pattern.

## Getting started

1. Copy `.env.example` to `.env`
2. Install Python dependencies
3. Build frontend as needed

### Run backend

```bash
poetry install
poetry run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Backend health and version endpoints:

- `GET /health`
- `GET /version`

### Run frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend talks to the existing FastAPI backend using `/matrix/generate`
with a `/matrix/demo` fallback for compatibility.

### Frontend health check page

Open `http://127.0.0.1:5173/health-check` to verify frontend + backend
connectivity, app version, and deployment environment metadata.

### Run frontend unit tests

```bash
cd frontend
npm test
```

### Run Playwright E2E tests

Start backend and frontend first, then run:

```bash
cd frontend
E2E_BASE_URL=http://127.0.0.1:5173 npm run test:e2e
```

### Deployment workflow

1. Push changes to `main`.
2. GitHub Actions runs:
	- backend tests
	- frontend unit tests + build
	- Playwright E2E tests
3. Railway deploys the updated revision.
4. Verify:
	- CI run status is `success`
	- Railway deployment state is `success`
	- Browser gameplay and `/health-check` render correctly

## Milestones

- Sprint 1 ✅
- Sprint 2 ✅

### Sprint 2 completed capabilities

- Structured `Distractor` object model for answer options
- Rule-specific distractor generation with metadata preservation
- Rule overlay support for composed matrix puzzles
- Full backend test suite verified cleanly

### Sprint 4.0 completed capabilities

- First playable Cognera web experience
- Responsive matrix gameplay with 6 answer options
- Immediate correctness feedback and explanation rendering
- Session statistics (score, puzzle count, accuracy, elapsed time, difficulty)
- Frontend unit tests and CI build validation

### Sprint 4.1 completed capabilities

- Playwright E2E coverage for the primary gameplay loop
- Frontend timeout handling and graceful retry UX
- Structured frontend diagnostics logging
- Frontend health diagnostics page
- Automated E2E execution in GitHub Actions
