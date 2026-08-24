from ..config.constant import agent_constants
from .log import _log
from .state import TicketState


def route_decision(state: TicketState) -> dict:
    """
    Deterministic gate — no LLM call. Combines classification_confidence and
    extraction_confidence (when extraction ran) into the single signal used
    for thresholding, and sets state["decision"]. Pure function, easy to
    unit-test against a table of inputs -> expected decisions.
    """
    classification_confidence = state.get("classification_confidence", 0.0)
    extraction_confidence = state.get("extraction_confidence")
    combined = (
        min(classification_confidence, extraction_confidence)
        if extraction_confidence is not None
        else classification_confidence
    )

    if state.get("hard_constraint_flag"):
        decision = "escalate"
        reason = state.get("failure_reason", "upstream failure")
    elif state.get("category") in agent_constants.hard_constraint_categories:
        decision = "escalate" if combined < agent_constants.draft_confidence_threshold else "draft_for_review"
        reason = "hard-constraint category — auto-resolve never allowed"
    elif combined >= agent_constants.auto_resolve_confidence_threshold:
        decision = "auto_resolve"
        reason = "high confidence, non-restricted category"
    elif combined >= agent_constants.draft_confidence_threshold:
        decision = "draft_for_review"
        reason = "moderate confidence"
    else:
        decision = "escalate"
        reason = "low confidence"

    return {
        "confidence": combined,
        "decision": decision,
        "trail": _log(state, "route_decision", decision=decision, reason=reason, combined_confidence=combined),
    }


def auto_resolve(state: TicketState) -> dict:
    template = f"[canned reply for category={state['category']}]"
    return {
        "response_text": template,
        "queued_for_human": False,
        "trail": _log(state, "auto_resolve", sent=True),
    }
