"""Modular Kernel — Algorithm for composing apps from kernel + components.

Architecture:
  1. Kernel: The core framework (Flask, Flask+SQLAlchemy, Flask+SocketIO, etc.)
     - Provides: routing, state, session, API base
  2. Components: Pluggable UI/logic modules
     - UI: editor, canvas, kanban, chat, etc.
     - Logic: auth, CRUD, search, export, etc.
  3. Glue: Integration code connecting components to kernel

The algorithm:
  1. Analyze description → extract requirements
  2. Select kernel based on requirements
  3. Select components based on description + past successes
  4. Compose them together
  5. Generate final app code
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
import hashlib

from build_memory import memory, BuildRecord
from template_registry import extract_features
from component_assembler import detect_components

# Try to import classifier (optional, graceful fallback)
try:
    from classifier import classifier as ml_classifier
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    ml_classifier = None


# =============================================================================
# Kernel Definitions
# =============================================================================

@dataclass
class Kernel:
    """Base kernel for app composition."""
    id: str
    name: str
    description: str
    requires: List[str] = field(default_factory=list)  # Required capabilities
    provides: List[str] = field(default_factory=list)  # What this kernel provides
    
    # Code templates
    imports: str = ""
    init: str = ""
    base_routes: str = ""
    main_block: str = ""


KERNELS = {
    "flask_minimal": Kernel(
        id="flask_minimal",
        name="Flask Minimal",
        description="Bare Flask app — routing only, no database",
        requires=[],
        provides=["routing", "templates", "static"],
        imports="""from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from datetime import datetime
""",
        init="""
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
CORS(app)
""",
        base_routes="""
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})
""",
        main_block="""
if __name__ == '__main__':
    app.run(debug=True, port=5000)
""",
    ),
    
    "flask_data": Kernel(
        id="flask_data",
        name="Flask + SQLAlchemy",
        description="Flask with SQLite database for data persistence",
        requires=["data"],
        provides=["routing", "templates", "static", "database", "models"],
        imports="""from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
""",
        init="""
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db = SQLAlchemy(app)
""",
        base_routes="""
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "database": "sqlite", "timestamp": datetime.utcnow().isoformat()})
""",
        main_block="""
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
""",
    ),
    
    "flask_auth": Kernel(
        id="flask_auth",
        name="Flask + Auth",
        description="Flask with user authentication and sessions",
        requires=["auth"],
        provides=["routing", "templates", "static", "database", "models", "auth", "sessions"],
        imports="""from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
""",
        init="""
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated
""",
        base_routes="""
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "auth": True, "timestamp": datetime.utcnow().isoformat()})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    if not username or not email or len(password) < 4:
        return jsonify({"error": "Username, email, and password (4+ chars) required"}), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already taken"}), 409
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({"id": user.id, "username": user.username}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '')
    password = data.get('password', '')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    session['user_id'] = user.id
    return jsonify({"id": user.id, "username": user.username})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route('/api/me')
def current_user():
    uid = session.get('user_id')
    if not uid:
        return jsonify({"user": None})
    user = User.query.get(uid)
    return jsonify({"user": {"id": user.id, "username": user.username} if user else None})
""",
        main_block="""
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
""",
    ),
    
    "flask_realtime": Kernel(
        id="flask_realtime",
        name="Flask + SocketIO",
        description="Flask with WebSocket support for real-time features",
        requires=["realtime"],
        provides=["routing", "templates", "static", "database", "models", "websocket"],
        imports="""from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime
""",
        init="""
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins='*')
""",
        base_routes="""
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "realtime": True, "timestamp": datetime.utcnow().isoformat()})

@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'ok'})

@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)
""",
        main_block="""
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, port=5000)
""",
    ),
    
    # NEW: FastAPI kernel for API-first apps
    "fastapi": Kernel(
        id="fastapi",
        name="FastAPI",
        description="Modern async API framework with automatic OpenAPI docs",
        requires=["api"],
        provides=["routing", "api", "validation", "openapi"],
        imports="""from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
""",
        init="""
