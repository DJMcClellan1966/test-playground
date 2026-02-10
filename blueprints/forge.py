#!/usr/bin/env python3
"""
FORGE - Template-Based App Builder (No AI Required)

Assembles working apps from proven templates. No guessing, no hallucination.
Same input = same output, every time.

Usage:
    python forge.py new "recipe tracker"              # Create from templates
    python forge.py new "tracker" --with auth search  # With specific features
    python forge.py run recipe-tracker                # Run a project
    python forge.py list                              # Show your projects
    python forge.py templates                         # Show available templates

The AI assistant is OPTIONAL. It can help if you're stuck, but:
- All code generation is template-based
- Templates are plain Python/HTML you can read and modify
- You own the code - edit it directly in VS Code
"""

import sys
import os
import re
import json
import shutil
from pathlib import Path
from datetime import datetime

FORGE_DIR = Path(__file__).parent / "forge_projects"
FORGE_DIR.mkdir(exist_ok=True)

# =============================================================================
# TEMPLATES - Proven, working code patterns
# =============================================================================

# These are the actual code templates - no AI, just copy/paste with variables

TEMPLATE_BASE = '''#!/usr/bin/env python3
"""
{title}
Built with Forge - Template-based, no AI required
Created: {date}
"""

from flask import Flask, request, jsonify, session, redirect
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "{secret_key}"

# =============================================================================
# DATABASE - SQLite for simple local storage
# =============================================================================

DB_PATH = Path(__file__).parent / "data.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
'''

TEMPLATE_AUTH = '''
# =============================================================================
# AUTHENTICATION - Simple username/password
# =============================================================================

from functools import wraps

# Default users - CHANGE THESE for production!
USERS = {
    "admin": "admin123",
    "user": "user123"
}

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle login form."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if USERS.get(username) == password:
            session["user"] = username
            return redirect("/")
    # Return login page
    return open(Path(__file__).parent / "templates" / "login.html").read()

@app.route("/logout")
def logout():
    """Log out current user."""
    session.pop("user", None)
    return redirect("/login")
'''

TEMPLATE_CRUD = '''
# =============================================================================
# CRUD API - Create, Read, Update, Delete
# =============================================================================

@app.route("/api/items", methods=["GET"])
def list_items():
    """Get all items."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()
        return jsonify({"items": [dict(r) for r in rows]})

@app.route("/api/items", methods=["POST"])
def create_item():
    """Create a new item."""
    data = request.get_json() or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Content is required"}), 400
    
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO items (content) VALUES (?)", (content,))
        conn.commit()
        return jsonify({"id": cursor.lastrowid, "content": content})

@app.route("/api/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    """Update an existing item."""
    data = request.get_json() or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Content is required"}), 400
    
    with get_db() as conn:
        conn.execute("UPDATE items SET content = ? WHERE id = ?", (content, item_id))
        conn.commit()
        return jsonify({"id": item_id, "content": content})

@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete an item."""
    with get_db() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        return jsonify({"deleted": item_id})
'''

TEMPLATE_SEARCH = '''
# =============================================================================
# SEARCH - Find items by content
# =============================================================================

@app.route("/api/search")
def search_items():
    """Search items by content."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"items": []})
    
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE content LIKE ? ORDER BY created_at DESC",
            (f"%{query}%",)
        ).fetchall()
        return jsonify({"items": [dict(r) for r in rows]})
'''

TEMPLATE_EXPORT = '''
# =============================================================================
# EXPORT - Download data as JSON
# =============================================================================

@app.route("/api/export")
def export_data():
    """Export all items as JSON."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        return jsonify([dict(r) for r in rows])
'''

TEMPLATE_MAIN = '''
# =============================================================================
# WEB INTERFACE
# =============================================================================

@app.route("/")
{auth_decorator}def index():
    """Serve the main page."""
    return open(Path(__file__).parent / "templates" / "index.html").read()

# =============================================================================
# START SERVER
# =============================================================================

if __name__ == "__main__":
    init_db()
    print()
    print("=" * 50)
    print("  {title}")
    print("=" * 50)
    print()
    print("  URL: http://localhost:5000")
{auth_message}
    print()
    print("  Files auto-reload when you edit them.")
    print("  Press Ctrl+C to stop.")
    print()
    app.run(debug=True, port=5000)
'''

# HTML Templates

