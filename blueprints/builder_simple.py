"""
Blueprint Builder - Simple & Working

A streamlined visual interface that actually works:
- Click blocks to select them (no complex drag-and-drop)
- Natural language: describe what you want
- Import existing code to analyze
- Live code preview
- Generate working apps

Based on the simple working version, with best features from NEXUS.

Run: python builder_simple.py
Opens: http://localhost:5000
"""

import os
import sys
import json
import webbrowser
import threading
import re
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))

from blocks import BLOCKS

PORT = 5000
OUTPUT_DIR = Path(__file__).parent / "output"


def get_blocks_json():
    """Get all blocks as JSON for the frontend."""
    blocks_list = []
    for block_id, block in BLOCKS.items():
        blocks_list.append({
            "id": block_id,
            "name": block.name,
            "description": block.description,
            "requires": [{"name": p.name, "type": p.type} for p in block.requires],
            "provides": [{"name": p.name, "type": p.type} for p in block.provides],
            "dependencies": block.dependencies.get("flask", []),
            "cost": getattr(block, 'cost', {"description": "Free"}) if hasattr(block, 'cost') else {"description": "Free"}
        })
    return blocks_list


def parse_natural_language(description: str) -> dict:
    """Parse natural language into block selections."""
    description = description.lower()
    
    suggested_blocks = []
    detected_intents = []
    
    # Intent detection with keywords
    intents = {
        "auth": ["auth", "login", "user", "account", "password", "sign in", "register"],
        "storage": ["save", "store", "database", "persist", "data", "record"],
        "realtime": ["realtime", "real-time", "live", "sync", "collaborative", "instant"],
        "api": ["api", "rest", "crud", "endpoint", "backend"],
        "email": ["email", "mail", "notification", "send message"],
        "cache": ["fast", "cache", "performance", "quick", "speed"],
        "deploy": ["deploy", "docker", "container", "production", "ship"]
    }
    
    for intent, keywords in intents.items():
        if any(kw in description for kw in keywords):
            detected_intents.append(intent)
    
    # Map intents to blocks
    if "auth" in detected_intents:
        if "oauth" in description or "google" in description or "github" in description:
            suggested_blocks.append("auth_oauth")
        else:
            suggested_blocks.append("auth_basic")
    
    if "storage" in detected_intents:
        if "postgres" in description or "sql" in description:
            suggested_blocks.append("storage_postgres")
        elif "s3" in description or "file" in description or "upload" in description:
            suggested_blocks.append("storage_s3")
        elif "sqlite" in description:
            suggested_blocks.append("storage_sqlite")
        else:
            suggested_blocks.append("storage_json")
    
    if "realtime" in detected_intents:
        suggested_blocks.append("websocket_basic")
        if "collaborative" in description or "sync" in description:
            suggested_blocks.append("sync_crdt")
    
    if "api" in detected_intents or len(detected_intents) > 1:
        suggested_blocks.append("crud_routes")
        if "fast" in description:
            suggested_blocks.append("backend_fastapi")
        else:
            suggested_blocks.append("backend_flask")
    
    if "email" in detected_intents:
        suggested_blocks.append("email_sendgrid")
    
    if "cache" in detected_intents:
        suggested_blocks.append("cache_redis")
    
    if "deploy" in detected_intents:
        suggested_blocks.append("docker_basic")
    
    # Calculate confidence
    confidence = len(detected_intents) / 3.0 if detected_intents else 0
    confidence = min(confidence, 1.0)
    
    # Remove duplicates
    suggested_blocks = list(dict.fromkeys(suggested_blocks))
    
    return {
        "blocks": suggested_blocks,
        "detected_intents": detected_intents,
        "confidence": confidence
    }


