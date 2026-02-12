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

# Import semantic kernel for AI-free semantic understanding
try:
    from semantic_kernel import understand, SemanticUnderstanding
    SEMANTIC_KERNEL_AVAILABLE = True
except ImportError:
    SEMANTIC_KERNEL_AVAILABLE = False

# Import new intelligence algorithms
try:
    from analogy_engine import process_analogy
    ANALOGY_ENGINE_AVAILABLE = True
except ImportError:
    ANALOGY_ENGINE_AVAILABLE = False

try:
    from constraint_validator import validate_and_fix
    CONSTRAINT_VALIDATOR_AVAILABLE = True
except ImportError:
    CONSTRAINT_VALIDATOR_AVAILABLE = False

try:
    from priority_system import partition_features, generate_priority_questions
    PRIORITY_SYSTEM_AVAILABLE = True
except ImportError:
    PRIORITY_SYSTEM_AVAILABLE = False

# Import semantic bridge for universal domain understanding
try:
    from semantic_bridge import build_semantic_bridge, SemanticMapping
    SEMANTIC_BRIDGE_AVAILABLE = True
except ImportError:
    SEMANTIC_BRIDGE_AVAILABLE = False

# Import intent classifier for understanding user goals
try:
    from intent_classifier import classify_intent, Intent, IntentResult
    INTENT_CLASSIFIER_AVAILABLE = True
except ImportError:
    INTENT_CLASSIFIER_AVAILABLE = False

# Import requirement completer for inferring missing requirements
try:
    from requirement_completer import complete_requirements, RequirementCompletion
    REQUIREMENT_COMPLETER_AVAILABLE = True
except ImportError:
    REQUIREMENT_COMPLETER_AVAILABLE = False

# Import build memory for learning from past builds
try:
    from build_memory import memory, BuildRecord
    BUILD_MEMORY_AVAILABLE = True
except ImportError:
    BUILD_MEMORY_AVAILABLE = False

# Import developer profile for personalized generation
try:
    from developer_profile import get_developer_profile, DeveloperProfile
    DEVELOPER_PROFILE_AVAILABLE = True
except ImportError:
    DEVELOPER_PROFILE_AVAILABLE = False

# Import complexity model for architecture recommendations
try:
    from complexity_model import analyze as analyze_complexity, ComplexityProfile
    COMPLEXITY_MODEL_AVAILABLE = True
except ImportError:
    COMPLEXITY_MODEL_AVAILABLE = False

# Import kernel composer for algorithm/simulation apps
try:
    from kernel_composer import can_compose, compose, generate as generate_kernel, analyze as analyze_kernel
    KERNEL_COMPOSER_AVAILABLE = True
except ImportError:
    KERNEL_COMPOSER_AVAILABLE = False

# Import template algebra for composable micro-templates
try:
    from template_algebra import (
        algebra as template_algebra, 
        discovery as template_discovery,
        auto_compose as auto_compose_templates,
        detect_patterns,
        ComposedTemplate
    )
    TEMPLATE_ALGEBRA_AVAILABLE = True
