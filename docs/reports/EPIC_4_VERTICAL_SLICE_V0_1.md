# Epic 4: Vertical Slice v0.1

Date: 2026-08-10
Goal: deliver a runnable end-to-end product slice where a user can generate a Raven-style matrix puzzle, answer it from the frontend, and see reasoning plus difficulty through the API.

Implementation approach:

1. Ship in small working commits.
2. Prioritize runtime gaps over new documentation.
3. Keep each slice independently runnable.

Initial delivery sequence:

1. Add a real puzzle-generation API endpoint for the frontend runtime.
2. Wire the frontend runtime to the generated puzzle API.
3. Align the UI flow to the vertical-slice product requirements.