app = FastAPI(title="Generated API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
""",
        base_routes="""
@app.get("/")
async def root():
    return {"message": "API is running", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
""",
        main_block="""
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
    ),
    
    # NEW: FastAPI with SQLAlchemy
    "fastapi_data": Kernel(
        id="fastapi_data",
        name="FastAPI + SQLAlchemy",
        description="FastAPI with database persistence",
        requires=["api", "data"],
        provides=["routing", "api", "validation", "openapi", "database", "models"],
        imports="""from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
""",
        init="""
app = FastAPI(title="Generated API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
        base_routes="""
@app.get("/")
async def root():
    return {"message": "API is running", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok", "database": "sqlite", "timestamp": datetime.utcnow().isoformat()}

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
""",
        main_block="""
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
    ),
    
    # NEW: CLI kernel with Click
    "cli_click": Kernel(
        id="cli_click",
        name="CLI with Click",
        description="Command-line interface application",
        requires=["cli"],
        provides=["cli", "commands", "arguments"],
        imports="""import click
import json
import sys
from pathlib import Path
from datetime import datetime
""",
        init="""
@click.group()
@click.version_option(version='1.0.0')
def cli():
    \"\"\"Generated CLI application.\"\"\"
    pass
""",
        base_routes="""
@cli.command()
def info():
    \"\"\"Show application information.\"\"\"
    click.echo("CLI Application v1.0.0")
    click.echo(f"Generated at: {datetime.now().isoformat()}")

@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def status(verbose):
    \"\"\"Check application status.\"\"\"
    click.echo(click.style('Status: OK', fg='green'))
    if verbose:
        click.echo(f"Python: {sys.version}")
""",
        main_block="""
if __name__ == '__main__':
    cli()
""",
    ),
    
    # NEW: HTML Canvas kernel for games
    "html_canvas": Kernel(
        id="html_canvas",
        name="HTML5 Canvas",
        description="Browser-based canvas game/visualization",
        requires=["canvas"],
        provides=["canvas", "rendering", "animation"],
        imports="""<!-- HTML5 Canvas Game -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canvas App</title>
    <style>
        body { margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #1a1a2e; }
        canvas { border: 2px solid #16213e; background: #0f3460; }
    </style>
</head>
<body>
    <canvas id="gameCanvas" width="800" height="600"></canvas>
""",
        init="""
<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
let gameState = { running: true };
""",
        base_routes="""
function gameLoop() {
    if (!gameState.running) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    update();
    render();
    requestAnimationFrame(gameLoop);
}

function update() {
    // Game logic here
}

function render() {
    // Drawing here
}
""",
        main_block="""
// Start the game
gameLoop();
</script>
</body>
</html>
""",
    ),
    
    # NEW: Phaser.js kernel for advanced games
    "phaser": Kernel(
        id="phaser",
        name="Phaser.js Game",
        description="Advanced 2D game framework with physics",
        requires=["game", "physics"],
        provides=["canvas", "physics", "sprites", "animation", "audio"],
        imports="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phaser Game</title>
    <script src="https://cdn.jsdelivr.net/npm/phaser@3/dist/phaser.min.js"></script>
    <style>
        body { margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #1a1a2e; }
    </style>
</head>
<body>
""",
        init="""
<script>
const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    physics: {
        default: 'arcade',
        arcade: { gravity: { y: 300 }, debug: false }
    },
    scene: { preload, create, update }
};

const game = new Phaser.Game(config);
let player, cursors;
""",
        base_routes="""
function preload() {
    // Load assets
}

function create() {
    // Setup game objects
    cursors = this.input.keyboard.createCursorKeys();
}

function update() {
    // Game loop logic
}
""",
        main_block="""
</script>
</body>
</html>
""",
    ),
    
    # NEW: Flask with ML/sklearn
    "flask_ml": Kernel(
        id="flask_ml",
        name="Flask + ML",
        description="Flask with machine learning model serving",
        requires=["ml"],
        provides=["routing", "templates", "ml", "prediction"],
        imports="""from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import numpy as np
from datetime import datetime
import pickle
import os
""",
        init="""
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
CORS(app)

# Load model if exists
model = None
MODEL_PATH = 'model.pkl'
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
""",
        base_routes="""
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({
        "status": "ok", 
        "model_loaded": model is not None,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({"error": "No model loaded"}), 400
    data = request.get_json()
    features = np.array(data.get('features', [])).reshape(1, -1)
    prediction = model.predict(features)
    return jsonify({"prediction": prediction.tolist()})
""",
        main_block="""
if __name__ == '__main__':
    app.run(debug=True, port=5000)
""",
    ),
}


# =============================================================================
# Component Slots
# =============================================================================

@dataclass
class ComponentSlot:
    """A slot where a UI/logic component can be plugged in."""
    id: str
    name: str
    category: str  # "ui", "logic", "data"
    requires: List[str] = field(default_factory=list)  # What this component needs from kernel
    provides: List[str] = field(default_factory=list)  # What this component adds


# Standard component slots (these map to component_assembler IDs)
COMPONENT_SLOTS = {
    # UI Components
    "editor": ComponentSlot("editor", "Text Editor", "ui", requires=["templates"], provides=["editing"]),
    "canvas": ComponentSlot("canvas", "Drawing Canvas", "ui", requires=["templates"], provides=["drawing"]),
    "kanban": ComponentSlot("kanban", "Kanban Board", "ui", requires=["templates"], provides=["task_management"]),
    "chat": ComponentSlot("chat", "Chat Interface", "ui", requires=["templates"], provides=["messaging"]),
    "flashcard": ComponentSlot("flashcard", "Flashcards", "ui", requires=["templates"], provides=["study"]),
    "typing_test": ComponentSlot("typing_test", "Typing Test", "ui", requires=["templates"], provides=["testing"]),
    
    # Generator Components
    "password_gen": ComponentSlot("password_gen", "Password Generator", "ui", requires=["templates"], provides=["generation"]),
    "color_gen": ComponentSlot("color_gen", "Color Palette", "ui", requires=["templates"], provides=["generation"]),
    "dice_roller": ComponentSlot("dice_roller", "Dice Roller", "ui", requires=["templates"], provides=["randomization"]),
    "coin_flip": ComponentSlot("coin_flip", "Coin Flipper", "ui", requires=["templates"], provides=["randomization"]),
    "quote_gen": ComponentSlot("quote_gen", "Quote Generator", "ui", requires=["templates"], provides=["generation"]),
    "lorem_gen": ComponentSlot("lorem_gen", "Lorem Generator", "ui", requires=["templates"], provides=["generation"]),
    "name_gen": ComponentSlot("name_gen", "Name Generator", "ui", requires=["templates"], provides=["generation"]),
    
    # Game Components
    "sliding_puzzle": ComponentSlot("sliding_puzzle", "Sliding Puzzle", "ui", requires=["templates"], provides=["game"]),
    "guess_game": ComponentSlot("guess_game", "Guessing Game", "ui", requires=["templates"], provides=["game"]),
    "memory_game": ComponentSlot("memory_game", "Memory Match", "ui", requires=["templates"], provides=["game"]),
    "tictactoe": ComponentSlot("tictactoe", "Tic Tac Toe", "ui", requires=["templates"], provides=["game"]),
    "hangman": ComponentSlot("hangman", "Hangman", "ui", requires=["templates"], provides=["game"]),
    "wordle": ComponentSlot("wordle", "Wordle", "ui", requires=["templates"], provides=["game"]),
    "quiz": ComponentSlot("quiz", "Quiz/Trivia", "ui", requires=["templates"], provides=["game", "study"]),
    "calculator": ComponentSlot("calculator", "Calculator", "ui", requires=["templates"], provides=["calculation"]),
    "converter": ComponentSlot("converter", "Unit Converter", "ui", requires=["templates"], provides=["calculation"]),
    "timer": ComponentSlot("timer", "Timer/Pomodoro", "ui", requires=["templates"], provides=["timing"]),
    "reaction_game": ComponentSlot("reaction_game", "Reaction Game", "ui", requires=["templates"], provides=["game"]),
    "simon_game": ComponentSlot("simon_game", "Simon/Grid Click Game", "ui", requires=["templates"], provides=["game"]),
    "reflex_game": ComponentSlot("reflex_game", "Reflex Game", "ui", requires=["templates"], provides=["game"]),
    "minesweeper": ComponentSlot("minesweeper", "Minesweeper", "ui", requires=["templates"], provides=["game"]),
    
    # Logic Components
    "crud": ComponentSlot("crud", "CRUD Operations", "logic", requires=["database", "models"], provides=["create", "read", "update", "delete"]),
    "search": ComponentSlot("search", "Search/Filter", "logic", requires=["database"], provides=["search"]),
    "export": ComponentSlot("export", "Data Export", "logic", requires=["database"], provides=["export"]),
}


# =============================================================================
# Composition Algorithm
# =============================================================================

@dataclass
class AppComposition:
    """Result of the composition algorithm."""
    kernel: Kernel
    components: List[str]  # Component IDs
    features: Dict[str, Any]
    description: str
    build_record: Optional[BuildRecord] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "kernel": self.kernel.id,
            "kernel_name": self.kernel.name,
            "kernel_description": self.kernel.description,
            "components": self.components,
            "features": self.features,
            "description": self.description,
            "build_id": self.build_record.id if self.build_record else None,
        }


class ModularBuilder:
    """Builds apps using the kernel + component architecture."""
    
    def __init__(self):
        self.memory = memory
        self.use_ml = ML_AVAILABLE
    
    def analyze(self, description: str, answers: Dict[str, bool] = None) -> Dict[str, Any]:
        """Step 1: Analyze description and extract requirements.
        
        Uses ML classifier if trained, falls back to regex-based detection.
        """
        answers = answers or {}
        features = extract_features(description)
        desc_lower = description.lower()
        
        # Try ML-based feature prediction first
        ml_features = {}
        ml_confidence = 0.0
        if self.use_ml and ml_classifier:
            ml_pred = ml_classifier.feature_clf.predict(description)
            if ml_pred:
                ml_features = ml_pred
                ml_confidence = max(ml_pred.values()) if ml_pred else 0.0
        
        # Regex-based detection (fallback or complement)
        regex_realtime = any(kw in desc_lower for kw in ["realtime", "real-time", "live", "chat", "websocket", "instant"])
        regex_auth = any(kw in desc_lower for kw in ["login", "auth", "user", "account", "profile", "password", "sign in", "register"])
        regex_data = "data_app" in features or any(kw in desc_lower for kw in ["database", "store", "save", "crud", "manage", "track", "list", "collection"])
        regex_search = "search" in desc_lower
        regex_export = "export" in desc_lower
        
        # Combine ML and regex: ML wins if confidence > 0.6, else use OR
        ml_threshold = 0.6
        
        def combine(ml_key: str, regex_val: bool, answer_key: str) -> bool:
            if answers.get(answer_key):
                return True
            ml_prob = ml_features.get(ml_key, 0.0)
            if ml_prob >= ml_threshold:
                return True
            if ml_prob > 0.3 and regex_val:
                return True  # ML + regex agree
            return regex_val
        
        needs_realtime = combine("needs_realtime", regex_realtime, "realtime")
        needs_auth = combine("needs_auth", regex_auth, "needs_auth")
        needs_data = combine("needs_data", regex_data, "has_data")
        needs_search = combine("needs_search", regex_search, "search")
        needs_export = combine("needs_export", regex_export, "export")
        
        return {
            "description": description,
            "features": {k: v.value for k, v in features.items()},
            "needs_data": needs_data,
            "needs_auth": needs_auth,
            "needs_realtime": needs_realtime,
            "needs_search": needs_search,
            "needs_export": needs_export,
            "ml_used": bool(ml_features),
            "ml_confidence": ml_confidence,
        }
    
    def select_kernel(self, requirements: Dict[str, Any], description: str = "") -> Kernel:
        """Step 2: Select the appropriate kernel based on requirements.
        
        Uses ML classifier if trained with high confidence, else rule-based.
        """
        # Try ML-based template selection first
        if self.use_ml and ml_classifier and description:
            ml_result = ml_classifier.template_clf.predict(description)
            if ml_result.used_ml and ml_result.confidence >= 0.7:
                # ML is confident, use its prediction if valid
                if ml_result.prediction in KERNELS:
                    return KERNELS[ml_result.prediction]
        
        # Rule-based fallback
        if requirements.get("needs_realtime"):
            return KERNELS["flask_realtime"]
        if requirements.get("needs_auth"):
            return KERNELS["flask_auth"]
        if requirements.get("needs_data"):
            return KERNELS["flask_data"]
        return KERNELS["flask_minimal"]
    
    def select_components(self, description: str, requirements: Dict[str, Any]) -> List[str]:
        """Step 3: Select components based on description and past successes."""
        components = []
        
        # Try ML-based component prediction first
        if self.use_ml and ml_classifier:
            ml_components = ml_classifier.component_clf.predict(description, threshold=0.5)
            for comp_id, prob in ml_components:
                if comp_id in COMPONENT_SLOTS and comp_id not in components:
                    components.append(comp_id)
        
        # Detect components from description (regex patterns)
        detected = detect_components(description)
        for priority, comp in detected:
            comp_id = comp.get("id")
            if comp_id and comp_id in COMPONENT_SLOTS and comp_id not in components:
                components.append(comp_id)
        
        # Add logic components based on requirements
        if requirements.get("needs_data"):
            components.append("crud")
        if requirements.get("needs_search"):
            components.append("search")
        if requirements.get("needs_export"):
            components.append("export")
        
        # Check build memory for recommendations
        similar_builds = self.memory.get_similar_good_builds(description, limit=3)
        for build in similar_builds:
            for comp in build.components:
                if comp not in components and comp in COMPONENT_SLOTS:
                    # Add components from similar successful builds
                    components.append(comp)
        
        # Remove components that failed in the past for similar descriptions
        patterns_to_avoid = self.memory.get_patterns_to_avoid(limit=20)
        # (Could filter here based on patterns, but keeping simple for now)
        
        return list(dict.fromkeys(components))  # Dedupe while preserving order
    
    def compose(self, description: str, answers: Dict[str, bool] = None) -> AppComposition:
        """Main algorithm: Compose an app from kernel + components."""
        # Step 1: Analyze
        requirements = self.analyze(description, answers)
        
        # Step 2: Select kernel (pass description for ML-based selection)
        kernel = self.select_kernel(requirements, description)
        
        # Step 3: Select components
        components = self.select_components(description, requirements)
        
        # Step 4: Validate compatibility
        provided = set(kernel.provides)
        for comp_id in components[:]:  # Copy to allow modification
            slot = COMPONENT_SLOTS.get(comp_id)
            if slot:
                # Check if kernel provides what component needs
                missing = set(slot.requires) - provided
                if missing:
                    # Upgrade kernel if needed
                    if "database" in missing and kernel.id == "flask_minimal":
                        kernel = KERNELS["flask_data"]
                        provided = set(kernel.provides)
        
        # Step 5: Create build record
        record = BuildRecord(
            description=description,
            template_used=kernel.id,
            components=components,
            features=requirements.get("features", {}),
            answers=answers or {},
            status="pending",
        )
        record.id = self.memory.save_build(record)
        
        composition = AppComposition(
            kernel=kernel,
            components=components,
            features=requirements.get("features", {}),
            description=description,
            build_record=record,
        )
        
        return composition
    
    def generate_app_py(self, composition: AppComposition, app_name: str) -> str:
        """Generate the app.py code from a composition."""
        kernel = composition.kernel
        
        parts = [
            f'"""{app_name} - Generated by App Forge Modular Builder."""\n',
            kernel.imports,
            kernel.init,
        ]
        
        # Add any model definitions for data components
        if "crud" in composition.components:
            # Models would be added here based on domain_parser
            pass
        
        parts.append(kernel.base_routes)
        
        # Add component-specific routes
        for comp_id in composition.components:
            slot = COMPONENT_SLOTS.get(comp_id)
            if slot and slot.category == "logic":
                # Logic components might add API routes
                parts.append(f"\n# === {slot.name} ===\n")
        
        parts.append(kernel.main_block)
        
        return "\n".join(parts)
    
    def accept_build(self, build_id: int) -> BuildRecord:
        """Accept a build (move to Good store)."""
        return self.memory.accept_build(build_id)
    
    def reject_build(self, build_id: int, reason: str) -> BuildRecord:
        """Reject a build with reason (move to Bad store)."""
        return self.memory.reject_build(build_id, reason)
    
    def delete_build(self, build_id: int, reason: str) -> BuildRecord:
        """Delete a build with reason (soft delete to Bad store)."""
        return self.memory.delete_build(build_id, reason)
    
    def create_revision(self, build_id: int, new_description: str = None,
                        user_edits: str = "") -> AppComposition:
        """Create a new revision of an existing build."""
        new_record = self.memory.create_revision(build_id, new_description, user_edits)
        if not new_record:
            return None
        
        # Re-compose with updated description
        return self.compose(
            new_record.description,
            new_record.answers,
        )
    
    def get_recommendations(self, description: str) -> Dict[str, Any]:
        """Get recommendations based on past builds."""
        features = extract_features(description)
        
        # Similar successful builds
        similar = self.memory.get_similar_good_builds(description, limit=5)
        
        # Success rates for detected features
        feature_rates = {}
        for key, feat in features.items():
            rate = self.memory.get_feature_success_rate(key, feat.value)
            feature_rates[key] = {
                "value": feat.value,
                "success_rate": f"{rate:.0%}",
                "recommendation": "suggested" if rate > 0.6 else "caution" if rate < 0.4 else "neutral"
            }
        
        return {
            "similar_builds": [
                {"description": b.description, "template": b.template_used, "revision": b.revision}
                for b in similar
            ],
            "feature_analysis": feature_rates,
            "stats": self.memory.get_stats(),
        }


# Singleton instance
builder = ModularBuilder()
