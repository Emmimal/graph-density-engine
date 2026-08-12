"""Outcome metric: Latency. See experiment.md §7.1. Wall-clock time to
synthesis or timeout, summed from each message's
AgentOutput.metadata['latency_ms']."""


class Latency:
    name = "latency"

    def compute(self, per_message_metadata: list[dict], wall_clock_ms: float) -> dict:
        summed_call_latency = sum(m.get("latency_ms", 0.0) for m in per_message_metadata)
        return {"wall_clock_ms": wall_clock_ms, "summed_call_latency_ms": summed_call_latency}
