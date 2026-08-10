const TONE_BY_NAME = {
  black: { panel: "#f3efe4", shell: "#fffdf7", ink: "#121212", accent: "#1f1f1f" },
  white: { panel: "#f7f5ed", shell: "#ffffff", ink: "#121212", accent: "#6b665d" },
  red: { panel: "#f4ece6", shell: "#fffaf4", ink: "#121212", accent: "#4b4b4b" },
  blue: { panel: "#ecece6", shell: "#fbfaf5", ink: "#121212", accent: "#50555a" },
  green: { panel: "#eceee5", shell: "#fcfcf7", ink: "#121212", accent: "#4f564d" },
  yellow: { panel: "#f2eee0", shell: "#fffdf4", ink: "#121212", accent: "#5f5744" },
  orange: { panel: "#f4ede4", shell: "#fffaf6", ink: "#121212", accent: "#64584c" },
  purple: { panel: "#efeaf0", shell: "#fcf8fc", ink: "#121212", accent: "#5d5562" },
  pink: { panel: "#f4eaed", shell: "#fff8fa", ink: "#121212", accent: "#65535b" },
  gray: { panel: "#ece7de", shell: "#fcfaf4", ink: "#121212", accent: "#5d5a52" },
  grey: { panel: "#ece7de", shell: "#fcfaf4", ink: "#121212", accent: "#5d5a52" },
};

const SCALE_BY_SIZE = {
  small: 0.66,
  medium: 0.81,
  large: 0.94,
};

const REPEAT_BY_SIZE = {
  small: 1,
  medium: 2,
  large: 3,
};

const INNER_SHAPE_BY_COLOR = {
  black: "diamond",
  white: "circle",
  red: "triangle",
  blue: "square",
  green: "diamond",
  yellow: "circle",
  orange: "triangle",
  purple: "square",
  pink: "triangle",
  gray: "diamond",
  grey: "diamond",
};

const MOTIF_BY_COLOR = {
  black: "bars",
  white: "dot",
  red: "slash",
  blue: "cross",
  green: "nodes",
  yellow: "beam",
  orange: "chevron",
  purple: "ring",
  pink: "slash",
  gray: "bars",
  grey: "bars",
};

const REGION_BY_SHAPE = {
  circle: "radial",
  square: "grid",
  triangle: "triad",
  diamond: "diagonal",
  pentagon: "radial",
  hexagon: "hex",
  octagon: "grid",
  line: "beam",
  arc: "radial",
};

function polygonPoints(sides, radius, rotationDeg = -90) {
  const points = [];
  for (let index = 0; index < sides; index += 1) {
    const theta = ((Math.PI * 2 * index) / sides) + ((rotationDeg * Math.PI) / 180);
    const x = 50 + (radius * Math.cos(theta));
    const y = 50 + (radius * Math.sin(theta));
    points.push(`${x.toFixed(2)},${y.toFixed(2)}`);
  }
  return points.join(" ");
}

function normalizeShape(shape) {
  if (typeof shape !== "string") {
    return "diamond";
  }
  const value = shape.toLowerCase();
  if (["circle", "square", "triangle", "diamond", "pentagon", "hexagon", "octagon", "line", "arc"].includes(value)) {
    return value;
  }
  return "diamond";
}

function shapeGeometry(shape, stroke, fill, className = "") {
  const classAttr = className ? ` class="${className}"` : "";
  if (shape === "circle") {
    return `<circle${classAttr} cx="50" cy="50" r="30" fill="${fill}" stroke="${stroke}" stroke-width="3.2" />`;
  }
  if (shape === "square") {
    return `<rect${classAttr} x="21" y="21" width="58" height="58" rx="2" fill="${fill}" stroke="${stroke}" stroke-width="3.2" />`;
  }
  if (shape === "triangle") {
    return `<polygon${classAttr} points="${polygonPoints(3, 34, -90)}" fill="${fill}" stroke="${stroke}" stroke-width="3.2" />`;
  }
  if (shape === "diamond") {
    return `<polygon${classAttr} points="50,14 86,50 50,86 14,50" fill="${fill}" stroke="${stroke}" stroke-width="3.2" />`;
  }
  if (shape === "pentagon") {
    return `<polygon${classAttr} points="${polygonPoints(5, 32, -90)}" fill="${fill}" stroke="${stroke}" stroke-width="3.2" />`;
  }
  if (shape === "hexagon") {
    return `<polygon${classAttr} points="${polygonPoints(6, 32, -90)}" fill="${fill}" stroke="${stroke}" stroke-width="3.2" />`;
  }
  if (shape === "octagon") {
    return `<polygon${classAttr} points="${polygonPoints(8, 31, -90)}" fill="${fill}" stroke="${stroke}" stroke-width="3.2" />`;
  }
  if (shape === "line") {
    return `<line${classAttr} x1="22" y1="50" x2="78" y2="50" stroke="${stroke}" stroke-width="7" stroke-linecap="round" />`;
  }
  if (shape === "arc") {
    return `<path${classAttr} d="M24 66 A28 28 0 0 1 76 66" fill="none" stroke="${stroke}" stroke-width="6" stroke-linecap="round" />`;
  }
  return `<polygon${classAttr} points="50,14 86,50 50,86 14,50" fill="${fill}" stroke="${stroke}" stroke-width="3.2" />`;
}

