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
    
    # -------------------------------------------------------------------------
    # BACKEND FRAMEWORKS
    # -------------------------------------------------------------------------
    "backend_flask": Block(
        id="backend_flask",
        name="Flask Backend",
        description="Flask application with factory pattern and blueprints",
        requires=[],
        provides=[
            Port("backend", "framework", "Flask application framework"),
            Port("routing", "service", "HTTP routing"),
            Port("middleware", "service", "Request/response middleware"),
        ],
        satisfies={"backend_type": "flask"},
        code={
            "flask": '''
# app.py - Flask Backend Block

from flask import Flask, jsonify
from flask_cors import CORS
import os


def create_app(config=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Configuration
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-in-prod"),
        DEBUG=os.environ.get("DEBUG", "true").lower() == "true",
    )
    
    if config:
        app.config.update(config)
    
    # Enable CORS
    CORS(app)
    
    # Health check
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "version": "1.0.0"})
    
    @app.route("/")
    def index():
        return jsonify({
            "message": "API is running",
            "docs": "/api/docs"
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
''',
        },
        dependencies={
            "flask": ["flask", "flask-cors"],
        }
    ),
    
    "backend_fastapi": Block(
        id="backend_fastapi",
        name="FastAPI Backend",
        description="FastAPI application with async support and OpenAPI docs",
        requires=[],
        provides=[
            Port("backend", "framework", "FastAPI application framework"),
            Port("routing", "service", "HTTP routing with async"),
            Port("openapi", "service", "Automatic OpenAPI documentation"),
        ],
        satisfies={"backend_type": "fastapi"},
        code={
            "fastapi": '''
# app.py - FastAPI Backend Block

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")


def create_app() -> FastAPI:
    """Application factory pattern."""
    app = FastAPI(
        title="API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": "1.0.0"}
    
    @app.get("/")
    async def root():
        return {"message": "API is running", "docs": "/api/docs"}
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
        },
        dependencies={
            "fastapi": ["fastapi", "uvicorn[standard]"],
        }
    ),
    
    # -------------------------------------------------------------------------
    # REAL-TIME
    # -------------------------------------------------------------------------
    "websocket_basic": Block(
        id="websocket_basic",
        name="WebSocket Support",
        description="Real-time bidirectional communication",
        requires=[
            Port("backend", "framework", "Web framework"),
        ],
        provides=[
            Port("realtime", "service", "Real-time messaging"),
            Port("broadcast", "service", "Message broadcasting"),
        ],
        satisfies={"realtime": True},
        code={
            "flask": '''
# websocket.py - WebSocket Block (Flask-SocketIO)

from flask_socketio import SocketIO, emit, join_room, leave_room
from functools import wraps

socketio = SocketIO(cors_allowed_origins="*")


def init_websocket(app):
    """Initialize WebSocket support."""
    socketio.init_app(app)
    
    @socketio.on("connect")
    def handle_connect():
        print(f"Client connected: {socketio.server.environ.get('REMOTE_ADDR')}")
        emit("connected", {"message": "Connected to server"})
    
    @socketio.on("disconnect")
    def handle_disconnect():
        print("Client disconnected")
    
    @socketio.on("join")
    def handle_join(data):
        room = data.get("room", "default")
        join_room(room)
        emit("joined", {"room": room}, room=room)
    
    @socketio.on("leave")
    def handle_leave(data):
        room = data.get("room", "default")
        leave_room(room)
        emit("left", {"room": room}, room=room)
    
    @socketio.on("message")
    def handle_message(data):
        room = data.get("room", "default")
        emit("message", data, room=room, include_self=False)
    
    return socketio


def broadcast(event: str, data: dict, room: str = None):
    """Broadcast event to all clients or specific room."""
    if room:
        socketio.emit(event, data, room=room)
    else:
        socketio.emit(event, data)


def run_with_socketio(app, **kwargs):
    """Run app with WebSocket support."""
    socketio.run(app, **kwargs)
''',
            "fastapi": '''
# websocket.py - WebSocket Block (FastAPI)

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room: str = "default"):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = set()
        self.active_connections[room].add(websocket)
    
    def disconnect(self, websocket: WebSocket, room: str = "default"):
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict, room: str = "default"):
        if room in self.active_connections:
            for connection in self.active_connections[room]:
                await connection.send_json(message)
    
    async def broadcast_except(self, message: dict, exclude: WebSocket, room: str = "default"):
        if room in self.active_connections:
            for connection in self.active_connections[room]:
                if connection != exclude:
                    await connection.send_json(message)


