"""
App Algebra: A Generative Model for App Synthesis

No templates. Apps are derived from mathematical structures.

Core Types:
    Entity  = Named collection of typed fields
    Field   = (name, type, constraints)
    Relation = (entity_a, entity_b, cardinality)
    Message = Entity × Operation (e.g., Recipe.Create, Rating.Update)
    State   = Dict[EntityName, List[EntityInstance]]
    Update  = (State, Message, Payload) → State
    View    = (State, ViewSpec) → HTML

The Elm Architecture applied to web apps:
    init : () → State
    update : (State, Message) → State
    view : State → HTML
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, Callable, Tuple
from enum import Enum, auto
import re
import json


# =============================================================================
# ALGEBRAIC TYPES
# =============================================================================

class FieldType(Enum):
    """Primitive field types that can be composed"""
    STRING = auto()      # Text data
    INT = auto()         # Whole numbers
    FLOAT = auto()       # Decimal numbers
    BOOL = auto()        # True/False
    DATE = auto()        # Date values
    DATETIME = auto()    # Date + time
    TEXT = auto()        # Long text (textarea)
    EMAIL = auto()       # Email address
    URL = auto()         # Web URL
    ENUM = auto()        # Fixed choices
    LIST = auto()        # List of values
    REF = auto()         # Reference to another entity


class Cardinality(Enum):
    """Relationship cardinalities"""
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_ONE = "N:1"
    MANY_TO_MANY = "N:M"


class Operation(Enum):
    """Universal CRUD+ operations"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    SEARCH = "search"
    FILTER = "filter"
    SORT = "sort"
    EXPORT = "export"
    IMPORT = "import"


@dataclass
class Constraint:
    """Field constraint"""
    name: str               # required, min, max, pattern, unique, etc.
    value: Any = None       # constraint parameter


@dataclass
class Field:
    """A typed, constrained field"""
    name: str
    type: FieldType
    constraints: List[Constraint] = field(default_factory=list)
    default: Any = None
    enum_values: List[str] = field(default_factory=list)  # For ENUM type
    ref_entity: Optional[str] = None  # For REF type

    @property
    def is_required(self) -> bool:
        return any(c.name == "required" for c in self.constraints)

    @property
    def python_type(self) -> str:
        mapping = {
            FieldType.STRING: "str",
            FieldType.INT: "int",
            FieldType.FLOAT: "float",
            FieldType.BOOL: "bool",
            FieldType.DATE: "date",
            FieldType.DATETIME: "datetime",
            FieldType.TEXT: "str",
            FieldType.EMAIL: "str",
            FieldType.URL: "str",
            FieldType.ENUM: "str",
            FieldType.LIST: "list",
            FieldType.REF: "int",
        }
        return mapping.get(self.type, "str")

    @property
    def html_input_type(self) -> str:
        mapping = {
            FieldType.STRING: "text",
            FieldType.INT: "number",
            FieldType.FLOAT: "number",
            FieldType.BOOL: "checkbox",
            FieldType.DATE: "date",
            FieldType.DATETIME: "datetime-local",
            FieldType.TEXT: "textarea",
            FieldType.EMAIL: "email",
            FieldType.URL: "url",
            FieldType.ENUM: "select",
            FieldType.LIST: "text",
            FieldType.REF: "select",
        }
        return mapping.get(self.type, "text")


@dataclass
class Entity:
    """A domain entity (model/table)"""
    name: str
    fields: List[Field] = field(default_factory=list)
    operations: Set[Operation] = field(default_factory=lambda: {
        Operation.CREATE, Operation.READ, Operation.UPDATE,
        Operation.DELETE, Operation.LIST
    })

    @property
    def table_name(self) -> str:
        return self.name.lower() + "s"

    @property
    def primary_display_field(self) -> Optional[Field]:
        """Find the best field to use as display name"""
        for f in self.fields:
            if f.name in ("name", "title", "label"):
                return f
        # Return first string field
        for f in self.fields:
            if f.type == FieldType.STRING:
                return f
        return self.fields[0] if self.fields else None


@dataclass
class Relation:
    """Relationship between entities"""
    from_entity: str
    to_entity: str
    cardinality: Cardinality
    name: Optional[str] = None  # e.g., "ingredients" for Recipe->Ingredient
    cascade_delete: bool = False