def analyze_code(code: str) -> dict:
    """Analyze code to detect patterns and suggest blocks."""
    detected_blocks = []
    evidence = {}
    
    patterns = {
        "backend_flask": [r"from flask import", r"Flask\(__name__\)", r"@app\.route"],
        "backend_fastapi": [r"from fastapi import", r"FastAPI\(\)", r"@app\.(get|post|put|delete)"],
        "storage_sqlite": [r"import sqlite3", r"sqlite3\.connect", r"\.execute\("],
        "storage_postgres": [r"import psycopg2", r"psycopg2\.connect"],
        "storage_json": [r"json\.(load|dump)", r"open\(.+\.json"],
        "storage_s3": [r"import boto3", r"s3\.upload", r"s3\.download"],
        "auth_basic": [r"session\[.user", r"login_required", r"@login_required", r"check_password"],
        "auth_oauth": [r"oauth", r"OAuth", r"google.*auth", r"github.*login"],
        "websocket_basic": [r"websocket", r"socketio", r"WebSocket"],
        "sync_crdt": [r"crdt", r"yjs", r"automerge"],
        "cache_redis": [r"import redis", r"Redis\(\)", r"\.cache"],
        "email_sendgrid": [r"sendgrid", r"smtp", r"send.*email"],
        "docker_basic": [r"FROM python", r"EXPOSE", r"CMD \["],
        "crud_routes": [r"@app\.(get|post|put|delete|patch)", r"/api/"],
        "html_templates": [r"render_template", r"\.html", r"jinja"]
    }
    
    for block_id, block_patterns in patterns.items():
        for pattern in block_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                if block_id not in detected_blocks:
                    detected_blocks.append(block_id)
                evidence[block_id] = evidence.get(block_id, []) + [pattern]
                break
    
    return {
        "blocks": detected_blocks,
        "evidence": evidence,
        "file_count": 1
    }


def analyze_directory(dir_path: str) -> dict:
    """Analyze a directory for patterns."""
    path = Path(dir_path.strip().strip('"').strip("'"))
    
    if not path.exists():
        return {"error": f"Directory not found: {dir_path}"}
    
    if not path.is_dir():
        return {"error": f"Not a directory: {dir_path}"}
    
    all_code = ""
    files_analyzed = []
    
    # Collect code files
    extensions = ['.py', '.js', '.ts', '.json', '.yaml', '.yml']
    for ext in extensions:
        for file_path in path.rglob(f"*{ext}"):
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                all_code += f"\n# File: {file_path.name}\n{content}"
                files_analyzed.append(str(file_path.relative_to(path)))
            except Exception:
                pass
    
    # Check for Dockerfile
    for dockerfile in path.rglob("Dockerfile*"):
        try:
            content = dockerfile.read_text(encoding='utf-8', errors='ignore')
            all_code += f"\n# File: {dockerfile.name}\n{content}"
            files_analyzed.append(str(dockerfile.relative_to(path)))
        except Exception:
            pass
    
    if not all_code:
        return {"error": "No code files found in directory"}
    
    result = analyze_code(all_code)
    result["files_analyzed"] = files_analyzed
    result["file_count"] = len(files_analyzed)
    
    return result


