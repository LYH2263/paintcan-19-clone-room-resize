from fastapi import APIRouter, HTTPException
from app.schemas.room import CloneRequest
from app.services.paint_service import PaintService
router = APIRouter()
@router.get("/rooms")
def list_rooms():
    with PaintService() as s: return {"items": s.list_rooms()}
@router.get("/rooms/{room_id}")
def room_detail(room_id: int):
    with PaintService() as s:
        d = s.room_detail(room_id)
        if not d: raise HTTPException(404)
        return d
@router.post("/rooms/{room_id}/clone")
def clone_room(room_id: int, body: CloneRequest):
    with PaintService() as s:
        try:
            d = s.clone_room(room_id, body.new_length, body.new_width, body.name)
        except ValueError as e:
            raise HTTPException(400, str(e))
        if not d: raise HTTPException(404)
        return d
