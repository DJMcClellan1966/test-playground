"""
blog - Flask Application

Auto-generated from Personal Website / Portfolio Blueprint blueprint.
Template-based generation - no LLM required.
"""

from flask import Flask, render_template, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

# Simple JSON file database (replace with SQLAlchemy for production)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def get_db_path(entity: str) -> str:
    """Get path to entity's JSON file."""
    return os.path.join(DATA_DIR, f"{entity}.json")


def load_data(entity: str) -> list:
    """Load all items for an entity."""
    path = get_db_path(entity)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


def save_data(entity: str, items: list):
    """Save all items for an entity."""
    with open(get_db_path(entity), "w") as f:
        json.dump(items, f, indent=2, default=str)


def find_item(items: list, item_id: str):
    """Find an item by ID."""
    for item in items:
        if item.get("id") == item_id:
            return item
    return None


# ==============================================================================
# Health & Home
# ==============================================================================

@app.route("/")
def index():
    """Home page - serve the blog frontend."""
    return render_template("index.html")


@app.route("/api")
def api_info():
    """API info endpoint."""
    return jsonify({
        "app": "blog",
        "version": "0.1.0",
        "status": "running",
        "blueprint": "Personal Website / Portfolio Blueprint"
    })


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


# ==============================================================================
# Generic CRUD Endpoints (PROJECT entity)
# ==============================================================================

@app.route("/api/project", methods=["GET"])
def list_project():
    """List all project items with optional filtering."""
    items = load_data("project")
    
    # Optional search filter
    search = request.args.get("search", "").lower()
    if search:
        items = [
            item for item in items 
            if search in json.dumps(item).lower()
        ]
    
    # Optional pagination
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", 10, type=int)
    
    if page:
        start = (page - 1) * per_page
        items = items[start:start + per_page]
    
    return jsonify({
        "items": items,
        "total": len(load_data("project")),
        "page": page or 1,
        "per_page": per_page
    })


@app.route("/api/project/<item_id>", methods=["GET"])
def get_project(item_id):
    """Get a single project by ID."""
    items = load_data("project")
    item = find_item(items, item_id)
    
    if not item:
        abort(404, description="Item not found")
    
    return jsonify(item)


@app.route("/api/project", methods=["POST"])
def create_project():
    """Create a new project."""
    data = request.get_json()
    
    if not data:
        abort(400, description="No data provided")
    
    items = load_data("project")
    
    # Generate ID and timestamps
    new_item = {
        "id": str(len(items) + 1).zfill(4),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **data
    }
    
    items.append(new_item)
    save_data("project", items)
    
    return jsonify(new_item), 201


@app.route("/api/project/<item_id>", methods=["PUT"])
def update_project(item_id):
    """Update an existing project."""
    data = request.get_json()
    
    if not data:
        abort(400, description="No data provided")
    
    items = load_data("project")
    item = find_item(items, item_id)
    
    if not item:
        abort(404, description="Item not found")
    
    # Update item
    item.update(data)
    item["updated_at"] = datetime.now().isoformat()
    
    save_data("project", items)
    
    return jsonify(item)


@app.route("/api/project/<item_id>", methods=["DELETE"])
def delete_project(item_id):
    """Delete a project."""
    items = load_data("project")
    original_len = len(items)
    
    items = [item for item in items if item.get("id") != item_id]
    
    if len(items) == original_len:
        abort(404, description="Item not found")
    
    save_data("project", items)
    
    return "", 204


# ==============================================================================
# Generic CRUD Endpoints (BLOG POST entity)
# ==============================================================================

@app.route("/api/posts", methods=["GET"])
def list_posts():
    """List all blog posts with optional filtering."""
    items = load_data("blog_post")
    
    # Optional search filter
    search = request.args.get("search", "").lower()
    if search:
        items = [
            item for item in items 
            if search in json.dumps(item).lower()
        ]
    
    # Optional pagination
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", 10, type=int)
    
    if page:
        start = (page - 1) * per_page
        items = items[start:start + per_page]
    
    return jsonify({
        "items": items,
        "total": len(load_data("blog_post")),
        "page": page or 1,
        "per_page": per_page
    })


@app.route("/api/posts/<item_id>", methods=["GET"])
def get_post(item_id):
    """Get a single blog post by ID."""
    items = load_data("blog_post")
    item = find_item(items, item_id)
    
    if not item:
        abort(404, description="Post not found")
    
    return jsonify(item)


@app.route("/api/posts", methods=["POST"])
def create_post():
    """Create a new blog post."""
    data = request.get_json()
    
    if not data:
        abort(400, description="No data provided")
    
    items = load_data("blog_post")
    
    # Generate ID and timestamps
    new_item = {
        "id": str(len(items) + 1).zfill(4),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **data
    }
    
    items.append(new_item)
    save_data("blog_post", items)
    
    return jsonify(new_item), 201


@app.route("/api/posts/<item_id>", methods=["PUT"])
def update_post(item_id):
    """Update an existing blog post."""
    data = request.get_json()
    
    if not data:
        abort(400, description="No data provided")
    
    items = load_data("blog_post")
    item = find_item(items, item_id)
    
    if not item:
        abort(404, description="Post not found")
    
    # Update item
    item.update(data)
    item["updated_at"] = datetime.now().isoformat()
    
    save_data("blog_post", items)
    
    return jsonify(item)


@app.route("/api/posts/<item_id>", methods=["DELETE"])
def delete_post(item_id):
    """Delete a blog post."""
    items = load_data("blog_post")
    original_len = len(items)
    
    items = [item for item in items if item.get("id") != item_id]
    
    if len(items) == original_len:
        abort(404, description="Post not found")
    
    save_data("blog_post", items)
    
    return "", 204


# ==============================================================================
# Error Handlers
# ==============================================================================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": str(error)}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server Error", "message": str(error)}), 500


# ==============================================================================
# Run Application
# ==============================================================================

if __name__ == "__main__":
    print(f"🚀 Starting blog...")
    print(f"📋 Blueprint: Personal Website / Portfolio Blueprint")
    print(f"🌐 http://localhost:5000")
    app.run(debug=True, port=5000)
