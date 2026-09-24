from pydantic import BaseModel
class EstimateRequest(BaseModel):
    room_id: int
    coats: int | None = None
    coverage: float | None = None
    persist: bool = True
class CloneRoomRequest(BaseModel):
    length: float | None = None
    width: float | None = None
    name: str | None = None
