"""
Compositional Blocks - Code LEGOs That Know How to Connect

Each block:
- Declares what it REQUIRES (dependencies)
- Declares what it PROVIDES (capabilities)
- Knows HOW to integrate with other blocks
- Contains actual code templates

Blocks auto-assemble based on constraints from the solver.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Callable, Any
from pathlib import Path
import re


@dataclass
class Port:
    """A connection point - what a block needs or provides."""
    name: str
    type: str  # e.g., "context", "hook", "route", "middleware"
    description: str = ""


@dataclass
class Block:
    """
    A composable code block.
    
    Blocks declare their interface and contain code that can be assembled.
    """
    id: str
    name: str
    description: str
    
    # Interface
    requires: List[Port] = field(default_factory=list)
    provides: List[Port] = field(default_factory=list)
    
    # Constraints this block satisfies
    satisfies: Dict[str, Any] = field(default_factory=dict)
    
    # Code templates per stack
    code: Dict[str, str] = field(default_factory=dict)  # stack -> code
    
    # Dependencies to add
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # stack -> [deps]


# ============================================================================
# BLOCK LIBRARY
# ============================================================================

BLOCKS = {
    # -------------------------------------------------------------------------
    # AUTHENTICATION
    # -------------------------------------------------------------------------
    "auth_basic": Block(
        id="auth_basic",
        name="Basic Authentication",
        description="Username/password authentication with sessions",
        requires=[
            Port("database", "storage", "User storage"),
        ],
        provides=[
            Port("current_user", "context", "Authenticated user context"),
            Port("login_required", "decorator", "Route protection"),
            Port("auth_routes", "route", "Login/logout/register endpoints"),
        ],
        satisfies={"needs_auth": True},
        code={
            "flask": '''
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
''',
            "fastapi": '''
# auth.py - Basic Authentication Block (FastAPI)

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
import secrets


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
    storage = None  # Injected by storage block
):
    user = storage.find_by_email(credentials.username) if storage else None
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user
''',
        },
        dependencies={
            "flask": ["werkzeug"],
            "fastapi": ["passlib[bcrypt]", "python-multipart"],
        }
    ),
    
    # -------------------------------------------------------------------------
    # STORAGE
    # -------------------------------------------------------------------------
    "storage_json": Block(
        id="storage_json",
        name="JSON File Storage",
        description="Simple JSON file-based storage (development/small apps)",
        requires=[],
        provides=[
            Port("storage", "service", "CRUD storage operations"),
            Port("database", "storage", "Database abstraction"),
        ],
        satisfies={"storage_type": "local_first"},
        code={
            "flask": '''
# storage.py - JSON File Storage Block

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class JSONStorage:
    """Simple JSON file-based storage."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, List[Dict]] = {}
    
    def _get_path(self, entity: str) -> Path:
        return self.data_dir / f"{entity}.json"
    
    def _load(self, entity: str) -> List[Dict]:
        if entity in self._cache:
            return self._cache[entity]
        
        path = self._get_path(entity)
        if path.exists():
            with open(path, "r") as f:
                self._cache[entity] = json.load(f)
        else:
            self._cache[entity] = []
        return self._cache[entity]
    
    def _save(self, entity: str):
        with open(self._get_path(entity), "w") as f:
            json.dump(self._cache.get(entity, []), f, indent=2, default=str)
    
    def _next_id(self, entity: str) -> str:
        items = self._load(entity)
        return str(len(items) + 1).zfill(4)
    
    # CRUD Operations
    
    def create(self, entity: str, data: Dict) -> Dict:
        items = self._load(entity)
        now = datetime.now().isoformat()
        
        item = {
            "id": self._next_id(entity),
            "created_at": now,
            "updated_at": now,
            **data
        }
        items.append(item)
        self._save(entity)
        return item
    
    def get(self, entity: str, id: str) -> Optional[Dict]:
        items = self._load(entity)
        for item in items:
            if item.get("id") == id:
                return item
        return None
    
    def list(self, entity: str, **filters) -> List[Dict]:
        items = self._load(entity)
        if not filters:
            return items
        
        result = []
        for item in items:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                result.append(item)
        return result
    
    def update(self, entity: str, id: str, data: Dict) -> Optional[Dict]:
        items = self._load(entity)
        for item in items:
            if item.get("id") == id:
                item.update(data)
                item["updated_at"] = datetime.now().isoformat()
                self._save(entity)
                return item
        return None
    
    def delete(self, entity: str, id: str) -> bool:
        items = self._load(entity)
        original_len = len(items)
        self._cache[entity] = [i for i in items if i.get("id") != id]
        if len(self._cache[entity]) < original_len:
            self._save(entity)
            return True
        return False
    
    def find_by_email(self, email: str) -> Optional[Dict]:
        """Helper for auth - find user by email."""
        users = self._load("user")
        for user in users:
            if user.get("email") == email:
                return user
        return None


