import { describe, expect, it } from "vitest";

import { renderFigureSvg } from "../src/figureSvg.js";

describe("renderFigureSvg", () => {
  it("renders an SVG for each supported shape", () => {
    const circle = renderFigureSvg({ shape: "circle", rotation: 0, size: "medium", color: "red" });
    const square = renderFigureSvg({ shape: "square", rotation: 90, size: "large", color: "blue" });
    const triangle = renderFigureSvg({ shape: "triangle", rotation: 180, size: "small", color: "green" });
    const diamond = renderFigureSvg({ shape: "diamond", rotation: 270, size: "medium", color: "purple" });

    expect(circle).toContain("<circle");
    expect(square).toContain("<rect");
    expect(triangle).toContain("<polygon points=\"50,16 84,80 16,80\"");
    expect(diamond).toContain("<polygon points=\"50,12 88,50 50,88 12,50\"");
  });

  it("renders rotation, color and size via transform and fill", () => {
    const rendered = renderFigureSvg(
      { shape: "triangle", rotation: 270, size: "large", color: "red" },
      { sizePx: 80, className: "custom-svg" }
    );

    expect(rendered).toContain("class=\"custom-svg\"");
    expect(rendered).toContain("width=\"80\"");
    expect(rendered).toContain("rotate(270)");
    expect(rendered).toContain("scale(0.96)");
    expect(rendered).toContain("#dc2626");
  });

  it("matches snapshot for deterministic visual markup", () => {
    const rendered = renderFigureSvg({
      shape: "square",
      rotation: 90,
      size: "small",
      color: "orange",
    });

    expect(rendered).toMatchInlineSnapshot(`
      "
          <svg
            class=\"figure-svg\"
            viewBox=\"0 0 100 100\"
            width=\"64\"
            height=\"64\"
            aria-hidden=\"true\"
            focusable=\"false\"
            role=\"img\"
          >
            <g transform=\"translate(50 50) rotate(90) scale(0.62) translate(-50 -50)\">
              <rect x=\"22\" y=\"22\" width=\"56\" height=\"56\" fill=\"#f97316\" stroke=\"#0f172a\" stroke-opacity=\"0.34\" stroke-width=\"4\" rx=\"4\" />
            </g>
          </svg>
        "
    `);
  });
});