function innerShapeMarkup(shape, stroke) {
  const innerFill = "none";
  if (shape === "circle") {
    return `<circle cx="50" cy="50" r="15" fill="${innerFill}" stroke="${stroke}" stroke-width="2.2" />`;
  }
  if (shape === "square") {
    return `<rect x="37" y="37" width="26" height="26" rx="1.5" fill="${innerFill}" stroke="${stroke}" stroke-width="2.2" />`;
  }
  if (shape === "triangle") {
    return `<polygon points="${polygonPoints(3, 16, -90)}" fill="${innerFill}" stroke="${stroke}" stroke-width="2.2" />`;
  }
  return `<polygon points="50,33 67,50 50,67 33,50" fill="${innerFill}" stroke="${stroke}" stroke-width="2.2" />`;
}

function regionMarkup(region, accent) {
  if (region === "grid") {
    return '<path d="M35 21 V79 M65 21 V79 M21 35 H79 M21 65 H79" stroke="' + accent + '" stroke-width="1.3" stroke-opacity="0.55" />';
  }
  if (region === "diagonal") {
    return '<path d="M24 24 L76 76 M76 24 L24 76" stroke="' + accent + '" stroke-width="1.5" stroke-opacity="0.55" />';
  }
  if (region === "triad") {
    return '<path d="M50 20 L50 80 M24 68 L76 68 M50 20 L24 68 M50 20 L76 68" stroke="' + accent + '" stroke-width="1.25" stroke-opacity="0.5" />';
  }
  if (region === "hex") {
    return '<path d="M24 50 H76 M37 28 L63 72 M63 28 L37 72" stroke="' + accent + '" stroke-width="1.35" stroke-opacity="0.5" />';
  }
  if (region === "beam") {
    return '<path d="M26 42 H74 M26 58 H74" stroke="' + accent + '" stroke-width="1.4" stroke-opacity="0.55" />';
  }
  return '<path d="M50 20 V80 M20 50 H80 M29 29 L71 71 M71 29 L29 71" stroke="' + accent + '" stroke-width="1.2" stroke-opacity="0.38" />';
}

function repeatedMotifMarkup(kind, repeatCount, stroke, accent) {
  const positions = {
    1: [[50, 50]],
    2: [[39, 50], [61, 50]],
    3: [[50, 38], [39, 58], [61, 58]],
  }[repeatCount] ?? [[50, 50]];

  return positions
    .map(([cx, cy]) => {
      if (kind === "dot") {
        return `<circle cx="${cx}" cy="${cy}" r="3.2" fill="${stroke}" />`;
      }
      if (kind === "bars") {
        return `<path d="M${cx - 4} ${cy - 6} V${cy + 6} M${cx + 4} ${cy - 6} V${cy + 6}" stroke="${stroke}" stroke-width="1.8" stroke-linecap="round" />`;
      }
      if (kind === "slash") {
        return `<path d="M${cx - 6} ${cy + 6} L${cx + 6} ${cy - 6}" stroke="${stroke}" stroke-width="2" stroke-linecap="round" />`;
      }
      if (kind === "cross") {
        return `<path d="M${cx - 5} ${cy} H${cx + 5} M${cx} ${cy - 5} V${cy + 5}" stroke="${stroke}" stroke-width="1.8" stroke-linecap="round" />`;
      }
      if (kind === "nodes") {
        return `<circle cx="${cx - 4}" cy="${cy}" r="2.3" fill="${accent}" /><circle cx="${cx + 4}" cy="${cy}" r="2.3" fill="${stroke}" />`;
      }
      if (kind === "beam") {
        return `<path d="M${cx - 6} ${cy} H${cx + 6}" stroke="${stroke}" stroke-width="2.2" stroke-linecap="round" /><path d="M${cx - 2} ${cy - 5} V${cy + 5}" stroke="${accent}" stroke-width="1.6" stroke-linecap="round" />`;
      }
      if (kind === "chevron") {
        return `<path d="M${cx - 6} ${cy - 4} L${cx} ${cy + 4} L${cx + 6} ${cy - 4}" fill="none" stroke="${stroke}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" />`;
      }
      if (kind === "ring") {
        return `<circle cx="${cx}" cy="${cy}" r="5.2" fill="none" stroke="${stroke}" stroke-width="1.7" /><circle cx="${cx}" cy="${cy}" r="1.4" fill="${accent}" />`;
      }
      return `<circle cx="${cx}" cy="${cy}" r="3.2" fill="${stroke}" />`;
    })
    .join("");
}

