
# storage.py - SQLite Storage Block

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


class SQLiteStorage:
    """SQLite-based storage with automatic schema."""
    
    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database with flexible entity table."""
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)")
    
    def create(self, entity: str, data: Dict) -> Dict:
        now = datetime.now().isoformat()
        item_id = f"{entity[:3]}{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        item = {
            "id": item_id,
            "created_at": now,
            "updated_at": now,
            **data
        }
        
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO entities (id, entity_type, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (item_id, entity, json.dumps(item), now, now)
            )
        return item
    
    def get(self, entity: str, id: str) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT data FROM entities WHERE id = ? AND entity_type = ?",
                (id, entity)
            ).fetchone()
            return json.loads(row["data"]) if row else None
    
    def list(self, entity: str, **filters) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT data FROM entities WHERE entity_type = ? ORDER BY created_at DESC",
                (entity,)
            ).fetchall()
            
            items = [json.loads(row["data"]) for row in rows]
            
            if filters:
                items = [
                    item for item in items
                    if all(item.get(k) == v for k, v in filters.items())
                ]
            return items
    
    def update(self, entity: str, id: str, data: Dict) -> Optional[Dict]:
        existing = self.get(entity, id)
        if not existing:
            return None
        
        now = datetime.now().isoformat()
        existing.update(data)
        existing["updated_at"] = now
        
        with self._conn() as conn:
            conn.execute(
                "UPDATE entities SET data = ?, updated_at = ? WHERE id = ?",
                (json.dumps(existing), now, id)
            )
        return existing
    
    def delete(self, entity: str, id: str) -> bool:
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM entities WHERE id = ? AND entity_type = ?",
                (id, entity)
            )
            return cursor.rowcount > 0
    
    def find_by_email(self, email: str) -> Optional[Dict]:
        users = self.list("user")
        for user in users:
            if user.get("email") == email:
                return user
        return None


storage = SQLiteStorage()
