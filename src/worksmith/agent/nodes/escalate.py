from langgraph.types import interrupt

from ..core.log import _log
from ..core.logger import get_logger
from ..state import TicketState

logger = get_logger("nodes.escalate")


async def escalate(state: TicketState) -> dict:
    """Escalate to Human for their comments"""
    logger.info(
        "node_start",
        node="escalate",
        ticket_id=state["ticket_id"],
        reason=state.get("failure_reason", "escalated for human review"),
    )
    decision = interrupt(
        {
            "ticket_id": state["ticket_id"],
            "category": state.get("category"),
            "from_name": state.get("from_name"),
            "from_email": state.get("from_email"),
            "subject": state.get("subject"),
            "body": state.get("body"),
            "reason": state.get("failure_reason", "escalated for human review"),
        }
    )

    logger.info(
        "node_complete",
        node="escalate",
        ticket_id=state["ticket_id"],
        resolved_by=decision.get("resolved_by"),
    )
    return {
        "response_text": decision.get("response_text"),
        "queued_for_human": True,
        "trail": await _log(
            state,
            "escalate",
            queued=True,
            resolved_by=decision.get("resolved_by"),
            response_text=decision.get("response_text"),
        ),
    }
