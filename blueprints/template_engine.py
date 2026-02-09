"""
Template-Based Code Generator

Generates working code from pre-written templates without requiring LLM.
Faster, deterministic, and works offline.

Usage:
    from template_engine import TemplateCodeGenerator
    
    gen = TemplateCodeGenerator(blueprint, stack, project_name)
    app_code = gen.generate_app()
    model_code = gen.generate_model(model_dict)
    routes_code = gen.generate_routes(entity_name)
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any

# Template directory
TEMPLATES_DIR = Path(__file__).parent / "templates"


class TemplateCodeGenerator:
    """
    Generate code from pre-written templates.
    
    No LLM required - uses pattern substitution for customization.
    Same interface as LLMCodeGenerator for drop-in replacement.
    """
    
    def __init__(self, blueprint: Dict, stack: str, project_name: str):
        self.blueprint = blueprint
        self.stack = stack.lower()
        self.project_name = project_name
        self.project_name_lower = project_name.lower().replace(" ", "-")
        
        # Validate stack has templates
        self.stack_dir = TEMPLATES_DIR / self.stack
        if not self.stack_dir.exists():
            available = [d.name for d in TEMPLATES_DIR.iterdir() if d.is_dir()]
            raise ValueError(f"No templates for stack '{stack}'. Available: {available}")
        
        # Extract primary entity from blueprint
        self.primary_entity = self._extract_primary_entity()
    
    def _extract_primary_entity(self) -> str:
        """Extract the primary entity name from the blueprint."""
        # Look for models in Data Model section
        data_model = self._get_section("Data Model")
        if data_model:
            # Find first ### heading
            match = re.search(r"###\s+(\w+)", data_model)
            if match:
                return match.group(1)
        
        # Fall back to inferring from blueprint name
        name = self.blueprint.get("name", "item")
        # learning-app -> Learning, task-manager -> Task
        return name.split("-")[0].title()
    
    def _get_section(self, name: str) -> str:
        """Get a blueprint section by partial name match."""
        for section_name, content in self.blueprint.get("sections", {}).items():
            if name.lower() in section_name.lower():
                return content
        return ""
    
    def _load_template(self, template_name: str) -> str:
        """Load a template file."""
        template_path = self.stack_dir / f"{template_name}.template"
        if not template_path.exists():
            return ""
        return template_path.read_text(encoding="utf-8")
    
    def _substitute(self, template: str, **kwargs) -> str:
        """
        Substitute placeholders in template.
        
        Uses {{PLACEHOLDER}} format for simple replacement.
        """
        result = template
        
        # Default substitutions
        defaults = {
            "PROJECT_NAME": self.project_name,
            "PROJECT_NAME_LOWER": self.project_name_lower,
            "BLUEPRINT_NAME": self.blueprint.get("title", "Blueprint"),
            "ENTITY_NAME": self.primary_entity,
            "ENTITY_LOWER": self.primary_entity.lower(),
            "ENTITY_UPPER": self.primary_entity.upper(),
        }
        defaults.update(kwargs)
        
        for key, value in defaults.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        
        return result
    
    def _format_fields_doc(self, fields: List[Dict]) -> str:
        """Format fields as documentation comments."""
        if not fields:
            return "   *   (no fields defined)"
        
        lines = []
        for field in fields:
            name = field.get("name", "field")
            ftype = field.get("type", "string")
            lines.append(f"   *   {name}: {ftype}")
        return "\n".join(lines)
    
    def _format_fields_definition(self, fields: List[Dict], stack: str) -> str:
        """Format fields as code definitions."""
        if not fields:
            if stack in ("flask", "fastapi"):
                return "    name: str = ''"
            else:
                return "    this.name = data.name || '';"
        
        lines = []
        for field in fields:
            name = field.get("name", "field")
            ftype = field.get("type", "string").lower()
            
            if stack in ("flask", "fastapi"):
                # Python type mapping
                py_type = {
                    "string": "str",
                    "text": "str",
                    "integer": "int",
                    "number": "float",
                    "boolean": "bool",
                    "array": "List",
                    "list": "List",
                    "date": "datetime",
                    "datetime": "datetime",
                    "json": "Dict",
                    "object": "Dict",
                }.get(ftype, "str")
                
                default = {
                    "str": "''",
                    "int": "0",
                    "float": "0.0",
                    "bool": "False",
                    "List": "field(default_factory=list)",
                    "Dict": "field(default_factory=dict)",
                    "datetime": "field(default_factory=datetime.now)",
                }.get(py_type, "None")
                
                lines.append(f"    {name}: {py_type} = {default}")
            else:
                # JavaScript
                default = {
                    "string": "''",
                    "text": "''",
                    "integer": "0",
                    "number": "0",
                    "boolean": "false",
                    "array": "[]",
                    "list": "[]",
                    "object": "{}",
                }.get(ftype, "null")
                
                lines.append(f"    this.{name} = data.{name} || {default};")
        
        return "\n".join(lines)
    
    def _format_fields_optional(self, fields: List[Dict]) -> str:
        """Format fields as optional (for update schemas)."""
        if not fields:
            return "    name: Optional[str] = None"
        
        lines = []
        for field in fields:
            name = field.get("name", "field")
            ftype = field.get("type", "string").lower()
            
            py_type = {
                "string": "str",
                "text": "str",
                "integer": "int",
                "number": "float",
                "boolean": "bool",
                "array": "List",
                "list": "List",
            }.get(ftype, "str")
            
            lines.append(f"    {name}: Optional[{py_type}] = None")
        
        return "\n".join(lines)
    
    def generate_app(self) -> str:
        """Generate the main application file."""
        print(f"   📦 Generating app from template...")
        
        template = self._load_template("app")
        if not template:
            return f"# No app template for {self.stack}\n"
        
        return self._substitute(template)
    
    def generate_model(self, model: Dict) -> str:
        """Generate a model implementation."""
        model_name = model.get("name", "Item")
        print(f"   📦 Generating {model_name} model from template...")
        
        template = self._load_template("model")
        if not template:
            return f"# No model template for {self.stack}\n"
        
        fields = model.get("fields", [])
        
        return self._substitute(
            template,
            MODEL_NAME=model_name,
            MODEL_LOWER=model_name.lower(),
            FIELDS_DOC=self._format_fields_doc(fields),
            FIELDS_DEFINITION=self._format_fields_definition(fields, self.stack),
            FIELDS_OPTIONAL=self._format_fields_optional(fields),
        )
    
    def generate_routes(self, entity_name: str) -> str:
        """Generate routes for an entity."""
        print(f"   📦 Generating {entity_name} routes from template...")
        
        template = self._load_template("routes")
        if not template:
            return f"# No routes template for {self.stack}\n"
        
        return self._substitute(
            template,
            ENTITY_NAME=entity_name,
            ENTITY_LOWER=entity_name.lower(),
            ENTITY_UPPER=entity_name.upper(),
        )
    
    def generate_component(self, name: str, component_type: str = "List") -> str:
        """Generate a React component."""
        if self.stack != "react":
            return ""
        
        print(f"   📦 Generating {name} component from template...")
        
        # Map component type to template
        template_map = {
            "list": "List",
            "detail": "Detail",
            "form": "Form",
            "app": "App",
        }
        template_name = template_map.get(component_type.lower(), "List")
        
        template = self._load_template(template_name)
        if not template:
            return f"// No {template_name} template\n"
        
        return self._substitute(
            template,
            ENTITY_NAME=name,
            ENTITY_LOWER=name.lower(),
        )
    
    def generate_api_service(self) -> str:
        """Generate API service (for React)."""
        if self.stack != "react":
            return ""
        
        print(f"   📦 Generating API service from template...")
        
        template = self._load_template("api")
        if not template:
            return "// No API template\n"
        
        return self._substitute(template)
    
    def generate_styles(self) -> str:
        """Generate styles (for React)."""
        if self.stack != "react":
            return ""
        
        print(f"   📦 Generating styles from template...")
        
        template = self._load_template("styles")
        if not template:
            return "/* No styles template */\n"
        
        return self._substitute(template)


def get_template_generator(
    blueprint: Dict,
    stack: str,
    project_name: str
) -> TemplateCodeGenerator:
    """
    Factory function to create a template generator.
    
    Same signature as get_llm_generator for easy switching.
    """
    return TemplateCodeGenerator(blueprint, stack, project_name)


def list_available_templates() -> Dict[str, List[str]]:
    """List all available templates by stack."""
    result = {}
    
    if not TEMPLATES_DIR.exists():
        return result
    
    for stack_dir in TEMPLATES_DIR.iterdir():
        if stack_dir.is_dir() and not stack_dir.name.startswith("_"):
            templates = [
                f.stem for f in stack_dir.glob("*.template")
            ]
            if templates:
                result[stack_dir.name] = sorted(templates)
    
    return result


# Quick test
if __name__ == "__main__":
    # Test with a mock blueprint
    mock_blueprint = {
        "name": "test-app",
        "title": "Test Application",
        "sections": {
            "Data Model": """
### Item
```
name: string
description: text
quantity: integer
active: boolean
```

### Category
```
name: string
parent_id: string
```
"""
        }
    }
    
    print("Available templates:", list_available_templates())
    print()
    
    for stack in ["flask", "fastapi", "express"]:
        try:
            gen = TemplateCodeGenerator(mock_blueprint, stack, "TestProject")
            print(f"\n=== {stack.upper()} ===")
            print(f"Primary entity: {gen.primary_entity}")
            
            # Generate app
            app_code = gen.generate_app()
            print(f"App code length: {len(app_code)} chars")
            
            # Generate model
            model_code = gen.generate_model({
                "name": "Item",
                "fields": [
                    {"name": "name", "type": "string"},
                    {"name": "quantity", "type": "integer"},
                ]
            })
            print(f"Model code length: {len(model_code)} chars")
            
        except Exception as e:
            print(f"  Error: {e}")
