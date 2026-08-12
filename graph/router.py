"""Router. Uses only the trial-scoped rng passed in — never the global
random module — per interfaces.md invariant 3.
"""
import random


class Router:
    def next_node(
        self,
        current_node: int,
        adjacency: list[list[int]],
        rng: random.Random,
    ) -> int:
        outbound = [j for j in range(len(adjacency)) if adjacency[current_node][j] == 1]
        if not outbound:
            # Structural dead end (shouldn't occur for a strongly connected
            # graph mid-walk, but guarded defensively): fall back to node 0.
            current_node = 0
            outbound = [j for j in range(len(adjacency)) if adjacency[0][j] == 1]
        return rng.choice(outbound)
