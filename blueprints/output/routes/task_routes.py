# Auto-generated from Task contract
# Hash: 37615aaa

from flask import Blueprint, request, jsonify
from models import Task

task_bp = Blueprint("task", __name__, url_prefix="/api/task")

@task_bp.route("", methods=["POST"])
def create_task():
    """Create a new Task."""

    data = request.get_json()
    
    # Validate against contract
    if "id" not in data:
        return jsonify({"error": "id is required"}), 400
    if "title" not in data:
        return jsonify({"error": "title is required"}), 400
    if data.get("title", 0) < 1:
        return jsonify({"error": "title must be >= 1"}), 400
    if "priority" not in data:
        return jsonify({"error": "priority is required"}), 400
    if data.get("priority", 0) < 1:
        return jsonify({"error": "priority must be >= 1"}), 400
    if data.get("priority", 0) > 5:
        return jsonify({"error": "priority must be <= 5"}), 400
    if "completed" not in data:
        return jsonify({"error": "completed is required"}), 400
    if "user_id" not in data:
        return jsonify({"error": "user_id is required"}), 400
    
    item = Task(**data)
    errors = item.validate() if hasattr(item, 'validate') else []
    if errors:
        return jsonify({"errors": errors}), 400
    
    # Storage
    saved = storage.create('task', data)
    return jsonify(saved), 201

@task_bp.route("", methods=["GET"])
def list_task():
    """List all Tasks."""
    items = storage.list('task')
    return jsonify({"items": items, "total": len(items)})

@task_bp.route("/<item_id>", methods=["GET"])
def get_task(item_id):
    """Get a Task by ID."""
    item = storage.get('task', item_id)
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(item)
