"""Diagnostic metric: Edge Utilization. See experiment.md §7.2.

Compares actually-traversed edges (current_node -> next_node pairs
observed via Context, which the Router populates every step) against
the total configured edges in the trial's adjacency matrix. High
configured density does not guarantee high realized communication —
that gap is exactly what this metric is for.
"""
from ..agent_output import AgentOutput
from ..context import Context
from ..state import State


class EdgeUtilization:
    name = "edge_utilization"

    def __init__(self, adjacency: list[list[int]]):
        self._adjacency = adjacency
        self._configured_edges = sum(sum(row) for row in adjacency)
        self._used_edges: set[tuple[int, int]] = set()

    def update(self, output: AgentOutput, prior_state: State, context: Context) -> None:
        self._used_edges.add((context.current_node, context.next_node))

    def result(self) -> dict:
        used = len(self._used_edges)
        utilization = used / self._configured_edges if self._configured_edges else 0.0
        return {
            "utilization": utilization,
            "used_edges": used,
            "configured_edges": self._configured_edges,
        }
