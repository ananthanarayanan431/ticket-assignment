from langgraph.graph import END, StateGraph

from .edge import classify_router, route_selector
from .core.log import audit_log
from .nodes import classify, draft_for_review, escalate, extract
from .route import auto_resolve, route_decision
from .state import TicketState


def build_graph(checkpointer):
    """
    `checkpointer` is required — escalate() calls interrupt() to pause the
    run for human review, and LangGraph needs a checkpointer to persist that
    paused state so it can be resumed later (see db.checkpointer.get_checkpointer).
    """
    graph = StateGraph(TicketState)

    graph.add_node("classify", classify)
    graph.add_node("extract", extract)
    graph.add_node("route_decision", route_decision)
    graph.add_node("auto_resolve", auto_resolve)
    graph.add_node("draft_for_review", draft_for_review)
    graph.add_node("escalate", escalate)
    graph.add_node("audit_log", audit_log)

    graph.set_entry_point("classify")

    graph.add_conditional_edges(
        "classify",
        classify_router,
        {
            "extract": "extract",
            "skip_extract": "route_decision",
        },
    )
    graph.add_edge("extract", "route_decision")

    graph.add_conditional_edges(
        "route_decision",
        route_selector,
        {
            "auto_resolve": "auto_resolve",
            "draft_for_review": "draft_for_review",
            "escalate": "escalate",
        },
    )

    graph.add_edge("auto_resolve", "audit_log")
    graph.add_edge("draft_for_review", "audit_log")
    graph.add_edge("escalate", "audit_log")
    graph.add_edge("audit_log", END)

    return graph.compile(checkpointer=checkpointer)
