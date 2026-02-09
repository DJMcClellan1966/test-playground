"""
Project Routes

Auto-generated from Personal Website / Portfolio Blueprint blueprint.
RESTful API endpoints for Project resource.
"""

from flask import Blueprint, request, jsonify, abort
from datetime import datetime
from typing import Optional

# Create blueprint
project_bp = Blueprint("project", __name__, url_prefix="/api/project")

# In-memory storage (replace with database in production)
_storage = {}
_next_id = 1


def _get_next_id() -> str:
    global _next_id
    item_id = str(_next_id).zfill(4)
    _next_id += 1
    return item_id


# ==============================================================================
# List & Search
# ==============================================================================

@project_bp.route("", methods=["GET"])
@project_bp.route("/", methods=["GET"])
def list_all():
    """
    List all Project items.
    
    Query parameters:
    - search: Filter by text match
    - sort: Field to sort by (prefix with - for descending)
    - page: Page number (1-indexed)
    - per_page: Items per page (default 20)
    """
    items = list(_storage.values())
    
    # Text search
    search = request.args.get("search", "").lower()
    if search:
        items = [
            item for item in items
            if search in str(item).lower()
        ]
    
    # Sorting
    sort_field = request.args.get("sort", "created_at")
    reverse = sort_field.startswith("-")
    if reverse:
        sort_field = sort_field[1:]
    
    try:
        items.sort(key=lambda x: x.get(sort_field, ""), reverse=reverse)
    except TypeError:
        pass  # Skip sort if field values not comparable
    
    # Pagination
    total = len(items)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    start = (page - 1) * per_page
    end = start + per_page
    items = items[start:end]
    
    return jsonify({
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    })


# ==============================================================================
# Create
# ==============================================================================

@project_bp.route("", methods=["POST"])
@project_bp.route("/", methods=["POST"])
def create():
    """
    Create a new Project.
    
    Request body: JSON with Project fields
    Response: Created Project with ID and timestamps
    """
    data = request.get_json()
    
    if not data:
        abort(400, description="Request body is required")
    
    # Create item with metadata
    item_id = _get_next_id()
    now = datetime.now().isoformat()
    
    item = {
        "id": item_id,
        "created_at": now,
        "updated_at": now,
        **data
    }
    
    _storage[item_id] = item
    
    return jsonify(item), 201


# ==============================================================================
# Read
# ==============================================================================

@project_bp.route("/<item_id>", methods=["GET"])
def get_one(item_id: str):
    """
    Get a single Project by ID.
    
    Path parameter: item_id
    Response: Project object or 404
    """
    item = _storage.get(item_id)
    
    if not item:
        abort(404, description=f"Project with id '{item_id}' not found")
    
    return jsonify(item)


# ==============================================================================
# Update
# ==============================================================================

@project_bp.route("/<item_id>", methods=["PUT"])
def update_full(item_id: str):
    """
    Full update of a Project.
    
    Replaces all fields (except id and created_at).
    """
    item = _storage.get(item_id)
    
    if not item:
        abort(404, description=f"Project with id '{item_id}' not found")
    
    data = request.get_json()
    if not data:
        abort(400, description="Request body is required")
    
    # Preserve id and created_at, update everything else
    updated = {
        "id": item_id,
        "created_at": item["created_at"],
        "updated_at": datetime.now().isoformat(),
        **data
    }
    
    _storage[item_id] = updated
    
    return jsonify(updated)


@project_bp.route("/<item_id>", methods=["PATCH"])
def update_partial(item_id: str):
    """
    Partial update of a Project.
    
    Only updates provided fields.
    """
    item = _storage.get(item_id)
    
    if not item:
        abort(404, description=f"Project with id '{item_id}' not found")
    
    data = request.get_json()
    if not data:
        abort(400, description="Request body is required")
    
    # Merge with existing, update timestamp
    item.update(data)
    item["updated_at"] = datetime.now().isoformat()
    
    return jsonify(item)


# ==============================================================================
# Delete
# ==============================================================================

@project_bp.route("/<item_id>", methods=["DELETE"])
def delete(item_id: str):
    """
    Delete a Project.
    
    Returns 204 No Content on success, 404 if not found.
    """
    if item_id not in _storage:
        abort(404, description=f"Project with id '{item_id}' not found")
    
    del _storage[item_id]
    
    return "", 204


# ==============================================================================
# Bulk Operations
# ==============================================================================

@project_bp.route("/bulk", methods=["POST"])
def bulk_create():
    """
    Create multiple Project items at once.
    
    Request body: {"items": [...]}
    """
    data = request.get_json()
    
    if not data or "items" not in data:
        abort(400, description='Request body must have "items" array')
    
    created = []
    now = datetime.now().isoformat()
    
    for item_data in data["items"]:
        item_id = _get_next_id()
        item = {
            "id": item_id,
            "created_at": now,
            "updated_at": now,
            **item_data
        }
        _storage[item_id] = item
        created.append(item)
    
    return jsonify({"created": len(created), "items": created}), 201


@project_bp.route("/bulk", methods=["DELETE"])
def bulk_delete():
    """
    Delete multiple Project items.
    
    Request body: {"ids": ["id1", "id2", ...]}
    """
    data = request.get_json()
    
    if not data or "ids" not in data:
        abort(400, description='Request body must have "ids" array')
    
    deleted = 0
    for item_id in data["ids"]:
        if item_id in _storage:
            del _storage[item_id]
            deleted += 1
    
    return jsonify({"deleted": deleted})
