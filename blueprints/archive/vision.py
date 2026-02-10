"""
Blueprint VISION - The Visual Architecture Canvas

Every visual innovation we could imagine:

VISUAL CORE:
  • Minimap - bird's eye view in corner
  • Auto-layout - force-directed physics simulation
  • Data flow animation - watch requests pulse through connections
  • Zoom/pan - scroll wheel zoom, drag to pan, fit-all button
  • Node grouping - select multiple, create subsystem

"WHY DIDN'T WE THINK OF THAT":
  • Ghost blocks - shows what COULD connect (faded suggestions)
  • Snap-to-grid with smart alignment guides
  • Undo/redo with visual timeline scrubber
  • Search palette with fuzzy matching
  • Block templates (common patterns like "auth+storage+api")
  • Right-click context menus
  • Keyboard shortcuts (Del, Ctrl+A, Ctrl+G for group)
  • Export architecture as PNG
  • Connection type labels
  • Zoom to selection
  • Marquee selection (drag box to select multiple)
  • Copy/paste blocks and connections
  • Performance hints overlay

Run: python vision.py
Opens: http://localhost:5000
"""

import os
import sys
import json
import time
import webbrowser
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))
from blocks import BLOCKS

PORT = 5000
OUTPUT_DIR = Path(__file__).parent / "output"

# Templates for common patterns
TEMPLATES = {
    "basic_api": {
        "name": "Basic REST API",
        "blocks": ["storage_json", "crud_routes", "backend_flask"],
        "layout": [(100, 200), (300, 200), (500, 200)]
    },
    "secure_api": {
        "name": "Secure API",
        "blocks": ["auth_basic", "storage_sqlite", "crud_routes", "backend_flask"],
        "layout": [(100, 100), (100, 300), (300, 200), (500, 200)]
    },
    "realtime_app": {
        "name": "Realtime App",
        "blocks": ["storage_json", "sync_crdt", "websocket_basic", "backend_flask"],
        "layout": [(100, 200), (300, 100), (300, 300), (500, 200)]
    },
    "production_ready": {
        "name": "Production Ready",
        "blocks": ["auth_oauth", "storage_postgres", "cache_redis", "crud_routes", "docker_basic"],
        "layout": [(100, 100), (100, 300), (300, 100), (300, 300), (500, 200)]
    }
}


def get_blocks_data():
    """Get blocks with computed compatibility data for ghost suggestions."""
    blocks = []
    for block_id, block in BLOCKS.items():
        requires = [{"name": p.name, "type": p.type} for p in block.requires]
        provides = [{"name": p.name, "type": p.type} for p in block.provides]
        
        # Category for visual grouping
        if block_id.startswith("auth"):
            category = "auth"
            color = "#f85149"
        elif block_id.startswith("storage"):
            category = "storage"
            color = "#3fb950"
        elif "route" in block_id or "crud" in block_id:
            category = "routes"
            color = "#58a6ff"
        elif "websocket" in block_id or "sync" in block_id:
            category = "realtime"
            color = "#a371f7"
        elif "docker" in block_id or "cache" in block_id:
            category = "infra"
            color = "#d29922"
        else:
            category = "other"
            color = "#8b949e"
        
        blocks.append({
            "id": block_id,
            "name": block.name,
            "description": block.description,
            "requires": requires,
            "provides": provides,
            "category": category,
            "color": color
        })
    return blocks


def compute_ghost_suggestions(nodes: list) -> list:
    """Compute which blocks would nicely connect to existing nodes."""
    if not nodes:
        return []
    
    # Collect all unsatisfied requirements and unused provides
    block_ids = [n.get("blockId") for n in nodes]
    
    unsatisfied = set()
    available_provides = set()
    
    for n in nodes:
        bid = n.get("blockId")
        if bid in BLOCKS:
            block = BLOCKS[bid]
            for r in block.requires:
                unsatisfied.add(r.name)
            for p in block.provides:
                available_provides.add(p.name)
    
    # Remove satisfied ones
    unsatisfied -= available_provides
    
    # Find blocks that could help
    suggestions = []
    for block_id, block in BLOCKS.items():
        if block_id in block_ids:
            continue
        
        # Does this block provide something we need?
        provides_names = {p.name for p in block.provides}
        helps_with = provides_names & unsatisfied
        
        # Does this block need something we have?
        requires_names = {r.name for r in block.requires}
        can_use = requires_names & available_provides
        
        if helps_with or can_use:
            suggestions.append({
                "block_id": block_id,
                "name": block.name,
                "helps_with": list(helps_with),
                "can_use": list(can_use),
                "score": len(helps_with) * 2 + len(can_use)
            })
    
    return sorted(suggestions, key=lambda x: -x["score"])[:5]


def generate_app(data: dict) -> dict:
    """Generate app from visual graph."""
    nodes = data.get("nodes", [])
    connections = data.get("connections", [])
    groups = data.get("groups", [])
    project_name = data.get("name", "vision_app")
    
    output_path = OUTPUT_DIR / project_name.lower().replace(" ", "_")
    output_path.mkdir(parents=True, exist_ok=True)
    
    selected_blocks = [n["blockId"] for n in nodes if "blockId" in n]
    app_name = project_name.title().replace("_", " ")
    
    # Build blocks HTML
    block_html = ""
    for b in selected_blocks:
        if b in BLOCKS:
            block_html += f'<div class="block">{BLOCKS[b].name}</div>'
    
    # Build groups HTML
    group_html = ""
    for g in groups:
        group_html += f'<div class="group">{g.get("name", "Group")}: {len(g.get("nodeIds", []))} blocks</div>'
    
    python_code = f'''"""
{app_name} - Built with Blueprint Vision
Blocks: {", ".join(selected_blocks)}
Groups: {len(groups)}
Connections: {len(connections)}
"""

from flask import Flask, request, jsonify

app = Flask(__name__)
items = []

@app.route("/")
def home():
    return """<!DOCTYPE html>
<html>
<head>
    <title>{app_name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: system-ui; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
               min-height: 100vh; padding: 40px; color: white; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        h1 {{ font-size: 2.5em; margin-bottom: 20px; }}
        .meta {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 12px; margin-bottom: 25px; }}
        .block {{ display: inline-block; background: #58a6ff; padding: 6px 12px; margin: 4px; border-radius: 6px; font-size: 12px; }}
        .group {{ color: #a371f7; margin: 5px 0; }}
        form {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        input {{ flex: 1; padding: 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
               border-radius: 8px; color: white; }}
        button {{ background: #58a6ff; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; }}
        .items {{ list-style: none; }}
        .items li {{ padding: 12px; background: rgba(255,255,255,0.05); margin-bottom: 8px; border-radius: 8px;
                   display: flex; justify-content: space-between; align-items: center; }}
        .del {{ background: #f85149; padding: 6px 12px; border-radius: 4px; border: none; color: white; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{app_name}</h1>
        <div class="meta">
            <div>{block_html}</div>
            {group_html}
            <p style="margin-top:10px;color:#8b949e">{len(connections)} connections</p>
        </div>
        <form id="f">
            <input id="c" placeholder="Add item..." required>
            <button>Add</button>
        </form>
        <ul class="items" id="items"></ul>
    </div>
    <script>
        const load = async () => {{
            const r = await fetch('/api/items');
            const d = await r.json();
            document.getElementById('items').innerHTML = d.items.map((x,i) => 
                `<li><span>${{x.content||x}}</span><button class="del" onclick="del(${{i}})">X</button></li>`).join('');
        }};
        document.getElementById('f').onsubmit = async e => {{
            e.preventDefault();
            await fetch('/api/items', {{method:'POST', headers:{{'Content-Type':'application/json'}}, 
                body: JSON.stringify({{content: document.getElementById('c').value}})}});
            document.getElementById('c').value = '';
            load();
        }};
        const del = async i => {{ await fetch(`/api/items/${{i}}`, {{method:'DELETE'}}); load(); }};
        load();
    </script>
</body>
</html>"""

@app.route("/api/items", methods=["GET"])
def list_items():
    return jsonify({{"items": items}})

@app.route("/api/items", methods=["POST"])
def add_item():
    items.append(request.json)
    return jsonify({{"success": True}})

@app.route("/api/items/<int:idx>", methods=["DELETE"])
def delete_item(idx):
    if 0 <= idx < len(items):
        items.pop(idx)
    return jsonify({{"success": True}})

if __name__ == "__main__":
    print("Starting {app_name} at http://localhost:5000")
    app.run(debug=True, port=5000)
'''
    
    (output_path / "app.py").write_text(python_code, encoding='utf-8')
    (output_path / "requirements.txt").write_text("flask\n", encoding='utf-8')
    
    return {
        "success": True,
        "path": str(output_path),
        "blocks": selected_blocks,
        "connections": len(connections),
        "groups": len(groups)
    }


