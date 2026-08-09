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
COPY .git ./.git

RUN set -eu; \
		head_ref_raw="$(cat .git/HEAD || true)"; \
		resolved_ref=""; \
		resolved_sha=""; \
		if [ -n "$head_ref_raw" ]; then \
			case "$head_ref_raw" in \
				ref:*) \
					resolved_ref="${head_ref_raw#ref: }"; \
					if [ -f ".git/${resolved_ref}" ]; then \
						resolved_sha="$(cat ".git/${resolved_ref}")"; \
					elif [ -f .git/packed-refs ]; then \
						resolved_sha="$(grep " ${resolved_ref}$" .git/packed-refs | tail -n 1 | cut -d' ' -f1)"; \
					fi \
					;; \
				*) \
					resolved_sha="$head_ref_raw"; \
					;; \
			esac; \
		fi; \
		printf "%s" "${resolved_sha:-unknown}" > /app/.build_commit_sha; \
		if [ -n "$resolved_ref" ]; then \
			printf "%s" "${resolved_ref##*/}" > /app/.build_git_branch; \
		else \
			printf "%s" "unknown" > /app/.build_git_branch; \
		fi; \
		date -u +"%Y-%m-%dT%H:%M:%SZ" > /app/.build_timestamp; \
		rm -rf /app/.git

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

COPY backend/ ./backend
COPY --from=frontend-builder /frontend/dist ./frontend-dist
RUN test -f /app/frontend-dist/index.html

EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