manager = ConnectionManager()


def setup_websocket_routes(app):
    """Add WebSocket routes to FastAPI app."""
    
    @app.websocket("/ws/{room}")
    async def websocket_endpoint(websocket: WebSocket, room: str = "default"):
        await manager.connect(websocket, room)
        try:
            while True:
                data = await websocket.receive_json()
                # Echo to room except sender
                await manager.broadcast_except(data, websocket, room)
        except WebSocketDisconnect:
            manager.disconnect(websocket, room)
            await manager.broadcast({"event": "user_left"}, room)
''',
        },
        dependencies={
            "flask": ["flask-socketio", "eventlet"],
            "fastapi": ["websockets"],
        }
    ),
    
    # -------------------------------------------------------------------------
    # DEPLOYMENT
    # -------------------------------------------------------------------------
    "docker_basic": Block(
        id="docker_basic",
        name="Docker Configuration",
        description="Dockerfile and docker-compose for containerized deployment",
        requires=[],
        provides=[
            Port("containerization", "deployment", "Docker container setup"),
        ],
        satisfies={"deployment": "docker"},
        code={
            "flask": '''
# --- Dockerfile ---
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:create_app()"]


# --- docker-compose.yml ---
version: "3.8"

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY:-dev-secret}
      - DEBUG=false
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  # Uncomment for PostgreSQL
  # db:
  #   image: postgres:15
  #   environment:
  #     POSTGRES_USER: ${DB_USER:-app}
  #     POSTGRES_PASSWORD: ${DB_PASSWORD:-secret}
  #     POSTGRES_DB: ${DB_NAME:-appdb}
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   ports:
  #     - "5432:5432"

volumes:
  postgres_data:
''',
            "fastapi": '''
# --- Dockerfile ---
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]


# --- docker-compose.yml ---
version: "3.8"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY:-dev-secret}
      - DEBUG=false
    volumes:
      - ./data:/app/data
    restart: unless-stopped
''',
        },
        dependencies={
            "flask": ["gunicorn"],
            "fastapi": [],
        }
    ),
    
    # -------------------------------------------------------------------------
    # DATABASE - PRODUCTION
    # -------------------------------------------------------------------------
    "storage_postgres": Block(
        id="storage_postgres",
        name="PostgreSQL Storage",
        description="Production-grade PostgreSQL storage with connection pooling",
        requires=[],
        provides=[
            Port("storage", "service", "CRUD storage operations"),
            Port("database", "storage", "PostgreSQL database"),
            Port("transactions", "service", "ACID transactions"),
        ],
        satisfies={"database_type": "postgres", "storage_type": "production"},
        code={
            "flask": '''
# storage.py - PostgreSQL Storage Block

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool


class PostgresStorage:
    """PostgreSQL storage with connection pooling."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/appdb"
        )
        self.pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=self.database_url
        )
        self._init_db()
    
    @contextmanager
    def _conn(self):
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)
    
    def _init_db(self):
        """Initialize database schema."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS entities (
                        id TEXT PRIMARY KEY,
                        entity_type TEXT NOT NULL,
                        data JSONB NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_entity_type 
                    ON entities(entity_type)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_entity_data 
                    ON entities USING GIN (data)
                """)
    
    def create(self, entity: str, data: Dict) -> Dict:
        now = datetime.now().isoformat()
        item_id = f"{entity[:3]}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        item = {"id": item_id, "created_at": now, "updated_at": now, **data}
        
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO entities (id, entity_type, data, created_at, updated_at) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (item_id, entity, json.dumps(item), now, now)
                )
        return item
    
    def get(self, entity: str, id: str) -> Optional[Dict]:
        with self._conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT data FROM entities WHERE id = %s AND entity_type = %s",
                    (id, entity)
                )
                row = cur.fetchone()
                return row["data"] if row else None
    
    def list(self, entity: str, **filters) -> List[Dict]:
        with self._conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if filters:
                    # Use JSONB containment for filtering
                    cur.execute(
                        """SELECT data FROM entities 
                           WHERE entity_type = %s AND data @> %s
                           ORDER BY created_at DESC""",
                        (entity, json.dumps(filters))
                    )
                else:
                    cur.execute(
                        """SELECT data FROM entities 
                           WHERE entity_type = %s 
                           ORDER BY created_at DESC""",
                        (entity,)
                    )
                return [row["data"] for row in cur.fetchall()]
    
    def update(self, entity: str, id: str, data: Dict) -> Optional[Dict]:
        existing = self.get(entity, id)
        if not existing:
            return None
        
        now = datetime.now().isoformat()
        existing.update(data)
        existing["updated_at"] = now
        
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE entities SET data = %s, updated_at = %s 
                       WHERE id = %s AND entity_type = %s""",
                    (json.dumps(existing), now, id, entity)
                )
        return existing
    
    def delete(self, entity: str, id: str) -> bool:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM entities WHERE id = %s AND entity_type = %s",
                    (id, entity)
                )
                return cur.rowcount > 0
    
    def find_by_email(self, email: str) -> Optional[Dict]:
        with self._conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """SELECT data FROM entities 
                       WHERE entity_type = 'user' AND data->>'email' = %s""",
                    (email,)
                )
                row = cur.fetchone()
                return row["data"] if row else None
    
    def close(self):
        """Close connection pool."""
        self.pool.closeall()


