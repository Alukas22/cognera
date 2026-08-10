"""Derived component hierarchy for compositional Raven-style figure reasoning."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Figure


_SHELL_BY_SHAPE = {
    "circle": "round_shell",
    "square": "quadrilateral_shell",
    "triangle": "triangular_shell",
    "diamond": "diamond_shell",
    "pentagon": "pentagonal_shell",
    "hexagon": "hexagonal_shell",
}

_REGION_BY_SHAPE = {
    "circle": "radial_regions",
    "square": "grid_regions",
    "triangle": "triad_regions",
    "diamond": "diagonal_regions",
    "pentagon": "radial_regions",
    "hexagon": "hex_regions",
}

_CORNERS_BY_SHAPE = {
    "circle": 0,
    "square": 4,
    "triangle": 3,
    "diamond": 4,
    "pentagon": 5,
    "hexagon": 6,
}

_INNER_BY_COLOR = {
    "black": "diamond_core",
    "white": "circle_core",
    "red": "triangle_core",
    "blue": "square_core",
}

_MOTIF_BY_COLOR = {
    "black": "bars",
    "white": "dot",
    "red": "slash",
    "blue": "cross",
}

_REPEAT_BY_SIZE = {
    "small": 1,
    "medium": 2,
    "large": 3,
}

_SIZE_BY_REPEAT = {value: key for key, value in _REPEAT_BY_SIZE.items()}

_COLOR_BY_INNER_MOTIF = {
    ("diamond_core", "bars"): "black",
    ("circle_core", "dot"): "white",
    ("triangle_core", "slash"): "red",
    ("square_core", "cross"): "blue",
}

_SHAPE_BY_SHELL = {value: key for key, value in _SHELL_BY_SHAPE.items()}


@dataclass(frozen=True)
class FigureComponents:
    outer_shell: str
    internal_regions: str
    corners: int
    internal_lines: str
    directional_marker: str
    repeated_motif: str
    repeated_count: int
    nested_figure: str
    nested_depth: int
    symmetry_group: str
    orientation: int

    def signature(self) -> tuple[object, ...]:
        return (
            self.outer_shell,
            self.internal_regions,
            self.corners,
            self.internal_lines,
            self.directional_marker,
            self.repeated_motif,
            self.repeated_count,
            self.nested_figure,
            self.nested_depth,
            self.symmetry_group,
            self.orientation,
        )


def derive_components(figure: Figure) -> FigureComponents:
    shape = figure.shape.lower()
    color = figure.color.lower()
    size = figure.size.lower()

    outer_shell = _SHELL_BY_SHAPE.get(shape, "diamond_shell")
    internal_regions = _REGION_BY_SHAPE.get(shape, "diagonal_regions")
    corners = _CORNERS_BY_SHAPE.get(shape, 4)
    nested_figure = _INNER_BY_COLOR.get(color, "diamond_core")
    repeated_motif = _MOTIF_BY_COLOR.get(color, "bars")
    repeated_count = _REPEAT_BY_SIZE.get(size, 2)
    nested_depth = 0 if size == "small" else 1 if size == "medium" else 2
    internal_lines = {
        "grid_regions": "orthogonal_lines",
        "triad_regions": "triangular_lines",
        "diagonal_regions": "diagonal_lines",
        "hex_regions": "hex_lines",
        "radial_regions": "radial_lines",
    }.get(internal_regions, "diagonal_lines")
    directional_marker = {
        "bars": "axial_marker",
        "dot": "point_marker",
        "slash": "diagonal_marker",
        "cross": "cross_marker",
    }.get(repeated_motif, "axial_marker")
    symmetry_group = {
        "circle": "radial",
        "triangle": "triangular",
        "square": "axial",
        "diamond": "diagonal",
        "pentagon": "radial",
        "hexagon": "axial",
    }.get(shape, "axial")

    return FigureComponents(
        outer_shell=outer_shell,
        internal_regions=internal_regions,
        corners=corners,
        internal_lines=internal_lines,
        directional_marker=directional_marker,
        repeated_motif=repeated_motif,
        repeated_count=repeated_count,
        nested_figure=nested_figure,
        nested_depth=nested_depth,
        symmetry_group=symmetry_group,
        orientation=figure.rotation,
    )


def component_distance(first: Figure, second: Figure) -> int:
    left = derive_components(first)
    right = derive_components(second)
    return sum(
        [
            left.outer_shell != right.outer_shell,
            left.internal_regions != right.internal_regions,
            left.directional_marker != right.directional_marker,
            left.repeated_motif != right.repeated_motif,
            left.repeated_count != right.repeated_count,
            left.nested_figure != right.nested_figure,
            left.nested_depth != right.nested_depth,
            left.orientation != right.orientation,
        ]
    )


def describe_component_change(rule_name: str) -> str:
    return {
        "rotation": "rotates the directional marker system",
        "size": "adds or removes repeated internal motifs",
        "count": "changes how many repeated internal components appear",
        "shape": "changes the outer shell and partition layout",
        "position": "moves a structural component to a new logical slot",
        "mirror": "reflects the internal construction across an axis",
        "color": "replaces the nested figure and motif family",
    }.get(rule_name, "changes the figure's internal construction")


def structure_summary(figure: Figure) -> str:
    components = derive_components(figure)
    return (
        f"{figure.shape} shell, {components.internal_regions}, {components.repeated_count} motif group, "
        f"{components.nested_figure}, orientation {components.orientation}\N{DEGREE SIGN}"
    )


def shell_from_components(components: FigureComponents) -> str:
    return _SHAPE_BY_SHELL.get(components.outer_shell, "diamond")


def color_from_components(components: FigureComponents) -> str:
    return _COLOR_BY_INNER_MOTIF.get((components.nested_figure, components.repeated_motif), "black")


def size_from_components(components: FigureComponents) -> str:
    repeat_count = max(1, min(3, components.repeated_count))
    return _SIZE_BY_REPEAT[repeat_count]