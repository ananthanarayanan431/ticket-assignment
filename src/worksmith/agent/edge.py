from ..config.constant import agent_constants
from .state import TicketState


def classify_router(state: TicketState) -> str:
    """
    Route based on classify's outcome. Spam ends the run right here — no
    extraction, no route_decision, no reply. A failed classify still needs
    route_decision's hard_constraint_flag -> escalate handling, so it goes
    through skip_extract rather than close_spam even though extraction is
    also pointless there (no reliable category to extract against).
    """
    if state.get("hard_constraint_flag"):
        return "skip_extract"
    if state.get("category") in agent_constants.no_reply_categories:
        return "close_spam"
    if state.get("category") in agent_constants.no_extraction_needed_categories:
        return "skip_extract"
    return "extract"


def route_selector(state: TicketState) -> str:
    """The actual conditional-edge function — just reads what route_decision set."""
    return state["decision"]
