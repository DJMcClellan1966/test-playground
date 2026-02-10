"""
Generated Code from Visual Block Editor
Generated at: 2026-02-09T09:41:11.691023
"""


# ---- Basic Authentication ----

# auth.py - Basic Authentication Block

from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash


def get_current_user():
    """Get the currently logged-in user from session."""
    user_id = session.get("user_id")
    if user_id:
        # {{STORAGE_LOOKUP}} - replaced by storage block
        return None  # Replace with actual lookup
    return None


def login_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            if request.is_json:
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def create_auth_routes(app, storage):
    """Create authentication routes."""
    from flask import Blueprint
    
    auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
    
    @auth_bp.route("/login", methods=["POST"])
    def login():
        data = request.get_json()
        user = storage.find_by_email(data.get("email"))
        if user and check_password_hash(user["password_hash"], data.get("password")):
            session["user_id"] = user["id"]
            return jsonify({"success": True, "user": user})
        return jsonify({"error": "Invalid credentials"}), 401
    
    @auth_bp.route("/logout", methods=["POST"])
    def logout():
        session.pop("user_id", None)
        return jsonify({"success": True})
    
    @auth_bp.route("/register", methods=["POST"])
    def register():
        data = request.get_json()
        if storage.find_by_email(data.get("email")):
            return jsonify({"error": "Email already registered"}), 400
        
        user = {
            "email": data["email"],
            "username": data.get("username", data["email"].split("@")[0]),
            "password_hash": generate_password_hash(data["password"]),
        }
        created = storage.create("user", user)
        session["user_id"] = created["id"]
        return jsonify({"success": True, "user": created}), 201
    
    app.register_blueprint(auth_bp)
    return auth_bp


# ---- SQLite Storage ----

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


# ---- CRUD Route Generator ----

# crud_routes.py - Generic CRUD Route Block

from flask import Blueprint, request, jsonify


def create_crud_routes(entity_name: str, storage) -> Blueprint:
    """
    Create CRUD routes for any entity.
    
    Creates: GET /api/{entity}, GET /api/{entity}/<id>, POST, PUT, DELETE
    """
    bp = Blueprint(f"{entity_name}_api", __name__, url_prefix=f"/api/{entity_name}")
    
    @bp.route("", methods=["GET"])
    @bp.route("/", methods=["GET"])
    def list_items():
        items = storage.list(entity_name)
        return jsonify({
            "items": items,
            "total": len(items)
        })
    
    @bp.route("/<item_id>", methods=["GET"])
    def get_item(item_id):
        item = storage.get(entity_name, item_id)
        if not item:
            return jsonify({"error": "Not found"}), 404
        return jsonify(item)
    
    @bp.route("", methods=["POST"])
    @bp.route("/", methods=["POST"])
    def create_item():
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        item = storage.create(entity_name, data)
        return jsonify(item), 201
    
    @bp.route("/<item_id>", methods=["PUT"])
    def update_item(item_id):
        data = request.get_json()
        item = storage.update(entity_name, item_id, data)
        if not item:
            return jsonify({"error": "Not found"}), 404
        return jsonify(item)
    
    @bp.route("/<item_id>", methods=["DELETE"])
    def delete_item(item_id):
        if storage.delete(entity_name, item_id):
            return "", 204
        return jsonify({"error": "Not found"}), 404
    
    return bp


def register_crud_for_entities(app, storage, entities: list):
    """Register CRUD routes for multiple entities."""
    for entity in entities:
        bp = create_crud_routes(entity, storage)
        app.register_blueprint(bp)
