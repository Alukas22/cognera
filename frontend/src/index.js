import "./styles.css";
import { fetchPuzzle, fetchSystemHealth } from "./api.js";
import {
  createGameState,
  resetSession,
  setHealthData,
  setPuzzle,
  selectOption,
  formatDuration,
} from "./game.js";
import { renderApp, renderHealthView } from "./ui.js";
import { createLogger } from "./logger.js";

const root = document.getElementById("root");
let state = createGameState();
const logger = createLogger("frontend.app");

function initialView() {
  return window.location.pathname === "/health-check" ? "health" : "game";
}

state = { ...state, view: initialView() };

window.addEventListener("error", (event) => {
  logger.error("app.unhandled_error", {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
  });
});

window.addEventListener("unhandledrejection", (event) => {
  logger.error("app.unhandled_promise", {
    reason: String(event.reason ?? "unknown"),
  });
});

function updateView() {
  if (state.view === "health") {
    renderHealthView(root, state, {
      onRefreshHealth: async () => {
        await loadHealth();
      },
      onBackToGame: async () => {
        window.history.pushState({}, "", "/");
        state = { ...state, view: "game", healthError: "" };
        updateView();
      },
    });
    return;
  }

  renderApp(root, state, {
    onGeneratePuzzle: async () => {
      state = resetSession(state);
      await loadNextPuzzle();
    },
    onNextPuzzle: async () => {
      await loadNextPuzzle();
    },
    onSelectOption: (index) => {
      state = selectOption(state, index);
      updateView();
    },
    onRetry: async () => {
      await loadNextPuzzle();
    },
    onOpenHealth: async () => {
      window.history.pushState({}, "", "/health-check");
      state = { ...state, view: "health" };
      updateView();
      await loadHealth();
    },
  });
}

async function loadHealth() {
  state = { ...state, appLoading: true, healthError: "" };
  updateView();
  try {
    const health = await fetchSystemHealth();
    state = setHealthData(state, health);
    logger.info("app.health_loaded", {
      backend_status: health.backend_status,
      backend_version: health.backend_version,
    });
  } catch (error) {
    state = {
      ...state,
      appLoading: false,
      healthError: "Unable to reach backend health endpoints. Check connectivity and retry.",
    };
    logger.error("app.health_failed", {
      message: error instanceof Error ? error.message : "unknown",
    });
  }
  updateView();
}

async function loadNextPuzzle() {
  state = { ...state, loading: true, errorMessage: "" };
  updateView();
  try {
    const puzzle = await fetchPuzzle();
    state = setPuzzle(state, puzzle);
    logger.info("app.puzzle_loaded", {
      puzzle_number: state.puzzleNumber,
      difficulty: puzzle.difficulty,
      latency_ms: puzzle.response_time_ms,
    });
  } catch (error) {
    logger.error("app.puzzle_load_failed", {
      message: error instanceof Error ? error.message : "unknown",
    });
    state = {
      ...state,
      loading: false,
      errorMessage:
        "Cognera cannot reach the puzzle service right now. Please retry in a few seconds.",
    };
  }
  updateView();
}

window.setInterval(() => {
  if (!state.sessionStartedAt) {
    return;
  }
  const elapsed = Date.now() - state.sessionStartedAt;
  const timerNode = document.querySelector("[data-role='timer']");
  if (timerNode) {
    timerNode.textContent = formatDuration(elapsed);
  }
}, 1000);

window.addEventListener("DOMContentLoaded", async () => {
  updateView();
  if (state.view === "health") {
    await loadHealth();
    return;
  }
  await loadNextPuzzle();
});