@dataclass
class Message:
    """An event/action in the system"""
    entity: str
    operation: Operation
    payload_schema: Dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return f"{self.entity}_{self.operation.value}"

    @property
    def handler_name(self) -> str:
        return f"handle_{self.name}"


@dataclass
class ViewSpec:
    """Specification for a view"""
    name: str
    entity: Optional[str] = None
    view_type: str = "list"  # list, detail, form, card, table
    fields: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)


@dataclass
class AppModel:
    """Complete app model - the algebraic representation"""
    name: str
    entities: List[Entity] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    views: List[ViewSpec] = field(default_factory=list)

    def get_entity(self, name: str) -> Optional[Entity]:
        for e in self.entities:
            if e.name.lower() == name.lower():
                return e
        return None

    def get_relations_for(self, entity_name: str) -> List[Relation]:
        return [r for r in self.relations
                if r.from_entity.lower() == entity_name.lower()
                or r.to_entity.lower() == entity_name.lower()]


# =============================================================================
# PARSER: Description → AppModel
# =============================================================================

class DescriptionParser:
    """Parse natural language into algebraic structures"""

    # Entity detection patterns (ordered by priority)
    ENTITY_PATTERNS = [
        # "recipe app with ingredients" - extract main entity
        r"(\w+)\s+app\b",
        # "task manager" - extract entity from compound
        r"(\w+)\s+(?:manager|tracker|organizer|planner|collection|catalog|log)\b",
        # "manage/track/organize X with Y"
        r"(?:manage|track|organize)\s+(\w+)\s+(?:with|and)\s+(\w+)",
        # "manage recipes"
        r"(?:manage|track|organize)\s+(\w+)",
        # "save recipes with ingredients"
        r"save\s+(\w+)\s+(?:with|and)\s+(\w+)",
        r"save\s+(\w+)",
        # "collection of recipes"
        r"collection\s+of\s+(\w+)",
        # Direct nouns after verbs
        r"(?:add|create|store|keep)\s+(\w+)",
        # "with X and Y" captures related entities
        r"\bwith\s+(\w+)\s+and\s+(\w+)",
        r"\bwith\s+(\w+)",
    ]

    # Relation patterns
    RELATION_PATTERNS = [
        # "recipes with ingredients"
        (r"(\w+)\s+with\s+(\w+)", Cardinality.ONE_TO_MANY),
        # "recipes have ingredients"
        (r"(\w+)\s+(?:have|has|contain|include)\s+(\w+)", Cardinality.ONE_TO_MANY),
        # "ingredients in recipes"
        (r"(\w+)\s+(?:in|of|for)\s+(\w+)", Cardinality.MANY_TO_ONE),
    ]

    # Field inference from context
    FIELD_INFERENCE = {
        "recipe": [
            Field("name", FieldType.STRING, [Constraint("required")]),
            Field("description", FieldType.TEXT),
            Field("prep_time", FieldType.INT),
            Field("cook_time", FieldType.INT),
            Field("servings", FieldType.INT),
        ],
        "ingredient": [
            Field("name", FieldType.STRING, [Constraint("required")]),
            Field("quantity", FieldType.STRING),
            Field("unit", FieldType.STRING),
        ],
        "task": [
            Field("title", FieldType.STRING, [Constraint("required")]),
            Field("description", FieldType.TEXT),
            Field("done", FieldType.BOOL, default=False),
            Field("due_date", FieldType.DATE),
            Field("priority", FieldType.ENUM, enum_values=["low", "medium", "high"]),
        ],
        "note": [
            Field("title", FieldType.STRING, [Constraint("required")]),
            Field("content", FieldType.TEXT, [Constraint("required")]),
            Field("created_at", FieldType.DATETIME),
        ],
        "contact": [
            Field("name", FieldType.STRING, [Constraint("required")]),
            Field("email", FieldType.EMAIL),
            Field("phone", FieldType.STRING),
            Field("notes", FieldType.TEXT),
        ],
        "event": [
            Field("title", FieldType.STRING, [Constraint("required")]),
            Field("description", FieldType.TEXT),
            Field("date", FieldType.DATETIME, [Constraint("required")]),
            Field("location", FieldType.STRING),
        ],
        "category": [
            Field("name", FieldType.STRING, [Constraint("required")]),
            Field("color", FieldType.STRING),
            Field("description", FieldType.TEXT),
        ],
        "movie": [
            Field("title", FieldType.STRING, [Constraint("required")]),
            Field("year", FieldType.INT),
            Field("genre", FieldType.STRING),
            Field("watched", FieldType.BOOL, default=False),
            Field("rating", FieldType.INT),
        ],
        "book": [
            Field("title", FieldType.STRING, [Constraint("required")]),
            Field("author", FieldType.STRING),
            Field("pages", FieldType.INT),
            Field("read", FieldType.BOOL, default=False),
            Field("rating", FieldType.INT),
        ],
        "product": [
            Field("name", FieldType.STRING, [Constraint("required")]),
            Field("price", FieldType.FLOAT),
            Field("quantity", FieldType.INT),
            Field("category", FieldType.STRING),
        ],
        "workout": [
            Field("name", FieldType.STRING, [Constraint("required")]),
            Field("date", FieldType.DATE),
            Field("duration", FieldType.INT),
            Field("notes", FieldType.TEXT),
        ],
        "rating": [
            Field("value", FieldType.INT, [Constraint("min", 1), Constraint("max", 5)]),
            Field("comment", FieldType.TEXT),
        ],
    }

    # Default fields for unknown entities
    DEFAULT_FIELDS = [
        Field("name", FieldType.STRING, [Constraint("required")]),
        Field("description", FieldType.TEXT),
        Field("created_at", FieldType.DATETIME),
    ]

    # Operation detection
    OPERATION_PATTERNS = {
        Operation.SEARCH: r"search|find|lookup|query",
        Operation.FILTER: r"filter|sort|organize|categorize",
        Operation.EXPORT: r"export|download|csv|backup",
        Operation.IMPORT: r"import|upload|load",
    }

    def parse(self, description: str) -> AppModel:
        """Parse description into AppModel"""
        desc_lower = description.lower()
        
        # Extract app name
        app_name = self._extract_app_name(desc_lower)
        
        # Extract entities
        entities = self._extract_entities(desc_lower)
        
        # Extract relations
        relations = self._extract_relations(desc_lower, entities)
        
        # Detect additional operations
        for entity in entities:
            for op, pattern in self.OPERATION_PATTERNS.items():
                if re.search(pattern, desc_lower):
                    entity.operations.add(op)
        
        # Generate messages from entities × operations
        messages = self._generate_messages(entities)
        
        # Generate default views
        views = self._generate_views(entities)
        
        return AppModel(
            name=app_name,
            entities=entities,
            relations=relations,
            messages=messages,
            views=views
        )

    def _extract_app_name(self, desc: str) -> str:
        """Extract app name from description"""
        match = re.search(r"(\w+)\s+app", desc)
        if match:
            return match.group(1).title() + "App"
        # Use first noun
        words = desc.split()
        for w in words:
            if len(w) > 3 and w.isalpha():
                return w.title() + "App"
        return "MyApp"

    def _extract_entities(self, desc: str) -> List[Entity]:
        """Extract entities from description"""
        found_entities: Dict[str, Entity] = {}
        
        # Skip words that aren't entities (noise words)
        skip_words = {"app", "manager", "tracker", "organizer", "planner", 
                      "collection", "catalog", "log", "list", "system",
                      "the", "a", "an", "my", "your", "our",
                      "simple", "basic", "quick", "easy", "new",
                      "with", "and", "or", "for", "to", "from"}
        
        for pattern in self.ENTITY_PATTERNS:
            for match in re.finditer(pattern, desc):
                # Get all captured groups (some patterns have 2 groups)
                groups = match.groups()
                for name in groups:
                    if name and name not in skip_words:
                        # Singularize
                        singular = self._singularize(name)
                        if singular not in found_entities and singular not in skip_words:
                            fields = self._infer_fields(singular)
                            found_entities[singular] = Entity(
                                name=singular.title(),
                                fields=fields
                            )
        
        # If no entities found, create a default one
        if not found_entities:
            found_entities["item"] = Entity(
                name="Item",
                fields=self.DEFAULT_FIELDS.copy()
            )
        
        return list(found_entities.values())

    def _extract_relations(self, desc: str, entities: List[Entity]) -> List[Relation]:
        """Extract relations between entities"""
        relations = []
        entity_names = {e.name.lower() for e in entities}
        
        # Skip words that shouldn't be treated as entities
        skip_words = {"app", "manager", "tracker", "organizer", "planner", 
                      "collection", "catalog", "log", "list", "system",
                      "the", "a", "an", "my", "your", "our"}
        
        for pattern, cardinality in self.RELATION_PATTERNS:
            for match in re.finditer(pattern, desc):
                from_name = self._singularize(match.group(1))
                to_name = self._singularize(match.group(2))
                
                # Skip noise words
                if from_name in skip_words or to_name in skip_words:
                    continue
                
                # Only create relation if at least one entity already exists
                if from_name in entity_names or to_name in entity_names:
                    # Add missing entity only if not a skip word
                    if from_name not in entity_names:
                        entities.append(Entity(
                            name=from_name.title(),
                            fields=self._infer_fields(from_name)
                        ))
                        entity_names.add(from_name)
                    if to_name not in entity_names:
                        entities.append(Entity(
                            name=to_name.title(),
                            fields=self._infer_fields(to_name)
                        ))
                        entity_names.add(to_name)
                    
                    relations.append(Relation(
                        from_entity=from_name.title(),
                        to_entity=to_name.title(),
                        cardinality=cardinality,
                        cascade_delete=True
                    ))
        
        return relations

    def _singularize(self, word: str) -> str:
        """Simple singularization"""
        if word.endswith("ies"):
            return word[:-3] + "y"
        if word.endswith("es") and len(word) > 4:
            return word[:-2]
        if word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        return word

    def _infer_fields(self, entity_name: str) -> List[Field]:
        """Infer fields for an entity based on its name"""
        name_lower = entity_name.lower()
        if name_lower in self.FIELD_INFERENCE:
            return [Field(f.name, f.type, f.constraints.copy(), f.default, 
                         f.enum_values.copy(), f.ref_entity)
                    for f in self.FIELD_INFERENCE[name_lower]]
        return [Field(f.name, f.type, f.constraints.copy(), f.default)
                for f in self.DEFAULT_FIELDS]

    def _generate_messages(self, entities: List[Entity]) -> List[Message]:
        """Generate messages from Entity × Operation"""
        messages = []
        for entity in entities:
            for op in entity.operations:
                payload = {}
                if op in (Operation.CREATE, Operation.UPDATE):
                    payload = {f.name: f.python_type for f in entity.fields}
                elif op == Operation.READ:
                    payload = {"id": "int"}
                elif op == Operation.DELETE:
                    payload = {"id": "int"}
                elif op == Operation.SEARCH:
                    payload = {"query": "str"}
                
                messages.append(Message(
                    entity=entity.name,
                    operation=op,
                    payload_schema=payload
                ))
        return messages

    def _generate_views(self, entities: List[Entity]) -> List[ViewSpec]:
        """Generate default views for entities"""
        views = []
        for entity in entities:
            # List view
            views.append(ViewSpec(
                name=f"{entity.name}List",
                entity=entity.name,
                view_type="list",
                fields=[f.name for f in entity.fields[:3]],
                actions=["view", "edit", "delete"]
            ))
            # Detail view
            views.append(ViewSpec(
                name=f"{entity.name}Detail",
                entity=entity.name,
                view_type="detail",
                fields=[f.name for f in entity.fields],
                actions=["edit", "delete", "back"]
            ))
            # Form view
            views.append(ViewSpec(
                name=f"{entity.name}Form",
                entity=entity.name,
                view_type="form",
                fields=[f.name for f in entity.fields],
                actions=["save", "cancel"]
            ))
        return views


