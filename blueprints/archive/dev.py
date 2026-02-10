#!/usr/bin/env python3
"""
DEV - Your Local Development Workflow

Start from an idea or existing code. Make changes live. Iterate forever.

Usage:
    python dev.py start "recipe manager with search"   # New project from idea
    python dev.py open ./my-project                    # Work on existing code
    python dev.py list                                 # Show your projects
    python dev.py run project-name                     # Run a project

The workflow:
    1. Start or open a project
    2. App runs with live-reload
    3. Make changes in VS Code (or ask the AI)
    4. See changes instantly in browser
    5. Stop when done - everything auto-saves
    6. Come back anytime with: python dev.py run project-name
"""

import sys
import os
import re
import json
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

PROJECTS_DIR = Path(__file__).parent / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

# =============================================================================
# PROJECT ANALYZER - Understand any codebase
# =============================================================================

def analyze_project(path: Path) -> dict:
    """Understand what an existing project is and how to run it."""
    
    info = {
        "path": str(path),
        "name": path.name,
        "files": [],
        "type": "unknown",
        "run_command": None,
        "main_file": None,
        "technologies": [],
        "description": ""
    }
    
    if not path.exists():
        info["error"] = "Path does not exist"
        return info
    
    # Collect all files
    for f in path.rglob("*"):
        if f.is_file() and not any(p in str(f) for p in ['__pycache__', '.git', 'node_modules', '.venv', 'venv']):
            info["files"].append(str(f.relative_to(path)))
    
    # Detect project type and find run command
    
    # Python Flask/FastAPI
    if (path / "app.py").exists():
        info["type"] = "python-web"
        info["main_file"] = "app.py"
        info["run_command"] = "python app.py"
        info["technologies"].append("Python")
        
        content = (path / "app.py").read_text(errors='ignore')
        if "flask" in content.lower():
            info["technologies"].append("Flask")
        if "fastapi" in content.lower():
            info["technologies"].append("FastAPI")
        if "sqlite" in content.lower():
            info["technologies"].append("SQLite")
    
    elif (path / "main.py").exists():
        info["type"] = "python"
        info["main_file"] = "main.py"
        info["run_command"] = "python main.py"
        info["technologies"].append("Python")
    
    # Node.js
    elif (path / "package.json").exists():
        info["type"] = "nodejs"
        info["main_file"] = "package.json"
        pkg = json.loads((path / "package.json").read_text())
        if "scripts" in pkg and "start" in pkg["scripts"]:
            info["run_command"] = "npm start"
        elif "scripts" in pkg and "dev" in pkg["scripts"]:
            info["run_command"] = "npm run dev"
        info["technologies"].append("Node.js")
        
        if (path / "index.html").exists():
            info["technologies"].append("HTML/CSS/JS")
    
    # Static HTML
    elif (path / "index.html").exists():
        info["type"] = "static-html"
        info["main_file"] = "index.html"
        info["run_command"] = "python -m http.server 5000"
        info["technologies"].append("HTML/CSS/JS")
    
    # Check for requirements.txt
    if (path / "requirements.txt").exists():
        info["has_requirements"] = True
    
    # Check for README
    for readme in ["README.md", "README.txt", "readme.md"]:
        if (path / readme).exists():
            content = (path / readme).read_text(errors='ignore')
            # First paragraph as description
            lines = content.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    info["description"] = line.strip()[:100]
                    break
    
    return info


# =============================================================================
# PROJECT CREATOR - Generate working apps from ideas
# =============================================================================

