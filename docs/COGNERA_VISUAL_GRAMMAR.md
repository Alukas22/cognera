# COGNERA Visual Grammar

Version: Sprint 7.1  
Status: Formal Architecture Specification  
Applies to: Visual object definition, symbol semantics, transformation policy, and rendering model

## 1. Design Philosophy

Cognera does not generate arbitrary shapes.

Cognera generates visual objects assembled from reusable primitives under a semantic model.

Every visual object MUST have explicit structure and meaning, so that transformations remain interpretable by human reasoning.

### 1.1 Core Philosophy Statements

1. Visual generation is semantic first, geometric second.
2. Objects are composed, not drawn ad hoc.
3. Transformations act on meaningful parts, not opaque blobs.
4. The same semantic object should render consistently across puzzles.
5. Visual language must support psychometric clarity over decorative novelty.

## 2. Primitive Library

The primitive library defines atomic graphical elements that can be composed into higher-order symbols.

### 2.1 Basic Geometry Primitives

1. Circle
2. Square
3. Triangle
4. Diamond
5. Pentagon
6. Hexagon
7. Octagon
8. Line
9. Arc

### 2.2 Organic Primitives

1. Petal
2. Leaf
3. Trefoil
4. Fourfoil
5. Flower
6. Rosette

### 2.3 Marker Primitives

1. Dot
2. Ring
3. Double Ring
4. Crosshair
5. Arrowhead

### 2.4 Frame Primitives

1. Circle frame
2. Square frame
3. Rounded frame
4. Hexagonal frame

### 2.5 Primitive Contract

Each primitive definition SHOULD include:

1. Canonical path/template geometry.
2. Anchor point and local coordinate space.
3. Default stroke/fill policy.
4. Symmetry metadata.
5. Allowed local transformations.

## 3. Figure Composition Model

A figure is a layered semantic composition.

### 3.1 Required Layer Schema

A figure MAY include the following layers:

1. Frame
2. Primary object
3. Secondary object
4. Overlay
5. Internal decoration
6. External decoration

### 3.2 Figure Attributes

A composed figure can carry these controlled attributes:

1. Rotation
2. Reflection
3. Scale
4. Fill
5. Stroke

### 3.3 Composition Invariants

1. Layers are independently addressable.
2. Layer order is explicit and stable.
3. Missing layers are represented as null/absent, not merged into other layers.
4. Layer semantics are preserved across transformations.

## 4. Transformation Rules

All transformations MUST operate on named layers or layer-local components.

Global figure-wide blind transformations are forbidden.

### 4.1 Allowed Transformation Patterns

1. Rotate overlay
2. Add frame
3. Remove dot
4. Replace primary object
5. Mirror decoration
6. Scale only secondary object

### 4.2 Transformation Contract

Each transformation operation MUST specify:

1. Target layer/component.
2. Operation type.
3. Parameter values (for example angle, scale factor, mirror axis).
4. Preconditions (for example non-symmetric target for visible rotation).
5. Postconditions preserving semantic consistency.

## 5. Visual Constraints

This section prevents invisible or non-perceivable logic steps.

### 5.1 Rejected Transformations

1. Square rotated 180° when no visible distinction is produced.
2. Circle rotated by any angle.
3. Mirror operation on a mirror-symmetric object with no visible change.

### 5.2 Accepted Transformations

1. Triangle rotated (orientation visibly changes).
2. Arrow mirrored (direction visibly changes).
3. Trefoil rotated when petal orientation/placement changes visibly.
4. Flower reflected when reflected structure is visually distinguishable.

### 5.3 Visibility Requirement

A transformation is valid only if a trained human observer can reliably detect the change under normal viewing conditions.

If detectability is doubtful, the transformation MUST be rejected.

## 6. Composite Objects

Composite objects are reusable symbols constructed from primitives.

### 6.1 Composition Examples

1. Trefoil = Circle + 3 petals
2. Flower = Center + 8 petals
3. Wheel = Circle + spokes
4. Target = Ring + inner ring + dot

### 6.2 Composite Object Rules

1. Composite definition MUST list all component primitives.
2. Relative placement constraints MUST be explicit.
3. Internal symmetry metadata MUST be declared.
4. Allowed transformations MAY differ from primitive defaults if justified by visibility.

## 7. Symbol Library

Reusable symbols are persisted in a structured symbol library.

### 7.1 Required Symbol Fields

Every symbol MUST include:

1. ID
2. SVG template
3. Semantic tags
4. Rotational symmetry metadata
5. Mirror symmetry metadata
6. Allowed transformations
7. Visual complexity score

### 7.2 Symbol Governance

1. IDs MUST be stable and unique.
2. Semantic tags MUST reflect reasoning-relevant attributes.
3. Complexity scoring MUST be deterministic and documented.
4. Symmetry metadata MUST be machine-readable for constraint validation.

## 8. Rendering

SVG is the mandatory rendering format for Cognera visual objects.

### 8.1 Rendering Requirements

1. All figures MUST render as SVG.
2. Every layer/component MUST be independently addressable.
3. No bitmap-only rendering path is allowed.
4. Rendering output MUST preserve semantic-layer boundaries.

### 8.2 Addressability Requirement

Each semantic component SHOULD map to stable SVG groups or element identifiers to support validation, testing, and explanation tooling.

## 9. Future Extensions

The architecture MUST reserve extension points for advanced visual operations.

### 9.1 Reserved Capabilities

1. Boolean unions
2. Masks
3. Cut-outs
4. Transparency
5. Patterns
6. Textures
7. Animation (future)
8. 3D illusion

### 9.2 Extension Safety Rule

Any extension MUST preserve:

1. Semantic interpretability.
2. Layer-addressable transformations.
3. Human-observable reasoning signals.
4. Compatibility with puzzle validity constraints.

## 10. Compliance Scope

This document defines the canonical visual language architecture for Cognera Sprint 7.1.

All future generator, validator, explanation, and quality-gate implementations involving visual objects MUST comply with this specification.

Generator implementation details are intentionally out of scope for this sprint.
