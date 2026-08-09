/**
 * Game state domain layer.
 * Keeps gameplay transitions deterministic and independently testable.
 */

export function createGameState(now = Date.now()) {
  return {
    view: "game",
    loading: false,
    appLoading: false,
    errorMessage: "",
    healthError: "",
    sessionStartedAt: now,
    puzzleStartedAt: now,
    puzzle: null,
    puzzleNumber: 0,
    totalAnswered: 0,
    correctAnswers: 0,
    totalDifficulty: 0,
    lastResponseTimeMs: null,
    developerMode: import.meta.env.DEV,
    health: null,
    selectedIndex: null,
    isResolved: false,
    lastResult: null,
  };
}

export function resetSession(state, now = Date.now()) {
  return {
    ...createGameState(now),
    loading: state.loading,
  };
}

export function setPuzzle(state, puzzle, now = Date.now()) {
  return {
    ...state,
    loading: false,
    appLoading: false,
    errorMessage: "",
    puzzle,
    puzzleNumber: state.puzzleNumber + 1,
    selectedIndex: null,
    isResolved: false,
    lastResult: null,
    lastResponseTimeMs:
      typeof puzzle.response_time_ms === "number" ? puzzle.response_time_ms : null,
    puzzleStartedAt: now,
  };
}

export function setHealthData(state, health) {
  return {
    ...state,
    appLoading: false,
    healthError: "",
    health,
  };
}

export function selectOption(state, index) {
  if (!state.puzzle || state.isResolved) {
    return state;
  }

  const isCorrect = index === state.puzzle.correct_index;
  return {
    ...state,
    selectedIndex: index,
    isResolved: true,
    lastResult: isCorrect ? "correct" : "incorrect",
    totalAnswered: state.totalAnswered + 1,
    correctAnswers: state.correctAnswers + (isCorrect ? 1 : 0),
    totalDifficulty: state.totalDifficulty + state.puzzle.difficulty,
  };
}

export function getAccuracy(state) {
  if (state.totalAnswered === 0) {
    return 0;
  }
  return state.correctAnswers / state.totalAnswered;
}

export function getAverageDifficulty(state) {
  if (state.totalAnswered === 0) {
    return 0;
  }
  return state.totalDifficulty / state.totalAnswered;
}

export function formatDuration(durationMs) {
  const totalSeconds = Math.floor(durationMs / 1000);
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}