"""Phase 1 / Phase 1.5 agent. No reasoning, no redundancy, no density-
or depth-awareness — deliberately boring, per experiment.md §8 and
interfaces.md. Used to validate the graph engine in isolation before
any real cognition is introduced.
"""
import uuid

from ..agent_output import AgentOutput
from ..context import Context
from ..state import State


class DummyAgent:
    def process(self, state: State, context: Context) -> AgentOutput:
        fact = f"dummy_fact_{uuid.uuid4().hex[:8]}"
        new_state = state.copy()
        new_state.facts.append(fact)
        new_state.last_modifier = context.agent_id
        return AgentOutput(state=new_state, message=fact, metadata={})
