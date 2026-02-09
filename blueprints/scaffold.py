"""
Blueprint Scaffolder - Generate project structure from blueprints.

Reads a blueprint file and generates a complete project skeleton with:
- Directory structure from File Structure section
- Model stubs from Data Model section
- Starter code with TODO comments pointing to blueprint
- README customized for the project

With --generate flag:
- Uses Ollama to generate ACTUAL working code
- Implements models, routes, and components based on blueprint spec
- Creates a runnable application, not just stubs

Usage:
    python scaffold.py learning-app --name MyBookTracker
    python scaffold.py task-manager --name TodoMaster --stack flask
    python scaffold.py learning-app --name MyApp --generate  # LLM-powered!
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add socratic-learner to path for llm_client
SOCRATIC_PATH = Path(__file__).parent.parent / "projects" / "socratic-learner"
sys.path.insert(0, str(SOCRATIC_PATH))


# Path to blueprints directory
BLUEPRINTS_DIR = Path(__file__).parent
OUTPUT_DIR = Path(__file__).parent.parent / "projects"


# ============================================================================
# STACK TEMPLATES - Starter code for different tech stacks
# ============================================================================

STACK_TEMPLATES = {
    # ----- Python Flask -----
    "flask": {
        "extension": ".py",
        "app_entry": '''"""
{project_name} - Flask Application

Generated from: {blueprint_name} blueprint
See: blueprints/{blueprint_file} for full specification
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# TODO: Configure database (see Data Model section in blueprint)
# TODO: Add authentication (see User Types section)


@app.route("/")
def index():
    """Home page."""
    return render_template("index.html")


@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({{"status": "ok", "app": "{project_name}"}})


# TODO: Add routes for each User Flow in the blueprint

if __name__ == "__main__":
    app.run(debug=True, port=5000)
''',
        "model": '''"""
{model_name} model.

See Data Model section in blueprints/{blueprint_file}
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import uuid4


@dataclass
class {model_name}:
    """
    {model_name} entity.
    
    Fields from blueprint:
{fields_commented}
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    # TODO: Add remaining fields from blueprint
''',
        "route": '''"""
{name} routes.

See User Flows section in blueprints/{blueprint_file}
"""

from flask import Blueprint, request, jsonify

{name_lower}_bp = Blueprint("{name_lower}", __name__, url_prefix="/{name_lower}")


@{name_lower}_bp.route("/", methods=["GET"])
def list_{name_lower}():
    """List all {name_lower} items."""
    # TODO: Implement - see blueprint for expected behavior
    return jsonify([])


@{name_lower}_bp.route("/<id>", methods=["GET"])
def get_{name_lower}(id):
    """Get a single {name_lower} by ID."""
    # TODO: Implement
    return jsonify({{"id": id}})


@{name_lower}_bp.route("/", methods=["POST"])
def create_{name_lower}():
    """Create a new {name_lower}."""
    data = request.get_json()
    # TODO: Validate and create
    return jsonify(data), 201


@{name_lower}_bp.route("/<id>", methods=["PUT"])
def update_{name_lower}(id):
    """Update a {name_lower}."""
    data = request.get_json()
    # TODO: Implement
    return jsonify({{"id": id, **data}})


@{name_lower}_bp.route("/<id>", methods=["DELETE"])
def delete_{name_lower}(id):
    """Delete a {name_lower}."""
    # TODO: Implement
    return "", 204
''',
        "requirements": '''# {project_name} dependencies
# Generated from {blueprint_name} blueprint

flask>=3.0.0
flask-cors>=4.0.0
python-dotenv>=1.0.0

# Database (choose one and uncomment)
# flask-sqlalchemy>=3.0.0  # SQL databases
# tinydb>=4.8.0  # Simple JSON file database

