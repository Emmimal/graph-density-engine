"""Read-only information about the current position in a trial.

Per interfaces.md: given to an agent alongside State, never mutated
by the agent. current_node / next_node are included so Telemetry
(specifically EdgeUtilization) can observe which edge was actually
traversed, without the Agent needing to read or branch on them.
message_index exists for logging only — see interfaces.md's
"Invariants" section: an Agent implementation must not branch on it.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Context:
    agent_id: int
    message_index: int
    communication_budget: int
    density_level: float
    current_node: int
    next_node: int
    scenario_id: str | None = None
