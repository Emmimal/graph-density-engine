"""Everything an agent call produces, kept separate from State so
telemetry can capture message-level detail without stuffing it into
the shared state object. See interfaces.md.
"""
from dataclasses import dataclass, field

from .state import State


@dataclass
class AgentOutput:
    state: State
    message: str
    metadata: dict = field(default_factory=dict)
