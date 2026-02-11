"""Code generator - Builds working Flask apps from requirements."""

import os
from pathlib import Path
from typing import Dict, Any


class CodeGenerator:
    """Generates Flask app boilerplate from requirements."""
    
    def generate_app_py(self, app_name: str, answers: Dict[str, bool]) -> str:
        """Generate app.py based on requirements."""
        
        needs_db = answers.get("has_data", False)
        needs_auth = answers.get("needs_auth", False)
        needs_realtime = answers.get("realtime", False)
        needs_search = answers.get("search", False)
        
        imports = """from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
"""
        
        if needs_db:
            imports += "from flask_sqlalchemy import SQLAlchemy\n"
        
        if needs_auth:
            imports += "from werkzeug.security import generate_password_hash, check_password_hash\n"
        
        if needs_realtime:
            imports += "from flask_socketio import SocketIO, emit\n"
        
        app_init = f"""
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
"""
        
        if needs_db:
            app_init += """app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
"""
        
        if needs_realtime:
            app_init += "socketio = SocketIO(app, cors_allowed_origins='*')\n"
        
        # Models
        models = ""
        if needs_auth and needs_db:
            models = """
# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
"""
        
        # Routes
        routes = """
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "app": "%s"})
""" % app_name
        
        if needs_auth:
            routes += """
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    # TODO: Implement login
    return jsonify({"error": "Not implemented"}), 501

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route('/api/current_user')
def current_user():
    user_id = session.get('user_id')
    return jsonify({"user_id": user_id})
"""
        
        if needs_db and not needs_auth:
            routes += """
@app.route('/api/items')
def list_items():
    # TODO: Implement item listing
    return jsonify([])

@app.route('/api/items', methods=['POST'])
def create_item():
    # TODO: Implement item creation
    return jsonify({"id": 1}), 201
"""
        
        # Main
        main = """
if __name__ == '__main__':
"""
        
        if needs_db:
            main += """    with app.app_context():
        db.create_all()
"""
        
        if needs_realtime:
            main += "    socketio.run(app, debug=True, port=5000)\n"
        else:
            main += "    app.run(debug=True, port=5000)\n"
        
        return imports + app_init + models + routes + main
    
    def generate_requirements_txt(self, answers: Dict[str, bool]) -> str:
        """Generate requirements.txt based on features."""
        reqs = [
            "flask==3.0.2",
            "flask-cors==4.0.0",
        ]
        
        if answers.get("has_data"):
            reqs.append("flask-sqlalchemy==3.1.1")
        
        if answers.get("realtime"):
            reqs.append("python-socketio==5.9.0")
            reqs.append("python-engineio==4.7.1")
        
        return "\n".join(reqs) + "\n"
    
    def generate_index_html(self, app_name: str, answers: Dict[str, bool]) -> str:
        """Generate basic index.html."""
        
        title = app_name.title()
        has_auth = answers.get("needs_auth", False)
        
        auth_section = ""
        if has_auth:
            auth_section = """
    <div id="auth-section" style="margin: 20px 0; padding: 20px; background: #f0f0f0; border-radius: 8px;">
        <h3>Authentication</h3>
        <div id="login-form" style="display: none;">
            <input type="email" id="email" placeholder="Email" style="padding: 8px; margin: 5px; width: 200px;">
            <input type="password" id="password" placeholder="Password" style="padding: 8px; margin: 5px; width: 200px;">
            <button onclick="login()" style="padding: 8px 16px; background: #ff7a59; color: white; border: none; border-radius: 4px; cursor: pointer;">Login</button>
        </div>
        <div id="user-info" style="display: none;">
            <p>Logged in as: <strong id="username"></strong></p>
            <button onclick="logout()" style="padding: 8px 16px; background: #999; color: white; border: none; border-radius: 4px; cursor: pointer;">Logout</button>
        </div>
    </div>
"""
        
        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #ff7a59;
            padding-bottom: 10px;
        }}
        .status {{
            padding: 12px;
            background: #d4edda;
            color: #155724;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .loading {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border: 2px solid #ff7a59;
            border-top: 2px solid transparent;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="status">
            ✓ App is running! 
            <span class="loading"></span>
        </div>
        <p>Generated by App Forge - your constraint-driven app builder.</p>
        <p>This is your starting point. Edit <code>templates/index.html</code> and <code>app.py</code> to build your app.</p>
{auth_section}
        <h3>Next Steps:</h3>
        <ul>
            <li>Edit <code>app.py</code> to add features</li>
            <li>Create templates in <code>templates/</code></li>
            <li>Run <code>pip install -r requirements.txt</code> if needed</li>
            <li>Test in your browser</li>
        </ul>
    </div>
    <script>
        async function checkHealth() {{
            try {{
                const res = await fetch('/api/health');
                console.log(await res.json());
            }} catch(e) {{
                console.error('Health check failed:', e);
            }}
        }}
        checkHealth();
    </script>
</body>
</html>
"""


# Singleton
generator = CodeGenerator()
