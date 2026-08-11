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
    targetDifficulty: 0.14,
    correctStreak: 0,
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
  const nextCorrectStreak = isCorrect ? state.correctStreak + 1 : 0;
  return {
    ...state,
    selectedIndex: index,
    isResolved: true,
    lastResult: isCorrect ? "correct" : "incorrect",
    totalAnswered: state.totalAnswered + 1,
    correctAnswers: state.correctAnswers + (isCorrect ? 1 : 0),
    totalDifficulty: state.totalDifficulty + state.puzzle.difficulty,
    correctStreak: nextCorrectStreak,
    targetDifficulty: nextTargetDifficulty(state.targetDifficulty, isCorrect, nextCorrectStreak),
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

const BEGINNER_PROGRESSIONS = [
  { min: 0.06, max: 0.22 },
  { min: 0.10, max: 0.28 },
  { min: 0.14, max: 0.34 },
  { min: 0.18, max: 0.40 },
  { min: 0.24, max: 0.48 },
  { min: 0.30, max: 0.56 },
  { min: 0.36, max: 0.64 },
];

export function getBeginnerProgressionBand(puzzleNumber) {
  const index = Math.max(0, Math.min(BEGINNER_PROGRESSIONS.length - 1, puzzleNumber - 1));
  return BEGINNER_PROGRESSIONS[index];
}

export function isWithinBeginnerProgressionBand(difficulty, puzzleNumber) {
  const band = getBeginnerProgressionBand(puzzleNumber);
  return difficulty >= band.min && difficulty <= band.max;
}

function nextTargetDifficulty(currentTarget, isCorrect, correctStreak) {
  if (!isCorrect) {
    return clampDifficulty(currentTarget - 0.02);
  }

  const streakBonus = Math.min(0.015, Math.max(0, correctStreak - 1) * 0.005);
  return clampDifficulty(currentTarget + 0.03 + streakBonus);
}

function clampDifficulty(value) {
  return Math.min(0.64, Math.max(0.06, Number(value.toFixed(3))));
}