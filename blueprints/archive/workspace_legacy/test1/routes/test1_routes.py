# Auto-generated from test1 contract
# Hash: 81b5d86c

from flask import Blueprint, request, jsonify
from models import test1

test1_bp = Blueprint("test1", __name__, url_prefix="/api/test1")

@test1_bp.route("", methods=["POST"])
def create_test1():
    """Create a new test1."""

    data = request.get_json()
    
    # Validate against contract
    
    item = test1(**data)
    errors = item.validate() if hasattr(item, 'validate') else []
    if errors:
        return jsonify({"errors": errors}), 400
    
    # Storage
    saved = storage.create('test1', data)
    return jsonify(saved), 201

@test1_bp.route("", methods=["GET"])
def list_test1():
    """List all test1s."""
    items = storage.list('test1')
    return jsonify({"items": items, "total": len(items)})

@test1_bp.route("/<item_id>", methods=["GET"])
def get_test1(item_id):
    """Get a test1 by ID."""
    item = storage.get('test1', item_id)
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(item)
