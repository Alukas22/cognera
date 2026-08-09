# Cognera

The future of cognitive performance.

## Project structure

- `backend/` - Python backend app and tests
- `frontend/` - Frontend source and public assets
- `.github/workflows/` - CI workflows
- `docs/` - Project documentation

## Getting started

1. Copy `.env.example` to `.env`
2. Install Python dependencies
3. Build frontend as needed

### Run backend

```bash
poetry install
poetry run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Run frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend talks to the existing FastAPI backend using `/matrix/generate`
with a `/matrix/demo` fallback for compatibility.

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
