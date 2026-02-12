"""Trait Store - App-specific patterns that grow over time.

Traits capture the unique characteristics of specific app types
that the universal template + features alone cannot handle.

Traits are learned from:
1. Manual specification (seed data)
2. Successful builds (what worked)
3. User feedback (corrections)

Each trait includes:
- Domain models specific to that app type
- UI patterns preferred
- Special features/generators needed
- Keywords that trigger this trait
- Common answer defaults
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import json
import re
from pathlib import Path
from datetime import datetime


@dataclass
class DomainField:
    """A field in a domain model."""
    name: str
    type: str           # "string", "int", "float", "bool", "date", "text", "email"
    required: bool = True
    default: Any = None


@dataclass
class DomainModelSchema:
    """Schema for a domain model."""
    name: str
    fields: List[DomainField]
    relationships: List[str] = field(default_factory=list)  # Related model names


@dataclass 
class AppTrait:
    """Unique characteristics of a specific app type."""
    id: str
    name: str
    description: str
    
    # Domain-specific models
    models: List[DomainModelSchema] = field(default_factory=list)
    
    # UI/UX preferences
    ui_pattern: str = "list"  # "list", "card_grid", "canvas", "dashboard", "form"
    
    # Special code generators needed
    special_features: List[str] = field(default_factory=list)
    
    # Keywords that trigger this trait
    trigger_keywords: List[str] = field(default_factory=list)
    
    # Default answers to skip questions
    default_answers: Dict[str, Any] = field(default_factory=dict)
    
    # Preferred framework
    preferred_framework: Optional[str] = None
    
    # Features typically needed
    typical_features: List[str] = field(default_factory=list)
    
    # How many times this trait was used (for ranking)
    usage_count: int = 0
    
    # Last used timestamp
    last_used: Optional[str] = None
    
    def matches(self, description: str) -> float:
        """Score how well this trait matches a description."""
        desc_lower = description.lower()
        matches = sum(1 for kw in self.trigger_keywords if kw.lower() in desc_lower)
        if not self.trigger_keywords:
            return 0.0
        return matches / len(self.trigger_keywords)
    
    def to_dict(self) -> Dict:
        """Serialize to dict for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "models": [
                {
                    "name": m.name,
                    "fields": [{"name": f.name, "type": f.type, "required": f.required, "default": f.default} for f in m.fields],
                    "relationships": m.relationships,
                }
                for m in self.models
            ],
            "ui_pattern": self.ui_pattern,
            "special_features": self.special_features,
            "trigger_keywords": self.trigger_keywords,
            "default_answers": self.default_answers,
            "preferred_framework": self.preferred_framework,
            "typical_features": self.typical_features,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AppTrait':
        """Deserialize from dict."""
        models = []
        for m in data.get("models", []):
            fields = [DomainField(**f) for f in m.get("fields", [])]
            models.append(DomainModelSchema(
                name=m["name"],
                fields=fields,
                relationships=m.get("relationships", []),
            ))
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            models=models,
            ui_pattern=data.get("ui_pattern", "list"),
            special_features=data.get("special_features", []),
            trigger_keywords=data.get("trigger_keywords", []),
            default_answers=data.get("default_answers", {}),
            preferred_framework=data.get("preferred_framework"),
            typical_features=data.get("typical_features", []),
            usage_count=data.get("usage_count", 0),
            last_used=data.get("last_used"),
        )


# =====================================================================
# Seed Traits (Built-in knowledge)
# =====================================================================

