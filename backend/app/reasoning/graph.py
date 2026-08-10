"""Core graph classes for reasoning graph construction and validation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from .models import EdgeType, ReasoningEdge, ReasoningNode


@dataclass(frozen=True, slots=True)
class ReasoningGraph:
    """Immutable directed reasoning graph."""

    nodes: tuple[ReasoningNode, ...]
    edges: tuple[ReasoningEdge, ...]

    def __post_init__(self) -> None:
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("duplicate node IDs are not allowed")

        known = set(node_ids)
        for edge in self.edges:
            if edge.source_node not in known or edge.target_node not in known:
                raise ValueError("edge references unknown node")

        GraphValidator().validate(self)

    def node_map(self) -> dict[UUID, ReasoningNode]:
        return {node.node_id: node for node in self.nodes}

    def outgoing(self, node_id: UUID) -> tuple[ReasoningEdge, ...]:
        return tuple(edge for edge in self.edges if edge.source_node == node_id)

    def incoming(self, node_id: UUID) -> tuple[ReasoningEdge, ...]:
        return tuple(edge for edge in self.edges if edge.target_node == node_id)

    def parents(self, node_id: UUID) -> tuple[UUID, ...]:
        return tuple(edge.source_node for edge in self.incoming(node_id))

    def children(self, node_id: UUID) -> tuple[UUID, ...]:
        return tuple(edge.target_node for edge in self.outgoing(node_id))

    def dependencies(self, node_id: UUID, transitive: bool = True) -> set[UUID]:
        direct = {edge.source_node for edge in self.incoming(node_id)}
        if not transitive:
            return direct

        all_dependencies: set[UUID] = set()
        stack = list(direct)
        while stack:
            current = stack.pop()
            if current in all_dependencies:
                continue
            all_dependencies.add(current)
            for edge in self.incoming(current):
                if edge.source_node not in all_dependencies:
                    stack.append(edge.source_node)
        return all_dependencies

    def provenance(self, node_id: UUID) -> set[UUID]:
        """Return all upstream provenance-linked nodes."""

        provenance_sources: set[UUID] = set()
        stack = [node_id]
        while stack:
            target = stack.pop()
            for edge in self.incoming(target):
                if edge.edge_type not in {EdgeType.PROVENANCE, EdgeType.DERIVES_FROM}:
                    continue
                if edge.source_node in provenance_sources:
                    continue
                provenance_sources.add(edge.source_node)
                stack.append(edge.source_node)
        return provenance_sources

    def has_cycle(self) -> bool:
        return GraphValidator().has_cycle(self)

    def topological_order(self) -> tuple[UUID, ...]:
        return GraphValidator().topological_order(self)


class GraphBuilder:
    """Mutable builder for assembling immutable reasoning graphs."""

    def __init__(self) -> None:
        self._nodes: dict[UUID, ReasoningNode] = {}
        self._edges: list[ReasoningEdge] = []

    def add_node(self, node: ReasoningNode) -> "GraphBuilder":
        if node.node_id in self._nodes:
            raise ValueError("duplicate node ID")
        self._nodes[node.node_id] = node
        return self

    def add_nodes(self, nodes: Iterable[ReasoningNode]) -> "GraphBuilder":
        for node in nodes:
            self.add_node(node)
        return self

    def add_edge(self, edge: ReasoningEdge) -> "GraphBuilder":
        if edge.source_node == edge.target_node:
            raise ValueError("self-loops are not allowed")
        self._edges.append(edge)
        return self

    def connect(
        self,
        source_node: ReasoningNode,
        target_node: ReasoningNode,
        *,
        edge_type: EdgeType,
        explanation: str,
        weight: float | None = None,
    ) -> "GraphBuilder":
        if source_node.node_id not in self._nodes:
            self.add_node(source_node)
        if target_node.node_id not in self._nodes:
            self.add_node(target_node)

        return self.add_edge(
            ReasoningEdge(
                source_node=source_node.node_id,
                target_node=target_node.node_id,
                edge_type=edge_type,
                explanation=explanation,
                weight=weight,
            )
        )

    def build(self, validate: bool = True) -> ReasoningGraph:
        graph = ReasoningGraph(nodes=tuple(self._nodes.values()), edges=tuple(self._edges))
        if validate:
            GraphValidator().validate(graph)
        return graph


class GraphValidator:
    """Validation and graph algorithms for reasoning graphs."""

    def validate(self, graph: ReasoningGraph) -> None:
        node_map = graph.node_map()
        for edge in graph.edges:
            if edge.source_node not in node_map or edge.target_node not in node_map:
                raise ValueError("edge references node that does not exist")
            if edge.source_node == edge.target_node:
                raise ValueError("self-loop edge is invalid")

        if self.has_cycle(graph):
            raise ValueError("reasoning graph contains a directed cycle")

    def has_cycle(self, graph: ReasoningGraph) -> bool:
        adjacency = self._adjacency(graph)
        state: dict[UUID, int] = {node.node_id: 0 for node in graph.nodes}

        def visit(node_id: UUID) -> bool:
            state[node_id] = 1
            for child in adjacency[node_id]:
                if state[child] == 1:
                    return True
                if state[child] == 0 and visit(child):
                    return True
            state[node_id] = 2
            return False

        for node in graph.nodes:
            if state[node.node_id] == 0 and visit(node.node_id):
                return True
        return False

    def topological_order(self, graph: ReasoningGraph) -> tuple[UUID, ...]:
        indegree: dict[UUID, int] = {node.node_id: 0 for node in graph.nodes}
        adjacency = self._adjacency(graph)
        for edge in graph.edges:
            indegree[edge.target_node] += 1

        queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
        ordering: list[UUID] = []

        while queue:
            current = queue.popleft()
            ordering.append(current)
            for child in adjacency[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        if len(ordering) != len(graph.nodes):
            raise ValueError("cannot topologically order graph with cycle")

        return tuple(ordering)

    def _adjacency(self, graph: ReasoningGraph) -> dict[UUID, list[UUID]]:
        adjacency: dict[UUID, list[UUID]] = defaultdict(list)
        for node in graph.nodes:
            adjacency[node.node_id]
        for edge in graph.edges:
            adjacency[edge.source_node].append(edge.target_node)
        return adjacency
