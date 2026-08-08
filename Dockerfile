FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY .env.example .

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

COPY backend/ ./backend

CMD ["python", "-m", "backend.app"]
