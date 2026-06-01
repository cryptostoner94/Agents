"""Memory Store - SQLite event logging"""
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class MemoryStore:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "memory.db"
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                data TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    async def log_event(self, event_type: str, data: dict):
        """Log an event to the database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (type, data, timestamp) VALUES (?, ?, ?)",
            (event_type, json.dumps(data), datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
    
    def get_events(self, limit: int = 50) -> List[Dict]:
        """Retrieve recent events"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT type, data, timestamp FROM events ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {"type": r[0], "data": json.loads(r[1]), "timestamp": r[2]}
            for r in rows
        ]
    
    def size(self) -> int:
        """Get total event count"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def clear(self):
        """Clear all events"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events")
        conn.commit()
        conn.close()
