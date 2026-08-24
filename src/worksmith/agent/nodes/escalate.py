from langgraph.types import interrupt

from ..core.log import _log
from ..state import TicketState


async def escalate(state: TicketState) -> dict:
    """Escalate to Human for their comments"""
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
