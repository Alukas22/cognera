/**
 * API access layer for frontend gameplay.
 * Uses the production puzzle endpoint and preserves compatibility with
 * legacy demo payloads if fallback is needed.
 */

import { createLogger } from "./logger.js";

const GENERATE_ENDPOINT = "/matrix/generate";
const DEMO_ENDPOINT = "/matrix/demo";
const HEALTH_ENDPOINT = "/health";
const VERSION_ENDPOINT = "/version";
const DEFAULT_TIMEOUT_MS = 8000;

const logger = createLogger("frontend.api");

class ApiTimeoutError extends Error {
  constructor(timeoutMs) {
    super(`Request timed out after ${timeoutMs}ms`);
    this.name = "ApiTimeoutError";
    this.timeoutMs = timeoutMs;
  }
}

function normalizeOption(option, index) {
  return {
    label: option.label ?? String.fromCharCode(65 + index),
    shape: option.shape,
    rotation: option.rotation,
    size: option.size,
    color: option.color,
    is_correct: Boolean(option.is_correct),
    difficulty: typeof option.difficulty === "number" ? option.difficulty : 0,
    reason: option.reason ?? null,
    explanation: option.explanation ?? "",
    origin_rule: option.origin_rule ?? null,
  };
}

function normalizePuzzle(payload) {
  const missingPosition = payload.missing_position ?? payload.missing ?? [2, 2];
  const correctIndex =
    typeof payload.correct_index === "number" ? payload.correct_index : payload.correct;

  if (!Array.isArray(payload.grid) || !Array.isArray(payload.options)) {
    throw new Error("Puzzle payload is missing required fields.");
  }

  return {
    seed: payload.seed ?? null,
    grid: payload.grid,
    missing_position: missingPosition,
    options: payload.options.map((option, index) => normalizeOption(option, index)),
    correct_index: correctIndex,
    explanation: payload.explanation ?? "",
    difficulty: typeof payload.difficulty === "number" ? payload.difficulty : 0,
    difficulty_profile: payload.difficulty_profile ?? null,
  };
}

function withApiBase(path) {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (!configured) {
    return path;
  }
  const normalizedBase = configured.replace(/\/$/, "");
  return `${normalizedBase}${path}`;
}

async function requestJson(path, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, timeoutMs);
  const started = performance.now();

  try {
    const response = await fetch(withApiBase(path), {
      ...options,
      signal: controller.signal,
    });
    const durationMs = performance.now() - started;

    if (!response.ok) {
      logger.warn("api.request_failed", {
        path,
        status: response.status,
        duration_ms: Number(durationMs.toFixed(1)),
      });
      throw new Error(`Request failed with status ${response.status}`);
    }

    const json = await response.json();
    return { json, durationMs };
  } catch (error) {
    const isAbort = error instanceof DOMException && error.name === "AbortError";
    if (isAbort) {
      logger.error("api.timeout", { path, timeout_ms: timeoutMs });
      throw new ApiTimeoutError(timeoutMs);
    }

    logger.error("api.exception", {
      path,
      message: error instanceof Error ? error.message : "Unknown error",
    });
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export async function fetchPuzzle(seed = null) {
  const requestBody = seed === null ? {} : { seed };
  try {
    const { json, durationMs } = await requestJson(
      GENERATE_ENDPOINT,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      },
      DEFAULT_TIMEOUT_MS
    );
    const normalized = normalizePuzzle(json);
    return {
      ...normalized,
      response_time_ms: Number(durationMs.toFixed(1)),
    };
  } catch (error) {
    logger.warn("api.fallback_demo", {
      reason: error instanceof Error ? error.message : "unknown",
    });
    const { json, durationMs } = await requestJson(DEMO_ENDPOINT, {}, DEFAULT_TIMEOUT_MS);
    const normalized = normalizePuzzle(json);
    return {
      ...normalized,
      response_time_ms: Number(durationMs.toFixed(1)),
    };
  }
}

export async function fetchSystemHealth() {
  const [{ json: health }, { json: version }] = await Promise.all([
    requestJson(HEALTH_ENDPOINT),
    requestJson(VERSION_ENDPOINT),
  ]);

  return {
    backend_status: health.status ?? "unknown",
    backend_version: version.application_version ?? version.version ?? "unknown",
    backend_name: version.app_name ?? "Cognera",
    backend_commit_sha: version.commit_sha ?? "unknown",
    backend_git_branch: version.git_branch ?? "unknown",
    backend_build_timestamp: version.build_timestamp ?? "unknown",
    deployment_environment: import.meta.env.VITE_DEPLOY_ENV ?? "local",
    frontend_version: __APP_VERSION__,
    frontend_mode: import.meta.env.MODE,
  };
}

export async function fetchVersionInfo() {
  const { json: version } = await requestJson(VERSION_ENDPOINT);
  return {
    app_name: version.app_name ?? "Cognera",
    application_version: version.application_version ?? version.version ?? "unknown",
    commit_sha: version.commit_sha ?? "unknown",
    git_branch: version.git_branch ?? "unknown",
    build_timestamp: version.build_timestamp ?? "unknown",
  };
}