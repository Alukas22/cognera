FROM node:20-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim

WORKDIR /app

ARG GIT_COMMIT_SHA=unknown
ARG GIT_BRANCH=unknown
ARG BUILD_TIMESTAMP=unknown

ENV GIT_COMMIT_SHA=$GIT_COMMIT_SHA
ENV GIT_BRANCH=$GIT_BRANCH
ENV BUILD_TIMESTAMP=$BUILD_TIMESTAMP

COPY pyproject.toml .
COPY poetry.lock .
COPY .env.example .

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

COPY backend/ ./backend
COPY --from=frontend-builder /frontend/dist ./frontend-dist
RUN test -f /app/frontend-dist/index.html

EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
