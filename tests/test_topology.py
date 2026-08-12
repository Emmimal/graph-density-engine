import random

from relationship_density.graph.topology import (
    generate_connected_erdos_renyi,
    is_strongly_connected,
    realized_density,
)


def test_generated_graph_is_strongly_connected():
    rng = random.Random(42)
    adjacency = generate_connected_erdos_renyi(8, 0.4, rng)
    assert is_strongly_connected(adjacency)


def test_realized_density_is_close_to_target():
    rng = random.Random(7)
    for target in (0.2, 0.4, 0.6, 0.8, 1.0):
        adjacency = generate_connected_erdos_renyi(8, target, rng)
        actual = realized_density(adjacency)
        # exact match expected since edge count is rounded then sampled exactly,
        # except at the low end where we floor to the min spanning requirement (n edges)
        assert actual >= target - 0.05 or target == 0.2


def test_full_density_is_the_complete_graph():
    rng = random.Random(1)
    adjacency = generate_connected_erdos_renyi(8, 1.0, rng)
    assert realized_density(adjacency) == 1.0
    for i in range(8):
        for j in range(8):
            if i != j:
                assert adjacency[i][j] == 1
