"""
Core human-review operations used by the Streamlit app: run tickets through
the graph, list what's pending, and resolve it.
"""

import json
from importlib import resources

from langgraph.types import Command
from sqlalchemy import select, text

from ..db.postgres import get_session_factory
from ..models import Ticket

TICKETS_FILE = resources.files("worksmith.data").joinpath("tickets.json")


def load_tickets() -> list[dict]:
    return json.loads(TICKETS_FILE.read_text())


async def pending_escalation(graph, ticket_id: str):
    """Return the graph state if `ticket_id` is currently paused at an interrupt, else None."""
    config = {"configurable": {"thread_id": ticket_id}}
    state = await graph.aget_state(config)
    if any(task.interrupts for task in state.tasks):
        return state
    return None


async def run_ticket(graph, ticket: dict) -> dict:
    config = {"configurable": {"thread_id": ticket["id"]}}
    initial_state = {
        "ticket_id": ticket["id"],
        "from_name": ticket["from_name"],
        "from_email": ticket["from_email"],
        "subject": ticket["subject"],
        "body": ticket["body"],
    }
    return await graph.ainvoke(initial_state, config=config)


async def list_escalations(graph) -> list[dict]:
    """
    A paused escalation hasn't reached audit_log yet, so it's never in
    `tickets` — the checkpointer's own thread ids are the only place pending
    runs are visible.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        thread_ids = (await session.execute(text("SELECT DISTINCT thread_id FROM checkpoints"))).scalars().all()

    escalations = []
    for thread_id in thread_ids:
        state = await pending_escalation(graph, thread_id)
        if state is not None:
            escalations.append({"ticket_id": thread_id, **state.tasks[0].interrupts[0].value})
    return escalations


async def list_drafts() -> list[Ticket]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        rows = await session.execute(select(Ticket).where(Ticket.decision == "draft_for_review", ~Ticket.resolved))
        return rows.scalars().all()


async def resolve_escalation(graph, ticket_id: str, response_text: str | None, resolved_by: str | None) -> dict:
    config = {"configurable": {"thread_id": ticket_id}}
    decision = {"response_text": response_text, "resolved_by": resolved_by}
    return await graph.ainvoke(Command(resume=decision), config=config)


async def resolve_draft(ticket_id: str, response_text: str | None, reject: bool) -> Ticket | None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        row = await session.get(Ticket, ticket_id)
        if row is None or row.decision != "draft_for_review" or row.resolved:
            return None
        row.response_text = None if reject else (response_text or row.response_text)
        row.resolved = True
        await session.commit()
        await session.refresh(row)
        return row
