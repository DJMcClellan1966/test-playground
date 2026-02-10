# Auto-generated from Task contract
# Hash: c1bf2387

from flask import Blueprint, request, jsonify
from models import Task

task_bp = Blueprint("task", __name__, url_prefix="/api/task")

@task_bp.route("", methods=["POST"])
def create_task():
    """Create a new Task."""

    data = request.get_json()
    
    # Validate against contract
    if "title" not in data:
        return jsonify({"error": "title is required"}), 400
    if "done" not in data:
        return jsonify({"error": "done is required"}), 400
    
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
