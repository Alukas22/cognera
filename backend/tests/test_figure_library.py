"""Tests for the Epic A symbolic figure library."""

from __future__ import annotations

from xml.etree import ElementTree

from backend.app.figure_library import FigureFamily, FigureSpec, build_figure_catalog, index_by_id


def test_figure_library_has_at_least_300_definitions() -> None:
    figures = build_figure_catalog()
    assert len(figures) >= 300


def test_figure_library_includes_all_required_families() -> None:
    figures = build_figure_catalog()
    present_families = {figure.family for figure in figures}

    assert FigureFamily.BASIC_PRIMITIVE in present_families
    assert FigureFamily.COMPOSITE_FIGURE in present_families
    assert FigureFamily.NESTED_FIGURE in present_families
    assert FigureFamily.DECORATIVE_ELEMENT in present_families
    assert FigureFamily.CONNECTOR in present_families
    assert FigureFamily.RADIAL_STRUCTURE in present_families
    assert FigureFamily.CONCENTRIC_STRUCTURE in present_families


def test_figure_library_is_deterministic() -> None:
    first = build_figure_catalog()
    second = build_figure_catalog()

    assert [item.figure_id for item in first] == [item.figure_id for item in second]
    assert [item.svg_markup for item in first] == [item.svg_markup for item in second]


def test_figure_spec_serialization_round_trip() -> None:
    figures = build_figure_catalog()
    sample = figures[123]

    payload = sample.to_dict()
    restored = FigureSpec.from_dict(payload)

    assert restored == sample


def test_every_figure_renders_valid_svg() -> None:
    for figure in build_figure_catalog():
        root = ElementTree.fromstring(figure.svg_markup)
        assert root.tag.endswith("svg")
        assert root.attrib.get("viewBox") == "0 0 100 100"


def test_index_by_id_maps_all_figures() -> None:
    figures = build_figure_catalog()
    mapping = index_by_id()

    assert len(mapping) == len(figures)
    assert mapping[figures[0].figure_id] == figures[0]
