# ---------------------------------------------------------------------
# HybridBrain: Combine Symbolic and Semantic Matching
# ---------------------------------------------------------------------
class HybridBrain:
    """Combines Brain (Jaccard) and SemanticMemory (GloVe) for template selection."""
    def __init__(self, semantic_memory=None, symbolic_weight=0.5, semantic_weight=0.5):
        self.symbolic_weight = symbolic_weight
        self.semantic_weight = semantic_weight
        self.semantic_memory = semantic_memory  # Should be a SemanticMemory instance

    def score_templates(self, user_input: str):
        # Symbolic (Jaccard) scores
        best_symbolic, symbolic_scores, user_params = Brain.map_user_intent(user_input)
        # Semantic (GloVe) scores
        semantic_scores = {}
        if self.semantic_memory:
            for tpl in Brain.template_params:
                # Use template name as label, or a description if available
                label = tpl
                # If template descriptions are available, use them here
                sim = 0.0
                if self.semantic_memory.db:
                    sim = max((score for l, score in self.semantic_memory.explain(user_input) if l == label), default=0.0)
                semantic_scores[tpl] = sim
        else:
            for tpl in Brain.template_params:
                semantic_scores[tpl] = 0.0
        # Combine scores
        hybrid_scores = {}
        for tpl in Brain.template_params:
            hybrid_scores[tpl] = (
                self.symbolic_weight * symbolic_scores.get(tpl, 0.0) +
                self.semantic_weight * semantic_scores.get(tpl, 0.0)
            )
        # Select best
        best = max(hybrid_scores, key=hybrid_scores.get)
        return {
            "input": user_input,
            "user_params": list(user_params),
            "symbolic_scores": symbolic_scores,
            "semantic_scores": semantic_scores,
            "hybrid_scores": hybrid_scores,
            "best_template": best
        }
# ---------------------------------------------------------------------
# Semantic Memory: GloVe Embedding + Attention + Similarity Search
# ---------------------------------------------------------------------
import numpy as np
import os

