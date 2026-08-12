"""Diagnostic metric: Information Gain. See experiment.md §7.2.

Defined at fact granularity (novel facts / total facts contributed)
rather than token granularity, to stay a genuinely separate signal
from TF-IDF Redundancy's continuous similarity score rather than its
mirror image — see the granularity note from design discussion.
A fact counts as "novel" if it is not an exact string match of any
fact already in prior_state.facts.
"""
from ..agent_output import AgentOutput
from ..context import Context
from ..state import State


class InformationGain:
    name = "information_gain"

    def __init__(self):
        self._total_facts_contributed = 0
        self._novel_facts_contributed = 0

    def update(self, output: AgentOutput, prior_state: State, context: Context) -> None:
        new_facts = output.state.facts[len(prior_state.facts):]
        prior_set = set(prior_state.facts)
        for fact in new_facts:
            self._total_facts_contributed += 1
            if fact not in prior_set:
                self._novel_facts_contributed += 1
            prior_set.add(fact)

    def result(self) -> dict:
        gain = (
            self._novel_facts_contributed / self._total_facts_contributed
            if self._total_facts_contributed else 0.0
        )
        return {
            "information_gain": gain,
            "novel_facts": self._novel_facts_contributed,
            "total_facts_contributed": self._total_facts_contributed,
        }
