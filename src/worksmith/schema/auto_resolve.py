from pydantic import BaseModel


class AutoResolveResponse(BaseModel):
    response: str
