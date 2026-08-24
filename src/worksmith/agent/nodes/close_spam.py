from ..core.log import _log
from ..state import TicketState


async def close_spam(state: TicketState) -> dict:
    """
    Closes spam right after classify — no extraction, no route_decision, no
    auto-generated reply. There's no one on the other end worth replying to,
    so this skips the LLM call entirely rather than spending a request
    writing a reply nobody will read.
    """
    return {
        "confidence": state.get("classification_confidence", 0.0),
        "decision": "auto_resolve",
        "response_text": None,
        "queued_for_human": False,
        "trail": await _log(
            state,
            "close_spam",
            decision="auto_resolve",
            reason="spam — closed with no reply",
            sent=False,
        ),
    }
