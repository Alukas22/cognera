# KNOWN FAILURE PATTERNS

Status: Permanent catalogue  
Owner: Cognera quality architecture  
Scope: Matrix puzzle generation, validation, and release gates

## Purpose

This document records recurring puzzle-quality failure classes.

Any puzzle matching any pattern in this catalogue MUST be rejected.

Each pattern requires:

1. Automated detection in validator pipeline.
2. Regression protection in tests.
3. Reporting visibility in quality analytics.

## Failure Patterns

### FP-001

- ID: FP-001
- Name: Invisible Rotation
- Description: Rotation rule is present but visual evidence of rotation is not observable.
- Why it is harmful: Creates hidden logic, undermines fairness, and violates visual reasoning constraints.
- Example: Circle or symmetric square marked as rotating by 90°.
- Detection strategy: Perceptual check for non-observable rotation signal.
- Validation rule: Reject if `invisible_rotation` is detected.
- Regression test: `test_fp_001_invisible_rotation_detected`
- Status: Active

### FP-002

- ID: FP-002
- Name: Invisible Mirror Symmetry
- Description: Mirror transformation is claimed but reflection is visually indistinguishable.
- Why it is harmful: Encourages guessing and non-inferable rules.
- Example: Mirror operation across a grid using only mirror-symmetric shapes.
- Detection strategy: Perceptual mirror observability test.
- Validation rule: Reject if `invisible_mirror` is detected.
- Regression test: `test_fp_002_invisible_mirror_detected`
- Status: Active

### FP-003

- ID: FP-003
- Name: Duplicate Answer Options
- Description: Two or more answer options are visually identical.
- Why it is harmful: Breaks unique-solution requirement and distorts distractor quality.
- Example: Option B and Option E have identical shape/rotation/size/color.
- Detection strategy: Option uniqueness check over normalized figure keys.
- Validation rule: Reject if answer option uniqueness fails.
- Regression test: `test_fp_003_duplicate_answer_options_detected`
- Status: Active

### FP-004

- ID: FP-004
- Name: Explanation Does Not Explain Whole Matrix
- Description: Explanation only partially describes logic and omits row/column or visible-cell reconstruction.
- Why it is harmful: Violates explainability and auditability requirements.
- Example: Explanation states only final answer with no row/column derivation.
- Detection strategy: Explanation coverage checks for rows, columns, and visible-cell derivation.
- Validation rule: Reject if full-matrix explanation coverage fails.
- Regression test: `test_fp_004_incomplete_explanation_detected`
- Status: Active

### FP-005

- ID: FP-005
- Name: Puzzle Solvable Without Discovering The Intended Rule
- Description: Puzzle can be solved through superficial cues without identifying intended rule structure.
- Why it is harmful: Measures shortcut exploitation rather than reasoning.
- Example: Single obvious visual cue determines answer while intended rule is redundant.
- Detection strategy: Entire-matrix requirement and no-redundant-rule checks.
- Validation rule: Reject if entire-matrix observation is not required.
- Regression test: `test_fp_005_solved_without_intended_rule_detected`
- Status: Active

### FP-006

- ID: FP-006
- Name: Multiple Plausible Solutions
- Description: More than one answer or rule interpretation appears valid.
- Why it is harmful: Introduces ambiguity and invalidates psychometric measurement.
- Example: Two options satisfy plausible completion paths.
- Detection strategy: Unambiguity and alternative-interpretation checks.
- Validation rule: Reject if puzzle is ambiguous.
- Regression test: `test_fp_006_multiple_plausible_solutions_detected`
- Status: Active

### FP-007

- ID: FP-007
- Name: Only One Row Or Column Contains The Rule
- Description: Reasoning signal is localized to a single row or single column.
- Why it is harmful: Reduces reasoning depth and encourages local heuristics.
- Example: Pattern appears only in top row while other rows/columns are static.
- Detection strategy: Row/column participation checks.
- Validation rule: Reject if every row and every column do not participate.
- Regression test: `test_fp_007_single_row_or_column_rule_detected`
- Status: Active

### FP-008

- ID: FP-008
- Name: Trivial Puzzle
- Description: Puzzle has insufficient reasoning depth.
- Why it is harmful: Fails cognitive assessment objective.
- Example: Single repetitive pattern with no cross-dimensional reasoning.
- Detection strategy: Reasoning-depth threshold and triviality checks.
- Validation rule: Reject if puzzle is trivial.
- Regression test: `test_fp_008_trivial_puzzle_detected`
- Status: Active

### FP-009

- ID: FP-009
- Name: Distractors Too Similar
- Description: Distractors are too close to each other or to the correct answer with low logical distinction.
- Why it is harmful: Shifts task from reasoning to perceptual noise discrimination.
- Example: Most distractors differ by one imperceptible attribute.
- Detection strategy: Distractor distance profile and distinctness floor.
- Validation rule: Reject when distractor similarity exceeds threshold.
- Regression test: `test_fp_009_distractors_too_similar_detected`
- Status: Active

### FP-010

- ID: FP-010
- Name: Distractors Too Easy
- Description: Distractors are obviously wrong and not plausible.
- Why it is harmful: Inflates scores and weakens discriminatory power.
- Example: All incorrect options differ on multiple unrelated attributes.
- Detection strategy: Distractor plausibility/near-miss ratio and quality component checks.
- Validation rule: Reject when distractor quality is below threshold.
- Regression test: `test_fp_010_distractors_too_easy_detected`
- Status: Active

### FP-011

- ID: FP-011
- Name: Rule Only Justifies Final Cell
- Description: Rules explain only missing cell but not the eight visible cells.
- Why it is harmful: Violates rule validity and human-derivation requirements.
- Example: Rule text matches answer while visible grid is not derivable from same rules.
- Detection strategy: Full visible-cell reconstruction checks.
- Validation rule: Reject if visible-cell derivation from generation rules fails.
- Regression test: `test_fp_011_rule_only_justifies_final_cell_detected`
- Status: Active

### FP-012

- ID: FP-012
- Name: Symmetric Shape Uses Rotation
- Description: Rotation is applied to rotationally symmetric figures, producing no observable change.
- Why it is harmful: Introduces invisible transformations and hidden assumptions.
- Example: Circle or square rotation used as active reasoning rule.
- Detection strategy: Rotation-rule + symmetry intersection detection.
- Validation rule: Reject if symmetric-shape rotation is active.
- Regression test: `test_fp_012_symmetric_shape_rotation_detected`
- Status: Active

## Change Management

To add a new pattern:

1. Assign next sequential ID (`FP-013`, `FP-014`, ...).
2. Add full pattern record to this document.
3. Add detector logic in failure-pattern registry.
4. Add regression test covering detection and rejection.
5. Confirm report output includes pattern frequency and trend.
