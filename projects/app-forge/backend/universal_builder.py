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

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Type
from enum import Enum

# Import existing App Forge components (backward compatible)
try:
    from domain_parser import DomainModel, parse_description
    from template_registry import extract_features, Feature
    from intent_graph import IntentGraph
except ImportError:
    # Standalone mode
    DomainModel = None
    parse_description = lambda x: []
    extract_features = lambda x: {}
    IntentGraph = None


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
        
        # Register built-ins
        self._register_defaults()
    
    def build(self, description: str, answers: Optional[Dict[str, Any]] = None) -> Project:
        """The universal build pipeline."""
        answers = answers or {}
        
        # 1. INTENT EXTRACTION
        category = self.categorize(description)
        features = extract_features(description)
        
        # 2. FRAMEWORK SELECTION
        framework_id = self.select_framework(category, answers, features)
        generator = self.framework_generators[framework_id]
        
        # 3. DOMAIN MODELING
        models = parse_description(description) if parse_description else []
        
        # 4. CONSTRAINT PROPAGATION
        inferred = self._infer_from_features(features)
        combined = {**inferred, **answers}
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
        
        return Project(
            name=self._extract_name(description),
            category=category,
            framework=framework_id,
            files=files,
            run_command=generator.get_run_command(self._extract_name(description)),
            install_command=generator.get_install_command(),
            description=description
        )
    
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
            AppCategory.GAME: ["game", "play", "score", "level", "puzzle", "quiz"],
            AppCategory.API_SERVICE: ["api", "endpoint", "rest", "graphql", "service", "backend"],
            AppCategory.ML_PIPELINE: ["ml", "machine learning", "model", "predict", "train", "dataset"],
            AppCategory.CLI_TOOL: ["cli", "command", "terminal", "script", "tool"],
            AppCategory.DESKTOP: ["desktop", "gui", "window", "native"],
            AppCategory.MOBILE: ["mobile", "ios", "android", "app store"],
            AppCategory.AUTOMATION: ["automate", "bot", "schedule", "workflow", "scrape"],
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
            AppCategory.GAME: "html_canvas",
            AppCategory.API_SERVICE: "fastapi",
            AppCategory.ML_PIPELINE: "sklearn_pipeline",
            AppCategory.CLI_TOOL: "click",
            AppCategory.DESKTOP: "tkinter",
            AppCategory.MOBILE: "flutter",
            AppCategory.AUTOMATION: "python_script",
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
        # Will be populated by category_registry.py, component_library.py, etc.
        pass


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

def build_app(description: str, answers: Optional[Dict[str, Any]] = None) -> Project:
    """Build an app from a description."""
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
