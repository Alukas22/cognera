import { describe, expect, it } from "vitest";

import {
  createGameState,
  getBeginnerProgressionBand,
  getAccuracy,
  getAverageDifficulty,
  isWithinBeginnerProgressionBand,
  resetSession,
  selectOption,
  setPuzzle,
} from "../src/game.js";

const samplePuzzle = {
  grid: [
    [{ shape: "circle", rotation: 0, size: "small", color: "black" }, { shape: "circle", rotation: 90, size: "small", color: "black" }, { shape: "circle", rotation: 180, size: "small", color: "black" }],
    [{ shape: "circle", rotation: 270, size: "small", color: "black" }, { shape: "circle", rotation: 0, size: "small", color: "black" }, { shape: "circle", rotation: 90, size: "small", color: "black" }],
    [{ shape: "circle", rotation: 180, size: "small", color: "black" }, { shape: "circle", rotation: 270, size: "small", color: "black" }, null],
  ],
  missing_position: [2, 2],
  options: [
    { label: "A", shape: "circle", rotation: 0, size: "small", color: "black", is_correct: false },
    { label: "B", shape: "circle", rotation: 90, size: "small", color: "black", is_correct: false },
    { label: "C", shape: "circle", rotation: 180, size: "small", color: "black", is_correct: false },
    { label: "D", shape: "circle", rotation: 270, size: "small", color: "black", is_correct: true },
    { label: "E", shape: "square", rotation: 270, size: "small", color: "black", is_correct: false },
    { label: "F", shape: "triangle", rotation: 270, size: "small", color: "black", is_correct: false },
  ],
  correct_index: 3,
  difficulty: 0.62,
  explanation: "Rotation advances by ninety degrees.",
};

describe("game state", () => {
  it("locks puzzle after selection and tracks correct answer", () => {
    let state = createGameState(0);
    state = setPuzzle(state, samplePuzzle, 1000);
    state = selectOption(state, 3);

    expect(state.isResolved).toBe(true);
    expect(state.correctAnswers).toBe(1);
    expect(state.totalAnswered).toBe(1);
    expect(state.lastResult).toBe("correct");
  });

  it("ignores repeated answer selection after puzzle is resolved", () => {
    let state = createGameState(0);
    state = setPuzzle(state, samplePuzzle, 1000);
    state = selectOption(state, 1);
    const afterFirstSelection = state;
    state = selectOption(state, 3);

    expect(state).toEqual(afterFirstSelection);
    expect(state.lastResult).toBe("incorrect");
  });

  it("calculates accuracy and average difficulty", () => {
    let state = createGameState(0);
    state = setPuzzle(state, { ...samplePuzzle, difficulty: 0.4 }, 1000);
    state = selectOption(state, 3);
    state = setPuzzle(state, { ...samplePuzzle, difficulty: 0.8 }, 2000);
    state = selectOption(state, 1);

    expect(getAccuracy(state)).toBe(0.5);
    expect(getAverageDifficulty(state)).toBeCloseTo(0.6, 8);
  });

  it("resets session cleanly", () => {
    let state = createGameState(0);
    state = setPuzzle(state, samplePuzzle, 1000);
    state = selectOption(state, 3);
    state = resetSession(state, 5000);

    expect(state.correctAnswers).toBe(0);
    expect(state.totalAnswered).toBe(0);
    expect(state.puzzle).toBeNull();
    expect(state.puzzleNumber).toBe(0);
  });

  it("ramps difficulty bands upward during the beginner progression", () => {
    const firstBand = getBeginnerProgressionBand(1);
    const laterBand = getBeginnerProgressionBand(6);

    expect(firstBand.min).toBeLessThan(laterBand.min);
    expect(firstBand.max).toBeLessThan(laterBand.max);
    expect(isWithinBeginnerProgressionBand(0.2, 1)).toBe(true);
    expect(isWithinBeginnerProgressionBand(0.6, 1)).toBe(false);
  });

  it("keeps the beginner band sensible across early puzzles", () => {
    for (let puzzleNumber = 1; puzzleNumber <= 3; puzzleNumber++) {
      const band = getBeginnerProgressionBand(puzzleNumber);
      expect(band.min).toBeLessThan(band.max);
      expect(band.min).toBeGreaterThanOrEqual(0);
      expect(band.max).toBeLessThanOrEqual(1);
    }
  });
});