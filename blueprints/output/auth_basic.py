
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