storage = PostgresStorage()
''',
        },
        dependencies={
            "flask": ["psycopg2-binary"],
            "fastapi": ["psycopg2-binary", "asyncpg"],
        }
    ),
    
    # -------------------------------------------------------------------------
    # OAUTH - Social Login
    # -------------------------------------------------------------------------
    "auth_oauth": Block(
        id="auth_oauth",
        name="OAuth Social Login",
        description="Login with Google, GitHub, or other OAuth providers",
        requires=[
            Port("backend", "framework", "Web framework"),
            Port("storage", "service", "User storage"),
        ],
        provides=[
            Port("social_auth", "service", "OAuth authentication"),
            Port("oauth_routes", "route", "OAuth callback endpoints"),
        ],
        satisfies={"auth_type": "oauth"},
        code={
            "flask": '''
# oauth.py - OAuth Social Login Block

from flask import Blueprint, redirect, url_for, session, request, jsonify
from functools import wraps
import os
import secrets
import urllib.parse
import urllib.request
import json


class OAuthProvider:
    """Base OAuth provider."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    def get_auth_url(self, state: str) -> str:
        raise NotImplementedError
    
    def exchange_code(self, code: str) -> dict:
        raise NotImplementedError
    
    def get_user_info(self, access_token: str) -> dict:
        raise NotImplementedError


class GoogleOAuth(OAuthProvider):
    """Google OAuth 2.0 provider."""
    
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_auth_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "email profile",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    def exchange_code(self, code: str) -> dict:
        data = urllib.parse.urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }).encode()
        req = urllib.request.Request(self.TOKEN_URL, data=data)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    
    def get_user_info(self, access_token: str) -> dict:
        req = urllib.request.Request(
            self.USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())


class GitHubOAuth(OAuthProvider):
    """GitHub OAuth provider."""
    
    AUTH_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_INFO_URL = "https://api.github.com/user"
    
    def get_auth_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    def exchange_code(self, code: str) -> dict:
        data = urllib.parse.urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }).encode()
        req = urllib.request.Request(
            self.TOKEN_URL, 
            data=data,
            headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    
    def get_user_info(self, access_token: str) -> dict:
        req = urllib.request.Request(
            self.USER_INFO_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())


def create_oauth_routes(app, storage, providers: dict) -> Blueprint:
    """Create OAuth routes for all configured providers."""
    
    oauth_bp = Blueprint("oauth", __name__, url_prefix="/auth")
    
    @oauth_bp.route("/login/<provider>")
    def oauth_login(provider):
        if provider not in providers:
            return jsonify({"error": f"Unknown provider: {provider}"}), 400
        
        state = secrets.token_urlsafe(32)
        session["oauth_state"] = state
        
        auth_url = providers[provider].get_auth_url(state)
        return redirect(auth_url)
    
    @oauth_bp.route("/callback/<provider>")
    def oauth_callback(provider):
        if provider not in providers:
            return jsonify({"error": f"Unknown provider: {provider}"}), 400
        
        # Verify state
        state = request.args.get("state")
        if state != session.get("oauth_state"):
            return jsonify({"error": "Invalid state"}), 400
        
        code = request.args.get("code")
        if not code:
            return jsonify({"error": "No code provided"}), 400
        
        try:
            # Exchange code for token
            token_data = providers[provider].exchange_code(code)
            access_token = token_data.get("access_token")
            
            # Get user info
            user_info = providers[provider].get_user_info(access_token)
            
            # Find or create user
            email = user_info.get("email")
            existing = storage.find_by_email(email) if email else None
            
            if existing:
                user = existing
            else:
                user = storage.create("user", {
                    "email": email,
                    "username": user_info.get("name") or user_info.get("login"),
                    "oauth_provider": provider,
                    "oauth_id": str(user_info.get("id")),
                })
            
            session["user_id"] = user["id"]
            session.pop("oauth_state", None)
            
            return redirect(url_for("index"))
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    app.register_blueprint(oauth_bp)
    return oauth_bp


# Quick setup helper
def setup_oauth(app, storage):
    """Setup OAuth with environment variables."""
    providers = {}
    
    if os.environ.get("GOOGLE_CLIENT_ID"):
        providers["google"] = GoogleOAuth(
            client_id=os.environ["GOOGLE_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
            redirect_uri=os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/callback/google")
        )
    
    if os.environ.get("GITHUB_CLIENT_ID"):
        providers["github"] = GitHubOAuth(
            client_id=os.environ["GITHUB_CLIENT_ID"],
            client_secret=os.environ["GITHUB_CLIENT_SECRET"],
            redirect_uri=os.environ.get("GITHUB_REDIRECT_URI", "http://localhost:5000/auth/callback/github")
        )
    
    if providers:
        create_oauth_routes(app, storage, providers)
    
    return providers
''',
        },
        dependencies={
            "flask": [],  # No extra deps - uses stdlib
        }
    ),
    
    # -------------------------------------------------------------------------
    # EMAIL - SendGrid
    # -------------------------------------------------------------------------
    "email_sendgrid": Block(
        id="email_sendgrid",
        name="Email (SendGrid)",
        description="Send transactional emails via SendGrid API",
        requires=[],
        provides=[
            Port("email", "service", "Email sending capability"),
        ],
        satisfies={"email": True},
        code={
            "flask": '''
# email_service.py - SendGrid Email Block

import os
import urllib.request
import urllib.error
import json
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class EmailMessage:
    """Email message structure."""
    to: List[str]
    subject: str
    html_content: str
    text_content: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None


class SendGridEmail:
    """SendGrid email service."""
    
    API_URL = "https://api.sendgrid.com/v3/mail/send"
    
    def __init__(self, api_key: str = None, default_from: str = None):
        self.api_key = api_key or os.environ.get("SENDGRID_API_KEY")
        self.default_from = default_from or os.environ.get("SENDGRID_FROM_EMAIL", "noreply@example.com")
        
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY environment variable required")
    
    def send(self, message: EmailMessage) -> dict:
        """Send an email via SendGrid."""
        
        payload = {
            "personalizations": [{"to": [{"email": email} for email in message.to]}],
            "from": {
                "email": message.from_email or self.default_from,
                "name": message.from_name or "App"
            },
            "subject": message.subject,
            "content": []
        }
        
        if message.text_content:
            payload["content"].append({"type": "text/plain", "value": message.text_content})
        
        payload["content"].append({"type": "text/html", "value": message.html_content})
        
        req = urllib.request.Request(
            self.API_URL,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        try:
            with urllib.request.urlopen(req) as resp:
                return {"success": True, "status": resp.status}
        except urllib.error.HTTPError as e:
            return {"success": False, "error": e.read().decode(), "status": e.code}
    
    def send_simple(self, to: str, subject: str, html: str) -> dict:
        """Simple email send helper."""
        return self.send(EmailMessage(to=[to], subject=subject, html_content=html))
    
    def send_template(self, to: str, subject: str, template: str, **kwargs) -> dict:
        """Send email with template substitution."""
        html = template
        for key, value in kwargs.items():
            html = html.replace(f"{{{{{key}}}}}", str(value))
        return self.send_simple(to, subject, html)


# Common email templates
TEMPLATES = {
    "welcome": """
    <h1>Welcome, {{name}}!</h1>
    <p>Thanks for signing up. Get started by exploring your dashboard.</p>
    <a href="{{dashboard_url}}">Go to Dashboard</a>
    """,
    
    "password_reset": """
    <h1>Reset Your Password</h1>
    <p>Click the link below to reset your password:</p>
    <a href="{{reset_url}}">Reset Password</a>
    <p>This link expires in 1 hour.</p>
    """,
    
    "notification": """
    <h1>{{title}}</h1>
    <p>{{message}}</p>
    """,
}


# Singleton instance
email_service = None

def get_email_service() -> SendGridEmail:
    global email_service
    if email_service is None:
        email_service = SendGridEmail()
    return email_service


# Flask integration
def send_welcome_email(user: dict, dashboard_url: str = "/dashboard"):
    """Send welcome email to new user."""
    svc = get_email_service()
    return svc.send_template(
        to=user["email"],
        subject="Welcome!",
        template=TEMPLATES["welcome"],
        name=user.get("username", "there"),
        dashboard_url=dashboard_url
    )


def send_password_reset(email: str, reset_url: str):
    """Send password reset email."""
    svc = get_email_service()
    return svc.send_template(
        to=email,
        subject="Reset Your Password",
        template=TEMPLATES["password_reset"],
        reset_url=reset_url
    )
''',
        },
        dependencies={
            "flask": [],  # Uses stdlib
        }
    ),
    
    # -------------------------------------------------------------------------
    # CACHE - Redis
    # -------------------------------------------------------------------------
    "cache_redis": Block(
        id="cache_redis",
        name="Redis Cache",
        description="Redis-based caching for performance",
        requires=[],
        provides=[
            Port("cache", "service", "Caching capability"),
        ],
        satisfies={"cache": True},
        code={
            "flask": '''
# cache.py - Redis Cache Block

import os
import json
import hashlib
from functools import wraps
from typing import Any, Optional, Callable
import redis


class RedisCache:
    """Redis caching service."""
    
    def __init__(self, url: str = None, prefix: str = "app"):
        self.url = url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.prefix = prefix
        self.client = redis.from_url(self.url, decode_responses=True)
    
    def _key(self, key: str) -> str:
        """Prefix key for namespacing."""
        return f"{self.prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        data = self.client.get(self._key(key))
        if data:
            return json.loads(data)
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (default 1 hour)."""
        return self.client.setex(
            self._key(key),
            ttl,
            json.dumps(value, default=str)
        )
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        return bool(self.client.delete(self._key(key)))
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return bool(self.client.exists(self._key(key)))
    
    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        full_pattern = self._key(pattern)
        keys = self.client.keys(full_pattern)
        if keys:
            return self.client.delete(*keys)
        return 0
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        return self.client.incrby(self._key(key), amount)
    
    def get_or_set(self, key: str, factory: Callable, ttl: int = 3600) -> Any:
        """Get from cache or compute and store."""
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value


