import json
import logging
import sys
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import AppConfig
from .database import prepare_database_connection
from .matrix import RuleRegistry, MatrixGenerator, RuleType

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
