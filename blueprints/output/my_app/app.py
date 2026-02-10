"""
My App - Built with Blueprint Builder

Description: A simple web application
Blocks: html_templates, auth_basic, storage_sqlite
"""

from flask import Flask, request, jsonify, session, redirect, render_template_string
from functools import wraps
import sqlite3
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ============ STORAGE ============

DB_PATH = "my_apps.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS my_apps (id INTEGER PRIMARY KEY, content TEXT, done INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()

init_db()

def get_items():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, content, done FROM my_apps")
    items = [{"id": r[0], "content": r[1], "done": bool(r[2])} for r in c.fetchall()]
    conn.close()
    return items

def add_item(content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO my_apps (content) VALUES (?)", (content,))
    conn.commit()
    item_id = c.lastrowid
    conn.close()
    return item_id

def delete_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM my_apps WHERE id = ?", (item_id,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ============ AUTH ============
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
@login_required
def home():
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My App</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
               background: linear-gradient(135deg, #1a1a2e, #16213e); 
               min-height: 100vh; padding: 40px; color: white; }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { font-size: 2em; margin-bottom: 20px; }
        .add-form { display: flex; gap: 10px; margin-bottom: 20px; }
        input { flex: 1; padding: 12px; border: 2px solid rgba(255,255,255,0.2); 
                background: rgba(255,255,255,0.1); border-radius: 8px; color: white; font-size: 16px; }
        input:focus { outline: none; border-color: #667eea; }
        button { background: #667eea; color: white; border: none; padding: 12px 24px; 
                 border-radius: 8px; cursor: pointer; font-weight: 600; }
        button:hover { background: #5a6fd6; }
        .items { list-style: none; }
        .items li { background: rgba(255,255,255,0.05); padding: 15px; margin-bottom: 8px; 
                    border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .del { background: #e74c3c; padding: 8px 12px; font-size: 12px; }
        .del:hover { background: #c0392b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>My App</h1>
        <form class="add-form" onsubmit="addItem(event)">
            <input type="text" id="newItem" placeholder="Add new item...">
            <button type="submit">Add</button>
        </form>
        <ul class="items" id="itemsList"></ul>
    </div>
    <script>
        async function loadItems() {
            const res = await fetch('/api/items');
            const data = await res.json();
            const list = document.getElementById('itemsList');
            list.innerHTML = data.items.map(item => `
                <li>
                    ${item.content}
                    <button class="del" onclick="deleteItem(${item.id})">Delete</button>
                </li>
            `).join('');
        }
        async function addItem(e) {
            e.preventDefault();
            const input = document.getElementById('newItem');
            const content = input.value.trim();
            if (!content) return;
            await fetch('/api/items', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content})
            });
            input.value = '';
            loadItems();
        }
        async function deleteItem(id) {
            await fetch('/api/items/' + id, {method: 'DELETE'});
            loadItems();
        }
        loadItems();
    </script>
</body>
</html>"""

if __name__ == "__main__":
    print(f"\n  My App running at http://localhost:5000\n")
    app.run(debug=True, port=5000)
