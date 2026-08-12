"""Outcome metric: Task Success. See experiment.md §7.1. Whether the
run reached the Information Recovery threshold at any point within
the communication budget.

Note: this is no longer "budget not exhausted" — Phase 2 runs every
trial to the full budget by design (see run_phase2.py's
_run_to_budget_check and experiment.md §12 Amendments), so that
signal would be trivially constant. Success is instead read from the
messages_to_threshold diagnostic computed alongside recovery.
"""


class TaskSuccess:
    name = "task_success"

    def compute(self, threshold_reached: bool) -> dict:
        return {"success": threshold_reached}