# Optional features (uncomment as needed)
# flask-login>=0.6.0  # User authentication
# flask-wtf>=1.2.0  # Form handling
# celery>=5.3.0  # Background tasks
''',
    },
    
    # ----- Python FastAPI -----
    "fastapi": {
        "extension": ".py",
        "app_entry": '''"""
{project_name} - FastAPI Application

Generated from: {blueprint_name} blueprint
See: blueprints/{blueprint_file} for full specification
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="{project_name}",
    description="Generated from {blueprint_name} blueprint",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {{"message": "Welcome to {project_name}"}}


@app.get("/health")
async def health():
    """Health check."""
    return {{"status": "ok"}}


# TODO: Add routers for each feature category in blueprint
# from .routes import tasks, users
# app.include_router(tasks.router)
''',
        "model": '''"""
{model_name} model.

See Data Model section in blueprints/{blueprint_file}
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import uuid4


class {model_name}Base(BaseModel):
    """Base schema for {model_name}."""
    # TODO: Add fields from blueprint
    pass


class {model_name}Create({model_name}Base):
    """Schema for creating {model_name}."""
    pass


class {model_name}({model_name}Base):
    """
    Full {model_name} schema.
    
    Fields from blueprint:
{fields_commented}
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
''',
        "requirements": '''# {project_name} dependencies
# Generated from {blueprint_name} blueprint

fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
python-dotenv>=1.0.0

# Database (choose one)
# sqlalchemy>=2.0.0
# databases>=0.8.0

# Optional
# python-jose[cryptography]>=3.3.0  # JWT auth
# passlib[bcrypt]>=1.7.4  # Password hashing
''',
    },
    
    # ----- JavaScript/React -----
    "react": {
        "extension": ".jsx",
        "app_entry": '''/**
 * {project_name} - React Application
 * 
 * Generated from: {blueprint_name} blueprint
 * See: blueprints/{blueprint_file} for full specification
 */

import React from 'react';
import {{ BrowserRouter, Routes, Route }} from 'react-router-dom';
import './styles/globals.css';

// TODO: Import components for each screen in blueprint
// import LibraryView from './components/Library/LibraryView';

function App() {{
  return (
    <BrowserRouter>
      <div className="app">
        {{/* TODO: Add navigation based on Screens section in blueprint */}}
        <main>
          <Routes>
            <Route path="/" element={{<div>Welcome to {project_name}</div>}} />
            {{/* TODO: Add routes for each screen */}}
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}}

export default App;
''',
        "component": '''/**
 * {name} Component
 * 
 * See Screens section in blueprints/{blueprint_file}
 */

import React from 'react';

// TODO: Define props based on data model
// interface {name}Props {{}}

function {name}({{ /* props */ }}) {{
  // TODO: Add state and handlers per blueprint

  return (
    <div className="{name_lower}">
      <h2>{name}</h2>
      {{/* TODO: Implement based on blueprint specification */}}
    </div>
  );
}}

export default {name};
''',
        "hook": '''/**
 * use{name} hook
 * 
 * See Feature Categories in blueprints/{blueprint_file}
 */

import {{ useState, useCallback }} from 'react';

export function use{name}() {{
  // TODO: Add state based on data model
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetch{name} = useCallback(async () => {{
    setLoading(true);
    // TODO: Implement data fetching
    setLoading(false);
  }}, []);

  const create{name} = useCallback(async (data) => {{
    // TODO: Implement creation
  }}, []);

  return {{
    items,
    loading,
    fetch{name},
    create{name},
  }};
}}
''',
        "package_json": '''{{
  "name": "{project_name_lower}",
  "version": "0.1.0",
  "description": "Generated from {blueprint_name} blueprint",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0"
  }},
  "devDependencies": {{
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }}
}}
''',
    },
    
    # ----- Node.js Express -----
    "express": {
        "extension": ".js",
        "app_entry": '''/**
 * {project_name} - Express API
 * 
 * Generated from: {blueprint_name} blueprint
 * See: blueprints/{blueprint_file} for full specification
 */

const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {{
  res.json({{ status: 'ok', app: '{project_name}' }});
}});

// TODO: Add routes for each user flow in blueprint
// const tasksRouter = require('./routes/tasks');
// app.use('/api/tasks', tasksRouter);

// Error handler
app.use((err, req, res, next) => {{
  console.error(err.stack);
  res.status(500).json({{ error: 'Something went wrong!' }});
}});

app.listen(PORT, () => {{
  console.log(`{project_name} running on port ${{PORT}}`);
}});
''',
        "model": '''/**
 * {model_name} model
 * 
 * See Data Model section in blueprints/{blueprint_file}
 * 
 * Fields from blueprint:
{fields_commented}
 */

// Using simple in-memory storage - replace with real database
let {name_lower}s = [];
let nextId = 1;

const {model_name} = {{
  findAll: () => {name_lower}s,
  
  findById: (id) => {name_lower}s.find(item => item.id === id),
  
  create: (data) => {{
    const item = {{
      id: String(nextId++),
      ...data,
      createdAt: new Date().toISOString(),
    }};
    {name_lower}s.push(item);
    return item;
  }},
  
  update: (id, data) => {{
    const index = {name_lower}s.findIndex(item => item.id === id);
    if (index === -1) return null;
    {name_lower}s[index] = {{ ...{name_lower}s[index], ...data }};
    return {name_lower}s[index];
  }},
  
  delete: (id) => {{
    const index = {name_lower}s.findIndex(item => item.id === id);
    if (index === -1) return false;
    {name_lower}s.splice(index, 1);
    return true;
  }},
}};

module.exports = {model_name};
''',
        "route": '''/**
 * {name} routes
 * 
 * See User Flows section in blueprints/{blueprint_file}
 */

const express = require('express');
const router = express.Router();
// const {name} = require('../models/{name_lower}');

// GET all
router.get('/', async (req, res) => {{
  // TODO: Implement - see blueprint for expected behavior
  res.json([]);
}});

// GET by ID
router.get('/:id', async (req, res) => {{
  // TODO: Implement
  res.json({{ id: req.params.id }});
}});

// POST create
router.post('/', async (req, res) => {{
  // TODO: Validate and create
  res.status(201).json(req.body);
}});

// PUT update
router.put('/:id', async (req, res) => {{
  // TODO: Implement
  res.json({{ id: req.params.id, ...req.body }});
}});

// DELETE
router.delete('/:id', async (req, res) => {{
  // TODO: Implement
  res.status(204).send();
}});

module.exports = router;
''',
        "package_json": '''{{
  "name": "{project_name_lower}",
  "version": "0.1.0",
  "description": "Generated from {blueprint_name} blueprint",
  "main": "src/index.js",
  "scripts": {{
    "start": "node src/index.js",
    "dev": "nodemon src/index.js"
  }},
  "dependencies": {{
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.0"
  }},
  "devDependencies": {{
    "nodemon": "^3.0.0"
  }}
}}
''',
    },
}


# ============================================================================
# LLM CODE GENERATION
# ============================================================================

def get_llm_client():
    """Import and return the LLM call function."""
    try:
        import config
        from llm_client import call_llm
        return call_llm, config
    except ImportError:
        print("⚠️  LLM client not available. Install socratic-learner or run without --generate")
        return None, None


CODE_GEN_SYSTEM = """You are an expert {stack} developer generating production-ready code.

