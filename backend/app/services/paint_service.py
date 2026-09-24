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
    def clone_room(self, room_id, new_length=None, new_width=None, name=None):
        src = rooms.get(self._c, room_id)
        if not src: return None
        for v in (new_length, new_width):
            if v is not None and v <= 0: raise ValueError("新长宽必须为正数")
        length = float(new_length) if new_length is not None else src["length"]
        width = float(new_width) if new_width is not None else src["width"]
        nm = name or f"{src['name']}·克隆"
        ops = openings.for_room(self._c, room_id)
        try:
            nid = rooms.create(self._c, nm, length, width, src["height"])
            for o in ops:
                openings.create(self._c, nid, o["kind"], o["w"], o["h"])
            self._c.commit()
        except Exception:
            self._c.rollback()
            raise
        return self.room_detail(nid)
    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
