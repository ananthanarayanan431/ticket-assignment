from langgraph.graph import END, StateGraph

from .edge import classify_router, route_selector
from .nodes import auto_resolve, classify, close_spam, draft_for_review, escalate, extract
from .route import route_decision
from .state import TicketState


def build_graph(checkpointer):
    """
    `checkpointer` is required — escalate() calls interrupt() to pause the
    run for human review, and LangGraph needs a checkpointer to persist that
    paused state so it can be resumed later (see db.checkpointer.get_checkpointer).

    There's no dedicated audit-log node: every node persists its own trail
    entry to Postgres as it runs (via agent.core.log._log), so the audit
    trail is durable step-by-step instead of only once at the end of the run.
    """
    graph = StateGraph(TicketState)

    graph.add_node("classify", classify)
    graph.add_node("extract", extract)
    graph.add_node("close_spam", close_spam)
    graph.add_node("route_decision", route_decision)
    graph.add_node("auto_resolve", auto_resolve)
    graph.add_node("draft_for_review", draft_for_review)
    graph.add_node("escalate", escalate)

    graph.set_entry_point("classify")

    graph.add_conditional_edges(
        "classify",
        classify_router,
        {
            "extract": "extract",
            "skip_extract": "route_decision",
            "close_spam": "close_spam",
        },
    )
    graph.add_edge("extract", "route_decision")
    graph.add_edge("close_spam", END)

    graph.add_conditional_edges(
        "route_decision",
        route_selector,
        {
            "auto_resolve": "auto_resolve",
            "draft_for_review": "draft_for_review",
            "escalate": "escalate",
        },
    )

    graph.add_edge("auto_resolve", END)
    graph.add_edge("draft_for_review", END)
    graph.add_edge("escalate", END)

    return graph.compile(checkpointer=checkpointer)