# Singleton instance
storage = JSONStorage()
''',
        },
        dependencies={}
    ),
    
    "storage_sqlite": Block(
        id="storage_sqlite",
        name="SQLite Storage",
        description="SQLite database storage for production-ready local apps",
        requires=[],
        provides=[
            Port("storage", "service", "CRUD storage operations"),
            Port("database", "storage", "Database abstraction"),
        ],
        satisfies={"database_type": "sql", "storage_type": "local_first"},
        code={
            "flask": '''
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
''',
        },
        dependencies={}
    ),
    
    # -------------------------------------------------------------------------
    # SYNC
    # -------------------------------------------------------------------------
    "sync_crdt": Block(
        id="sync_crdt",
        name="CRDT Sync Engine",
        description="Conflict-free replicated data types for offline-first sync",
        requires=[
            Port("storage", "service", "Local storage"),
            Port("transport", "service", "Network transport"),
        ],
        provides=[
            Port("sync", "service", "Sync operations"),
            Port("conflict_resolver", "handler", "Automatic conflict resolution"),
        ],
        satisfies={"sync_strategy": "crdt"},
        code={
            "flask": '''
# sync.py - CRDT Sync Block

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import json


@dataclass
class VectorClock:
    """Logical vector clock for causality tracking."""
    clocks: Dict[str, int] = field(default_factory=dict)
    
    def increment(self, node_id: str):
        self.clocks[node_id] = self.clocks.get(node_id, 0) + 1
    
    def merge(self, other: "VectorClock"):
        for node, time in other.clocks.items():
            self.clocks[node] = max(self.clocks.get(node, 0), time)
    
    def happens_before(self, other: "VectorClock") -> bool:
        """Returns True if self happened before other."""
        dominated = False
        for node in set(self.clocks.keys()) | set(other.clocks.keys()):
            self_time = self.clocks.get(node, 0)
            other_time = other.clocks.get(node, 0)
            if self_time > other_time:
                return False
            if self_time < other_time:
                dominated = True
        return dominated


@dataclass
class CRDTItem:
    """A CRDT-wrapped item with version tracking."""
    id: str
    data: Dict[str, Any]
    clock: VectorClock
    deleted: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "data": self.data,
            "clock": self.clock.clocks,
            "deleted": self.deleted,
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> "CRDTItem":
        clock = VectorClock(clocks=d.get("clock", {}))
        return cls(
            id=d["id"],
            data=d.get("data", {}),
            clock=clock,
            deleted=d.get("deleted", False),
        )


