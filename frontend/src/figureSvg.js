const TONE_BY_NAME = {
  black: { fill: "#111111", stroke: "#111111", pattern: null },
  white: { fill: "#fbfbf8", stroke: "#111111", pattern: null },
  red: { fill: "#f5f5f0", stroke: "#111111", pattern: "diag" },
  blue: { fill: "#ecece6", stroke: "#111111", pattern: "cross" },
  green: { fill: "#ededeb", stroke: "#111111", pattern: "dots" },
  yellow: { fill: "#f6f3ea", stroke: "#111111", pattern: "grid" },
  orange: { fill: "#f4efe6", stroke: "#111111", pattern: "wide-diag" },
  purple: { fill: "#efedf2", stroke: "#111111", pattern: "bars" },
  pink: { fill: "#f6ecef", stroke: "#111111", pattern: "diag" },
  gray: { fill: "#d8d8d2", stroke: "#111111", pattern: null },
  grey: { fill: "#d8d8d2", stroke: "#111111", pattern: null },
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

function defsMarkup(strokeColor, toneKey, patternName) {
  const patternId = `tone-${toneKey}`;
  if (!patternName) {
    return { defs: "", fill: TONE_BY_NAME[toneKey]?.fill ?? "#d8d8d2" };
  }

  const base = TONE_BY_NAME[toneKey]?.fill ?? "#f1f1ec";
  const patternMarkup = {
    diag: `<pattern id="${patternId}" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="8" fill="${base}" /><line x1="0" y1="0" x2="0" y2="8" stroke="${strokeColor}" stroke-width="1.6" /></pattern>`,
    "wide-diag": `<pattern id="${patternId}" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="12" height="12" fill="${base}" /><line x1="0" y1="0" x2="0" y2="12" stroke="${strokeColor}" stroke-width="2.2" /></pattern>`,
    cross: `<pattern id="${patternId}" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="${base}" /><path d="M0 0 L10 10 M10 0 L0 10" stroke="${strokeColor}" stroke-width="1.3" /></pattern>`,
    dots: `<pattern id="${patternId}" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="${base}" /><circle cx="2.5" cy="2.5" r="1.2" fill="${strokeColor}" /><circle cx="7.5" cy="7.5" r="1.2" fill="${strokeColor}" /></pattern>`,
    grid: `<pattern id="${patternId}" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="${base}" /><path d="M0 0 H10 M0 5 H10 M0 10 H10 M0 0 V10 M5 0 V10 M10 0 V10" stroke="${strokeColor}" stroke-width="0.8" /></pattern>`,
    bars: `<pattern id="${patternId}" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="${base}" /><path d="M2 0 V8 M6 0 V8" stroke="${strokeColor}" stroke-width="1.4" /></pattern>`,
  }[patternName];

  return {
    defs: `<defs>${patternMarkup}</defs>`,
    fill: `url(#${patternId})`,
  };
}

function shapeMarkup(shape, fillColor, strokeColor) {
  if (shape === "circle") {
    return `<circle cx="50" cy="50" r="27" fill="${fillColor}" stroke="${strokeColor}" stroke-width="3.6" />`;
  }
  if (shape === "square") {
    return `<rect x="23" y="23" width="54" height="54" fill="${fillColor}" stroke="${strokeColor}" stroke-width="3.6" rx="2" />`;
  }
  if (shape === "triangle") {
    return `<polygon points="50,18 82,79 18,79" fill="${fillColor}" stroke="${strokeColor}" stroke-width="3.6" />`;
  }
  return `<polygon points="50,14 86,50 50,86 14,50" fill="${fillColor}" stroke="${strokeColor}" stroke-width="3.6" />`;
}

export function FigureRenderer(figure, options = {}) {
  if (!figure) {
    return "";
  }

  const rotation = Number.isFinite(figure.rotation) ? figure.rotation : 0;
  const shape = normalizeShape(figure.shape);
  const toneKey = String(figure.color || "").toLowerCase();
  const tone = TONE_BY_NAME[toneKey] ?? TONE_BY_NAME.gray;
  const scale = SCALE_BY_SIZE[String(figure.size || "").toLowerCase()] ?? SCALE_BY_SIZE.medium;
  const sizePx = typeof options.sizePx === "number" ? options.sizePx : 64;
  const className = options.className ?? "figure-svg";
  const { defs, fill } = defsMarkup(tone.stroke, toneKey in TONE_BY_NAME ? toneKey : "gray", tone.pattern);

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
      ${defs}
      <rect x="6" y="6" width="88" height="88" rx="12" fill="#fcfcf8" stroke="#d8d6cd" stroke-width="1.2" />
      <g transform="translate(50 50) rotate(${rotation}) scale(${scale}) translate(-50 -50)">
        ${shapeMarkup(shape, fill, tone.stroke)}
      </g>
    </svg>
  `;
}

export function renderFigureSvg(figure, options = {}) {
  return FigureRenderer(figure, options);
}
