"""Export figure library SVG assets and documentation."""

from __future__ import annotations

from pathlib import Path

from .library import FigureFamily, build_figure_catalog


def export_library_docs(repo_root: Path) -> tuple[int, Path]:
    figures = build_figure_catalog()
    images_dir = repo_root / "docs" / "figure_library" / "images"
    docs_file = repo_root / "docs" / "FIGURE_LIBRARY.md"

    images_dir.mkdir(parents=True, exist_ok=True)

    for figure in figures:
        (images_dir / f"{figure.figure_id}.svg").write_text(figure.svg_markup, encoding="utf-8")

    grouped: dict[FigureFamily, list] = {family: [] for family in FigureFamily}
    for figure in figures:
        grouped[figure.family].append(figure)

    lines: list[str] = []
    lines.append("# Cognera Figure Library")
    lines.append("")
    lines.append("Status: Epic A implementation")
    lines.append("")
    lines.append(f"Total figure definitions: {len(figures)}")
    lines.append("")
    lines.append("Each figure below is deterministic, serializable, and rendered as SVG.")
    lines.append("")

    for family in FigureFamily:
        family_figures = grouped[family]
        if not family_figures:
            continue
        lines.append(f"## {family.value.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"Count: {len(family_figures)}")
        lines.append("")
        for figure in family_figures:
            lines.append(f"### {figure.figure_id} - {figure.name}")
            lines.append("")
            lines.append(f"![{figure.figure_id}](figure_library/images/{figure.figure_id}.svg)")
            lines.append("")
            lines.append("Parameters:")
            lines.append("")
            for key in sorted(figure.parameters):
                value = figure.parameters[key]
                lines.append(f"- {key}: {value}")
            lines.append("")

    docs_file.write_text("\n".join(lines), encoding="utf-8")
    return len(figures), docs_file


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    count, docs_file = export_library_docs(repo_root)
    print(f"Generated {count} figure assets and {docs_file}")


if __name__ == "__main__":
    main()