# Decorator for caching function results
def cached(ttl: int = 3600, key_prefix: str = None):
    """Cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Build cache key from function name and args
            prefix = key_prefix or func.__name__
            key_parts = [prefix] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try cache first
            result = cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        return wrapper
    return decorator


# Rate limiting helper
def rate_limit(key: str, limit: int, window: int = 60) -> tuple:
    """
    Check rate limit.
    
    Returns: (allowed: bool, remaining: int, reset_in: int)
    """
    cache = get_cache()
    full_key = f"ratelimit:{key}"
    
    current = cache.client.get(cache._key(full_key))
    if current is None:
        cache.client.setex(cache._key(full_key), window, 1)
        return (True, limit - 1, window)
    
    current = int(current)
    if current >= limit:
        ttl = cache.client.ttl(cache._key(full_key))
        return (False, 0, ttl)
    
    cache.incr(full_key)
    ttl = cache.client.ttl(cache._key(full_key))
    return (True, limit - current - 1, ttl)


# Singleton
_cache = None

def get_cache() -> RedisCache:
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache


# Flask middleware for rate limiting
def flask_rate_limit(limit: int = 60, window: int = 60):
    """Flask decorator for rate limiting."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            # Use IP as rate limit key
            key = request.remote_addr
            allowed, remaining, reset = rate_limit(key, limit, window)
            
            if not allowed:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": reset
                }), 429
            
            response = func(*args, **kwargs)
            return response
        
        return wrapper
    return decorator
