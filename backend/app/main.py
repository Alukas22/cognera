import json
import logging
from pathlib import Path
import sys
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import AppConfig
from .database import prepare_database_connection
from .matrix import DifficultyEngine, RuleRegistry, MatrixGenerator, RuleType, explain_puzzle

config = AppConfig()

logger = logging.getLogger("cognera")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = getattr(record, "request_id", None)
        if request_id is not None:
            payload["request_id"] = request_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


handler.setFormatter(StructuredJsonFormatter())
logger.addHandler(handler)


class MatrixGenerateRequest(BaseModel):
    seed: int | None = None


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = BASE_DIR / "frontend-dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"
API_PREFIXES = (
    "/matrix",
    "/health",
    "/version",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/assets",
)

app = FastAPI(title=config.app_name, debug=config.debug, version=config.version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="frontend-assets")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    extra = {"request_id": request_id, "path": request.url.path, "method": request.method}
    logger.info("request.started", extra=extra)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    logger.info("request.completed", extra={**extra, "status_code": response.status_code})
    return response


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("application.startup", extra={"app_name": config.app_name, "version": config.version})
    logger.info(
        "frontend.bundle",
        extra={
            "dist_dir": str(FRONTEND_DIST_DIR),
            "index_path": str(FRONTEND_INDEX_FILE),
            "index_exists": FRONTEND_INDEX_FILE.exists(),
        },
    )
    prepare_database_connection()


def _serve_frontend_index() -> FileResponse:
    if FRONTEND_INDEX_FILE.exists():
        return FileResponse(FRONTEND_INDEX_FILE)
    raise HTTPException(status_code=503, detail="Frontend build is not available in runtime image.")


@app.get("/")
async def read_root():
    logger.info("endpoint.root", extra={"path": "/"})
    return _serve_frontend_index()


@app.get("/health-check")
async def health_check_page():
    logger.info("endpoint.health_check_page", extra={"path": "/health-check"})
    return _serve_frontend_index()


@app.get("/health")
async def health() -> dict[str, str]:
    logger.info("endpoint.health", extra={"path": "/health"})
    return {"status": "ok"}


@app.get("/version")
async def version() -> dict[str, str]:
    logger.info("endpoint.version", extra={"path": "/version"})
    return {"app_name": config.app_name, "version": config.version}


def _serialize_figure(figure):
    if figure is None:
        return None
    return {
        "shape": figure.shape,
        "rotation": figure.rotation,
        "size": figure.size,
        "color": figure.color,
    }


def _serialize_distractor(distractor):
    return {
        "shape": distractor.figure.shape,
        "rotation": distractor.figure.rotation,
        "size": distractor.figure.size,
        "color": distractor.figure.color,
        "reason": distractor.reason.value,
        "explanation": distractor.explanation,
        "origin_rule": distractor.origin_rule.value,
        "difficulty": distractor.difficulty,
    }


def _serialize_option(option):
    payload = {
        "label": option.label,
        "shape": option.figure.shape,
        "rotation": option.figure.rotation,
        "size": option.figure.size,
        "color": option.figure.color,
        "is_correct": option.is_correct,
        "difficulty": option.difficulty,
    }
    if option.reason is not None:
        payload["reason"] = option.reason.value
    if option.explanation:
        payload["explanation"] = option.explanation
    if option.origin_rule is not None:
        payload["origin_rule"] = option.origin_rule.value
    return payload


def _serialize_rule(rule):
    return {
        "type": rule.type.value,
        "value": rule.value,
        "difficulty": rule.difficulty,
    }


def _serialize_puzzle(puzzle):
    return {
        "seed": puzzle.seed,
        "grid": [[_serialize_figure(cell) for cell in row] for row in puzzle.grid],
        "missing_position": list(puzzle.missing_position),
        "solution": _serialize_figure(puzzle.solution),
        "options": [_serialize_option(option) for option in puzzle.options],
        "correct_index": puzzle.correct_index,
        "rules": [_serialize_rule(rule) for rule in puzzle.rules],
        "difficulty": puzzle.difficulty,
        "difficulty_profile": puzzle.difficulty_profile.as_dict() if puzzle.difficulty_profile is not None else None,
        "explanation": puzzle.explanation,
    }


@app.get("/matrix/demo")
async def matrix_demo() -> dict:
    logger.info("endpoint.matrix_demo", extra={"path": "/matrix/demo"})

    registry = RuleRegistry()
    rule = registry.get(RuleType.ROTATION)
    puzzle = MatrixGenerator(rule).generate(seed=123)
    explanation_text = explain_puzzle(puzzle)

    options = [
        _serialize_option(option) for option in puzzle.options
    ]

    return {
        "grid": [
            [_serialize_figure(cell) for cell in row] for row in puzzle.grid
        ],
        "missing": [2, 2],
        "options": options,
        "correct": puzzle.correct_index,
        "correct_index": puzzle.correct_index,
        "explanation": explanation_text,
        "skills": puzzle.skill_profile.as_dict(),
        "difficulty": puzzle.difficulty,
        "difficulty_profile": puzzle.difficulty_profile.as_dict() if puzzle.difficulty_profile is not None else None,
    }


@app.post("/matrix/generate")
async def matrix_generate(request: MatrixGenerateRequest | None = None) -> dict:
    logger.info("endpoint.matrix_generate", extra={"path": "/matrix/generate"})

    seed = request.seed if request is not None and request.seed is not None else uuid.uuid4().int % (2 ** 31)
    puzzle = MatrixGenerator(RuleRegistry()).generate(seed=seed)
    return _serialize_puzzle(puzzle)


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    request_path = f"/{full_path}"

    for prefix in API_PREFIXES:
        if request_path == prefix or request_path.startswith(f"{prefix}/"):
            raise HTTPException(status_code=404, detail="Not Found")

    # Do not hijack real file lookups that should 404 when missing.
    if "." in full_path.split("/")[-1]:
        raise HTTPException(status_code=404, detail="Not Found")

    return _serve_frontend_index()