RULES:
- Generate complete, working code - not stubs or pseudocode
- Follow best practices for {stack}
- Include proper error handling
- Add brief docstrings/comments explaining key logic
- Use the exact field names and types from the data model
- Make the code immediately runnable

Do NOT include:
- Markdown formatting or code blocks
- Explanations outside the code
- TODO comments (implement everything)

Output ONLY the code, nothing else."""


MODEL_GEN_PROMPT = """Generate a complete {stack} model for: {model_name}

DATA MODEL FROM BLUEPRINT:
{fields}

REQUIREMENTS:
- Implement all fields with proper types
- Add CRUD operations (create, read, update, delete)
- Include validation where appropriate
- For Python: use dataclasses or Pydantic
- For JS: include proper exports

Generate the complete implementation:"""


ROUTE_GEN_PROMPT = """Generate complete {stack} routes for: {entity_name}

DATA MODEL:
{model_spec}

FEATURE REQUIREMENTS (from blueprint):
{features}

IMPLEMENTATION:
- Full CRUD endpoints
- Proper request validation
- Error handling with appropriate status codes
- JSON responses

Generate the complete route file:"""


APP_GEN_PROMPT = """Generate the main {stack} application entry point.

PROJECT: {project_name}
BLUEPRINT: {blueprint_title}

