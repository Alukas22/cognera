"""Deterministic symbolic figure library for Cognera.

This module is intentionally isolated from puzzle generation code.
It defines reusable figure specifications and SVG rendering utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import cos, pi, sin
from typing import Any


PALETTE = (
    "#111827",
    "#1D4ED8",
    "#DC2626",
    "#059669",
    "#7C3AED",
    "#EA580C",
    "#0F766E",
    "#BE123C",
)


class FigureFamily(StrEnum):
    BASIC_PRIMITIVE = "basic_primitive"
    COMPOSITE_FIGURE = "composite_figure"
    NESTED_FIGURE = "nested_figure"
    DECORATIVE_ELEMENT = "decorative_element"
    CONNECTOR = "connector"
    RADIAL_STRUCTURE = "radial_structure"
    CONCENTRIC_STRUCTURE = "concentric_structure"


@dataclass(frozen=True)
class FigureSpec:
    """Serializable figure definition with deterministic parameters."""

    figure_id: str
    name: str
    family: FigureFamily
    svg_markup: str
    parameters: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "figure_id": self.figure_id,
            "name": self.name,
            "family": self.family.value,
            "svg_markup": self.svg_markup,
            "parameters": self.parameters,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FigureSpec":
        return cls(
            figure_id=str(payload["figure_id"]),
            name=str(payload["name"]),
            family=FigureFamily(str(payload["family"])),
            svg_markup=str(payload["svg_markup"]),
            parameters=dict(payload["parameters"]),
        )


def _svg_wrapper(markup: str, size: int = 128) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 100 100" role="img" aria-label="Cognera figure">'
        f"{markup}</svg>"
    )


def _regular_polygon(cx: float, cy: float, radius: float, sides: int, rotation_deg: float = 0.0) -> str:
    points: list[str] = []
    for i in range(sides):
        theta = (2 * pi * i / sides) + (rotation_deg * pi / 180.0)
        x = cx + radius * cos(theta)
        y = cy + radius * sin(theta)
        points.append(f"{x:.2f},{y:.2f}")
    return " ".join(points)


def _primitive_markup(shape: str, color: str, rotation: int, scale: float) -> str:
    group_open = f'<g transform="translate(50 50) rotate({rotation}) scale({scale:.3f}) translate(-50 -50)">'
    group_close = "</g>"
    stroke = "#0f172a"
    if shape == "circle":
        node = f'<circle cx="50" cy="50" r="26" fill="{color}" stroke="{stroke}" stroke-width="3" />'
    elif shape == "square":
        node = f'<rect x="24" y="24" width="52" height="52" rx="4" fill="{color}" stroke="{stroke}" stroke-width="3" />'
    elif shape == "triangle":
        node = f'<polygon points="{_regular_polygon(50, 50, 32, 3, -90)}" fill="{color}" stroke="{stroke}" stroke-width="3" />'
    elif shape == "diamond":
        node = f'<polygon points="50,16 84,50 50,84 16,50" fill="{color}" stroke="{stroke}" stroke-width="3" />'
    elif shape == "pentagon":
        node = f'<polygon points="{_regular_polygon(50, 50, 30, 5, -90)}" fill="{color}" stroke="{stroke}" stroke-width="3" />'
    elif shape == "hexagon":
        node = f'<polygon points="{_regular_polygon(50, 50, 30, 6, -90)}" fill="{color}" stroke="{stroke}" stroke-width="3" />'
    elif shape == "octagon":
        node = f'<polygon points="{_regular_polygon(50, 50, 30, 8, -90)}" fill="{color}" stroke="{stroke}" stroke-width="3" />'
    elif shape == "line":
        node = f'<line x1="20" y1="50" x2="80" y2="50" stroke="{color}" stroke-width="8" stroke-linecap="round" />'
    elif shape == "arc":
        node = f'<path d="M 20 60 A 30 30 0 0 1 80 60" fill="none" stroke="{color}" stroke-width="6" stroke-linecap="round" />'
    else:
        node = f'<circle cx="50" cy="50" r="20" fill="{color}" stroke="{stroke}" stroke-width="3" />'
    return _svg_wrapper(group_open + node + group_close)


def _composite_markup(shape_a: str, shape_b: str, color_a: str, color_b: str, rotation: int) -> str:
    base = _primitive_markup(shape_a, color_a, 0, 1.0)
    overlay = _primitive_markup(shape_b, color_b, rotation, 0.52)
    base_body = base.split(">", 1)[1].rsplit("</svg>", 1)[0]
    overlay_body = overlay.split(">", 1)[1].rsplit("</svg>", 1)[0]
    return _svg_wrapper(base_body + overlay_body)


def _nested_markup(outer: str, inner: str, outer_color: str, inner_color: str, ring_stroke: int) -> str:
    outer_svg = _primitive_markup(outer, outer_color, 0, 1.0)
    inner_svg = _primitive_markup(inner, inner_color, 0, 0.45)
    outer_body = outer_svg.split(">", 1)[1].rsplit("</svg>", 1)[0]
    inner_body = inner_svg.split(">", 1)[1].rsplit("</svg>", 1)[0]
    ring = f'<circle cx="50" cy="50" r="40" fill="none" stroke="#1f2937" stroke-width="{ring_stroke}" stroke-opacity="0.35" />'
    return _svg_wrapper(ring + outer_body + inner_body)


def _decorative_markup(base_shape: str, color: str, decoration: str, rotation: int) -> str:
    base = _primitive_markup(base_shape, color, rotation, 0.9)
    body = base.split(">", 1)[1].rsplit("</svg>", 1)[0]
    if decoration == "dots":
        deco = "".join(
            f'<circle cx="{x}" cy="{y}" r="3" fill="#111827" fill-opacity="0.7" />'
            for x, y in ((20, 20), (80, 20), (20, 80), (80, 80))
        )
    elif decoration == "crosshair":
        deco = (
            '<line x1="50" y1="14" x2="50" y2="86" stroke="#111827" stroke-width="2" />'
            '<line x1="14" y1="50" x2="86" y2="50" stroke="#111827" stroke-width="2" />'
        )
    elif decoration == "ring":
        deco = '<circle cx="50" cy="50" r="42" fill="none" stroke="#111827" stroke-width="3" stroke-dasharray="4 4" />'
    else:
        deco = '<path d="M20 80 C35 30, 65 30, 80 80" fill="none" stroke="#111827" stroke-width="3" />'
    return _svg_wrapper(body + deco)


def _connector_markup(connector_kind: str, color: str, node_shape: str) -> str:
    node = _primitive_markup(node_shape, color, 0, 0.26)
    node_body = node.split(">", 1)[1].rsplit("</svg>", 1)[0]
    if connector_kind == "bridge":
        lines = (
            '<line x1="20" y1="50" x2="80" y2="50" stroke="#111827" stroke-width="4" />'
            '<g transform="translate(-22 0)">' + node_body + "</g>"
            '<g transform="translate(22 0)">' + node_body + "</g>"
        )
    elif connector_kind == "triangle":
        lines = (
            '<line x1="50" y1="18" x2="20" y2="78" stroke="#111827" stroke-width="3" />'
            '<line x1="50" y1="18" x2="80" y2="78" stroke="#111827" stroke-width="3" />'
            '<line x1="20" y1="78" x2="80" y2="78" stroke="#111827" stroke-width="3" />'
            '<g transform="translate(0 -24)">' + node_body + "</g>"
            '<g transform="translate(-30 36)">' + node_body + "</g>"
            '<g transform="translate(30 36)">' + node_body + "</g>"
        )
    else:
        lines = (
            '<line x1="20" y1="20" x2="80" y2="20" stroke="#111827" stroke-width="3" />'
            '<line x1="20" y1="50" x2="80" y2="50" stroke="#111827" stroke-width="3" />'
            '<line x1="20" y1="80" x2="80" y2="80" stroke="#111827" stroke-width="3" />'
            '<g transform="translate(-22 -30)">' + node_body + "</g>"
            '<g transform="translate(22 -30)">' + node_body + "</g>"
            '<g transform="translate(-22 0)">' + node_body + "</g>"
            '<g transform="translate(22 0)">' + node_body + "</g>"
            '<g transform="translate(-22 30)">' + node_body + "</g>"
            '<g transform="translate(22 30)">' + node_body + "</g>"
        )
    return _svg_wrapper(lines)


def _radial_markup(spokes: int, shape: str, color: str) -> str:
    pieces: list[str] = ['<circle cx="50" cy="50" r="6" fill="#111827" />']
    petal = _primitive_markup(shape, color, 0, 0.22)
    petal_body = petal.split(">", 1)[1].rsplit("</svg>", 1)[0]
    for i in range(spokes):
        angle = int(360 * i / spokes)
        pieces.append(
            f'<g transform="translate(50 50) rotate({angle}) translate(0 -30)">{petal_body}</g>'
        )
    return _svg_wrapper("".join(pieces))


def _concentric_markup(rings: int, color: str, accent: str) -> str:
    circles: list[str] = []
    radius = 44
    stroke_width = 3
    for index in range(rings):
        stroke = color if index % 2 == 0 else accent
        circles.append(
            f'<circle cx="50" cy="50" r="{radius}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}" />'
        )
        radius -= 8
    circles.append('<circle cx="50" cy="50" r="4" fill="#111827" />')
    return _svg_wrapper("".join(circles))


def build_figure_catalog() -> tuple[FigureSpec, ...]:
    """Build deterministic catalog of reusable symbolic figures."""

    specs: list[FigureSpec] = []
    counter = 1

    primitive_shapes = ("circle", "square", "triangle", "diamond", "pentagon", "hexagon", "octagon", "line", "arc")
    primitive_rotations = (0, 90, 180)
    primitive_scales = (0.8, 1.0)
    for shape in primitive_shapes:
        for rotation in primitive_rotations:
            for scale in primitive_scales:
                color = PALETTE[(counter - 1) % len(PALETTE)]
                figure_id = f"fig-{counter:03d}"
                specs.append(
                    FigureSpec(
                        figure_id=figure_id,
                        name=f"Primitive {shape} r{rotation} s{scale:.2f}",
                        family=FigureFamily.BASIC_PRIMITIVE,
                        svg_markup=_primitive_markup(shape, color, rotation, scale),
                        parameters={
                            "shape": shape,
                            "rotation": rotation,
                            "scale": scale,
                            "color": color,
                        },
                    )
                )
                counter += 1
                if counter > 54:
                    break
            if counter > 54:
                break
        if counter > 54:
            break

    composite_pairs = [
        ("circle", "triangle"),
        ("square", "circle"),
        ("diamond", "square"),
        ("hexagon", "triangle"),
        ("octagon", "circle"),
        ("pentagon", "diamond"),
        ("triangle", "line"),
        ("circle", "arc"),
    ]
    for pair in composite_pairs:
        for rotation in (0, 90, 180, 270):
            color_a = PALETTE[(counter - 1) % len(PALETTE)]
            color_b = PALETTE[(counter + 2) % len(PALETTE)]
            figure_id = f"fig-{counter:03d}"
            specs.append(
                FigureSpec(
                    figure_id=figure_id,
                    name=f"Composite {pair[0]}-{pair[1]} r{rotation}",
                    family=FigureFamily.COMPOSITE_FIGURE,
                    svg_markup=_composite_markup(pair[0], pair[1], color_a, color_b, rotation),
                    parameters={
                        "base": pair[0],
                        "overlay": pair[1],
                        "rotation": rotation,
                        "base_color": color_a,
                        "overlay_color": color_b,
                    },
                )
            )
            counter += 1

    nested_pairs = [
        ("circle", "circle"),
        ("square", "diamond"),
        ("triangle", "circle"),
        ("hexagon", "triangle"),
        ("octagon", "square"),
    ]
    for outer, inner in nested_pairs:
        for ring_stroke in (2, 4, 6):
            for variant in range(3):
                outer_color = PALETTE[(counter + variant) % len(PALETTE)]
                inner_color = PALETTE[(counter + variant + 3) % len(PALETTE)]
                figure_id = f"fig-{counter:03d}"
                specs.append(
                    FigureSpec(
                        figure_id=figure_id,
                        name=f"Nested {outer}-{inner} v{variant + 1}",
                        family=FigureFamily.NESTED_FIGURE,
                        svg_markup=_nested_markup(outer, inner, outer_color, inner_color, ring_stroke),
                        parameters={
                            "outer": outer,
                            "inner": inner,
                            "ring_stroke": ring_stroke,
                            "variant": variant,
                            "outer_color": outer_color,
                            "inner_color": inner_color,
                        },
                    )
                )
                counter += 1

    for base_shape in ("circle", "square", "triangle", "diamond", "pentagon", "hexagon"):
        for decoration in ("dots", "crosshair", "ring"):
            for rotation in (0, 90, 180, 270):
                color = PALETTE[(counter - 1) % len(PALETTE)]
                figure_id = f"fig-{counter:03d}"
                specs.append(
                    FigureSpec(
                        figure_id=figure_id,
                        name=f"Decorative {base_shape} {decoration} r{rotation}",
                        family=FigureFamily.DECORATIVE_ELEMENT,
                        svg_markup=_decorative_markup(base_shape, color, decoration, rotation),
                        parameters={
                            "base_shape": base_shape,
                            "decoration": decoration,
                            "rotation": rotation,
                            "color": color,
                        },
                    )
                )
                counter += 1

    for connector_kind in ("bridge", "triangle", "ladder"):
        for node_shape in ("circle", "square", "diamond", "triangle", "hexagon"):
            for variant in range(4):
                color = PALETTE[(counter + variant) % len(PALETTE)]
                figure_id = f"fig-{counter:03d}"
                specs.append(
                    FigureSpec(
                        figure_id=figure_id,
                        name=f"Connector {connector_kind} {node_shape} v{variant + 1}",
                        family=FigureFamily.CONNECTOR,
                        svg_markup=_connector_markup(connector_kind, color, node_shape),
                        parameters={
                            "connector_kind": connector_kind,
                            "node_shape": node_shape,
                            "variant": variant,
                            "color": color,
                        },
                    )
                )
                counter += 1

    for spokes in (5, 6, 7, 8, 9, 10):
        for shape in ("circle", "triangle", "diamond", "square", "pentagon"):
            for variant in range(2):
                color = PALETTE[(counter + variant) % len(PALETTE)]
                figure_id = f"fig-{counter:03d}"
                specs.append(
                    FigureSpec(
                        figure_id=figure_id,
                        name=f"Radial {shape} spokes{spokes} v{variant + 1}",
                        family=FigureFamily.RADIAL_STRUCTURE,
                        svg_markup=_radial_markup(spokes, shape, color),
                        parameters={
                            "spokes": spokes,
                            "shape": shape,
                            "variant": variant,
                            "color": color,
                        },
                    )
                )
                counter += 1

    for rings in (3, 4, 5, 6, 7, 8):
        for variant in range(5):
            color = PALETTE[(counter + variant) % len(PALETTE)]
            accent = PALETTE[(counter + variant + 4) % len(PALETTE)]
            figure_id = f"fig-{counter:03d}"
            specs.append(
                FigureSpec(
                    figure_id=figure_id,
                    name=f"Concentric rings{rings} v{variant + 1}",
                    family=FigureFamily.CONCENTRIC_STRUCTURE,
                    svg_markup=_concentric_markup(rings, color, accent),
                    parameters={
                        "rings": rings,
                        "variant": variant,
                        "primary_color": color,
                        "accent_color": accent,
                    },
                )
            )
            counter += 1

    return tuple(specs)


def index_by_id() -> dict[str, FigureSpec]:
    """Return deterministic id -> figure map."""

    return {figure.figure_id: figure for figure in build_figure_catalog()}
