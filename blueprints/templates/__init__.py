"""
Template Library for Blueprint Scaffolder.

Pre-written, working code templates that replace LLM generation.
Supports: Flask, FastAPI, React, Express

Each template is a complete, tested implementation that can be
customized by substituting variable names.
"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent

def get_template(stack: str, template_type: str) -> str:
    """Load a template file."""
    template_path = TEMPLATES_DIR / stack / f"{template_type}.template"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return ""


def list_templates() -> dict:
    """List all available templates by stack."""
    templates = {}
    for stack_dir in TEMPLATES_DIR.iterdir():
        if stack_dir.is_dir() and not stack_dir.name.startswith("_"):
            templates[stack_dir.name] = [
                f.stem for f in stack_dir.glob("*.template")
            ]
    return templates
