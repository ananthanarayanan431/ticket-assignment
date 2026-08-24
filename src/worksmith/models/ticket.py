import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[str] = mapped_column(String, primary_key=True)
    trace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    decision: Mapped[str] = mapped_column(String)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # False only for draft_for_review until a human approves/edits/rejects it via the CLI;
    # every other decision is already final by the time audit_log runs.
    resolved: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    trail_json: Mapped[list] = mapped_column(JSONB)