SEED_TRAITS: Dict[str, AppTrait] = {
    "recipe_app": AppTrait(
        id="recipe_app",
        name="Recipe Collection",
        description="An app for managing recipes with ingredients",
        models=[
            DomainModelSchema(
                name="Recipe",
                fields=[
                    DomainField("title", "string"),
                    DomainField("description", "text", required=False),
                    DomainField("ingredients", "text"),
                    DomainField("instructions", "text"),
                    DomainField("cook_time_minutes", "int", required=False),
                    DomainField("servings", "int", required=False),
                    DomainField("rating", "float", required=False),
                    DomainField("category", "string", required=False),
                ],
                relationships=["Category", "Tag"],
            ),
        ],
        ui_pattern="card_grid",
        special_features=["ingredient_parser", "serving_scaler"],
        trigger_keywords=["recipe", "cook", "meal", "ingredient", "dish", "cuisine", "food"],
        default_answers={"needs_auth": False, "search": True, "export": True},
        preferred_framework="flask",
        typical_features=["database", "crud", "search", "export"],
    ),
    
    "todo_app": AppTrait(
        id="todo_app",
        name="Todo List",
        description="A task/todo tracking application",
        models=[
            DomainModelSchema(
                name="Task",
                fields=[
                    DomainField("title", "string"),
                    DomainField("description", "text", required=False),
                    DomainField("done", "bool", required=True, default=False),
                    DomainField("priority", "string", required=False),
                    DomainField("due_date", "date", required=False),
                ],
                relationships=["Category"],
            ),
        ],
        ui_pattern="list",
        special_features=["drag_reorder", "completion_animation"],
        trigger_keywords=["todo", "task", "checklist", "reminder", "to-do"],
        default_answers={"search": True, "export": False},
        preferred_framework="flask",
        typical_features=["database", "crud"],
    ),
    
    "game_generic": AppTrait(
        id="game_generic",
        name="Generic Game",
        description="A browser-based game",
        models=[
            DomainModelSchema(
                name="GameState",
                fields=[
                    DomainField("score", "int", default=0),
                    DomainField("level", "int", default=1),
                    DomainField("lives", "int", default=3),
                    DomainField("is_running", "bool", default=True),
                ],
            ),
        ],
        ui_pattern="canvas",
        special_features=["collision_detection", "physics_2d"],
        trigger_keywords=["game", "play", "score", "level", "player"],
        default_answers={"needs_auth": False, "has_data": False},
        preferred_framework="html_canvas",
        typical_features=["game_loop", "input_handler", "scoring"],
    ),
    
    "quiz_app": AppTrait(
        id="quiz_app",
        name="Quiz/Trivia",
        description="A quiz or trivia application",
        models=[
            DomainModelSchema(
                name="Question",
                fields=[
                    DomainField("text", "string"),
                    DomainField("correct_answer", "string"),
                    DomainField("wrong_answers", "text"),  # JSON array
                    DomainField("category", "string", required=False),
                    DomainField("difficulty", "int", default=1),
                ],
            ),
        ],
        ui_pattern="form",
        special_features=["shuffle_answers", "timed_questions"],
        trigger_keywords=["quiz", "trivia", "question", "answer", "test"],
        default_answers={"needs_auth": False, "search": False},
        preferred_framework="html_canvas",
        typical_features=["game_loop", "scoring", "timer"],
    ),
    
    "api_service": AppTrait(
        id="api_service",
        name="REST API",
        description="A REST API service",
        models=[],  # Inferred from description
        ui_pattern="none",
        special_features=["openapi_docs", "rate_limiting"],
        trigger_keywords=["api", "rest", "endpoint", "service", "server"],
        default_answers={"needs_auth": True, "export": True},
        preferred_framework="fastapi",
        typical_features=["database", "crud", "auth"],
    ),
    
    "ml_model": AppTrait(
        id="ml_model",
        name="ML Pipeline",
        description="A machine learning pipeline",
        models=[
            DomainModelSchema(
                name="Dataset",
                fields=[
                    DomainField("path", "string"),
                    DomainField("target_column", "string"),
                    DomainField("features", "text"),  # JSON array
                ],
            ),
        ],
        ui_pattern="dashboard",
        special_features=["model_evaluation", "visualization"],
        trigger_keywords=["ml", "machine learning", "predict", "train", "model", "classification", "regression"],
        default_answers={"needs_auth": False, "export": True},
        preferred_framework="sklearn",
        typical_features=["database"],
    ),
    
    "calculator": AppTrait(
        id="calculator",
        name="Calculator",
        description="A calculator application",
        models=[],
        ui_pattern="form",
        special_features=["expression_parser"],
        trigger_keywords=["calculator", "math", "calculate", "compute"],
        default_answers={"needs_auth": False, "has_data": False},
        preferred_framework="html_canvas",
        typical_features=["input_handler"],
    ),
    
    "converter": AppTrait(
        id="converter",
        name="Unit Converter",
        description="A unit conversion tool",
        models=[],
        ui_pattern="form",
        special_features=["unit_database"],
        trigger_keywords=["convert", "converter", "unit", "temperature", "length", "weight"],
        default_answers={"needs_auth": False, "has_data": False},
        preferred_framework="html_canvas",
        typical_features=["input_handler"],
    ),
}


# =====================================================================
# Trait Store
# =====================================================================