# =============================================================================
# SYNTHESIZER: AppModel → Code
# =============================================================================

class CodeSynthesizer:
    """Synthesize code from AppModel - no templates!"""

    def synthesize_app(self, model: AppModel) -> Dict[str, str]:
        """Generate all code files from the model"""
        return {
            "app.py": self._synthesize_backend(model),
            "templates/index.html": self._synthesize_frontend(model),
            "requirements.txt": self._synthesize_requirements(model),
        }

    def _synthesize_backend(self, model: AppModel) -> str:
        """Synthesize Flask backend from model"""
        lines = []
        
        # Imports - derived from what we need
        imports = self._derive_imports(model)
        lines.extend(imports)
        lines.append("")
        
        # App initialization
        lines.extend(self._synthesize_app_init(model))
        lines.append("")
        
        # Models - one per entity
        for entity in model.entities:
            lines.extend(self._synthesize_model(entity, model.relations))
            lines.append("")
        
        # Routes - one per message
        for message in model.messages:
            lines.extend(self._synthesize_route(message, model))
            lines.append("")
        
        # Main route
        lines.extend(self._synthesize_main_route(model))
        lines.append("")
        
        # Main block
        lines.extend([
            "if __name__ == '__main__':",
            "    with app.app_context():",
            "        db.create_all()",
            "    app.run(debug=True, port=5000)",
        ])
        
        return "\n".join(lines)

    def _derive_imports(self, model: AppModel) -> List[str]:
        """Derive required imports from model structure"""
        imports = [
            "from flask import Flask, render_template, request, jsonify, redirect, url_for",
            "from flask_sqlalchemy import SQLAlchemy",
            "from datetime import datetime, date",
        ]
        
        # Add more imports based on operations
        ops = set()
        for entity in model.entities:
            ops.update(entity.operations)
        
        if Operation.EXPORT in ops:
            imports.append("import csv")
            imports.append("from io import StringIO")
        
        return imports

    def _synthesize_app_init(self, model: AppModel) -> List[str]:
        """Synthesize app initialization"""
        return [
            f"app = Flask(__name__)",
            f"app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{model.name.lower()}.db'",
            "app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False",
            "db = SQLAlchemy(app)",
        ]

    def _synthesize_model(self, entity: Entity, relations: List[Relation]) -> List[str]:
        """Synthesize SQLAlchemy model from Entity"""
        lines = [
            f"class {entity.name}(db.Model):",
            f"    __tablename__ = '{entity.table_name}'",
            "    id = db.Column(db.Integer, primary_key=True)",
        ]
        
        # Fields
        for field in entity.fields:
            col_type = self._field_to_column(field)
            nullable = "" if field.is_required else ", nullable=True"
            default = f", default={repr(field.default)}" if field.default is not None else ""
            lines.append(f"    {field.name} = db.Column({col_type}{nullable}{default})")
        
        # Relations
        for rel in relations:
            if rel.from_entity == entity.name:
                # This entity has many of the other
                backref = rel.to_entity.lower() + "s"
                lines.append(
                    f"    {backref} = db.relationship('{rel.to_entity}', backref='{entity.name.lower()}', lazy=True)"
                )
            elif rel.to_entity == entity.name:
                # This entity belongs to the other
                fk_name = rel.from_entity.lower() + "_id"
                lines.append(
                    f"    {fk_name} = db.Column(db.Integer, db.ForeignKey('{rel.from_entity.lower()}s.id'))"
                )
        
        # to_dict method
        lines.append("")
        lines.append("    def to_dict(self):")
        lines.append("        return {")
        lines.append("            'id': self.id,")
        for field in entity.fields:
            if field.type in (FieldType.DATE, FieldType.DATETIME):
                lines.append(f"            '{field.name}': str(self.{field.name}) if self.{field.name} else None,")
            else:
                lines.append(f"            '{field.name}': self.{field.name},")
        lines.append("        }")
        
        return lines

    def _field_to_column(self, field: Field) -> str:
        """Convert Field type to SQLAlchemy column type"""
        mapping = {
            FieldType.STRING: "db.String(200)",
            FieldType.INT: "db.Integer",
            FieldType.FLOAT: "db.Float",
            FieldType.BOOL: "db.Boolean",
            FieldType.DATE: "db.Date",
            FieldType.DATETIME: "db.DateTime",
            FieldType.TEXT: "db.Text",
            FieldType.EMAIL: "db.String(120)",
            FieldType.URL: "db.String(500)",
            FieldType.ENUM: "db.String(50)",
            FieldType.LIST: "db.Text",  # JSON serialized
            FieldType.REF: "db.Integer",
        }
        return mapping.get(field.type, "db.String(200)")

    def _synthesize_route(self, message: Message, model: AppModel) -> List[str]:
        """Synthesize a route handler from a Message"""
        entity = model.get_entity(message.entity)
        if not entity:
            return []
        
        op = message.operation
        route_name = message.name
        
        if op == Operation.LIST:
            return [
                f"@app.route('/api/{entity.table_name}', methods=['GET'])",
                f"def {route_name}():",
                f"    items = {entity.name}.query.all()",
                f"    return jsonify([item.to_dict() for item in items])",
            ]
        
        elif op == Operation.CREATE:
            return [
                f"@app.route('/api/{entity.table_name}', methods=['POST'])",
                f"def {route_name}():",
                f"    data = request.get_json()",
                f"    item = {entity.name}(",
                *[f"        {f.name}=data.get('{f.name}')," for f in entity.fields],
                f"    )",
                f"    db.session.add(item)",
                f"    db.session.commit()",
                f"    return jsonify(item.to_dict()), 201",
            ]
        
        elif op == Operation.READ:
            return [
                f"@app.route('/api/{entity.table_name}/<int:id>', methods=['GET'])",
                f"def {route_name}(id):",
                f"    item = {entity.name}.query.get_or_404(id)",
                f"    return jsonify(item.to_dict())",
            ]
        
        elif op == Operation.UPDATE:
            return [
                f"@app.route('/api/{entity.table_name}/<int:id>', methods=['PUT'])",
                f"def {route_name}(id):",
                f"    item = {entity.name}.query.get_or_404(id)",
                f"    data = request.get_json()",
                *[f"    if '{f.name}' in data: item.{f.name} = data['{f.name}']"
                  for f in entity.fields],
                f"    db.session.commit()",
                f"    return jsonify(item.to_dict())",
            ]
        
        elif op == Operation.DELETE:
            return [
                f"@app.route('/api/{entity.table_name}/<int:id>', methods=['DELETE'])",
                f"def {route_name}(id):",
                f"    item = {entity.name}.query.get_or_404(id)",
                f"    db.session.delete(item)",
                f"    db.session.commit()",
                f"    return '', 204",
            ]
        
        elif op == Operation.SEARCH:
            display_field = entity.primary_display_field
            search_field = display_field.name if display_field else "name"
            return [
                f"@app.route('/api/{entity.table_name}/search', methods=['GET'])",
                f"def {route_name}():",
                f"    q = request.args.get('q', '')",
                f"    items = {entity.name}.query.filter(",
                f"        {entity.name}.{search_field}.ilike(f'%{{q}}%')",
                f"    ).all()",
                f"    return jsonify([item.to_dict() for item in items])",
            ]
        
        return []

    def _synthesize_main_route(self, model: AppModel) -> List[str]:
        """Synthesize the main index route"""
        return [
            "@app.route('/')",
            "def index():",
            "    return render_template('index.html')",
        ]

    def _synthesize_frontend(self, model: AppModel) -> str:
        """Synthesize frontend HTML from model - generative, not template!"""
        # Build CSS from field types and view types
        css = self._synthesize_css(model)
        
        # Build HTML structure from entities and views
        html_body = self._synthesize_html_body(model)
        
        # Build JavaScript from messages
        js = self._synthesize_javascript(model)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{model.name}</title>
    <style>
{css}
    </style>