ENTITIES TO MANAGE:
{entities}

KEY FEATURES:
{features}

REQUIREMENTS:
- Import and register all route modules
- Configure middleware (CORS, JSON parsing)
- Set up error handling
- Include health check endpoint
- For Flask: use blueprints for routes
- For Express: use Router

Generate the complete app file:"""


COMPONENT_GEN_PROMPT = """Generate a complete React component: {component_name}

PURPOSE: {purpose}

DATA IT DISPLAYS:
{data_model}

RELATED FEATURES:
{features}

REQUIREMENTS:
- Functional component with hooks
- Proper TypeScript/prop types if applicable
- Handle loading and error states
- Include basic styling classes

Generate the complete component:"""


class LLMCodeGenerator:
    """Generate actual code using LLM based on blueprint specifications."""
    
    def __init__(self, blueprint: Dict, stack: str, project_name: str):
        self.blueprint = blueprint
        self.stack = stack
        self.project_name = project_name
        
        self.call_llm, self.config = get_llm_client()
        if not self.call_llm:
            raise RuntimeError("LLM client not available")
        
        # Increase token limit for code generation
        self._original_predict = self.config.OLLAMA_NUM_PREDICT
        self.config.OLLAMA_NUM_PREDICT = 2000
    
    def __del__(self):
        """Restore original config."""
        if hasattr(self, 'config') and self.config:
            self.config.OLLAMA_NUM_PREDICT = getattr(self, '_original_predict', 1000)
    
    def _get_section(self, name: str) -> str:
        """Get a blueprint section by partial name match."""
        for section_name, content in self.blueprint.get("sections", {}).items():
            if name.lower() in section_name.lower():
                return content
        return ""
    
    def _clean_code(self, code: str) -> str:
        """Remove markdown formatting if LLM added any, and check for errors."""
        # Check for error messages from LLM client
        if code.startswith("Error connecting to Ollama:") or code.startswith("Error calling"):
            raise RuntimeError(f"LLM generation failed: {code.split(chr(10))[0]}")
        
        lines = code.strip().split("\n")
        
        # Remove opening code fence
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        
        # Remove closing code fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        
        return "\n".join(lines)
    
    def generate_model(self, model: Dict) -> str:
        """Generate a complete model implementation."""
        print(f"   🧠 Generating {model['name']} model...")
        
        fields_text = "\n".join(
            f"  {f['name']}: {f['type']}" for f in model.get("fields", [])
        )
        
        prompt = MODEL_GEN_PROMPT.format(
            stack=self.stack,
            model_name=model["name"],
            fields=fields_text
        )
        
        system = CODE_GEN_SYSTEM.format(stack=self.stack)
        code = self.call_llm(prompt, system)
        return self._clean_code(code)
    
    def generate_routes(self, entity_name: str, model_spec: str) -> str:
        """Generate routes for an entity."""
        print(f"   🧠 Generating {entity_name} routes...")
        
        features = self._get_section("Feature")[:500]  # Limit context
        
        prompt = ROUTE_GEN_PROMPT.format(
            stack=self.stack,
            entity_name=entity_name,
            model_spec=model_spec,
            features=features
        )
        
        system = CODE_GEN_SYSTEM.format(stack=self.stack)
        code = self.call_llm(prompt, system)
        return self._clean_code(code)
    
    def generate_app_entry(self, entities: List[str]) -> str:
        """Generate the main application entry point."""
        print(f"   🧠 Generating main app...")
        
        features = self._get_section("Feature")[:500]
        
        prompt = APP_GEN_PROMPT.format(
            stack=self.stack,
            project_name=self.project_name,
            blueprint_title=self.blueprint.get("title", "App"),
            entities=", ".join(entities),
            features=features
        )
        
        system = CODE_GEN_SYSTEM.format(stack=self.stack)
        code = self.call_llm(prompt, system)
        return self._clean_code(code)
    
    def generate_component(self, name: str, purpose: str, data_model: str) -> str:
        """Generate a React component."""
        print(f"   🧠 Generating {name} component...")
        
        features = self._get_section("Feature")[:300]
        
        prompt = COMPONENT_GEN_PROMPT.format(
            component_name=name,
            purpose=purpose,
            data_model=data_model,
            features=features
        )
        
        system = CODE_GEN_SYSTEM.format(stack="React")
        code = self.call_llm(prompt, system)
        return self._clean_code(code)


# ============================================================================
# BLUEPRINT PARSER
# ============================================================================

def parse_blueprint(blueprint_path: Path) -> Dict:
    """Parse a blueprint markdown file into structured data."""
    content = blueprint_path.read_text(encoding="utf-8")
    
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split("\n"):
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_content)
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = "\n".join(current_content)
    
    # Extract title
    title = blueprint_path.stem.replace("-", " ").title()
    for line in content.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break
    
    return {
        "name": blueprint_path.stem,
        "title": title,
        "sections": sections,
        "path": blueprint_path,
    }


def parse_file_structure(content: str) -> List[str]:
    """Extract file paths from a File Structure section."""
    paths = []
    
    # Find code block with structure
    in_code_block = False
    for line in content.split("\n"):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        
        if in_code_block and line.strip():
            # Parse tree line: "│   ├── filename.ext"
            # Remove tree characters and extract path
            cleaned = re.sub(r"[│├└──\s]+", "", line)
            if cleaned and not cleaned.endswith("/"):
                # It's a file
                # Reconstruct the path based on indentation
                indent = len(line) - len(line.lstrip("│├└── "))
                depth = indent // 4
                paths.append((depth, cleaned))
    
    # Convert (depth, name) to full paths
    full_paths = []
    path_stack = []
    
    for depth, name in paths:
        # Trim stack to current depth
        path_stack = path_stack[:depth]
        path_stack.append(name)
        full_paths.append("/".join(path_stack))
    
    return full_paths


def parse_data_models(content: str) -> List[Dict]:
    """Extract data models from a Data Model section."""
    models = []
    current_model = None
    current_fields = []
    in_code_block = False
    
    for line in content.split("\n"):
        # Check for model header (### ModelName)
        if line.startswith("### "):
            if current_model and current_fields:
                models.append({
                    "name": current_model,
                    "fields": current_fields
                })
            current_model = line[4:].strip()
            current_fields = []
            continue
        
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        
        if in_code_block and current_model and line.strip():
            # Parse field: "fieldName: type (optional)"
            match = re.match(r"(\w+):\s*(.+)", line.strip())
            if match:
                current_fields.append({
                    "name": match.group(1),
                    "type": match.group(2)
                })
    
    # Don't forget the last model
    if current_model and current_fields:
        models.append({
            "name": current_model,
            "fields": current_fields
        })
    
    return models


# ============================================================================
# SCAFFOLDER
# ============================================================================

class Scaffolder:
    """Generate project structure from a blueprint."""
    
    def __init__(self, blueprint_name: str, project_name: str, stack: str = "flask"):
        self.blueprint_path = BLUEPRINTS_DIR / f"{blueprint_name}.md"
        if not self.blueprint_path.exists():
            raise FileNotFoundError(f"Blueprint not found: {self.blueprint_path}")
        
        self.blueprint = parse_blueprint(self.blueprint_path)
        self.project_name = project_name
        self.project_name_lower = project_name.lower().replace(" ", "-")
        self.stack = stack
        self.output_path = OUTPUT_DIR / self.project_name_lower
        
        if stack not in STACK_TEMPLATES:
            available = ", ".join(STACK_TEMPLATES.keys())
            raise ValueError(f"Unknown stack '{stack}'. Available: {available}")
        
        self.templates = STACK_TEMPLATES[stack]
        self.llm_generator = None  # Lazy-load when needed
    
    def scaffold(self, dry_run: bool = False, generate: bool = False) -> List[str]:
        """
        Generate the project structure.
        
        Args:
            dry_run: If True, just print what would be created
            generate: If True, use LLM to generate actual implementations
            
        Returns:
            List of created file paths
        """
        created = []
        
        mode = "🤖 LLM-Generated" if generate else "📝 Scaffolded"
        print(f"\n🏗️  {mode}: {self.project_name}")
        print(f"   Blueprint: {self.blueprint['title']}")
        print(f"   Stack: {self.stack}")
        print(f"   Output: {self.output_path}")
        if generate:
            print(f"   ⚡ Using Ollama for code generation")
        print()
        
        # Initialize LLM generator if needed
        if generate and not dry_run:
            try:
                self.llm_generator = LLMCodeGenerator(
                    self.blueprint, self.stack, self.project_name
                )
            except RuntimeError as e:
                print(f"⚠️  {e}")
                print("   Falling back to stub generation")
                generate = False
        
        # Create output directory
        if not dry_run:
            self.output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Generate README
        readme_path = self._create_readme(dry_run)
        if readme_path:
            created.append(readme_path)
        
        # 2. Generate main app entry
        entry_path = self._create_app_entry(dry_run, generate)
        if entry_path:
            created.append(entry_path)
        
        # 3. Generate models from Data Model section
        model_section = self._find_section("Data Model")
        models = []
        if model_section:
            models = parse_data_models(model_section)
            for model in models:
                model_path = self._create_model(model, dry_run, generate)
                if model_path:
                    created.append(model_path)
        
        # 4. Generate routes (only in generate mode)
        if generate and models and not dry_run:
            for model in models[:3]:  # Limit to first 3 models
                route_path = self._create_route(model, dry_run)
                if route_path:
                    created.append(route_path)
        
        # 5. Generate package/requirements file
        pkg_path = self._create_package_file(dry_run)
        if pkg_path:
            created.append(pkg_path)
        
        # 6. Create directories from File Structure
        file_section = self._find_section("File Structure")
        if file_section:
            dirs = self._extract_directories(file_section)
            for d in dirs:
                dir_path = self.output_path / d
                if dry_run:
                    print(f"  📁 Would create: {d}/")
                else:
                    dir_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n✅ Created {len(created)} files")
        if generate:
            print("   💡 Generated code is functional but review before production use")
        return created
    
    def _find_section(self, name: str) -> Optional[str]:
        """Find a section by name (partial match)."""
        for section_name, content in self.blueprint["sections"].items():
            if name.lower() in section_name.lower():
                return content
        return None
    
    def _extract_directories(self, content: str) -> List[str]:
        """Extract directory paths from File Structure section."""
        dirs = set()
        in_code_block = False
        
        for line in content.split("\n"):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            
            if in_code_block and "/" in line:
                # Extract directory path
                cleaned = re.sub(r"[│├└──\s]+", "", line)
                if cleaned.endswith("/"):
                    # Remove trailing / and project root
                    parts = cleaned.rstrip("/").split("/")
                    if len(parts) > 1:
                        dirs.add("/".join(parts[1:]))
        
        return sorted(dirs)
    
    def _create_readme(self, dry_run: bool) -> Optional[str]:
        """Create project README."""
        path = self.output_path / "README.md"
        
        content = f"""# {self.project_name}

