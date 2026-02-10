"""
Test App - Built with Blueprint Builder

Description: Test
Blocks: storage_sqlite, crud_routes
"""

from flask import Flask, request, jsonify, session, redirect, render_template_string
import sqlite3
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ============ STORAGE ============

DB_PATH = "test_apps.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS test_apps (id INTEGER PRIMARY KEY, content TEXT, done INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()

init_db()

def get_items():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, content, done FROM test_apps")
    items = [{"id": r[0], "content": r[1], "done": bool(r[2])} for r in c.fetchall()]
    conn.close()
    return items

def add_item(content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO test_apps (content) VALUES (?)", (content,))
    conn.commit()
    item_id = c.lastrowid
    conn.close()
    return item_id

def delete_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM test_apps WHERE id = ?", (item_id,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


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
def home():
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test App</title>
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
        <h1>Test App</h1>
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
    print(f"\n  Test App running at http://localhost:5000\n")
    app.run(debug=True, port=5000)
