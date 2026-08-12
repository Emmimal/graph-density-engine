"""Shared, append-only record of accumulated facts and metadata.

Per interfaces.md: passed into every agent call and returned, updated,
after it. facts is treated as append-only within a trial — nothing
in this codebase removes or edits an existing fact once added.
"""
from dataclasses import dataclass, field


@dataclass
class State:
    facts: list[str] = field(default_factory=list)
    last_modifier: int = -1
    metadata: dict = field(default_factory=dict)

    def copy(self) -> "State":
        return State(
            facts=list(self.facts),
            last_modifier=self.last_modifier,
            metadata=dict(self.metadata),
        )
