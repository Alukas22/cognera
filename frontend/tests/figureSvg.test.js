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
    expect(triangle).toContain("<polygon points=\"50,18 82,79 18,79\"");
    expect(diamond).toContain("<polygon points=\"50,14 86,50 50,86 14,50\"");
  });

  it("renders rotation, encoded visual tone and size via transform and fill", () => {
    const rendered = renderFigureSvg(
      { shape: "triangle", rotation: 270, size: "large", color: "red" },
      { sizePx: 80, className: "custom-svg" }
    );

    expect(rendered).toContain("class=\"custom-svg\"");
    expect(rendered).toContain("width=\"80\"");
    expect(rendered).toContain("rotate(270)");
    expect(rendered).toContain("scale(0.96)");
    expect(rendered).toContain("tone-red");
    expect(rendered).toContain("url(#tone-red)");
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
            <defs><pattern id=\"tone-orange\" width=\"12\" height=\"12\" patternUnits=\"userSpaceOnUse\" patternTransform=\"rotate(45)\"><rect width=\"12\" height=\"12\" fill=\"#f4efe6\" /><line x1=\"0\" y1=\"0\" x2=\"0\" y2=\"12\" stroke=\"#111111\" stroke-width=\"2.2\" /></pattern></defs>
            <rect x=\"6\" y=\"6\" width=\"88\" height=\"88\" rx=\"12\" fill=\"#fcfcf8\" stroke=\"#d8d6cd\" stroke-width=\"1.2\" />
            <g transform=\"translate(50 50) rotate(90) scale(0.62) translate(-50 -50)\">
              <rect x=\"23\" y=\"23\" width=\"54\" height=\"54\" fill=\"url(#tone-orange)\" stroke=\"#111111\" stroke-width=\"3.6\" rx=\"2\" />
            </g>
          </svg>
        "
    `);
  });
});
