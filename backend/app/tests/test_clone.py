import json

import pytest

from app import seed
from app.db import connect
from app.repositories import openings as openings_repo
from app.services.paint_service import PaintService


@pytest.fixture()
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr("app.db.DB_PATH", tmp_path / "t.db")
    seed.init_db()
    with PaintService() as s:
        yield s


def counts():
    with connect() as c:
        rooms = c.execute("SELECT COUNT(*) c FROM rooms").fetchone()["c"]
        ops = c.execute("SELECT COUNT(*) c FROM openings").fetchone()["c"]
    return rooms, ops


def test_clone_resize_copies_openings(svc):
    d = svc.clone_room(1, new_length=6.0)
    assert d["room"]["id"] != 1
    assert d["room"]["length"] == 6.0
    assert d["room"]["width"] == 4.0  # 未指定的维度沿用源房
    assert d["room"]["height"] == 2.8
    got = sorted((o["kind"], o["w"], o["h"]) for o in d["openings"])
    assert got == [("door", 0.9, 2.1), ("window", 1.5, 1.4)]
    assert all(o["room_id"] == d["room"]["id"] for o in d["openings"])
    src = svc.room_detail(1)  # 源房保持不变
    assert (src["room"]["length"], src["room"]["width"]) == (5.0, 4.0)
    assert len(src["openings"]) == 2


def test_clone_without_resize_keeps_dims(svc):
    d = svc.clone_room(2)
    assert (d["room"]["length"], d["room"]["width"]) == (4.0, 3.2)
    assert len(d["openings"]) == 3


@pytest.mark.parametrize("kw", [{"new_length": 0}, {"new_width": -1.5}, {"new_length": 3, "new_width": 0}])
def test_clone_nonpositive_fails_without_partial_writes(svc, kw):
    before = counts()
    with pytest.raises(ValueError):
        svc.clone_room(1, **kw)
    assert counts() == before  # 整单失败：不留半个房间或半套门窗


def test_clone_missing_source(svc):
    before = counts()
    assert svc.clone_room(999, new_length=3.0) is None
    assert counts() == before


def test_clone_rolls_back_when_opening_insert_fails(svc, monkeypatch):
    def boom(*a):
        raise RuntimeError("disk full")
    monkeypatch.setattr(openings_repo, "create", boom)
    before = counts()
    with pytest.raises(RuntimeError):
        svc.clone_room(1, new_length=6.0)
    assert counts() == before  # 房间与开洞一并回滚


def test_persist_estimates_write_separate_runs(svc):
    clone = svc.clone_room(1, new_length=6.0)
    cid = clone["room"]["id"]
    a = svc.estimate(1, persist=True)
    b = svc.estimate(cid, persist=True)
    assert a["run_id"] != b["run_id"]
    assert a["liters"] != b["liters"]  # 升数可对照
    with connect() as c:
        rows = c.execute(
            "SELECT id, room_id, result_json FROM calc_runs WHERE id IN (?,?)",
            (a["run_id"], b["run_id"]),
        ).fetchall()
    by_run = {r["id"]: r for r in rows}
    assert by_run[a["run_id"]]["room_id"] == 1  # 各写各的 calc_runs
    assert by_run[b["run_id"]]["room_id"] == cid
    la = json.loads(by_run[a["run_id"]]["result_json"])["liters"]
    lb = json.loads(by_run[b["run_id"]]["result_json"])["liters"]
    assert (la, lb) == (a["liters"], b["liters"])
