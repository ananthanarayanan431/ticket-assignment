from ..config.constant import agent_constants
from .core.logger import get_logger
from .state import TicketState

logger = get_logger("edge")


def classify_router(state: TicketState) -> str:
    """
    Route based on classify's outcome. Spam ends the run right here — no
    extraction, no route_decision, no reply. A failed classify still needs
    route_decision's hard_constraint_flag -> escalate handling, so it goes
    through skip_extract rather than close_spam even though extraction is
    also pointless there (no reliable category to extract against).
    """
    if state.get("hard_constraint_flag"):
        target = "skip_extract"
    elif state.get("category") in agent_constants.no_reply_categories:
        target = "close_spam"
    elif state.get("category") in agent_constants.no_extraction_needed_categories:
        target = "skip_extract"
    else:
        target = "extract"

    logger.info(
        "edge_taken",
        edge="classify_router",
        ticket_id=state.get("ticket_id"),
        category=state.get("category"),
        target=target,
    )
    return target


def route_selector(state: TicketState) -> str:
    """The actual conditional-edge function — just reads what route_decision set."""
    target = state["decision"]
    logger.info(
        "edge_taken",
        edge="route_selector",
        ticket_id=state.get("ticket_id"),
        target=target,
    )
    return target
