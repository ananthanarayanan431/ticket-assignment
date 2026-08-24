from pydantic import BaseModel, Field


class ExtractedFields(BaseModel):
    account_identifier: str | None = None
    product_area: str | None = None
    urgency: str | None = None
    sentiment: str | None = None


class ExtractionResponse(BaseModel):
    extracted_fields: ExtractedFields
    confidence: float = Field(ge=0, le=1)
