from ...config.constant import agent_constants
from ..state import TicketState


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


def auto_resolve_on_error(state: TicketState, err: Exception) -> dict:
    """
    auto_resolve sends its reply with no human review, so it can't degrade
    by silently sending nothing (or a broken response) — that's the "silently
    drop the ticket" failure mode we're explicitly required to avoid. Fall
    back to a canned template and route it through draft_for_review instead,
    so a human sees it before anything goes out.
    """
    template = f"[canned reply for category={state['category']}]"
    return {
        "response_text": template,
        "queued_for_human": True,
        "decision": "draft_for_review",
        "failure_reason": f"auto_resolve failed, downgraded to draft_for_review: {err}",
    }
 