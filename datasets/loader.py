"""Loads frozen incident scenarios from datasets/incident_*.json.
See experiment.md §6 and interfaces.md's Dataset contract.
"""
import json
from dataclasses import dataclass
from pathlib import Path

_DATASET_DIR = Path(__file__).parent


@dataclass
class IncidentScenario:
    scenario_id: str
    per_agent_knowledge: dict  # str(agent_id) -> knowledge text
    expected_facts: list
    ground_truth_sections: dict


class DatasetLoader:
    def __init__(self, dataset_dir: Path = _DATASET_DIR):
        self._dataset_dir = dataset_dir

    def all_ids(self) -> list:
        return [f"incident_{i:02d}" for i in range(1, 11)]

    def load(self, scenario_id: str) -> IncidentScenario:
        path = self._dataset_dir / f"{scenario_id}.json"
        with open(path) as f:
            raw = json.load(f)
        return IncidentScenario(
            scenario_id=raw["scenario_id"],
            per_agent_knowledge=raw["per_agent_knowledge"],
            expected_facts=raw["expected_facts"],
            ground_truth_sections=raw["ground_truth_sections"],
        )
