from typing import TypedDict, Literal, Optional

class TrailEntry(TypedDict):
    node: str
    timestamp: float
    detail: dict
 
 
class TicketState(TypedDict, total=False):
    ticket_id: str
    from_name: str
    from_email: str
    subject: str
    body: str
 
    category: str
    classification_confidence: float
 
    extracted_fields: dict
    extraction_confidence: float
    extraction_failed: bool
 
    confidence: float
    decision: Literal["auto_resolve", "draft_for_review", "escalate"]
 
    hard_constraint_flag: bool
    failure_reason: Optional[str]
 
    response_text: Optional[str]
    queued_for_human: bool
 
    trail: list[TrailEntry]
 
 