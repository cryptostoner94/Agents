import os
import sqlite3, json, time
from pathlib import Path
 
BASE = Path(os.getenv("NEXUS_BASE", "./data"))
STATE = BASE / "state"
STATE.mkdir(parents=True, exist_ok=True)
DB = STATE / "memory.sqlite3"
 
def init_db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, task_id TEXT, kind TEXT, payload TEXT)""")
    con.commit()
    con.close()
 
def log_event(task_id, kind, payload):
    init_db()
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO events(ts,task_id,kind,payload) VALUES(?,?,?,?)", (time.time(), task_id, kind, json.dumps(payload, ensure_ascii=False)))
    con.commit()
    con.close()
 
def recent(limit=30):
    init_db()
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT ts,task_id,kind,payload FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    return [{"ts":r[0],"task_id":r[1],"kind":r[2],"payload":json.loads(r[3])} for r in rows]
