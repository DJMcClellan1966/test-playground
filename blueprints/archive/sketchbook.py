"""
Blueprint Sketchbook - Visual Node-Based App Builder

A canvas where you:
- Drag blocks as visual nodes
- See require/provide ports on each node
- Draw connections between compatible ports
- Preview the app live as you build

Run: python sketchbook.py
Opens: http://localhost:5000
"""

import os
import sys
import json
import webbrowser
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))
from blocks import BLOCKS

PORT = 5000
OUTPUT_DIR = Path(__file__).parent / "output"


def get_blocks_for_canvas():
    """Get blocks formatted for the visual canvas."""
    blocks = []
    for block_id, block in BLOCKS.items():
        blocks.append({
            "id": block_id,
            "name": block.name,
            "description": block.description,
            "requires": [{"name": p.name, "type": p.type, "desc": p.description} for p in block.requires],
            "provides": [{"name": p.name, "type": p.type, "desc": p.description} for p in block.provides],
        })
    return blocks


def generate_app_from_graph(graph_data: dict) -> dict:
    """Generate app from the visual graph."""
    nodes = graph_data.get("nodes", [])
    connections = graph_data.get("connections", [])
    project_name = graph_data.get("name", "my_app")
    description = graph_data.get("description", "")
    
    output_path = OUTPUT_DIR / project_name.lower().replace(" ", "_")
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Extract block IDs from nodes
    selected_blocks = [n["blockId"] for n in nodes if "blockId" in n]
    
    app_name = project_name.title().replace("_", " ")
    entity = project_name.lower().split()[0] if project_name else "item"
    secret_key = project_name.lower().replace(" ", "-")
    
    # Generate connection info
    conn_info = [f"{c.get('fromNode', '?')}:{c.get('fromPort', '?')} -> {c.get('toNode', '?')}:{c.get('toPort', '?')}" for c in connections]
    
    # Build block descriptions for explain page
    block_html = ""
    for b in selected_blocks:
        desc = BLOCKS[b].description if b in BLOCKS else "Block"
        block_html += f'<div class="block"><strong>{b}</strong> - {desc}</div>'
    if not block_html:
        block_html = "<p>No blocks selected</p>"
    
    conn_html = ""
    for c in conn_info:
        conn_html += f'<div class="conn">{c}</div>'
    if not conn_html:
        conn_html = "<p>No connections</p>"
    
    # Generate simple in-memory app
    app_code = f'''"""
{app_name} - Built with Blueprint Sketchbook

Description: {description}
Blocks: {", ".join(selected_blocks) if selected_blocks else "minimal"}
Connections: {len(connections)} port connections
"""

from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = "blueprint-{secret_key}-secret"

# In-memory storage
items = []

@app.route("/")
def home():
    return """<!DOCTYPE html>
<html>
<head>
    <title>{app_name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: system-ui, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               min-height: 100vh; padding: 40px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; 
                     border-radius: 16px; padding: 30px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        .meta {{ background: #f0f4ff; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; color: #666; }}
        form {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        input {{ flex: 1; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }}
        input:focus {{ outline: none; border-color: #667eea; }}
        button {{ background: #667eea; color: white; border: none; padding: 12px 24px;
                 border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; }}
        button:hover {{ background: #5a6fd6; }}
        .items {{ list-style: none; }}
        .items li {{ display: flex; align-items: center; padding: 12px; 
                    background: #f8f9fa; margin-bottom: 8px; border-radius: 8px; }}
        .items li span {{ flex: 1; }}
        .del {{ background: #e74c3c; padding: 6px 12px; font-size: 12px; }}
        footer {{ margin-top: 30px; text-align: center; }}
        footer a {{ color: #667eea; text-decoration: none; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{app_name}</h1>
        <div class="meta">Built with Blueprint Sketchbook | {len(selected_blocks)} blocks | {len(connections)} connections</div>
        <form id="f"><input id="c" placeholder="Add item..." required><button>Add</button></form>
        <ul class="items" id="items"></ul>
        <footer><a href="/explain">View architecture</a></footer>
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
    data = request.json or {{}}
    items.append({{"content": data.get("content", ""), "done": False}})
    return jsonify({{"success": True}})

@app.route("/api/items/<int:idx>", methods=["DELETE"])
def delete_item(idx):
    if 0 <= idx < len(items):
        items.pop(idx)
    return jsonify({{"success": True}})

@app.route("/explain")
def explain():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Architecture - {app_name}</title>
    <style>
        body {{ font-family: system-ui, sans-serif; background: #f5f5f5; padding: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 16px; padding: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #667eea; margin-top: 30px; }}
        .block {{ background: #f0f4ff; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }}
        .conn {{ background: #e8f5e9; padding: 10px; margin: 5px 0; border-radius: 4px; font-family: monospace; }}
        .back {{ display: inline-block; margin-top: 20px; color: #667eea; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>How {app_name} Works</h1>
        <p>This app was visually designed in the Blueprint Sketchbook.</p>
        
        <h2>Blocks ({len(selected_blocks)})</h2>
        {block_html}
        
        <h2>Port Connections ({len(connections)})</h2>
        {conn_html}
        
        <h2>How It Works</h2>
        <p>Each block declares <strong>requires</strong> (inputs) and <strong>provides</strong> (outputs). 
           The visual sketchbook lets you wire these together, ensuring compatibility.</p>
        
        <a href="/" class="back">Back to app</a>
    </div>
</body>
</html>"""

if __name__ == "__main__":
    print("Starting {app_name} on http://localhost:5000")
    app.run(debug=True, port=5000)
'''
    
    # Write files
    (output_path / "app.py").write_text(app_code, encoding='utf-8')
    (output_path / "requirements.txt").write_text("flask\\n", encoding='utf-8')
    
    return {
        "success": True,
        "path": str(output_path),
        "blocks": selected_blocks,
        "connections": len(connections),
        "run_command": f"cd {output_path} && python app.py"
    }


class SketchbookHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the sketchbook."""
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(get_sketchbook_html().encode())
            return
        
        if parsed.path == "/api/blocks":
            self.send_json({"blocks": get_blocks_for_canvas()})
            return
        
        self.send_error(404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body) if body else {}
            result = generate_app_from_graph(data)
            self.send_json(result)
            return
        
        self.send_error(404)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass


def get_sketchbook_html():
    """The visual sketchbook canvas."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blueprint Sketchbook</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --bg: #1a1a2e;
            --canvas: #0d1117;
            --node: #21262d;
            --node-border: #30363d;
            --port-require: #f85149;
            --port-provide: #3fb950;
            --accent: #58a6ff;
            --text: #c9d1d9;
            --text-dim: #8b949e;
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
            grid-template-columns: 260px 1fr 300px;
            height: 100vh;
        }
        
        /* Palette */
        .palette {
            background: var(--node);
            border-right: 1px solid var(--node-border);
            padding: 15px;
            overflow-y: auto;
        }
        
        .palette h2 {
            font-size: 14px;
            color: var(--text-dim);
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .palette-block {
            background: var(--canvas);
            border: 1px solid var(--node-border);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            cursor: grab;
            transition: all 0.2s;
        }
        
        .palette-block:hover {
            border-color: var(--accent);
            transform: translateX(3px);
        }
        
        .palette-block .name {
            font-weight: 600;
            font-size: 13px;
            margin-bottom: 4px;
        }
        
        .palette-block .desc {
            font-size: 11px;
            color: var(--text-dim);
        }
        
        .palette-block .ports-preview {
            display: flex;
            gap: 8px;
            margin-top: 8px;
        }
        
        .port-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        
        .port-dot.require { background: var(--port-require); }
        .port-dot.provide { background: var(--port-provide); }
        
        /* Canvas */
        .canvas-container {
            position: relative;
            background: var(--canvas);
            background-image: 
                radial-gradient(circle, #30363d 1px, transparent 1px);
            background-size: 20px 20px;
            overflow: hidden;
        }
        
        .canvas {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
        
        /* Nodes */
        .node {
            position: absolute;
            background: var(--node);
            border: 2px solid var(--node-border);
            border-radius: 12px;
            min-width: 180px;
            cursor: move;
            user-select: none;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .node.selected {
            border-color: var(--accent);
            box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.3);
        }
        
        .node-header {
            background: rgba(0,0,0,0.3);
            padding: 10px 12px;
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .node-title {
            font-weight: 600;
            font-size: 13px;
        }
        
        .node-delete {
            background: none;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            font-size: 16px;
            padding: 0 4px;
        }
        
        .node-delete:hover {
            color: var(--port-require);
        }
        
        .node-body {
            padding: 10px 0;
        }
        
        .port-row {
            display: flex;
            align-items: center;
            padding: 4px 12px;
            font-size: 11px;
        }
        
        .port-row.require {
            justify-content: flex-start;
        }
        
        .port-row.provide {
            justify-content: flex-end;
        }
        
        .port {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            cursor: crosshair;
            transition: transform 0.1s;
        }
        
        .port:hover {
            transform: scale(1.3);
        }
        
        .port.require {
            background: var(--port-require);
            margin-right: 8px;
        }
        
        .port.provide {
            background: var(--port-provide);
            margin-left: 8px;
        }
        
        .port.connected {
            box-shadow: 0 0 0 3px rgba(255,255,255,0.2);
        }
        
        /* SVG Connections */
        .connections-svg {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        
        .connection {
            fill: none;
            stroke: var(--accent);
            stroke-width: 2;
            stroke-linecap: round;
        }
        
        .connection-preview {
            stroke-dasharray: 5 5;
            opacity: 0.6;
        }
        
        /* Preview Panel */
        .preview-panel {
            background: var(--node);
            border-left: 1px solid var(--node-border);
            display: flex;
            flex-direction: column;
        }
        
        .preview-header {
            padding: 15px;
            border-bottom: 1px solid var(--node-border);
        }
        
        .preview-header h2 {
            font-size: 14px;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .preview-header input {
            width: 100%;
            padding: 8px 12px;
            background: var(--canvas);
            border: 1px solid var(--node-border);
            border-radius: 6px;
            color: var(--text);
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        .preview-header input:focus {
            outline: none;
            border-color: var(--accent);
        }
        
        .preview-stats {
            display: flex;
            gap: 15px;
            font-size: 12px;
            color: var(--text-dim);
        }
        
        .stat {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .stat-num {
            font-weight: bold;
            color: var(--accent);
        }
        
        .preview-content {
            flex: 1;
            overflow: auto;
            padding: 15px;
        }
        
        .preview-list {
            list-style: none;
        }
        
        .preview-list li {
            padding: 8px 12px;
            background: var(--canvas);
            margin-bottom: 6px;
            border-radius: 6px;
            font-size: 12px;
            display: flex;
            justify-content: space-between;
        }
        
        .preview-list .type {
            color: var(--text-dim);
            font-size: 10px;
        }
        
        .generate-btn {
            margin: 15px;
            background: linear-gradient(135deg, #58a6ff 0%, #3fb950 100%);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .generate-btn:hover {
            transform: translateY(-2px);
        }
        
        .generate-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Result modal */
        .modal {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.8);
            align-items: center;
            justify-content: center;
            z-index: 100;
        }
        
        .modal.show { display: flex; }
        
        .modal-content {
            background: var(--node);
            border-radius: 16px;
            padding: 30px;
            max-width: 500px;
            text-align: center;
        }
        
        .modal-content h3 {
            color: var(--port-provide);
            margin-bottom: 15px;
        }
        
        .modal-content code {
            display: block;
            background: var(--canvas);
            padding: 12px;
            border-radius: 6px;
            margin: 15px 0;
            font-family: monospace;
            font-size: 12px;
            text-align: left;
            overflow-x: auto;
        }
        
        .modal-content button {
            background: var(--accent);
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 10px;
        }
        
        /* Help */
        .help-tip {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 12px;
            color: var(--text-dim);
        }
    </style>
</head>
<body>
    <div class="app">
        <!-- Block Palette -->
        <div class="palette">
            <h2>Blocks</h2>
            <div id="palette"></div>
        </div>
        
        <!-- Canvas -->
        <div class="canvas-container" id="canvasContainer">
            <svg class="connections-svg" id="connectionsSvg"></svg>
            <div class="canvas" id="canvas"></div>
            <div class="help-tip">Drag blocks to canvas. Connect ports by dragging from one to another.</div>
        </div>
        
        <!-- Preview -->
        <div class="preview-panel">
            <div class="preview-header">
                <h2>Your App</h2>
                <input type="text" id="appName" placeholder="App name..." value="my_app">
                <input type="text" id="appDesc" placeholder="Description...">
                <div class="preview-stats">
                    <div class="stat"><span class="stat-num" id="nodeCount">0</span> blocks</div>
                    <div class="stat"><span class="stat-num" id="connCount">0</span> connections</div>
                </div>
            </div>
            <div class="preview-content">
                <h3 style="font-size: 12px; color: var(--text-dim); margin-bottom: 10px;">ARCHITECTURE</h3>
                <ul class="preview-list" id="previewList"></ul>
            </div>
            <button class="generate-btn" id="generateBtn">Generate App</button>
        </div>
    </div>
    
    <!-- Result Modal -->
    <div class="modal" id="resultModal">
        <div class="modal-content">
            <h3>App Generated!</h3>
            <p>Your app has been created:</p>
            <code id="resultPath"></code>
            <p>Run it with:</p>
            <code id="resultCmd"></code>
            <button onclick="closeModal()">Close</button>
        </div>
    </div>
    
    <script>
        // State
        let blocks = [];
        let nodes = [];
        let connections = [];
        let nextNodeId = 1;
        let draggingNode = null;
        let draggingPort = null;
        let previewConnection = null;
        let offset = { x: 0, y: 0 };
        
        // Load blocks
        async function init() {
            const res = await fetch('/api/blocks');
            const data = await res.json();
            blocks = data.blocks;
            renderPalette();
        }
        
        function renderPalette() {
            const palette = document.getElementById('palette');
            palette.innerHTML = blocks.map(b => `
                <div class="palette-block" draggable="true" data-block-id="${b.id}">
                    <div class="name">${b.name}</div>
                    <div class="desc">${b.description}</div>
                    <div class="ports-preview">
                        ${b.requires.map(() => '<div class="port-dot require"></div>').join('')}
                        ${b.provides.map(() => '<div class="port-dot provide"></div>').join('')}
                    </div>
                </div>
            `).join('');
            
            // Add drag handlers
            document.querySelectorAll('.palette-block').forEach(el => {
                el.addEventListener('dragstart', e => {
                    e.dataTransfer.setData('blockId', el.dataset.blockId);
                });
            });
        }
        
        // Canvas drop
        const canvas = document.getElementById('canvas');
        const canvasContainer = document.getElementById('canvasContainer');
        
        canvasContainer.addEventListener('dragover', e => e.preventDefault());
        canvasContainer.addEventListener('drop', e => {
            e.preventDefault();
            const blockId = e.dataTransfer.getData('blockId');
            if (!blockId) return;
            
            const block = blocks.find(b => b.id === blockId);
            if (!block) return;
            
            const rect = canvasContainer.getBoundingClientRect();
            const x = e.clientX - rect.left - 90;
            const y = e.clientY - rect.top - 30;
            
            addNode(block, x, y);
        });
        
        function addNode(block, x, y) {
            const node = {
                id: nextNodeId++,
                blockId: block.id,
                block: block,
                x: x,
                y: y
            };
            nodes.push(node);
            renderNodes();
            updatePreview();
        }
        
        function renderNodes() {
            canvas.innerHTML = nodes.map(n => `
                <div class="node" id="node-${n.id}" style="left: ${n.x}px; top: ${n.y}px;">
                    <div class="node-header">
                        <span class="node-title">${n.block.name}</span>
                        <button class="node-delete" onclick="deleteNode(${n.id})">×</button>
                    </div>
                    <div class="node-body">
                        ${n.block.requires.map((p, i) => `
                            <div class="port-row require">
                                <div class="port require" data-node="${n.id}" data-port="${p.name}" data-type="require" data-index="${i}"></div>
                                <span>${p.name}</span>
                            </div>
                        `).join('')}
                        ${n.block.provides.map((p, i) => `
                            <div class="port-row provide">
                                <span>${p.name}</span>
                                <div class="port provide" data-node="${n.id}" data-port="${p.name}" data-type="provide" data-index="${i}"></div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('');
            
            // Make nodes draggable
            document.querySelectorAll('.node').forEach(el => {
                const header = el.querySelector('.node-header');
                header.addEventListener('mousedown', e => {
                    if (e.target.classList.contains('node-delete')) return;
                    const nodeId = parseInt(el.id.split('-')[1]);
                    draggingNode = nodes.find(n => n.id === nodeId);
                    offset = { x: e.offsetX, y: e.offsetY };
                    el.classList.add('selected');
                });
            });
            
            // Port connection handlers
            document.querySelectorAll('.port').forEach(el => {
                el.addEventListener('mousedown', e => {
                    e.stopPropagation();
                    draggingPort = {
                        node: parseInt(el.dataset.node),
                        port: el.dataset.port,
                        type: el.dataset.type,
                        el: el
                    };
                });
                
                el.addEventListener('mouseup', e => {
                    if (draggingPort && draggingPort.el !== el) {
                        // Try to connect
                        const toType = el.dataset.type;
                        if (draggingPort.type === 'provide' && toType === 'require') {
                            addConnection(draggingPort.node, draggingPort.port, 
                                         parseInt(el.dataset.node), el.dataset.port);
                        } else if (draggingPort.type === 'require' && toType === 'provide') {
                            addConnection(parseInt(el.dataset.node), el.dataset.port,
                                         draggingPort.node, draggingPort.port);
                        }
                    }
                    draggingPort = null;
                    previewConnection = null;
                    renderConnections();
                });
            });
            
            renderConnections();
        }
        
        function deleteNode(nodeId) {
            nodes = nodes.filter(n => n.id !== nodeId);
            connections = connections.filter(c => c.fromNode !== nodeId && c.toNode !== nodeId);
            renderNodes();
            updatePreview();
        }
        
        function addConnection(fromNode, fromPort, toNode, toPort) {
            // Check if already exists
            const exists = connections.some(c => 
                c.fromNode === fromNode && c.fromPort === fromPort &&
                c.toNode === toNode && c.toPort === toPort
            );
            if (!exists) {
                connections.push({ fromNode, fromPort, toNode, toPort });
                updatePreview();
            }
        }
        
        function renderConnections() {
            const svg = document.getElementById('connectionsSvg');
            let paths = '';
            
            for (const conn of connections) {
                const fromEl = document.querySelector(`.port.provide[data-node="${conn.fromNode}"][data-port="${conn.fromPort}"]`);
                const toEl = document.querySelector(`.port.require[data-node="${conn.toNode}"][data-port="${conn.toPort}"]`);
                
                if (fromEl && toEl) {
                    const fromRect = fromEl.getBoundingClientRect();
                    const toRect = toEl.getBoundingClientRect();
                    const containerRect = canvasContainer.getBoundingClientRect();
                    
                    const x1 = fromRect.left + fromRect.width/2 - containerRect.left;
                    const y1 = fromRect.top + fromRect.height/2 - containerRect.top;
                    const x2 = toRect.left + toRect.width/2 - containerRect.left;
                    const y2 = toRect.top + toRect.height/2 - containerRect.top;
                    
                    const cx = (x1 + x2) / 2;
                    paths += `<path class="connection" d="M${x1},${y1} C${cx},${y1} ${cx},${y2} ${x2},${y2}"/>`;
                    
                    fromEl.classList.add('connected');
                    toEl.classList.add('connected');
                }
            }
            
            if (previewConnection) {
                paths += `<path class="connection connection-preview" d="${previewConnection}"/>`;
            }
            
            svg.innerHTML = paths;
        }
        
        // Mouse move for dragging
        document.addEventListener('mousemove', e => {
            if (draggingNode) {
                const rect = canvasContainer.getBoundingClientRect();
                draggingNode.x = e.clientX - rect.left - offset.x;
                draggingNode.y = e.clientY - rect.top - offset.y;
                const nodeEl = document.getElementById(`node-${draggingNode.id}`);
                nodeEl.style.left = draggingNode.x + 'px';
                nodeEl.style.top = draggingNode.y + 'px';
                renderConnections();
            }
            
            if (draggingPort) {
                const rect = canvasContainer.getBoundingClientRect();
                const portRect = draggingPort.el.getBoundingClientRect();
                const x1 = portRect.left + portRect.width/2 - rect.left;
                const y1 = portRect.top + portRect.height/2 - rect.top;
                const x2 = e.clientX - rect.left;
                const y2 = e.clientY - rect.top;
                const cx = (x1 + x2) / 2;
                previewConnection = `M${x1},${y1} C${cx},${y1} ${cx},${y2} ${x2},${y2}`;
                renderConnections();
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (draggingNode) {
                document.querySelectorAll('.node').forEach(el => el.classList.remove('selected'));
            }
            draggingNode = null;
            draggingPort = null;
            previewConnection = null;
            renderConnections();
        });
        
        function updatePreview() {
            document.getElementById('nodeCount').textContent = nodes.length;
            document.getElementById('connCount').textContent = connections.length;
            
            const list = document.getElementById('previewList');
            let items = nodes.map(n => 
                `<li>${n.block.name} <span class="type">${n.block.id}</span></li>`
            );
            
            connections.forEach(c => {
                const fromNode = nodes.find(n => n.id === c.fromNode);
                const toNode = nodes.find(n => n.id === c.toNode);
                if (fromNode && toNode) {
                    items.push(`<li style="background: #1a3a1a;">${fromNode.block.name}:${c.fromPort} → ${toNode.block.name}:${c.toPort}</li>`);
                }
            });
            
            list.innerHTML = items.join('');
        }
        
        // Generate
        document.getElementById('generateBtn').addEventListener('click', async () => {
            const btn = document.getElementById('generateBtn');
            btn.disabled = true;
            btn.textContent = 'Generating...';
            
            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: document.getElementById('appName').value,
                        description: document.getElementById('appDesc').value,
                        nodes: nodes.map(n => ({ id: n.id, blockId: n.blockId, x: n.x, y: n.y })),
                        connections: connections
                    })
                });
                
                const result = await res.json();
                if (result.success) {
                    document.getElementById('resultPath').textContent = result.path;
                    document.getElementById('resultCmd').textContent = result.run_command;
                    document.getElementById('resultModal').classList.add('show');
                }
            } catch (e) {
                alert('Generation failed: ' + e.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Generate App';
            }
        });
        
        function closeModal() {
            document.getElementById('resultModal').classList.remove('show');
        }
        
        init();
    </script>
</body>
</html>'''


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print("=" * 50)
    print("  Blueprint Sketchbook")
    print("=" * 50)
    print(f"  Canvas: http://localhost:{PORT}")
    print("=" * 50)
    print("  Drag blocks to canvas, wire ports together")
    print("  Press Ctrl+C to stop")
    print()
    
    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open(f"http://localhost:{PORT}")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    server = HTTPServer(("", PORT), SketchbookHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
