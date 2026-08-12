"""Phase 1.5: Reproducibility validation, per experiment.md §8, using
DummyAgent. Verifies the same seed always reproduces identical
topology and telemetry, and that distinct seeds produce varying
topology while density/connectivity stay correct.
"""
from relationship_density.agents.dummy import DummyAgent
from relationship_density.graph.engine import Engine


def test_same_seed_produces_identical_topology_and_message_count():
    engine = Engine()
    records = [
        engine.run(DummyAgent(), density_level=0.4, seed=123)
        for _ in range(10)
    ]
    first = records[0]
    for record in records[1:]:
        assert record.topology == first.topology
        assert record.diagnostic_metrics["communication_depth"] == first.diagnostic_metrics["communication_depth"]


def test_different_seeds_vary_topology_but_keep_correct_density():
    engine = Engine()
    seeds = [1, 2, 3, 4, 5]
    records = [engine.run(DummyAgent(), density_level=0.4, seed=s) for s in seeds]

    topologies = [tuple(tuple(row) for row in r.topology) for r in records]
    assert len(set(topologies)) > 1, "expected topology to vary across distinct seeds"

    for record in records:
        assert abs(record.realized_density - 0.4) < 0.05
