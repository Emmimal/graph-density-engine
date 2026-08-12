"""Locked topology family: connected Erdős–Rényi random graphs, G(n, p).
See experiment.md §4. This is the ONLY topology-generation procedure
used anywhere in this project — no hub/ring/clique code path exists —
which is what keeps density the sole independent variable.
"""
import random


def all_possible_directed_edges(num_agents: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(num_agents) for j in range(num_agents) if i != j]


def is_strongly_connected(adjacency: list[list[int]]) -> bool:
    """BFS reachability from node 0 forward and on the reversed graph.
    Strong connectivity is required so any node's contribution can, in
    principle, reach any other node given enough messages.
    """
    n = len(adjacency)

    def reachable(adj):
        seen = {0}
        frontier = [0]
        while frontier:
            node = frontier.pop()
            for neighbor in range(n):
                if adj[node][neighbor] == 1 and neighbor not in seen:
                    seen.add(neighbor)
                    frontier.append(neighbor)
        return seen

    forward_adj = adjacency
    reverse_adj = [[adjacency[j][i] for j in range(n)] for i in range(n)]
    return len(reachable(forward_adj)) == n and len(reachable(reverse_adj)) == n


def generate_connected_erdos_renyi(
    num_agents: int,
    target_density: float,
    rng: random.Random,
    max_attempts: int = 20000,
) -> list[list[int]]:
    """Sample a directed adjacency matrix by choosing edges uniformly
    at random at the density implied by target_density, rejecting and
    resampling until the result is strongly connected. Uses only the
    rng passed in (never the global random module) so a trial is
    exactly reproducible from its seed — see interfaces.md invariant 3.
    """
    edges = all_possible_directed_edges(num_agents)
    target_edge_count = round(target_density * len(edges))
    target_edge_count = max(num_agents, min(target_edge_count, len(edges)))  # need >= n for a cycle

    for _ in range(max_attempts):
        chosen = rng.sample(edges, target_edge_count)
        adjacency = [[0] * num_agents for _ in range(num_agents)]
        for (i, j) in chosen:
            adjacency[i][j] = 1
        if is_strongly_connected(adjacency):
            return adjacency

    raise RuntimeError(
        f"Could not sample a connected graph at density={target_density} "
        f"for num_agents={num_agents} within {max_attempts} attempts."
    )


def realized_density(adjacency: list[list[int]]) -> float:
    n = len(adjacency)
    edge_count = sum(sum(row) for row in adjacency)
    return edge_count / (n * (n - 1))
