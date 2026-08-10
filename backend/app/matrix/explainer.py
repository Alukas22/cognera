"""Explanation utilities for Cognera matrix puzzles."""

from __future__ import annotations

from .figure_components import describe_component_change
from .models import DistractorReason, Figure, MatrixPuzzle


def _describe_figure(figure: Figure) -> str:
    rotation = figure.rotation % 360
    rotation_text = "without rotation" if rotation == 0 else f"rotated {rotation} degrees"
    return f"{figure.size} {figure.color} {figure.shape} {rotation_text}"


def _format_cell(cell: Figure | None) -> str:
    if cell is None:
        return "missing target cell"
    return _describe_figure(cell)


def _shape_label_sv(shape: str) -> str:
    return {
        "circle": "cirkel",
        "square": "kvadrat",
        "triangle": "triangel",
        "diamond": "romb",
        "pentagon": "pentagon",
        "hexagon": "hexagon",
    }.get(shape, shape)


def _size_label_sv(size: str) -> str:
    return {
        "small": "liten",
        "medium": "mellanstor",
        "large": "stor",
    }.get(size, size)


def _rotation_label_sv(rotation: int) -> str:
    normalized = rotation % 360
    if normalized == 0:
        return "utan vridning"
    if normalized == 90:
        return "vriden ett kvarts varv"
    if normalized == 180:
        return "vriden ett halvt varv"
    if normalized == 270:
        return "vriden tre kvarts varv"
    return f"vriden {rotation} grader"


def _figure_summary_sv(figure: Figure) -> str:
    return f"{_size_label_sv(figure.size)} {_shape_label_sv(figure.shape)} {_rotation_label_sv(figure.rotation)}"


def _correct_answer_summary_sv(figure: Figure) -> str:
    return f"{_size_label_sv(figure.size)} {_shape_label_sv(figure.shape)} {_rotation_label_sv(figure.rotation)}"


def _describe_figure_sv(figure: Figure) -> str:
    return _figure_summary_sv(figure)


def _rule_overview_sv(rule_name: str) -> str:
    return {
        "rotation": "figuren vrids stegvis i samma riktning",
        "size": "storleken växlar i ett tydligt mönster",
        "count": "antalet återkommande delar förändras på ett konsekvent sätt",
        "shape": "den yttre formen följer en bestämd ordning",
        "position": "placeringen flyttar sig på ett förutsägbart sätt",
        "mirror": "strukturen speglas över mitten",
        "color": "den inre markeringen byts i en fast ordning",
    }.get(rule_name, "figuren förändras på ett konsekvent sätt")


def _rule_label_sv(rule_name: str) -> str:
    return {
        "rotation": "vridning",
        "size": "storlek",
        "count": "antal",
        "shape": "yttre form",
        "position": "placering",
        "mirror": "spegling",
        "color": "inre markering",
    }.get(rule_name, "regeln")


def _rule_summary_sv(puzzle: MatrixPuzzle) -> str:
    if not puzzle.rules:
        return "ingen tydlig regel"
    labels = [_rule_label_sv(rule.type.value) for rule in puzzle.rules]
    unique_labels: list[str] = []
    for label in labels:
        if label not in unique_labels:
            unique_labels.append(label)
    return ", ".join(unique_labels)


def _correct_answer_reason_sv(puzzle: MatrixPuzzle) -> str:
    return (
        "Rätt svar följer samma ordning som de synliga rutorna. "
        "Det passar i både rad- och kolumnmönstret samtidigt."
    )


def _format_cell_sv(cell: Figure | None) -> str:
    if cell is None:
        return "den saknade rutan"
    return _describe_figure_sv(cell)