class CRDTSync:
    """
    CRDT-based sync engine.
    
    Provides automatic conflict resolution using Last-Writer-Wins
    with vector clocks for causality.
    """
    
    def __init__(self, node_id: str, storage):
        self.node_id = node_id
        self.storage = storage
        self.pending_changes: List[CRDTItem] = []
    
    def local_update(self, entity: str, id: str, data: Dict) -> CRDTItem:
        """Record a local change."""
        existing = self.storage.get(entity, id)
        
        # Create or update clock
        if existing and "_clock" in existing:
            clock = VectorClock(clocks=existing["_clock"])
        else:
            clock = VectorClock()
        
        clock.increment(self.node_id)
        
        item = CRDTItem(id=id, data=data, clock=clock)
        
        # Save with clock metadata
        save_data = {**data, "_clock": clock.clocks}
        if existing:
            self.storage.update(entity, id, save_data)
        else:
            self.storage.create(entity, {"id": id, **save_data})
        
        self.pending_changes.append(item)
        return item
    
    def merge_remote(self, entity: str, remote_item: CRDTItem) -> str:
        """
        Merge a remote change.
        
        Returns: "applied", "rejected", or "conflict_resolved"
        """
        local = self.storage.get(entity, remote_item.id)
        
        if not local:
            # New item - just apply
            save_data = {**remote_item.data, "_clock": remote_item.clock.clocks}
            self.storage.create(entity, {"id": remote_item.id, **save_data})
            return "applied"
        
        local_clock = VectorClock(clocks=local.get("_clock", {}))
        
        if remote_item.clock.happens_before(local_clock):
            # Remote is older - reject
            return "rejected"
        
        if local_clock.happens_before(remote_item.clock):
            # Remote is newer - apply
            save_data = {**remote_item.data, "_clock": remote_item.clock.clocks}
            self.storage.update(entity, remote_item.id, save_data)
            return "applied"
        
        # Concurrent - need to merge (LWW based on node_id for determinism)
        local_clock.merge(remote_item.clock)
        
        # Use remote if its node_id is "greater" (deterministic tiebreaker)
        if max(remote_item.clock.clocks.keys()) > max(local_clock.clocks.keys()):
            merged_data = remote_item.data
        else:
            merged_data = {k: v for k, v in local.items() if not k.startswith("_")}
        
        merged_data["_clock"] = local_clock.clocks
        self.storage.update(entity, remote_item.id, merged_data)
        return "conflict_resolved"
    
    def get_pending_changes(self) -> List[Dict]:
        """Get changes to sync to server."""
        changes = [item.to_dict() for item in self.pending_changes]
        self.pending_changes = []
        return changes


