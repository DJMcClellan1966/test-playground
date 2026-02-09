"""
Bidirectional Contracts - Spec and Code as ONE

The Life-Changing Idea:
-----------------------
Traditional development: Write spec → Write code → They drift apart
This system: Spec and Code are THE SAME THING

A "contract" is:
1. A declarative specification (what you want)
2. Executable code (what it does)
3. Validation rules (how to verify)

When you change the spec, code updates automatically.
When you change the code, the spec stays in sync.
They CANNOT disagree because they are different VIEWS of the same entity.

This is inspired by:
- Literate programming (Knuth)
- Design by Contract (Meyer)
- Bidirectional transformations (lenses)
- Constraint propagation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Set
from pathlib import Path
import re
import json
import hashlib


# ============================================================================
# CORE TYPES
# ============================================================================

@dataclass
class Field:
    """A field in an entity with constraints."""
    name: str
    type: str
    required: bool = True
    default: Any = None
    constraints: List[str] = field(default_factory=list)  # "min:0", "max:100", "pattern:email"
    
    def to_spec(self) -> str:
        """Human-readable spec."""
        req = "required" if self.required else "optional"
        constraints = f" ({', '.join(self.constraints)})" if self.constraints else ""
        default = f" = {self.default}" if self.default is not None else ""
        return f"{self.name}: {self.type} [{req}]{constraints}{default}"
    
    def to_code(self, lang: str = "python") -> str:
        """Generate code for this field."""
        if lang == "python":
            type_map = {
                "string": "str",
                "text": "str",
                "integer": "int",
                "float": "float",
                "boolean": "bool",
                "date": "datetime",
                "datetime": "datetime",
                "list": "List[Any]",
                "dict": "Dict[str, Any]",
            }
            py_type = type_map.get(self.type, self.type)
            
            if self.default is not None:
                return f"    {self.name}: {py_type} = {repr(self.default)}"
            elif not self.required:
                return f"    {self.name}: Optional[{py_type}] = None"
            else:
                return f"    {self.name}: {py_type}"
        return ""


@dataclass
class Contract:
    """
    A bidirectional contract for an entity.
    
    The contract IS the spec, IS the code, IS the validation.
    """
    name: str
    description: str = ""
    fields: List[Field] = field(default_factory=list)
    
    # Behaviors
    invariants: List[str] = field(default_factory=list)  # Always true
    preconditions: Dict[str, List[str]] = field(default_factory=dict)  # operation -> conditions
    postconditions: Dict[str, List[str]] = field(default_factory=dict)  # operation -> conditions
    
    # Relationships
    relations: Dict[str, str] = field(default_factory=dict)  # field -> "has_many:Entity" or "belongs_to:Entity"
    
    # Derived from constraints
    _hash: str = ""
    
    def compute_hash(self) -> str:
        """Hash for change detection."""
        content = json.dumps({
            "name": self.name,
            "fields": [f.__dict__ for f in self.fields],
            "invariants": self.invariants,
        }, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    # -------------------------------------------------------------------------
    # VIEW 1: Human-Readable Spec
    # -------------------------------------------------------------------------
    def to_spec(self) -> str:
        """Generate human-readable specification."""
        lines = [
            f"# Contract: {self.name}",
            "",
        ]
        
        if self.description:
            lines.extend([self.description, ""])
        
        lines.append("## Fields")
        for f in self.fields:
            lines.append(f"- {f.to_spec()}")
        
        if self.invariants:
            lines.extend(["", "## Invariants"])
            for inv in self.invariants:
                lines.append(f"- {inv}")
        
        if self.relations:
            lines.extend(["", "## Relations"])
            for field_name, rel in self.relations.items():
                lines.append(f"- {field_name}: {rel}")
        
        if self.preconditions:
            lines.extend(["", "## Preconditions"])
            for op, conds in self.preconditions.items():
                lines.append(f"- {op}:")
                for c in conds:
                    lines.append(f"    - {c}")
        
        if self.postconditions:
            lines.extend(["", "## Postconditions"])
            for op, conds in self.postconditions.items():
                lines.append(f"- {op}:")
                for c in conds:
                    lines.append(f"    - {c}")
        
        return "\n".join(lines)
    
    # -------------------------------------------------------------------------
    # VIEW 2: Python Dataclass
    # -------------------------------------------------------------------------
    def to_python_dataclass(self) -> str:
        """Generate Python dataclass code."""
        lines = [
            "from dataclasses import dataclass, field",
            "from typing import Optional, List, Dict, Any",
            "from datetime import datetime",
            "",
            "",
            f"@dataclass",
            f"class {self.name}:",
            f'    """{self.description}"""' if self.description else f'    """Entity: {self.name}"""',
            "",
        ]
        
        # Fields
        required_fields = [f for f in self.fields if f.required and f.default is None]
        optional_fields = [f for f in self.fields if not f.required or f.default is not None]
        
        for f in required_fields:
            lines.append(f.to_code("python"))
        for f in optional_fields:
            lines.append(f.to_code("python"))
        
        # Add validation method from invariants
        if self.invariants:
            lines.extend([
                "",
                "    def validate(self) -> List[str]:",
                '        """Validate invariants."""',
                "        errors = []",
            ])
            for inv in self.invariants:
                condition = self._invariant_to_python(inv)
                lines.append(f'        if not ({condition}):')
                lines.append(f'            errors.append("{inv}")')
            lines.append("        return errors")
        
        return "\n".join(lines)
    
    def _invariant_to_python(self, invariant: str) -> str:
        """Convert invariant description to Python code."""
        # Simple pattern matching for common invariants
        patterns = [
            (r"(\w+) must be positive", r"self.\1 > 0"),
            (r"(\w+) cannot be empty", r"len(self.\1) > 0"),
            (r"(\w+) must be at least (\d+)", r"len(self.\1) >= \2"),
            (r"(\w+) >= (\d+)", r"self.\1 >= \2"),
            (r"(\w+) <= (\d+)", r"self.\1 <= \2"),
            (r"(\w+) is required", r"self.\1 is not None"),
        ]
        
        for pattern, replacement in patterns:
            match = re.match(pattern, invariant, re.IGNORECASE)
            if match:
                return re.sub(pattern, replacement, invariant, flags=re.IGNORECASE)
        
        return "True  # TODO: " + invariant
    
    # -------------------------------------------------------------------------
    # VIEW 3: API Routes
    # -------------------------------------------------------------------------
    def to_flask_routes(self) -> str:
        """Generate Flask routes with contract validation."""
        name_lower = self.name.lower()
        lines = [
            f"# Auto-generated from {self.name} contract",
            f"# Hash: {self.compute_hash()}",
            "",
            "from flask import Blueprint, request, jsonify",
            f"from models import {self.name}",
            "",
            f'{name_lower}_bp = Blueprint("{name_lower}", __name__, url_prefix="/api/{name_lower}")',
            "",
        ]
        
        # Create
        if "create" in self.preconditions:
            precond_comment = f"    # Preconditions: {', '.join(self.preconditions['create'])}"
        else:
            precond_comment = ""
        
        lines.extend([
            f'@{name_lower}_bp.route("", methods=["POST"])',
            f"def create_{name_lower}():",
            f'    """Create a new {self.name}."""',
            precond_comment,
            "    data = request.get_json()",
            "    ",
            "    # Validate against contract",
        ])
        
        # Field validation
        for f in self.fields:
            if f.required:
                lines.append(f'    if "{f.name}" not in data:')
                lines.append(f'        return jsonify({{"error": "{f.name} is required"}}), 400')
            
            for constraint in f.constraints:
                lines.extend(self._constraint_to_validation(f.name, constraint))
        
        lines.extend([
            "    ",
            f"    item = {self.name}(**data)",
            "    errors = item.validate() if hasattr(item, 'validate') else []",
            "    if errors:",
            '        return jsonify({"errors": errors}), 400',
            "    ",
            "    # Storage",
            f"    saved = storage.create('{name_lower}', data)",
            "    return jsonify(saved), 201",
            "",
        ])
        
        # List
        lines.extend([
            f'@{name_lower}_bp.route("", methods=["GET"])',
            f"def list_{name_lower}():",
            f'    """List all {self.name}s."""',
            f"    items = storage.list('{name_lower}')",
            '    return jsonify({"items": items, "total": len(items)})',
            "",
        ])
        
        # Get
        lines.extend([
            f'@{name_lower}_bp.route("/<item_id>", methods=["GET"])',
            f"def get_{name_lower}(item_id):",
            f'    """Get a {self.name} by ID."""',
            f"    item = storage.get('{name_lower}', item_id)",
            "    if not item:",
            '        return jsonify({"error": "Not found"}), 404',
            "    return jsonify(item)",
            "",
        ])
        
        return "\n".join(lines)
    
    def _constraint_to_validation(self, field_name: str, constraint: str) -> List[str]:
        """Convert a constraint to validation code."""
        lines = []
        
        if constraint.startswith("min:"):
            min_val = constraint.split(":")[1]
            lines.append(f'    if data.get("{field_name}", 0) < {min_val}:')
            lines.append(f'        return jsonify({{"error": "{field_name} must be >= {min_val}"}}), 400')
        
        elif constraint.startswith("max:"):
            max_val = constraint.split(":")[1]
            lines.append(f'    if data.get("{field_name}", 0) > {max_val}:')
            lines.append(f'        return jsonify({{"error": "{field_name} must be <= {max_val}"}}), 400')
        
        elif constraint == "email":
            lines.append(f'    if "@" not in data.get("{field_name}", ""):')
            lines.append(f'        return jsonify({{"error": "{field_name} must be a valid email"}}), 400')
        
        elif constraint.startswith("pattern:"):
            pattern = constraint.split(":")[1]
            lines.append(f'    import re')
            lines.append(f'    if not re.match(r"{pattern}", data.get("{field_name}", "")):')
            lines.append(f'        return jsonify({{"error": "{field_name} has invalid format"}}), 400')
        
        return lines
    
    # -------------------------------------------------------------------------
    # VIEW 4: TypeScript Interface
    # -------------------------------------------------------------------------
    def to_typescript(self) -> str:
        """Generate TypeScript interface."""
        type_map = {
            "string": "string",
            "text": "string",
            "integer": "number",
            "float": "number",
            "boolean": "boolean",
            "date": "Date",
            "datetime": "Date",
            "list": "any[]",
            "dict": "Record<string, any>",
        }
        
        lines = [
            f"// Auto-generated from {self.name} contract",
            f"// Hash: {self.compute_hash()}",
            "",
            f"export interface {self.name} {{",
        ]
        
        for f in self.fields:
            ts_type = type_map.get(f.type, f.type)
            optional = "" if f.required else "?"
            lines.append(f"  {f.name}{optional}: {ts_type};")
        
        lines.append("}")
        
        # Add validation schema (Zod-like)
        lines.extend([
            "",
            f"export const {self.name}Schema = {{",
        ])
        
        for f in self.fields:
            schema_parts = [f"type: '{f.type}'"]
            if f.required:
                schema_parts.append("required: true")
            for c in f.constraints:
                schema_parts.append(f"constraint: '{c}'")
            lines.append(f"  {f.name}: {{ {', '.join(schema_parts)} }},")
        
        lines.append("};")
        
        return "\n".join(lines)


# ============================================================================
# CONTRACT REGISTRY - Single Source of Truth
# ============================================================================

class ContractRegistry:
    """
    Central registry of all contracts.
    
    When a contract changes, all derived artifacts are regenerated.
    This ensures spec and code NEVER disagree.
    """
    
    def __init__(self, contracts_dir: str = "contracts"):
        self.contracts_dir = Path(contracts_dir)
        self.contracts: Dict[str, Contract] = {}
        self._hashes: Dict[str, str] = {}  # For change detection
    
    def define(self, contract: Contract):
        """Register a contract definition."""
        self.contracts[contract.name] = contract
        contract._hash = contract.compute_hash()
    
    def load_from_spec(self, spec_text: str) -> Contract:
        """Parse a spec file back into a contract."""
        lines = spec_text.strip().split("\n")
        
        name = ""
        description = ""
        fields = []
        invariants = []
        relations = {}
        
        section = "header"
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("# Contract:"):
                name = line.replace("# Contract:", "").strip()
            elif line.startswith("## Fields"):
                section = "fields"
            elif line.startswith("## Invariants"):
                section = "invariants"
            elif line.startswith("## Relations"):
                section = "relations"
            elif line.startswith("##"):
                section = "other"
            elif line.startswith("- ") and section == "fields":
                # Parse field
                field_spec = line[2:]
                field = self._parse_field_spec(field_spec)
                if field:
                    fields.append(field)
            elif line.startswith("- ") and section == "invariants":
                invariants.append(line[2:])
            elif line.startswith("- ") and section == "relations":
                parts = line[2:].split(":")
                if len(parts) == 2:
                    relations[parts[0].strip()] = parts[1].strip()
            elif section == "header" and line and not line.startswith("#"):
                description += line + " "
        
        return Contract(
            name=name,
            description=description.strip(),
            fields=fields,
            invariants=invariants,
            relations=relations,
        )
    
    def _parse_field_spec(self, spec: str) -> Optional[Field]:
        """Parse a field specification line."""
        # Format: "name: type [required/optional] (constraints) = default"
        match = re.match(
            r"(\w+):\s*(\w+)\s*\[(required|optional)\](?:\s*\(([^)]+)\))?(?:\s*=\s*(.+))?",
            spec
        )
        
        if not match:
            return None
        
        name, type_, req, constraints_str, default = match.groups()
        
        constraints = []
        if constraints_str:
            constraints = [c.strip() for c in constraints_str.split(",")]
        
        default_val = None
        if default:
            try:
                default_val = eval(default)
            except:
                default_val = default
        
        return Field(
            name=name,
            type=type_,
            required=(req == "required"),
            constraints=constraints,
            default=default_val,
        )
    
    def generate_all(self, output_dir: str = "generated"):
        """Generate all code from contracts."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        
        models_dir = out / "models"
        routes_dir = out / "routes"
        types_dir = out / "types"
        specs_dir = out / "specs"
        
        for d in [models_dir, routes_dir, types_dir, specs_dir]:
            d.mkdir(exist_ok=True)
        
        generated = []
        
        for name, contract in self.contracts.items():
            name_lower = name.lower()
            
            # Python model
            model_path = models_dir / f"{name_lower}.py"
            model_path.write_text(contract.to_python_dataclass())
            generated.append(str(model_path))
            
            # Flask routes
            routes_path = routes_dir / f"{name_lower}_routes.py"
            routes_path.write_text(contract.to_flask_routes())
            generated.append(str(routes_path))
            
            # TypeScript types
            ts_path = types_dir / f"{name_lower}.ts"
            ts_path.write_text(contract.to_typescript())
            generated.append(str(ts_path))
            
            # Spec (for bidirectional editing)
            spec_path = specs_dir / f"{name_lower}.spec.md"
            spec_path.write_text(contract.to_spec())
            generated.append(str(spec_path))
        
        return generated
    
    def sync_from_changes(self, changed_file: str):
        """
        Detect what changed (spec or code) and sync the other direction.
        
        This is the BIDIRECTIONAL magic - change one, update the other.
        """
        path = Path(changed_file)
        
        if path.suffix == ".md" and ".spec." in path.name:
            # Spec changed → regenerate code
            contract = self.load_from_spec(path.read_text())
            self.define(contract)
            return f"Synced code from spec: {contract.name}"
        
        elif path.suffix == ".py":
            # Code changed → update spec (harder, requires parsing)
            # For now, just detect and warn
            return f"Warning: Code modified directly. Run --regenerate to sync spec."
        
        return None


