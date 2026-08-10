"""Immutable data models for reasoning graph infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


class NodeType(StrEnum):
    OBSERVATION = "observation"
    RULE = "rule"
    CONSTRAINT = "constraint"
    HYPOTHESIS = "hypothesis"
    CONCLUSION = "conclusion"


class EdgeType(StrEnum):
    DERIVES_FROM = "derives_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONSTRAINS = "constrains"
    LEADS_TO = "leads_to"
    PROVENANCE = "provenance"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class ReasoningNode:
    """Base immutable node for reasoning graph structures."""

    node_id: UUID = field(default_factory=uuid4)
    node_type: NodeType = field(default=NodeType.OBSERVATION)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    source_info: str = "unspecified"
    confidence_score: float | None = None

    def __post_init__(self) -> None:
        metadata_copy = dict(self.metadata)
        object.__setattr__(self, "metadata", MappingProxyType(metadata_copy))

        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")

        if self.confidence_score is not None:
            if self.confidence_score < 0.0 or self.confidence_score > 1.0:
                raise ValueError("confidence_score must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True, init=False)
class ObservationNode(ReasoningNode):
    """Observation node created from empirical puzzle evidence."""

    def __init__(
        self,
        *,
        node_id: UUID | None = None,
        metadata: Mapping[str, Any] | None = None,
        created_at: datetime | None = None,
        source_info: str = "observation",
        confidence_score: float | None = None,
    ) -> None:
        ReasoningNode.__init__(
            self,
            node_id=node_id or uuid4(),
            node_type=NodeType.OBSERVATION,
            metadata=metadata or {},
            created_at=created_at or _utcnow(),
            source_info=source_info,
            confidence_score=confidence_score,
        )


@dataclass(frozen=True, slots=True, init=False)
class RuleNode(ReasoningNode):
    """Rule node representing a reusable inference rule."""

    def __init__(
        self,
        *,
        node_id: UUID | None = None,
        metadata: Mapping[str, Any] | None = None,
        created_at: datetime | None = None,
        source_info: str = "rule",
        confidence_score: float | None = None,
    ) -> None:
        ReasoningNode.__init__(
            self,
            node_id=node_id or uuid4(),
            node_type=NodeType.RULE,
            metadata=metadata or {},
            created_at=created_at or _utcnow(),
            source_info=source_info,
            confidence_score=confidence_score,
        )


@dataclass(frozen=True, slots=True, init=False)
class ConstraintNode(ReasoningNode):
    """Constraint node representing restrictions over hypotheses."""

    def __init__(
        self,
        *,
        node_id: UUID | None = None,
        metadata: Mapping[str, Any] | None = None,
        created_at: datetime | None = None,
        source_info: str = "constraint",
        confidence_score: float | None = None,
    ) -> None:
        ReasoningNode.__init__(
            self,
            node_id=node_id or uuid4(),
            node_type=NodeType.CONSTRAINT,
            metadata=metadata or {},
            created_at=created_at or _utcnow(),
            source_info=source_info,
            confidence_score=confidence_score,
        )


@dataclass(frozen=True, slots=True, init=False)
class HypothesisNode(ReasoningNode):
    """Hypothesis node representing a possible explanation branch."""

    def __init__(
        self,
        *,
        node_id: UUID | None = None,
        metadata: Mapping[str, Any] | None = None,
        created_at: datetime | None = None,
        source_info: str = "hypothesis",
        confidence_score: float | None = None,
    ) -> None:
        ReasoningNode.__init__(
            self,
            node_id=node_id or uuid4(),
            node_type=NodeType.HYPOTHESIS,
            metadata=metadata or {},
            created_at=created_at or _utcnow(),
            source_info=source_info,
            confidence_score=confidence_score,
        )


@dataclass(frozen=True, slots=True, init=False)
class ConclusionNode(ReasoningNode):
    """Conclusion node representing accepted reasoning outcomes."""

    def __init__(
        self,
        *,
        node_id: UUID | None = None,
        metadata: Mapping[str, Any] | None = None,
        created_at: datetime | None = None,
        source_info: str = "conclusion",
        confidence_score: float | None = None,
    ) -> None:
        ReasoningNode.__init__(
            self,
            node_id=node_id or uuid4(),
            node_type=NodeType.CONCLUSION,
            metadata=metadata or {},
            created_at=created_at or _utcnow(),
            source_info=source_info,
            confidence_score=confidence_score,
        )


@dataclass(frozen=True, slots=True)
class ReasoningEdge:
    """Directed edge connecting reasoning nodes."""

    source_node: UUID
    target_node: UUID
    edge_type: EdgeType
    explanation: str
    weight: float | None = None

    def __post_init__(self) -> None:
        if not self.explanation.strip():
            raise ValueError("edge explanation must be non-empty")
        if self.weight is not None and (self.weight < 0.0 or self.weight > 1.0):
            raise ValueError("edge weight must be between 0.0 and 1.0")
