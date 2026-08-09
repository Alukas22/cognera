import "./styles.css";
import { fetchPuzzle } from "./api.js";
import {
  createGameState,
  resetSession,
  setPuzzle,
  selectOption,
  formatDuration,
} from "./game.js";
import { renderApp } from "./ui.js";

const root = document.getElementById("root");
let state = createGameState();

function updateView() {
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
  });
}

async function loadNextPuzzle() {
  state = { ...state, loading: true, errorMessage: "" };
  updateView();
  try {
    const puzzle = await fetchPuzzle();
    state = setPuzzle(state, puzzle);
  } catch (error) {
    state = {
      ...state,
      loading: false,
      errorMessage: "Unable to load puzzle. Please try again.",
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
  await loadNextPuzzle();
});
