import json
import logging
import random
import sys
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import AppConfig
from .database import prepare_database_connection
from .matrix import RuleRegistry, MatrixGenerator, RuleType

config = AppConfig()


class GeneratePuzzleRequest(BaseModel):
    seed: int | None = None

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


def _serialize_option(option) -> dict[str, Any]:
    return {
        "label": option.label,
        **_serialize_figure(option.figure),
        "is_correct": option.is_correct,
        "difficulty": option.difficulty,
        "reason": None if option.reason is None else option.reason.value,
        "explanation": option.explanation,
        "origin_rule": None if option.origin_rule is None else option.origin_rule.value,
    }


def _serialize_difficulty_profile(profile) -> dict[str, float]:
    return profile.as_dict()


def _project_vertical_slice_options(puzzle) -> tuple[list[dict[str, Any]], int]:
    correct_index = puzzle.correct_index
    candidate_indices = [correct_index]
    candidate_indices.extend(
        index
        for index, option in enumerate(puzzle.options)
        if index != correct_index and not option.is_correct
    )
    selected_indices = sorted(candidate_indices[:4])

    options: list[dict[str, Any]] = []
    remapped_correct_index = 0
    for projected_index, original_index in enumerate(selected_indices):
        option = puzzle.options[original_index]
        serialized = _serialize_option(option)
        serialized["label"] = chr(65 + projected_index)
        options.append(serialized)
        if original_index == correct_index:
            remapped_correct_index = projected_index

    return options, remapped_correct_index


def _serialize_generated_puzzle(puzzle) -> dict[str, Any]:
    options, correct_index = _project_vertical_slice_options(puzzle)
    return {
        "seed": puzzle.seed,
        "grid": [
            [_serialize_figure(cell) for cell in row] for row in puzzle.grid
        ],
        "missing_position": list(puzzle.missing_position),
        "options": options,
        "correct_index": correct_index,
        "explanation": puzzle.explanation,
        "difficulty": puzzle.difficulty,
        "difficulty_profile": _serialize_difficulty_profile(puzzle.difficulty_profile),
    }


@app.get("/matrix/demo")
async def matrix_demo() -> dict:
    logger.info("endpoint.matrix_demo", extra={"path": "/matrix/demo"})

    registry = RuleRegistry()
    rule = registry.get(RuleType.ROTATION)
    puzzle = MatrixGenerator(rule).generate(seed=123)

    return {
        "grid": [
            [_serialize_figure(cell) for cell in row] for row in puzzle.grid
        ],
        "missing": list(puzzle.missing_position),
        "options": [_serialize_figure(option.figure) for option in puzzle.options],
        "correct": puzzle.correct_index,
        "explanation": puzzle.explanation,
        "skills": puzzle.skill_profile.as_dict(),
        "difficulty": puzzle.difficulty,
        "difficulty_profile": {
            "overall": puzzle.difficulty_profile.overall,
            "working_memory": puzzle.difficulty_profile.working_memory,
            "pattern_complexity": puzzle.difficulty_profile.pattern_complexity,
            "visual_complexity": puzzle.difficulty_profile.visual_complexity,
            "rule_complexity": puzzle.difficulty_profile.rule_complexity,
            "abstraction": puzzle.difficulty_profile.abstraction,
            "distractor_strength": puzzle.difficulty_profile.distractor_strength,
        },
    }


@app.post("/matrix/generate")
async def matrix_generate(payload: GeneratePuzzleRequest | None = None) -> dict[str, Any]:
    logger.info("endpoint.matrix_generate", extra={"path": "/matrix/generate"})

    seed = payload.seed if payload and payload.seed is not None else random.randint(1, 1_000_000_000)
    puzzle = MatrixGenerator(RuleRegistry()).generate(seed=seed)
    return _serialize_generated_puzzle(puzzle)
