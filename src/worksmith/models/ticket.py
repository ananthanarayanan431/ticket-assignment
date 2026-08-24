import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[str] = mapped_column(String, primary_key=True)
    trace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    # Null until route_decision runs — the row is first written by classify,
    # before a decision exists (see agent/core/log.py).
    decision: Mapped[str | None] = mapped_column(String, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # False while there's no decision yet, or the decision is draft_for_review
    # / escalate pending a human. True once auto_resolve, draft approval, or
    # escalation resolution has happened.
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    trail_json: Mapped[list] = mapped_column(JSONB)
