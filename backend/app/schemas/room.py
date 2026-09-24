from pydantic import BaseModel

class CloneRequest(BaseModel):
    new_length: float | None = None
    new_width: float | None = None
    name: str | None = None
