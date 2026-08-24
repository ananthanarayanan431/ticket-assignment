from typing import Literal

from pydantic import BaseModel, Field

# Must stay in sync with agent_constants.hard_constraint_categories and
# .no_extraction_needed_categories (config/constant.py), which key off these
# exact values — a free-text category here would silently break routing.
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
