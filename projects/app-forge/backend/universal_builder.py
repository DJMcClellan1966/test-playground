"""Universal App Builder - The Generalized Algorithm.

This is the evolution of App Forge from a game/CRUD builder to a 
universal application generator. The core insight:

    Description → Intent → Constraints → Components → Code

This pipeline works for ANY application type. The only things that
change are the categories, components, and framework generators.

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                    UniversalBuilder                      │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
    │  │ Category │→ │Constraint│→ │Component │→ │Framework│ │
    │  │ Registry │  │  Solver  │  │ Library  │  │Generator│ │
    │  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
    └─────────────────────────────────────────────────────────┘

Benefits:
- Same algorithm for games, APIs, ML pipelines, CLI tools
- Framework-agnostic component definitions
- Pluggable generators for any language/stack
- Constraint propagation reduces questions needed
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Type, Set, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from domain_parser import DomainModel
    from template_registry import Feature

# Import existing App Forge components (backward compatible)
try:
    from domain_parser import DomainModel, parse_description  # noqa: F811
    from template_registry import extract_features, Feature
    from intent_graph import IntentGraph
    _HAS_DOMAIN_PARSER = True
except ImportError:
    # Standalone mode
    _HAS_DOMAIN_PARSER = False
    parse_description = lambda x: []  # type: ignore[misc]
    extract_features = lambda x: {}  # type: ignore[misc]
    IntentGraph = None

# Import the 50 optimal training examples
try:
    from optimal_50 import (
        OPTIMAL_TRAINING_SET, TrainingExample, find_best_match,
        get_domain_fields, get_by_category, get_by_feature,
        Category as TrainingCategory
    )
    HAS_OPTIMAL_50 = True
except ImportError:
    HAS_OPTIMAL_50 = False
    OPTIMAL_TRAINING_SET = []
    find_best_match = lambda x: None
    get_domain_fields = lambda x: {}

# Import template synthesis for filling gaps
try:
    from template_synthesis import SmartSynthesizer, synthesize as synth_analyze
    HAS_SYNTHESIS = True
except ImportError:
    HAS_SYNTHESIS = False
    SmartSynthesizer = None
    synth_analyze = lambda x: {'all_fields': [], 'synthesized_templates': []}

# Import template updater for periodic improvements
try:
    from template_updater import updater as template_updater, start_background_updates
    HAS_UPDATER = True
except ImportError:
    HAS_UPDATER = False
    template_updater = None
    start_background_updates = lambda x=300: None


# =====================================================================
# Core Domain Objects
# =====================================================================

class AppCategory(Enum):
    """High-level application categories."""
    DATA_APP = "data_app"       # CRUD, collections, trackers
    GAME = "game"               # Browser games, interactive
    API_SERVICE = "api_service" # REST/GraphQL APIs
    ML_PIPELINE = "ml_pipeline" # Data science, ML models
    CLI_TOOL = "cli_tool"       # Command-line tools
    DESKTOP = "desktop"         # Desktop GUI apps
    MOBILE = "mobile"           # Mobile apps
    AUTOMATION = "automation"   # Scripts, bots, workflows


@dataclass
class Question:
    """A question to ask the user."""
    id: str
    text: str
    options: List[str] = field(default_factory=list)
    default: Optional[str] = None
    depends_on: Optional[str] = None  # Only ask if this feature present
    infers: Dict[str, Any] = field(default_factory=dict)  # Auto-set other answers


@dataclass
class Component:
    """A reusable piece of functionality."""
    id: str
    name: str
    description: str
    requires: List[str] = field(default_factory=list)   # Other component IDs
    provides: List[str] = field(default_factory=list)   # Capabilities this adds
    questions: List[Question] = field(default_factory=list)
    supported_frameworks: List[str] = field(default_factory=lambda: ["all"])
    

@dataclass
class ProjectFile:
    """A file to be generated."""
    path: str
    content: str
    executable: bool = False


@dataclass
class Project:
    """The final output - a complete project."""
    name: str
    category: AppCategory
    framework: str
    files: List[ProjectFile]
    run_command: str
    install_command: Optional[str] = None
    description: str = ""
    

# =====================================================================
# Abstract Base Classes (Extension Points)
# =====================================================================

class FrameworkGenerator(ABC):
    """Base class for all framework-specific code generators."""
    
    id: str = "base"
    name: str = "Base Generator"
    language: str = "python"
    categories: List[AppCategory] = []
    
    @abstractmethod
    def generate(self, 
                 app_name: str,
                 models: List[DomainModel],
                 components: List[Component],
                 answers: Dict[str, Any],
                 description: str) -> List[ProjectFile]:
        """Generate project files."""
        pass
    
    @abstractmethod
    def get_run_command(self, app_name: str) -> str:
        """Return the command to run the app."""
        pass
    
    def get_install_command(self) -> Optional[str]:
        """Return the command to install dependencies."""
        return None


class ComponentGenerator(ABC):
    """Base class for component-specific code generation."""
    
    component_id: str = "base"
    
    @abstractmethod
    def generate_for_framework(self, 
                               framework_id: str,
                               models: List[DomainModel],
                               answers: Dict[str, Any]) -> Dict[str, str]:
        """Generate code snippets for a specific framework.
        
        Returns dict of {snippet_name: code} that the framework generator
        can inject into its templates.
        """
        pass


# =====================================================================
# Basic Framework Generators
# =====================================================================

class FlaskGenerator(FrameworkGenerator):
    """Flask framework code generator."""
    
    id = "flask"
    name = "Flask"
    language = "python"
    categories = [AppCategory.DATA_APP, AppCategory.API_SERVICE, AppCategory.AUTOMATION]
    
    def generate(self, app_name: str, models: List[DomainModel], 
                 components: List[Component], answers: Dict[str, Any],
                 description: str) -> List[ProjectFile]:
        """Generate a Flask project."""
        # Generate models code
        models_code = self._generate_models(models)
        routes_code = self._generate_routes(models, answers)
        
        app_code = f'''"""
{app_name} - Generated by App Forge
{description}
"""
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

{models_code}

{routes_code}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
'''
        return [
            ProjectFile(path="app.py", content=app_code),
            ProjectFile(path="requirements.txt", content="flask\nflask-sqlalchemy"),
        ]
    
    def _generate_models(self, models: List[DomainModel]) -> str:
        lines = []
        for model in models:
            fields = ["    id = db.Column(db.Integer, primary_key=True)"]
            for f in model.fields:
                # Fields are tuples: (name, sql_type, nullable)
                if isinstance(f, tuple):
                    field_name, sql_type, nullable = f
                    fields.append(f"    {field_name} = db.Column({sql_type})")
                else:
                    # Fallback for other field formats
                    col_type = "db.String(200)" if getattr(f, 'type_hint', 'str') == "str" else "db.Integer"
                    fields.append(f"    {getattr(f, 'name', 'field')} = db.Column({col_type})")
            fields.append("    created_at = db.Column(db.DateTime, default=datetime.utcnow)")
            lines.append(f"class {model.name}(db.Model):\n" + "\n".join(fields))
        return "\n\n".join(lines) if lines else "# No models"
    
    def _generate_routes(self, models: List[DomainModel], answers: Dict[str, Any]) -> str:
        if not models:
            return """@app.route('/')
