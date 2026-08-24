from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "billing",
    "account_deletion",
    "legal",
    "security",
    "bug",
    "feature_request",
    "account_access",
    "spam",
    "other",
]


class ClassificationResponse(BaseModel):
    category: Category
    confidence: float = Field(ge=0, le=1)
