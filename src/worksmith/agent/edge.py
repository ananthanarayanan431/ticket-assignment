from ..config.constant import agent_constants
from .state import TicketState


def classify_router(state: TicketState) -> str:
    """Skip extraction for spam, or when classify itself already failed."""
    if state.get("hard_constraint_flag"):
        return "skip_extract"
    if state.get("category") in agent_constants.no_extraction_needed_categories:
        return "skip_extract"
    return "extract"


def route_selector(state: TicketState) -> str:
    """The actual conditional-edge function — just reads what route_decision set."""
    return state["decision"]
