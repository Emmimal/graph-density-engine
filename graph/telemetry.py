"""Telemetry owns the set of diagnostic Metric instances for a trial,
feeds them state transitions, and produces the per-trial record
specified in experiment.md §12 (Reproducibility).
"""
from dataclasses import dataclass, field

from ..agent_output import AgentOutput
from ..context import Context
from ..state import State


@dataclass
class TrialRecord:
    seed: int
    density_level: float
    realized_density: float
    topology: list[list[int]]
    scenario_id: str | None
    prompt_version: str | None
    model_version: str | None
    budget_exhausted: bool
    outcome_metrics: dict = field(default_factory=dict)
    diagnostic_metrics: dict = field(default_factory=dict)
    final_response: str = ""
    final_facts: list = field(default_factory=list)
    per_message_metadata: list = field(default_factory=list)


class Telemetry:
    def __init__(self, diagnostic_metrics: list):
        self._metrics = diagnostic_metrics
        self._per_message_metadata: list[dict] = []

    def record_message(self, output: AgentOutput, prior_state: State, context: Context) -> None:
        for metric in self._metrics:
            metric.update(output, prior_state, context)
        self._per_message_metadata.append(output.metadata)

    def diagnostic_results(self) -> dict:
        return {metric.name: metric.result() for metric in self._metrics}

    @property
    def per_message_metadata(self) -> list[dict]:
        return list(self._per_message_metadata)
