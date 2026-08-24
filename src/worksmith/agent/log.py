import time

from sqlalchemy.dialects.postgresql import insert as pg_insert
from ..db.postgres import get_session_factory
from ..models import Ticket
from .state import TicketState, TrailEntry


async def audit_log(state: TicketState) -> dict:
    """
    Persist the full decision trail to Postgres, keyed by ticket_id. Every
    decision is final by the time this runs, except draft_for_review — that
    one is queued (resolved=False) until a human approves/edits/rejects it.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = pg_insert(Ticket).values(
            ticket_id=state["ticket_id"],
            decision=state["decision"],
            response_text=state.get("response_text"),
            resolved=state["decision"] != "draft_for_review",
            trail_json=state["trail"],
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[Ticket.ticket_id],
            set_={
                "decision": stmt.excluded.decision,
                "response_text": stmt.excluded.response_text,
                "resolved": stmt.excluded.resolved,
                "trail_json": stmt.excluded.trail_json,
            },
        )
        await session.execute(stmt)
        await session.commit()
    return {"trail": _log(state, "audit_log", persisted=True)}


def _log(state: TicketState, node: str, **detail) -> list[TrailEntry]:
    """Append a trail entry without mutating the existing list in place."""
    entry: TrailEntry = {"node": node, "timestamp": time.time(), "detail": detail}
    return [*state.get("trail", []), entry]
