const COLOR_BY_NAME = {
  black: "#111827",
  blue: "#2563eb",
  red: "#dc2626",
  green: "#16a34a",
  yellow: "#f59e0b",
  orange: "#f97316",
  purple: "#7c3aed",
  pink: "#db2777",
  gray: "#6b7280",
  grey: "#6b7280",
};

const SCALE_BY_SIZE = {
  small: 0.62,
  medium: 0.78,
  large: 0.96,
};

function normalizeShape(shape) {
  if (typeof shape !== "string") {
    return "diamond";
  }
  const value = shape.toLowerCase();
  if (value === "circle" || value === "square" || value === "triangle" || value === "diamond") {
    return value;
  }
  return "diamond";
}

function shapeMarkup(shape, fillColor) {
  if (shape === "circle") {
    return `<circle cx="50" cy="50" r="28" fill="${fillColor}" stroke="#0f172a" stroke-opacity="0.34" stroke-width="4" />`;
  }
  if (shape === "square") {
    return `<rect x="22" y="22" width="56" height="56" fill="${fillColor}" stroke="#0f172a" stroke-opacity="0.34" stroke-width="4" rx="4" />`;
  }
  if (shape === "triangle") {
    return `<polygon points="50,16 84,80 16,80" fill="${fillColor}" stroke="#0f172a" stroke-opacity="0.34" stroke-width="4" />`;
  }
  return `<polygon points="50,12 88,50 50,88 12,50" fill="${fillColor}" stroke="#0f172a" stroke-opacity="0.34" stroke-width="4" />`;
}

export function renderFigureSvg(figure, options = {}) {
  if (!figure) {
    return "";
  }

  const rotation = Number.isFinite(figure.rotation) ? figure.rotation : 0;
  const shape = normalizeShape(figure.shape);
  const fillColor = COLOR_BY_NAME[String(figure.color || "").toLowerCase()] ?? "#334155";
  const scale = SCALE_BY_SIZE[String(figure.size || "").toLowerCase()] ?? SCALE_BY_SIZE.medium;
  const sizePx = typeof options.sizePx === "number" ? options.sizePx : 64;
  const className = options.className ?? "figure-svg";

  return `
    <svg
      class="${className}"
      viewBox="0 0 100 100"
      width="${sizePx}"
      height="${sizePx}"
      aria-hidden="true"
      focusable="false"
      role="img"
    >
      <g transform="translate(50 50) rotate(${rotation}) scale(${scale}) translate(-50 -50)">
        ${shapeMarkup(shape, fillColor)}
      </g>
    </svg>
  `;
}
