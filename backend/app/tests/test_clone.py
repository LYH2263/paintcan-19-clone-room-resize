import pytest
from app import db, seed
from app.repositories import openings
from app.services.paint_service import PaintService

@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    seed.init_db()
    with PaintService() as s:
        yield s

def _count(conn, table):
    return conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]

def test_clone_copies_room_with_new_length(svc):
    d = svc.clone_room(1, new_length=6.0)
    new = d["room"]
    assert new["id"] != 1
    assert (new["length"], new["width"], new["height"]) == (6.0, 4.0, 2.8)
    assert "克隆" in new["name"]
    assert [(o["kind"], o["w"], o["h"]) for o in d["openings"]] == \
           [("door", 0.9, 2.1), ("window", 1.5, 1.4)]

def test_clone_keeps_source_unchanged(svc):
    before_rooms = _count(svc._c, "rooms")
    before_ops = _count(svc._c, "openings")
    svc.clone_room(1, new_length=6.0, new_width=5.0)
    src = svc.room_detail(1)
    assert (src["room"]["length"], src["room"]["width"]) == (5.0, 4.0)
    assert len(src["openings"]) == 2
    assert _count(svc._c, "rooms") == before_rooms + 1
    assert _count(svc._c, "openings") == before_ops + 2

def test_clone_default_keeps_size(svc):
    d = svc.clone_room(1)
    assert (d["room"]["length"], d["room"]["width"]) == (5.0, 4.0)

def test_clone_non_positive_length_rolls_back(svc):
    rooms_before = _count(svc._c, "rooms")
    ops_before = _count(svc._c, "openings")
    with pytest.raises(ValueError):
        svc.clone_room(1, new_length=0)
    assert _count(svc._c, "rooms") == rooms_before
    assert _count(svc._c, "openings") == ops_before

def test_clone_negative_width_rolls_back(svc):
    with pytest.raises(ValueError):
        svc.clone_room(1, new_width=-3.0)
    assert _count(svc._c, "rooms") == 2

def test_clone_missing_source_is_none(svc):
    assert svc.clone_room(999, new_length=6.0) is None

def test_clone_atomic_when_opening_insert_fails(svc, monkeypatch):
    orig_add = openings.add
    calls = {"n": 0}
    def flaky_add(conn, room_id, kind, w, h):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("模拟开洞写入失败")
        return orig_add(conn, room_id, kind, w, h)
    monkeypatch.setattr(openings, "add", flaky_add)
    rooms_before = _count(svc._c, "rooms")
    ops_before = _count(svc._c, "openings")
    with pytest.raises(RuntimeError):
        svc.clone_room(1, new_length=6.0)
    assert _count(svc._c, "rooms") == rooms_before
    assert _count(svc._c, "openings") == ops_before
    assert svc._c.execute("SELECT COUNT(*) c FROM rooms WHERE name LIKE '%克隆%'").fetchone()["c"] == 0

def test_persist_writes_separate_runs_per_room(svc):
    svc.estimate(1, persist=True)
    new_id = svc.clone_room(1, new_length=6.0)["room"]["id"]
    svc.estimate(new_id, persist=True)
    rows = {r["room_id"]: r["c"] for r in
            svc._c.execute("SELECT room_id, COUNT(*) c FROM calc_runs WHERE kind='estimate' GROUP BY room_id")}
    assert rows[new_id] == 1
    assert rows[1] == 2
    assert svc._c.execute("SELECT COUNT(*) c FROM calc_runs WHERE room_id=?", (new_id,)).fetchone()["c"] == 1

def test_clone_estimates_reflect_new_size(svc):
    src = svc.estimate(1, persist=False)
    new_id = svc.clone_room(1, new_length=6.0)["room"]["id"]
    clone = svc.estimate(new_id, persist=False)
    assert clone["gross_m2"] > src["gross_m2"]
    assert clone["liters"] > src["liters"]
