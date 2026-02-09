
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
