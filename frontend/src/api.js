/**
 * API access layer for frontend gameplay.
 * Uses the production puzzle endpoint and preserves compatibility with
 * legacy demo payloads if fallback is needed.
 */

const GENERATE_ENDPOINT = "/matrix/generate";
const DEMO_ENDPOINT = "/matrix/demo";

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

export async function fetchPuzzle(seed = null) {
  const requestBody = seed === null ? {} : { seed };
  const response = await fetch(GENERATE_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody),
  });

  if (response.ok) {
    const payload = await response.json();
    return normalizePuzzle(payload);
  }

  const fallback = await fetch(DEMO_ENDPOINT);
  if (!fallback.ok) {
    throw new Error("Puzzle request failed.");
  }
  const payload = await fallback.json();
  return normalizePuzzle(payload);
}