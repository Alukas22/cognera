"""Tests for reasoning graph architecture."""

from __future__ import annotations

import pytest

from backend.app.reasoning import (
    ConstraintNode,
    ConclusionNode,
    EdgeType,
    GraphBuilder,
    GraphValidator,
    HypothesisNode,
    ObservationNode,
    ReasoningEdge,
    RuleNode,
)


def _build_valid_graph():
    obs = ObservationNode(metadata={"cell": "r1c1"}, source_info="vision")
    rule = RuleNode(metadata={"rule": "rotation_step"}, source_info="rule_engine", confidence_score=0.9)
    constraint = ConstraintNode(metadata={"must_be_unique": True}, source_info="quality_gate")
    hyp_a = HypothesisNode(metadata={"candidate": "A"}, source_info="solver", confidence_score=0.75)
    hyp_b = HypothesisNode(metadata={"candidate": "B"}, source_info="solver", confidence_score=0.4)
    conclusion = ConclusionNode(metadata={"selected": "A"}, source_info="inference", confidence_score=0.88)

    builder = GraphBuilder()
    builder.add_nodes([obs, rule, constraint, hyp_a, hyp_b, conclusion])
    builder.add_edge(
        ReasoningEdge(
            source_node=obs.node_id,
            target_node=rule.node_id,
            edge_type=EdgeType.DERIVES_FROM,
            explanation="Observed pattern feeds rule extraction",
        )
    )
    builder.add_edge(
        ReasoningEdge(
            source_node=rule.node_id,
            target_node=hyp_a.node_id,
            edge_type=EdgeType.SUPPORTS,
            explanation="Rule supports hypothesis A",
            weight=0.85,
        )
    )
    builder.add_edge(
        ReasoningEdge(
            source_node=rule.node_id,
            target_node=hyp_b.node_id,
            edge_type=EdgeType.SUPPORTS,
            explanation="Rule also weakly supports hypothesis B",
            weight=0.35,
        )
    )
    builder.add_edge(
        ReasoningEdge(
            source_node=constraint.node_id,
            target_node=hyp_b.node_id,
            edge_type=EdgeType.CONTRADICTS,
            explanation="Constraint weakens hypothesis B",
        )
    )
    builder.add_edge(
        ReasoningEdge(
            source_node=constraint.node_id,
            target_node=hyp_a.node_id,
            edge_type=EdgeType.CONSTRAINS,
            explanation="Constraint keeps only consistent hypotheses",
        )
    )
    builder.add_edge(
        ReasoningEdge(
            source_node=hyp_a.node_id,
            target_node=conclusion.node_id,
            edge_type=EdgeType.LEADS_TO,
            explanation="Best supported hypothesis becomes conclusion",
        )
    )
    builder.add_edge(
        ReasoningEdge(
            source_node=obs.node_id,
            target_node=conclusion.node_id,
            edge_type=EdgeType.PROVENANCE,
            explanation="Conclusion provenance tracks original observation",
        )
    )

    return builder.build(), obs, rule, constraint, hyp_a, hyp_b, conclusion


def test_graph_creation_and_core_relations() -> None:
    graph, obs, rule, constraint, hyp_a, hyp_b, conclusion = _build_valid_graph()

    assert len(graph.nodes) == 6
    assert len(graph.edges) == 7

    assert set(graph.parents(hyp_a.node_id)) == {rule.node_id, constraint.node_id}
    assert set(graph.children(rule.node_id)) == {hyp_a.node_id, hyp_b.node_id}
    assert rule.node_id in graph.dependencies(conclusion.node_id)
    assert obs.node_id in graph.provenance(conclusion.node_id)


def test_cycle_detection() -> None:
    graph, obs, _, _, _, _, conclusion = _build_valid_graph()
    builder = GraphBuilder().add_nodes(graph.nodes)
    for edge in graph.edges:
        builder.add_edge(edge)

    builder.add_edge(
        ReasoningEdge(
            source_node=conclusion.node_id,
            target_node=obs.node_id,
            edge_type=EdgeType.DERIVES_FROM,
            explanation="Invalid backward dependency",
        )
    )

    with pytest.raises(ValueError, match="cycle"):
        builder.build()


def test_graph_validation_accepts_valid_graph() -> None:
    graph, *_ = _build_valid_graph()
    GraphValidator().validate(graph)


def test_topological_sort_orders_dependencies_before_conclusions() -> None:
    graph, obs, rule, constraint, hyp_a, hyp_b, conclusion = _build_valid_graph()
    order = graph.topological_order()
    index = {node_id: idx for idx, node_id in enumerate(order)}

    assert index[obs.node_id] < index[rule.node_id]
    assert index[rule.node_id] < index[hyp_a.node_id]
    assert index[rule.node_id] < index[hyp_b.node_id]
    assert index[hyp_a.node_id] < index[conclusion.node_id]
    assert index[constraint.node_id] < index[hyp_a.node_id]


def test_multiple_hypothesis_branches_are_supported() -> None:
    graph, _, rule, _, hyp_a, hyp_b, _ = _build_valid_graph()

    hypothesis_children = set(graph.children(rule.node_id))
    assert hypothesis_children == {hyp_a.node_id, hyp_b.node_id}


def test_invalid_graph_rejection_for_unknown_nodes_and_self_loop() -> None:
    obs = ObservationNode(metadata={"k": "v"})
    rule = RuleNode(metadata={"r": "x"})

    builder = GraphBuilder()
    builder.add_node(obs)

    with pytest.raises(ValueError, match="unknown node"):
        builder.add_edge(
            ReasoningEdge(
                source_node=obs.node_id,
                target_node=rule.node_id,
                edge_type=EdgeType.SUPPORTS,
                explanation="References non-added target",
            )
        ).build()

    with pytest.raises(ValueError, match="self-loop"):
        GraphBuilder().add_node(obs).add_edge(
            ReasoningEdge(
                source_node=obs.node_id,
                target_node=obs.node_id,
                edge_type=EdgeType.DERIVES_FROM,
                explanation="Self dependency",
            )
        )


def test_node_and_edge_validation_constraints() -> None:
    with pytest.raises(ValueError, match="confidence_score"):
        ObservationNode(confidence_score=1.5)

    with pytest.raises(ValueError, match="edge explanation"):
        ReasoningEdge(
            source_node=ObservationNode().node_id,
            target_node=RuleNode().node_id,
            edge_type=EdgeType.SUPPORTS,
            explanation=" ",
        )
