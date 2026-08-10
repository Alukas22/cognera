import { fetchPuzzle, fetchSystemHealth } from "./api.js";
import { createGameState, isWithinBeginnerProgressionBand, selectOption, setHealthData, setPuzzle } from "./game.js";
import { createLogger } from "./logger.js";
import { renderApp, renderHealthView } from "./ui.js";
import "./styles.css";

const logger = createLogger("frontend.app");
const root = document.getElementById("root");

let state = createGameState();

function routeView() {
  return window.location.pathname === "/health-check" ? "health" : "game";
}

function setView(view) {
  state = {
    ...state,
    view,
    errorMessage: view === "game" ? state.errorMessage : "",
    healthError: view === "health" ? state.healthError : "",
  };
}

function render() {
  if (!root) {
    return;
  }

  if (state.view === "health") {
    renderHealthView(root, state, {
      onRefreshHealth: loadHealth,
      onBackToGame: () => navigateTo("/"),
    });
    return;
  }

  renderApp(root, state, {
    onGeneratePuzzle: loadPuzzle,
    onNextPuzzle: loadPuzzle,
    onSelectOption: handleSelectOption,
    onRetry: loadPuzzle,
    onOpenHealth: () => navigateTo("/health-check"),
  });
}

async function loadPuzzle() {
  state = {
    ...state,
    view: "game",
    loading: true,
    appLoading: false,
    errorMessage: "",
  };
  render();

  try {
    const nextPuzzleNumber = state.puzzleNumber + 1;
    const attemptLimit = nextPuzzleNumber <= 3 ? 10 : 6;
    const uiLanguage = "sv";
    let bestPuzzle = null;

    for (let attempt = 0; attempt < attemptLimit; attempt++) {
      const seed = (nextPuzzleNumber * 1_000_003 + attempt * 7_919) % 1_000_000_000;
      const puzzle = await fetchPuzzle(seed, uiLanguage);

      if (bestPuzzle === null || puzzle.difficulty < bestPuzzle.difficulty) {
        bestPuzzle = puzzle;
      }

      if (isWithinBeginnerProgressionBand(puzzle.difficulty, nextPuzzleNumber)) {
        bestPuzzle = puzzle;
        break;
      }
    }

    state = setPuzzle(state, bestPuzzle);
  } catch (error) {
    logger.error("puzzle.load_failed", {
      message: error instanceof Error ? error.message : "Unknown error",
    });
    state = {
      ...state,
      loading: false,
      appLoading: false,
      errorMessage: "Det gick inte att ladda en uppgift just nu.",
    };
  }

  render();
}

async function loadHealth() {
  state = {
    ...state,
    view: "health",
    appLoading: true,
    loading: false,
    healthError: "",
  };
  render();

  try {
    const health = await fetchSystemHealth();
    state = setHealthData(state, health);
  } catch (error) {
    logger.error("health.load_failed", {
      message: error instanceof Error ? error.message : "Unknown error",
    });
    state = {
      ...state,
      appLoading: false,
      healthError: "Det gick inte att ladda driftsinformationen.",
    };
  }

  render();
}

function handleSelectOption(index) {
  state = selectOption(state, index);
  render();
}

function navigateTo(path) {
  window.history.pushState({}, "", path);
  syncRoute();
}

function syncRoute() {
  const view = routeView();
  setView(view);
  render();

  if (view === "health" && state.health === null && !state.appLoading) {
    void loadHealth();
    return;
  }

  if (view === "game" && state.puzzle === null && !state.loading) {
    void loadPuzzle();
  }
}

window.addEventListener("popstate", syncRoute);
window.addEventListener("DOMContentLoaded", syncRoute);
