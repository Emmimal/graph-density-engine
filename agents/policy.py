"""Phase 2 agent. Zero external dependencies, zero API calls — every
line here is stdlib plus this project's own tfidf module. See
experiment.md's Phase 2 description and the "Agent Policy
Specification" section for the rule this implements.

Design rationale (why this replaces a "real LLM" agent): the original
draft's problem was a simulator that hardcoded its own conclusion
(random redundancy injection keyed to message depth). Calling a real
LLM API would have fixed that but breaks this project's no-API,
zero-dependency constraint. This agent resolves both problems at
once: its behavior is deterministic and fully inspectable (no hidden
randomness pretending to be cognition), but the redundancy/novelty
dynamic that emerges is a genuine consequence of density and finite
per-agent knowledge — not an injected assumption.

Policy, in full:
  1. Each agent starts with a small, fixed list of "own facts" (its
     partition of the scenario's expected_facts — see datasets/).
  2. On its turn, the agent picks the not-yet-contributed own fact
     that is LEAST similar (by TF-IDF cosine similarity) to the
     facts already in shared state — i.e. it greedily seeks novelty.
  3. Once an agent has contributed every one of its own facts, it has
     nothing new to say. It falls back to re-stating the own-fact
     that is MOST similar to the most recently added shared fact
     (a deterministic "stay on topic" repeat rule, not a random pick).
  4. At higher density, a fixed 8-agent, fixed-knowledge network gets
     visited more often per agent before the run's synthesis/budget
     condition is reached, so agents exhaust their own facts sooner
     and spend a larger share of their turns in step 3 (repeating).
     That is the mechanism this experiment measures — it is not
     injected as a rule that says "redundancy increases with depth";
     it falls out of turn frequency vs. a fixed knowledge pool size.
"""
from ..agent_output import AgentOutput
from ..context import Context
from ..metrics.tfidf import TFIDFVectorizer, cosine_similarity
from ..state import State


class PureAgent:
    """Deterministic, rule-based agent. No randomness, no network
    calls, no external dependencies beyond this project's own code."""

    def __init__(self, scenario, agent_id: int | None = None):
        self.scenario = scenario
        self.agent_id = agent_id
        self._contributed: dict[int, set[str]] = {}

    def _own_facts(self, agent_id: int) -> list[str]:
        return list(self.scenario.per_agent_knowledge.get(str(agent_id), []))

    def process(self, state: State, context: Context) -> AgentOutput:
        agent_id = self.agent_id if self.agent_id is not None else context.agent_id
        own_facts = self._own_facts(agent_id)
        contributed = self._contributed.setdefault(agent_id, set())
        remaining = [f for f in own_facts if f not in contributed]

        shared_facts = state.facts
        message = self._select_message(remaining, own_facts, shared_facts)

        new_state = state.copy()
        is_repeat = message in contributed
        if not is_repeat:
            new_state.facts.append(message)
            new_state.last_modifier = agent_id
        contributed.add(message)

        return AgentOutput(
            state=new_state,
            message=message,
            metadata={
                "tokens_used": len(message.split()),  # word-count proxy — no LLM tokenizer, no dependency
                "latency_ms": 0.0,  # local computation; not a meaningful metric here, kept for schema parity
                "is_repeat": is_repeat,
            },
        )

    def _select_message(self, remaining: list[str], own_facts: list[str], shared_facts: list[str]) -> str:
        if remaining:
            return self._most_novel(remaining, shared_facts)
        if not own_facts:
            return "NO_KNOWLEDGE_AVAILABLE"
        return self._most_on_topic(own_facts, shared_facts)

    @staticmethod
    def _most_novel(candidates: list[str], shared_facts: list[str]) -> str:
        """Pick the candidate with the LOWEST max similarity to
        anything already in shared state — the most novel one."""
        if not shared_facts:
            return candidates[0]
        corpus = shared_facts + candidates
        vectorizer = TFIDFVectorizer(corpus)
        shared_vectors = [vectorizer.vectorize(f) for f in shared_facts]

        best_candidate = candidates[0]
        best_score = float("inf")
        for candidate in candidates:
            cand_vec = vectorizer.vectorize(candidate)
            max_sim = max(cosine_similarity(cand_vec, sv) for sv in shared_vectors)
            if max_sim < best_score:
                best_score = max_sim
                best_candidate = candidate
        return best_candidate

    @staticmethod
    def _most_on_topic(candidates: list[str], shared_facts: list[str]) -> str:
        """Repeat rule: pick the own-fact with the HIGHEST similarity
        to the most recently added shared fact (stay on topic),
        falling back to the first own fact if state is empty."""
        if not shared_facts:
            return candidates[0]
        last_fact = shared_facts[-1]
        corpus = [last_fact] + candidates
        vectorizer = TFIDFVectorizer(corpus)
        last_vec = vectorizer.vectorize(last_fact)

        best_candidate = candidates[0]
        best_score = -1.0
        for candidate in candidates:
            sim = cosine_similarity(last_vec, vectorizer.vectorize(candidate))
            if sim > best_score:
                best_score = sim
                best_candidate = candidate
        return best_candidate
