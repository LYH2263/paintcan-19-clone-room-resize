import sqlite3
def for_room(conn, room_id):
    return [dict(r) for r in conn.execute("SELECT * FROM openings WHERE room_id=?", (room_id,)).fetchall()]
def create(conn, room_id, kind, w, h):
    cur = conn.execute("INSERT INTO openings(room_id,kind,w,h) VALUES (?,?,?,?)", (room_id, kind, w, h))
    return int(cur.lastrowid)
