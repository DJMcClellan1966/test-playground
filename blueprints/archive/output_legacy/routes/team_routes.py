# Auto-generated from Team contract
# Hash: 9cde843f

from flask import Blueprint, request, jsonify
from models import Team

team_bp = Blueprint("team", __name__, url_prefix="/api/team")

@team_bp.route("", methods=["POST"])
def create_team():
    """Create a new Team."""

    data = request.get_json()
    
    # Validate against contract
    if "id" not in data:
        return jsonify({"error": "id is required"}), 400
    if "name" not in data:
        return jsonify({"error": "name is required"}), 400
    if "member_ids" not in data:
        return jsonify({"error": "member_ids is required"}), 400
    
    item = Team(**data)
    errors = item.validate() if hasattr(item, 'validate') else []
    if errors:
        return jsonify({"errors": errors}), 400
    
    # Storage
    saved = storage.create('team', data)
    return jsonify(saved), 201

@team_bp.route("", methods=["GET"])
def list_team():
    """List all Teams."""
    items = storage.list('team')
    return jsonify({"items": items, "total": len(items)})

@team_bp.route("/<item_id>", methods=["GET"])
def get_team(item_id):
    """Get a Team by ID."""
    item = storage.get('team', item_id)
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(item)
