from pydantic import BaseModel, Field


class GoldLabel(BaseModel):
    """Hand-annotated ground truth for one ticket in golden_tickets.json."""

    expected_category: str
    acceptable_categories: list[str] | None = None
    hard_constraint: bool
    acceptable_decisions: list[str]
    forbidden_decisions: list[str] = Field(default_factory=list)
    expected_extracted_fields: dict[str, str | None]
    rationale: str
    observational: bool = False

    def categories(self) -> list[str]:
        return self.acceptable_categories or [self.expected_category]


class JudgeVerdict(BaseModel):
    """Structured output from the LLM judge for one ticket."""

    category_correct: bool
    category_feedback: str
    decision_correct: bool
    decision_feedback: str
    extraction_score: float = Field(ge=0, le=1)
    extraction_feedback: str
    overall_notes: str