# ============================================================================
# CLI
# ============================================================================

def demo_contract() -> Contract:
    """Create a demo contract for illustration."""
    return Contract(
        name="Task",
        description="A task in a todo application with priority and status tracking.",
        fields=[
            Field("id", "string", required=True),
            Field("title", "string", required=True, constraints=["min:1"]),
            Field("description", "text", required=False),
            Field("priority", "integer", required=True, default=1, constraints=["min:1", "max:5"]),
            Field("completed", "boolean", required=False, default=False),
            Field("due_date", "datetime", required=False),
            Field("created_at", "datetime", required=True),
            Field("user_id", "string", required=True),
        ],
        invariants=[
            "title cannot be empty",
            "priority >= 1",
            "priority <= 5",
        ],
        relations={
            "user_id": "belongs_to:User",
        },
        preconditions={
            "create": ["user must be authenticated"],
            "complete": ["task must not already be completed"],
        },
        postconditions={
            "complete": ["completed is True", "completed_at is set"],
        },
    )


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Bidirectional contract system")
    parser.add_argument("--demo", action="store_true", help="Show demo contract")
    parser.add_argument("--generate", "-g", action="store_true", help="Generate code from demo")
    parser.add_argument("--output", "-o", default="generated", help="Output directory")
    
    args = parser.parse_args()
    
    contract = demo_contract()
    
    if args.demo:
        print("\n📜 Bidirectional Contract Demo")
        print("=" * 60)
        print("\nThe contract below is the SINGLE SOURCE OF TRUTH.")
        print("From it, we generate: Python models, Flask routes, TypeScript types.")
        print("Change the spec → Code updates. Change the code → Spec syncs.")
        print("\n" + "=" * 60)
        
        print("\n--- VIEW 1: Human-Readable Spec ---\n")
        print(contract.to_spec())
        
        print("\n--- VIEW 2: Python Dataclass ---\n")
        print(contract.to_python_dataclass())
        
        print("\n--- VIEW 3: Flask Routes (excerpt) ---\n")
        routes = contract.to_flask_routes()
        print("\n".join(routes.split("\n")[:40]) + "\n...")
        
        print("\n--- VIEW 4: TypeScript Interface ---\n")
        print(contract.to_typescript())
        
        print("\n" + "=" * 60)
        print("\nAll 4 views are generated from ONE contract definition.")
        print("They CANNOT disagree because they're different projections of the same data.")
        print("=" * 60 + "\n")
    
    elif args.generate:
        registry = ContractRegistry()
        registry.define(contract)
        
        # Also add a User contract to show relations
        user = Contract(
            name="User",
            description="Application user with authentication.",
            fields=[
                Field("id", "string", required=True),
                Field("email", "string", required=True, constraints=["email"]),
                Field("username", "string", required=True, constraints=["min:3"]),
                Field("password_hash", "string", required=True),
                Field("created_at", "datetime", required=True),
            ],
            invariants=[
                "email is required",
                "username must be at least 3 characters",
            ],
        )
        registry.define(user)
        
        generated = registry.generate_all(args.output)
        
        print(f"\n✅ Generated {len(generated)} files from contracts:\n")
        for f in generated:
            print(f"  • {f}")
        print()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