except ImportError:
    TEMPLATE_ALGEBRA_AVAILABLE = False


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
        
        # 0a. INTENT CLASSIFIER - Understand what user wants to do
        intent_result = None
        if INTENT_CLASSIFIER_AVAILABLE:
            intent_result = classify_intent(description)
            if intent_result.confidence > 0.5:
                print(f"🎯 Intent: {intent_result.primary.value.upper()} ({intent_result.confidence:.0%})")
                if intent_result.object_nouns:
                    print(f"   Objects: {intent_result.object_nouns}")
        
        # 0a2. DEVELOPER PROFILE - Personalize based on your coding patterns
        dev_profile = None
        dev_prefs = None
        if DEVELOPER_PROFILE_AVAILABLE:
            dev_profile = get_developer_profile()
            dev_prefs = dev_profile.preferences
            if dev_prefs.confidence > 0.3:
                print(f"👤 Developer Profile ({dev_prefs.confidence:.0%} confidence):")
                print(f"   Preferred: {dev_prefs.preferred_framework} / {dev_prefs.preferred_database}")
                if dev_prefs.common_technologies:
                    techs = list(dev_prefs.common_technologies)[:3]
                    print(f"   Technologies: {', '.join(techs)}")
        
        # 0a3. COMPLEXITY MODEL - Understand app architecture needs
        complexity_result = None
        if COMPLEXITY_MODEL_AVAILABLE:
            complexity_result = analyze_complexity(description)
            tier = complexity_result['profile']['tier'].upper()
            total = complexity_result['profile']['total']
            arch_name = complexity_result['architecture']['name']
            nearest = complexity_result['nearest_canonical']
            print(f"📊 Complexity: {tier} (score: {total})")
            print(f"   Architecture: {arch_name}")
            if complexity_result['architecture']['warnings']:
                for warn in complexity_result['architecture']['warnings'][:2]:
                    print(f"   ⚠️  {warn}")
            if complexity_result['growth_suggestions']:
                print(f"   💡 Growth: {complexity_result['growth_suggestions'][0]}")
        
        # 0a4. KERNEL COMPOSER - Detect algorithm/simulation apps
        # These are apps like Game of Life, pathfinding, particle sims, etc.
        # that can be composed from primitives rather than templates
        if KERNEL_COMPOSER_AVAILABLE:
            kernel_analysis = analyze_kernel(description)
            if kernel_analysis['can_compose']:
                spec = compose(description)
                if spec:
                    prim = spec.primitive.value
                    ctrl = spec.control.value
                    known = kernel_analysis['known_algorithm']
                    print(f"🧬 Kernel Composer: {prim.upper()} primitive")
                    print(f"   Control: {ctrl}, Algorithm: {known or 'novel'}")
                    
                    # Generate the kernel code
                    kernel_code = generate_kernel(description)
                    if kernel_code:
                        app_name = self._extract_app_name(description)
                        return GeneratedProject(
                            name=app_name,
                            category='algorithm',
                            framework='html_canvas',
                            files=[GeneratedFile('index.html', kernel_code)],
                            run_command='open index.html  # or use a local server',
                            install_command=None,
                            packages=[],
                            trait_id=f'kernel:{prim}'
                        )
        
        # 0a5. TEMPLATE ALGEBRA - Compose micro-templates for complex apps
        # This detects universal patterns (container, relationship, state, etc.)
        # and combines them like an LLM but without hallucination
        algebra_composed = None
        if TEMPLATE_ALGEBRA_AVAILABLE:
            detected_patterns = detect_patterns(description)
            if detected_patterns and len(detected_patterns) >= 2:
                entity_name = self._extract_model_name(description)
                algebra_composed = auto_compose_templates(description, entity_name)
                if algebra_composed.templates:
                    print(f"🧮 Template Algebra: {len(algebra_composed.templates)} micro-templates")
                    print(f"   Patterns: {algebra_composed.templates[:4]}")
                    print(f"   Fields: {[f['name'] for f in algebra_composed.all_fields[:5]]}")
                    suggestions = template_algebra.suggest_templates(description, detected_patterns[:3])
                    if suggestions:
                        print(f"   💡 Consider adding: {[s[0] for s in suggestions[:2]]}")
        
        # 0b. REQUIREMENT COMPLETER - Infer missing requirements
        completion = None
        if REQUIREMENT_COMPLETER_AVAILABLE:
            completion = complete_requirements(description)
            high_conf_fields = [r for r in completion.inferred if r.confidence >= 0.70]
            if high_conf_fields:
                print(f"💡 Inferred requirements ({len(high_conf_fields)} high-confidence):")
                for req in high_conf_fields[:4]:
                    print(f"   • {req.name}: {req.field_type} ({req.confidence:.0%})")
            if completion.features:
                print(f"   Suggested features: {completion.features}")
        
        # 0c. BUILD MEMORY - Learn from past builds
        memory_suggestions = None
        patterns_to_avoid = []
        similar_successes = []
        if BUILD_MEMORY_AVAILABLE:
            # Find similar successful builds
            similar_successes = memory.get_similar_good_builds(description, limit=3)
            if similar_successes:
                print(f"📚 Found {len(similar_successes)} similar successful builds:")
                for build in similar_successes[:2]:
                    print(f"   • \"{build.description[:50]}...\" ({build.template_used})")
            
            # Get patterns that lead to failure
            patterns_to_avoid = memory.get_patterns_to_avoid(limit=5)
            if patterns_to_avoid:
                avoid_msgs = [p['feature'] for p in patterns_to_avoid[:3]]
                print(f"⚠️  Patterns to avoid: {avoid_msgs}")
        
        # 0d. ANALOGY ENGINE - Process analogies first
        analogy_result = None
        if ANALOGY_ENGINE_AVAILABLE:
            analogy_result = process_analogy(description)
            if analogy_result:
                print(f"🔄 Detected analogy: {analogy_result.base_trait_id} + {analogy_result.modifications}")
        
        # 1. Match to trait
        if analogy_result:
            # Use analogy-derived trait/features
            trait = None  # Could create trait from analogy_result
            trait_match = []
        else:
            trait_match = self.trait_store.match(description)
            trait = trait_match[0] if trait_match else None
        
        # 1b. SEMANTIC BRIDGE - Universal domain understanding
        semantic_mapping = None
        if SEMANTIC_BRIDGE_AVAILABLE and (not trait or len(trait_match) == 0) and not analogy_result:
            semantic_mapping = build_semantic_bridge(description)
            if semantic_mapping.confidence > 0.4:
                print(f"🌉 Semantic Bridge: {semantic_mapping.primary_archetype} archetype (confidence: {semantic_mapping.confidence:.2f})")
                print(f"   Domain fields: {semantic_mapping.suggested_fields[:3]}...")
        
        # 1c. SEMANTIC KERNEL FALLBACK - Use if no trait or low confidence
        semantic_understanding = None
        use_semantic = False
        
        if SEMANTIC_KERNEL_AVAILABLE and (not trait or len(trait_match) == 0) and not analogy_result:
            semantic_understanding = understand(description, verbose=False)
            # Use semantic kernel if confidence is reasonable and we have models/features
            if semantic_understanding.confidence > 0.3 and (semantic_understanding.models or semantic_understanding.features):
                use_semantic = True
                print(f"🧠 Using Semantic Kernel (confidence: {semantic_understanding.confidence:.2f})")
        
        # 2. Determine framework
        if analogy_result:
            framework = analogy_result.framework
        elif use_semantic and semantic_understanding:
            framework = semantic_understanding.framework
        else:
            # Try developer profile first for personalization
            if dev_profile and dev_prefs and dev_prefs.confidence > 0.5:
                framework_rec, fw_conf = dev_profile.get_framework_for_description(description)
                if fw_conf >= 0.7:  # High confidence = use profile preference
                    framework = framework_rec
                    print(f"   👤 Using preferred framework: {framework}")
                else:
                    framework = self._select_framework(description, answers, trait)
            else:
                framework = self._select_framework(description, answers, trait)
        
        # 3. Merge answers with trait defaults
        merged_answers = {}
        if trait:
            merged_answers.update(trait.default_answers)
        merged_answers.update(answers)
        
        # 4. Select features
        if analogy_result:
            # Use analogy-derived features
            feature_ids = list(analogy_result.features)
        elif use_semantic and semantic_understanding:
            # Use semantic kernel's inferred features
            feature_ids = list(semantic_understanding.features)
        else:
            feature_ids = self._select_features(description, merged_answers, trait)
        
        # 4a. MEMORY-BASED FEATURE ENHANCEMENT - Learn from similar successes
        if BUILD_MEMORY_AVAILABLE and similar_successes:
            # Get valid feature IDs from feature store
            valid_feature_ids = set(self.feature_store.features.keys()) if hasattr(self.feature_store, 'features') else set()
            
            # Extract features from similar successful builds
            for past_build in similar_successes:
                # Only learn from builds with the same template (app type)
                if past_build.template_used == (trait.id if trait else 'generic'):
                    if past_build.features:
                        for feature_key, feature_val in past_build.features.items():
                            # Only add if it's a valid feature and not already present
                            if feature_val and feature_key not in feature_ids:
                                if not valid_feature_ids or feature_key in valid_feature_ids:
                                    rate = memory.get_feature_success_rate(feature_key, str(feature_val))
                                    if rate > 0.7:  # Higher threshold for suggestions
                                        feature_ids.append(feature_key)
                                        print(f"   📚 Added '{feature_key}' from past success ({rate:.0%} rate)")
        
        # 4a2. DEVELOPER PROFILE FEATURES - Add features you commonly use
        if DEVELOPER_PROFILE_AVAILABLE and dev_profile and dev_prefs:
            for feature in dev_profile.get_suggested_features():
                should_add, weight = dev_profile.should_include_feature(feature)
                if should_add and feature not in feature_ids:
                    # Map profile features to actual feature IDs
                    feature_mapping = {
                        'auth': 'auth',
                        'ml_integration': 'ml',
                        'ai_features': 'ai',
                        'realtime': 'websocket',
                        'search': 'search',
                    }
                    mapped = feature_mapping.get(feature, feature)
                    if mapped in self.feature_store.features:
                        feature_ids.append(mapped)
                        print(f"   👤 Added '{mapped}' from developer profile ({weight:.0%} tendency)")
        
        # 4b. PRIORITY SYSTEM - Partition features by importance
        if PRIORITY_SYSTEM_AVAILABLE and feature_ids:
            context = {
                "app_type": description,
                "existing_features": set(feature_ids)
            }
            partitions = partition_features(set(feature_ids), context)
            print(f"🎯 Feature priorities:")
            print(f"   Critical: {partitions['critical']}")
            print(f"   Important: {partitions['important']}")
            # Could use this to ask user about optional features
        
        # 4c. CONSTRAINT VALIDATOR - Check and fix feature combinations
        if CONSTRAINT_VALIDATOR_AVAILABLE and feature_ids:
            fixed_features, violations = validate_and_fix(set(feature_ids), framework)
            if violations:
                print(f"⚠️  Constraint violations detected (auto-fixed):")
                for v in violations:
                    print(f"   - {v.message}")
            feature_ids = list(fixed_features)
        
        # 4d. MEMORY-BASED PATTERN AVOIDANCE - Warn about risky combinations
        if BUILD_MEMORY_AVAILABLE and patterns_to_avoid and feature_ids:
            risky_features = []
            for pattern in patterns_to_avoid:
                # Pattern format: "feature_key=value"
                parts = pattern['feature'].split('=')
                if len(parts) == 2:
                    feat_key = parts[0]
                    if feat_key in feature_ids:
                        fail_rate = pattern['failures'] / (pattern['failures'] + pattern['successes'] + 1)
                        if fail_rate > 0.5:  # More failures than successes
                            risky_features.append((feat_key, fail_rate))
            
            if risky_features:
                print(f"🔴 Risky features (from past failures):")
                for feat, rate in risky_features[:3]:
                    print(f"   • '{feat}' has {rate:.0%} failure rate")
        
        # 5. Get models
        if analogy_result and analogy_result.models:
            # Use analogy-derived models
            models = analogy_result.models
        elif use_semantic and semantic_understanding and semantic_understanding.models:
            # Convert semantic kernel models to DomainModelSchema
            models = self._convert_semantic_models(semantic_understanding.models)
        elif trait:
            models = trait.models
        elif semantic_mapping and semantic_mapping.suggested_fields:
            # Use semantic bridge to create model from universal archetypes
            # Merge with requirement completer inferences if available
            fields_to_use = list(semantic_mapping.suggested_fields[:8])
            
            if completion and completion.inferred:
                # Add high-confidence inferred fields not already present
                field_names = set(f.lower() for f in fields_to_use)
                for req in completion.inferred:
                    if req.confidence >= 0.70 and req.name.lower() not in field_names:
                        fields_to_use.append(req.name)
                        field_names.add(req.name.lower())
            
            bridge_model = DomainModelSchema(
                name=semantic_mapping.data_model_name,
                fields=[
                    DomainField(name=f, type=self._infer_field_type(f))
                    for f in fields_to_use[:10]  # Limit to 10 fields
                ]
            )
            models = [bridge_model]
            print(f"🌉 Semantic bridge created model: {bridge_model.name} with {len(bridge_model.fields)} fields")
        elif completion and completion.inferred:
            # Use requirement completer only (no semantic bridge match)
            high_conf = [r for r in completion.inferred if r.confidence >= 0.60]
            if high_conf:
                # Extract model name from description
                model_name = self._extract_model_name(description)
                completer_model = DomainModelSchema(
                    name=model_name,
                    fields=[
                        DomainField(name=r.name, type=r.field_type)
                        for r in high_conf[:8]
                    ]
                )
                models = [completer_model]
                print(f"💡 Requirement completer created model: {model_name} with {len(completer_model.fields)} fields")
            else:
                models = []
        else:
            models = []
        
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
    
    def _convert_semantic_models(self, semantic_models) -> List[DomainModelSchema]:
        """Convert semantic kernel InferredModel to DomainModelSchema."""
        result = []
        
        for sem_model in semantic_models:
            # Convert FieldDefinition to DomainField
            fields = []
            for field_def in sem_model.fields:
                fields.append(DomainField(
                    name=field_def.name,
                    type=field_def.field_type,
                    required=field_def.required,
                    default=None  # Semantic kernel doesn't provide defaults yet
                ))
            
            result.append(DomainModelSchema(
                name=sem_model.name,
                fields=fields
            ))
        
        return result
    
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
    
    def _extract_model_name(self, description: str) -> str:
        """Extract a model name from description for data models."""
        import re
        
        text = description.lower()
        
        # Look for explicit model indicators
        patterns = [
            r'(\w+)\s+(tracker|manager|logger|organizer|planner)',
            r'(\w+)\s+(collection|list|inventory)',
            r'track(?:ing)?\s+(\w+)',
            r'manage(?:ing)?\s+(\w+)',
            r'(\w+)\s+app',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Get the first captured group that's meaningful
                for group in match.groups():
                    if group and group not in ['a', 'an', 'the', 'my', 'app', 'tracker']:
                        return group.capitalize()
        
        # Fallback: first significant noun
        text = re.sub(r'\b(a|an|the|app|application|for|to|with|that|and|or|my)\b', '', text)
        words = [w.strip() for w in text.split() if w.strip() and len(w) > 2]
        
        if words:
            return words[0].capitalize()
        return "Item"
    
    def _infer_field_type(self, field_name: str) -> str:
        """Infer field type from name using common patterns."""
        name = field_name.lower()
        
        # Boolean patterns
        if any(p in name for p in ['is_', 'has_', 'can_', 'active', 'enabled', 'completed', 'done']):
            return 'boolean'
        
        # Date/time patterns
        if any(p in name for p in ['date', 'time', 'created', 'updated', 'start', 'end', 'timestamp']):
            return 'datetime'
        
        # Numeric patterns
        if any(p in name for p in ['count', 'amount', 'price', 'cost', 'quantity', 'number', 'total', 
                                    'rating', 'score', 'duration', 'weight', 'height', 'temperature',
                                    'age', 'level', 'ph', 'gravity', 'batch']):
            return 'float'
        
        if any(p in name for p in ['id', 'year', 'month', 'day', 'size', 'position']):
            return 'integer'
        
        # Text patterns (notes, descriptions tend to be longer)
        if any(p in name for p in ['notes', 'description', 'content', 'body', 'text', 'details', 'comments']):
            return 'text'
        
        # Default to string
        return 'string'
    
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
