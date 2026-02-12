"""Slot-Based Generator - Combines Universal Template + Features + Traits.

This is the main generator that:
1. Matches description to a Trait (app-specific knowledge)
2. Selects Features based on answers and trait defaults
3. Generates domain Models from trait or description
4. Renders using Universal Template with Feature-injected slots

The architecture:
    Description → Trait Match → Feature Selection → Slot Injection → Code
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from universal_template import (
    Slot, TemplateRenderer, TemplateContext, UNIVERSAL_TEMPLATES
)
from feature_store import feature_store, Feature
from trait_store import trait_store, AppTrait, DomainModelSchema, DomainField


@dataclass
class GeneratedFile:
    """A generated file."""
    path: str
    content: str


@dataclass
class GeneratedProject:
    """A complete generated project."""
    name: str
    category: str
    framework: str
    files: List[GeneratedFile]
    run_command: str
    install_command: Optional[str] = None
    packages: List[str] = field(default_factory=list)
    trait_id: Optional[str] = None


# =====================================================================
# Model Code Generator
# =====================================================================

def generate_model_code(models: List[DomainModelSchema], framework: str) -> str:
    """Generate model class code from schemas."""
    if not models:
        return "# No domain models"
    
    if framework == "flask":
        return _flask_models(models)
    elif framework == "fastapi":
        return _fastapi_models(models)
    elif framework == "html_canvas":
        return _js_models(models)
    else:
        return _generic_models(models)


def _flask_models(models: List[DomainModelSchema]) -> str:
    """Generate Flask-SQLAlchemy models."""
    code_parts = []
    
    for model in models:
        lines = [f"\nclass {model.name}(db.Model):"]
        lines.append(f"    __tablename__ = '{model.name.lower()}'")
        lines.append("    id = db.Column(db.Integer, primary_key=True)")
        lines.append("    created_at = db.Column(db.DateTime, default=datetime.utcnow)")
        
        for f in model.fields:
            col_type = _sql_type(f.type)
            nullable = "True" if not f.required else "False"
            default = f", default={repr(f.default)}" if f.default is not None else ""
            lines.append(f"    {f.name} = db.Column({col_type}, nullable={nullable}{default})")
        
        # to_dict method
        lines.append("")
        lines.append("    def to_dict(self):")
        lines.append("        return {")
        lines.append('            "id": self.id,')
        for f in model.fields:
            lines.append(f'            "{f.name}": self.{f.name},')
        lines.append('            "created_at": self.created_at.isoformat() if self.created_at else None,')
        lines.append("        }")
        
        code_parts.append("\n".join(lines))
    
    return "\n".join(code_parts)


def _fastapi_models(models: List[DomainModelSchema]) -> str:
    """Generate Pydantic models for FastAPI."""
    code_parts = []
    
    for model in models:
        # SQLAlchemy model
        lines = [f"\nclass {model.name}(Base):"]
        lines.append(f"    __tablename__ = '{model.name.lower()}'")
        lines.append("    id = Column(Integer, primary_key=True, index=True)")
        lines.append("    created_at = Column(DateTime, default=datetime.utcnow)")
        
        for f in model.fields:
            col_type = _sqlalchemy_type(f.type)
            lines.append(f"    {f.name} = Column({col_type})")
        
        lines.append("")
        lines.append("    def to_dict(self):")
        lines.append("        return {")
        lines.append('            "id": self.id,')
        for f in model.fields:
            lines.append(f'            "{f.name}": self.{f.name},')
        lines.append("        }")
        
        code_parts.append("\n".join(lines))
        
        # Pydantic schemas
        code_parts.append(f"\n\nclass {model.name}Base(BaseModel):")
        for f in model.fields:
            py_type = _python_type(f.type)
            optional = " = None" if not f.required else ""
            code_parts.append(f"    {f.name}: {py_type}{optional}")
        
        code_parts.append(f"\n\nclass {model.name}Create({model.name}Base):")
        code_parts.append("    pass")
        
        code_parts.append(f"\n\nclass {model.name}Response({model.name}Base):")
        code_parts.append("    id: int")
        code_parts.append("    class Config:")
        code_parts.append("        from_attributes = True")
    
    return "\n".join(code_parts)


def _js_models(models: List[DomainModelSchema]) -> str:
    """Generate JavaScript object literals for HTML Canvas."""
    if not models:
        return "// No models"
    
    code_parts = []
    for model in models:
        fields = []
        for f in model.fields:
            default = _js_default(f.type, f.default)
            fields.append(f"        {f.name}: {default}")
        
        code_parts.append(f"    // {model.name}")
        code_parts.append(",\n".join(fields))
    
    return ",\n".join(code_parts)


def _generic_models(models: List[DomainModelSchema]) -> str:
    """Generate generic Python dataclasses."""
    code_parts = ["from dataclasses import dataclass, field"]
    
    for model in models:
        lines = [f"\n@dataclass"]
        lines.append(f"class {model.name}:")
        
        for f in model.fields:
            py_type = _python_type(f.type)
            if f.default is not None:
                lines.append(f"    {f.name}: {py_type} = {repr(f.default)}")
            elif not f.required:
                lines.append(f"    {f.name}: {py_type} = None")
            else:
                lines.append(f"    {f.name}: {py_type}")
        
        code_parts.append("\n".join(lines))
    
    return "\n".join(code_parts)


def _sql_type(field_type: str) -> str:
    """Map field type to Flask-SQLAlchemy column type."""
    mapping = {
        "string": "db.String(200)",
        "text": "db.Text",
        "int": "db.Integer",
        "float": "db.Float",
        "bool": "db.Boolean",
        "date": "db.Date",
        "email": "db.String(120)",
    }
    return mapping.get(field_type, "db.String(200)")


def _sqlalchemy_type(field_type: str) -> str:
    """Map field type to SQLAlchemy column type."""
    mapping = {
        "string": "String(200)",
        "text": "Text",
        "int": "Integer",
        "float": "Float",
        "bool": "Boolean",
        "date": "Date",
        "email": "String(120)",
    }
    return mapping.get(field_type, "String(200)")


def _python_type(field_type: str) -> str:
    """Map field type to Python type hint."""
    mapping = {
        "string": "str",
        "text": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "date": "str",  # ISO format
        "email": "str",
    }
    return mapping.get(field_type, "str")


def _js_default(field_type: str, default: Any) -> str:
    """Get JavaScript default value."""
    if default is not None:
        if isinstance(default, bool):
            return "true" if default else "false"
        elif isinstance(default, str):
            return repr(default)
        return str(default)
    
    defaults = {
        "string": "''",
        "text": "''",
        "int": "0",
        "float": "0.0",
        "bool": "false",
        "date": "null",
    }
    return defaults.get(field_type, "null")


# =====================================================================
# CRUD Route Generator
# =====================================================================

def generate_crud_routes(models: List[DomainModelSchema], framework: str) -> str:
    """Generate CRUD routes for models."""
    if not models:
        return ""
    
    # For now, use first model as primary
    model = models[0]
    name = model.name
    name_lower = name.lower()
    name_plural = name_lower + "s"
    
    if framework == "flask":
        return f'''
# CRUD Routes for {name}
@app.route('/api/{name_plural}', methods=['GET'])
def list_{name_plural}():
    items = {name}.query.order_by({name}.created_at.desc()).all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/{name_plural}', methods=['POST'])
def create_{name_lower}():
    data = request.get_json()
    item = {name}(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/{name_plural}/<int:id>', methods=['GET'])
def get_{name_lower}(id):
    item = {name}.query.get_or_404(id)
    return jsonify(item.to_dict())

@app.route('/api/{name_plural}/<int:id>', methods=['PUT'])
def update_{name_lower}(id):
    item = {name}.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        if hasattr(item, key) and key != 'id':
            setattr(item, key, value)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/{name_plural}/<int:id>', methods=['DELETE'])
def delete_{name_lower}(id):
    item = {name}.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return '', 204
'''
    
    elif framework == "fastapi":
        return f'''
# CRUD Endpoints for {name}
@app.get("/api/{name_plural}")
async def list_{name_plural}():
    db = SessionLocal()
    try:
        items = db.query({name}).all()
        return [item.to_dict() for item in items]
    finally:
        db.close()

@app.post("/api/{name_plural}")
async def create_{name_lower}(data: {name}Create):
    db = SessionLocal()
    try:
        item = {name}(**data.dict())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item.to_dict()
    finally:
        db.close()

@app.get("/api/{name_plural}/{{id}}")
async def get_{name_lower}(id: int):
    db = SessionLocal()
    try:
        item = db.query({name}).filter({name}.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="{name} not found")
        return item.to_dict()
    finally:
        db.close()

@app.delete("/api/{name_plural}/{{id}}")
async def delete_{name_lower}(id: int):
    db = SessionLocal()
    try:
        item = db.query({name}).filter({name}.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="{name} not found")
        db.delete(item)
        db.commit()
        return {{"ok": True}}
    finally:
        db.close()
'''
    
    return ""


# =====================================================================
# Index HTML Generator
# =====================================================================

def generate_index_html(app_name: str, models: List[DomainModelSchema], framework: str) -> str:
    """Generate index.html template for Flask apps."""
    if framework != "flask" or not models:
        return None
    
    model = models[0]
    name = model.name
    name_plural = name.lower() + "s"
    
    # Generate form fields
    form_fields = []
    for f in model.fields:
        input_type = "text"
        if f.type == "int" or f.type == "float":
            input_type = "number"
        elif f.type == "bool":
            input_type = "checkbox"
        elif f.type == "date":
            input_type = "date"
        elif f.type == "text":
            form_fields.append(f'''<div class="field">
                <label>{f.name.replace('_', ' ').title()}</label>
                <textarea name="{f.name}" id="input-{f.name}"{"" if f.required else ""}></textarea>
            </div>''')
            continue
        
        form_fields.append(f'''<div class="field">
            <label>{f.name.replace('_', ' ').title()}</label>
            <input type="{input_type}" name="{f.name}" id="input-{f.name}"{"" if not f.required else " required"}>
        </div>''')
    
    form_html = "\n            ".join(form_fields)
    
    # Generate display fields
    display_fields = [f'<span class="item-{f.name}">${{item.{f.name} || ""}}</span>' for f in model.fields]
    display_html = "\n                ".join(display_fields)
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: system-ui, -apple-system, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        .form-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .field {{ margin-bottom: 15px; }}
        .field label {{ display: block; margin-bottom: 5px; font-weight: 500; }}
        .field input, .field textarea {{
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        .field textarea {{ min-height: 100px; resize: vertical; }}
        button {{
            background: #4f46e5;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        button:hover {{ background: #4338ca; }}
        .items {{ display: grid; gap: 15px; }}
        .item {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .item-actions {{ margin-top: 10px; }}
        .btn-delete {{ background: #dc2626; }}
        .btn-delete:hover {{ background: #b91c1c; }}
        @media (max-width: 600px) {{
            body {{ padding: 10px; }}
            .form-section {{ padding: 15px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{app_name}</h1>
        
        <div class="form-section">
            <h2>Add {name}</h2>
            <form id="add-form">
                {form_html}
                <button type="submit">Add</button>
            </form>
        </div>
        
        <div class="items" id="items-list">
            <!-- Items loaded via JS -->
        </div>
    </div>
    
    <script>
        const API = '/api/{name_plural}';
        
        async function loadItems() {{
            const res = await fetch(API);
            const items = await res.json();
            const list = document.getElementById('items-list');
            list.innerHTML = items.map(item => `
                <div class="item" data-id="${{item.id}}">
                    {display_html}
                    <div class="item-actions">
                        <button class="btn-delete" onclick="deleteItem(${{item.id}})">Delete</button>
                    </div>
                </div>
            `).join('');
        }}
        
        document.getElementById('add-form').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const form = e.target;
            const data = Object.fromEntries(new FormData(form));
            
            await fetch(API, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }});
            
            form.reset();
            loadItems();
        }});
        
        async function deleteItem(id) {{
            await fetch(`${{API}}/${{id}}`, {{ method: 'DELETE' }});
            loadItems();
        }}
        
        loadItems();
    </script>
</body>
</html>
'''


# =====================================================================
# Requirements Generator
# =====================================================================

def generate_requirements(packages: List[str], framework: str) -> str:
    """Generate requirements.txt content."""
    base_packages = {
        "flask": ["flask>=3.0.0"],
        "fastapi": ["fastapi>=0.109.0", "uvicorn>=0.27.0"],
        "click": ["click>=8.1.0"],
        "sklearn": ["scikit-learn>=1.4.0", "pandas>=2.2.0", "numpy>=1.26.0"],
    }
    
    all_packages = set(base_packages.get(framework, []))
    all_packages.update(packages)
    
    return "\n".join(sorted(all_packages))


# =====================================================================
# Slot-Based Generator
# =====================================================================

class SlotBasedGenerator:
    """Main generator combining templates, features, and traits."""
    
    def __init__(self):
        self.feature_store = feature_store
        self.trait_store = trait_store
    
    def generate(self, 
                 description: str, 
                 answers: Dict[str, Any] = None) -> GeneratedProject:
        """Generate a project from description and answers."""
        answers = answers or {}
        
        # 1. Match to trait
        trait_match = self.trait_store.match(description)
        trait = trait_match[0] if trait_match else None
        
        # 2. Determine framework
        framework = self._select_framework(description, answers, trait)
        
        # 3. Merge answers with trait defaults
        merged_answers = {}
        if trait:
            merged_answers.update(trait.default_answers)
        merged_answers.update(answers)
        
        # 4. Select features
        feature_ids = self._select_features(description, merged_answers, trait)
        
        # 5. Get models
        models = trait.models if trait else []
        
        # 6. Create renderer and inject features
        renderer = TemplateRenderer(framework)
        packages = self.feature_store.apply_features(renderer, feature_ids, framework)
        
        # 7. Inject models
        if models:
            model_code = generate_model_code(models, framework)
            renderer.inject(Slot.MODELS, model_code, priority=30)
            
            # Inject CRUD routes for the models
            crud_code = generate_crud_routes(models, framework)
            if crud_code:
                renderer.inject(Slot.ROUTES, crud_code, priority=65)
        
        # 8. Render main file
        app_name = self._extract_app_name(description)
        context = TemplateContext(
            app_name=app_name,
            description=description,
            framework=framework,
            answers=merged_answers,
            models=models,
        )
        
        main_code = renderer.render(context)
        
        # 9. Generate project files
        files = self._generate_files(app_name, main_code, models, framework, packages)
        
        # 10. Record trait usage
        if trait:
            self.trait_store.record_usage(trait.id)
        
        return GeneratedProject(
            name=app_name,
            category=trait.id if trait else "generic",
            framework=framework,
            files=files,
            run_command=self._get_run_command(framework),
            install_command=f"pip install -r requirements.txt" if framework not in ["html_canvas"] else None,
            packages=packages,
            trait_id=trait.id if trait else None,
        )
    
    def _select_framework(self, description: str, answers: Dict, trait: Optional[AppTrait]) -> str:
        """Select the best framework."""
        # Check explicit preference
        if answers.get("framework"):
            return answers["framework"]
        
        # Use trait preference
        if trait and trait.preferred_framework:
            return trait.preferred_framework
        
        # Infer from description
        desc_lower = description.lower()
        
        if any(kw in desc_lower for kw in ["game", "canvas", "animation", "interactive"]):
            return "html_canvas"
        elif any(kw in desc_lower for kw in ["api", "rest", "endpoint", "async"]):
            return "fastapi"
        elif any(kw in desc_lower for kw in ["cli", "command", "terminal"]):
            return "click"
        elif any(kw in desc_lower for kw in ["ml", "machine learning", "predict", "train"]):
            return "sklearn"
        
        # Default to Flask
        return "flask"
    
    def _select_features(self, description: str, answers: Dict, trait: Optional[AppTrait]) -> List[str]:
        """Select features based on description and answers."""
        features = set()
        
        # Start with trait's typical features
        if trait:
            features.update(trait.typical_features)
        
        # Add based on answers
        if answers.get("needs_auth"):
            features.add("auth")
        if answers.get("search"):
            features.add("search")
        if answers.get("export"):
            features.add("export")
        if answers.get("realtime"):
            features.add("realtime")
        if answers.get("has_data") or answers.get("database"):
            features.add("database")
            features.add("crud")
        if answers.get("responsive"):
            features.add("responsive_ui")
        
        # Infer from description
        desc_lower = description.lower()
        
        if any(kw in desc_lower for kw in ["login", "user", "account", "auth"]):
            features.add("auth")
        if any(kw in desc_lower for kw in ["search", "find", "filter"]):
            features.add("search")
        if any(kw in desc_lower for kw in ["export", "download", "csv"]):
            features.add("export")
        if any(kw in desc_lower for kw in ["real-time", "live", "websocket"]):
            features.add("realtime")
        if any(kw in desc_lower for kw in ["game", "play"]):
            features.add("game_loop")
            features.add("input_handler")
            features.add("scoring")
        
        return list(features)
    
    def _extract_app_name(self, description: str) -> str:
        """Extract an app name from description."""
        import re
        
        # Remove common words
        text = description.lower()
        text = re.sub(r'\b(a|an|the|app|application|for|to|with|that|and|or)\b', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        
        # Take first few significant words
        words = [w.strip() for w in text.split() if w.strip()][:3]
        
        if words:
            return "".join(w.capitalize() for w in words)
        return "GeneratedApp"
    
    def _generate_files(self, app_name: str, main_code: str, 
                       models: List[DomainModelSchema], 
                       framework: str, packages: List[str]) -> List[GeneratedFile]:
        """Generate all project files."""
        files = []
        
        if framework == "flask":
            files.append(GeneratedFile("app.py", main_code))
            files.append(GeneratedFile("requirements.txt", generate_requirements(packages, framework)))
            
            # Index HTML template
            if models:
                index_html = generate_index_html(app_name, models, framework)
                if index_html:
                    files.append(GeneratedFile("templates/index.html", index_html))
        
        elif framework == "fastapi":
            files.append(GeneratedFile("main.py", main_code))
            files.append(GeneratedFile("requirements.txt", generate_requirements(packages, framework)))
        
        elif framework == "click":
            files.append(GeneratedFile("cli.py", main_code))
            files.append(GeneratedFile("requirements.txt", generate_requirements(packages, framework)))
        
        elif framework == "html_canvas":
            files.append(GeneratedFile("index.html", main_code))
        
        elif framework == "sklearn":
            files.append(GeneratedFile("pipeline.py", main_code))
            files.append(GeneratedFile("requirements.txt", generate_requirements(packages, framework)))
        
        return files
    
    def _get_run_command(self, framework: str) -> str:
        """Get the command to run the app."""
        commands = {
            "flask": "python app.py",
            "fastapi": "uvicorn main:app --reload",
            "click": "python cli.py --help",
            "html_canvas": "open index.html  # or use a local server",
            "sklearn": "python pipeline.py",
        }
        return commands.get(framework, "python app.py")
    
    def learn_from_build(self, description: str, answers: Dict, 
                        framework: str, features: List[str],
                        models: List = None) -> AppTrait:
        """Learn a new trait from a successful build."""
        return self.trait_store.learn_from_build(description, answers, framework, features, models)


# Singleton
slot_generator = SlotBasedGenerator()


# =====================================================================
# Convenience Function
# =====================================================================

def generate_app(description: str, answers: Dict[str, Any] = None) -> GeneratedProject:
    """Generate an app from a natural language description."""
    return slot_generator.generate(description, answers)


# =====================================================================
# CLI and Testing
# =====================================================================

if __name__ == "__main__":
    print("Slot-Based Generator")
    print("=" * 60)
    
    test_cases = [
        ("a recipe collection app", {"search": True, "export": True}),
        ("a snake game", {}),
        ("a todo list app", {"search": True}),
        ("REST API for user management", {"needs_auth": True}),
    ]
    
    for desc, answers in test_cases:
        print(f"\n--- Generating: '{desc}' ---")
        project = generate_app(desc, answers)
        
        print(f"  Name: {project.name}")
        print(f"  Trait: {project.trait_id}")
        print(f"  Framework: {project.framework}")
        print(f"  Files: {[f.path for f in project.files]}")
        print(f"  Run: {project.run_command}")
        print(f"  Packages: {project.packages}")
        
        # Show first file content length
        if project.files:
            print(f"  Main file: {len(project.files[0].content)} chars")