</head>
<body>
{html_body}
    <script>
{js}
    </script>
</body>
</html>"""

    def _synthesize_css(self, model: AppModel) -> str:
        """Synthesize CSS from model structure"""
        # Base styles derived from common patterns
        return """        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f5f5f5; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        h1 { color: #333; margin-bottom: 24px; }
        h2 { color: #555; margin-bottom: 16px; font-size: 18px; }
        .form-group { margin-bottom: 16px; }
        label { display: block; margin-bottom: 6px; font-weight: 500; color: #555; }
        input, textarea, select { width: 100%; padding: 10px 12px; border: 1px solid #ddd;
                                   border-radius: 8px; font-size: 14px; }
        input:focus, textarea:focus, select:focus { outline: none; border-color: #007bff; }
        textarea { min-height: 100px; resize: vertical; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer;
               font-size: 14px; font-weight: 500; transition: all 0.2s; }
        .btn-primary { background: #007bff; color: white; }
        .btn-primary:hover { background: #0056b3; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-danger:hover { background: #c82333; }
        .btn-secondary { background: #6c757d; color: white; }
        .list-item { display: flex; justify-content: space-between; align-items: center;
                     padding: 12px 0; border-bottom: 1px solid #eee; }
        .list-item:last-child { border-bottom: none; }
        .list-item-title { font-weight: 500; color: #333; }
        .list-item-actions { display: flex; gap: 8px; }
        .list-item-actions .btn { padding: 6px 12px; font-size: 12px; }
        .empty-state { text-align: center; padding: 40px; color: #888; }
        .tabs { display: flex; gap: 8px; margin-bottom: 20px; }
        .tab { padding: 8px 16px; background: #e9ecef; border-radius: 8px; cursor: pointer; }
        .tab.active { background: #007bff; color: white; }"""

    def _synthesize_html_body(self, model: AppModel) -> str:
        """Synthesize HTML body from entities"""
        sections = []
        
        # Header
        sections.append(f'    <div class="container">')
        sections.append(f'        <h1>{model.name}</h1>')
        
        # Tabs for each entity
        if len(model.entities) > 1:
            tabs = "".join(
                f'<div class="tab" onclick="showEntity(\'{e.name}\')">{e.name}s</div>'
                for e in model.entities
            )
            sections.append(f'        <div class="tabs">{tabs}</div>')
        
        # Section for each entity
        for entity in model.entities:
            sections.append(self._synthesize_entity_section(entity))
        
        sections.append('    </div>')
        
        return "\n".join(sections)

    def _synthesize_entity_section(self, entity: Entity) -> str:
        """Synthesize HTML section for an entity"""
        # Form for creating
        form_fields = "\n".join(
            self._synthesize_form_field(f)
            for f in entity.fields
        )
        
        return f"""
        <div class="entity-section" id="{entity.name.lower()}-section">
            <!-- Add Form -->
            <div class="card">
                <h2>Add {entity.name}</h2>
                <form id="{entity.name.lower()}-form" onsubmit="handleSubmit(event, '{entity.name}')">
{form_fields}
                    <button type="submit" class="btn btn-primary">Add {entity.name}</button>
                </form>
            </div>
            
            <!-- List -->
            <div class="card">
                <h2>{entity.name}s</h2>
                <div id="{entity.name.lower()}-list">
                    <div class="empty-state">No {entity.name.lower()}s yet</div>
                </div>
            </div>
        </div>"""

    def _synthesize_form_field(self, field: Field) -> str:
        """Synthesize a form field from Field type"""
        input_type = field.html_input_type
        required = "required" if field.is_required else ""
        
        if input_type == "textarea":
            return f"""                    <div class="form-group">
                        <label for="{field.name}">{field.name.replace('_', ' ').title()}</label>
                        <textarea id="{field.name}" name="{field.name}" {required}></textarea>
                    </div>"""
        elif input_type == "checkbox":
            return f"""                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="{field.name}" name="{field.name}">
                            {field.name.replace('_', ' ').title()}
                        </label>
                    </div>"""
        elif input_type == "select" and field.enum_values:
            options = "".join(
                f'<option value="{v}">{v}</option>'
                for v in field.enum_values
            )
            return f"""                    <div class="form-group">
                        <label for="{field.name}">{field.name.replace('_', ' ').title()}</label>
                        <select id="{field.name}" name="{field.name}" {required}>
                            <option value="">Select...</option>
                            {options}
                        </select>
                    </div>"""
        else:
            return f"""                    <div class="form-group">
                        <label for="{field.name}">{field.name.replace('_', ' ').title()}</label>
                        <input type="{input_type}" id="{field.name}" name="{field.name}" {required}>
                    </div>"""

    def _synthesize_javascript(self, model: AppModel) -> str:
        """Synthesize JavaScript from messages"""
        # Group entities for API calls
        entity_fetches = "\n".join(
            f"        fetch{e.name}s();"
            for e in model.entities
        )
        
        fetch_functions = "\n".join(
            self._synthesize_fetch_function(e)
            for e in model.entities
        )
        
        submit_handlers = "\n".join(
            self._synthesize_submit_handler(e)
            for e in model.entities
        )
        
        delete_handlers = "\n".join(
            self._synthesize_delete_handler(e)
            for e in model.entities
        )
        
        return f"""
        // State
        const state = {{{", ".join(f"'{e.name.lower()}s': []" for e in model.entities)}}};
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
{entity_fetches}
        }});
        
        // Fetch functions
{fetch_functions}
        
        // Submit handler
        function handleSubmit(event, entityName) {{
            event.preventDefault();
            const form = event.target;
            const data = Object.fromEntries(new FormData(form));
            
            // Handle checkboxes
            form.querySelectorAll('input[type="checkbox"]').forEach(cb => {{
                data[cb.name] = cb.checked;
            }});
            
            switch(entityName) {{
{submit_handlers}
            }}
        }}
        
        // Delete handlers
{delete_handlers}
        
        // Render functions
{self._synthesize_render_functions(model)}
        
        // Tab switching
        function showEntity(name) {{
            document.querySelectorAll('.entity-section').forEach(s => s.style.display = 'none');
            document.getElementById(name.toLowerCase() + '-section').style.display = 'block';
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
        }}"""

    def _synthesize_fetch_function(self, entity: Entity) -> str:
        """Synthesize fetch function for entity"""
        return f"""
        function fetch{entity.name}s() {{
            fetch('/api/{entity.table_name}')
                .then(r => r.json())
                .then(data => {{
                    state.{entity.name.lower()}s = data;
                    render{entity.name}s();
                }});
        }}"""

    def _synthesize_submit_handler(self, entity: Entity) -> str:
        """Synthesize submit case for entity"""
        return f"""                case '{entity.name}':
                    fetch('/api/{entity.table_name}', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }}).then(() => {{
                        form.reset();
                        fetch{entity.name}s();
                    }});
                    break;"""

    def _synthesize_delete_handler(self, entity: Entity) -> str:
        """Synthesize delete function for entity"""
        return f"""
        function delete{entity.name}(id) {{
            if (!confirm('Delete this {entity.name.lower()}?')) return;
            fetch('/api/{entity.table_name}/' + id, {{method: 'DELETE'}})
                .then(() => fetch{entity.name}s());
        }}"""

    def _synthesize_render_functions(self, model: AppModel) -> str:
        """Synthesize render functions for all entities"""
        return "\n".join(
            self._synthesize_render_function(e)
            for e in model.entities
        )

    def _synthesize_render_function(self, entity: Entity) -> str:
        """Synthesize render function for entity"""
        display_field = entity.primary_display_field
        display_name = display_field.name if display_field else "name"
        
        return f"""
        function render{entity.name}s() {{
            const list = document.getElementById('{entity.name.lower()}-list');
            if (state.{entity.name.lower()}s.length === 0) {{
                list.innerHTML = '<div class="empty-state">No {entity.name.lower()}s yet</div>';
                return;
            }}
            list.innerHTML = state.{entity.name.lower()}s.map(item => `
                <div class="list-item">
                    <span class="list-item-title">${{item.{display_name} || 'Untitled'}}</span>
                    <div class="list-item-actions">
                        <button class="btn btn-danger" onclick="delete{entity.name}(${{item.id}})">Delete</button>
                    </div>
                </div>
            `).join('');
        }}"""

    def _synthesize_requirements(self, model: AppModel) -> str:
        """Synthesize requirements.txt"""
        return "flask==3.0.2\nflask-sqlalchemy==3.1.1\n"


# =============================================================================
# PUBLIC API
# =============================================================================

def parse(description: str) -> AppModel:
    """Parse a description into an AppModel"""
    parser = DescriptionParser()
    return parser.parse(description)


def synthesize(model: AppModel) -> Dict[str, str]:
    """Synthesize code from an AppModel"""
    synthesizer = CodeSynthesizer()
    return synthesizer.synthesize_app(model)


def build(description: str) -> Dict[str, str]:
    """One-shot: description → code files"""
    model = parse(description)
    return synthesize(model)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python app_algebra.py 'description'")
        print("\nExamples:")
        print("  python app_algebra.py 'recipe app with ingredients'")
        print("  python app_algebra.py 'task manager with categories'")
        print("  python app_algebra.py 'movie collection with ratings'")
        sys.exit(1)
    
    description = " ".join(sys.argv[1:])
    
    print(f"\n{'='*60}")
    print(f"DESCRIPTION: {description}")
    print(f"{'='*60}\n")
    
    # Parse
    model = parse(description)
    
    print("ENTITIES:")
    for e in model.entities:
        print(f"  {e.name}:")
        for f in e.fields:
            req = " (required)" if f.is_required else ""
            print(f"    - {f.name}: {f.type.name}{req}")
    
    print("\nRELATIONS:")
    for r in model.relations:
        print(f"  {r.from_entity} --[{r.cardinality.value}]--> {r.to_entity}")
    
    print("\nMESSAGES:")
    for m in model.messages:
        print(f"  {m.name}")
    
    print("\nVIEWS:")
    for v in model.views:
        print(f"  {v.name} ({v.view_type})")
    
    # Synthesize
    print(f"\n{'='*60}")
    print("SYNTHESIZING CODE...")
    print(f"{'='*60}\n")
    
    files = synthesize(model)
    
    for filename, content in files.items():
        print(f"\n--- {filename} ({len(content)} chars) ---")
        if len(content) < 2000:
            print(content[:2000])
        else:
            print(content[:1000])
            print(f"\n... ({len(content) - 1000} more chars)")
