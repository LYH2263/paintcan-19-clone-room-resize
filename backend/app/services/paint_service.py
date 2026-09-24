from app.db import connect
from app.engines.estimate import estimate_room
from app.repositories import openings, rooms, runs, settings

class PaintService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_rooms(self): return rooms.list_all(self._c)
    def room_detail(self, rid):
        r = rooms.get(self._c, rid)
        if not r: return None
        return {"room": r, "openings": openings.for_room(self._c, rid)}
    def clone_room(self, src_id, new_length=None, new_width=None, new_name=None):
        src = rooms.get(self._c, src_id)
        if not src: return None
        length = float(new_length) if new_length is not None else float(src["length"])
        width = float(new_width) if new_width is not None else float(src["width"])
        if length <= 0 or width <= 0:
            raise ValueError("新房间的长和宽必须为正数")
        name = new_name or f"{src['name']}(克隆)"
        src_ops = openings.for_room(self._c, src_id)
        try:
            new_id = rooms.insert(self._c, name, length, width, src["height"])
            openings.copy_for(self._c, src_ops, new_id)
            self._c.commit()
        except Exception:
            self._c.rollback()
            raise
        return self.room_detail(new_id)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)
    def estimate(self, room_id, persist, coats=None, coverage=None):
        detail = self.room_detail(room_id)
        if not detail: return None
        r = detail["room"]
        cov, ct = settings.coverage_coats(self._c)
        cov = float(coverage or cov)
        ct = int(coats or ct)
        ops = [{"w": o["w"], "h": o["h"]} for o in detail["openings"]]
        result = estimate_room(r["length"], r["width"], r["height"], ops, cov, ct)
        rid = runs.insert(self._c, "estimate", {"room_id": room_id, "coats": ct, "coverage": cov}, result, room_id) if persist else None
        return {"run_id": rid, "room_id": room_id, **result}
    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
