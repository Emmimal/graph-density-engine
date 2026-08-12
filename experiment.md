# Experiment Design: Relationship Density in Multi-Agent Systems

**Status:** Frozen pre-registration. Any change made after Phase 2 execution begins must be logged in the "Amendments" section at the bottom, with a timestamp and reason.

**§0. Project constraint (locked, applies to every phase):** this project uses zero external dependencies and makes zero API calls. Phase 2 does not call a real language model — it uses a deterministic, fully local, rule-based agent policy (§8.2). This is a design constraint carried over from the author's broader body of work, not a compromise adopted partway through — see §8.2 for why this also resolves the original "simulator encodes its own conclusion" problem without needing an API.

---

## 1. Research Question

Does relationship density — the ratio of active communication edges to maximum possible edges in a fixed-size agent network — explain variation in multi-agent task performance better than agent count or topology shape alone?

## 2. Hypotheses

- **H₀ (null):** Relationship density has no measurable effect on task outcomes beyond random variation, once agent count, topology family, task, agent policy, and routing policy are held constant.
- **H₁ (alternative):** Relationship density significantly affects communication efficiency and downstream task performance under otherwise identical conditions.

The experiment must be capable of returning either result. A failure to reject H₀ is a valid, reportable outcome, not a failed experiment.

## 3. Independent Variables

- **Relationship density:** swept at 20%, 40%, 60%, 80%, 100% of maximum possible directed edges for a fixed 8-node graph.

That is the only variable this experiment is designed to isolate. If topology *shape* (chain/mesh/clique) is reintroduced later, it must be a separate, explicitly labeled experiment — not mixed into this density sweep.

## 4. Controlled Variables

Held constant across every density level and every trial:

- Number of agents (8)
- **Topology family — locked: connected Erdős–Rényi random graphs, G(n, p).** At each target density, edges are sampled uniformly at random; disconnected samples are rejected and resampled until a connected graph is obtained. This is the sole graph-generation procedure used at every density level, so density is not confounded with topology shape (e.g. hub vs. ring vs. random) at a given edge count.
- Task / prompt content (see §5)
- Evaluation dataset (see §6)
- Agent policy — locked: a deterministic, rule-based greedy-novelty policy (see §8.2, Agent Policy Specification). No model, no temperature, no API call of any kind is used anywhere in this project — see the zero-dependency note in §0.
- Routing policy (how the router selects among available outbound edges)
- Initial state (per-agent knowledge distribution, per dataset item — see §6)
- Communication budget (max messages before a run is flagged as a structural timeout)
- Random seed **policy** (see §9 — the policy itself is fixed even though seed values vary by trial)

## 5. Task Definition

**Locked task: Collaborative Technical Incident Analysis.**

**Input** (distributed across the 8 agents as per-agent partial knowledge — no single agent starts with the full picture):
- Incident log
- System architecture description
- Error traces
- Deployment timeline

**Required output** (five sections):
1. Root cause
2. Evidence
3. Impact
4. Recommended fix
5. Verification plan

This task is chosen over open-ended writing tasks specifically because it supports objective, script-checkable evaluation (§7) rather than requiring subjective judgment as the primary outcome measure.

## 6. Evaluation Datasets

**Locked before implementation.** A fixed corpus of 10 synthetic incident scenarios (`datasets/incident_01.json` ... `incident_10.json`), each containing:
- The per-agent initial knowledge distribution (what each of the 8 agents starts with)
- A ground-truth answer for all five required sections
- An explicit list of expected facts (e.g. root cause, affected service, timeline, mitigation, dependency, regression — approximately 20 discrete facts per scenario)
- An expected synthesis, for reference during manual spot-checks

**Every density level and every trial runs against the same 10-item corpus.** The dataset is not regenerated or altered after freezing — doing so would reintroduce exactly the kind of uncontrolled variation this protocol exists to eliminate. Trials are distributed across the corpus (e.g. trial N uses `incident_{(N mod 10) + 1}`) so that all density levels are evaluated against an identical, balanced set of scenarios.

## 7. Metrics

### 7.1 Outcome metrics (what readers care about)

| Metric | What it measures |
|---|---|
| Task success | Whether the run reaches a valid synthesis state before the communication budget is exhausted |
| **Information recovery (primary)** | Recovered expected facts / total expected facts, per §6's per-scenario fact list. This is the sole quality outcome metric — there is no secondary LLM judge, since the project makes zero API calls (§0). |
| Messages to threshold | Number of messages elapsed before Recovery first reached 0.7, replayed from the full-budget run (added per Amendment 2 — not subject to the ceiling effect that can mask Recovery differences). `None`/not-reached if the budget ends first. |
| Token cost | Total tokens consumed across the run (word-count proxy — see §8.2; no LLM tokenizer is used) |
| Latency | Wall-clock time to synthesis or timeout |

