from relationship_density.agent_output import AgentOutput
from relationship_density.context import Context
from relationship_density.metrics.relationship_efficiency import RelationshipEfficiency
from relationship_density.state import State


def _ctx():
    return Context(agent_id=0, message_index=0, communication_budget=35,
                   density_level=0.4, current_node=0, next_node=1)


def test_useful_message_increments_efficiency():
    metric = RelationshipEfficiency()
    prior = State(facts=["a"])
    output = AgentOutput(state=State(facts=["a", "b"]), message="b")
    metric.update(output, prior, _ctx())
    result = metric.result()
    assert result["useful_messages"] == 1
    assert result["total_messages"] == 1
    assert result["efficiency"] == 1.0


def test_non_useful_message_does_not_increment_useful_count():
    metric = RelationshipEfficiency()
    prior = State(facts=["a"])
    output = AgentOutput(state=State(facts=["a"]), message="NO_NEW_INFORMATION")
    metric.update(output, prior, _ctx())
    result = metric.result()
    assert result["useful_messages"] == 0
    assert result["total_messages"] == 1
    assert result["efficiency"] == 0.0


def test_empty_metric_returns_zero_efficiency():
    metric = RelationshipEfficiency()
    result = metric.result()
    assert result["efficiency"] == 0.0
