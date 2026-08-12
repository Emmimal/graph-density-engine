"""Metric contract. See interfaces.md — no Metric implementation may
read another Metric's result() (outcome/diagnostic separation is
enforced by convention here: nothing in this codebase passes one
metric's output into another's constructor or update()).
"""
from typing import Protocol

from ..agent_output import AgentOutput
from ..context import Context
from ..state import State


class Metric(Protocol):
    name: str

    def update(self, output: AgentOutput, prior_state: State, context: Context) -> None:
        ...

    def result(self) -> dict:
        ...
