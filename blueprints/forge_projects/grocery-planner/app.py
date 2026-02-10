#!/usr/bin/env python3
"""
Grocery Planner
Built with Forge - Template-based, no AI required
Created: 2026-02-10
"""

from flask import Flask, request, jsonify, session, redirect
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "forge-grocery-planner-2026-02-10"

# =============================================================================
# DATABASE - SQLite for simple local storage
# =============================================================================

DB_PATH = Path(__file__).parent / "data.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# =============================================================================
# CRUD API - Create, Read, Update, Delete
# =============================================================================

@app.route("/api/items", methods=["GET"])
def list_items():
    """Get all items."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()
        return jsonify({"items": [dict(r) for r in rows]})

@app.route("/api/items", methods=["POST"])
def create_item():
    """Create a new item."""
    data = request.get_json() or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Content is required"}), 400
    
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO items (content) VALUES (?)", (content,))
        conn.commit()
        return jsonify({"id": cursor.lastrowid, "content": content})

@app.route("/api/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    """Update an existing item."""
    data = request.get_json() or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Content is required"}), 400
    
    with get_db() as conn:
        conn.execute("UPDATE items SET content = ? WHERE id = ?", (content, item_id))
        conn.commit()
        return jsonify({"id": item_id, "content": content})

@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete an item."""
    with get_db() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        return jsonify({"deleted": item_id})

# =============================================================================
# SEARCH - Find items by content
# =============================================================================

@app.route("/api/search")
def search_items():
    """Search items by content."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"items": []})
    
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE content LIKE ? ORDER BY created_at DESC",
            (f"%{query}%",)
        ).fetchall()
        return jsonify({"items": [dict(r) for r in rows]})

# =============================================================================
# WEB INTERFACE
# =============================================================================

@app.route("/")
def index():
    """Serve the main page."""
    return open(Path(__file__).parent / "templates" / "index.html").read()

# =============================================================================
# START SERVER
# =============================================================================

if __name__ == "__main__":
    init_db()
    print()
    print("=" * 50)
    print("  Grocery Planner")
    print("=" * 50)
    print()
    print("  URL: http://localhost:5000")

    print()
    print("  Files auto-reload when you edit them.")
    print("  Press Ctrl+C to stop.")
    print()
    app.run(debug=True, port=5000)
