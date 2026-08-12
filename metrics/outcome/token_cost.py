"""Outcome metric: Token Cost. See experiment.md §7.1. Summed from
each message's AgentOutput.metadata['tokens_used'] (populated by
LLMAgent; DummyAgent leaves it at 0)."""


class TokenCost:
    name = "token_cost"

    def compute(self, per_message_metadata: list[dict]) -> dict:
        total = sum(m.get("tokens_used", 0) for m in per_message_metadata)
        return {"total_tokens": total}