''',
        },
        dependencies={
            "flask": ["redis"],
        }
    ),
    
    # -------------------------------------------------------------------------
    # FILE UPLOAD - S3
    # -------------------------------------------------------------------------
    "storage_s3": Block(
        id="storage_s3",
        name="S3 File Storage",
        description="Upload and serve files via AWS S3 or compatible",
        requires=[],
        provides=[
            Port("file_storage", "service", "File upload/download"),
        ],
        satisfies={"file_storage": True},
        code={
            "flask": '''
# file_storage.py - S3 File Storage Block

import os
import uuid
from datetime import datetime
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError


class S3FileStorage:
    """S3-compatible file storage service."""
    
    def __init__(
        self,
        bucket: str = None,
        region: str = None,
        endpoint_url: str = None,  # For MinIO/LocalStack
        access_key: str = None,
        secret_key: str = None,
    ):
        self.bucket = bucket or os.environ.get("S3_BUCKET", "app-uploads")
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        
        # Support custom endpoints (MinIO, LocalStack, etc.)
        self.endpoint_url = endpoint_url or os.environ.get("S3_ENDPOINT_URL")
        
        self.client = boto3.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key or os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
    
    def upload(
        self,
        file: BinaryIO,
        filename: str,
        folder: str = "uploads",
        content_type: str = None,
        public: bool = False,
    ) -> dict:
        """
        Upload a file to S3.
        
        Returns: {"key": str, "url": str, "size": int}
        """
        # Generate unique key
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        key = f"{folder}/{datetime.now().strftime('%Y/%m/%d')}/{unique_name}"
        
        # Get file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        # Upload
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if public:
            extra_args["ACL"] = "public-read"
        
        self.client.upload_fileobj(file, self.bucket, key, ExtraArgs=extra_args)
        
        # Build URL
        if self.endpoint_url:
            url = f"{self.endpoint_url}/{self.bucket}/{key}"
        else:
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
        
        return {
            "key": key,
            "url": url,
            "size": size,
            "filename": filename,
        }
    
    def download(self, key: str) -> bytes:
        """Download file from S3."""
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()
    
    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for private file access."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    
    def get_upload_url(self, key: str, content_type: str, expires_in: int = 3600) -> str:
        """Get presigned URL for direct upload from browser."""
        return self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
    
    def delete(self, key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
    
    def list_files(self, prefix: str = "", max_keys: int = 100) -> list:
        """List files with prefix."""
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            MaxKeys=max_keys,
        )
        return [
            {"key": obj["Key"], "size": obj["Size"], "modified": obj["LastModified"]}
            for obj in response.get("Contents", [])
        ]