def _reject_reason_sv(option) -> str:
    reason = getattr(option, "reason", None)
    if reason == DistractorReason.WRONG_ROTATION:
        return "Bryter mot rotationsregeln."
    if reason == DistractorReason.WRONG_SIZE:
        return "Bryter mot storleksregeln."
    if reason == DistractorReason.WRONG_SHAPE:
        return "Bryter mot regeln för yttre form."
    if reason == DistractorReason.WRONG_COUNT:
        return "Bryter mot regeln för antal återkommande delar."
    if reason == DistractorReason.WRONG_POSITION:
        return "Bryter mot placeringsregeln."
    if reason == DistractorReason.WRONG_COLOR:
        return "Bryter mot regeln för den inre markeringen."
    if reason == DistractorReason.WRONG_PROGRESSION:
        return "Bryter mot den fortsatta utvecklingen."
    if reason == DistractorReason.OMISSION_OF_RULE:
        return "Följer bara en del av reglerna."
    if reason == DistractorReason.PARTIAL_REASONING:
        return "Ser nära ut, men håller inte ihop med helheten."
    if reason == DistractorReason.PERCEPTUAL_SIMILARITY:
        return "Ser rimlig ut vid första blick, men bryter mot en regel."
    if reason == DistractorReason.PARTIAL_PATTERN:
        return "Följer mönstret bara delvis."
    if reason == DistractorReason.MIRROR_INSTEAD_OF_ROTATION:
        return "Använder spegling där uppgiften kräver något annat."
    return "Bryter mot minst en av de aktiva reglerna."


def _explain_puzzle_sv(puzzle: MatrixPuzzle) -> str:
    rule_summary = _rule_summary_sv(puzzle)
    rows_focus = "radmönstret" if not puzzle.rules else f"radmönstret i {rule_summary}"
    cols_focus = "kolumnmönstret" if not puzzle.rules else f"kolumnmönstret i {rule_summary}"

    lines: list[str] = [
        "Översikt",
        "- Vad är huvudidén? Följ samma förändring i varje rad och kolumn för att hitta den enda rimliga saknade figuren.",
        "",
        "Steg 1",
        f"- Vad händer i raderna? Identifiera {rows_focus} och kontrollera att progressionen är konsekvent.",
        "",
        "Steg 2",
        f"- Vad händer i kolumnerna? Kontrollera {cols_focus} så att samma logik återkommer vertikalt.",
        "",
        "Kontroll",
        "- Varför fungerar båda samtidigt? Endast ett alternativ uppfyller både rad- och kolumnregeln samtidigt.",
        "",
        "Rätt svar",
        (
            "- Varför är detta korrekt? "
            f"Figuren är {_correct_answer_summary_sv(puzzle.correct_answer)} och följer alla aktiva regler."
        ),
        "",
    ]

    option_by_label = {option.label: option for option in puzzle.options or ()}
    for label in ("A", "B", "C", "D", "E", "F"):
        option = option_by_label.get(label)
        lines.append(f"Alternativ {label}")
        if option is None:
            lines.append("- Varför är detta fel? Alternativet saknar bedömningsdata och uppfyller inte valideringskravet.")
        elif option.is_correct:
            lines.append("- Varför är detta fel? Det är inte fel, detta är rätt svar.")
        else:
            lines.append(f"- Varför är detta fel? {_reject_reason_sv(option)}")
        lines.append("")

    return "\n".join(lines).strip()


def explain_puzzle(puzzle: MatrixPuzzle, language: str = "en") -> str:
    """Produce a localized explanation for the generated puzzle."""

    normalized_language = (language or "en").lower()
    if normalized_language.startswith("sv"):
        return _explain_puzzle_sv(puzzle)

    if not puzzle.rules:
        return "No rules are available for this puzzle."

    lines: list[str] = []

    for index, rule in enumerate(puzzle.rules, start=1):
        lines.append(
            f"Rule {index}: {rule.type.value.capitalize()} rule -> {rule.value}; this {describe_component_change(rule.type.value)}"
        )

    lines.append(
        "Correct answer: "
        f"The missing figure is {_describe_figure(puzzle.correct_answer)}."
    )

    for row_index, row in enumerate(puzzle.grid, start=1):
        rendered = " | ".join(_format_cell(cell) for cell in row)
        lines.append(f"Row {row_index}: {rendered}")

    for col_index in range(3):
        col_cells = [puzzle.grid[row_index][col_index] for row_index in range(3)]
        rendered = " | ".join(_format_cell(cell) for cell in col_cells)
        lines.append(f"Column {col_index + 1}: {rendered}")

    for option in puzzle.options or ():
        if option.is_correct:
            continue
        reason = option.explanation.strip() or "it violates at least one active rule"
        lines.append(f"Option {option.label} is incorrect because {reason}")

    return "\n".join(lines)
