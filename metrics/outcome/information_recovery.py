"""Outcome metric: Information Recovery (primary). See experiment.md
§7.1. Recovered expected facts / total expected facts, per the
scenario's ground-truth fact list (experiment.md §6). Chosen over a
section-presence rubric because it measures whether density affected
what information actually reached the final synthesis.

Since this codebase deliberately avoids an LLM-as-primary-judge (per
experiment.md §7.1's "primary rubric, LLM secondary" decision), fact
recovery is checked with lexical containment against the final
response text: an expected fact is "recovered" if enough of its
keyword tokens (excluding common stopwords) appear in the response.
This is a documented heuristic, not a semantic judgment — the same
limitation TF-IDF Redundancy documents, applied here to recall
instead of similarity.

Threshold locked at 0.85 (raised from an initial 0.6 after a Phase 2
audit — see experiment.md §12 Amendments): at 0.6, facts about the
same incident that share entity tokens (service names, timestamps,
config values) cross-credited each other — sharing exactly one real
fact spuriously "recovered" two unrelated ones. At 0.85 that no
longer happens; verified against the same test case.
"""
import re

_STOPWORDS = {
    "the", "a", "an", "is", "was", "were", "are", "of", "to", "in", "on",
    "and", "or", "for", "with", "at", "by", "from", "that", "this", "it",
    "as", "be", "has", "had", "have", "not", "but", "which", "when",
}


def _keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 2}


class InformationRecovery:
    name = "information_recovery"

    def compute(self, expected_facts: list[str], final_response: str, threshold: float = 0.85) -> dict:
        response_keywords = _keywords(final_response)
        recovered = []
        for fact in expected_facts:
            fact_keywords = _keywords(fact)
            if not fact_keywords:
                continue
            overlap = len(fact_keywords & response_keywords) / len(fact_keywords)
            if overlap >= threshold:
                recovered.append(fact)

        rate = len(recovered) / len(expected_facts) if expected_facts else 0.0
        return {
            "recovery_rate": rate,
            "recovered_facts": recovered,
            "expected_fact_count": len(expected_facts),
        }