# Singleton
_storage = None

def get_file_storage() -> S3FileStorage:
    global _storage
    if _storage is None:
        _storage = S3FileStorage()
    return _storage


# Flask routes for file upload
def create_upload_routes(app, allowed_types: list = None):
    """Create file upload routes."""
    from flask import Blueprint, request, jsonify
    
    upload_bp = Blueprint("upload", __name__, url_prefix="/api/files")
    allowed = allowed_types or ["image/jpeg", "image/png", "image/gif", "application/pdf"]
    
    @upload_bp.route("/upload", methods=["POST"])
    def upload_file():
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No filename"}), 400
        
        # Check content type
        if allowed and file.content_type not in allowed:
            return jsonify({"error": f"File type not allowed: {file.content_type}"}), 400
        
        storage = get_file_storage()
        result = storage.upload(
            file=file.stream,
            filename=file.filename,
            content_type=file.content_type,
            folder=request.form.get("folder", "uploads"),
        )
        
        return jsonify(result), 201
    
    @upload_bp.route("/presign", methods=["POST"])
    def get_presigned():
        """Get presigned URL for direct browser upload."""
        data = request.get_json()
        filename = data.get("filename")
        content_type = data.get("content_type")
        
        if not filename or not content_type:
            return jsonify({"error": "filename and content_type required"}), 400
        
        storage = get_file_storage()
        key = f"uploads/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}_{filename}"
        
        upload_url = storage.get_upload_url(key, content_type)
        
        return jsonify({
            "upload_url": upload_url,
            "key": key,
        })
    
    app.register_blueprint(upload_bp)
    return upload_bp
''',
        },
        dependencies={
            "flask": ["boto3"],
        }
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
