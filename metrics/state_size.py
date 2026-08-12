"""Diagnostic metric: State Size. See experiment.md §7.2. Proxy for
context/token pressure, not a direct outcome measure.
"""
from ..agent_output import AgentOutput
from ..context import Context
from ..state import State


class StateSize:
    name = "state_size"

    def __init__(self):
        self._sizes_over_time: list[int] = []

    def update(self, output: AgentOutput, prior_state: State, context: Context) -> None:
        size = sum(len(fact) for fact in output.state.facts)
        self._sizes_over_time.append(size)

    def result(self) -> dict:
        final_size = self._sizes_over_time[-1] if self._sizes_over_time else 0
        return {"final_size_chars": final_size, "size_over_time": list(self._sizes_over_time)}
