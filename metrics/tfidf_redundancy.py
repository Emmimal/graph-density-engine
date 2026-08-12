"""Diagnostic metric: TF-IDF Redundancy. See experiment.md §7.2 and §8.1.

Documented limitation (per experiment.md): TF-IDF captures lexical
overlap, not semantic contradiction. Acceptable here because this
metric estimates communication redundancy (are agents re-treading the
same ground), not factual correctness.
"""
from ..agent_output import AgentOutput
from ..context import Context
from ..state import State
from .tfidf import TFIDFVectorizer, cosine_similarity


class TFIDFRedundancy:
    name = "tfidf_redundancy"

    def __init__(self):
        self._per_message_scores: list[float] = []

    def update(self, output: AgentOutput, prior_state: State, context: Context) -> None:
        new_facts = output.state.facts[len(prior_state.facts):]
        if not new_facts:
            return
        prior_facts = prior_state.facts
        for fact in new_facts:
            if not prior_facts:
                self._per_message_scores.append(0.0)
                continue
            vectorizer = TFIDFVectorizer(prior_facts + [fact])
            fact_vec = vectorizer.vectorize(fact)
            max_similarity = max(
                cosine_similarity(fact_vec, vectorizer.vectorize(prior))
                for prior in prior_facts
            )
            self._per_message_scores.append(max_similarity)

    def result(self) -> dict:
        if not self._per_message_scores:
            return {"mean_redundancy": 0.0, "per_message": []}
        mean_redundancy = sum(self._per_message_scores) / len(self._per_message_scores)
        return {"mean_redundancy": mean_redundancy, "per_message": list(self._per_message_scores)}
