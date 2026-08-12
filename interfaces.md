# Interface Contracts

**Status:** Frozen contracts, written after `experiment.md` and before any implementation. These interfaces must not change between Phase 1 (`DummyAgent`) and Phase 2 (`PureAgent`) — that invariance is the point of the design. Signatures only; no logic.

---

## State

```python
class State:
    """Shared, append-only record of accumulated facts and metadata.
    Passed into every agent call and returned, updated, after it."""
    facts: list[str]
    last_modifier: int
    metadata: dict  # trial_id, density_level, message_index, etc.
```

## Context

```python
class Context:
    """Read-only information about the current position in the run,
    given to an agent alongside State. Never mutated by the agent."""
    agent_id: int
    message_index: int
    communication_budget: int
    density_level: float
```

## AgentOutput

```python
@dataclass
class AgentOutput:
    """Everything an agent call produces, kept separate from State
    so telemetry can capture message-level detail without stuffing
    it into the shared state object."""
    state: State           # updated shared state
    message: str            # the content this agent emitted this turn
    metadata: dict          # tokens_used, latency_ms, confidence, tool_calls, etc.
                             # (DummyAgent may leave most of this empty; PureAgent
                             # populates it from the underlying model response)
```

## Agent

```python
class Agent(Protocol):
    def process(self, state: State, context: Context) -> AgentOutput:
        """Given current shared state and read-only context, return
        an AgentOutput. Must not read or write anything outside
        state/context (no global RNG dependence beyond what's seeded
        for this trial, no topology awareness, no density awareness).
        Must not branch on context.message_index (see Invariants)."""
        ...
```

Two implementations, identical signature:

```python
class DummyAgent(Agent):
    """Phase 1 / Phase 1.5 only. Returns a random unique token as its
    message, wraps it into State, leaves metadata empty. No reasoning,
    no redundancy, no depth- or density-awareness."""
    ...

class PureAgent(Agent):
    """Phase 2 only. Deterministic, rule-based greedy-novelty policy —
    zero external dependencies, zero API calls (experiment.md §0, §8.2).
    The policy version is fixed and logged per the Reproducibility
    section, in place of a model/prompt version."""
    ...
```

## Router

```python
class Router(Protocol):
    def next_node(self, current_node: int, adjacency: AdjacencyMatrix,
                  rng: random.Random) -> int:
        """Select the next node to receive control, given the current
        node and the graph's adjacency matrix. Must use only the
        trial-scoped rng passed in — never the global random module —
        so trials are independently reproducible from their seed."""
        ...
```

## Topology / Density

```python
class TopologyGenerator(Protocol):
    def generate(self, num_agents: int, target_density: float,
                 rng: random.Random) -> AdjacencyMatrix:
        """Produce a connected Erdős–Rényi (G(n, p)) adjacency matrix
        for num_agents at the requested density — locked per
        experiment.md §4. Edges are sampled uniformly at random at
        the density implied by target_density; disconnected samples
        are rejected and resampled (using the same rng, so the
        rejection loop stays reproducible from the trial's seed)
        until a connected graph is obtained. This is the ONLY
        topology-generation procedure used anywhere in this project
        — there is no second implementation, no shape parameter, and
        no code path that produces a hub/ring/clique graph. That is
        what keeps density the sole independent variable."""
        ...
```

## Metric

```python
class Metric(Protocol):
    def update(self, state: State, prior_state: State,
               context: Context) -> None:
        """Called once per message with the state before and after an
        agent's process() call. Accumulates whatever the metric needs
        internally."""
        ...

    def result(self) -> dict:
        """Return this metric's value(s) for the completed trial.
        Must not depend on any other Metric instance's internal state —
        metrics are computed independently (see experiment.md §5.1,
        outcome/diagnostic separation: no metric here may be defined
        as a function of another metric's result)."""
        ...
```

Concrete metrics implementing this contract (Phase 0): `RelationshipEfficiency`, `TFIDFRedundancy`, `InformationGain`, `EdgeUtilization`, `StateSize`, `CommunicationDepth`.

Outcome metrics (`TaskSuccess`, `JudgeScorePrimary`, `JudgeScoreSecondary`, `TokenCost`, `Latency`) implement the same `Metric` contract but are computed from the run's final state/log, never from the diagnostic metrics' results.

## Dataset

```python
@dataclass
class IncidentScenario:
    """One frozen item from datasets/incident_01.json .. incident_10.json
    (experiment.md §6). Loaded once; never mutated during a trial."""
    scenario_id: str
    per_agent_knowledge: dict[int, str]   # agent_id -> initial partial knowledge
    expected_facts: list[str]              # ground truth for Information Recovery (§7.1)
    ground_truth_sections: dict[str, str]  # root_cause, evidence, impact, fix, verification_plan


class DatasetLoader(Protocol):
    def load(self, scenario_id: str) -> IncidentScenario: ...
    def all_ids(self) -> list[str]: ...  # fixed 10-item corpus, order stable across runs
```

## Telemetry

```python
class Telemetry:
    """Owns the set of Metric instances for a trial, feeds them
    state transitions, and produces the per-trial record specified
    in experiment.md §12 (Reproducibility)."""
    def record_message(self, output: AgentOutput, prior_state: State,
                        context: Context) -> None: ...
    def finalize(self) -> TrialRecord: ...
```

```python
class TrialRecord:
    seed: int
    density_level: float
    topology: AdjacencyMatrix
    scenario_id: str            # which of the 10 frozen dataset items (experiment.md §6)
    prompt_version: str
    model_version: str | None   # None for DummyAgent trials
    outcome_metrics: dict        # includes Information Recovery (experiment.md §7.1)
    diagnostic_metrics: dict
    final_response: str
```

## Engine

```python
class Engine:
    def __init__(self, num_agents: int, communication_budget: int,
                 topology_generator: TopologyGenerator,
                 router: Router):
        ...

    def run(self, agent: Agent, density_level: float, seed: int,
            scenario_id: str | None = None) -> TrialRecord:
        """Execute one trial at the given density level and seed,
        using the given agent implementation. scenario_id is required
        from Phase 2 onward (selects the frozen dataset item per
        experiment.md §6); Phase 1/1.5 DummyAgent runs can omit it,
        since DummyAgent doesn't consume scenario content. This
        signature is identical whether agent is a DummyAgent
        (Phase 1/1.5) or a PureAgent (Phase 2) — that is the entire
        point of the dependency inversion. Engine has zero knowledge
        of what kind of agent it's driving."""
        ...
```

---

## Invariants this file exists to protect

1. `Engine.run(agent, ...)` never branches on the type of `agent`.
2. No `Metric` implementation reads another `Metric`'s output.
3. `Router` and `TopologyGenerator` receive an explicit `rng`, never touch the global `random` module — required for the independent-trial seed policy in `experiment.md` §7.
4. `Agent.process` receives no information about density, topology, or communication depth beyond what's explicitly passed in `Context` — and `Context` does not currently expose depth in a way an agent could branch on (`message_index` exists for logging, not for agent-side conditional behavior; if an agent implementation is found to branch on it, that's a protocol violation to flag, not a feature).
