from pydantic import BaseModel


class DraftResponse(BaseModel):
    draft: str
