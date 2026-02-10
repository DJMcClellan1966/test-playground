"""
Canvas App - Built with Blueprint Sketchbook

Description: Built with visual canvas
Blocks: storage_json, crud_routes
Connections: 1 port connections
"""

from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = "blueprint-canvas_app-secret"

# In-memory storage
items = []

@app.route("/")
def home():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Canvas App</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               min-height: 100vh; padding: 40px; }
        .container { max-width: 600px; margin: 0 auto; background: white; 
                     border-radius: 16px; padding: 30px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        h1 { color: #333; margin-bottom: 20px; }
        .meta { background: #f0f4ff; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; color: #666; }
        form { display: flex; gap: 10px; margin-bottom: 20px; }
        input { flex: 1; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
        input:focus { outline: none; border-color: #667eea; }
        button { background: #667eea; color: white; border: none; padding: 12px 24px;
                 border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; }
        button:hover { background: #5a6fd6; }
        .items { list-style: none; }
        .items li { display: flex; align-items: center; padding: 12px; 
                    background: #f8f9fa; margin-bottom: 8px; border-radius: 8px; }
        .items li span { flex: 1; }
        .del { background: #e74c3c; padding: 6px 12px; font-size: 12px; }
        footer { margin-top: 30px; text-align: center; }
        footer a { color: #667eea; text-decoration: none; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Canvas App</h1>
        <div class="meta">Built with Blueprint Sketchbook | 2 blocks | 1 connections</div>
        <form id="f"><input id="c" placeholder="Add item..." required><button>Add</button></form>
        <ul class="items" id="items"></ul>
        <footer><a href="/explain">View architecture</a></footer>
    </div>
    <script>
        const load = async () => {
            const r = await fetch('/api/items');
            const d = await r.json();
            document.getElementById('items').innerHTML = d.items.map((x,i) => 
                `<li><span>${x.content||x}</span><button class="del" onclick="del(${i})">X</button></li>`).join('');
        };
        document.getElementById('f').onsubmit = async e => {
            e.preventDefault();
            await fetch('/api/items', {method:'POST', headers:{'Content-Type':'application/json'}, 
                body: JSON.stringify({content: document.getElementById('c').value})});
            document.getElementById('c').value = '';
            load();
        };
        const del = async i => { await fetch(`/api/items/${i}`, {method:'DELETE'}); load(); };
        load();
    </script>
</body>
</html>"""

@app.route("/api/items", methods=["GET"])
def list_items():
    return jsonify({"items": items})

@app.route("/api/items", methods=["POST"])
def add_item():
    data = request.json or {}
    items.append({"content": data.get("content", ""), "done": False})
    return jsonify({"success": True})

@app.route("/api/items/<int:idx>", methods=["DELETE"])
def delete_item(idx):
    if 0 <= idx < len(items):
        items.pop(idx)
    return jsonify({"success": True})

@app.route("/explain")
def explain():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Architecture - Canvas App</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #f5f5f5; padding: 40px; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 16px; padding: 40px; }
        h1 { color: #333; }
        h2 { color: #667eea; margin-top: 30px; }
        .block { background: #f0f4ff; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }
        .conn { background: #e8f5e9; padding: 10px; margin: 5px 0; border-radius: 4px; font-family: monospace; }
        .back { display: inline-block; margin-top: 20px; color: #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <h1>How Canvas App Works</h1>
        <p>This app was visually designed in the Blueprint Sketchbook.</p>
        
        <h2>Blocks (2)</h2>
        <div class="block"><strong>storage_json</strong> - Simple JSON file-based storage (development/small apps)</div><div class="block"><strong>crud_routes</strong> - Automatic REST endpoints for any entity</div>
        
        <h2>Port Connections (1)</h2>
        <div class="conn">1:storage -> 2:database</div>
        
        <h2>How It Works</h2>
        <p>Each block declares <strong>requires</strong> (inputs) and <strong>provides</strong> (outputs). 
           The visual sketchbook lets you wire these together, ensuring compatibility.</p>
        
        <a href="/" class="back">Back to app</a>
    </div>
</body>
</html>"""

if __name__ == "__main__":
    print("Starting Canvas App on http://localhost:5000")
    app.run(debug=True, port=5000)
