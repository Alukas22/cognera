import json
import logging
import sys
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI(title=config.app_name, debug=config.debug, version=config.version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    prepare_database_connection()


@app.get("/")
async def read_root() -> dict[str, str]:
    logger.info("endpoint.root", extra={"path": "/"})
    return {"message": "Welcome to Cognera"}


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
    }


@app.post("/matrix/generate")
async def matrix_generate(request: MatrixGenerateRequest | None = None) -> dict:
    logger.info("endpoint.matrix_generate", extra={"path": "/matrix/generate"})

    seed = request.seed if request is not None and request.seed is not None else uuid.uuid4().int % (2 ** 31)
    puzzle = MatrixGenerator(RuleRegistry()).generate(seed=seed)
    return _serialize_puzzle(puzzle)