# Usage:
# sync = CRDTSync(node_id="client_123", storage=storage)
# sync.local_update("task", "task_1", {"title": "Updated task"})
# changes = sync.get_pending_changes()  # Send these to server
''',
        },
        dependencies={}
    ),
    
    # -------------------------------------------------------------------------
    # CRUD ROUTES
    # -------------------------------------------------------------------------
    "crud_routes": Block(
        id="crud_routes",
        name="CRUD Route Generator",
        description="Automatic REST endpoints for any entity",
        requires=[
            Port("storage", "service", "Storage backend"),
        ],
        provides=[
            Port("entity_routes", "route", "CRUD endpoints for entities"),
        ],
        satisfies={},
        code={
            "flask": '''
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
''',
        },
        dependencies={}
    ),
}


# ============================================================================
# BLOCK ASSEMBLER
# ============================================================================

class BlockAssembler:
    """
    Assembles blocks based on constraints.
    
    Automatically resolves dependencies and generates integrated code.
    """
    
    def __init__(self, constraints: Dict[str, Any], stack: str = "flask"):
        self.constraints = constraints
        self.stack = stack
        self.selected_blocks: List[Block] = []
        self.resolved_ports: Dict[str, str] = {}  # port_name -> providing_block_id
    
    def select_blocks(self) -> List[Block]:
        """Select blocks that satisfy constraints."""
        selected = []
        
        for block in BLOCKS.values():
            # Check if block satisfies any constraints
            for constraint, value in block.satisfies.items():
                if self.constraints.get(constraint) == value:
                    if block not in selected:
                        selected.append(block)
                    break
        
        # Always include CRUD routes if we have storage
        if any(b.id.startswith("storage_") for b in selected):
            if BLOCKS["crud_routes"] not in selected:
                selected.append(BLOCKS["crud_routes"])
        
        self.selected_blocks = selected
        return selected
    
    def resolve_dependencies(self):
        """Ensure all required ports are satisfied."""
        provided = {}
        required = []
        
        # Collect all provided ports
        for block in self.selected_blocks:
            for port in block.provides:
                provided[port.name] = block.id
        
        # Check all required ports
        for block in self.selected_blocks:
            for port in block.requires:
                if port.name not in provided:
                    required.append((block.id, port))
        
        # Try to add blocks that provide missing ports
        for block_id, port in required:
            for candidate in BLOCKS.values():
                if candidate in self.selected_blocks:
                    continue
                for p in candidate.provides:
                    if p.name == port.name:
                        self.selected_blocks.append(candidate)
                        provided[p.name] = candidate.id
                        break
        
        self.resolved_ports = provided
        return required
    
    def get_code(self) -> Dict[str, str]:
        """Get code for all selected blocks."""
        code = {}
        for block in self.selected_blocks:
            if self.stack in block.code:
                code[block.id] = block.code[self.stack]
        return code
    
    def get_dependencies(self) -> List[str]:
        """Get all dependencies for the stack."""
        deps = set()
        for block in self.selected_blocks:
            if self.stack in block.dependencies:
                deps.update(block.dependencies[self.stack])
        return sorted(deps)
    
    def generate_app_imports(self) -> str:
        """Generate import statements for app.py."""
        imports = []
        for block in self.selected_blocks:
            if block.id.startswith("storage_"):
                imports.append(f"from storage import storage")
            elif block.id == "auth_basic":
                imports.append(f"from auth import create_auth_routes, login_required")
            elif block.id == "crud_routes":
                imports.append(f"from crud_routes import register_crud_for_entities")
            elif block.id == "sync_crdt":
                imports.append(f"from sync import CRDTSync")
        return "\n".join(imports)
    
    def explain(self) -> str:
        """Explain what blocks were selected and why."""
        lines = ["Selected blocks:"]
        for block in self.selected_blocks:
            reasons = [f"{k}={v}" for k, v in block.satisfies.items() 
                      if k in self.constraints]
            reason_str = f" (satisfies: {', '.join(reasons)})" if reasons else ""
            lines.append(f"  • {block.name}{reason_str}")
        return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Compositional block assembler")
    parser.add_argument("--list", "-l", action="store_true", help="List all blocks")
    parser.add_argument("--auth", action="store_true", help="Include authentication")
    parser.add_argument("--offline", action="store_true", help="Offline-first with sync")
    parser.add_argument("--sqlite", action="store_true", help="Use SQLite instead of JSON")
    parser.add_argument("--stack", "-s", default="flask", help="Tech stack")
    
    args = parser.parse_args()
    
    if args.list:
        print("\n📦 Available Blocks\n")
        for block in BLOCKS.values():
            provides = [p.name for p in block.provides]
            requires = [p.name for p in block.requires]
            print(f"  {block.id}")
            print(f"    {block.name}: {block.description}")
            print(f"    Provides: {', '.join(provides) or 'none'}")
            print(f"    Requires: {', '.join(requires) or 'none'}")
            print()
        return
    
    # Build constraints from args
    constraints = {}
    if args.auth:
        constraints["needs_auth"] = True
    if args.offline:
        constraints["sync_strategy"] = "crdt"
        constraints["storage_type"] = "local_first"
    if args.sqlite:
        constraints["database_type"] = "sql"
    else:
        constraints["storage_type"] = "local_first"
    
    # Assemble
    assembler = BlockAssembler(constraints, args.stack)
    selected = assembler.select_blocks()
    assembler.resolve_dependencies()
    
    print("\n🧱 Block Assembly Result")
    print("=" * 50)
    print(assembler.explain())
    
    print("\n📄 Generated Code Files:")
    for block_id, code in assembler.get_code().items():
        lines = len(code.strip().split('\n'))
        print(f"  • {block_id}.py ({lines} lines)")
    
    deps = assembler.get_dependencies()
    if deps:
        print(f"\n📦 Dependencies: {', '.join(deps)}")
    
    print()


if __name__ == "__main__":
    main()