def create_project(name: str, idea: str, features: list) -> Path:
    """Create a new project from an idea."""
    
    project_dir = PROJECTS_DIR / name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    has_auth = "auth" in features
    has_search = "search" in features
    has_export = "export" in features
    
    title = name.replace("-", " ").title()
    
    # Create app.py
    app_lines = [
        '#!/usr/bin/env python3',
        '"""',
        f'{title}',
        f'Created: {datetime.now().strftime("%Y-%m-%d")}',
        f'Idea: {idea}',
        '"""',
        '',
        'from flask import Flask, request, jsonify, redirect, session',
        'import sqlite3',
        'from pathlib import Path',
        '',
        'app = Flask(__name__)',
        f'app.secret_key = "dev-{name}"',
        '',
        '# Database',
        'DB_PATH = Path(__file__).parent / "data.db"',
        '',
        'def get_db():',
        '    conn = sqlite3.connect(DB_PATH)',
        '    conn.row_factory = sqlite3.Row',
        '    return conn',
        '',
        'def init_db():',
        '    with get_db() as conn:',
        '        conn.execute("""',
        '            CREATE TABLE IF NOT EXISTS items (',
        '                id INTEGER PRIMARY KEY AUTOINCREMENT,',
        '                content TEXT NOT NULL,',
        '                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        '            )',
        '        """)',
        '        conn.commit()',
        '',
    ]
    
    if has_auth:
        app_lines.extend([
            'from functools import wraps',
            '',
            'USERS = {"admin": "admin123"}  # Change these!',
            '',
            'def login_required(f):',
            '    @wraps(f)',
            '    def decorated(*args, **kwargs):',
            '        if "user" not in session:',
            '            return redirect("/login")',
            '        return f(*args, **kwargs)',
            '    return decorated',
            '',
            '@app.route("/login", methods=["GET", "POST"])',
            'def login():',
            '    if request.method == "POST":',
            '        if USERS.get(request.form.get("username")) == request.form.get("password"):',
            '            session["user"] = request.form.get("username")',
            '            return redirect("/")',
            '    return open(Path(__file__).parent / "templates" / "login.html").read()',
            '',
            '@app.route("/logout")',
            'def logout():',
            '    session.pop("user", None)',
            '    return redirect("/login")',
            '',
        ])
    
    app_lines.extend([
        '# API Routes',
        '@app.route("/api/items", methods=["GET"])',
        'def list_items():',
        '    with get_db() as conn:',
        '        items = conn.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()',
        '        return jsonify({"items": [dict(row) for row in items]})',
        '',
        '@app.route("/api/items", methods=["POST"])',
        'def create_item():',
        '    data = request.get_json() or {}',
        '    content = data.get("content", "").strip()',
        '    if not content:',
        '        return jsonify({"error": "Content required"}), 400',
        '    with get_db() as conn:',
        '        cursor = conn.execute("INSERT INTO items (content) VALUES (?)", (content,))',
        '        conn.commit()',
        '        return jsonify({"id": cursor.lastrowid, "content": content})',
        '',
        '@app.route("/api/items/<int:item_id>", methods=["DELETE"])',
        'def delete_item(item_id):',
        '    with get_db() as conn:',
        '        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))',
        '        conn.commit()',
        '        return jsonify({"deleted": item_id})',
        '',
    ])
    
    if has_search:
        app_lines.extend([
            '@app.route("/api/search")',
            'def search_items():',
            '    q = request.args.get("q", "")',
            '    with get_db() as conn:',
            '        items = conn.execute(',
            '            "SELECT * FROM items WHERE content LIKE ?",',
            '            (f"%{q}%",)',
            '        ).fetchall()',
            '        return jsonify({"items": [dict(row) for row in items]})',
            '',
        ])
    
    if has_export:
        app_lines.extend([
            '@app.route("/api/export")',
            'def export_items():',
            '    with get_db() as conn:',
            '        items = conn.execute("SELECT * FROM items").fetchall()',
            '    return jsonify([dict(row) for row in items])',
            '',
        ])
    
    app_lines.extend([
        '# Main page',
        '@app.route("/")',
    ])
    
    if has_auth:
        app_lines.append('@login_required')
    
    app_lines.extend([
        'def index():',
        '    return open(Path(__file__).parent / "templates" / "index.html").read()',
        '',
        'if __name__ == "__main__":',
        '    init_db()',
        '    print()',
        '    print("=" * 50)',
        f'    print("  {title}")',
        '    print("=" * 50)',
        '    print()',
        '    print("  http://localhost:5000")',
    ])
    
    if has_auth:
        app_lines.extend([
            '    print()',
            '    print("  Login: admin / admin123")',
        ])
    
    app_lines.extend([
        '    print()',
        '    print("  Edit files in VS Code - changes reload automatically!")',
        '    print("  Press Ctrl+C to stop")',
        '    print()',
        '    app.run(debug=True, port=5000)',
    ])
    
    (project_dir / "app.py").write_text('\n'.join(app_lines))
    
    # Create templates
    templates_dir = project_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # index.html
    search_html = '''
        <div style="margin-bottom:20px">
            <input type="text" id="searchInput" placeholder="Search..." 
                   oninput="searchItems()" class="search-input">
        </div>''' if has_search else ""
    
    export_html = '''
        <div style="margin-top:20px">
            <a href="/api/export" download="data.json">
                <button class="btn-secondary">Export JSON</button>
            </a>
        </div>''' if has_export else ""
    
    logout_btn = '<a href="/logout"><button class="btn-secondary">Logout</button></a>' if has_auth else ""
    
    search_js = '''
        async function searchItems() {
            const q = document.getElementById('searchInput').value;
            const resp = await fetch('/api/search?q=' + encodeURIComponent(q));
            const data = await resp.json();
            renderItems(data.items);
        }''' if has_search else ""
    
    index_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
            color: #e0e0e0; 
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        h1 {{ 
            color: #667eea;
            font-size: 28px;
        }}
        .toolbar {{ 
            display: flex; 
            gap: 10px; 
            margin-bottom: 20px; 
        }}
        input[type="text"], .search-input {{ 
            flex: 1; 
            padding: 14px 18px; 
            background: rgba(255,255,255,0.05); 
            border: 2px solid rgba(255,255,255,0.1); 
            border-radius: 10px; 
            color: white; 
            font-size: 16px;
            transition: border-color 0.2s;
        }}
        input:focus {{ 
            outline: none; 
            border-color: #667eea;
            background: rgba(255,255,255,0.08);
        }}
        button, .btn {{ 
            padding: 14px 28px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            border: none; 
            border-radius: 10px; 
            cursor: pointer; 
            font-weight: 600;
            font-size: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        button:hover {{ 
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        .btn-secondary {{
            background: rgba(255,255,255,0.1);
            padding: 10px 20px;
        }}
        .btn-secondary:hover {{
            background: rgba(255,255,255,0.15);
            box-shadow: none;
            transform: none;
        }}
        .btn-danger {{
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            padding: 8px 16px;
            font-size: 13px;
        }}
        .items {{ display: flex; flex-direction: column; gap: 12px; }}
        .item {{ 
            background: rgba(255,255,255,0.05); 
            padding: 18px 20px; 
            border-radius: 12px;
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            border: 1px solid rgba(255,255,255,0.05);
            transition: background 0.2s;
        }}
        .item:hover {{
            background: rgba(255,255,255,0.08);
        }}
        .item-content {{
            font-size: 16px;
        }}
        .empty {{ 
            text-align: center; 
            padding: 60px 20px; 
            color: #666;
            font-size: 18px;
        }}
        .idea-note {{
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 20px;
            font-size: 14px;
            color: #a0a0ff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            {logout_btn}
        </div>
        
        <div class="idea-note">
            {idea}
        </div>
        
        {search_html}
        
        <div class="toolbar">
            <input type="text" id="newItem" placeholder="Add new item..." 
                   onkeypress="if(event.key==='Enter')addItem()">
            <button onclick="addItem()">Add</button>
        </div>
        
        <div class="items" id="itemList">
            <div class="empty">Loading...</div>
        </div>
        
        {export_html}
    </div>
    
    <script>
        async function loadItems() {{
            const resp = await fetch('/api/items');
            const data = await resp.json();
            renderItems(data.items);
        }}
        
        function renderItems(items) {{
            const container = document.getElementById('itemList');
            if (items.length === 0) {{
                container.innerHTML = '<div class="empty">No items yet. Add your first one above!</div>';
                return;
            }}
            container.innerHTML = items.map(item => 
                `<div class="item">
                    <span class="item-content">${{item.content}}</span>
                    <button class="btn-danger" onclick="deleteItem(${{item.id}})">Delete</button>
                </div>`
            ).join('');
        }}
        
        async function addItem() {{
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
        
        {search_js}
        
        loadItems();
    </script>
</body>
</html>'''
    
    (templates_dir / "index.html").write_text(index_html)
    
    # login.html if auth enabled
    if has_auth:
        login_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, sans-serif; 
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
        }
        .box { 
            background: rgba(255,255,255,0.05); 
            padding: 40px; 
            border-radius: 16px; 
            width: 320px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        h2 { color: white; margin-bottom: 24px; text-align: center; }
        input { 
            width: 100%; 
            padding: 14px; 
            margin-bottom: 14px; 
            border: 2px solid rgba(255,255,255,0.1);
            background: rgba(0,0,0,0.3);
            border-radius: 8px; 
            color: white;
            font-size: 16px;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button { 
            width: 100%; 
            padding: 14px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
        }
        .hint { 
            background: rgba(102,126,234,0.2); 
            padding: 12px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
            color: #a0a0ff; 
            font-size: 13px; 
            text-align: center; 
        }
    </style>
</head>
<body>
    <div class="box">
        <h2>Login</h2>
        <div class="hint">Default: admin / admin123</div>
        <form method="POST">
            <input name="username" placeholder="Username" required>
            <input name="password" type="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>'''
        (templates_dir / "login.html").write_text(login_html)
    
    # Create README
    login_section = ""
    if has_auth:
        login_section = """
## Login

Default: admin / admin123
"""
    
    readme = f'''# {title}

**Idea:** {idea}

## Quick Start

```bash
cd {project_dir}
python app.py
```

Open http://localhost:5000
{login_section}
## Development

- Edit any file in VS Code
- The app auto-reloads - just refresh the browser
- Your data is in `data.db`

## Evolving This Project

Ask the AI assistant to make changes! For example:
- "Add a priority field to items"
- "Change the color scheme to blue"
- "Add an edit button for each item"
- "Add categories/tags"

The AI can edit the files directly and your app will update.
'''
    (project_dir / "README.md").write_text(readme)
    
    # Create project.json for metadata
    project_meta = {
        "name": name,
        "idea": idea,
        "features": features,
        "created": datetime.now().isoformat(),
        "last_opened": datetime.now().isoformat()
    }
    (project_dir / "project.json").write_text(json.dumps(project_meta, indent=2))
    
    return project_dir


def slugify(text: str) -> str:
    """Convert text to a valid folder name."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:30].strip('-')


def detect_features(idea: str) -> list:
    """Detect features from natural language."""
    idea_lower = idea.lower()
    features = []
    
    if any(w in idea_lower for w in ["login", "auth", "user", "password", "secure", "private"]):
        features.append("auth")
    if any(w in idea_lower for w in ["search", "find", "filter", "query", "lookup"]):
        features.append("search")
    if any(w in idea_lower for w in ["export", "download", "backup", "save as"]):
        features.append("export")
    
    return features


# =============================================================================
# CLI
# =============================================================================

def list_projects():
    """List all projects."""
    print("\n  YOUR PROJECTS")
    print("  " + "=" * 48)
    
    projects = []
    for p in PROJECTS_DIR.iterdir():
        if p.is_dir() and (p / "project.json").exists():
            meta = json.loads((p / "project.json").read_text())
            projects.append((p.name, meta.get("idea", ""), meta.get("last_opened", "")))
    
    if not projects:
        print("\n  No projects yet. Create one with:")
        print('    python dev.py start "your idea here"')
        print()
        return
    
    for name, idea, last_opened in sorted(projects, key=lambda x: x[2], reverse=True):
        print(f"\n  {name}")
        if idea:
            print(f"    {idea[:60]}{'...' if len(idea) > 60 else ''}")
    
    print("\n  Run a project:")
    print("    python dev.py run <project-name>")
    print()


def run_project(path: Path):
    """Run a project with live reload."""
    
    if not path.exists():
        print(f"\n  Error: {path} does not exist")
        return
    
    info = analyze_project(path)
    
    if not info.get("run_command"):
        print(f"\n  Cannot auto-detect how to run this project.")
        print(f"  Files found: {len(info['files'])}")
        return
    
    # Update last_opened
    if (path / "project.json").exists():
        meta = json.loads((path / "project.json").read_text())
        meta["last_opened"] = datetime.now().isoformat()
        (path / "project.json").write_text(json.dumps(meta, indent=2))
    
    print()
    print("=" * 50)
    print(f"  Running: {info['name']}")
    print("=" * 50)
    print()
    print(f"  Tech: {', '.join(info['technologies'])}")
    print(f"  Command: {info['run_command']}")
    print()
    print("  The app will open in your browser.")
    print("  Edit files in VS Code - they auto-reload!")
    print()
    print("  Press Ctrl+C to stop")
    print()
    
    # Open browser after a delay
    import threading
    def open_browser():
        import time
        time.sleep(2)
        webbrowser.open("http://localhost:5000")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the project
    os.chdir(path)
    os.system(info["run_command"])


def main():
    args = sys.argv[1:]
    
    if not args:
        print("""
DEV - Your Local Development Workflow

Commands:
  python dev.py start "your idea"    Create and run a new project
  python dev.py open ./folder        Open and run existing code
  python dev.py list                 Show your projects
  python dev.py run <name>           Run a saved project

Workflow:
  1. Start or open a project
  2. App runs with live-reload
  3. Edit files in VS Code (or ask the AI)
  4. Changes appear instantly in browser
  5. Ctrl+C to stop - everything auto-saves
  6. Come back anytime!

Examples:
  python dev.py start "recipe manager with search"
  python dev.py start "todo app with login"
  python dev.py open ../my-existing-project
  python dev.py run recipe-manager
""")
        return
    
    cmd = args[0]
    
    if cmd == "list":
        list_projects()
        return
    
    if cmd == "start" and len(args) > 1:
        idea = " ".join(args[1:])
        name = slugify(idea)
        features = detect_features(idea)
        
        print(f"\n  Creating: {name}")
        print(f"  Idea: {idea}")
        print(f"  Features: {', '.join(features) if features else 'basic CRUD'}")
        
        project_dir = create_project(name, idea, features)
        print(f"  Created: {project_dir}")
        print()
        
        run_project(project_dir)
        return
    
    if cmd == "open" and len(args) > 1:
        path = Path(args[1]).resolve()
        
        print(f"\n  Analyzing: {path}")
        info = analyze_project(path)
        
        print(f"  Type: {info['type']}")
        print(f"  Tech: {', '.join(info['technologies'])}")
        print(f"  Files: {len(info['files'])}")
        
        if info.get("run_command"):
            print(f"  Run: {info['run_command']}")
            print()
            run_project(path)
        else:
            print("\n  Could not detect how to run this project.")
            print("  Make sure it has an app.py, main.py, or package.json")
        return
    
    if cmd == "run" and len(args) > 1:
        name = args[1]
        project_path = PROJECTS_DIR / name
        
        if not project_path.exists():
            # Try finding it
            matches = [p for p in PROJECTS_DIR.iterdir() if name.lower() in p.name.lower()]
            if matches:
                project_path = matches[0]
            else:
                print(f"\n  Project '{name}' not found.")
                print("  Use 'python dev.py list' to see your projects.")
                return
        
        run_project(project_path)
        return
    
    # Default: treat as idea
    idea = " ".join(args)
    name = slugify(idea)
    features = detect_features(idea)
    
    print(f"\n  Creating: {name}")
    project_dir = create_project(name, idea, features)
    run_project(project_dir)


if __name__ == "__main__":
    main()