class TraitStore:
    """Manages app traits with persistence and learning."""
    
    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or Path(__file__).parent / "data" / "traits.json"
        self.traits: Dict[str, AppTrait] = dict(SEED_TRAITS)
        self._load()
    
    def _load(self):
        """Load persisted traits."""
        if self.store_path.exists():
            try:
                with open(self.store_path) as f:
                    data = json.load(f)
                    for trait_data in data.get("traits", []):
                        trait = AppTrait.from_dict(trait_data)
                        self.traits[trait.id] = trait
            except Exception as e:
                print(f"Warning: Could not load traits: {e}")
    
    def _save(self):
        """Persist traits to disk."""
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "updated": datetime.now().isoformat(),
            "traits": [t.to_dict() for t in self.traits.values() if t.id not in SEED_TRAITS],
        }
        with open(self.store_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get(self, trait_id: str) -> Optional[AppTrait]:
        """Get a trait by ID."""
        return self.traits.get(trait_id)
    
    def list_all(self) -> List[AppTrait]:
        """List all traits."""
        return list(self.traits.values())
    
    def match(self, description: str) -> Optional[Tuple[AppTrait, float]]:
        """Find the best matching trait for a description."""
        best_trait = None
        best_score = 0.0
        
        for trait in self.traits.values():
            score = trait.matches(description)
            if score > best_score:
                best_score = score
                best_trait = trait
        
        if best_trait and best_score > 0.1:  # Minimum threshold
            return (best_trait, best_score)
        return None
    
    def record_usage(self, trait_id: str):
        """Record that a trait was used (for ranking)."""
        if trait := self.get(trait_id):
            trait.usage_count += 1
            trait.last_used = datetime.now().isoformat()
            self._save()
    
    def learn_from_build(self, 
                         description: str,
                         answers: Dict[str, Any],
                         framework: str,
                         features: List[str],
                         models: List[Any] = None) -> AppTrait:
        """Learn a new trait from a successful build."""
        # Extract keywords from description
        keywords = self._extract_keywords(description)
        
        # Generate ID
        trait_id = self._generate_id(description)
        
        # Convert models if provided
        model_schemas = []
        if models:
            for m in models:
                if hasattr(m, 'name') and hasattr(m, 'fields'):
                    fields = [
                        DomainField(f[0], self._infer_type(f[1]), len(f) < 3 or f[2])
                        for f in m.fields
                    ]
                    model_schemas.append(DomainModelSchema(name=m.name, fields=fields))
        
        # Create trait
        trait = AppTrait(
            id=trait_id,
            name=description[:50],
            description=description,
            models=model_schemas,
            trigger_keywords=keywords,
            default_answers=answers,
            preferred_framework=framework,
            typical_features=features,
            usage_count=1,
            last_used=datetime.now().isoformat(),
        )
        
        # Store
        self.traits[trait_id] = trait
        self._save()
        
        return trait
    
    def _extract_keywords(self, description: str) -> List[str]:
        """Extract relevant keywords from a description."""
        # Simple extraction - could be enhanced with NLP
        stop_words = {"a", "an", "the", "is", "are", "for", "to", "and", "or", "with", "that", "this", "i", "my", "me", "can"}
        words = re.findall(r'\b[a-z]+\b', description.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return list(set(keywords))[:10]  # Max 10 keywords
    
    def _generate_id(self, description: str) -> str:
        """Generate a unique ID from description."""
        # Take first few significant words
        words = re.findall(r'\b[a-z]+\b', description.lower())
        significant = [w for w in words if len(w) > 3][:3]
        base_id = "_".join(significant) or "app"
        
        # Ensure uniqueness
        test_id = base_id
        counter = 1
        while test_id in self.traits:
            test_id = f"{base_id}_{counter}"
            counter += 1
        
        return test_id
    
    def _infer_type(self, sql_type: str) -> str:
        """Infer field type from SQL type."""
        sql_lower = sql_type.lower()
        if "int" in sql_lower:
            return "int"
        elif "float" in sql_lower or "real" in sql_lower:
            return "float"
        elif "bool" in sql_lower:
            return "bool"
        elif "date" in sql_lower:
            return "date"
        elif "text" in sql_lower:
            return "text"
        return "string"


# Singleton
trait_store = TraitStore()


# =====================================================================
# Usage Example
# =====================================================================

if __name__ == "__main__":
    print("Trait Store Contents:")
    print("=" * 60)
    for trait in trait_store.list_all():
        kw = ", ".join(trait.trigger_keywords[:5])
        print(f"  {trait.id:15} ({trait.name})")
        print(f"    Keywords: {kw}")
        print(f"    Features: {trait.typical_features}")
        print()
    
    print("\nTrait Matching:")
    print("-" * 40)
    test_descriptions = [
        "a recipe collection app",
        "a snake game",
        "REST API for users",
        "machine learning prediction model",
        "a todo checklist app",
    ]
    
    for desc in test_descriptions:
        match = trait_store.match(desc)
        if match:
            trait, score = match
            print(f"  '{desc}' → {trait.id} (score: {score:.2f})")
        else:
            print(f"  '{desc}' → No match")
