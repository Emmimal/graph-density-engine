"""Engine. Its run(agent, ...) signature never branches on the type of
agent — DummyAgent (Phase 1/1.5) and LLMAgent (Phase 2) are driven
identically. Engine has zero knowledge of what kind of agent it's
running; that's the dependency inversion the whole protocol depends
on. See interfaces.md.
"""
import random
from typing import Callable

from ..context import Context
from ..state import State
from ..metrics.communication_depth import CommunicationDepth
from ..metrics.edge_utilization import EdgeUtilization
from ..metrics.information_gain import InformationGain
from ..metrics.relationship_efficiency import RelationshipEfficiency
from ..metrics.state_size import StateSize
from ..metrics.tfidf_redundancy import TFIDFRedundancy
from .budget import DEFAULT_COMMUNICATION_BUDGET, is_budget_exhausted
from .router import Router
from .telemetry import Telemetry, TrialRecord
from .topology import generate_connected_erdos_renyi, realized_density


def default_diagnostic_metrics(adjacency: list[list[int]]) -> list:
    return [
        RelationshipEfficiency(),
        TFIDFRedundancy(),
        InformationGain(),
        EdgeUtilization(adjacency),
        StateSize(),
        CommunicationDepth(),
    ]


def default_synthesis_check(state: State) -> bool:
    """Phase 1/1.5 default: treat 14 unique facts as 'enough' to stop.
    Phase 2 should pass a scenario-aware check instead (e.g. based on
    Information Recovery against the scenario's expected facts) —
    see run_phase2.py.
    """
    return len(set(state.facts)) >= 14


class Engine:
    def __init__(
        self,
        num_agents: int = 8,
        communication_budget: int = DEFAULT_COMMUNICATION_BUDGET,
        router: Router | None = None,
    ):
        self.num_agents = num_agents
        self.communication_budget = communication_budget
        self.router = router or Router()

    def run(
        self,
        agent,
        density_level: float,
        seed: int,
        scenario_id: str | None = None,
        prompt_version: str | None = None,
        model_version: str | None = None,
        synthesis_check: Callable[[State], bool] = default_synthesis_check,
        diagnostic_metrics_factory: Callable[[list[list[int]]], list] = default_diagnostic_metrics,
    ) -> TrialRecord:
        rng = random.Random(seed)
        adjacency = generate_connected_erdos_renyi(self.num_agents, density_level, rng)
        telemetry = Telemetry(diagnostic_metrics_factory(adjacency))

        state = State()
        current_node = 0
        message_index = 0
        budget_exhausted = False

        while True:
            if is_budget_exhausted(message_index, self.communication_budget):
                budget_exhausted = True
                break
            if synthesis_check(state):
                break

            next_node = self.router.next_node(current_node, adjacency, rng)
            context = Context(
                agent_id=current_node,
                message_index=message_index,
                communication_budget=self.communication_budget,
                density_level=density_level,
                current_node=current_node,
                next_node=next_node,
                scenario_id=scenario_id,
            )
            prior_state = state.copy()
            output = agent.process(state, context)
            telemetry.record_message(output, prior_state, context)

            state = output.state
            current_node = next_node
            message_index += 1

        final_response = state.facts[-1] if state.facts else ""

        return TrialRecord(
            seed=seed,
            density_level=density_level,
            realized_density=realized_density(adjacency),
            topology=adjacency,
            scenario_id=scenario_id,
            prompt_version=prompt_version,
            model_version=model_version,
            budget_exhausted=budget_exhausted,
            diagnostic_metrics=telemetry.diagnostic_results(),
            final_response=final_response,
            final_facts=list(state.facts),
            per_message_metadata=telemetry.per_message_metadata,
        )
