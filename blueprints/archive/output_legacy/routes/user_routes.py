# Auto-generated from User contract
# Hash: 28391d59

from flask import Blueprint, request, jsonify
from models import User

user_bp = Blueprint("user", __name__, url_prefix="/api/user")

@user_bp.route("", methods=["POST"])
def create_user():
    """Create a new User."""

    data = request.get_json()
    
    # Validate against contract
    if "id" not in data:
        return jsonify({"error": "id is required"}), 400
    if "email" not in data:
        return jsonify({"error": "email is required"}), 400
    if "@" not in data.get("email", ""):
        return jsonify({"error": "email must be a valid email"}), 400
    if "username" not in data:
        return jsonify({"error": "username is required"}), 400
    if data.get("username", 0) < 3:
        return jsonify({"error": "username must be >= 3"}), 400
    if "password_hash" not in data:
        return jsonify({"error": "password_hash is required"}), 400
    
    item = User(**data)
    errors = item.validate() if hasattr(item, 'validate') else []
    if errors:
        return jsonify({"errors": errors}), 400
    
    # Storage
    saved = storage.create('user', data)
    return jsonify(saved), 201

@user_bp.route("", methods=["GET"])
def list_user():
    """List all Users."""
    items = storage.list('user')
    return jsonify({"items": items, "total": len(items)})

@user_bp.route("/<item_id>", methods=["GET"])
def get_user(item_id):
    """Get a User by ID."""
    item = storage.get('user', item_id)
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(item)