### 7.2 Diagnostic metrics (why outcomes changed)

| Metric | Purpose | Known limitation |
|---|---|---|
| Relationship Efficiency | Useful (unique state-updating) messages / total inter-agent messages | "Useful" is an operational heuristic, not a semantic judgment |
| TF-IDF Redundancy | Lexical overlap between a new fact and accumulated state | Captures lexical overlap, not semantic contradiction — see negation limitation below |
| Information Gain | Novel tokens or novel facts / total tokens or facts per message | Sensitive to tokenization choices |
| Edge Utilization | Actually-used edges / configured edges at a given density | High configured density does not guarantee high realized communication |
| State Size | Size of accumulated shared state over time | Proxy for context/token pressure, not a direct outcome measure |
| Communication Depth | Number of messages elapsed at any point in a run | Correlates with but is not identical to density |

**Outcome and diagnostic metrics are kept structurally separate.** No outcome metric (e.g. a performance score) is defined as a formula over diagnostic metrics. Diagnostics are analyzed as candidate predictors of outcomes (e.g. does Information Gain predict Information Recovery across density levels), not as components of them.

## 8. Procedure

1. **Phase 0 — Metric validation.** Each metric in §7 is implemented and unit-tested independently against small synthetic examples before any graph exists. TF-IDF Redundancy is tested against an adversarial set (see §8.1). No graph engine or agents involved.
2. **Phase 1 — Graph engine validation.** The topology generator (§4's locked Erdős–Rényi procedure), density controller, router, communication budget, and telemetry logging are implemented and validated using a `DummyAgent` that returns a random unique token per call — no reasoning, no redundancy, no density- or depth-awareness. This phase validates infrastructure correctness only. It makes no claim about multi-agent behavior and must not be described as an experiment in the eventual article.
3. **Phase 1.5 — Reproducibility validation.** Using the Phase 1 infrastructure (still `DummyAgent`): (a) run the same seed 10 times and verify identical topology, routing sequence, and telemetry output; (b) run distinct seeds and verify topology varies while density and connectedness remain correct. This catches infrastructure bugs before they can be mistaken for experimental noise in Phase 2.
4. **Phase 2 — Experiment execution.** `DummyAgent` is replaced with `PureAgent` (returning `AgentOutput`, see `interfaces.md` and §8.2 below) behind the identical `engine.run(agent)` interface. Topology family, routing, density levels, communication budget, dataset corpus, and all metric implementations remain unchanged from Phase 1/1.5. This is the only phase whose results are used to evaluate H₀/H₁.

### 8.2 Agent Policy Specification (Phase 2)

Locked, deterministic, zero-dependency, zero-API. Each agent starts with a small fixed list of "own facts" (its partition of the scenario's `expected_facts`, per §6). On its turn:

1. If the agent has own facts it has not yet contributed, it contributes whichever one has the **lowest maximum TF-IDF cosine similarity** to any fact currently in shared state — i.e. it greedily seeks novelty.
2. If the agent has already contributed all of its own facts, it repeats whichever own fact has the **highest TF-IDF cosine similarity** to the most recently added shared fact — a deterministic "stay on topic" rule, not a random pick.

This is the mechanism the experiment measures: at higher density a fixed-size, fixed-knowledge 8-agent network gets visited more often per agent before the synthesis/budget condition is reached, so agents exhaust their own facts sooner and spend a larger share of turns in step 2 (repeating). The redundancy/novelty dynamic is a genuine consequence of density and finite knowledge, not an assumption injected into the agent's logic — this is the specific fix for the "simulator encodes its own conclusion" problem identified earlier in this project's design review, achieved without an API call.

### 8.1 Adversarial TF-IDF validation set (Phase 0)

| Pair | Expected similarity |
|---|---|
| "Database timeout occurred" / "Database timeout happened" | High |
| "Database timeout occurred" / "Database timeout was avoided" | High lexical similarity, opposite meaning |
| "Database timeout occurred" / "Redis cache timeout" | Medium |
| "Database timeout occurred" / "The API returned 500" | Low |

Documented limitation: TF-IDF captures lexical overlap rather than semantic contradiction. This is acceptable here because the metric estimates communication redundancy (are agents re-treading the same ground), not factual correctness (is the content accurate).

## 9. Randomization & Seed Policy

**Locked.** For each density level, execute N independent trials using distinct random seeds. Report the mean and standard deviation (or confidence interval) for every outcome and diagnostic metric. Single-reseed-per-level is rejected in favor of measuring run-to-run variability directly.

## 10. Trial Count & Success Criteria

**Trial count — locked.** Run 10 independent trials per density level (50 total experimental runs across five density levels), distributed across the 10-item dataset corpus (§6). This count is fixed before execution and will not be increased based on intermediate results. It may only be amended (with a logged reason, per §15) before Phase 2 execution begins — never during or after.

**Success criteria — locked.** The experiment is considered conclusive if and only if:
- All density levels complete the planned 10 trials.
- Outcome metrics can be summarized with finite variance estimates (no runs so degenerate — e.g. all-timeout — that variance is undefined).
- Observed differences between density levels are large enough to be distinguished from run-to-run variability (per the analysis plan in §11).

If these conditions are not met, the result is reported as inconclusive — not as evidence for either H₀ or H₁.

## 11. Statistical Analysis Plan

**Locked.** For each outcome and diagnostic metric, report mean ± standard deviation per density level, plotted with error bars or shaded confidence intervals rather than single-point values. Density-level comparisons are treated as distinguishable only when their variability bands (e.g. ±1 SD) do not substantially overlap — no p-value threshold is invented for a 5-condition, N=10 design; the visual/interval comparison is the reported evidence, and this limitation is stated explicitly in the article rather than dressed up with unwarranted statistical formality.

## 12. Reproducibility

Every trial records, at minimum:
- Random seed
- Density level and generated topology configuration
- Dataset item used (§6)
- Prompt version
- Agent policy version (fixed at §8.2's specification for the whole project; recorded per trial for forward compatibility if the policy is ever revised)
- All metric outputs (outcome and diagnostic)
- The final synthesized response

This record enables exact reruns and post-hoc inspection of any anomalous trial (e.g. an unexpected timeout or an outlier judge score).

## 13. Threats to Validity

**Internal validity**
- TF-IDF measures lexical rather than semantic similarity (see §8.1).
- The agent policy is deterministic, so run-to-run variance within a fixed (density, seed, scenario) triple is exactly zero by construction — all observed variance across trials at a density level comes from topology sampling and scenario rotation, not from any agent-behavior noise. This is a stronger reproducibility guarantee than a real-model version would have, but it also means the experiment cannot speak to how a stochastic (e.g. LLM-based) agent population would behave — that's an explicit scope boundary, not an oversight.
- "Usefulness" of a message (for Relationship Efficiency) requires an operational definition, stated explicitly wherever it's used.
- The fact-recovery ground truth (§6) is authored by the experimenter and could itself be incomplete or ambiguous for edge-case facts.

**External validity**
- Results are based on a single task domain (technical incident analysis).
- Results are based on a single model family/version.
- Agent count is fixed at 8; findings may not generalize to smaller or larger networks.
- Topology family is fixed to Erdős–Rényi; findings are specific to this topology family and may not generalize to structured topologies (hub, ring, hierarchical).

**Construct validity**
- Relationship density is operationalized as the ratio of active communication edges to maximum possible edges. Other reasonable operationalizations (e.g. weighting by message frequency rather than edge existence) may produce different results.

## 14. Limitations

- Phase 1 / Phase 1.5 results characterize infrastructure correctness only and carry no empirical claim about multi-agent behavior.
- Findings are scoped to the configurations actually evaluated (5 density levels, one topology family, fixed agent count, one task domain, 10 dataset items) and should not be generalized beyond them without qualification.

## 15. Amendments

**Amendment 1 (post-Phase-2-execution).** `InformationRecovery`'s per-fact keyword-overlap threshold was found to be miscalibrated at 0.6: facts describing the same incident share entity tokens (service names, timestamps, config values), causing sharing one real fact to spuriously credit 2-3 unrelated facts as "recovered." Verified directly (sharing exactly 1 fact recovered 3 at threshold=0.6; corrected to exactly 1 at threshold=0.75/0.85). Threshold raised to 0.85. This is a metric-implementation bug fix, not a change to what is being measured.

**Amendment 2 (post-Phase-2-execution).** The Phase 2 synthesis exit condition (stop once Information Recovery ≥ 0.7) was discovered to be circular: since Recovery was both the stopping rule and the primary outcome metric, every trial's recovery value was mechanically quantized to whichever fact-count first crossed the threshold (only 2 distinct values were observed across the first 50-trial run). This made Recovery structurally incapable of showing a density effect regardless of the true underlying relationship. Fixed by removing the early-exit condition entirely — every Phase 2 trial now runs to the full communication budget (35 messages), and Recovery is measured once, at the end, as a genuine continuous outcome. `TaskSuccess` is correspondingly redefined from "budget not exhausted" (now trivially always false) to "recovery threshold reached at any point within budget," read from the new `messages_to_threshold` diagnostic.

**Amendment 3 (observation, no further code change yet).** Under the full-budget design (Amendment 2), Recovery now shows a ceiling effect: nearly all trials reach 90-100% recovery regardless of density, because the 35-message budget is generous relative to a 17-fact/8-agent scenario. This may be masking a real density effect rather than demonstrating its absence. Candidate fixes for a future amendment, not yet applied: reduce the communication budget, increase facts per scenario relative to agent count, or treat `messages_to_threshold` (which is not subject to the ceiling effect) as a co-primary outcome alongside Recovery.