class SemanticMemory:
    """Semantic memory using GloVe embeddings and cosine similarity."""
    def __init__(self, glove_path=None, dim=50):
        self.glove = None
        self.dim = dim
        self.db = []  # List of (label, vector)
        if glove_path and os.path.exists(glove_path):
            self.glove = self.load_glove(glove_path)

    def load_glove(self, path):
        glove = {}
        with open(path, 'r', encoding='utf8') as f:
            for line in f:
                parts = line.split()
                word = parts[0]
                vec = np.array(parts[1:], dtype=np.float32)
                glove[word] = vec
        return glove

    def embed_sentence(self, sentence, attention=None):
        if self.glove is None:
            return np.zeros(self.dim)
        words = sentence.lower().split()
        vectors = [self.glove[w] for w in words if w in self.glove]
        if not vectors:
            return np.zeros(self.dim)
        if attention:
            weights = np.array([attention.get(w, 1.0) for w in words if w in self.glove])
            return np.average(vectors, axis=0, weights=weights)
        return np.mean(vectors, axis=0)

    def add(self, label, sentence, attention=None):
        vec = self.embed_sentence(sentence, attention)
        self.db.append((label, vec))

    def cosine_similarity(self, a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def find_most_similar(self, sentence, attention=None):
        query_vec = self.embed_sentence(sentence, attention)
        if not self.db:
            return None, 0.0
        best = max(self.db, key=lambda x: self.cosine_similarity(query_vec, x[1]))
        score = self.cosine_similarity(query_vec, best[1])
        return best[0], score

    def explain(self, sentence, attention=None):
        query_vec = self.embed_sentence(sentence, attention)
        sims = [(label, self.cosine_similarity(query_vec, vec)) for label, vec in self.db]
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims

# Example usage (requires GloVe file):
# mem = SemanticMemory('glove.6B.50d.txt')
# mem.add('todo list', 'todo list')
# mem.add('note app', 'note taking application')
# print(mem.find_most_similar('I want a task tracker'))
# ---------------------------------------------------------------------
# Brain: User Intent Mapping via Jaccard Similarity
# ---------------------------------------------------------------------
from typing import Set

def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Compute Jaccard similarity: |A ∩ B| / |A ∪ B|."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

class Brain:
    """Maps user input to template parameters using Jaccard similarity."""
    param_table = {
        "login": "auth",
        "list": "list",
        "dark mode": "theme_dark",
        "api": "api",
        "form": "form",
        "todo": "list",
        "register": "auth",
        "notes": "crud",
        # Add more mappings as needed
    }

    template_params = {
        "react": {"list", "form", "theme_dark", "api"},
        "flask": {"auth", "list", "form"},
        "fastapi": {"api", "auth", "list"},
    }

    @classmethod
    def map_user_intent(cls, user_input: str):
        # Simple keyword extraction (split, can be replaced with NLP)
        keywords = set(user_input.lower().split())
        # Map keywords to parameters
        user_params = set(cls.param_table.get(k, k) for k in keywords)
        # Score each template
        scores = {tpl: jaccard_similarity(user_params, params) for tpl, params in cls.template_params.items()}
        # Select best template(s)
        best = max(scores, key=scores.get)
        return best, scores, user_params

    @classmethod
    def explain(cls, user_input: str):
        best, scores, user_params = cls.map_user_intent(user_input)
        return {
            "input": user_input,
            "extracted_params": list(user_params),
            "scores": scores,
            "best_template": best
        }
import json
from pathlib import Path
import types
from universal_template import Slot, TemplateRenderer, TemplateContext

@dataclass(frozen=True)
class Feature:
    """A composable feature that injects code into template slots."""
    id: str
"""Feature Store - Composable building blocks for apps."""
import json
from pathlib import Path
import types
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from universal_template import Slot, TemplateRenderer, TemplateContext

@dataclass(frozen=True)
class Feature:
    """A composable feature that injects code into template slots."""
    id: str
    name: str
    description: str
    slots: types.MappingProxyType = field(default_factory=lambda: types.MappingProxyType({}))
    variants: types.MappingProxyType = field(default_factory=lambda: types.MappingProxyType({}))
    requires_features: tuple = field(default_factory=tuple)
    requires_packages: types.MappingProxyType = field(default_factory=lambda: types.MappingProxyType({}))
    config_keys: tuple = field(default_factory=tuple)
    priority: int = 50

    def get_slots(self, framework: str) -> dict:
        """Get slot content for a specific framework."""
        #...

    def __hash__(self):
        def make_hashable(obj):
            if isinstance(obj, dict) or isinstance(obj, types.MappingProxyType):
                return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
            elif isinstance(obj, (list, set, frozenset, tuple)):
                return tuple(make_hashable(x) for x in obj)
            elif hasattr(obj, '__dict__'):
                return make_hashable(vars(obj))
            return obj
        return hash((
            self.id,
            self.name,
            self.description,
            make_hashable(self.slots),
            make_hashable(self.variants),
            make_hashable(self.requires_features),
            make_hashable(self.requires_packages),
            make_hashable(self.config_keys),
            self.priority
        ))
    
    # Dependencies
    requires_features: List[str] = field(default_factory=list)
    requires_packages: Dict[str, List[str]] = field(default_factory=dict)  # framework -> packages
    
    # Config keys this feature needs
    config_keys: List[str] = field(default_factory=list)
    
    # Priority for slot injection (lower = earlier)
    priority: int = 50
    
    def get_slots(self, framework: str) -> Dict[Slot, str]:
        """Get slot content for a specific framework."""
        # Start with defaults
        result = dict(self.slots)
        
        # Override with framework-specific
        if framework in self.variants:
            result.update(self.variants[framework])
        
        return result
    
    def get_packages(self, framework: str) -> List[str]:
        """Get required packages for a framework."""
        return self.requires_packages.get(framework, [])


# =====================================================================
# Feature Definitions
# =====================================================================

FEATURES: Dict[str, Feature] = {}


def register_feature(feature: Feature):
    """Register a feature in the store."""
    FEATURES[feature.id] = feature
    return feature


# ---------------------
# CORE FEATURES
# ---------------------

register_feature(Feature(
    id="database",
    name="Database",
    description="SQLite database with SQLAlchemy ORM",
    slots={
        Slot.IMPORTS: "from flask_sqlalchemy import SQLAlchemy\nfrom datetime import datetime",
        Slot.CONFIG: '''app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)''',
        Slot.INIT: '''with app.app_context():
    db.create_all()''',
    },
    variants={
        "fastapi": {
            Slot.IMPORTS: '''from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime''',
            Slot.CONFIG: '''DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()''',
            Slot.INIT: "Base.metadata.create_all(bind=engine)",
        },
    },
    requires_packages={
        "flask": ["flask-sqlalchemy"],
        "fastapi": ["sqlalchemy", "databases"],
    },
    priority=10,  # Database should initialize early
))


register_feature(Feature(
    id="crud",
    name="CRUD Operations",
    description="Create, Read, Update, Delete API endpoints",
    requires_features=["database"],
    slots={
        Slot.ROUTES: '''
# CRUD Routes
@app.route('/api/items', methods=['GET'])
def list_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    item = Item(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/items/<int:id>', methods=['GET'])
def get_item(id):
    item = Item.query.get_or_404(id)
    return jsonify(item.to_dict())

@app.route('/api/items/<int:id>', methods=['PUT'])
def update_item(id):
    item = Item.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        if hasattr(item, key):
            setattr(item, key, value)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/items/<int:id>', methods=['DELETE'])
def delete_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return '', 204
''',
    },
    variants={
        "fastapi": {
            Slot.ROUTES: '''
# CRUD Endpoints
@app.get("/api/items")
async def list_items():
    db = SessionLocal()
    try:
        items = db.query(Item).all()
        return [item.to_dict() for item in items]
    finally:
        db.close()

@app.post("/api/items")
async def create_item(item: ItemCreate):
    db = SessionLocal()
    try:
        db_item = Item(**item.dict())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item.to_dict()
    finally:
        db.close()

@app.get("/api/items/{id}")
async def get_item(id: int):
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item.to_dict()
    finally:
        db.close()

@app.delete("/api/items/{id}")
async def delete_item(id: int):
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        db.delete(item)
        db.commit()
        return {"ok": True}
    finally:
        db.close()
''',
        },
    },
    priority=60,
))


register_feature(Feature(
    id="auth",
    name="Authentication",
    description="User login/logout with session management",
    requires_features=["database"],
    slots={
        Slot.IMPORTS: '''from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash''',
        Slot.CONFIG: '''login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' ''',
        Slot.MODELS: '''
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
''',
        Slot.ROUTES: '''
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        user = User.query.filter_by(username=data.get('username')).first()
        if user and user.check_password(data.get('password')):
            login_user(user)
            return jsonify({"success": True, "user": user.username})
        return jsonify({"error": "Invalid credentials"}), 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"success": True})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() if request.is_json else request.form
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({"error": "Username taken"}), 400
    user = User(username=data['username'], email=data.get('email', ''))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"success": True}), 201
''',
    },
    requires_packages={
        "flask": ["flask-login", "werkzeug"],
        "fastapi": ["python-jose", "passlib", "python-multipart"],
    },
    config_keys=["SECRET_KEY"],
    priority=20,
))


register_feature(Feature(
    id="search",
    name="Search",
    description="Full-text search across records",
    requires_features=["database"],
    slots={
        Slot.ROUTES: '''
@app.route('/api/search')
def search():
    q = request.args.get('q', '')
    if not q:
        return jsonify([])
    # Simple LIKE search - upgrade to full-text for production
    results = Item.query.filter(Item.title.contains(q)).all()
    return jsonify([r.to_dict() for r in results])
''',
        Slot.HELPERS: '''
def search_items(query, fields=['title', 'description']):
    """Search items across multiple fields."""
    from sqlalchemy import or_
    conditions = [getattr(Item, f).contains(query) for f in fields if hasattr(Item, f)]
    return Item.query.filter(or_(*conditions)).all()
''',
    },
    priority=70,
))


register_feature(Feature(
    id="export",
    name="Data Export",
    description="Export data to CSV and JSON",
    requires_features=["database"],
    slots={
        Slot.IMPORTS: "import csv\nimport io",
        Slot.ROUTES: '''
@app.route('/api/export/json')
def export_json():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/export/csv')
def export_csv():
    items = Item.query.all()
    if not items:
        return "No data", 404
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=items[0].to_dict().keys())
    writer.writeheader()
    for item in items:
        writer.writerow(item.to_dict())
    
    response = app.response_class(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=export.csv'
    return response
''',
    },
    priority=80,
))


register_feature(Feature(
    id="realtime",
    name="Realtime Updates",
    description="WebSocket for live updates",
    slots={
        Slot.IMPORTS: "from flask_socketio import SocketIO, emit",
        Slot.CONFIG: '''socketio = SocketIO(app, cors_allowed_origins="*")''',
        Slot.ROUTES: '''
@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected!'})

@socketio.on('message')
def handle_message(data):
    emit('response', {'data': data}, broadcast=True)
''',
        Slot.MAIN: '''if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)''',
    },
    requires_packages={"flask": ["flask-socketio", "eventlet"]},
    priority=30,
))


register_feature(Feature(
    id="responsive_ui",
    name="Responsive UI",
    description="Mobile-friendly CSS layout",
    variants={
        "flask": {
            Slot.HELPERS: '''
# Responsive CSS injected into templates
RESPONSIVE_CSS = """
<style>
    @media (max-width: 768px) {
        .container { padding: 10px; }
        .card { margin: 5px 0; }
        table { display: block; overflow-x: auto; }
        .hide-mobile { display: none; }
    }
</style>
"""
''',
        },
        "html_canvas": {
            Slot.INIT: '''
// Responsive canvas
function resizeCanvas() {
    const ratio = Math.min(window.innerWidth / CONFIG.width, window.innerHeight / CONFIG.height);
    canvas.style.width = CONFIG.width * ratio + 'px';
    canvas.style.height = CONFIG.height * ratio + 'px';
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();
''',
        },
    },
    priority=40,
))


register_feature(Feature(
    id="game_loop",
    name="Game Loop",
    description="Animation frame-based game loop",
    variants={
        "html_canvas": {
            Slot.IMPORTS: '''
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
let lastTime = 0;
let running = true;
''',
            Slot.ROUTES: '''
function update(deltaTime) {
    // Update game state
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Draw game objects
}

function gameLoop(timestamp) {
    const deltaTime = timestamp - lastTime;
    lastTime = timestamp;
    
    if (running) {
        update(deltaTime);
        draw();
        requestAnimationFrame(gameLoop);
    }
}
''',
            Slot.MAIN: "requestAnimationFrame(gameLoop);",
        },
    },
    priority=50,
))


register_feature(Feature(
    id="input_handler",
    name="Input Handler",
    description="Keyboard and mouse/touch input handling",
    variants={
        "html_canvas": {
            Slot.IMPORTS: '''
const keys = {};
let mouseX = 0, mouseY = 0;
let mouseDown = false;
''',
            Slot.INIT: '''
// Keyboard
document.addEventListener('keydown', e => { keys[e.code] = true; e.preventDefault(); });
document.addEventListener('keyup', e => { keys[e.code] = false; });

// Mouse/Touch
canvas.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    mouseX = (e.clientX - rect.left) * (canvas.width / rect.width);
    mouseY = (e.clientY - rect.top) * (canvas.height / rect.height);
});
canvas.addEventListener('mousedown', () => mouseDown = true);
canvas.addEventListener('mouseup', () => mouseDown = false);

// Touch support
canvas.addEventListener('touchstart', e => {
    const touch = e.touches[0];
    const rect = canvas.getBoundingClientRect();
    mouseX = (touch.clientX - rect.left) * (canvas.width / rect.width);
    mouseY = (touch.clientY - rect.top) * (canvas.height / rect.height);
    mouseDown = true;
    e.preventDefault();
});
canvas.addEventListener('touchend', () => mouseDown = false);
''',
            Slot.HELPERS: '''
function isKeyPressed(code) { return !!keys[code]; }
function getMousePosition() { return { x: mouseX, y: mouseY }; }
''',
        },
    },
    priority=25,
))


register_feature(Feature(
    id="scoring",
    name="Scoring System",
    description="Score tracking and display",
    variants={
        "html_canvas": {
            Slot.IMPORTS: "let score = 0;\nlet highScore = parseInt(localStorage.getItem('highScore') || '0');",
            Slot.HELPERS: '''
function addScore(points) {
    score += points;
    if (score > highScore) {
        highScore = score;
        localStorage.setItem('highScore', highScore);
    }
}

function resetScore() { score = 0; }

function drawScore() {
    ctx.fillStyle = 'white';
    ctx.font = '24px monospace';
    ctx.fillText('Score: ' + score, 10, 30);
    ctx.fillText('High: ' + highScore, 10, 60);
}
''',
        },
    },
    priority=55,
))


register_feature(Feature(
    id="timer",
    name="Timer",
    description="Countdown or elapsed time tracking",
    variants={
        "html_canvas": {
            Slot.IMPORTS: '''
let timerStart = 0;
let timerDuration = 0;
let timerCallback = null;
''',
            Slot.HELPERS: '''
function startTimer(seconds, onComplete) {
    timerStart = Date.now();
    timerDuration = seconds * 1000;
    timerCallback = onComplete;
}

function getTimeLeft() {
    const elapsed = Date.now() - timerStart;
    const left = Math.max(0, timerDuration - elapsed);
    if (left === 0 && timerCallback) {
        timerCallback();
        timerCallback = null;
    }
    return Math.ceil(left / 1000);
}

function drawTimer() {
    const timeLeft = getTimeLeft();
    ctx.fillStyle = 'white';
    ctx.font = '20px monospace';
    ctx.fillText('Time: ' + timeLeft + 's', canvas.width - 120, 30);
}
''',
        },
    },
    priority=56,
))


# =====================================================================
# Feature Store API
# =====================================================================

class FeatureStore:
    """Manages features and resolves dependencies."""
    
    def __init__(self):
        self.features = FEATURES
    
    def get(self, feature_id: str) -> Optional[Feature]:
        """Get a feature by ID."""
        return self.features.get(feature_id)
    
    def list_all(self) -> List[Feature]:
        """List all features."""
        return list(self.features.values())
    
    def resolve_dependencies(self, feature_ids: List[str]) -> List[Feature]:
        """Resolve feature dependencies and return in order."""
        resolved = []
        visited = set()
        
        def visit(feature_id: str):
            if feature_id in visited:
                return
            visited.add(feature_id)
            
            feature = self.get(feature_id)
            if not feature:
                return
            
            # Visit dependencies first
            for dep_id in feature.requires_features:
                visit(dep_id)
            
            resolved.append(feature)
        
        for fid in feature_ids:
            visit(fid)
        
        return resolved
    
    def apply_features(self, renderer: TemplateRenderer, 
                       feature_ids: List[str], 
                       framework: str) -> List[str]:
        """Apply features to a template renderer. Returns required packages."""
        features = self.resolve_dependencies(feature_ids)
        packages = []
        
        for feature in features:
            # Inject slot content
            slots = feature.get_slots(framework)
            for slot, code in slots.items():
                if code:
                    renderer.inject(slot, code, priority=feature.priority, comment=feature.name)
            
            # Collect packages
            packages.extend(feature.get_packages(framework))
        
        return list(set(packages))


# Singleton
feature_store = FeatureStore()


# =====================================================================
# Usage Example
# =====================================================================

if __name__ == "__main__":
    from universal_template import TemplateRenderer, TemplateContext, Slot
    
    print("Feature Store Contents:")
    print("=" * 60)
    for f in feature_store.list_all():
        deps = f", requires: {f.requires_features}" if f.requires_features else ""
        print(f"  {f.id:15} - {f.name} {deps}")
    
    print("\n\nResolving dependencies for ['crud', 'search', 'auth']:")
    resolved = feature_store.resolve_dependencies(["crud", "search", "auth"])
    print("  Order:", [f.id for f in resolved])
    
    print("\n\nGenerating Flask app with features:")
    renderer = TemplateRenderer("flask")
    packages = feature_store.apply_features(renderer, ["database", "crud", "search"], "flask")
    
    context = TemplateContext(
        app_name="FeatureDemo",
        description="Demo app with database, CRUD, and search",
        framework="flask"
    )
    
    code = renderer.render(context)
    print(f"\nGenerated {len(code)} chars of code")
    print(f"Required packages: {packages}")
