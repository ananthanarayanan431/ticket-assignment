import time

from sqlalchemy.dialects.postgresql import insert as pg_insert

from ...db.postgres import get_session_factory
from ...models import Ticket
from ..state import TicketState, TrailEntry


async def _persist(ticket_id: str, trail: list[TrailEntry], decision: str | None, response_text: str | None) -> None:
    """
    Upsert the ticket's audit row. Called from `_log` after every node (not
    just a terminal one), so the trail — and whatever decision/response is
    known so far — is durable in Postgres even if the run crashes mid-
    pipeline or pauses at escalate()'s interrupt() before reaching a
    terminal node.
    """
    resolved = decision is not None and decision != "draft_for_review"
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = pg_insert(Ticket).values(
            ticket_id=ticket_id,
            decision=decision,
            response_text=response_text,
            resolved=resolved,
            trail_json=trail,
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


async def _log(state: TicketState, node: str, **detail) -> list[TrailEntry]:
    """
    Append a trail entry and immediately persist it. `decision` and
    `response_text` are read from `detail` (a node passes them explicitly
    when it's the one computing them this step) falling back to whatever's
    already on `state` (set by an earlier node in the same run).
    """
    entry: TrailEntry = {"node": node, "timestamp": time.time(), "detail": detail}
    trail = [*state.get("trail", []), entry]
    decision = detail.get("decision", state.get("decision"))
    response_text = detail.get("response_text", state.get("response_text"))
    await _persist(state["ticket_id"], trail, decision, response_text)
    return trail