> Generated from [{self.blueprint['title']}](../../blueprints/{self.blueprint['name']}.md) blueprint

## Quick Start

```bash
# Install dependencies
{self._get_install_command()}

# Run development server
{self._get_run_command()}
```

## Blueprint Reference

See the full specification in [blueprints/{self.blueprint['name']}.md](../../blueprints/{self.blueprint['name']}.md):

- **Core Purpose:** What problem this solves
- **User Types:** Who this is for
- **Feature Categories:** All planned features
- **User Flows:** Step-by-step interactions
- **Screens:** UI components to build
- **Data Model:** Database schema
- **Common Pitfalls:** What to avoid
- **Implementation Order:** Build sequence

## Project Structure

See File Structure section in the blueprint for the complete layout.

## TODO

- [ ] Review blueprint Core Purpose and adjust for your needs
- [ ] Customize feature list (remove what you don't need)
- [ ] Implement models (see Data Model section)
- [ ] Build screens one at a time (see Screens section)
- [ ] Check Common Pitfalls before deploying
"""
        
        if dry_run:
            print(f"  📄 Would create: README.md")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"  📄 Created: README.md")
        
        return str(path)
    
    def _create_app_entry(self, dry_run: bool, generate: bool = False) -> Optional[str]:
        """Create main application entry point."""
        template = self.templates.get("app_entry", "")
        if not template and not generate:
            return None
        
        ext = self.templates.get("extension", ".py")
        
        if self.stack in ("flask", "fastapi"):
            filename = "app.py"
            subdir = "src"
        elif self.stack == "react":
            filename = "App.jsx"
            subdir = "src"
        elif self.stack == "express":
            filename = "index.js"
            subdir = "src"
        else:
            filename = f"main{ext}"
            subdir = "src"
        
        path = self.output_path / subdir / filename
        
        # Use LLM generation if enabled
        if generate and self.llm_generator:
            model_section = self._find_section("Data Model")
            entities = []
            if model_section:
                models = parse_data_models(model_section)
                entities = [m["name"] for m in models]
            content = self.llm_generator.generate_app_entry(entities)
        else:
            content = template.format(
                project_name=self.project_name,
                blueprint_name=self.blueprint["title"],
                blueprint_file=f"{self.blueprint['name']}.md"
            )
        
        if dry_run:
            print(f"  📄 Would create: {subdir}/{filename}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"  📄 Created: {subdir}/{filename}")
        
        return str(path)
    
    def _create_model(self, model: Dict, dry_run: bool, generate: bool = False) -> Optional[str]:
        """Create a model file."""
        template = self.templates.get("model", "")
        if not template and not generate:
            return None
        
        ext = self.templates.get("extension", ".py")
        model_name = model["name"]
        name_lower = model_name.lower()
        
        # Use LLM generation if enabled
        if generate and self.llm_generator:
            content = self.llm_generator.generate_model(model)
        else:
            # Format fields as comments
            fields_lines = []
            for field in model["fields"]:
                fields_lines.append(f"    #   {field['name']}: {field['type']}")
            fields_commented = "\n".join(fields_lines) if fields_lines else "    #   (see blueprint)"
            
            content = template.format(
                model_name=model_name,
                name_lower=name_lower,
                blueprint_file=f"{self.blueprint['name']}.md",
                fields_commented=fields_commented
            )
        
        if self.stack in ("flask", "fastapi"):
            subdir = "src/models"
            filename = f"{name_lower}{ext}"
        elif self.stack == "express":
            subdir = "src/models"
            filename = f"{name_lower}.js"
        else:
            subdir = "src/models"
            filename = f"{name_lower}{ext}"
        
        path = self.output_path / subdir / filename
        
        if dry_run:
            print(f"  📄 Would create: {subdir}/{filename}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"  📄 Created: {subdir}/{filename}")
        
        return str(path)
    
    def _create_route(self, model: Dict, dry_run: bool) -> Optional[str]:
        """Create a route file for a model (only used in generate mode)."""
        if not self.llm_generator:
            return None
        
        ext = self.templates.get("extension", ".py")
        model_name = model["name"]
        name_lower = model_name.lower()
        
        # Build model spec for the prompt
        fields_text = "\n".join(
            f"  {f['name']}: {f['type']}" for f in model.get("fields", [])
        )
        model_spec = f"{model_name}:\n{fields_text}"
        
        content = self.llm_generator.generate_routes(model_name, model_spec)
        
        if self.stack in ("flask", "fastapi"):
            subdir = "src/routes"
            filename = f"{name_lower}{ext}"
        elif self.stack == "express":
            subdir = "src/routes"
            filename = f"{name_lower}.js"
        else:
            subdir = "src/routes"
            filename = f"{name_lower}{ext}"
        
        path = self.output_path / subdir / filename
        
        if dry_run:
            print(f"  📄 Would create: {subdir}/{filename}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"  📄 Created: {subdir}/{filename}")
        
        return str(path)
    
    def _create_package_file(self, dry_run: bool) -> Optional[str]:
        """Create package.json or requirements.txt."""
        if self.stack in ("flask", "fastapi"):
            template = self.templates.get("requirements", "")
            filename = "requirements.txt"
        else:
            template = self.templates.get("package_json", "")
            filename = "package.json"
        
        if not template:
            return None
        
        content = template.format(
            project_name=self.project_name,
            project_name_lower=self.project_name_lower,
            blueprint_name=self.blueprint["title"]
        )
        
        path = self.output_path / filename
        
        if dry_run:
            print(f"  📄 Would create: {filename}")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"  📄 Created: {filename}")
        
        return str(path)
    
    def _get_install_command(self) -> str:
        """Get the install command for this stack."""
        if self.stack in ("flask", "fastapi"):
            return "pip install -r requirements.txt"
        else:
            return "npm install"
    
    def _get_run_command(self) -> str:
        """Get the run command for this stack."""
        commands = {
            "flask": "python src/app.py",
            "fastapi": "uvicorn src.app:app --reload",
            "react": "npm run dev",
            "express": "npm run dev",
        }
        return commands.get(self.stack, "# See README")


# ============================================================================
# CLI
# ============================================================================

def list_blueprints():
    """List all available blueprints."""
    print("\n📋 Available blueprints:\n")
    
    for md_file in sorted(BLUEPRINTS_DIR.glob("*.md")):
        if md_file.name in ("README.md", "GUIDE-building-without-ai.md"):
            continue
        
        # Read first few lines to get title
        content = md_file.read_text(encoding="utf-8")
        title = md_file.stem
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break
        
        print(f"  {md_file.stem:30} - {title}")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate project structure from a blueprint",
        epilog="Example: python scaffold.py learning-app --name MyBookTracker --stack flask"
    )
    
    parser.add_argument(
        "blueprint",
        nargs="?",
        help="Blueprint name (e.g., learning-app, task-manager)"
    )
    
    parser.add_argument(
        "--name", "-n",
        help="Project name (default: based on blueprint name)"
    )
    
    parser.add_argument(
        "--stack", "-s",
        default="flask",
        choices=list(STACK_TEMPLATES.keys()),
        help="Tech stack to use (default: flask)"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available blueprints"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Show what would be created without creating files"
    )
    
    parser.add_argument(
        "--generate", "-g",
        action="store_true",
        help="Use Ollama LLM to generate actual working code (not just stubs)"
    )
    
    args = parser.parse_args()
    
    if args.list or not args.blueprint:
        list_blueprints()
        print("Available stacks:", ", ".join(STACK_TEMPLATES.keys()))
        print("\n💡 Add --generate to use LLM for actual code generation")
        print()
        return
    
    # Default project name from blueprint
    project_name = args.name or args.blueprint.replace("-", " ").title().replace(" ", "")
    
    try:
        scaffolder = Scaffolder(
            blueprint_name=args.blueprint,
            project_name=project_name,
            stack=args.stack
        )
        scaffolder.scaffold(dry_run=args.dry_run, generate=args.generate)
        
        if not args.dry_run:
            print(f"\n🚀 Next steps:")
            print(f"   cd projects/{scaffolder.project_name_lower}")
            print(f"   {scaffolder._get_install_command()}")
            print(f"   {scaffolder._get_run_command()}")
            print(f"\n📖 Read the blueprint: blueprints/{args.blueprint}.md")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        list_blueprints()
    except ValueError as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
