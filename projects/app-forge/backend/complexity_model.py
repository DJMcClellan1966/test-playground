"""Complexity Model - Universal App Architecture Patterns.

The key insight: ALL apps exist on a multi-dimensional complexity space.
Each dimension has discrete levels that unlock capabilities.

DIMENSIONS:
  1. ENTITY    : Single → Multiple → Graph → Temporal
  2. USER      : Anonymous → Single → Multi → RBAC → Multi-tenant
  3. DATA      : Ephemeral → Persist → Query → Aggregate → Stream
  4. STATE     : Stateless → Stateful → State Machine → Event Sourced
  5. INTEGRATION: Standalone → Consumes → Provides → Event-driven

Simple apps cluster at (1,1,1,1,1). Complex apps expand outward.
The model detects complexity signals and recommends appropriate patterns.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum, auto
import re


# =============================================================================
# COMPLEXITY DIMENSIONS
# =============================================================================

class EntityComplexity(Enum):
    """How many entities and how they relate."""
    SINGLE = 1       # Todo item, Calculator input
    MULTIPLE = 2     # Recipe + Ingredients  
    GRAPH = 3        # User → Posts → Comments → Reactions
    TEMPORAL = 4     # Version history, audit logs


class UserComplexity(Enum):
    """Who uses the app and how."""
    ANONYMOUS = 1    # Calculator, Timer
    SINGLE = 2       # Personal todo, notes app
    MULTI = 3        # Shared todo, collab tools
    RBAC = 4         # Admin/editor/viewer roles
    MULTI_TENANT = 5 # SaaS, isolated customer data


class DataComplexity(Enum):
    """How data is stored and queried."""
    EPHEMERAL = 1    # In-memory only (calculator)
    PERSIST = 2      # Save/load (JSON file, localStorage)
    QUERY = 3        # Filter, sort, search (SQL)
    AGGREGATE = 4    # Stats, reports, dashboards
    STREAM = 5       # Real-time feeds, event streams


class StateComplexity(Enum):
    """How state changes over time."""
    STATELESS = 1    # Pure functions (converter)
    STATEFUL = 2     # Current state (game score)
    STATE_MACHINE = 3 # Defined transitions (Order: pending→paid→shipped)
    EVENT_SOURCED = 4 # Complete history, rebuild state


class IntegrationComplexity(Enum):
    """How the app connects to other systems."""
    STANDALONE = 1   # No external dependencies
    CONSUMES = 2     # Uses external APIs
    PROVIDES = 3     # Exposes its own API
    EVENT_DRIVEN = 4 # Webhooks, pub/sub, message queues


@dataclass
class ComplexityProfile:
    """Multi-dimensional complexity position of an app."""
    entity: EntityComplexity = EntityComplexity.SINGLE
    user: UserComplexity = UserComplexity.ANONYMOUS
    data: DataComplexity = DataComplexity.EPHEMERAL
    state: StateComplexity = StateComplexity.STATELESS
    integration: IntegrationComplexity = IntegrationComplexity.STANDALONE
    
    def total_complexity(self) -> int:
        """Sum of all dimension values (5-24 range)."""
        return sum([
            self.entity.value,
            self.user.value,
            self.data.value,
            self.state.value,
            self.integration.value
        ])
    
    def complexity_tier(self) -> str:
        """Human-readable tier name."""
        total = self.total_complexity()
        if total <= 6:
            return "trivial"      # Calculator, timer, dice
        elif total <= 9:
            return "simple"       # Personal todo, notes, recipe
        elif total <= 12:
            return "moderate"     # Recipe app with auth
        elif total <= 18:
            return "complex"      # E-commerce, project manager
        else:
            return "enterprise"   # SaaS, multi-tenant platforms
    
    def as_tuple(self) -> Tuple[int, int, int, int, int]:
        """For easy comparison."""
        return (
            self.entity.value,
            self.user.value,
            self.data.value,
            self.state.value,
            self.integration.value
        )


# =============================================================================
# COMPLEXITY DETECTION - Parse description for signals
# =============================================================================

COMPLEXITY_SIGNALS = {
    # Entity complexity signals
    "entity": {
        EntityComplexity.TEMPORAL: [
            r"history", r"version", r"audit", r"changes\s+over\s+time",
            r"track\s+changes", r"undo", r"revisions"
        ],
        EntityComplexity.GRAPH: [
            r"network", r"followers", r"friends", r"connections",
            r"hierarchy", r"nested", r"tree\s+structure", r"comments\s+on",
            r"replies", r"thread", r"teams?\s+and\s+", r"roles?\s+and\s+",
            r"e-?commerce", r"blog\s+with\s+comments"
        ],
        EntityComplexity.MULTIPLE: [
            r"\bwith\s+\w+\s+and\s+\w+", r"related\s+to", r"has\s+many",
            r"belongs\s+to", r"ingredients", r"categories", r"tags",
            r"\w+,\s*\w+,\s*(?:and\s+)?\w+",  # "products, cart, orders"
            r"products?", r"orders?", r"cart", r"items?",
            r"tasks?\s+and\s+", r"users?\s+and\s+"
        ],
    },
    
    # User complexity signals
    "user": {
        UserComplexity.MULTI_TENANT: [
            r"saas", r"multi-tenant", r"customers\s+each\s+have",
            r"isolated\s+data", r"per-organization", r"white-?label"
        ],
        UserComplexity.RBAC: [
            r"admin", r"roles?", r"permissions?", r"editor", r"viewer",
            r"moderator", r"access\s+control", r"can\s+only\s+see"
        ],
        UserComplexity.MULTI: [
            r"team", r"collab", r"shared", r"together", r"multiple\s+users",
            r"co-?edit", r"invite", r"members", r"login", r"register",
            r"users?", r"accounts?", r"sign\s*up"
        ],
        UserComplexity.SINGLE: [
            r"personal", r"my\s+own", r"just\s+me", r"private",
            r"i\s+want", r"where\s+i\s+can", r"for\s+myself"
        ],
    },
    
    # Data complexity signals
    "data": {
        DataComplexity.STREAM: [
            r"real-?time", r"live\s+updates?", r"streaming", r"websocket",
            r"notifications?", r"push", r"instant"
        ],
        DataComplexity.AGGREGATE: [
            r"dashboard", r"analytics", r"reports?", r"statistics",
            r"charts?", r"graphs?", r"metrics", r"trends?", r"sum\s+of"
        ],
        DataComplexity.QUERY: [
            r"search", r"filter", r"sort", r"find", r"query",
            r"by\s+date", r"by\s+category", r"lookup"
        ],
        DataComplexity.PERSIST: [
            r"save", r"store", r"keep", r"remember", r"database",
            r"collection", r"list\s+of", r"\bapp\b", r"manager",
            r"tracker", r"log", r"organizer", r"catalog",
            r"todo", r"notes?", r"recipe", r"inventory"
        ],
    },
    
    # State complexity signals
    "state": {
        StateComplexity.EVENT_SOURCED: [
            r"event\s+log", r"audit\s+trail", r"replay", r"immutable",
            r"full\s+history", r"never\s+delete"
        ],
        StateComplexity.STATE_MACHINE: [
            r"workflow", r"status", r"pending", r"approved", r"stages?",
            r"transitions?", r"draft", r"published", r"archived",
            r"order\s+status", r"state\s+machine",
            r"\borders?\b", r"shipping", r"checkout", r"kanban",
            r"deadlines?", r"milestones?", r"project\s+manage"
        ],
        StateComplexity.STATEFUL: [
            r"game", r"score", r"level", r"session", r"progress",
            r"current", r"state"
        ],
    },
    
    # Integration complexity signals
    "integration": {
        IntegrationComplexity.EVENT_DRIVEN: [
            r"webhook", r"events?", r"queue", r"pubsub", r"message",
            r"trigger\s+when", r"notify\s+external"
        ],
        IntegrationComplexity.PROVIDES: [
            r"api\s+for", r"expose", r"endpoints?", r"rest\s+api",
            r"graphql", r"webhook\s+endpoint"
        ],
        IntegrationComplexity.CONSUMES: [
            r"fetch\s+from", r"external\s+api", r"weather\s+api",
            r"third-?party", r"integrate\s+with", r"import\s+from",
            r"payment", r"stripe", r"paypal", r"checkout",
            r"oauth", r"google\s+login", r"social\s+login"
        ],
    },
}


def detect_complexity(description: str) -> ComplexityProfile:
    """Analyze description to determine complexity profile."""
    desc_lower = description.lower()
    
    profile = ComplexityProfile()
    
    # Check each dimension
    for dimension, level_patterns in COMPLEXITY_SIGNALS.items():
        # Check levels in order (highest first)
        for level, patterns in level_patterns.items():
            if any(re.search(p, desc_lower) for p in patterns):
                if dimension == "entity":
                    profile.entity = level
                elif dimension == "user":
                    profile.user = level
                elif dimension == "data":
                    profile.data = level
                elif dimension == "state":
                    profile.state = level
                elif dimension == "integration":
                    profile.integration = level
                break  # Found highest match for this dimension
    
    # Apply minimum complexity for known app types
    profile = _apply_app_type_minimums(desc_lower, profile)
    
    return profile


def _apply_app_type_minimums(desc: str, profile: ComplexityProfile) -> ComplexityProfile:
    """Boost complexity for known app types that have inherent requirements."""
    
    # E-commerce/store apps are inherently complex
    if re.search(r"e-?commerce|store|shop|marketplace", desc):
        profile.entity = max(profile.entity, EntityComplexity.GRAPH, key=lambda x: x.value)
        profile.state = max(profile.state, StateComplexity.STATE_MACHINE, key=lambda x: x.value)
        profile.data = max(profile.data, DataComplexity.QUERY, key=lambda x: x.value)
    
    # Project management tools with teams/roles are complex
    if re.search(r"project\s+manage|task\s+board", desc):
        profile.entity = max(profile.entity, EntityComplexity.MULTIPLE, key=lambda x: x.value)
        profile.state = max(profile.state, StateComplexity.STATE_MACHINE, key=lambda x: x.value)
        profile.data = max(profile.data, DataComplexity.QUERY, key=lambda x: x.value)
        if re.search(r"team|role|member", desc):
            profile.user = max(profile.user, UserComplexity.RBAC, key=lambda x: x.value)
            profile.entity = max(profile.entity, EntityComplexity.GRAPH, key=lambda x: x.value)
    
    # Kanban boards need workflow state
    if re.search(r"kanban", desc):
        profile.entity = max(profile.entity, EntityComplexity.MULTIPLE, key=lambda x: x.value)
        profile.state = max(profile.state, StateComplexity.STATE_MACHINE, key=lambda x: x.value)
    
    # Blog/CMS with comments implies graph relationships
    if re.search(r"blog.*comments?|cms|content\s+manage", desc):
        profile.entity = max(profile.entity, EntityComplexity.GRAPH, key=lambda x: x.value)
        profile.data = max(profile.data, DataComplexity.QUERY, key=lambda x: x.value)
    
    # Login + sharing = multi-user with relationships
    if re.search(r"login|auth", desc) and re.search(r"shar(e|ing)", desc):
        profile.user = max(profile.user, UserComplexity.MULTI, key=lambda x: x.value)
        profile.entity = max(profile.entity, EntityComplexity.MULTIPLE, key=lambda x: x.value)
        profile.data = max(profile.data, DataComplexity.QUERY, key=lambda x: x.value)
    
    # Social/sharing features imply multi-user
    if re.search(r"shar(e|ing)|social|collab", desc):
        profile.user = max(profile.user, UserComplexity.MULTI, key=lambda x: x.value)
    
    # Team implies multi-user at minimum
    if re.search(r"team", desc):
        profile.user = max(profile.user, UserComplexity.MULTI, key=lambda x: x.value)
    
    # Login/auth implies single-user at minimum
    if re.search(r"login|auth|register|account", desc):
        profile.user = max(profile.user, UserComplexity.SINGLE, key=lambda x: x.value)
        profile.data = max(profile.data, DataComplexity.PERSIST, key=lambda x: x.value)
    
    # SaaS/multi-tenant is enterprise level
    if re.search(r"saas|multi-?tenant|organization\s+isolation", desc):
        profile.user = max(profile.user, UserComplexity.MULTI_TENANT, key=lambda x: x.value)
        profile.entity = max(profile.entity, EntityComplexity.GRAPH, key=lambda x: x.value)
        profile.data = max(profile.data, DataComplexity.AGGREGATE, key=lambda x: x.value)
        profile.state = max(profile.state, StateComplexity.STATE_MACHINE, key=lambda x: x.value)
        profile.integration = max(profile.integration, IntegrationComplexity.EVENT_DRIVEN, key=lambda x: x.value)
    
    # Webhooks/API explicitly means event-driven integration
    if re.search(r"webhook|api\b", desc):
        profile.integration = max(profile.integration, IntegrationComplexity.PROVIDES, key=lambda x: x.value)
    
    # Admin panel implies RBAC
    if re.search(r"admin\s+panel|admin\s+dashboard|role", desc):
        profile.user = max(profile.user, UserComplexity.RBAC, key=lambda x: x.value)
    
    # CRM is inherently complex
    if re.search(r"\bcrm\b", desc):
        profile.entity = max(profile.entity, EntityComplexity.GRAPH, key=lambda x: x.value)
        profile.data = max(profile.data, DataComplexity.AGGREGATE, key=lambda x: x.value)
    
    # Any "with X and Y" pattern implies multiple entities
    if re.search(r"with\s+\w+\s+and\s+\w+", desc):
        profile.entity = max(profile.entity, EntityComplexity.MULTIPLE, key=lambda x: x.value)
        profile.data = max(profile.data, DataComplexity.PERSIST, key=lambda x: x.value)
    
    return profile


# =============================================================================
# ARCHITECTURE PATTERNS - Map complexity to solutions
# =============================================================================

@dataclass
class ArchitecturePattern:
    """A recommended architecture for a complexity profile."""
    name: str
    description: str
    file_structure: List[str]
    technologies: List[str]
    patterns: List[str]       # Design patterns to use
    components: List[str]     # Required components
    warnings: List[str]       # Complexity warnings
    growth_path: List[str]    # How to evolve this architecture


# Define architecture patterns for different complexity tiers
ARCHITECTURE_PATTERNS: Dict[str, ArchitecturePattern] = {
    "trivial": ArchitecturePattern(
        name="Single-File App",
        description="Everything in one file - fastest to build and understand",
        file_structure=["app.py"],  # or index.html
        technologies=["Flask", "vanilla JS"],
        patterns=["Procedural", "In-memory state"],
        components=["routes", "view"],
        warnings=[],
        growth_path=[
            "Add data file → Move to 'simple'",
            "Add second entity → Split into modules",
        ]
    ),
    
    "simple": ArchitecturePattern(
        name="Standard CRUD",
        description="Separate concerns: app, models, templates",
        file_structure=["app.py", "models.py", "templates/"],
        technologies=["Flask", "SQLite", "Jinja2"],
        patterns=["MVC", "Repository"],
        components=["routes", "models", "templates", "database"],
        warnings=["Add auth before going multi-user"],
        growth_path=[
            "Add authentication → Move to 'moderate'",
            "Add search/filter → Add query layer",
            "Add relationships → Add ORM"
        ]
    ),
    
    "moderate": ArchitecturePattern(
        name="Domain-Driven",
        description="Clear domain boundaries, proper authentication",
        file_structure=[
            "app.py",
            "models/",
            "routes/",
            "services/",
            "templates/",
            "static/"
        ],
        technologies=["Flask", "SQLAlchemy", "Flask-Login", "PostgreSQL"],
        patterns=["MVC", "Repository", "Service Layer"],
        components=["routes", "models", "services", "auth", "database", "migrations"],
        warnings=[
            "Consider caching for complex queries",
            "Add input validation",
            "Plan for backup/restore"
        ],
        growth_path=[
            "Add RBAC → Move to 'complex'",
            "Add async jobs → Add Celery/RQ",
            "Add API → Add versioned endpoints"
        ]
    ),
    
    "complex": ArchitecturePattern(
        name="Layered Architecture",
        description="Full separation: API, domain, infrastructure",
        file_structure=[
            "api/",
            "domain/",
            "infrastructure/",
            "services/",
            "tests/",
            "config/",
            "migrations/"
        ],
        technologies=["FastAPI", "SQLAlchemy", "PostgreSQL", "Redis", "Celery"],
        patterns=["Clean Architecture", "CQRS (light)", "Repository", "Unit of Work"],
        components=[
            "api_routes", "domain_models", "repositories",
            "services", "auth", "rbac", "caching", "background_jobs"
        ],
        warnings=[
            "Consider read/write separation",
            "Add comprehensive logging",
            "Implement rate limiting",
            "Plan for horizontal scaling"
        ],
        growth_path=[
            "Add multi-tenancy → Move to 'enterprise'",
            "Add event sourcing → Track all changes",
            "Add microservices → Split domains"
        ]
    ),
    
    "enterprise": ArchitecturePattern(
        name="Distributed System",
        description="Multi-service, event-driven, multi-tenant capable",
        file_structure=[
            "services/",
            "  auth/",
            "  core/",
            "  notifications/",
            "shared/",
            "gateway/",
            "infra/",
            "tests/"
        ],
        technologies=[
            "FastAPI", "PostgreSQL", "Redis", "RabbitMQ/Kafka",
            "Docker", "Kubernetes", "OpenTelemetry"
        ],
        patterns=[
            "Microservices", "Event Sourcing", "CQRS",
            "Saga", "Circuit Breaker", "API Gateway"
        ],
        components=[
            "api_gateway", "auth_service", "domain_services",
            "event_bus", "tenant_isolation", "audit_log",
            "monitoring", "distributed_tracing"
        ],
        warnings=[
            "High operational complexity",
            "Need DevOps expertise",
            "Consider if really needed"
        ],
        growth_path=[
            "This is the ceiling for most apps",
            "Consider managed services to reduce ops"
        ]
    ),
}


def get_architecture(profile: ComplexityProfile) -> ArchitecturePattern:
    """Get recommended architecture for complexity profile."""
    tier = profile.complexity_tier()
    return ARCHITECTURE_PATTERNS.get(tier, ARCHITECTURE_PATTERNS["simple"])


# =============================================================================
# COMPONENT UNLOCKING - What capabilities unlock at each level
# =============================================================================

COMPONENT_UNLOCKS: Dict[str, Dict[int, List[str]]] = {
    # Entity complexity unlocks
    "entity": {
        1: ["single_model"],
        2: ["relationships", "foreign_keys", "joins"],
        3: ["recursive_queries", "graph_traversal", "adjacency_list"],
        4: ["temporal_tables", "history_tracking", "versioning"]
    },
    
    # User complexity unlocks
    "user": {
        1: [],  # No user management needed
        2: ["user_model", "sessions"],
        3: ["auth", "login", "register", "password_hash"],
        4: ["roles", "permissions", "rbac_tables"],
        5: ["tenant_id", "row_level_security", "tenant_middleware"]
    },
    
    # Data complexity unlocks
    "data": {
        1: [],  # In-memory
        2: ["json_storage", "localStorage"],
        3: ["sql_database", "indexes", "orm"],
        4: ["aggregations", "views", "materialized_views"],
        5: ["websockets", "sse", "pubsub", "event_store"]
    },
    
    # State complexity unlocks
    "state": {
        1: [],  # Stateless
        2: ["session_state", "local_state"],
        3: ["status_field", "state_transitions", "workflow_engine"],
        4: ["event_store", "projections", "snapshots"]
    },
    
    # Integration complexity unlocks
    "integration": {
        1: [],  # Standalone
        2: ["http_client", "api_wrappers"],
        3: ["api_routes", "openapi", "versioning"],
        4: ["webhook_endpoints", "message_queue", "event_handlers"]
    }
}


def get_unlocked_components(profile: ComplexityProfile) -> Set[str]:
    """Get all components unlocked by this complexity profile."""
    components = set()
    
    for level in range(1, profile.entity.value + 1):
        components.update(COMPONENT_UNLOCKS["entity"].get(level, []))
    
    for level in range(1, profile.user.value + 1):
        components.update(COMPONENT_UNLOCKS["user"].get(level, []))
    
    for level in range(1, profile.data.value + 1):
        components.update(COMPONENT_UNLOCKS["data"].get(level, []))
    
    for level in range(1, profile.state.value + 1):
        components.update(COMPONENT_UNLOCKS["state"].get(level, []))
    
    for level in range(1, profile.integration.value + 1):
        components.update(COMPONENT_UNLOCKS["integration"].get(level, []))
    
    return components


# =============================================================================
# CANONICAL APP PROFILES - Reference points in complexity space
# =============================================================================

CANONICAL_APPS = {
    "calculator": ComplexityProfile(
        entity=EntityComplexity.SINGLE,
        user=UserComplexity.ANONYMOUS,
        data=DataComplexity.EPHEMERAL,
        state=StateComplexity.STATELESS,
        integration=IntegrationComplexity.STANDALONE
    ),
    
    "timer": ComplexityProfile(
        entity=EntityComplexity.SINGLE,
        user=UserComplexity.ANONYMOUS,
        data=DataComplexity.EPHEMERAL,
        state=StateComplexity.STATEFUL,
        integration=IntegrationComplexity.STANDALONE
    ),
    
    "personal_todo": ComplexityProfile(
        entity=EntityComplexity.SINGLE,
        user=UserComplexity.SINGLE,
        data=DataComplexity.PERSIST,
        state=StateComplexity.STATEFUL,
        integration=IntegrationComplexity.STANDALONE
    ),
    
    "recipe_app": ComplexityProfile(
        entity=EntityComplexity.MULTIPLE,
        user=UserComplexity.SINGLE,
        data=DataComplexity.QUERY,
        state=StateComplexity.STATEFUL,
        integration=IntegrationComplexity.STANDALONE
    ),
    
    "recipe_app_with_auth": ComplexityProfile(
        entity=EntityComplexity.MULTIPLE,
        user=UserComplexity.MULTI,
        data=DataComplexity.QUERY,
        state=StateComplexity.STATEFUL,
        integration=IntegrationComplexity.STANDALONE
    ),
    
    "ecommerce": ComplexityProfile(
        entity=EntityComplexity.GRAPH,
        user=UserComplexity.MULTI,
        data=DataComplexity.AGGREGATE,
        state=StateComplexity.STATE_MACHINE,
        integration=IntegrationComplexity.CONSUMES  # Payment APIs
    ),
    
    "project_manager": ComplexityProfile(
        entity=EntityComplexity.GRAPH,
        user=UserComplexity.RBAC,
        data=DataComplexity.QUERY,
        state=StateComplexity.STATE_MACHINE,
        integration=IntegrationComplexity.PROVIDES
    ),
    
    "social_network": ComplexityProfile(
        entity=EntityComplexity.GRAPH,
        user=UserComplexity.MULTI,
        data=DataComplexity.STREAM,
        state=StateComplexity.STATEFUL,
        integration=IntegrationComplexity.PROVIDES
    ),
    
    "saas_platform": ComplexityProfile(
        entity=EntityComplexity.GRAPH,
        user=UserComplexity.MULTI_TENANT,
        data=DataComplexity.AGGREGATE,
        state=StateComplexity.STATE_MACHINE,
        integration=IntegrationComplexity.EVENT_DRIVEN
    ),
}


def find_nearest_canonical(profile: ComplexityProfile) -> Tuple[str, int]:
    """Find the nearest canonical app and distance."""
    target = profile.as_tuple()
    
    best_name = "custom"
    best_distance = float("inf")
    
    for name, canonical in CANONICAL_APPS.items():
        distance = sum(abs(a - b) for a, b in zip(target, canonical.as_tuple()))
        if distance < best_distance:
            best_distance = distance
            best_name = name
    
    return best_name, best_distance


# =============================================================================
# GROWTH PATH - How apps evolve
# =============================================================================

def suggest_growth_path(profile: ComplexityProfile) -> List[str]:
    """Suggest natural evolution paths for this app."""
    suggestions = []
    
    # Entity growth
    if profile.entity == EntityComplexity.SINGLE:
        suggestions.append("Add a second entity to unlock relationships")
    elif profile.entity == EntityComplexity.MULTIPLE:
        suggestions.append("Consider nested data (comments, threads) for richer interaction")
    
    # User growth
    if profile.user == UserComplexity.ANONYMOUS:
        suggestions.append("Add user accounts for personalization")
    elif profile.user == UserComplexity.SINGLE:
        suggestions.append("Enable sharing/collaboration for team features")
    elif profile.user == UserComplexity.MULTI:
        suggestions.append("Add roles (admin/editor) for access control")
    
    # Data growth
    if profile.data == DataComplexity.PERSIST:
        suggestions.append("Add search/filter for faster data access")
    elif profile.data == DataComplexity.QUERY:
        suggestions.append("Add dashboard/reports for insights")
    
    # State growth
    if profile.state == StateComplexity.STATEFUL:
        suggestions.append("Define status workflows for clearer processes")
    
    # Integration growth
    if profile.integration == IntegrationComplexity.STANDALONE:
        suggestions.append("Consider external APIs to enrich data")
    elif profile.integration == IntegrationComplexity.CONSUMES:
        suggestions.append("Expose an API for external integrations")
    
    return suggestions


# =============================================================================
# MAIN API
# =============================================================================

def analyze(description: str) -> Dict:
    """
    Full complexity analysis of an app description.
    
    Returns:
        dict with profile, architecture, components, and growth suggestions
    """
    profile = detect_complexity(description)
    architecture = get_architecture(profile)
    components = get_unlocked_components(profile)
    nearest, distance = find_nearest_canonical(profile)
    growth = suggest_growth_path(profile)
    
    return {
        "profile": {
            "entity": profile.entity.name,
            "user": profile.user.name,
            "data": profile.data.name,
            "state": profile.state.name,
            "integration": profile.integration.name,
            "total": profile.total_complexity(),
            "tier": profile.complexity_tier()
        },
        "architecture": {
            "name": architecture.name,
            "description": architecture.description,
            "files": architecture.file_structure,
            "technologies": architecture.technologies,
            "patterns": architecture.patterns,
            "warnings": architecture.warnings
        },
        "components": sorted(list(components)),
        "nearest_canonical": nearest,
        "distance_from_canonical": distance,
        "growth_suggestions": growth
    }


# =============================================================================
# CLI DEMO
# =============================================================================

if __name__ == "__main__":
    test_cases = [
        "a calculator",
        "a timer app",
        "a personal todo list",
        "a recipe collection app with ingredients and categories",
        "a recipe app with user login where people can save and share recipes",
        "an e-commerce store with products, cart, orders, and payment",
        "a project management tool with tasks, teams, and admin roles",
        "a social network with posts, comments, followers, and live notifications",
        "a multi-tenant SaaS platform with organization isolation and webhooks",
    ]
    
    print("=" * 70)
    print("COMPLEXITY MODEL - Universal App Architecture Analysis")
    print("=" * 70)
    
    for desc in test_cases:
        result = analyze(desc)
        profile = result["profile"]
        
        print(f"\n📱 \"{desc}\"")
        print(f"   Tier: {profile['tier'].upper()} (score: {profile['total']})")
        print(f"   Profile: E={profile['entity']}, U={profile['user']}, D={profile['data']}, S={profile['state']}, I={profile['integration']}")
        print(f"   Architecture: {result['architecture']['name']}")
        print(f"   Nearest canonical: {result['nearest_canonical']} (distance: {result['distance_from_canonical']})")
        print(f"   Components: {', '.join(result['components'][:5])}{'...' if len(result['components']) > 5 else ''}")
        print(f"   Growth: {result['growth_suggestions'][0] if result['growth_suggestions'] else 'At maximum'}")
