/**
 * Presentation layer for the playable Cognera experience.
 */

import { formatDuration, getAccuracy, getAverageDifficulty } from "./game.js";
import { FigureRenderer } from "./figureSvg.js";

function matrixCell(cell, isMissing) {
  const content = isMissing
    ? "?"
    : `
      <div class="figure-wrap" data-testid="matrix-figure">
        ${FigureRenderer(cell, { sizePx: 132, className: "matrix-figure-svg" })}
      </div>
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
      data-testid="option-${index}"
      aria-label="Alternativ ${option.label}"
      data-index="${index}"
      ${state.isResolved || state.loading ? "disabled" : ""}
    >
      <span class="option-visual" data-testid="option-visual-${index}">
        ${FigureRenderer(option, { sizePx: 112, className: "option-figure-svg" })}
      </span>
    </button>
  `;
}

function feedbackBlock(state) {
  if (!state.isResolved || !state.puzzle) {
    return "<p class='feedback feedback--neutral'>Välj ett alternativ för att lämna in uppgiften.</p>";
  }

  const statusClass = state.lastResult === "correct" ? "feedback--correct" : "feedback--incorrect";
  const statusText = state.lastResult === "correct" ? "Rätt" : "Fel";
  const correctOption = state.puzzle.options[state.puzzle.correct_index];

  return `
    <div class="feedback-wrap">
      <p class="feedback ${statusClass}">${statusText}</p>
      <p class="feedback-answer" data-testid="correct-answer">Rätt svar: ${correctOption.label}</p>
      <div class="feedback-visual">${FigureRenderer(correctOption, { sizePx: 96, className: "feedback-figure-svg" })}</div>
      <p class="feedback-explanation" data-testid="explanation-text">${state.puzzle.explanation}</p>
    </div>
  `;
}

function loadingOverlay(state) {
  if (!state.loading && !state.appLoading) {
    return "";
  }
  return "<div class='loading-overlay'><div class='spinner'></div><span>Laddar…</span></div>";
}

function errorPanel(state) {
  if (!state.errorMessage) {
    return "";
  }
  return `
    <section class="card fatal-panel" data-role="fatal-error">
      <h2>Anslutningsproblem</h2>
      <p>${state.errorMessage}</p>
      <button class="action-button" data-action="retry">Försök igen</button>
    </section>
  `;
}

function diagnosticsPill(state) {
  if (!state.developerMode || state.lastResponseTimeMs === null) {
    return "";
  }
  return `<div class="pill" data-role="latency">API ${state.lastResponseTimeMs.toFixed(1)}ms</div>`;
}

export function renderHealthView(root, state, handlers) {
  const health = state.health;
  root.innerHTML = `
    <main class="app-shell health-shell">
      <header class="app-header card">
        <div class="brand">
          <div class="brand-mark">◈</div>
          <div>
            <h1>Cognera driftskontroll</h1>
            <p class="tagline">Status och diagnostik</p>
          </div>
        </div>
        <div class="header-controls">
          <button class="ghost-button" data-action="back-to-game">Till spelet</button>
          <button class="action-button" data-action="refresh-health">Uppdatera</button>
        </div>
      </header>
      ${
        state.healthError
          ? `<section class="card fatal-panel"><h2>Driftskontrollen misslyckades</h2><p>${state.healthError}</p></section>`
          : ""
      }
      <section class="card health-grid">
        <article class="health-item"><span>Bakgrundsstatus</span><strong>${health ? health.backend_status : "--"}</strong></article>
        <article class="health-item"><span>Bakgrundsversion</span><strong>${health ? health.backend_version : "--"}</strong></article>
        <article class="health-item"><span>Applikation</span><strong>${health ? health.backend_name : "--"}</strong></article>
        <article class="health-item"><span>Framkantsversion</span><strong>${health ? health.frontend_version : "--"}</strong></article>
        <article class="health-item"><span>Framkantsläge</span><strong>${health ? health.frontend_mode : "--"}</strong></article>
        <article class="health-item"><span>Miljö</span><strong>${health ? health.deployment_environment : "--"}</strong></article>
      </section>
      ${loadingOverlay(state)}
    </main>
  `;

  root.querySelector("[data-action='refresh-health']")?.addEventListener("click", handlers.onRefreshHealth);
  root.querySelector("[data-action='back-to-game']")?.addEventListener("click", handlers.onBackToGame);
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
            <p class="tagline">Kognitiv matrisbedömning</p>
          </div>
        </div>
        <div class="header-controls">
          <button class="action-button" data-action="generate" data-testid="generate-button">Skapa uppgift</button>
          <div class="pill">Svårighet ${puzzleDifficulty}</div>
          <div class="pill" data-role="timer">${elapsed}</div>
          ${diagnosticsPill(state)}
          <button class="ghost-button" data-action="open-health">Drift</button>
        </div>
      </header>

      ${errorPanel(state)}

      <section class="stats-grid">
        <article class="card stat">
          <span>Poäng</span>
          <strong data-testid="current-score">${state.correctAnswers}</strong>
        </article>
        <article class="card stat">
          <span>Uppgiftsnummer</span>
          <strong data-testid="puzzle-number">${state.puzzleNumber}</strong>
        </article>
        <article class="card stat">
          <span>Träffsäkerhet</span>
          <strong>${accuracy}</strong>
        </article>
        <article class="card stat">
          <span>Genomsnittlig svårighet</span>
          <strong>${averageDifficulty}</strong>
        </article>
      </section>

      <section class="play-area">
        <section class="card board-panel">
          <h2>Matris</h2>
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
              : "<p class='empty-state'>Skapa en uppgift för att börja.</p>"
          }
        </section>

        <section class="card answer-panel">
          <div class="answer-header">
            <h2>Svarsalternativ</h2>
            <button
              class="ghost-button"
              data-action="next"
              data-testid="next-puzzle-button"
              ${state.loading ? "disabled" : ""}
            >
              Nästa uppgift
            </button>
          </div>
          ${
            state.errorMessage
              ? `<p class="feedback feedback--incorrect">${state.errorMessage}</p>`
              : ""
          }
          ${
            state.loading
              ? "<p class='feedback feedback--neutral'>Laddar uppgift...</p>"
              : ""
          }
          ${
            state.puzzle
              ? `<div class="options-grid" data-testid="options-grid">${state.puzzle.options
                  .map((option, index) => optionButton(state, option, index))
                  .join("")}</div>`
              : ""
          }
          <div data-testid="feedback-block">${feedbackBlock(state)}</div>
        </section>
      </section>
      ${loadingOverlay(state)}
    </main>
  `;

  root.querySelector("[data-action='generate']")?.addEventListener("click", handlers.onGeneratePuzzle);
  root.querySelector("[data-action='next']")?.addEventListener("click", handlers.onNextPuzzle);
  root.querySelector("[data-action='retry']")?.addEventListener("click", handlers.onRetry);
  root.querySelector("[data-action='open-health']")?.addEventListener("click", handlers.onOpenHealth);

  root.querySelectorAll("[data-action='select-option']").forEach((node) => {
    node.addEventListener("click", () => {
      const index = Number(node.getAttribute("data-index"));
      handlers.onSelectOption(index);
    });
  });
}