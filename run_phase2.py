"""Phase 2 — the real experiment. Swaps DummyAgent for PureAgent
(agents/policy.py); everything else (topology family, routing,
density levels, communication budget, dataset corpus, metric
implementations) is identical to Phase 1/1.5, per experiment.md §8
and interfaces.md.

Zero external dependencies, zero API calls, zero cost. Safe to run
the full 50-trial sweep locally as many times as you want.

Usage: python -m relationship_density.run_phase2 [--trials N] [--out results.json]
"""
import argparse
import json
import statistics
import time

from .agents.policy import PureAgent
from .datasets.loader import DatasetLoader
from .graph.engine import Engine
from .metrics.outcome.information_recovery import InformationRecovery
from .metrics.outcome.latency import Latency
from .metrics.outcome.task_success import TaskSuccess
from .metrics.outcome.token_cost import TokenCost

DENSITY_LEVELS = [0.2, 0.4, 0.6, 0.8, 1.0]


def _run_to_budget_check(state) -> bool:
    """No early exit. Every trial runs to the full communication
    budget. This is a deliberate design correction (see
    experiment.md §12 Amendments): using Information Recovery as
    BOTH the stopping rule and the outcome metric was circular —
    every run stopped the instant it crossed the threshold, which
    quantizes recovery to whichever fact-count first cleared 70%
    (only 2 distinct values were ever observed across 50 trials).
    Running to a fixed budget makes recovery a genuine continuous
    outcome and lets messages-to-threshold be analyzed separately
    as its own diagnostic, without conflating the two."""
    return False


def run_trial(engine: Engine, scenario, density: float, seed: int) -> dict:
    agent = PureAgent(scenario=scenario)

    start = time.monotonic()
    record = engine.run(
        agent,
        density_level=density,
        seed=seed,
        scenario_id=scenario.scenario_id,
        prompt_version="pure-agent-policy-v1",
        model_version=None,  # no model — deterministic local policy, see agents/policy.py
        synthesis_check=_run_to_budget_check,
    )
    wall_clock_ms = (time.monotonic() - start) * 1000

    recovery_result = InformationRecovery().compute(scenario.expected_facts, " ".join(record.final_facts))
    messages_to_threshold = _messages_to_threshold(scenario, record.final_facts, threshold=0.7)

    outcome = {
        "task_success": TaskSuccess().compute(messages_to_threshold["reached"]),
        "information_recovery": recovery_result,
        "messages_to_threshold": messages_to_threshold,
        "token_cost": TokenCost().compute(record.per_message_metadata),
        "latency": Latency().compute(record.per_message_metadata, wall_clock_ms),
    }

    return {
        "seed": seed,
        "density_level": density,
        "realized_density": record.realized_density,
        "scenario_id": record.scenario_id,
        "budget_exhausted": record.budget_exhausted,
        "outcome_metrics": outcome,
        "diagnostic_metrics": record.diagnostic_metrics,
        "final_response": record.final_response,
    }


def _messages_to_threshold(scenario, final_facts: list, threshold: float = 0.7) -> dict:
    """Replay recovery incrementally over the trial's accumulated
    facts (in order) to find how many messages it took to first
    clear `threshold` — kept as a separate diagnostic now that the
    engine no longer stops early on this condition. None if the
    threshold was never reached within the budget."""
    recovery_metric = InformationRecovery()
    accumulated = []
    for index, fact in enumerate(final_facts, start=1):
        accumulated.append(fact)
        result = recovery_metric.compute(scenario.expected_facts, " ".join(accumulated))
        if result["recovery_rate"] >= threshold:
            return {"messages": index, "reached": True}
    return {"messages": None, "reached": False}


def summarize(trials: list[dict]) -> dict:
    def mean_std(values):
        if not values:
            return {"mean": None, "std": None}
        mean = statistics.fmean(values)
        std = statistics.pstdev(values) if len(values) > 1 else 0.0
        return {"mean": mean, "std": std}

    by_density = {}
    for density in DENSITY_LEVELS:
        level_trials = [t for t in trials if t["density_level"] == density]
        by_density[density] = {
            "n_trials": len(level_trials),
            "task_success_rate": mean_std(
                [1.0 if t["outcome_metrics"]["task_success"]["success"] else 0.0 for t in level_trials]
            ),
            "information_recovery": mean_std(
                [t["outcome_metrics"]["information_recovery"]["recovery_rate"] for t in level_trials]
            ),
            "messages_to_threshold": mean_std(
                [t["outcome_metrics"]["messages_to_threshold"]["messages"] for t in level_trials
                 if t["outcome_metrics"]["messages_to_threshold"]["reached"]]
            ),
            "token_cost": mean_std(
                [t["outcome_metrics"]["token_cost"]["total_tokens"] for t in level_trials]
            ),
            "relationship_efficiency": mean_std(
                [t["diagnostic_metrics"]["relationship_efficiency"]["efficiency"] for t in level_trials]
            ),
            "tfidf_redundancy": mean_std(
                [t["diagnostic_metrics"]["tfidf_redundancy"]["mean_redundancy"] for t in level_trials]
            ),
            "information_gain": mean_std(
                [t["diagnostic_metrics"]["information_gain"]["information_gain"] for t in level_trials]
            ),
            "edge_utilization": mean_std(
                [t["diagnostic_metrics"]["edge_utilization"]["utilization"] for t in level_trials]
            ),
        }
    return by_density


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=10,
                         help="Trials per density level. experiment.md §10 locks this at 10 for the real run.")
    parser.add_argument("--out", type=str, default="phase2_results.json")
    args = parser.parse_args()

    loader = DatasetLoader()
    scenario_ids = loader.all_ids()
    engine = Engine()

    all_trials = []
    for density_index, density in enumerate(DENSITY_LEVELS):
        for trial_index in range(args.trials):
            scenario = loader.load(scenario_ids[trial_index % len(scenario_ids)])
            seed = density_index * 10_000 + trial_index
            result = run_trial(engine, scenario, density, seed)
            all_trials.append(result)
            print(f"[density={density:.1f} trial={trial_index} scenario={scenario.scenario_id} seed={seed}] "
                  f"success={result['outcome_metrics']['task_success']['success']} "
                  f"recovery={result['outcome_metrics']['information_recovery']['recovery_rate']:.2f} "
                  f"redundancy={result['diagnostic_metrics']['tfidf_redundancy']['mean_redundancy']:.3f}")

    summary = summarize(all_trials)

    with open(args.out, "w") as f:
        json.dump({"trials": all_trials, "summary_by_density": summary}, f, indent=2)

    print(f"\nWrote {len(all_trials)} trial records and summary to {args.out}")
    print("\nSummary (mean ± std per density level):")
    for density, stats in summary.items():
        print(f"  density={density:.1f}  "
              f"recovery={stats['information_recovery']['mean']:.3f}±{stats['information_recovery']['std']:.3f}  "
              f"efficiency={stats['relationship_efficiency']['mean']:.3f}±{stats['relationship_efficiency']['std']:.3f}  "
              f"redundancy={stats['tfidf_redundancy']['mean']:.3f}±{stats['tfidf_redundancy']['std']:.3f}")


if __name__ == "__main__":
    main()
