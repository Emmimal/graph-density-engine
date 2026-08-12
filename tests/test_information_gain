from relationship_density.agent_output import AgentOutput
from relationship_density.context import Context
from relationship_density.metrics.information_gain import InformationGain
from relationship_density.state import State


def _ctx():
    return Context(agent_id=0, message_index=0, communication_budget=35,
                   density_level=0.4, current_node=0, next_node=1)


def test_novel_fact_counts_as_gain():
    metric = InformationGain()
    prior = State(facts=["a"])
    output = AgentOutput(state=State(facts=["a", "b"]), message="b")
    metric.update(output, prior, _ctx())
    result = metric.result()
    assert result["novel_facts"] == 1
    assert result["information_gain"] == 1.0


def test_repeated_fact_does_not_count_as_gain():
    metric = InformationGain()
    prior = State(facts=["a"])
    output = AgentOutput(state=State(facts=["a", "a"]), message="a")
    metric.update(output, prior, _ctx())
    result = metric.result()
    assert result["novel_facts"] == 0
    assert result["total_facts_contributed"] == 1
    assert result["information_gain"] == 0.0