def index():
    return render_template('index.html')"""
        
        model = models[0]
        model_lower = model.name.lower()
        return f"""@app.route('/')
def index():
    items = {model.name}.query.all()
    return render_template('index.html', items=items)

@app.route('/add', methods=['POST'])
def add():
    item = {model.name}()
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    item = {model.name}.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('index'))"""
    
    def get_run_command(self, app_name: str) -> str:
        return "python app.py"
    
    def get_install_command(self) -> Optional[str]:
        return "pip install -r requirements.txt"


class CanvasGenerator(FrameworkGenerator):
    """HTML Canvas framework for games."""
    
    id = "canvas"
    name = "HTML Canvas"
    language = "javascript"
    categories = [AppCategory.GAME]
    
    def generate(self, app_name: str, models: List[DomainModel],
                 components: List[Component], answers: Dict[str, Any],
                 description: str) -> List[ProjectFile]:
        html_code = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name}</title>
    <style>
        body {{ display: flex; justify-content: center; align-items: center; 
               min-height: 100vh; margin: 0; background: #1a1a2e; }}
        canvas {{ border: 2px solid #333; background: #16213e; }}
        #score {{ color: white; font-family: monospace; font-size: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div>
        <div id="score">Score: 0</div>
        <canvas id="game" width="800" height="600"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('game');
        const ctx = canvas.getContext('2d');
        let score = 0;
        
        // Game loop
        function gameLoop() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            // Game logic here
            document.getElementById('score').textContent = 'Score: ' + score;
            requestAnimationFrame(gameLoop);
        }}
        gameLoop();
    </script>
</body>
</html>'''
        return [ProjectFile(path="index.html", content=html_code)]
    
    def get_run_command(self, app_name: str) -> str:
        return "open index.html"


class ClickGenerator(FrameworkGenerator):
    """Click CLI framework generator."""
    
    id = "click"
    name = "Click CLI"
    language = "python"
    categories = [AppCategory.CLI_TOOL]
    
    def generate(self, app_name: str, models: List[DomainModel],
                 components: List[Component], answers: Dict[str, Any],
                 description: str) -> List[ProjectFile]:
        cli_code = f'''"""
{app_name} - CLI Tool
{description}
"""
import click

@click.group()
def cli():
    """CLI tool generated by App Forge."""
    pass

@cli.command()
def run():
    """Run the main command."""
    click.echo("Running {app_name}...")

@cli.command()
@click.argument('name')
def greet(name):
    """Greet someone."""
    click.echo(f"Hello, {{name}}!")

if __name__ == '__main__':
    cli()
'''
        return [
            ProjectFile(path="cli.py", content=cli_code),
            ProjectFile(path="requirements.txt", content="click"),
        ]
    
    def get_run_command(self, app_name: str) -> str:
        return "python cli.py"


class FastAPIGenerator(FrameworkGenerator):
    """FastAPI framework generator for APIs."""
    
    id = "fastapi"
    name = "FastAPI"
    language = "python"
    categories = [AppCategory.API_SERVICE]
    
    def generate(self, app_name: str, models: List[DomainModel],
                 components: List[Component], answers: Dict[str, Any],
                 description: str) -> List[ProjectFile]:
        api_code = f'''"""
{app_name} - API
{description}
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="{app_name}")

