import { beforeEach, describe, expect, it, vi } from "vitest";

const figureRendererSpy = vi.fn(() => "<svg data-testid='mock-figure'></svg>");

vi.mock("../src/figureSvg.js", () => ({
  FigureRenderer: (...args) => figureRendererSpy(...args),
}));

import { renderApp } from "../src/ui.js";

const samplePuzzle = {
  grid: [
    [
      { shape: "circle", rotation: 0, size: "small", color: "black" },
      { shape: "square", rotation: 90, size: "medium", color: "blue" },
      { shape: "triangle", rotation: 180, size: "large", color: "red" },
    ],
    [
      { shape: "diamond", rotation: 270, size: "small", color: "green" },
      { shape: "circle", rotation: 0, size: "medium", color: "black" },
      { shape: "square", rotation: 90, size: "large", color: "blue" },
    ],
    [
      { shape: "triangle", rotation: 180, size: "small", color: "red" },
      { shape: "diamond", rotation: 270, size: "medium", color: "green" },
      null,
    ],
  ],
  missing_position: [2, 2],
  options: [
    { label: "A", shape: "circle", rotation: 0, size: "small", color: "black", is_correct: false },
    { label: "B", shape: "square", rotation: 90, size: "medium", color: "blue", is_correct: false },
    { label: "C", shape: "triangle", rotation: 180, size: "large", color: "red", is_correct: false },
    { label: "D", shape: "diamond", rotation: 270, size: "small", color: "green", is_correct: true },
    { label: "E", shape: "circle", rotation: 90, size: "small", color: "black", is_correct: false },
    { label: "F", shape: "square", rotation: 180, size: "medium", color: "blue", is_correct: false },
  ],
  correct_index: 3,
  difficulty: 0.5,
  explanation: "sample",
};

function makeState() {
  return {
    view: "game",
    loading: false,
    appLoading: false,
    errorMessage: "",
    healthError: "",
    sessionStartedAt: 0,
    puzzleStartedAt: 0,
    puzzle: samplePuzzle,
    puzzleNumber: 1,
    totalAnswered: 0,
    correctAnswers: 0,
    totalDifficulty: 0,
    lastResponseTimeMs: null,
    developerMode: false,
    health: null,
    selectedIndex: null,
    isResolved: true,
    lastResult: "correct",
  };
}

describe("ui svg answer options", () => {
  beforeEach(() => {
    figureRendererSpy.mockClear();
  });

  it("uses FigureRenderer for matrix cells and answer options", () => {
    const root = {
      innerHTML: "",
      querySelector: () => null,
      querySelectorAll: () => [],
    };

    renderApp(root, makeState(), {
      onGeneratePuzzle: () => {},
      onNextPuzzle: () => {},
      onSelectOption: () => {},
      onRetry: () => {},
      onOpenHealth: () => {},
    });

    expect(figureRendererSpy).toHaveBeenCalled();
    expect(root.innerHTML).toContain("data-testid='mock-figure'");
    expect(root.innerHTML).not.toContain("option-label");

    const matrixCall = figureRendererSpy.mock.calls.find((call) => call[1]?.className === "matrix-figure-svg");
    const optionCall = figureRendererSpy.mock.calls.find((call) => call[1]?.className === "option-figure-svg");
    const feedbackCall = figureRendererSpy.mock.calls.find((call) => call[1]?.className === "feedback-figure-svg");

    expect(matrixCall?.[1]?.sizePx).toBeGreaterThanOrEqual(132);
    expect(optionCall?.[1]?.sizePx).toBeGreaterThanOrEqual(112);
    expect(feedbackCall?.[1]?.sizePx).toBeGreaterThanOrEqual(96);
  });
});
