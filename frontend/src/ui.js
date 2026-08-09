/**
 * Presentation layer for the playable Cognera experience.
 */

import { formatDuration, getAccuracy, getAverageDifficulty } from "./game.js";

function renderFigure(figure) {
  if (!figure) {
    return "";
  }
  return `${figure.shape} • ${figure.rotation}° • ${figure.size} • ${figure.color}`;
}

function matrixCell(cell, isMissing) {
  const content = isMissing
    ? "?"
    : `
      <span class="cell-shape">${cell.shape}</span>
      <span class="cell-meta">${cell.rotation}°</span>
      <span class="cell-meta">${cell.size}</span>
      <span class="cell-meta">${cell.color}</span>
    `;

  return `<div class="matrix-cell ${isMissing ? "matrix-cell--missing" : ""}">${content}</div>`;
}

function optionButton(state, option, index) {
  const isSelected = state.selectedIndex === index;
  const isCorrect = index === state.puzzle.correct_index;

  let optionClass = "option-button";
  if (state.isResolved && isCorrect) {
    optionClass += " option-button--correct";
  }
  if (state.isResolved && isSelected && !isCorrect) {
    optionClass += " option-button--incorrect";
  }
  if (isSelected) {
    optionClass += " option-button--selected";
  }

  return `
    <button
      class="${optionClass}"
      data-action="select-option"
      data-index="${index}"
      ${state.isResolved || state.loading ? "disabled" : ""}
    >
      <span class="option-label">${option.label}</span>
      <span class="option-value">${renderFigure(option)}</span>
    </button>
  `;
}

function feedbackBlock(state) {
  if (!state.isResolved || !state.puzzle) {
    return "<p class='feedback feedback--neutral'>Select an answer to submit this puzzle.</p>";
  }

  const statusClass = state.lastResult === "correct" ? "feedback--correct" : "feedback--incorrect";
  const statusText = state.lastResult === "correct" ? "Correct" : "Incorrect";
  const correctOption = state.puzzle.options[state.puzzle.correct_index];

  return `
    <div class="feedback-wrap">
      <p class="feedback ${statusClass}">${statusText}</p>
      <p class="feedback-answer">Correct answer: ${correctOption.label} — ${renderFigure(correctOption)}</p>
      <p class="feedback-explanation">${state.puzzle.explanation}</p>
    </div>
  `;
}

export function renderApp(root, state, handlers) {
  const elapsed = formatDuration(Date.now() - state.sessionStartedAt);
  const puzzleDifficulty = state.puzzle ? state.puzzle.difficulty.toFixed(2) : "--";
  const accuracy = `${(getAccuracy(state) * 100).toFixed(1)}%`;
  const averageDifficulty = getAverageDifficulty(state).toFixed(2);

  root.innerHTML = `
    <main class="app-shell">
      <header class="app-header card">
        <div class="brand">
          <div class="brand-mark">◈</div>
          <div>
            <h1>Cognera</h1>
            <p class="tagline">Cognitive Matrix Assessment</p>
          </div>
        </div>
        <div class="header-controls">
          <button class="action-button" data-action="generate">Generate Puzzle</button>
          <div class="pill">Difficulty ${puzzleDifficulty}</div>
          <div class="pill" data-role="timer">${elapsed}</div>
        </div>
      </header>

      <section class="stats-grid">
        <article class="card stat">
          <span>Current Score</span>
          <strong>${state.correctAnswers}</strong>
        </article>
        <article class="card stat">
          <span>Puzzle Number</span>
          <strong>${state.puzzleNumber}</strong>
        </article>
        <article class="card stat">
          <span>Accuracy</span>
          <strong>${accuracy}</strong>
        </article>
        <article class="card stat">
          <span>Average Difficulty</span>
          <strong>${averageDifficulty}</strong>
        </article>
      </section>

      <section class="card board-panel">
        <h2>Matrix</h2>
        ${
          state.puzzle
            ? `<div class="matrix-board">${state.puzzle.grid
                .map((row, rowIndex) =>
                  row
                    .map((cell, colIndex) =>
                      matrixCell(
                        cell,
                        rowIndex === state.puzzle.missing_position[0] &&
                          colIndex === state.puzzle.missing_position[1]
                      )
                    )
                    .join("")
                )
                .join("")}</div>`
            : "<p class='empty-state'>Generate a puzzle to begin.</p>"
        }
      </section>

      <section class="card answer-panel">
        <div class="answer-header">
          <h2>Answer Options</h2>
          <button
            class="ghost-button"
            data-action="next"
            ${state.loading ? "disabled" : ""}
          >
            Next Puzzle
          </button>
        </div>
        ${
          state.errorMessage
            ? `<p class="feedback feedback--incorrect">${state.errorMessage}</p>`
            : ""
        }
        ${
          state.loading
            ? "<p class='feedback feedback--neutral'>Loading puzzle...</p>"
            : ""
        }
        ${
          state.puzzle
            ? `<div class="options-grid">${state.puzzle.options
                .map((option, index) => optionButton(state, option, index))
                .join("")}</div>`
            : ""
        }
        ${feedbackBlock(state)}
      </section>
    </main>
  `;

  root.querySelector("[data-action='generate']")?.addEventListener("click", handlers.onGeneratePuzzle);
  root.querySelector("[data-action='next']")?.addEventListener("click", handlers.onNextPuzzle);

  root.querySelectorAll("[data-action='select-option']").forEach((node) => {
    node.addEventListener("click", () => {
      const index = Number(node.getAttribute("data-index"));
      handlers.onSelectOption(index);
    });
  });
}