# In-memory storage
db = []

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    
@app.get("/")
def root():
    return {{"message": "Welcome to {app_name}"}}
    
@app.get("/items", response_model=List[Item])
def list_items():
    return db
    
@app.post("/items", response_model=Item)
def create_item(item: Item):
    item.id = len(db) + 1
    db.append(item)
    return item

@app.delete("/items/{{item_id}}")
def delete_item(item_id: int):
    for i, item in enumerate(db):
        if item.id == item_id:
            db.pop(i)
            return {{"deleted": True}}
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        return [
            ProjectFile(path="main.py", content=api_code),
            ProjectFile(path="requirements.txt", content="fastapi\nuvicorn\npydantic"),
        ]
    
    def get_run_command(self, app_name: str) -> str:
        return "uvicorn main:app --reload"


class SklearnGenerator(FrameworkGenerator):
    """Scikit-learn ML pipeline generator."""
    
    id = "sklearn"
    name = "Scikit-learn"
    language = "python"
    categories = [AppCategory.ML_PIPELINE]
    
    def generate(self, app_name: str, models: List[DomainModel],
                 components: List[Component], answers: Dict[str, Any],
                 description: str) -> List[ProjectFile]:
        ml_code = f'''"""
{app_name} - ML Pipeline
{description}
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

def load_data():
    """Load and prepare data."""
    # Replace with your data loading
    X = np.random.randn(100, 4)
    y = np.random.randint(0, 2, 100)
    return X, y

def train_model(X, y):
    """Train the ML model."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    print(classification_report(y_test, y_pred))
    
    return model, scaler

if __name__ == "__main__":
    X, y = load_data()
    model, scaler = train_model(X, y)
    print("Model trained successfully!")
'''
        return [
            ProjectFile(path="pipeline.py", content=ml_code),
            ProjectFile(path="requirements.txt", content="pandas\nnumpy\nscikit-learn"),
        ]
    
    def get_run_command(self, app_name: str) -> str:
        return "python pipeline.py"


