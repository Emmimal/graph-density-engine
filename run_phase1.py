"""Phase 1 + Phase 1.5 runner. Validates the graph engine using
DummyAgent across the full density sweep. Makes no empirical claim
about multi-agent behavior — see experiment.md §8 and §14. Run this
first, before touching Phase 2 / an API key.

Usage: python -m relationship_density.run_phase1
"""
from .agents.dummy import DummyAgent
from .graph.engine import Engine

DENSITY_LEVELS = [0.2, 0.4, 0.6, 0.8, 1.0]
TRIALS_PER_LEVEL = 10


def main():
    engine = Engine()
    print("Phase 1 / 1.5 — infrastructure validation (DummyAgent, no LLM calls)\n")

    for density in DENSITY_LEVELS:
        records = [
            engine.run(DummyAgent(), density_level=density, seed=1000 * int(density * 100) + trial)
            for trial in range(TRIALS_PER_LEVEL)
        ]

        realized = [r.realized_density for r in records]
        messages = [r.diagnostic_metrics["communication_depth"]["total_messages"] for r in records]
        efficiency = [r.diagnostic_metrics["relationship_efficiency"]["efficiency"] for r in records]
        redundancy = [r.diagnostic_metrics["tfidf_redundancy"]["mean_redundancy"] for r in records]
        timeouts = sum(1 for r in records if r.budget_exhausted)

        print(f"density={density:.1f}  "
              f"realized_density(avg)={sum(realized)/len(realized):.3f}  "
              f"messages(avg)={sum(messages)/len(messages):.1f}  "
              f"efficiency(avg)={sum(efficiency)/len(efficiency):.3f}  "
              f"redundancy(avg)={sum(redundancy)/len(redundancy):.3f}  "
              f"timeouts={timeouts}/{TRIALS_PER_LEVEL}")

    print("\nThese numbers characterize the DummyAgent + graph engine only.")
    print("They carry no claim about real multi-agent behavior (experiment.md §14).")


if __name__ == "__main__":
    main()
