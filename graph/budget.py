DEFAULT_COMMUNICATION_BUDGET = 35


def is_budget_exhausted(message_index: int, budget: int = DEFAULT_COMMUNICATION_BUDGET) -> bool:
    return message_index >= budget
