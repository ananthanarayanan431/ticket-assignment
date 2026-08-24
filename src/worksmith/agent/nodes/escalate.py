from langgraph.types import interrupt

from ..log import _log
from ..state import TicketState


def escalate(state: TicketState) -> dict:
    """
    Routes to a human agent with no auto-generated response. Pauses the
    graph run here (requires a checkpointer) until a human submits their
    decision via Command(resume=...); the run then continues on to
    audit_log with that decision baked in.
    """
    decision = interrupt(
        {
            "ticket_id": state["ticket_id"],
            "category": state.get("category"),
            "subject": state.get("subject"),
            "body": state.get("body"),
            "reason": state.get("failure_reason", "escalated for human review"),
        }
    )

    return {
        "response_text": decision.get("response_text"),
        "queued_for_human": True,
        "trail": _log(state, "escalate", queued=True, resolved_by=decision.get("resolved_by")),
    }
