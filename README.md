# graph-density-engine

A pure-Python, zero-dependency framework for testing how communication topology affects multi-agent LLM systems — Erdős–Rényi graph generation, deterministic agent policies, and reproducible density sweeps in one pipeline.

![Python Version](https://img.shields.io/badge/python-3.12-blue) ![License](https://img.shields.io/badge/license-MIT-green)

Most multi-agent tutorials pick a communication topology by instinct — a fully connected mesh because it "feels safer," or a chain because it's easy to trace. This library isolates relationship density as a single, controlled variable, so you can measure whether adding communication pathways actually changes what a network can do, instead of assuming it does.

Read the full write-up on Towards Data Science → Graph Engineering Isn't About More Connections — It's About Which Ones Get Used

## What It Does

```
Topology Generator → Router → Agent Policy → Shared State → Telemetry → Diagnostic Metrics
   (Erdos-Renyi,      (picks    (PureAgent:
    density-locked)    next      novelty-seeking,
                       speaker)  then repeat)
```

Five components, one `Engine.run()` call:

| Component | Job |
|---|---|
| Topology Generator | Connected Erdős–Rényi random graphs at a locked target density, rejecting disconnected samples |
| Router | Picks the next speaker from the current node's open outbound edges |
| Agent Policy | Deterministic greedy-novelty-then-repeat policy (`PureAgent`), or a trivial `DummyAgent` for infrastructure validation |
| Telemetry | Per-message logging feeding six diagnostic metrics |
| Diagnostic Metrics | Relationship Efficiency, TF-IDF Redundancy, Information Gain, Edge Utilization, Communication Depth, and outcome metrics (Task Success, Information Recovery) |

## Installation

```bash
git clone https://github.com/Emmimal/graph-density-engine.git
cd graph-density-engine
pip install -r requirements.txt   # pytest only — for running the test suite
```

No other dependencies, at any stage. The graph engine, agent policy, and every metric (including a from-scratch TF-IDF implementation) run on the Python standard library alone. There is no API key, no network call, and no model of any kind anywhere in the pipeline.

## Quick Start

```python
from graph_density_engine.agents.policy import PureAgent
from graph_density_engine.datasets.loader import DatasetLoader
from graph_density_engine.graph.engine import Engine

loader = DatasetLoader()
scenario = loader.load("incident_01")
agent = PureAgent(scenario=scenario)

engine = Engine(communication_budget=35)
record = engine.run(agent, density_level=0.6, seed=42, scenario_id=scenario.scenario_id)

print(record.diagnostic_metrics["edge_utilization"])
print(record.diagnostic_metrics["tfidf_redundancy"])
print(record.final_facts)
```

## Running the Experiment

Four phases, run in order, each validating the one before it:

| Phase | Command | What It Shows |
|---|---|---|
| 0 | `python -m pytest tests/ -v` | 16 unit tests validating every metric against synthetic examples, plus same-seed/different-seed reproducibility checks |
| 1 | `python -m graph_density_engine.run_phase1` | Graph engine sanity check across the full density sweep, using a trivial `DummyAgent` — infrastructure only, no behavioral claim |
| 2 | `python -m graph_density_engine.run_phase2 --trials 10 --out results.json` | The real experiment: 50 runs (5 density levels × 10 trials) with the deterministic `PureAgent` |
| 2b | `python -m graph_density_engine.run_experiment2 --trials 10 --out results2.json` | A separately pre-registered follow-up under a constrained communication budget |

## Configuration Reference

```python
Engine(
    num_agents=8,                  # Fixed agent count
    communication_budget=35,       # Max messages per trial before a forced timeout
    router=None,                   # Defaults to uniform-random edge selection
)

engine.run(
    agent,                         # DummyAgent or PureAgent — same interface, either works
    density_level=0.6,             # 0.0-1.0, fraction of the 56 possible directed edges (at 8 agents)
    seed=42,                       # Full reproducibility: same seed -> identical topology and trace
    scenario_id="incident_01",     # Which frozen dataset scenario to load
    synthesis_check=...,           # Optional early-exit predicate (default: run to full budget)
)
```

Density sweep used throughout the published results: `[0.2, 0.4, 0.6, 0.8, 1.0]`, 10 trials each, seeds locked before execution.

## Project Structure

```
graph-density-engine/
├── state.py, context.py, agent_output.py   # Core dataclasses
├── agents/
│   ├── dummy.py                            # Trivial agent for infrastructure validation
│   └── policy.py                           # PureAgent — deterministic novelty-seeking policy
├── graph/
│   ├── topology.py                         # Connected Erdos-Renyi generator
│   ├── router.py                           # Edge selection
│   ├── telemetry.py                        # Per-trial recording
│   └── engine.py                           # Orchestrates one trial end to end
├── metrics/
│   ├── tfidf.py                            # From-scratch TF-IDF vectorizer + cosine similarity
│   ├── relationship_efficiency.py
│   ├── tfidf_redundancy.py
│   ├── information_gain.py
│   ├── edge_utilization.py
│   └── outcome/                            # task_success.py, information_recovery.py, ...
├── datasets/
│   ├── generate_datasets.py                # Builds the frozen incident_01..10.json corpus
│   └── loader.py
├── tests/                                  # 16-test Phase 0 + reproducibility suite
├── run_phase1.py, run_phase2.py, run_experiment2.py
├── experiment.md                           # Frozen pre-registration protocol
└── interfaces.md                           # Frozen interface contracts
```

## Performance (CPU only, zero API calls)

| Operation | Measured Time |
|---|---|
| Phase 0 — 16 unit tests | under 0.25s |
| Phase 1 — 50 runs, DummyAgent | under 1s |
| Phase 2 — 50 runs, PureAgent | ~0.70s |
| API cost, any phase | $0 |

Every number above was actually measured, not estimated — reproduced independently across two machines and two operating systems with identical results to three decimal places.

## When to Use This

Worth adapting if you:

- Are choosing a multi-agent communication topology by instinct rather than measurement
- Want a template for running controlled, reproducible agent-architecture experiments without spending API budget on every iteration

Skip it if you:

- Want a specific density value to copy into production — these numbers are scoped to one task, one topology family, one agent count
- Have a bottleneck in individual agent reasoning quality rather than communication structure
- Need true model stochasticity — this framework deliberately trades that away for exact reproducibility

## Known Limitations

- The agent policy is deterministic and rule-based, not an LLM. Results describe how a fixed, rational communication strategy behaves under different topologies, not how a stochastic model population would.
- Information Recovery uses keyword-overlap matching, not semantic similarity — a documented, deliberate trade-off for staying dependency-free.
- The included dataset corpus rotates 3 incident templates across 10 scenario files.
- The default 35-message communication budget is generous relative to the included 17-fact scenarios, producing a ceiling effect — see `experiment.md` §12 for the full amendment history, including a bug that was found and fixed in the Information Recovery threshold and in an earlier circular stopping condition.