function directionalMarkup(kind, stroke, accent, sizeKey) {
  if (kind === "bars") {
    return `<path d="M50 20 V32 M50 68 V80" stroke="${accent}" stroke-width="2" stroke-linecap="round" />`;
  }
  if (kind === "slash") {
    return `<path d="M33 26 L67 12" stroke="${accent}" stroke-width="2" stroke-linecap="round" /><path d="M33 74 L67 88" stroke="${accent}" stroke-width="2" stroke-linecap="round" />`;
  }
  if (kind === "cross") {
    return `<path d="M28 50 H40 M60 50 H72" stroke="${accent}" stroke-width="2" stroke-linecap="round" />`;
  }
  if (kind === "nodes") {
    return `<circle cx="50" cy="22" r="2.5" fill="${stroke}" /><circle cx="50" cy="78" r="2.5" fill="${accent}" />`;
  }
  if (kind === "beam") {
    return `<path d="M30 24 H70" stroke="${accent}" stroke-width="2" stroke-linecap="round" />`;
  }
  if (kind === "chevron") {
    return `<path d="M40 24 L50 16 L60 24" fill="none" stroke="${accent}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />`;
  }
  if (kind === "ring") {
    return sizeKey === "large"
      ? `<circle cx="50" cy="50" r="24" fill="none" stroke="${accent}" stroke-width="1.8" stroke-dasharray="3 3" />`
      : "";
  }
  return `<circle cx="50" cy="22" r="2.5" fill="${accent}" />`;
}

function cutoutMarkup(shape, panel) {
  if (shape === "circle") {
    return `<path d="M37 19 H63" stroke="${panel}" stroke-width="6" stroke-linecap="round" />`;
  }
  if (shape === "square") {
    return `<path d="M36 21 H64" stroke="${panel}" stroke-width="6" stroke-linecap="square" />`;
  }
  if (shape === "triangle") {
    return `<path d="M42 25 H58" stroke="${panel}" stroke-width="6" stroke-linecap="round" />`;
  }
  return `<path d="M40 20 H60" stroke="${panel}" stroke-width="6" stroke-linecap="round" />`;
}

function buildComposition(figure) {
  const colorKey = String(figure.color || "gray").toLowerCase();
  const tone = TONE_BY_NAME[colorKey] ?? TONE_BY_NAME.gray;
  const outerShape = normalizeShape(figure.shape);
  const sizeKey = String(figure.size || "medium").toLowerCase();
  return {
    tone,
    outerShape,
    innerShape: INNER_SHAPE_BY_COLOR[colorKey] ?? "diamond",
    motifKind: MOTIF_BY_COLOR[colorKey] ?? "bars",
    region: REGION_BY_SHAPE[outerShape] ?? "radial",
    repeatCount: REPEAT_BY_SIZE[sizeKey] ?? 2,
    nested: sizeKey !== "small",
    cutout: sizeKey === "large",
    scale: SCALE_BY_SIZE[sizeKey] ?? SCALE_BY_SIZE.medium,
  };
}

export function FigureRenderer(figure, options = {}) {
  if (!figure) {
    return "";
  }

  const rotation = Number.isFinite(figure.rotation) ? figure.rotation : 0;
  const composition = buildComposition(figure);
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
      <rect x="6" y="6" width="88" height="88" rx="12" fill="${composition.tone.panel}" stroke="#d8d3c5" stroke-width="1.2" />
      <g transform="translate(50 50) rotate(${rotation}) scale(${composition.scale}) translate(-50 -50)">
        ${shapeGeometry(composition.outerShape, composition.tone.ink, composition.tone.shell, "figure-shell")}
        ${composition.cutout ? cutoutMarkup(composition.outerShape, composition.tone.panel) : ""}
        ${regionMarkup(composition.region, composition.tone.accent)}
        ${composition.nested ? innerShapeMarkup(composition.innerShape, composition.tone.ink) : ""}
        ${repeatedMotifMarkup(composition.motifKind, composition.repeatCount, composition.tone.ink, composition.tone.accent)}
        ${directionalMarkup(composition.motifKind, composition.tone.ink, composition.tone.accent, String(figure.size || "medium").toLowerCase())}
      </g>
    </svg>
  `;
}

export function renderFigureSvg(figure, options = {}) {
  return FigureRenderer(figure, options);
}
