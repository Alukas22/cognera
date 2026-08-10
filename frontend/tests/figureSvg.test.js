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
    expect(triangle).toContain('class="figure-shell"');
    expect(triangle).toContain("<path d=\"M50 20 L50 80");
    expect(diamond).toContain("<polygon");
    expect(diamond).toContain("stroke-opacity=\"0.55\"");
  });

  it("renders rotation, encoded visual tone and size via transform and fill", () => {
    const rendered = renderFigureSvg(
      { shape: "triangle", rotation: 270, size: "large", color: "red" },
      { sizePx: 80, className: "custom-svg" }
    );

    expect(rendered).toContain("class=\"custom-svg\"");
    expect(rendered).toContain("width=\"80\"");
    expect(rendered).toContain("rotate(270)");
    expect(rendered).toContain("scale(0.94)");
    expect(rendered).toContain("figure-shell");
    expect(rendered).toContain("<polygon points=\"50.00,34.00 63.86,58.00 36.14,58.00\"");
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
            <rect x=\"6\" y=\"6\" width=\"88\" height=\"88\" rx=\"12\" fill=\"#f4ede4\" stroke=\"#d8d3c5\" stroke-width=\"1.2\" />
            <g transform=\"translate(50 50) rotate(90) scale(0.66) translate(-50 -50)\">
              <rect class=\"figure-shell\" x=\"21\" y=\"21\" width=\"58\" height=\"58\" rx=\"2\" fill=\"#fffaf6\" stroke=\"#121212\" stroke-width=\"3.2\" />
              
              <path d=\"M35 21 V79 M65 21 V79 M21 35 H79 M21 65 H79\" stroke=\"#64584c\" stroke-width=\"1.3\" stroke-opacity=\"0.55\" />
              
              <path d=\"M44 46 L50 54 L56 46\" fill=\"none\" stroke=\"#121212\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\" />
              <path d=\"M40 24 L50 16 L60 24\" fill=\"none\" stroke=\"#64584c\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" />
            </g>
          </svg>
        "
    `);
  });
});
