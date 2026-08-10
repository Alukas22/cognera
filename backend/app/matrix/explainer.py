"""Explanation utilities for Cognera matrix puzzles."""

from __future__ import annotations

from .figure_components import describe_component_change, structure_summary
from .models import DistractorReason, Figure, MatrixPuzzle


def _describe_figure(figure: Figure) -> str:
    return f"{figure.size} {figure.color} {figure.shape} at {figure.rotation}\N{DEGREE SIGN} ({structure_summary(figure)})"


def _format_cell(cell: Figure | None) -> str:
    if cell is None:
        return "missing target cell"
    return _describe_figure(cell)


def _describe_figure_sv(figure: Figure) -> str:
    size_words = {
        "small": "liten",
        "medium": "mellanstor",
        "large": "stor",
    }
    color_words = {
        "black": "svart",
        "white": "vit",
        "red": "röd",
        "blue": "blå",
        "green": "grön",
        "yellow": "gul",
        "orange": "orange",
        "purple": "lila",
    }
    shape_words = {
        "circle": "cirkel",
        "square": "kvadrat",
        "triangle": "triangel",
        "diamond": "romb",
        "pentagon": "pentagon",
        "hexagon": "hexagon",
    }

    size = size_words.get(figure.size, figure.size)
    color = color_words.get(figure.color, figure.color)
    shape = shape_words.get(figure.shape, figure.shape)
    rotation = "utan vridning" if figure.rotation % 360 == 0 else f"vriden {figure.rotation} grader"
    return f"en {size} {color} {shape} {rotation}"


def _format_cell_sv(cell: Figure | None) -> str:
    if cell is None:
        return "den saknade rutan"
    return _describe_figure_sv(cell)


def _rule_sentence_sv(rule_name: str) -> str:
    return {
        "rotation": "rotationen förändras steg för steg och håller figuren orienterad på ett konsekvent sätt",
        "size": "storleken följer en tydlig utveckling som går att läsa över hela matrisen",
        "count": "antalet återkommande detaljer byggs upp metodiskt",
        "shape": "ytterformen växlar på ett sätt som bevarar den övergripande strukturen",
        "position": "placeringen rör sig logiskt i rutnätet och flyttar ett strukturellt drag i taget",
        "mirror": "spegelvändningen skapar en balans som måste läsas över hela figuren",
        "color": "färgen markerar en stabil övergång i den inre figuren",
    }.get(rule_name, "regeln förändrar figurens struktur på ett konsekvent sätt")


def _reject_reason_sv(option) -> str:
    reason = getattr(option, "reason", None)
    if reason == DistractorReason.WRONG_ROTATION:
        return "ser rimlig ut vid första anblick, men missar rotationssteget"
    if reason == DistractorReason.WRONG_SIZE:
        return "bevarar mycket av formen, men bryter storleksmönstret"
    if reason == DistractorReason.WRONG_SHAPE:
        return "liknar rätt svar visuellt, men använder fel ytterform"
    if reason == DistractorReason.WRONG_COUNT:
        return "får inte med antalet återkommande detaljer"
    if reason == DistractorReason.WRONG_POSITION:
        return "placerar ett strukturellt drag på fel plats"
    if reason == DistractorReason.WRONG_COLOR:
        return "byter färg på ett sätt som stör den inre logiken"
    if reason == DistractorReason.WRONG_PROGRESSION:
        return "stannar ett steg för tidigt och fullföljer inte utvecklingen"
    if reason == DistractorReason.OMISSION_OF_RULE:
        return "fångar bara en del av logiken och lämnar en viktig regel utanför"
    if reason == DistractorReason.PARTIAL_REASONING:
        return "känns nära, men håller inte ihop när man granskar helheten"
    if reason == DistractorReason.PERCEPTUAL_SIMILARITY:
        return "ser plausibel ut vid snabb blick, men faller när man läser detaljerna"
    if reason == DistractorReason.PARTIAL_PATTERN:
        return "följer mönstret delvis, men inte tillräckligt för att vara rätt"
    if reason == DistractorReason.MIRROR_INSTEAD_OF_ROTATION:
        return "använder spegling där uppgiften kräver en annan förändring"
    return "bryter mot minst en av de aktiva reglerna"


def _explain_puzzle_sv(puzzle: MatrixPuzzle) -> str:
    if not puzzle.rules:
        return "Inga regler är tillgängliga för det här pusslet."

    lines: list[str] = []
    lines.append("Titta efter hur figurerna förändras från ruta till ruta; den saknade rutan ska följa samma logik.")

    for index, rule in enumerate(puzzle.rules, start=1):
        lines.append(f"Regel {index}: {_rule_sentence_sv(rule.type.value)}.")

    lines.append(f"Den saknade figuren är {_describe_figure_sv(puzzle.correct_answer)}.")

    for row_index, row in enumerate(puzzle.grid, start=1):
        rendered = " | ".join(_format_cell_sv(cell) for cell in row)
        lines.append(f"Rad {row_index}: {rendered}.")

    for col_index in range(3):
        col_cells = [puzzle.grid[row_index][col_index] for row_index in range(3)]
        rendered = " | ".join(_format_cell_sv(cell) for cell in col_cells)
        lines.append(f"Kolumn {col_index + 1}: {rendered}.")

    for option in puzzle.options or ():
        if option.is_correct:
            continue
        lines.append(f"Alternativ {option.label} är fel eftersom det {_reject_reason_sv(option)}.")

    lines.append("Sammanfattat: lösningen blir tydlig när man håller fast vid både helheten och de små förändringarna.")
    return "\n".join(lines)


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