# =====================================================================
# Constraint Solver
# =====================================================================

class ConstraintSolver:
    """Propagates constraints to reduce questions and ensure consistency."""
    
    # Rules: if X is true, then Y is also true
    IMPLICATIONS = [
        # Auth requirements
        ("multi_user", "needs_auth"),
        ("needs_auth", "has_data"),
        ("user_profiles", "needs_auth"),
        ("social_features", "multi_user"),
        
        # Data requirements
        ("search", "has_data"),
        ("export", "has_data"),
        ("import", "has_data"),
        ("analytics", "has_data"),
        
        # Realtime
        ("multiplayer", "realtime"),
        ("live_updates", "realtime"),
        ("chat", "realtime"),
        
        # ML implies certain things
        ("ml_features", "has_data"),
        ("ml_features", "python_preferred"),
        
        # Mobile
        ("offline_mode", "local_storage"),
        ("push_notifications", "mobile_or_pwa"),
    ]
    
    # Conflicts: if X is true, Y cannot be true
    CONFLICTS = [
        ("single_user", "multi_user"),
        ("offline_only", "realtime"),
        ("cli_only", "web_ui"),
    ]
    
    def propagate(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Apply constraint propagation rules."""
        result = dict(answers)
        changed = True
        
        while changed:
            changed = False
            for source, target in self.IMPLICATIONS:
                if result.get(source) and not result.get(target):
                    result[target] = True
                    changed = True
        
        return result
    
    def check_conflicts(self, answers: Dict[str, Any]) -> List[str]:
        """Return list of conflicting pairs."""
        conflicts = []
        for a, b in self.CONFLICTS:
            if answers.get(a) and answers.get(b):
                conflicts.append(f"{a} conflicts with {b}")
        return conflicts
    
    def get_skippable_questions(self, answers: Dict[str, Any]) -> List[str]:
        """Return question IDs that don't need to be asked."""
        skip = []
        propagated = self.propagate(answers)
        
        # Skip questions whose answers are already determined
        for key, value in propagated.items():
            if key not in answers:
                skip.append(key)
        
        return skip


# =====================================================================
# The Universal Builder
# =====================================================================

class UniversalBuilder:
    """The core algorithm for building any app type."""
    
    def __init__(self):
        self.category_registry: Dict[AppCategory, 'CategoryConfig'] = {}
        self.component_library: Dict[str, Component] = {}
        self.framework_generators: Dict[str, FrameworkGenerator] = {}
        self.component_generators: Dict[str, ComponentGenerator] = {}
        self.constraint_solver = ConstraintSolver()
        self.intent_graph = IntentGraph() if IntentGraph else None
        
        # Template synthesis for filling gaps
        self.synthesizer = SmartSynthesizer() if HAS_SYNTHESIS else None
        
        # Template updater for learning and improvement
        self.updater = template_updater if HAS_UPDATER else None
        
        # Register built-ins
        self._register_defaults()
    
    def build(self, description: str, answers: Optional[Dict[str, Any]] = None) -> Project:
        """The universal build pipeline."""
        answers = answers or {}
        
        # 1. INTENT EXTRACTION
        category = self.categorize(description)
        features = extract_features(description)
        
        # 1.5. TRAINING SET LOOKUP (use optimal 50 for domain knowledge)
        training_match = self._lookup_training_example(description)
        training_inferences = {}
        if training_match:
            # Inherit features and framework from best training example
            training_inferences = self._infer_from_training(training_match)
        
        # 1.6. TEMPLATE SYNTHESIS (fill gaps for novel concepts)
        synthesis_result = {}
        if self.synthesizer:
            synthesis_result = synth_analyze(description)
        
        # 2. FRAMEWORK SELECTION
        # Prefer training example's framework if matched
        if training_match and 'framework' not in answers:
            answers['framework'] = training_match.framework
        framework_id = self.select_framework(category, answers, features)
        
        # Fallback to flask if framework not registered
        if framework_id not in self.framework_generators:
            framework_id = "flask"
        generator = self.framework_generators[framework_id]
        
        # 3. DOMAIN MODELING
        models = parse_description(description) if parse_description else []
        
        # 3.5. ENRICH MODELS WITH SYNTHESIZED FIELDS
        if synthesis_result.get('all_fields'):
            self._enrich_models_with_fields(models, synthesis_result['all_fields'])
        
        # 4. CONSTRAINT PROPAGATION
        inferred = self._infer_from_features(features)
        combined = {**training_inferences, **inferred, **answers}
        propagated = self.constraint_solver.propagate(combined)
        
        # 5. COMPONENT SELECTION
        components = self.select_components(category, propagated, features)
        
        # 6. CODE GENERATION
        files = generator.generate(
            app_name=self._extract_name(description),
            models=models,
            components=components,
            answers=propagated,
            description=description
        )
        
        # 7. RECORD BUILD FOR LEARNING
        template_id = training_match.id if training_match else 'unknown'
        feature_list = list(features.keys())
        field_list = synthesis_result.get('all_fields', [])
        self._record_build(description, template_id, feature_list, field_list)
        
        return Project(
            name=self._extract_name(description),
            category=category,
            framework=framework_id,
            files=files,
            run_command=generator.get_run_command(self._extract_name(description)),
            install_command=generator.get_install_command(),
            description=description
        )
    
    def _record_build(self, description: str, template_id: str,
                      features: List[str], fields: List[str], success: bool = True):
        """Record build for template learning."""
        if self.updater:
            try:
                self.updater.record_build(description, template_id, features, fields, success)
            except Exception:
                pass  # Don't fail builds due to recording errors
    
    def get_questions(self, description: str, 
                      answered: Optional[Dict[str, Any]] = None) -> List[Question]:
        """Get remaining questions to ask, after inference and propagation."""
        answered = answered or {}
        
        # Categorize and extract features
        category = self.categorize(description)
        features = extract_features(description)
        
        # Get category-specific questions
        config = self.category_registry.get(category)
        if not config:
            return []
        
        # Infer from features
        inferred = self._infer_from_features(features)
        combined = {**inferred, **answered}
        propagated = self.constraint_solver.propagate(combined)
        
        # Get component questions
        components = self.select_components(category, propagated, features)
        component_questions = []
        for comp in components:
            component_questions.extend(comp.questions)
        
        # Filter out already-answered questions
        all_questions = config.questions + component_questions
        remaining = []
        for q in all_questions:
            if q.id not in propagated:
                # Check dependencies
                if q.depends_on is None or propagated.get(q.depends_on):
                    remaining.append(q)
        
        return remaining
    
    def categorize(self, description: str) -> AppCategory:
        """Determine the high-level category of the app."""
        desc_lower = description.lower()
        
        # Use intent graph if available
        if self.intent_graph:
            activated = self.intent_graph.activate(desc_lower)
            # Map activated concepts to categories
            if "game" in activated or "play" in activated:
                return AppCategory.GAME
            if "api" in activated or "endpoint" in activated:
                return AppCategory.API_SERVICE
            if "ml" in activated or "model" in activated or "predict" in activated:
                return AppCategory.ML_PIPELINE
            if "cli" in activated or "command" in activated or "terminal" in activated:
                return AppCategory.CLI_TOOL
        
        # Fallback: keyword matching
        category_keywords = {
            AppCategory.GAME: ["game", "play", "score", "level", "puzzle", "quiz",
                               "wordle", "dice", "reaction", "reflex", "tetris", 
                               "sudoku", "snake", "pong", "tic tac", "hangman", 
                               "memory", "match", "minesweeper", "cards"],
            AppCategory.API_SERVICE: ["api", "endpoint", "rest", "graphql", "service", "backend"],
            AppCategory.ML_PIPELINE: ["ml", "machine learning", "model", "predict", "train", "dataset",
                                       "classifier", "sentiment", "recommendation", "spam", "image classif"],
            # AUTOMATION must come before CLI_TOOL - requires explicit "automation" or phrases like "backup automation"
            AppCategory.AUTOMATION: ["automation script", "backup automation", "file backup automation",
                                      "monitoring script", "price monitoring",
                                      "automate", "bot", "schedule", "workflow", 
                                      "scrape", "scraper", "web scraper", "sync job"],
            AppCategory.CLI_TOOL: ["cli", "command", "terminal", "tool", "script",
                                    "password gen", "file converter", "backup script", "file backup script"],
            AppCategory.DESKTOP: ["desktop", "gui", "window", "native"],
            AppCategory.MOBILE: ["mobile", "ios", "android", "app store"],
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                return category
        
        # Default to data app
        return AppCategory.DATA_APP
    
    def select_framework(self, category: AppCategory, 
                         answers: Dict[str, Any],
                         features: Dict[str, Feature]) -> str:
        """Select the best framework for this app."""
        # User preference takes priority
        if "framework" in answers:
            return answers["framework"]
        
        # Category-based defaults
        category_defaults = {
            AppCategory.DATA_APP: "flask",
            AppCategory.GAME: "canvas",
            AppCategory.API_SERVICE: "fastapi",
            AppCategory.ML_PIPELINE: "sklearn",
            AppCategory.CLI_TOOL: "click",
            AppCategory.DESKTOP: "flask",  # Fallback to flask
            AppCategory.MOBILE: "flask",   # Fallback to flask
            AppCategory.AUTOMATION: "flask",  # Fallback to flask
        }
        
        default = category_defaults.get(category, "flask")
        
        # Feature-based adjustments
        if features.get("async"):
            if default == "flask":
                default = "fastapi"
        if features.get("realtime"):
            if default == "flask":
                default = "flask_socketio"
        
        return default
    
    def select_components(self, category: AppCategory,
                          answers: Dict[str, Any],
                          features: Dict[str, Feature]) -> List[Component]:
        """Select which components to include."""
        selected = []
        
        # Always-included components per category
        category_base = {
            AppCategory.DATA_APP: ["crud"],
            AppCategory.GAME: ["game_loop"],
            AppCategory.API_SERVICE: ["endpoints"],
            AppCategory.ML_PIPELINE: ["data_loader", "model"],
            AppCategory.CLI_TOOL: ["commands"],
            AppCategory.AUTOMATION: ["scheduler"],
        }
        
        for comp_id in category_base.get(category, []):
            if comp_id in self.component_library:
                selected.append(self.component_library[comp_id])
        
        # Feature-based components
        feature_components = {
            "needs_auth": "auth",
            "search": "search",
            "export": "export",
            "import": "import_data",
            "realtime": "websocket",
            "notifications": "notifications",
            "file_upload": "file_upload",
            "charts": "charts",
            "ml_features": "ml_integration",
        }
        
        for feature, comp_id in feature_components.items():
            if answers.get(feature) or features.get(feature):
                if comp_id in self.component_library:
                    comp = self.component_library[comp_id]
                    if comp not in selected:
                        selected.append(comp)
        
        # Resolve dependencies
        return self._resolve_dependencies(selected)
    
    def _resolve_dependencies(self, components: List[Component]) -> List[Component]:
        """Add any missing dependencies and sort topologically."""
        all_ids = {c.id for c in components}
        result = list(components)
        
        # Add missing dependencies
        changed = True
        while changed:
            changed = False
            for comp in list(result):
                for req_id in comp.requires:
                    if req_id not in all_ids and req_id in self.component_library:
                        result.append(self.component_library[req_id])
                        all_ids.add(req_id)
                        changed = True
        
        # Simple topological sort (dependencies first)
        def sort_key(c):
            return len([r for r in c.requires if r in all_ids])
        
        return sorted(result, key=sort_key)
    
    def _infer_from_features(self, features: Dict[str, Feature]) -> Dict[str, Any]:
        """Convert extracted features to answer values."""
        inferred = {}
        
        # Map feature names to answer keys
        feature_map = {
            "auth": "needs_auth",
            "storage": "has_data", 
            "data_app": "has_data",
            "search": "search",
            "export": "export",
            "realtime": "realtime",
            "mobile": "responsive",
            "social": "multi_user",
        }
        
        for feat_name, answer_key in feature_map.items():
            if feat_name in features:
                inferred[answer_key] = True
        
        return inferred
    
    def _extract_name(self, description: str) -> str:
        """Extract an app name from description."""
        words = description.lower().split()
        
        # Remove common words
        skip = {"a", "an", "the", "my", "simple", "basic", "app", "application", 
                "create", "build", "make", "want", "need", "for", "to", "that", "with"}
        
        meaningful = [w for w in words[:5] if w not in skip and len(w) > 2]
        
        if meaningful:
            return meaningful[0].title() + "App"
        return "MyApp"
    
    # =====================================================================
    # Training Set & Synthesis Integration
    # =====================================================================
    
    def _lookup_training_example(self, description: str) -> Optional['TrainingExample']:
        """Find the best matching training example from optimal 50."""
        if not HAS_OPTIMAL_50:
            return None
        return find_best_match(description)
    
    def _infer_from_training(self, example: 'TrainingExample') -> Dict[str, Any]:
        """Extract answers/features from a training example."""
        inferred = {}
        
        # Map training features to answer keys
        feature_map = {
            'auth': 'needs_auth',
            'search': 'search',
            'tags': 'tags',
            'ratings': 'ratings',
            'comments': 'comments',
            'share': 'share',
            'export': 'export',
            'history': 'history',
            'stats': 'stats',
            'notifications': 'notifications',
        }
        
        for feat in example.features:
            if feat in feature_map:
                inferred[feature_map[feat]] = True
        
        # Database requirement
        if example.needs_database:
            inferred['has_data'] = True
        
        # Complexity hints
        if example.complexity.value in ('moderate', 'complex'):
            inferred['multi_feature'] = True
        
        return inferred
    
    def _enrich_models_with_fields(self, models: List, synthesized_fields: List[str]):
        """Add synthesized fields to existing models."""
        if not models or not synthesized_fields:
            return
        
        # Add to first model (main entity)
        main_model = models[0]
        if hasattr(main_model, 'fields'):
            # Get existing field names (handle various field formats)
            existing = set()
            for f in main_model.fields:
                if isinstance(f, tuple):
                    existing.add(f[0])  # First element is field name
                elif isinstance(f, dict):
                    existing.add(f.get('name', ''))
                elif hasattr(f, 'name'):
                    existing.add(f.name)
            
            for field_name in synthesized_fields:
                if field_name not in existing:
                    # Add as tuple to match existing format
                    main_model.fields.append((field_name, 'db.String(200)', True))
    
    def get_domain_fields_for(self, entity: str) -> Dict[str, str]:
        """Get domain-specific fields from optimal training set."""
        if HAS_OPTIMAL_50:
            return get_domain_fields(entity)
        return {}
    
    def get_synthesis_info(self, description: str) -> Dict:
        """Get info about what would be synthesized for a description."""
        result = {
            'training_match': None,
            'synthesized_templates': [],
            'all_fields': [],
            'confidence': 0.0,
        }
        
        # Training lookup
        match = self._lookup_training_example(description)
        if match:
            result['training_match'] = {
                'id': match.id,
                'description': match.description,
                'category': match.category.value,
                'complexity': match.complexity.value,
                'features': list(match.features),
                'domain_fields': list(match.domain_fields.keys()),
            }
            result['confidence'] = 0.85  # Training match is high confidence
        
        # Synthesis
        if self.synthesizer:
            synth = synth_analyze(description)
            result['synthesized_templates'] = synth.get('synthesized_templates', [])
            result['all_fields'] = synth.get('all_fields', [])
            
            # Adjust confidence based on synthesis
            if synth.get('synthesized_details'):
                avg_conf = sum(d['confidence'] for d in synth['synthesized_details']) / len(synth['synthesized_details'])
                if not match:
                    result['confidence'] = avg_conf
        
        return result
    
    # =====================================================================
    # Registry Methods
    # =====================================================================
    
    def register_category(self, config: 'CategoryConfig'):
        """Register a category configuration."""
        self.category_registry[config.category] = config
    
    def register_component(self, component: Component):
        """Register a reusable component."""
        self.component_library[component.id] = component
    
    def register_framework(self, generator: FrameworkGenerator):
        """Register a framework generator."""
        self.framework_generators[generator.id] = generator
    
    def register_component_generator(self, gen: ComponentGenerator):
        """Register a component-specific generator."""
        self.component_generators[gen.component_id] = gen
    
    def _register_defaults(self):
        """Register default components and categories."""
        # Register framework generators
        self.register_framework(FlaskGenerator())
        self.register_framework(CanvasGenerator())
        self.register_framework(ClickGenerator())
        self.register_framework(FastAPIGenerator())
        self.register_framework(SklearnGenerator())
    
    # =====================================================================
    # Updater Management
    # =====================================================================
    
    def start_learning(self, interval_seconds: int = 300):
        """Start background template learning/updates."""
        if self.updater:
            self.updater.start_background(interval_seconds)
    
    def stop_learning(self):
        """Stop background template learning."""
        if self.updater:
            self.updater.stop_background()
    
    def run_update_now(self):
        """Run a template update cycle immediately."""
        if self.updater:
            return self.updater.run_update()
        return None
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get template learning statistics."""
        if self.updater:
            return self.updater.get_statistics()
        return {'status': 'updater not available'}
    
    def suggest_fields_for(self, existing_fields: List[str]) -> List[str]:
        """Get field suggestions based on learned co-occurrence patterns."""
        if self.updater:
            return self.updater.suggest_fields(existing_fields)
        return []
    
    def predict_template_for(self, description: str) -> List[Tuple[str, float]]:
        """Predict likely templates from learned patterns."""
        if self.updater:
            return self.updater.predict_template(description)
        return []


@dataclass
class CategoryConfig:
    """Configuration for an app category."""
    category: AppCategory
    name: str
    description: str
    default_framework: str
    supported_frameworks: List[str]
    questions: List[Question] = field(default_factory=list)
    base_components: List[str] = field(default_factory=list)


# =====================================================================
# Singleton instance
# =====================================================================

universal_builder = UniversalBuilder()


# =====================================================================
# Convenience functions
# =====================================================================

def _ensure_registered():
    """Import registries to trigger auto-registration."""
    try:
        import framework_registry  # Registers generators
        import component_library   # Registers components
        import category_registry   # Registers categories
    except ImportError:
        pass  # Standalone mode - manual registration needed


def build_app(description: str, answers: Optional[Dict[str, Any]] = None) -> Project:
    """Build an app from a description."""
    _ensure_registered()
    return universal_builder.build(description, answers)


def get_questions(description: str, answered: Optional[Dict[str, Any]] = None) -> List[Question]:
    """Get questions to ask for a description."""
    return universal_builder.get_questions(description, answered)


def categorize(description: str) -> AppCategory:
    """Categorize a description."""
    return universal_builder.categorize(description)


# =====================================================================
# Example usage
# =====================================================================

if __name__ == "__main__":
    # Test categorization
    test_descriptions = [
        "a recipe collection app",
        "a snake game",
        "a REST API for user management",
        "a machine learning model to predict house prices",
        "a CLI tool for file conversion",
        "a bot that scrapes news sites",
    ]
    
    print("Category Detection Test")
    print("=" * 50)
    for desc in test_descriptions:
        cat = categorize(desc)
        print(f"'{desc}' → {cat.value}")
    
    # Test training set lookup + synthesis
    print("\n" + "=" * 50)
    print("Training Set + Synthesis Integration Test")
    print("=" * 50)
    
    test_cases = [
        "a recipe app with ratings",
        "a workout tracker with exercise history",
        "a budget manager with expense categories",
        "a photo gallery with location data",
    ]
    
    for desc in test_cases:
        print(f"\n'{desc}'")
        info = universal_builder.get_synthesis_info(desc)
        
        if info['training_match']:
            tm = info['training_match']
            print(f"  Training Match: {tm['id']} ({tm['category']}, {tm['complexity']})")
            print(f"    Features: {tm['features']}")
            print(f"    Domain Fields: {tm['domain_fields'][:4]}...")
        
        if info['synthesized_templates']:
            print(f"  Synthesized: {info['synthesized_templates']}")
        
        if info['all_fields']:
            print(f"  All Fields: {info['all_fields'][:5]}...")
        
        print(f"  Confidence: {info['confidence']:.0%}")
