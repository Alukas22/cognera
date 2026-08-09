const API_URL = "/matrix/demo";

async function fetchMatrixPuzzle() {
  const response = await fetch(API_URL);
  return response.json();
}

function createCell(value) {
  const cell = document.createElement("div");
  cell.style.width = "120px";
  cell.style.height = "120px";
  cell.style.display = "flex";
  cell.style.alignItems = "center";
  cell.style.justifyContent = "center";
  cell.style.border = "1px solid #000";
  cell.style.boxSizing = "border-box";
  cell.style.fontSize = "14px";
  cell.style.whiteSpace = "pre-wrap";
  cell.style.padding = "8px";

  if (value === null) {
    cell.textContent = "";
  } else {
    const lines = [];
    for (const key of ["shape", "rotation", "size", "color"]) {
      if (value[key] !== undefined) {
        lines.push(`${key}: ${value[key]}`);
      }
    }
    cell.textContent = lines.join("\n");
  }

  return cell;
}

function renderPuzzle(puzzle) {
  const root = document.getElementById("root");
  root.innerHTML = "";

  const matrix = document.createElement("div");
  matrix.style.display = "grid";
  matrix.style.gridTemplateColumns = "repeat(3, 120px)";
  matrix.style.gap = "0px";
  matrix.style.marginBottom = "16px";

  puzzle.grid.forEach((row, rowIndex) => {
    row.forEach((cellValue, colIndex) => {
      const isMissing = rowIndex === puzzle.missing[0] && colIndex === puzzle.missing[1];
      matrix.appendChild(createCell(isMissing ? null : cellValue));
    });
  });

  root.appendChild(matrix);

  const optionsHeader = document.createElement("div");
  optionsHeader.textContent = "Select the missing answer:";
  optionsHeader.style.margin = "16px 0 8px";
  root.appendChild(optionsHeader);

  const options = document.createElement("div");
  options.style.display = "grid";
  options.style.gridTemplateColumns = "repeat(2, 1fr)";
  options.style.gap = "8px";
  options.style.marginBottom = "16px";

  const result = document.createElement("div");
  const explanation = document.createElement("div");
  explanation.style.marginTop = "12px";

  puzzle.options.forEach((option, index) => {
    const button = document.createElement("button");
    button.style.padding = "12px";
    const text = [];
    for (const key of ["shape", "rotation", "size", "color"]) {
      if (option[key] !== undefined) {
        text.push(`${key}: ${option[key]}`);
      }
    }
    button.textContent = text.join(" | ");
    button.addEventListener("click", () => {
      result.textContent = index === puzzle.correct ? "Correct!" : "Try again.";
      explanation.textContent = puzzle.explanation;
    });
    options.appendChild(button);
  });

  root.appendChild(options);
  root.appendChild(result);
  root.appendChild(explanation);
}

window.addEventListener("DOMContentLoaded", async () => {
  const puzzle = await fetchMatrixPuzzle();
  renderPuzzle(puzzle);
});
