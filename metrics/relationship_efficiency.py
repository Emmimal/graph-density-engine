"""Diagnostic metric: Relationship Efficiency. See experiment.md §7.2.

"Useful" is operationalized as: this message resulted in a net-new
fact being appended to shared state. This is an operational heuristic,
not a semantic judgment of usefulness — documented limitation per
experiment.md §7.2.
"""
from ..agent_output import AgentOutput
from ..context import Context
from ..state import State


class RelationshipEfficiency:
    name = "relationship_efficiency"

    def __init__(self):
        self._total_messages = 0
        self._useful_messages = 0

    def update(self, output: AgentOutput, prior_state: State, context: Context) -> None:
        self._total_messages += 1
        if len(output.state.facts) > len(prior_state.facts):
            self._useful_messages += 1

    def result(self) -> dict:
        efficiency = (
            self._useful_messages / self._total_messages if self._total_messages else 0.0
        )
        return {
            "efficiency": efficiency,
            "useful_messages": self._useful_messages,
            "total_messages": self._total_messages,
        }
