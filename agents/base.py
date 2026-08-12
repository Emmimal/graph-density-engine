"""Agent contract. See interfaces.md — this signature must not change
between DummyAgent (Phase 1/1.5) and LLMAgent (Phase 2).
"""
from typing import Protocol

from ..agent_output import AgentOutput
from ..context import Context
from ..state import State


class Agent(Protocol):
    def process(self, state: State, context: Context) -> AgentOutput:
        ...
