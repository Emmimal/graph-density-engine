from relationship_density.agent_output import AgentOutput
from relationship_density.context import Context
from relationship_density.metrics.edge_utilization import EdgeUtilization
from relationship_density.state import State


def test_utilization_counts_distinct_edges_used():
    adjacency = [[0, 1, 1], [1, 0, 1], [1, 1, 0]]  # 6 configured edges
    metric = EdgeUtilization(adjacency)
    output = AgentOutput(state=State(), message="")
    ctx1 = Context(agent_id=0, message_index=0, communication_budget=35,
                    density_level=1.0, current_node=0, next_node=1)
    ctx2 = Context(agent_id=1, message_index=1, communication_budget=35,
                    density_level=1.0, current_node=0, next_node=1)  # same edge again
    metric.update(output, State(), ctx1)
    metric.update(output, State(), ctx2)
    result = metric.result()
    assert result["used_edges"] == 1  # repeated edge only counted once
    assert result["configured_edges"] == 6
    assert abs(result["utilization"] - (1 / 6)) < 1e-9
