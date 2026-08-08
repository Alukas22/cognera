FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY poetry.lock .
COPY .env.example .

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

COPY backend/ ./backend

EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