TEMPLATE_INDEX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 48rem; margin: 0 auto; }}
        
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #334155;
        }}
        h1 {{ color: #60a5fa; font-size: 1.5rem; }}
        
        .add-form {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        input[type="text"] {{
            flex: 1;
            padding: 0.75rem 1rem;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 0.5rem;
            color: #e2e8f0;
            font-size: 1rem;
        }}
        input:focus {{
            outline: none;
            border-color: #60a5fa;
        }}
        
        button {{
            padding: 0.75rem 1.5rem;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
        }}
        button:hover {{ background: #2563eb; }}
        .btn-danger {{ background: #ef4444; padding: 0.5rem 1rem; font-size: 0.875rem; }}
        .btn-danger:hover {{ background: #dc2626; }}
        .btn-secondary {{ background: #475569; }}
        .btn-secondary:hover {{ background: #64748b; }}
        
        {search_styles}
        
        .items {{ display: flex; flex-direction: column; gap: 0.5rem; }}
        .item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background: #1e293b;
            border-radius: 0.5rem;
        }}
        .item-content {{ flex: 1; }}
        
        .empty {{
            text-align: center;
            padding: 3rem;
            color: #64748b;
        }}
        
        {export_styles}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            {logout_button}
        </header>
        
        {search_html}
        
        <div class="add-form">
            <input type="text" id="newItem" placeholder="Add new item..." 
                   onkeypress="if(event.key==='Enter')addItem()">
            <button onclick="addItem()">Add</button>
        </div>
        
        <div class="items" id="items">
            <div class="empty">Loading...</div>
        </div>
        
        {export_html}
    </div>
    
    <script>
        // Load items on page load
        async function loadItems() {{
            const resp = await fetch('/api/items');
            const data = await resp.json();
            renderItems(data.items);
        }}
        
        // Render items to the page
        function renderItems(items) {{
            const container = document.getElementById('items');
            if (items.length === 0) {{
                container.innerHTML = '<div class="empty">No items yet. Add one above!</div>';
                return;
            }}
            container.innerHTML = items.map(item => `
                <div class="item">
                    <span class="item-content">${{item.content}}</span>
                    <button class="btn-danger" onclick="deleteItem(${{item.id}})">Delete</button>
                </div>
            `).join('');
        }}
        
        // Add a new item
        async function addItem() {{
            const input = document.getElementById('newItem');
            const content = input.value.trim();
            if (!content) return;
            
            await fetch('/api/items', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ content }})
            }});
            input.value = '';
            loadItems();
        }}
        
        // Delete an item
        async function deleteItem(id) {{
            await fetch('/api/items/' + id, {{ method: 'DELETE' }});
            loadItems();
        }}
        
        {search_js}
        
        // Initial load
        loadItems();
    </script>
</body>
</html>'''

TEMPLATE_LOGIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-box {
            background: #1e293b;
            padding: 2rem;
            border-radius: 1rem;
            width: 100%;
            max-width: 20rem;
        }
        h2 { margin-bottom: 1.5rem; text-align: center; }
        input {
            width: 100%;
            padding: 0.75rem;
            margin-bottom: 0.75rem;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 0.5rem;
            color: #e2e8f0;
            font-size: 1rem;
        }
        input:focus { outline: none; border-color: #60a5fa; }
        button {
            width: 100%;
            padding: 0.75rem;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
            font-size: 1rem;
        }
        button:hover { background: #2563eb; }
        .hint {
            background: #1e40af20;
            border: 1px solid #1e40af40;
            padding: 0.75rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            text-align: center;
            font-size: 0.875rem;
            color: #93c5fd;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Login</h2>
        <div class="hint">
            Default: admin / admin123
        </div>
        <form method="POST">
            <input name="username" placeholder="Username" required>
            <input name="password" type="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>'''

# =============================================================================
# TEMPLATE FEATURES - What can be added
# =============================================================================

FEATURES = {
    "auth": {
        "name": "Authentication",
        "desc": "Login/logout with username and password",
        "keywords": ["login", "auth", "user", "password", "secure", "private", "account"],
    },
    "search": {
        "name": "Search",
        "desc": "Find items by keyword",
        "keywords": ["search", "find", "filter", "query", "lookup"],
    },
    "export": {
        "name": "Export",
        "desc": "Download data as JSON",
        "keywords": ["export", "download", "backup", "save"],
    },
}

# =============================================================================
# PROJECT BUILDER - Assemble templates into working app
# =============================================================================

def build_project(name: str, features: list) -> Path:
    """
    Assemble a project from templates.
    
    This is DETERMINISTIC - same name + features = same output every time.
    No AI, no guessing, no randomness.
    """
    
    project_dir = FORGE_DIR / name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    title = name.replace("-", " ").title()
    date = datetime.now().strftime("%Y-%m-%d")
    has_auth = "auth" in features
    has_search = "search" in features
    has_export = "export" in features
    
    # Build app.py by concatenating templates
    app_code = TEMPLATE_BASE.format(
        title=title,
        date=date,
        secret_key=f"forge-{name}-{date}"
    )
    
    if has_auth:
        app_code += TEMPLATE_AUTH
    
    app_code += TEMPLATE_CRUD
    
    if has_search:
        app_code += TEMPLATE_SEARCH
    
    if has_export:
        app_code += TEMPLATE_EXPORT
    
    # Main route and server start
    auth_decorator = "@login_required\n" if has_auth else ""
    auth_message = '    print("  Login: admin / admin123")' if has_auth else ""
    
    app_code += TEMPLATE_MAIN.format(
        title=title,
        auth_decorator=auth_decorator,
        auth_message=auth_message
    )
    
    (project_dir / "app.py").write_text(app_code)
    
    # Build templates directory
    templates_dir = project_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Build index.html
    search_styles = ".search-box { margin-bottom: 1rem; }" if has_search else ""
    search_html = '''<div class="search-box">
            <input type="text" id="searchInput" placeholder="Search..." 
                   oninput="searchItems()" style="width:100%">
        </div>''' if has_search else ""
    search_js = '''
        async function searchItems() {
            const q = document.getElementById('searchInput').value.trim();
            if (!q) { loadItems(); return; }
            const resp = await fetch('/api/search?q=' + encodeURIComponent(q));
            const data = await resp.json();
            renderItems(data.items);
        }''' if has_search else ""
    
    export_styles = ".export-section { margin-top: 1.5rem; }" if has_export else ""
    export_html = '''<div class="export-section">
            <a href="/api/export" download="data.json">
                <button class="btn-secondary">Export JSON</button>
            </a>
        </div>''' if has_export else ""
    
    logout_button = '<a href="/logout"><button class="btn-secondary">Logout</button></a>' if has_auth else ""
    
    index_html = TEMPLATE_INDEX_HTML.format(
        title=title,
        search_styles=search_styles,
        search_html=search_html,
        search_js=search_js,
        export_styles=export_styles,
        export_html=export_html,
        logout_button=logout_button
    )
    
    (templates_dir / "index.html").write_text(index_html)
    
    if has_auth:
        (templates_dir / "login.html").write_text(TEMPLATE_LOGIN_HTML)
    
    # Create project metadata
    meta = {
        "name": name,
        "title": title,
        "features": features,
        "created": date,
        "last_run": None
    }
    (project_dir / "forge.json").write_text(json.dumps(meta, indent=2))
    
    # Create README
    feature_list = "\n".join(f"- {FEATURES[f]['name']}: {FEATURES[f]['desc']}" for f in features if f in FEATURES)
    if not feature_list:
        feature_list = "- Basic CRUD (Create, Read, Update, Delete)"
    
    readme = f'''# {title}

Built with Forge - Template-based, no AI required.

## Run

```bash
python app.py
```

Then open http://localhost:5000

## Features

{feature_list}

## Files

- `app.py` - The Flask application (edit this!)
- `templates/index.html` - The web interface (edit this!)
- `data.db` - SQLite database (created on first run)

## Editing

All code is plain Python and HTML. Edit directly in VS Code.
Changes auto-reload - just refresh the browser.

No AI required. If you want AI help, just ask - but the code you see
is exactly what's running. No magic, no hidden generation.
'''
    (project_dir / "README.md").write_text(readme)
    
    return project_dir


def detect_features(words: list) -> list:
    """Detect features from words in the name/description."""
    detected = []
    all_words = " ".join(words).lower()
    
    for feature_id, feature in FEATURES.items():
        for keyword in feature["keywords"]:
            if keyword in all_words:
                detected.append(feature_id)
                break
    
    return detected


def slugify(text: str) -> str:
    """Convert text to a valid folder name."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:40].strip('-')


# =============================================================================
# CLI
# =============================================================================

def cmd_new(args: list):
    """Create a new project."""
    if not args:
        print("\n  Usage: python forge.py new \"project name\" [--with feature1 feature2]")
        print("\n  Example: python forge.py new \"recipe tracker\" --with auth search")
        return
    
    # Parse args
    name_parts = []
    features = []
    in_with = False
    
    for arg in args:
        if arg == "--with":
            in_with = True
        elif in_with:
            features.append(arg)
        else:
            name_parts.append(arg)
    
    name_text = " ".join(name_parts)
    name = slugify(name_text)
    
    # Auto-detect features from name if none specified
    if not features:
        features = detect_features(name_parts)
    
    print(f"\n  Creating: {name}")
    print(f"  Features: {', '.join(features) if features else 'basic CRUD'}")
    
    project_dir = build_project(name, features)
    
    print(f"  Location: {project_dir}")
    print()
    print("  Run it:")
    print(f"    cd {project_dir}")
    print("    python app.py")
    print()


def cmd_run(args: list):
    """Run a project."""
    if not args:
        print("\n  Usage: python forge.py run <project-name>")
        print("  Use 'python forge.py list' to see your projects.")
        return
    
    name = args[0]
    project_dir = FORGE_DIR / name
    
    if not project_dir.exists():
        # Try partial match
        matches = [p for p in FORGE_DIR.iterdir() if p.is_dir() and name.lower() in p.name.lower()]
        if matches:
            project_dir = matches[0]
        else:
            print(f"\n  Project '{name}' not found.")
            print("  Use 'python forge.py list' to see your projects.")
            return
    
    # Update last_run
    meta_file = project_dir / "forge.json"
    if meta_file.exists():
        meta = json.loads(meta_file.read_text())
        meta["last_run"] = datetime.now().isoformat()
        meta_file.write_text(json.dumps(meta, indent=2))
    
    print(f"\n  Running: {project_dir.name}")
    print()
    
    os.chdir(project_dir)
    os.system("python app.py")


def cmd_list(args: list):
    """List all projects."""
    print("\n  YOUR PROJECTS")
    print("  " + "=" * 50)
    
    projects = []
    for p in FORGE_DIR.iterdir():
        if p.is_dir() and (p / "forge.json").exists():
            meta = json.loads((p / "forge.json").read_text())
            projects.append((p.name, meta.get("features", []), meta.get("last_run")))
    
    if not projects:
        print("\n  No projects yet.")
        print("\n  Create one:")
        print('    python forge.py new "my project"')
        print()
        return
    
    for name, features, last_run in sorted(projects):
        feature_str = ", ".join(features) if features else "basic"
        print(f"\n  {name}")
        print(f"    Features: {feature_str}")
    
    print()
    print("  Run a project:")
    print("    python forge.py run <name>")
    print()


def cmd_templates(args: list):
    """Show available features/templates."""
    print("\n  AVAILABLE FEATURES")
    print("  " + "=" * 50)
    
    print("\n  Base (always included):")
    print("    - Flask web server")
    print("    - SQLite database")
    print("    - CRUD API (Create, Read, Update, Delete)")
    print("    - Responsive web interface")
    
    print("\n  Optional features (--with):")
    for fid, f in FEATURES.items():
        print(f"\n    {fid}")
        print(f"      {f['desc']}")
        print(f"      Triggers: {', '.join(f['keywords'][:4])}")
    
    print()
    print("  Example:")
    print('    python forge.py new "todo app" --with auth search')
    print()


def main():
    args = sys.argv[1:]
    
    if not args:
        print("""
FORGE - Template-Based App Builder

No AI required. Same input = same output, every time.

Commands:
  python forge.py new "name"              Create a new project
  python forge.py new "name" --with auth  Create with specific features
  python forge.py run <name>              Run a project
  python forge.py list                    Show your projects
  python forge.py templates               Show available features

Examples:
  python forge.py new "recipe tracker"
  python forge.py new "todo app" --with auth search
  python forge.py run recipe-tracker

How it works:
  1. You describe what you want
  2. Forge assembles pre-written templates
  3. You get working code you can read and edit
  4. No AI involved in code generation

The AI assistant is OPTIONAL - ask it for help if stuck,
but the code itself is just templates. No magic.
""")
        return
    
    cmd = args[0]
    rest = args[1:]
    
    if cmd == "new":
        cmd_new(rest)
    elif cmd == "run":
        cmd_run(rest)
    elif cmd == "list":
        cmd_list(rest)
    elif cmd == "templates":
        cmd_templates(rest)
    else:
        # Treat as project name
        cmd_new(args)


if __name__ == "__main__":
    main()