def generate_app(project_name: str, selected_blocks: list, description: str = "") -> dict:
    """Generate a working app from selected blocks."""
    output_path = OUTPUT_DIR / project_name.lower().replace(" ", "_")
    output_path.mkdir(parents=True, exist_ok=True)
    
    app_name = project_name.title().replace("_", " ")
    entity = project_name.lower().split()[0] if project_name else "item"
    
    # Analyze what's needed
    has_auth = any(b.startswith("auth_") for b in selected_blocks)
    has_storage = any(b.startswith("storage_") for b in selected_blocks)
    has_sqlite = "storage_sqlite" in selected_blocks
    has_crud = "crud_routes" in selected_blocks
    
    # Build app code
    imports = ["from flask import Flask, request, jsonify, session, redirect, render_template_string"]
    if has_auth:
        imports.append("from functools import wraps")
    if has_sqlite:
        imports.append("import sqlite3")
    imports.append("import secrets")
    
    app_code = f'''"""
{app_name} - Built with Blueprint Builder

Description: {description or "A web application"}
Blocks: {", ".join(selected_blocks) if selected_blocks else "minimal"}
"""

{chr(10).join(imports)}

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ============ STORAGE ============
'''
    
    if has_sqlite:
        app_code += f'''
DB_PATH = "{entity}s.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS {entity}s (id INTEGER PRIMARY KEY, content TEXT, done INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()

init_db()

def get_items():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, content, done FROM {entity}s")
    items = [{{"id": r[0], "content": r[1], "done": bool(r[2])}} for r in c.fetchall()]
    conn.close()
    return items

def add_item(content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO {entity}s (content) VALUES (?)", (content,))
    conn.commit()
    item_id = c.lastrowid
    conn.close()
    return item_id

def delete_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM {entity}s WHERE id = ?", (item_id,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
'''
    else:
        app_code += '''
items = []

def get_items():
    return items

def add_item(content):
    item = {"id": len(items), "content": content, "done": False}
    items.append(item)
    return item["id"]

def delete_item(item_id):
    global items
    original_len = len(items)
    items = [i for i in items if i["id"] != item_id]
    return len(items) < original_len
'''
    
    if has_auth:
        app_code += '''

# ============ AUTH ============
# DEFAULT LOGIN: admin / admin123
users = {"admin": "admin123"}  # Replace with real user storage

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    error_msg = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if users.get(username) == password:
            session["user"] = username
            return redirect("/")
        error_msg = "<p style='color:#e74c3c;margin-bottom:15px;'>Invalid credentials</p>"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #1a1a2e, #16213e); 
                   min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }}
            .login-box {{ background: rgba(255,255,255,0.05); padding: 40px; border-radius: 16px; 
                         border: 1px solid rgba(255,255,255,0.1); width: 100%; max-width: 350px; }}
            h2 {{ color: white; margin-bottom: 20px; text-align: center; }}
            input {{ width: 100%; padding: 12px; margin-bottom: 12px; border: 2px solid rgba(255,255,255,0.2); 
                    background: rgba(0,0,0,0.3); border-radius: 8px; color: white; font-size: 16px; box-sizing: border-box; }}
            input:focus {{ outline: none; border-color: #667eea; }}
            button {{ width: 100%; padding: 14px; background: #667eea; color: white; border: none; 
                     border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; }}
            button:hover {{ background: #5a6fd6; }}
            .hint {{ background: rgba(102, 126, 234, 0.2); border: 1px solid rgba(102, 126, 234, 0.4); 
                    padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; }}
            .hint-title {{ color: #667eea; font-size: 12px; margin-bottom: 5px; }}
            .hint-creds {{ color: white; font-family: monospace; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>Login</h2>
            {error_msg}
            <div class="hint">
                <div class="hint-title">DEFAULT CREDENTIALS</div>
                <div class="hint-creds">admin / admin123</div>
            </div>
            <form method="POST">
                <input name="username" placeholder="Username" required>
                <input name="password" type="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")
'''
    
    app_code += '''

# ============ API ROUTES ============
@app.route("/api/items", methods=["GET"])
def api_get_items():
    return jsonify({"items": get_items()})

@app.route("/api/items", methods=["POST"])
def api_add_item():
    data = request.get_json() or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Content required"}), 400
    item_id = add_item(content)
    return jsonify({"success": True, "id": item_id})

@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def api_delete_item(item_id):
    if delete_item(item_id):
        return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

# ============ WEB UI ============
@app.route("/")
'''
    
    if has_auth:
        app_code += "@login_required\n"
    
    app_code += f'''def home():
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
               background: linear-gradient(135deg, #1a1a2e, #16213e); 
               min-height: 100vh; padding: 40px; color: white; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        h1 {{ font-size: 2em; margin-bottom: 20px; }}
        .add-form {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        input {{ flex: 1; padding: 12px; border: 2px solid rgba(255,255,255,0.2); 
                background: rgba(255,255,255,0.1); border-radius: 8px; color: white; font-size: 16px; }}
        input:focus {{ outline: none; border-color: #667eea; }}
        button {{ background: #667eea; color: white; border: none; padding: 12px 24px; 
                 border-radius: 8px; cursor: pointer; font-weight: 600; }}
        button:hover {{ background: #5a6fd6; }}
        .items {{ list-style: none; }}
        .items li {{ background: rgba(255,255,255,0.05); padding: 15px; margin-bottom: 8px; 
                    border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }}
        .del {{ background: #e74c3c; padding: 8px 12px; font-size: 12px; }}
        .del:hover {{ background: #c0392b; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{app_name}</h1>
        <form class="add-form" onsubmit="addItem(event)">
            <input type="text" id="newItem" placeholder="Add new item...">
            <button type="submit">Add</button>
        </form>
        <ul class="items" id="itemsList"></ul>
    </div>
    <script>
        async function loadItems() {{
            const res = await fetch('/api/items');
            const data = await res.json();
            const list = document.getElementById('itemsList');
            list.innerHTML = data.items.map(item => `
                <li>
                    ${{item.content}}
                    <button class="del" onclick="deleteItem(${{item.id}})">Delete</button>
                </li>
            `).join('');
        }}
        async function addItem(e) {{
            e.preventDefault();
            const input = document.getElementById('newItem');
            const content = input.value.trim();
            if (!content) return;
            await fetch('/api/items', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{content}})
            }});
            input.value = '';
            loadItems();
        }}
        async function deleteItem(id) {{
            await fetch('/api/items/' + id, {{method: 'DELETE'}});
            loadItems();
        }}
        loadItems();
    </script>
</body>
</html>"""

if __name__ == "__main__":
    print(f"\\n  {app_name} running at http://localhost:5000")
'''
    
    # Add auth credentials message if auth is enabled
    if has_auth:
        app_code += '''    print("  ┌────────────────────────────────────┐")
    print("  │  LOGIN: admin / admin123           │")
    print("  └────────────────────────────────────┘")
'''
    
    app_code += '''    print()
    app.run(debug=True, port=5000)
'''
    
    # Write the app
    app_file = output_path / "app.py"
    app_file.write_text(app_code)
    
    # Write requirements
    deps = ["flask"]
    for block_id in selected_blocks:
        if block_id in BLOCKS:
            block_deps = BLOCKS[block_id].dependencies.get("flask", [])
            deps.extend(block_deps)
    deps = list(set(deps))
    
    req_file = output_path / "requirements.txt"
    req_file.write_text("\n".join(deps))
    
    return {
        "success": True,
        "path": str(output_path),
        "run_command": f"cd {output_path} && python app.py",
        "blocks": selected_blocks
    }


