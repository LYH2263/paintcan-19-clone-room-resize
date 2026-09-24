import sqlite3
def for_room(conn, room_id):
    return [dict(r) for r in conn.execute("SELECT * FROM openings WHERE room_id=?", (room_id,)).fetchall()]
def add(conn, room_id, kind, w, h):
    conn.execute("INSERT INTO openings(room_id,kind,w,h) VALUES (?,?,?,?)",
        (room_id, kind, float(w), float(h)))
def copy_for(conn, src_openings, dst_room_id):
    for o in src_openings:
        add(conn, dst_room_id, o["kind"], o["w"], o["h"])
