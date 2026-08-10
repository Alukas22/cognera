# Assessment Experience Iteration

## Goal

Improve the user-facing assessment flow without changing the reasoning engine or redesigning the puzzle generator.

## Scope

- Show six answer options for every puzzle.
- Increase the visible size of the matrix and answer options.
- Add a beginner-friendly progression curve that starts with easier items and ramps up gradually.
- Localize puzzle explanations into natural Swedish when the UI language is Swedish.

## Constraints

- Do not change the underlying reasoning engine.
- Do not redesign puzzle generation logic.
- Preserve deterministic puzzle generation for a given seed.

## Acceptance Criteria

- The public matrix API returns six answer options.
- The frontend renders the larger matrix and option cards without clipping internal figure details.
- Early puzzles are selected from a lower difficulty band than later puzzles.
- Swedish UI sessions receive Swedish explanations that read naturally rather than as literal translations.