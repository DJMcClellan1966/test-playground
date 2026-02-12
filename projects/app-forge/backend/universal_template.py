"""Universal Template - Base structure all apps share.

This defines the common structure that every application has,
with named slots where features inject their code.

The key insight: ALL apps (regardless of type) share these common elements:
- Entry point / initialization
- Configuration
- Domain models / data structures
- Main logic (routes, commands, game loop, etc.)
- Helper functions
- Error handling
- Cleanup / shutdown

The slots are filled by Features from the Feature Store.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class Slot(Enum):
    """Named slots in the universal template."""
    IMPORTS = "imports"
    CONFIG = "config"
    MODELS = "models"
    INIT = "init"
    ROUTES = "routes"           # Main logic - routes, handlers, game loop
    HELPERS = "helpers"
    ERROR_HANDLING = "error_handling"
    CLEANUP = "cleanup"
    MAIN = "main"


@dataclass
class SlotContent:
    """Content to inject into a slot."""
    code: str
    priority: int = 50          # 0-100, lower = earlier in slot
    comment: str = ""           # Optional comment for debugging


@dataclass
class TemplateContext:
    """Context passed to template rendering."""
    app_name: str
    description: str
    framework: str
    answers: Dict[str, Any] = field(default_factory=dict)
    models: List[Any] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# Universal Templates per Framework
# =====================================================================

UNIVERSAL_TEMPLATES = {
    "flask": '''"""
{app_name} - Auto-generated Flask Application
{description}
"""

# Imports
{imports}

# Configuration
{config}

# Models
{models}

# Initialization
{init}

# Routes / Main Logic
{routes}

# Helpers
{helpers}

# Error Handling
{error_handling}

# Cleanup
{cleanup}

# Entry Point
{main}
''',

    "fastapi": '''"""
{app_name} - Auto-generated FastAPI Application
{description}
"""

# Imports
{imports}

# Configuration
{config}

# Models / Schemas
{models}

# Initialization
{init}

# Endpoints
{routes}

# Helpers
{helpers}

# Error Handling
{error_handling}

# Lifecycle
{cleanup}

# Entry Point
{main}
''',

    "click": '''"""
{app_name} - Auto-generated CLI Application
{description}
"""

# Imports
{imports}

# Configuration
{config}

# Models / Data Structures
{models}

# Initialization
{init}

# Commands
{routes}

# Helpers
{helpers}

# Error Handling
{error_handling}

# Cleanup
{cleanup}

# Entry Point
{main}
''',

    "html_canvas": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh;
            background: #1a1a2e;
            font-family: system-ui;
        }}
        canvas {{ border: 2px solid #4a4e69; border-radius: 8px; }}
        #ui {{ position: absolute; top: 20px; left: 50%; transform: translateX(-50%); color: white; }}
        {config}
    </style>
</head>
<body>
    <div id="ui"></div>
    <canvas id="game"></canvas>
    
    <script>
    // {description}
    
    // Imports / Globals
    {imports}
    
    // Configuration
    const CONFIG = {{
        {models}
    }};
    
    // Initialization
    {init}
    
    // Main Logic
    {routes}
    
    // Helpers
    {helpers}
    
    // Error Handling
    {error_handling}
    
    // Cleanup
    {cleanup}
    
    // Entry Point
    {main}
    </script>
</body>
</html>
''',

    "sklearn": '''"""
{app_name} - Auto-generated ML Pipeline
{description}
"""

# Imports
{imports}

# Configuration
{config}

# Data Models / Schemas
{models}

# Pipeline Setup
{init}

# Training / Inference
{routes}

# Helpers
{helpers}

# Error Handling
{error_handling}

# Cleanup
{cleanup}

# Entry Point
{main}
'''
}


# =====================================================================
# Slot Defaults (minimal working code for each slot)
# =====================================================================

SLOT_DEFAULTS = {
    "flask": {
        Slot.IMPORTS: "from flask import Flask, render_template, request, jsonify",
        Slot.CONFIG: "app = Flask(__name__)\napp.config['SECRET_KEY'] = 'dev-secret-key'",
        Slot.MODELS: "# No models defined",
        Slot.INIT: "# App initialized above",
        Slot.ROUTES: '''@app.route('/')
def index():
    return render_template('index.html')''',
        Slot.HELPERS: "# No helpers defined",
        Slot.ERROR_HANDLING: '''@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Not found"), 404''',
        Slot.CLEANUP: "# No cleanup needed",
        Slot.MAIN: '''if __name__ == '__main__':
    app.run(debug=True, port=5000)''',
    },
    
    "fastapi": {
        Slot.IMPORTS: "from fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel",
        Slot.CONFIG: "app = FastAPI()",
        Slot.MODELS: "# No models defined",
        Slot.INIT: "# App initialized above",
        Slot.ROUTES: '''@app.get("/")
async def root():
    return {"message": "Hello World"}''',
        Slot.HELPERS: "# No helpers defined",
        Slot.ERROR_HANDLING: "# FastAPI handles errors automatically",
        Slot.CLEANUP: "# No cleanup needed",
        Slot.MAIN: '''if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)''',
    },
    
    "click": {
        Slot.IMPORTS: "import click",
        Slot.CONFIG: "# CLI Configuration",
        Slot.MODELS: "# No models defined",
        Slot.INIT: "# Initialization",
        Slot.ROUTES: '''@click.group()
def cli():
    """CLI Application"""
    pass

@cli.command()
def hello():
    """Say hello"""
    click.echo("Hello, World!")''',
        Slot.HELPERS: "# No helpers defined",
        Slot.ERROR_HANDLING: "# Click handles errors",
        Slot.CLEANUP: "# No cleanup needed",
        Slot.MAIN: '''if __name__ == "__main__":
    cli()''',
    },
    
    "html_canvas": {
        Slot.IMPORTS: "const canvas = document.getElementById('game');\nconst ctx = canvas.getContext('2d');",
        Slot.CONFIG: "",
        Slot.MODELS: "width: 800,\n    height: 600",
        Slot.INIT: "canvas.width = CONFIG.width;\ncanvas.height = CONFIG.height;",
        Slot.ROUTES: '''function gameLoop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Game logic here
    requestAnimationFrame(gameLoop);
}''',
        Slot.HELPERS: "// No helpers defined",
        Slot.ERROR_HANDLING: "window.onerror = (msg) => console.error(msg);",
        Slot.CLEANUP: "// No cleanup needed",
        Slot.MAIN: "gameLoop();",
    },
    
    "sklearn": {
        Slot.IMPORTS: "import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split",
        Slot.CONFIG: "RANDOM_STATE = 42\nTEST_SIZE = 0.2",
        Slot.MODELS: "# No data models defined",
        Slot.INIT: "# Pipeline setup",
        Slot.ROUTES: '''def train(X, y):
    """Train the model."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    # Training logic here
    return None''',
        Slot.HELPERS: "# No helpers defined",
        Slot.ERROR_HANDLING: "# Error handling",
        Slot.CLEANUP: "# Cleanup",
        Slot.MAIN: '''if __name__ == "__main__":
    print("ML Pipeline ready")''',
    },
}


# =====================================================================
# Template Renderer
# =====================================================================

class TemplateRenderer:
    """Renders the universal template with slot content."""
    
    def __init__(self, framework: str):
        self.framework = framework
        self.slots: Dict[Slot, List[SlotContent]] = {s: [] for s in Slot}
    
    def inject(self, slot: Slot, code: str, priority: int = 50, comment: str = ""):
        """Inject code into a slot."""
        self.slots[slot].append(SlotContent(code=code, priority=priority, comment=comment))
    
    def inject_many(self, slot_contents: Dict[Slot, str]):
        """Inject code into multiple slots."""
        for slot, code in slot_contents.items():
            if code:
                self.inject(slot, code)
    
    def render(self, context: TemplateContext) -> str:
        """Render the template with all injected content."""
        template = UNIVERSAL_TEMPLATES.get(self.framework, UNIVERSAL_TEMPLATES["flask"])
        defaults = SLOT_DEFAULTS.get(self.framework, SLOT_DEFAULTS["flask"])
        
        # Compile slot contents
        slot_code = {}
        for slot in Slot:
            contents = sorted(self.slots[slot], key=lambda x: x.priority)
            
            if contents:
                # Combine injected content
                code_parts = []
                for content in contents:
                    if content.comment:
                        code_parts.append(f"# {content.comment}")
                    code_parts.append(content.code)
                slot_code[slot.value] = "\n\n".join(code_parts)
            else:
                # Use default
                slot_code[slot.value] = defaults.get(slot, "")
        
        # Render template
        return template.format(
            app_name=context.app_name,
            description=context.description,
            **slot_code
        )


# =====================================================================
# Usage Example
# =====================================================================

if __name__ == "__main__":
    # Example: Render a Flask app with custom routes
    renderer = TemplateRenderer("flask")
    
    # Inject custom code
    renderer.inject(Slot.IMPORTS, "from flask_sqlalchemy import SQLAlchemy", priority=10)
    renderer.inject(Slot.MODELS, '''
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
''')
    renderer.inject(Slot.ROUTES, '''
@app.route('/items')
def list_items():
    items = Item.query.all()
    return jsonify([i.name for i in items])
''', priority=60)
    
    context = TemplateContext(
        app_name="ItemTracker",
        description="A simple item tracking app",
        framework="flask"
    )
    
    code = renderer.render(context)
    print(code)
