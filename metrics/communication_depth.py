"""Diagnostic metric: Communication Depth. See experiment.md §7.2.
Correlates with but is not identical to density.
"""
from ..agent_output import AgentOutput
from ..context import Context
from ..state import State


class CommunicationDepth:
    name = "communication_depth"

    def __init__(self):
        self._message_count = 0

    def update(self, output: AgentOutput, prior_state: State, context: Context) -> None:
        self._message_count += 1

    def result(self) -> dict:
        return {"total_messages": self._message_count}
