"""Domain parser - Extracts domain models from natural language descriptions."""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class DomainModel:
    """A detected domain entity with fields."""
    name: str           # e.g. "Recipe"
    table_name: str     # e.g. "recipe"
    fields: List[Tuple[str, str, bool]]  # (name, sql_type, nullable)
    has_relationship: str = ""  # parent model name if any


# Keyword → (model_name, [(field_name, sql_type, nullable), ...])
DOMAIN_CATALOG = {
    # Food / Recipes
    r"recipe|cook|meal|dish|menu": {
        "name": "Recipe",
        "fields": [
            ("title", "db.String(200)", False),
            ("description", "db.Text", True),
            ("ingredients", "db.Text", True),
            ("instructions", "db.Text", True),
            ("cook_time_minutes", "db.Integer", True),
            ("servings", "db.Integer", True),
            ("rating", "db.Float", True),
            ("category", "db.String(80)", True),
        ],
    },
    # Todos (explicit - maps to Todo)
    r"\btodo\b|to-do": {
        "name": "Todo",
        "fields": [
            ("title", "db.String(200)", False),
            ("description", "db.Text", True),
            ("done", "db.Boolean", False),
            ("priority", "db.String(20)", True),
            ("due_date", "db.DateTime", True),
        ],
    },
    # Tasks (more generic task management)
    r"task|checklist|kanban": {
        "name": "Task",
        "fields": [
            ("title", "db.String(200)", False),
            ("description", "db.Text", True),
            ("done", "db.Boolean", False),
            ("priority", "db.String(20)", True),
            ("due_date", "db.DateTime", True),
        ],
    },
    # Tags (when explicitly mentioned)
    r"\bwith\s+tags?\b|\btag(s|ging)?\b": {
        "name": "Tag",
        "fields": [
            ("name", "db.String(80)", False),
            ("color", "db.String(20)", True),
        ],
    },
    # Inventory / Products
    r"inventory|product|stock|warehouse|store|shop": {
        "name": "Product",
        "fields": [
            ("name", "db.String(200)", False),
            ("sku", "db.String(50)", True),
            ("quantity", "db.Integer", False),
            ("price", "db.Float", True),
            ("category", "db.String(80)", True),
            ("description", "db.Text", True),
        ],
    },
    # Workouts / Fitness
    r"workout|exercise|fitness|gym|training": {
        "name": "Workout",
        "fields": [
            ("name", "db.String(200)", False),
            ("exercise_type", "db.String(80)", True),
            ("sets", "db.Integer", True),
            ("reps", "db.Integer", True),
            ("weight", "db.Float", True),
            ("duration_minutes", "db.Integer", True),
            ("notes", "db.Text", True),
        ],
    },
    # Blog / Posts
    r"blog|post|article|write|journal|diary": {
        "name": "Post",
        "fields": [
            ("title", "db.String(200)", False),
            ("content", "db.Text", False),
            ("slug", "db.String(200)", True),
            ("published", "db.Boolean", False),
            ("tags", "db.String(200)", True),
        ],
    },
    # Contacts / CRM
    r"contact|customer|client|crm|address book": {
        "name": "Contact",
        "fields": [
            ("name", "db.String(150)", False),
            ("email", "db.String(120)", True),
            ("phone", "db.String(30)", True),
            ("company", "db.String(150)", True),
            ("notes", "db.Text", True),
        ],
    },
    # Events / Calendar
    r"event|calendar|booking|appointment|schedule": {
        "name": "Event",
        "fields": [
            ("title", "db.String(200)", False),
            ("description", "db.Text", True),
            ("start_time", "db.DateTime", False),
            ("end_time", "db.DateTime", True),
            ("location", "db.String(200)", True),
        ],
    },
    # Notes / Knowledge
    r"note|snippet|bookmark|knowledge|wiki": {
        "name": "Note",
        "fields": [
            ("title", "db.String(200)", False),
            ("content", "db.Text", False),
            ("category", "db.String(80)", True),
            ("pinned", "db.Boolean", False),
        ],
    },
    # Movies / Media
    r"movie|film|show|series|media|watch": {
        "name": "Movie",
        "fields": [
            ("title", "db.String(200)", False),
            ("year", "db.Integer", True),
            ("genre", "db.String(80)", True),
            ("rating", "db.Float", True),
            ("watched", "db.Boolean", False),
            ("notes", "db.Text", True),
        ],
    },
    # Habits / Tracking
    r"habit|tracker|streak|daily|check.?in|log": {
        "name": "Habit",
        "fields": [
            ("name", "db.String(200)", False),
            ("description", "db.Text", True),
            ("target_per_day", "db.Integer", True),
            ("completed_today", "db.Boolean", False),
            ("streak", "db.Integer", True),
        ],
    },
    # Generic Item (fallback)
    r"item|thing|record|entry": {
        "name": "Item",
        "fields": [
            ("name", "db.String(200)", False),
            ("description", "db.Text", True),
            ("category", "db.String(80)", True),
            ("status", "db.String(40)", True),
        ],
    },
}


def parse_description(description: str) -> List[DomainModel]:
    """Extract domain models from a user's app description."""
    desc_lower = description.lower()
    found = []
    seen_names = set()

    for pattern, model_def in DOMAIN_CATALOG.items():
        if re.search(pattern, desc_lower):
            name = model_def["name"]
            if name not in seen_names:
                seen_names.add(name)
                found.append(DomainModel(
                    name=name,
                    table_name=name.lower(),
                    fields=model_def["fields"],
                ))

    # Fallback: if nothing matched and they want data, give them a generic Item
    if not found:
        fallback = DOMAIN_CATALOG[r"item|thing|record|entry"]
        found.append(DomainModel(
            name=fallback["name"],
            table_name="item",
            fields=fallback["fields"],
        ))

    return found
