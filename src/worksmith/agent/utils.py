from ..config.constant import agent_constants
from .state import TicketState


def extract_on_error(state: TicketState, err: Exception) -> dict:
    """
    Degrade gracefully: keep the category we already have, mark fields as
    missing rather than blanking the whole ticket. Only force a hard escalate
    if the category is one where drafting without fields would be unsafe.
    """
    updates = {"extracted_fields": {}, "extraction_confidence": 0.0, "extraction_failed": True}
    if state.get("category") in agent_constants.hard_constraint_categories:
        updates["hard_constraint_flag"] = True
        updates["failure_reason"] = f"extract failed on hard-constraint category: {err}"
    return updates
 