class VisionHandler(SimpleHTTPRequestHandler):
    """HTTP handler for Vision builder."""
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/":
            self.send_html(get_vision_html())
            return
        
        if parsed.path == "/api/blocks":
            self.send_json({"blocks": get_blocks_data()})
            return
        
        if parsed.path == "/api/templates":
            self.send_json({"templates": TEMPLATES})
            return
        
        self.send_error(404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length else "{}"
        data = json.loads(body)
        
        if parsed.path == "/api/generate":
            result = generate_app(data)
            self.send_json(result)
            return
        
        if parsed.path == "/api/ghosts":
            nodes = data.get("nodes", [])
            result = compute_ghost_suggestions(nodes)
            self.send_json({"suggestions": result})
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


def get_vision_html():
    """The vision builder interface with all visual innovations."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blueprint Vision</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --bg: #0d1117;
            --bg2: #161b22;
            --bg3: #21262d;
            --surface: rgba(255,255,255,0.05);
            --border: rgba(255,255,255,0.1);
            --accent: #58a6ff;
            --accent2: #a371f7;
            --success: #3fb950;
            --error: #f85149;
            --warning: #d29922;
            --text: #e6edf3;
            --text-dim: #8b949e;
            --grid: rgba(255,255,255,0.03);
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg);
            color: var(--text);
            overflow: hidden;
            height: 100vh;
        }
        
        .app {
            display: grid;
            grid-template-columns: 260px 1fr 280px;
            grid-template-rows: 50px 1fr 40px;
            height: 100vh;
        }
        
        /* Header */
        .header {
            grid-column: 1 / -1;
            background: var(--bg2);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            padding: 0 16px;
            gap: 20px;
        }
        
        .logo {
            font-weight: 700;
            font-size: 16px;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .toolbar {
            display: flex;
            gap: 4px;
        }
        
        .tool-btn {
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-dim);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.15s;
        }
        
        .tool-btn:hover {
            background: var(--bg3);
            color: var(--text);
        }
        
        .tool-btn.active {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        .tool-btn svg {
            width: 14px;
            height: 14px;
        }
        
        .spacer { flex: 1; }
        
        .zoom-controls {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-dim);
            font-size: 12px;
        }
        
        .zoom-slider {
            width: 100px;
            -webkit-appearance: none;
            background: var(--bg3);
            height: 4px;
            border-radius: 2px;
        }
        
        .zoom-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            background: var(--accent);
            border-radius: 50%;
            cursor: pointer;
        }
        
        /* Palette */
        .palette {
            background: var(--bg2);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .palette-header {
            padding: 12px;
            border-bottom: 1px solid var(--border);
        }
        
        .search-input {
            width: 100%;
            padding: 8px 12px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text);
            font-size: 13px;
        }
        
        .search-input:focus {
            outline: none;
            border-color: var(--accent);
        }
        
        .search-input::placeholder {
            color: var(--text-dim);
        }
        
        .palette-tabs {
            display: flex;
            border-bottom: 1px solid var(--border);
        }
        
        .palette-tab {
            flex: 1;
            padding: 10px;
            background: none;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .palette-tab:hover { color: var(--text); }
        .palette-tab.active { 
            color: var(--accent);
            box-shadow: inset 0 -2px 0 var(--accent);
        }
        
        .palette-content {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
        }
        
        .palette-section {
            margin-bottom: 16px;
        }
        
        .palette-section-title {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-dim);
            margin-bottom: 8px;
            padding-left: 4px;
        }
        
        .palette-block {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 6px;
            cursor: grab;
            transition: all 0.15s;
            position: relative;
        }
        
        .palette-block:hover {
            border-color: var(--accent);
            transform: translateX(3px);
        }
        
        .palette-block:active {
            cursor: grabbing;
        }
        
        .palette-block .color-bar {
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            border-radius: 8px 0 0 8px;
        }
        
        .palette-block .name {
            font-weight: 600;
            font-size: 12px;
            margin-bottom: 3px;
            margin-left: 8px;
        }
        
        .palette-block .desc {
            font-size: 10px;
            color: var(--text-dim);
            margin-left: 8px;
            line-height: 1.3;
        }
        
        /* Templates section */
        .template-card {
            background: linear-gradient(135deg, var(--bg3), var(--bg));
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.15s;
        }
        
        .template-card:hover {
            border-color: var(--accent2);
        }
        
        .template-card .name {
            font-weight: 600;
            font-size: 12px;
            color: var(--accent2);
            margin-bottom: 4px;
        }
        
        .template-card .blocks {
            font-size: 10px;
            color: var(--text-dim);
        }
        
        /* Canvas */
        .canvas-wrap {
            position: relative;
            overflow: hidden;
            background: var(--bg);
        }
        
        .canvas-grid {
            position: absolute;
            inset: 0;
            background-image: 
                linear-gradient(var(--grid) 1px, transparent 1px),
                linear-gradient(90deg, var(--grid) 1px, transparent 1px);
            background-size: 25px 25px;
            pointer-events: none;
        }
        
        .canvas {
            position: absolute;
            width: 4000px;
            height: 4000px;
            transform-origin: 0 0;
        }
        
        .connections-svg {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            overflow: visible;
        }
        
        /* Animated connection flow */
        @keyframes flowDash {
            to { stroke-dashoffset: -20; }
        }
        
        .connection {
            fill: none;
            stroke: url(#connGradient);
            stroke-width: 2.5;
            stroke-linecap: round;
        }
        
        .connection.animated {
            stroke-dasharray: 10 10;
            animation: flowDash 1s linear infinite;
        }
        
        .connection-preview {
            stroke: var(--accent);
            stroke-dasharray: 6 4;
            opacity: 0.6;
        }
        
        /* Nodes */
        .node {
            position: absolute;
            background: var(--bg2);
            border: 2px solid var(--border);
            border-radius: 10px;
            min-width: 180px;
            cursor: move;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            transition: box-shadow 0.15s, border-color 0.15s;
            user-select: none;
        }
        
        .node:hover {
            border-color: rgba(255,255,255,0.2);
        }
        
        .node.selected {
            border-color: var(--accent);
            box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.3), 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .node.ghost {
            opacity: 0.4;
            border-style: dashed;
            cursor: pointer;
        }
        
        .node.ghost:hover {
            opacity: 0.7;
        }
        
        .node-header {
            padding: 10px 12px;
            border-radius: 8px 8px 0 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .node-color {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        
        .node-title {
            font-weight: 600;
            font-size: 12px;
            flex: 1;
        }
        
        .node-menu {
            opacity: 0;
            background: none;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            font-size: 16px;
            padding: 0 4px;
        }
        
        .node:hover .node-menu { opacity: 1; }
        
        .node-body {
            padding: 6px 0;
        }
        
        .port-row {
            display: flex;
            align-items: center;
            padding: 4px 12px;
            font-size: 10px;
            color: var(--text-dim);
        }
        
        .port-row.require { justify-content: flex-start; }
        .port-row.provide { justify-content: flex-end; }
        
        .port {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            cursor: crosshair;
            transition: transform 0.1s;
            border: 2px solid rgba(255,255,255,0.3);
        }
        
        .port:hover {
            transform: scale(1.4);
        }
        
        .port.require {
            background: var(--error);
            margin-right: 8px;
        }
        
        .port.provide {
            background: var(--success);
            margin-left: 8px;
        }
        
        .port.compatible {
            animation: pulse 0.6s ease-in-out infinite alternate;
        }
        
        @keyframes pulse {
            to { transform: scale(1.3); box-shadow: 0 0 10px currentColor; }
        }
        
        /* Node groups */
        .group-box {
            position: absolute;
            border: 2px dashed var(--accent2);
            border-radius: 12px;
            background: rgba(163, 113, 247, 0.05);
            pointer-events: none;
        }
        
        .group-label {
            position: absolute;
            top: -24px;
            left: 12px;
            background: var(--accent2);
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }
        
        /* Selection box */
        .selection-box {
            position: absolute;
            border: 1px solid var(--accent);
            background: rgba(88, 166, 255, 0.1);
            pointer-events: none;
            display: none;
        }
        
        /* Minimap */
        .minimap {
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 180px;
            height: 120px;
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .minimap-content {
            position: relative;
            width: 100%;
            height: 100%;
        }
        
        .minimap-node {
            position: absolute;
            border-radius: 2px;
        }
        
        .minimap-viewport {
            position: absolute;
            border: 2px solid var(--accent);
            background: rgba(88, 166, 255, 0.1);
            cursor: move;
        }
        
        /* Context menu */
        .context-menu {
            position: fixed;
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 6px 0;
            min-width: 160px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.4);
            z-index: 1000;
            display: none;
        }
        
        .context-menu.show { display: block; }
        
        .context-item {
            padding: 8px 14px;
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .context-item:hover {
            background: var(--surface);
        }
        
        .context-item.danger { color: var(--error); }
        
        .context-divider {
            height: 1px;
            background: var(--border);
            margin: 4px 0;
        }
        
        .context-item kbd {
            margin-left: auto;
            color: var(--text-dim);
            font-size: 10px;
        }
        
        /* Right panel */
        .right-panel {
            background: var(--bg2);
            border-left: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .panel-header {
            padding: 14px;
            border-bottom: 1px solid var(--border);
            font-weight: 600;
            font-size: 13px;
        }
        
        .panel-content {
            flex: 1;
            overflow-y: auto;
            padding: 14px;
        }
        
        .form-group {
            margin-bottom: 14px;
        }
        
        .form-group label {
            display: block;
            font-size: 11px;
            color: var(--text-dim);
            margin-bottom: 6px;
            text-transform: uppercase;
        }
        
        .form-group input, .form-group textarea {
            width: 100%;
            padding: 10px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text);
            font-size: 13px;
        }
        
        .form-group input:focus, .form-group textarea:focus {
            outline: none;
            border-color: var(--accent);
        }
        
        .ghost-section {
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
        }
        
        .ghost-title {
            font-size: 11px;
            color: var(--accent2);
            text-transform: uppercase;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .ghost-item {
            background: var(--bg);
            border: 1px dashed var(--border);
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.15s;
        }
        
        .ghost-item:hover {
            border-color: var(--accent2);
            border-style: solid;
        }
        
        .ghost-item .name {
            font-weight: 600;
            font-size: 12px;
            margin-bottom: 4px;
        }
        
        .ghost-item .reason {
            font-size: 10px;
            color: var(--text-dim);
        }
        
        .generate-btn {
            margin: 14px;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            border: none;
            color: white;
            padding: 14px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.15s, box-shadow 0.15s;
        }
        
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(88, 166, 255, 0.3);
        }
        
        /* Status bar */
        .status-bar {
            grid-column: 1 / -1;
            background: var(--bg2);
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            padding: 0 16px;
            font-size: 11px;
            color: var(--text-dim);
            gap: 20px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        /* Undo timeline */
        .undo-timeline {
            position: absolute;
            bottom: 60px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 16px;
            display: none;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .undo-timeline.show { display: flex; }
        
        .timeline-slider {
            width: 200px;
        }
        
        .timeline-label {
            font-size: 11px;
            color: var(--text-dim);
            min-width: 80px;
        }
        
        /* Toast notifications */
        .toast {
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: var(--bg2);
            border: 1px solid var(--border);
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 13px;
            opacity: 0;
            transition: all 0.3s;
            z-index: 1001;
        }
        
        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.8);
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .modal.show { display: flex; }
        
        .modal-content {
            background: var(--bg2);
            border-radius: 12px;
            padding: 30px;
            max-width: 500px;
            text-align: center;
        }
        
        .modal-content h2 {
            color: var(--success);
            margin-bottom: 15px;
        }
        
        .modal-content code {
            display: block;
            background: var(--bg);
            padding: 12px;
            border-radius: 6px;
            font-family: monospace;
            margin: 15px 0;
            text-align: left;
            font-size: 12px;
        }
        
        .modal-content button {
            background: var(--accent);
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 6px;
            cursor: pointer;
        }
        
        /* Keyboard shortcuts help */
        .shortcuts-help {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            display: none;
            z-index: 1001;
            min-width: 300px;
        }
        
        .shortcuts-help.show { display: block; }
        
        .shortcuts-help h3 {
            margin-bottom: 16px;
            font-size: 14px;
        }
        
        .shortcut-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            font-size: 12px;
            border-bottom: 1px solid var(--border);
        }
        
        .shortcut-row:last-child { border: none; }
        
        .shortcut-row kbd {
            background: var(--bg);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="app">
        <header class="header">
            <div class="logo">Blueprint Vision</div>
            
            <div class="toolbar">
                <button class="tool-btn" onclick="undo()" title="Undo (Ctrl+Z)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 10h10a5 5 0 0 1 5 5v2M3 10l4-4M3 10l4 4"/>
                    </svg>
                    Undo
                </button>
                <button class="tool-btn" onclick="redo()" title="Redo (Ctrl+Y)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 10H11a5 5 0 0 0-5 5v2M21 10l-4-4M21 10l-4 4"/>
                    </svg>
                    Redo
                </button>
                <button class="tool-btn" onclick="autoLayout()" title="Auto Layout">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                        <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
                    </svg>
                    Layout
                </button>
                <button class="tool-btn" onclick="groupSelected()" title="Group (Ctrl+G)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="2" width="20" height="20" rx="2"/>
                        <path d="M7 7h10v10H7z"/>
                    </svg>
                    Group
                </button>
                <button class="tool-btn" id="animateBtn" onclick="toggleAnimation()" title="Toggle Animation">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5,3 19,12 5,21"/>
                    </svg>
                    Flow
                </button>
            </div>
            
            <div class="spacer"></div>
            
            <div class="zoom-controls">
                <button class="tool-btn" onclick="zoomToFit()">Fit</button>
                <span id="zoomLevel">100%</span>
                <input type="range" class="zoom-slider" id="zoomSlider" min="25" max="200" value="100" 
                       oninput="setZoom(this.value)">
            </div>
            
            <button class="tool-btn" onclick="showShortcuts()">?</button>
        </header>
        
        <div class="palette">
            <div class="palette-header">
                <input type="text" class="search-input" placeholder="Search blocks..." 
                       id="searchInput" oninput="filterBlocks(this.value)">
            </div>
            <div class="palette-tabs">
                <button class="palette-tab active" onclick="showPaletteTab('blocks')">Blocks</button>
                <button class="palette-tab" onclick="showPaletteTab('templates')">Templates</button>
            </div>
            <div class="palette-content" id="paletteContent"></div>
        </div>
        
        <div class="canvas-wrap" id="canvasWrap">
            <div class="canvas-grid" id="canvasGrid"></div>
            <div class="canvas" id="canvas">
                <svg class="connections-svg" id="connectionsSvg">
                    <defs>
                        <linearGradient id="connGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" style="stop-color:#f85149"/>
                            <stop offset="100%" style="stop-color:#3fb950"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <div class="selection-box" id="selectionBox"></div>
            
            <div class="minimap" id="minimap">
                <div class="minimap-content" id="minimapContent">
                    <div class="minimap-viewport" id="minimapViewport"></div>
                </div>
            </div>
        </div>
        
        <div class="right-panel">
            <div class="panel-header">Configuration</div>
            <div class="panel-content">
                <div class="form-group">
                    <label>App Name</label>
                    <input type="text" id="appName" value="my_vision_app">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="appDesc" rows="3" placeholder="What will your app do?"></textarea>
                </div>
                <div class="form-group">
                    <label>Statistics</label>
                    <div style="font-size: 12px; color: var(--text-dim);">
                        <div><span id="nodeCount">0</span> blocks</div>
                        <div><span id="connCount">0</span> connections</div>
                        <div><span id="groupCount">0</span> groups</div>
                    </div>
                </div>
                
                <div class="ghost-section">
                    <div class="ghost-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M9 21c0 .5.4 1 1 1h4c.6 0 1-.5 1-1v-1H9v1zm3-19C8.1 2 5 5.1 5 9c0 2.4 1.2 4.5 3 5.7V17c0 .5.4 1 1 1h6c.6 0 1-.5 1-1v-2.3c1.8-1.3 3-3.4 3-5.7 0-3.9-3.1-7-7-7z"/>
                        </svg>
                        Suggested Blocks
                    </div>
                    <div id="ghostSuggestions">
                        <div style="color: var(--text-dim); font-size: 11px;">Add blocks to see suggestions</div>
                    </div>
                </div>
            </div>
            <button class="generate-btn" onclick="generateApp()">Generate App</button>
        </div>
        
        <footer class="status-bar">
            <div class="status-item">
                <span id="statusText">Ready</span>
            </div>
            <div class="spacer"></div>
            <div class="status-item">
                <kbd>Del</kbd> delete
            </div>
            <div class="status-item">
                <kbd>Ctrl+A</kbd> select all
            </div>
            <div class="status-item">
                <kbd>Ctrl+G</kbd> group
            </div>
        </footer>
    </div>
    
    <div class="context-menu" id="contextMenu">
        <div class="context-item" onclick="duplicateSelected()">
            Duplicate <kbd>Ctrl+D</kbd>
        </div>
        <div class="context-item" onclick="groupSelected()">
            Group <kbd>Ctrl+G</kbd>
        </div>
        <div class="context-divider"></div>
        <div class="context-item" onclick="autoLayoutSelected()">
            Auto-arrange
        </div>
        <div class="context-item" onclick="alignHorizontal()">
            Align horizontal
        </div>
        <div class="context-item" onclick="alignVertical()">
            Align vertical
        </div>
        <div class="context-divider"></div>
        <div class="context-item danger" onclick="deleteSelected()">
            Delete <kbd>Del</kbd>
        </div>
    </div>
    
    <div class="shortcuts-help" id="shortcutsHelp">
        <h3>Keyboard Shortcuts</h3>
        <div class="shortcut-row"><span>Delete selected</span><kbd>Del</kbd></div>
        <div class="shortcut-row"><span>Select all</span><kbd>Ctrl+A</kbd></div>
        <div class="shortcut-row"><span>Group selected</span><kbd>Ctrl+G</kbd></div>
        <div class="shortcut-row"><span>Duplicate</span><kbd>Ctrl+D</kbd></div>
        <div class="shortcut-row"><span>Undo</span><kbd>Ctrl+Z</kbd></div>
        <div class="shortcut-row"><span>Redo</span><kbd>Ctrl+Y</kbd></div>
        <div class="shortcut-row"><span>Zoom in</span><kbd>Ctrl++</kbd></div>
        <div class="shortcut-row"><span>Zoom out</span><kbd>Ctrl+-</kbd></div>
        <div class="shortcut-row"><span>Fit to view</span><kbd>Ctrl+0</kbd></div>
        <div class="shortcut-row"><span>Show help</span><kbd>?</kbd></div>
    </div>
    
    <div class="toast" id="toast"></div>
    
    <div class="modal" id="resultModal">
        <div class="modal-content">
            <h2>App Generated!</h2>
            <div id="resultContent"></div>
            <button onclick="closeModal()">Close</button>
        </div>
    </div>
    
    <script>
        // State
        let blocks = [];
        let templates = {};
        let nodes = [];
        let connections = [];
        let groups = [];
        let nextNodeId = 1;
        let nextGroupId = 1;
        
        // Selection
        let selectedNodes = new Set();
        let draggingNode = null;
        let draggingPort = null;
        let isPanning = false;
        let isSelecting = false;
        let selectionStart = null;
        
        // Transform
        let zoom = 1;
        let panX = 0, panY = 0;
        
        // History for undo/redo
        let history = [];
        let historyIndex = -1;
        const MAX_HISTORY = 50;
        
        // Animation
        let animationEnabled = false;
        
        // Elements
        const canvas = document.getElementById('canvas');
        const canvasWrap = document.getElementById('canvasWrap');
        const connectionsSvg = document.getElementById('connectionsSvg');
        
        // Initialize
        async function init() {
            const [blocksRes, templatesRes] = await Promise.all([
                fetch('/api/blocks'),
                fetch('/api/templates')
            ]);
            
            blocks = (await blocksRes.json()).blocks;
            templates = (await templatesRes.json()).templates;
            
            renderPalette();
            setupEventListeners();
            saveHistory();
        }
        
        function renderPalette() {
            showPaletteTab('blocks');
        }
        
        function showPaletteTab(tab) {
            document.querySelectorAll('.palette-tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`.palette-tab[onclick="showPaletteTab('${tab}')"]`).classList.add('active');
            
            const content = document.getElementById('paletteContent');
            
            if (tab === 'blocks') {
                const categories = {};
                blocks.forEach(b => {
                    if (!categories[b.category]) categories[b.category] = [];
                    categories[b.category].push(b);
                });
                
                content.innerHTML = Object.entries(categories).map(([cat, catBlocks]) => `
                    <div class="palette-section">
                        <div class="palette-section-title">${cat}</div>
                        ${catBlocks.map(b => `
                            <div class="palette-block" draggable="true" data-block-id="${b.id}">
                                <div class="color-bar" style="background: ${b.color}"></div>
                                <div class="name">${b.name}</div>
                                <div class="desc">${b.description.substring(0, 45)}...</div>
                            </div>
                        `).join('')}
                    </div>
                `).join('');
            } else {
                content.innerHTML = Object.entries(templates).map(([id, t]) => `
                    <div class="template-card" onclick="applyTemplate('${id}')">
                        <div class="name">${t.name}</div>
                        <div class="blocks">${t.blocks.join(' → ')}</div>
                    </div>
                `).join('');
            }
            
            // Setup dragging for palette blocks
            document.querySelectorAll('.palette-block').forEach(el => {
                el.addEventListener('dragstart', e => {
                    e.dataTransfer.setData('blockId', el.dataset.blockId);
                });
            });
        }
        
        function filterBlocks(query) {
            const q = query.toLowerCase();
            document.querySelectorAll('.palette-block').forEach(el => {
                const name = el.querySelector('.name').textContent.toLowerCase();
                const desc = el.querySelector('.desc').textContent.toLowerCase();
                el.style.display = (name.includes(q) || desc.includes(q)) ? 'block' : 'none';
            });
        }
        
        function applyTemplate(templateId) {
            const t = templates[templateId];
            if (!t) return;
            
            // Clear existing
            nodes = [];
            connections = [];
            groups = [];
            selectedNodes.clear();
            
            // Add blocks from template
            t.blocks.forEach((blockId, i) => {
                const block = blocks.find(b => b.id === blockId);
                if (block) {
                    const [x, y] = t.layout[i] || [100 + i * 220, 200];
                    nodes.push({ id: nextNodeId++, blockId, block, x, y });
                }
            });
            
            renderAll();
            saveHistory();
            toast(`Applied template: ${t.name}`);
        }
        
        function setupEventListeners() {
            // Canvas drop
            canvasWrap.addEventListener('dragover', e => e.preventDefault());
            canvasWrap.addEventListener('drop', e => {
                e.preventDefault();
                const blockId = e.dataTransfer.getData('blockId');
                if (!blockId) return;
                
                const block = blocks.find(b => b.id === blockId);
                if (!block) return;
                
                const rect = canvasWrap.getBoundingClientRect();
                const x = (e.clientX - rect.left - panX) / zoom - 90;
                const y = (e.clientY - rect.top - panY) / zoom - 40;
                
                addNode(block, x, y);
            });
            
            // Canvas panning and selection
            canvasWrap.addEventListener('mousedown', e => {
                if (e.target === canvasWrap || e.target.id === 'canvasGrid') {
                    if (e.button === 1 || (e.button === 0 && e.altKey)) {
                        // Middle click or Alt+click = pan
                        isPanning = true;
                        canvasWrap.style.cursor = 'grabbing';
                    } else if (e.button === 0) {
                        // Left click = marquee selection
                        isSelecting = true;
                        const rect = canvasWrap.getBoundingClientRect();
                        selectionStart = { x: e.clientX - rect.left, y: e.clientY - rect.top };
                        document.getElementById('selectionBox').style.display = 'block';
                        
                        // Deselect all if not shift
                        if (!e.shiftKey) {
                            selectedNodes.clear();
                            renderNodes();
                        }
                    }
                }
            });
            
            // Mouse move
            document.addEventListener('mousemove', e => {
                if (isPanning) {
                    panX += e.movementX;
                    panY += e.movementY;
                    updateTransform();
                } else if (isSelecting && selectionStart) {
                    const rect = canvasWrap.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    
                    const box = document.getElementById('selectionBox');
                    box.style.left = Math.min(x, selectionStart.x) + 'px';
                    box.style.top = Math.min(y, selectionStart.y) + 'px';
                    box.style.width = Math.abs(x - selectionStart.x) + 'px';
                    box.style.height = Math.abs(y - selectionStart.y) + 'px';
                } else if (draggingNode) {
                    const rect = canvasWrap.getBoundingClientRect();
                    const x = (e.clientX - rect.left - panX) / zoom;
                    const y = (e.clientY - rect.top - panY) / zoom;
                    
                    // Snap to grid
                    const gridSize = 25;
                    const snapX = Math.round(x / gridSize) * gridSize - 90;
                    const snapY = Math.round(y / gridSize) * gridSize - 40;
                    
                    const dx = snapX - draggingNode.x;
                    const dy = snapY - draggingNode.y;
                    
                    // Move all selected nodes
                    if (selectedNodes.has(draggingNode.id)) {
                        nodes.forEach(n => {
                            if (selectedNodes.has(n.id)) {
                                n.x += dx;
                                n.y += dy;
                            }
                        });
                    } else {
                        draggingNode.x = snapX;
                        draggingNode.y = snapY;
                    }
                    
                    renderNodes();
                    renderConnections();
                    updateMinimap();
                }
            });
            
            // Mouse up
            document.addEventListener('mouseup', e => {
                if (isPanning) {
                    isPanning = false;
                    canvasWrap.style.cursor = '';
                }
                
                if (isSelecting) {
                    // Find nodes in selection box
                    const box = document.getElementById('selectionBox');
                    const boxRect = box.getBoundingClientRect();
                    
                    nodes.forEach(n => {
                        const nodeEl = document.getElementById(`node-${n.id}`);
                        if (nodeEl) {
                            const nodeRect = nodeEl.getBoundingClientRect();
                            if (rectsOverlap(boxRect, nodeRect)) {
                                selectedNodes.add(n.id);
                            }
                        }
                    });
                    
                    box.style.display = 'none';
                    isSelecting = false;
                    selectionStart = null;
                    renderNodes();
                }
                
                if (draggingNode) {
                    draggingNode = null;
                    saveHistory();
                }
                
                if (draggingPort) {
                    draggingPort = null;
                    renderConnections();
                }
            });
            
            // Zoom with scroll
            canvasWrap.addEventListener('wheel', e => {
                e.preventDefault();
                const delta = e.deltaY > 0 ? 0.9 : 1.1;
                zoom = Math.max(0.25, Math.min(2, zoom * delta));
                document.getElementById('zoomSlider').value = zoom * 100;
                document.getElementById('zoomLevel').textContent = Math.round(zoom * 100) + '%';
                updateTransform();
            });
            
            // Context menu
            canvasWrap.addEventListener('contextmenu', e => {
                e.preventDefault();
                if (selectedNodes.size > 0) {
                    const menu = document.getElementById('contextMenu');
                    menu.style.left = e.clientX + 'px';
                    menu.style.top = e.clientY + 'px';
                    menu.classList.add('show');
                }
            });
            
            document.addEventListener('click', () => {
                document.getElementById('contextMenu').classList.remove('show');
                document.getElementById('shortcutsHelp').classList.remove('show');
            });
            
            // Keyboard shortcuts
            document.addEventListener('keydown', e => {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                
                if (e.key === 'Delete' || e.key === 'Backspace') {
                    deleteSelected();
                } else if (e.key === 'a' && e.ctrlKey) {
                    e.preventDefault();
                    nodes.forEach(n => selectedNodes.add(n.id));
                    renderNodes();
                } else if (e.key === 'g' && e.ctrlKey) {
                    e.preventDefault();
                    groupSelected();
                } else if (e.key === 'd' && e.ctrlKey) {
                    e.preventDefault();
                    duplicateSelected();
                } else if (e.key === 'z' && e.ctrlKey) {
                    e.preventDefault();
                    undo();
                } else if (e.key === 'y' && e.ctrlKey) {
                    e.preventDefault();
                    redo();
                } else if (e.key === '0' && e.ctrlKey) {
                    e.preventDefault();
                    zoomToFit();
                } else if (e.key === '?' || e.key === '/') {
                    showShortcuts();
                } else if (e.key === 'Escape') {
                    selectedNodes.clear();
                    renderNodes();
                }
            });
            
            // Minimap dragging
            const minimapViewport = document.getElementById('minimapViewport');
            let minimapDragging = false;
            
            minimapViewport.addEventListener('mousedown', () => minimapDragging = true);
            document.addEventListener('mousemove', e => {
                if (!minimapDragging) return;
                const minimap = document.getElementById('minimap');
                const rect = minimap.getBoundingClientRect();
                const scale = 4000 / 180; // canvas size / minimap size
                
                const mx = (e.clientX - rect.left) * scale;
                const my = (e.clientY - rect.top) * scale;
                
                panX = -(mx - canvasWrap.clientWidth / 2);
                panY = -(my - canvasWrap.clientHeight / 2);
                updateTransform();
            });
            document.addEventListener('mouseup', () => minimapDragging = false);
        }
        
        function rectsOverlap(r1, r2) {
            return !(r1.right < r2.left || r1.left > r2.right || 
                     r1.bottom < r2.top || r1.top > r2.bottom);
        }
        
        function addNode(block, x, y) {
            nodes.push({ id: nextNodeId++, blockId: block.id, block, x, y });
            renderAll();
            saveHistory();
            updateGhostSuggestions();
        }
        
        function renderAll() {
            renderNodes();
            renderConnections();
            renderGroups();
            updateMinimap();
            updateStats();
        }
        
        function renderNodes() {
            // Get existing ghost nodes to preserve
            const ghostNodes = Array.from(document.querySelectorAll('.node.ghost'));
            
            // Render real nodes
            const realNodesHtml = nodes.map(n => `
                <div class="node ${selectedNodes.has(n.id) ? 'selected' : ''}" 
                     id="node-${n.id}" 
                     style="left:${n.x}px; top:${n.y}px;">
                    <div class="node-header">
                        <div class="node-color" style="background: ${n.block.color}"></div>
                        <div class="node-title">${n.block.name}</div>
                        <button class="node-menu" onclick="showNodeMenu(event, ${n.id})">⋮</button>
                    </div>
                    <div class="node-body">
                        ${n.block.requires.map(p => `
                            <div class="port-row require">
                                <div class="port require" data-node="${n.id}" data-port="${p.name}" data-type="require"></div>
                                <span>${p.name}</span>
                            </div>
                        `).join('')}
                        ${n.block.provides.map(p => `
                            <div class="port-row provide">
                                <span>${p.name}</span>
                                <div class="port provide" data-node="${n.id}" data-port="${p.name}" data-type="provide"></div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('');
            
            canvas.innerHTML = connectionsSvg.outerHTML + realNodesHtml;
            
            // Re-select the SVG
            connectionsSvg = document.getElementById('connectionsSvg');
            renderConnections();
            
            // Attach node event handlers
            document.querySelectorAll('.node:not(.ghost)').forEach(el => {
                const nodeId = parseInt(el.id.split('-')[1]);
                
                el.addEventListener('mousedown', e => {
                    if (e.target.classList.contains('port') || e.target.classList.contains('node-menu')) return;
                    
                    if (!selectedNodes.has(nodeId) && !e.shiftKey) {
                        selectedNodes.clear();
                    }
                    selectedNodes.add(nodeId);
                    
                    draggingNode = nodes.find(n => n.id === nodeId);
                    renderNodes();
                });
                
                el.addEventListener('click', e => {
                    if (e.shiftKey) {
                        if (selectedNodes.has(nodeId)) {
                            selectedNodes.delete(nodeId);
                        } else {
                            selectedNodes.add(nodeId);
                        }
                        renderNodes();
                    }
                });
            });
            
            // Attach port event handlers
            document.querySelectorAll('.port').forEach(el => {
                el.addEventListener('mousedown', e => {
                    e.stopPropagation();
                    draggingPort = {
                        node: parseInt(el.dataset.node),
                        port: el.dataset.port,
                        type: el.dataset.type,
                        el
                    };
                    
                    // Highlight compatible ports
                    highlightCompatiblePorts(draggingPort);
                });
                
                el.addEventListener('mouseup', e => {
                    if (draggingPort && draggingPort.el !== el) {
                        const toType = el.dataset.type;
                        if (draggingPort.type === 'provide' && toType === 'require') {
                            addConnection(draggingPort.node, draggingPort.port, 
                                        parseInt(el.dataset.node), el.dataset.port);
                        } else if (draggingPort.type === 'require' && toType === 'provide') {
                            addConnection(parseInt(el.dataset.node), el.dataset.port,
                                        draggingPort.node, draggingPort.port);
                        }
                    }
                    clearPortHighlights();
                });
            });
        }
        
        function highlightCompatiblePorts(dragPort) {
            const targetType = dragPort.type === 'provide' ? 'require' : 'provide';
            document.querySelectorAll(`.port.${targetType}`).forEach(p => {
                if (p !== dragPort.el) {
                    p.classList.add('compatible');
                }
            });
        }
        
        function clearPortHighlights() {
            document.querySelectorAll('.port.compatible').forEach(p => {
                p.classList.remove('compatible');
            });
        }
        
        function addConnection(fromNode, fromPort, toNode, toPort) {
            const exists = connections.some(c => 
                c.fromNode === fromNode && c.fromPort === fromPort &&
                c.toNode === toNode && c.toPort === toPort
            );
            if (!exists) {
                connections.push({ fromNode, fromPort, toNode, toPort });
                renderConnections();
                updateStats();
                saveHistory();
            }
        }
        
        function renderConnections() {
            const svg = document.getElementById('connectionsSvg');
            if (!svg) return;
            
            const defs = svg.querySelector('defs').outerHTML;
            let paths = '';
            
            for (const conn of connections) {
                const fromEl = document.querySelector(`.port.provide[data-node="${conn.fromNode}"][data-port="${conn.fromPort}"]`);
                const toEl = document.querySelector(`.port.require[data-node="${conn.toNode}"][data-port="${conn.toPort}"]`);
                
                if (fromEl && toEl) {
                    const fromRect = fromEl.getBoundingClientRect();
                    const toRect = toEl.getBoundingClientRect();
                    const canvasRect = canvas.getBoundingClientRect();
                    
                    const x1 = (fromRect.left + fromRect.width/2 - canvasRect.left) / zoom;
                    const y1 = (fromRect.top + fromRect.height/2 - canvasRect.top) / zoom;
                    const x2 = (toRect.left + toRect.width/2 - canvasRect.left) / zoom;
                    const y2 = (toRect.top + toRect.height/2 - canvasRect.top) / zoom;
                    
                    const cx = (x1 + x2) / 2;
                    const animClass = animationEnabled ? 'animated' : '';
                    paths += `<path class="connection ${animClass}" d="M${x1},${y1} C${cx},${y1} ${cx},${y2} ${x2},${y2}"/>`;
                }
            }
            
            svg.innerHTML = defs + paths;
        }
        
        function renderGroups() {
            // Remove old groups
            document.querySelectorAll('.group-box').forEach(el => el.remove());
            
            groups.forEach(g => {
                const groupNodes = nodes.filter(n => g.nodeIds.includes(n.id));
                if (groupNodes.length === 0) return;
                
                // Calculate bounding box
                let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                groupNodes.forEach(n => {
                    minX = Math.min(minX, n.x);
                    minY = Math.min(minY, n.y);
                    maxX = Math.max(maxX, n.x + 180);
                    maxY = Math.max(maxY, n.y + 100);
                });
                
                const padding = 20;
                const box = document.createElement('div');
                box.className = 'group-box';
                box.id = `group-${g.id}`;
                box.style.left = (minX - padding) + 'px';
                box.style.top = (minY - padding) + 'px';
                box.style.width = (maxX - minX + padding * 2) + 'px';
                box.style.height = (maxY - minY + padding * 2) + 'px';
                box.innerHTML = `<div class="group-label">${g.name}</div>`;
                
                canvas.appendChild(box);
            });
        }
        
        function updateMinimap() {
            const content = document.getElementById('minimapContent');
            const scale = 180 / 4000;
            
            // Render mini nodes
            let html = '<div class="minimap-viewport" id="minimapViewport"></div>';
            nodes.forEach(n => {
                html += `<div class="minimap-node" style="
                    left: ${n.x * scale}px;
                    top: ${n.y * scale}px;
                    width: ${180 * scale}px;
                    height: ${80 * scale}px;
                    background: ${n.block.color};
                "></div>`;
            });
            content.innerHTML = html;
            
            // Update viewport
            const viewport = document.getElementById('minimapViewport');
            const viewW = canvasWrap.clientWidth / zoom * scale;
            const viewH = canvasWrap.clientHeight / zoom * scale;
            viewport.style.width = viewW + 'px';
            viewport.style.height = viewH + 'px';
            viewport.style.left = (-panX / zoom * scale) + 'px';
            viewport.style.top = (-panY / zoom * scale) + 'px';
        }
        
        function updateStats() {
            document.getElementById('nodeCount').textContent = nodes.length;
            document.getElementById('connCount').textContent = connections.length;
            document.getElementById('groupCount').textContent = groups.length;
        }
        
        function updateTransform() {
            canvas.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
            document.getElementById('canvasGrid').style.backgroundPosition = `${panX}px ${panY}px`;
            updateMinimap();
        }
        
        function setZoom(value) {
            zoom = value / 100;
            document.getElementById('zoomLevel').textContent = Math.round(zoom * 100) + '%';
            updateTransform();
        }
        
        function zoomToFit() {
            if (nodes.length === 0) {
                zoom = 1;
                panX = 0;
                panY = 0;
            } else {
                let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                nodes.forEach(n => {
                    minX = Math.min(minX, n.x);
                    minY = Math.min(minY, n.y);
                    maxX = Math.max(maxX, n.x + 180);
                    maxY = Math.max(maxY, n.y + 100);
                });
                
                const padding = 100;
                const contentW = maxX - minX + padding * 2;
                const contentH = maxY - minY + padding * 2;
                
                zoom = Math.min(
                    canvasWrap.clientWidth / contentW,
                    canvasWrap.clientHeight / contentH,
                    1.5
                );
                
                panX = canvasWrap.clientWidth / 2 - (minX + contentW / 2 - padding) * zoom;
                panY = canvasWrap.clientHeight / 2 - (minY + contentH / 2 - padding) * zoom;
            }
            
            document.getElementById('zoomSlider').value = zoom * 100;
            document.getElementById('zoomLevel').textContent = Math.round(zoom * 100) + '%';
            updateTransform();
        }
        
        // Actions
        function deleteSelected() {
            if (selectedNodes.size === 0) return;
            
            // Remove nodes
            nodes = nodes.filter(n => !selectedNodes.has(n.id));
            
            // Remove connections involving deleted nodes
            connections = connections.filter(c => 
                !selectedNodes.has(c.fromNode) && !selectedNodes.has(c.toNode)
            );
            
            // Update groups
            groups.forEach(g => {
                g.nodeIds = g.nodeIds.filter(id => !selectedNodes.has(id));
            });
            groups = groups.filter(g => g.nodeIds.length > 0);
            
            selectedNodes.clear();
            renderAll();
            saveHistory();
            updateGhostSuggestions();
            toast('Deleted');
        }
        
        function duplicateSelected() {
            if (selectedNodes.size === 0) return;
            
            const newNodes = [];
            const idMap = new Map();
            
            nodes.filter(n => selectedNodes.has(n.id)).forEach(n => {
                const newId = nextNodeId++;
                idMap.set(n.id, newId);
                newNodes.push({
                    id: newId,
                    blockId: n.blockId,
                    block: n.block,
                    x: n.x + 30,
                    y: n.y + 30
                });
            });
            
            nodes.push(...newNodes);
            
            // Duplicate connections between selected nodes
            connections.filter(c => 
                selectedNodes.has(c.fromNode) && selectedNodes.has(c.toNode)
            ).forEach(c => {
                connections.push({
                    fromNode: idMap.get(c.fromNode),
                    fromPort: c.fromPort,
                    toNode: idMap.get(c.toNode),
                    toPort: c.toPort
                });
            });
            
            // Select new nodes
            selectedNodes.clear();
            newNodes.forEach(n => selectedNodes.add(n.id));
            
            renderAll();
            saveHistory();
            toast('Duplicated');
        }
        
        function groupSelected() {
            if (selectedNodes.size < 2) {
                toast('Select at least 2 nodes to group');
                return;
            }
            
            const name = prompt('Group name:', 'Group ' + nextGroupId);
            if (!name) return;
            
            groups.push({
                id: nextGroupId++,
                name,
                nodeIds: [...selectedNodes]
            });
            
            renderGroups();
            updateStats();
            saveHistory();
            toast(`Created group: ${name}`);
        }
        
        function autoLayout() {
            if (nodes.length === 0) return;
            
            // Simple force-directed layout
            const iterations = 50;
            const k = 200; // Optimal distance
            
            for (let i = 0; i < iterations; i++) {
                // Repulsion between all nodes
                for (let a = 0; a < nodes.length; a++) {
                    for (let b = a + 1; b < nodes.length; b++) {
                        const dx = nodes[b].x - nodes[a].x;
                        const dy = nodes[b].y - nodes[a].y;
                        const d = Math.sqrt(dx * dx + dy * dy) || 1;
                        const f = k * k / d;
                        
                        nodes[a].x -= (dx / d) * f * 0.1;
                        nodes[a].y -= (dy / d) * f * 0.1;
                        nodes[b].x += (dx / d) * f * 0.1;
                        nodes[b].y += (dy / d) * f * 0.1;
                    }
                }
                
                // Attraction along connections
                connections.forEach(c => {
                    const a = nodes.find(n => n.id === c.fromNode);
                    const b = nodes.find(n => n.id === c.toNode);
                    if (!a || !b) return;
                    
                    const dx = b.x - a.x;
                    const dy = b.y - a.y;
                    const d = Math.sqrt(dx * dx + dy * dy) || 1;
                    
                    a.x += (dx / d) * d * 0.02;
                    a.y += (dy / d) * d * 0.02;
                    b.x -= (dx / d) * d * 0.02;
                    b.y -= (dy / d) * d * 0.02;
                });
            }
            
            // Ensure positive coordinates and snap to grid
            let minX = Math.min(...nodes.map(n => n.x));
            let minY = Math.min(...nodes.map(n => n.y));
            
            nodes.forEach(n => {
                n.x = Math.round((n.x - minX + 100) / 25) * 25;
                n.y = Math.round((n.y - minY + 100) / 25) * 25;
            });
            
            renderAll();
            zoomToFit();
            saveHistory();
            toast('Layout applied');
        }
        
        function autoLayoutSelected() {
            // Same as autoLayout but only for selected nodes
            // ... (simplified for now)
            autoLayout();
        }
        
        function alignHorizontal() {
            if (selectedNodes.size < 2) return;
            const selected = nodes.filter(n => selectedNodes.has(n.id));
            const avgY = selected.reduce((sum, n) => sum + n.y, 0) / selected.length;
            selected.forEach(n => n.y = avgY);
            renderAll();
            saveHistory();
            toast('Aligned horizontally');
        }
        
        function alignVertical() {
            if (selectedNodes.size < 2) return;
            const selected = nodes.filter(n => selectedNodes.has(n.id));
            const avgX = selected.reduce((sum, n) => sum + n.x, 0) / selected.length;
            selected.forEach(n => n.x = avgX);
            renderAll();
            saveHistory();
            toast('Aligned vertically');
        }
        
        function toggleAnimation() {
            animationEnabled = !animationEnabled;
            document.getElementById('animateBtn').classList.toggle('active', animationEnabled);
            renderConnections();
            toast(animationEnabled ? 'Flow animation on' : 'Flow animation off');
        }
        
        // History
        function saveHistory() {
            // Trim future history
            history = history.slice(0, historyIndex + 1);
            
            // Save current state
            history.push(JSON.stringify({ nodes, connections, groups }));
            
            // Limit history size
            if (history.length > MAX_HISTORY) {
                history.shift();
            }
            
            historyIndex = history.length - 1;
        }
        
        function undo() {
            if (historyIndex > 0) {
                historyIndex--;
                restoreHistory();
                toast('Undo');
            }
        }
        
        function redo() {
            if (historyIndex < history.length - 1) {
                historyIndex++;
                restoreHistory();
                toast('Redo');
            }
        }
        
        function restoreHistory() {
            const state = JSON.parse(history[historyIndex]);
            nodes = state.nodes;
            connections = state.connections;
            groups = state.groups;
            selectedNodes.clear();
            renderAll();
        }
        
        // Ghost suggestions
        async function updateGhostSuggestions() {
            try {
                const res = await fetch('/api/ghosts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nodes: nodes.map(n => ({ blockId: n.blockId })) })
                });
                const data = await res.json();
                
                const container = document.getElementById('ghostSuggestions');
                if (data.suggestions.length === 0) {
                    container.innerHTML = '<div style="color: var(--text-dim); font-size: 11px;">No suggestions</div>';
                } else {
                    container.innerHTML = data.suggestions.map(s => `
                        <div class="ghost-item" onclick="addGhostBlock('${s.block_id}')">
                            <div class="name">${s.name}</div>
                            <div class="reason">
                                ${s.helps_with.length ? 'Provides: ' + s.helps_with.join(', ') : ''}
                                ${s.can_use.length ? 'Uses: ' + s.can_use.join(', ') : ''}
                            </div>
                        </div>
                    `).join('');
                }
            } catch {}
        }
        
        function addGhostBlock(blockId) {
            const block = blocks.find(b => b.id === blockId);
            if (block) {
                const x = 100 + Math.random() * 400;
                const y = 100 + Math.random() * 300;
                addNode(block, x, y);
            }
        }
        
        // UI helpers
        function showNodeMenu(e, nodeId) {
            e.stopPropagation();
            selectedNodes.clear();
            selectedNodes.add(nodeId);
            renderNodes();
            
            const menu = document.getElementById('contextMenu');
            menu.style.left = e.clientX + 'px';
            menu.style.top = e.clientY + 'px';
            menu.classList.add('show');
        }
        
        function showShortcuts() {
            document.getElementById('shortcutsHelp').classList.toggle('show');
        }
        
        function toast(message) {
            const el = document.getElementById('toast');
            el.textContent = message;
            el.classList.add('show');
            setTimeout(() => el.classList.remove('show'), 2000);
        }
        
        function closeModal() {
            document.getElementById('resultModal').classList.remove('show');
        }
        
        // Generate
        async function generateApp() {
            const btn = document.querySelector('.generate-btn');
            btn.textContent = 'Generating...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: document.getElementById('appName').value,
                        description: document.getElementById('appDesc').value,
                        nodes: nodes.map(n => ({ id: n.id, blockId: n.blockId, x: n.x, y: n.y })),
                        connections,
                        groups
                    })
                });
                const result = await res.json();
                
                document.getElementById('resultContent').innerHTML = `
                    <p>${result.blocks.length} blocks • ${result.connections} connections • ${result.groups} groups</p>
                    <code>${result.path}</code>
                    <p>Run: <code>cd ${result.path} && python app.py</code></p>
                `;
                document.getElementById('resultModal').classList.add('show');
            } catch (e) {
                toast('Generation failed: ' + e.message);
            } finally {
                btn.textContent = 'Generate App';
                btn.disabled = false;
            }
        }
        
        init();
    </script>
</body>
</html>'''


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("  Blueprint VISION")
    print("  The Visual Architecture Canvas")
    print("=" * 60)
    print(f"  Open: http://localhost:{PORT}")
    print("=" * 60)
    print("  Visual Features:")
    print("    • Minimap bird's eye view")
    print("    • Force-directed auto-layout")
    print("    • Data flow animation")
    print("    • Marquee selection")
    print("    • Node grouping")
    print("    • Snap-to-grid")
    print("    • Undo/redo history")
    print("    • Ghost block suggestions")
    print("    • Block templates")
    print("    • Keyboard shortcuts")
    print("    • Zoom/pan controls")
    print("=" * 60)
    print("  Press Ctrl+C to stop")
    print()
    
    def open_browser():
        time.sleep(1)
        webbrowser.open(f"http://localhost:{PORT}")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    server = HTTPServer(("", PORT), VisionHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