def get_code_preview(project_name: str, selected_blocks: list, description: str = "") -> str:
    """Get a preview of generated code."""
    has_auth = any(b.startswith("auth_") for b in selected_blocks)
    has_sqlite = "storage_sqlite" in selected_blocks
    
    preview = f'''# {project_name.title()} - Preview
# Blocks: {", ".join(selected_blocks) if selected_blocks else "none selected"}

from flask import Flask, request, jsonify
'''
    
    if has_sqlite:
        preview += "import sqlite3\n"
    if has_auth:
        preview += "from functools import wraps\n"
    
    preview += '''
app = Flask(__name__)

'''
    
    if has_sqlite:
        preview += '''# SQLite storage
def init_db():
    conn = sqlite3.connect("app.db")
    # ...create tables...
    conn.close()

'''
    else:
        preview += "items = []  # In-memory storage\n\n"
    
    if has_auth:
        preview += '''# Authentication
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

'''
    
    preview += '''# API Routes
@app.route("/api/items", methods=["GET"])
def get_items():
    return jsonify({"items": items})

@app.route("/api/items", methods=["POST"])
def add_item():
    # Add item logic...
    pass

if __name__ == "__main__":
    app.run(port=5000)
'''
    
    return preview


class BuilderHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the builder."""
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/":
            self.send_html(get_builder_html())
            return
        
        if parsed.path == "/api/blocks":
            self.send_json({"blocks": get_blocks_json()})
            return
        
        self.send_error(404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length else "{}"
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"})
            return
        
        if parsed.path == "/api/generate":
            result = generate_app(
                project_name=data.get("name", "my_app"),
                selected_blocks=data.get("blocks", []),
                description=data.get("description", "")
            )
            self.send_json(result)
            return
        
        if parsed.path == "/api/preview":
            preview = get_code_preview(
                project_name=data.get("name", "my_app"),
                selected_blocks=data.get("blocks", []),
                description=data.get("description", "")
            )
            self.send_json({"code": preview})
            return
        
        if parsed.path == "/api/parse":
            description = data.get("description", "")
            result = parse_natural_language(description)
            self.send_json(result)
            return
        
        if parsed.path == "/api/analyze-code":
            code = data.get("code", "")
            result = analyze_code(code)
            self.send_json(result)
            return
        
        if parsed.path == "/api/analyze-directory":
            dir_path = data.get("path", "")
            result = analyze_directory(dir_path)
            self.send_json(result)
            return
        
        self.send_error(404)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        pass


def get_builder_html():
    """Return the simple builder HTML."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blueprint Builder</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --primary: #667eea;
            --primary-dark: #5a6fd6;
            --success: #00b894;
            --danger: #e74c3c;
            --warning: #f39c12;
            --bg: #1a1a2e;
            --bg-card: #16213e;
            --text: #e0e0e0;
            --text-dim: #888;
            --border: rgba(255,255,255,0.1);
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--bg) 0%, var(--bg-card) 100%);
            min-height: 100vh;
            color: var(--text);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, var(--primary), #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: var(--text-dim);
        }
        
        /* Natural Language Input */
        .nl-section {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid var(--border);
        }
        
        .nl-section h2 {
            font-size: 1.2em;
            margin-bottom: 15px;
        }
        
        .nl-input-row {
            display: flex;
            gap: 10px;
        }
        
        .nl-input-row input {
            flex: 1;
            padding: 14px 18px;
            background: rgba(0,0,0,0.3);
            border: 2px solid var(--border);
            border-radius: 10px;
            color: var(--text);
            font-size: 1em;
        }
        
        .nl-input-row input:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .nl-btn {
            background: linear-gradient(135deg, var(--primary), #764ba2);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            font-size: 1em;
        }
        
        .nl-btn:hover {
            transform: translateY(-1px);
        }
        
        .nl-keywords {
            margin-top: 12px;
            font-size: 0.85em;
            color: var(--text-dim);
        }
        
        .nl-keywords span {
            background: rgba(102, 126, 234, 0.2);
            padding: 2px 8px;
            border-radius: 4px;
            margin: 2px;
            display: inline-block;
        }
        
        /* Main Grid */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-bottom: 25px;
        }
        
        .panel {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid var(--border);
        }
        
        .panel h2 {
            font-size: 1.2em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .panel h2::before {
            content: "";
            width: 4px;
            height: 20px;
            background: var(--primary);
            border-radius: 2px;
        }
        
        /* Form */
        .form-group {
            margin-bottom: 18px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-size: 0.9em;
            color: var(--text-dim);
        }
        
        input[type="text"], textarea {
            width: 100%;
            padding: 12px 16px;
            background: rgba(0,0,0,0.3);
            border: 2px solid var(--border);
            border-radius: 10px;
            color: var(--text);
            font-size: 1em;
        }
        
        input[type="text"]:focus, textarea:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        textarea {
            resize: vertical;
            min-height: 80px;
        }
        
        /* Blocks Grid */
        .blocks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 12px;
            max-height: 350px;
            overflow-y: auto;
            padding-right: 5px;
        }
        
        .block-card {
            background: rgba(0,0,0,0.3);
            border: 2px solid var(--border);
            border-radius: 10px;
            padding: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .block-card:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
        }
        
        .block-card.selected {
            border-color: var(--success);
            background: rgba(0, 184, 148, 0.15);
        }
        
        .block-card .name {
            font-weight: 600;
            margin-bottom: 4px;
            font-size: 0.95em;
        }
        
        .block-card .desc {
            font-size: 0.8em;
            color: var(--text-dim);
            line-height: 1.3;
        }
        
        /* Selected Tags */
        .selected-summary {
            margin-top: 20px;
            padding: 15px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }
        
        .selected-summary h3 {
            font-size: 0.9em;
            color: var(--text-dim);
            margin-bottom: 10px;
        }
        
        .selected-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .selected-tag {
            background: var(--success);
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .selected-tag .remove {
            cursor: pointer;
            opacity: 0.7;
            font-size: 1.1em;
        }
        
        .selected-tag .remove:hover {
            opacity: 1;
        }
        
        /* Import Section */
        .import-section {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }
        
        .import-section h3 {
            font-size: 0.9em;
            color: var(--text-dim);
            margin-bottom: 10px;
        }
        
        .import-row {
            display: flex;
            gap: 10px;
        }
        
        .import-row input {
            flex: 1;
            padding: 10px;
            font-size: 0.9em;
        }
        
        .import-btn {
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9em;
        }
        
        .import-btn:hover {
            border-color: var(--primary);
        }
        
        .import-result {
            margin-top: 10px;
            font-size: 0.85em;
            color: var(--success);
        }
        
        /* Code Preview */
        .code-preview {
            background: #0d1117;
            border-radius: 10px;
            padding: 20px;
            max-height: 300px;
            overflow: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            line-height: 1.5;
            color: #c9d1d9;
            border: 1px solid #30363d;
        }
        
        .code-preview code {
            white-space: pre;
        }
        
        /* Generate Section */
        .generate-section {
            text-align: center;
        }
        
        .btn-generate {
            background: linear-gradient(135deg, var(--primary), #764ba2);
            color: white;
            border: none;
            padding: 18px 50px;
            font-size: 1.2em;
            font-weight: 600;
            border-radius: 12px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn-generate:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        
        .btn-generate:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Result Panel */
        .result-panel {
            margin-top: 25px;
            display: none;
        }
        
        .result-panel.show {
            display: block;
        }
        
        .result-content {
            background: rgba(0, 184, 148, 0.1);
            border: 2px solid var(--success);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
        }
        
        .result-content h3 {
            color: var(--success);
            font-size: 1.5em;
            margin-bottom: 15px;
        }
        
        .result-content code {
            background: rgba(0,0,0,0.3);
            padding: 12px 20px;
            border-radius: 8px;
            display: block;
            font-family: 'Consolas', 'Monaco', monospace;
            margin: 15px 0;
            font-size: 0.95em;
        }
        
        .btn-copy {
            background: var(--success);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
        }
        
        .btn-copy:hover {
            background: #00a884;
        }
        
        /* Toast */
        .toast {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 12px 24px;
            border-radius: 8px;
            opacity: 0;
            transition: all 0.3s;
            z-index: 1000;
        }
        
        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); border-radius: 4px; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
        
        /* Loading */
        .loading {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 0.8s linear infinite;
            vertical-align: middle;
            margin-right: 8px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Blueprint Builder</h1>
            <p class="subtitle">Build backend apps with composable blocks</p>
        </header>
        
        <!-- Natural Language Section -->
        <div class="nl-section">
            <h2>Describe What You Need</h2>
            <div class="nl-input-row">
                <input type="text" id="nlInput" placeholder="e.g., 'API with auth and database' or 'realtime collaborative app'">
                <button class="nl-btn" onclick="parseDescription()">Build</button>
            </div>
            <div class="nl-keywords">
                <strong>Recognized:</strong>
                <span>auth/login</span>
                <span>database/storage</span>
                <span>api/crud</span>
                <span>realtime/websocket</span>
                <span>email</span>
                <span>cache/redis</span>
                <span>docker/deploy</span>
            </div>
        </div>
        
        <div class="main-grid">
            <!-- Left Panel: Project Config -->
            <div class="panel">
                <h2>Your Project</h2>
                
                <div class="form-group">
                    <label for="projectName">Project Name</label>
                    <input type="text" id="projectName" placeholder="my-awesome-app" value="my_app">
                </div>
                
                <div class="form-group">
                    <label for="description">Description</label>
                    <textarea id="description" placeholder="What does your app do?">A simple web application</textarea>
                </div>
                
                <div class="selected-summary">
                    <h3>Selected Blocks (<span id="blockCount">0</span>)</h3>
                    <div class="selected-tags" id="selectedTags">
                        <span style="color: var(--text-dim); font-size: 0.9em;">Click blocks to select them →</span>
                    </div>
                </div>
                
                <!-- Import Section -->
                <div class="import-section">
                    <h3>Or analyze existing code:</h3>
                    <div class="import-row">
                        <input type="text" id="importPath" placeholder="C:\\path\\to\\your\\project">
                        <button class="import-btn" onclick="analyzeDirectory()">Analyze</button>
                    </div>
                    <div class="import-result" id="importResult"></div>
                </div>
            </div>
            
            <!-- Right Panel: Blocks -->
            <div class="panel">
                <h2>Available Blocks</h2>
                <div class="blocks-grid" id="blocksGrid">
                    <div style="color: var(--text-dim);">Loading blocks...</div>
                </div>
            </div>
        </div>
        
        <!-- Live Preview -->
        <div class="panel" style="margin-bottom: 25px;">
            <h2>Code Preview</h2>
            <pre class="code-preview" id="codePreview"><code>// Select blocks to preview generated code...</code></pre>
        </div>
        
        <!-- Generate Button -->
        <div class="generate-section">
            <button class="btn-generate" id="generateBtn" onclick="generateApp()">
                Generate App
            </button>
        </div>
        
        <!-- Result Panel -->
        <div class="result-panel" id="resultPanel">
            <div class="result-content">
                <h3>✓ App Generated!</h3>
                <p>Your app has been created at:</p>
                <code id="resultPath"></code>
                <p>To run it:</p>
                <code id="resultCmd"></code>
                <button class="btn-copy" onclick="copyCommand()">Copy Command</button>
            </div>
        </div>
    </div>
    
    <div class="toast" id="toast"></div>
    
    <script>
        let blocks = [];
        let selectedBlocks = new Set();
        
        // Initialize
        async function init() {
            try {
                const response = await fetch('/api/blocks');
                const data = await response.json();
                blocks = data.blocks;
                renderBlocks();
            } catch (error) {
                console.error('Failed to load blocks:', error);
                document.getElementById('blocksGrid').innerHTML = 
                    '<div style="color: #e74c3c;">Failed to load blocks. Refresh the page.</div>';
            }
        }
        
        function renderBlocks() {
            const grid = document.getElementById('blocksGrid');
            grid.innerHTML = blocks.map(block => `
                <div class="block-card ${selectedBlocks.has(block.id) ? 'selected' : ''}" 
                     onclick="toggleBlock('${block.id}')">
                    <div class="name">${block.name}</div>
                    <div class="desc">${block.description}</div>
                </div>
            `).join('');
        }
        
        function toggleBlock(blockId) {
            if (selectedBlocks.has(blockId)) {
                selectedBlocks.delete(blockId);
            } else {
                selectedBlocks.add(blockId);
            }
            renderBlocks();
            renderSelectedTags();
            updatePreview();
        }
        
        function renderSelectedTags() {
            const container = document.getElementById('selectedTags');
            document.getElementById('blockCount').textContent = selectedBlocks.size;
            
            if (selectedBlocks.size === 0) {
                container.innerHTML = '<span style="color: var(--text-dim); font-size: 0.9em;">Click blocks to select them →</span>';
                return;
            }
            
            container.innerHTML = Array.from(selectedBlocks).map(id => {
                const block = blocks.find(b => b.id === id);
                return `
                    <span class="selected-tag">
                        ${block ? block.name : id}
                        <span class="remove" onclick="event.stopPropagation(); toggleBlock('${id}')">×</span>
                    </span>
                `;
            }).join('');
        }
        
        async function updatePreview() {
            const previewEl = document.getElementById('codePreview');
            
            try {
                const response = await fetch('/api/preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: document.getElementById('projectName').value,
                        description: document.getElementById('description').value,
                        blocks: Array.from(selectedBlocks)
                    })
                });
                
                const result = await response.json();
                previewEl.innerHTML = `<code>${escapeHtml(result.code)}</code>`;
            } catch (error) {
                console.error('Preview failed:', error);
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Natural language parsing
        async function parseDescription() {
            const input = document.getElementById('nlInput');
            const description = input.value.trim();
            
            if (!description) {
                toast('Enter a description first');
                return;
            }
            
            input.disabled = true;
            
            try {
                const response = await fetch('/api/parse', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description })
                });
                
                const result = await response.json();
                
                if (result.confidence === 0 || result.blocks.length === 0) {
                    toast('No patterns recognized. Try: auth, database, api, realtime, email, cache, docker');
                    return;
                }
                
                // Add detected blocks
                result.blocks.forEach(blockId => {
                    if (blocks.find(b => b.id === blockId)) {
                        selectedBlocks.add(blockId);
                    }
                });
                
                renderBlocks();
                renderSelectedTags();
                updatePreview();
                
                toast(`Added ${result.blocks.length} blocks: ${result.detected_intents.join(', ')}`);
                
            } catch (error) {
                console.error('Parse failed:', error);
                toast('Failed to parse description');
            } finally {
                input.disabled = false;
            }
        }
        
        // Analyze directory
        async function analyzeDirectory() {
            const pathInput = document.getElementById('importPath');
            const resultEl = document.getElementById('importResult');
            const path = pathInput.value.trim();
            
            if (!path) {
                toast('Enter a directory path');
                return;
            }
            
            resultEl.textContent = 'Analyzing...';
            
            try {
                const response = await fetch('/api/analyze-directory', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path })
                });
                
                const result = await response.json();
                
                if (result.error) {
                    resultEl.textContent = '';
                    resultEl.style.color = 'var(--danger)';
                    resultEl.textContent = result.error;
                    return;
                }
                
                // Add detected blocks
                result.blocks.forEach(blockId => {
                    if (blocks.find(b => b.id === blockId)) {
                        selectedBlocks.add(blockId);
                    }
                });
                
                renderBlocks();
                renderSelectedTags();
                updatePreview();
                
                resultEl.style.color = 'var(--success)';
                resultEl.textContent = `Found ${result.file_count} files, detected: ${result.blocks.join(', ') || 'none'}`;
                
            } catch (error) {
                console.error('Analyze failed:', error);
                resultEl.style.color = 'var(--danger)';
                resultEl.textContent = 'Analysis failed';
            }
        }
        
        // Generate app
        async function generateApp() {
            const btn = document.getElementById('generateBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading"></span> Generating...';
            btn.disabled = true;
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: document.getElementById('projectName').value,
                        description: document.getElementById('description').value,
                        blocks: Array.from(selectedBlocks)
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('resultPath').textContent = result.path;
                    document.getElementById('resultCmd').textContent = result.run_command;
                    document.getElementById('resultPanel').classList.add('show');
                    toast('App generated successfully!');
                } else {
                    toast('Generation failed');
                }
            } catch (error) {
                console.error('Generation failed:', error);
                toast('Generation failed. Check console.');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
        
        function copyCommand() {
            const cmd = document.getElementById('resultCmd').textContent;
            navigator.clipboard.writeText(cmd).then(() => {
                toast('Command copied!');
            }).catch(() => {
                toast('Copy failed');
            });
        }
        
        function toast(message) {
            const el = document.getElementById('toast');
            el.textContent = message;
            el.classList.add('show');
            setTimeout(() => el.classList.remove('show'), 3000);
        }
        
        // Enter to parse
        document.getElementById('nlInput').addEventListener('keypress', e => {
            if (e.key === 'Enter') parseDescription();
        });
        
        // Initialize
        init();
    </script>
</body>
</html>'''


def main():
    """Start the builder server."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    server = HTTPServer(("", PORT), BuilderHandler)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   Blueprint Builder - Simple & Working                       ║
║                                                              ║
║   Open: http://localhost:{PORT}                               ║
║                                                              ║
║   Features:                                                  ║
║   • Click blocks to select them                              ║
║   • Type natural language to auto-select blocks              ║
║   • Analyze existing code to detect patterns                 ║
║   • Live code preview                                        ║
║   • Generate working Flask apps                              ║
║                                                              ║
║   Press Ctrl+C to stop                                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Open browser
    def open_browser():
        webbrowser.open(f"http://localhost:{PORT}")
    
    threading.Timer(1.0, open_browser).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
