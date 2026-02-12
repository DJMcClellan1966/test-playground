"""Knowledge Base for Semantic Inference.

This module contains compact but comprehensive mappings that replicate
what LLMs "know" through training. Instead of neural networks, we use
curated dictionaries derived from common patterns in software.

Sources: No LLM needed - these are distilled from:
1. Common database schemas (entity→fields)
2. REST API patterns (action→feature)
3. Type system conventions (word→type)
"""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


# =============================================================================
# LAYER 3: DOMAIN KNOWLEDGE (What LLMs learn from training data)
# =============================================================================

@dataclass
class FieldDefinition:
    """Definition of a field with type and typical attributes."""
    name: str
    field_type: str  # str, int, float, bool, datetime, text
    required: bool = True
    description: str = ""


# Entity → Typical Fields Mapping
# This is what LLMs learn from seeing millions of database schemas
ENTITY_FIELDS: Dict[str, List[FieldDefinition]] = {
    # Business & Commerce
    "product": [
        FieldDefinition("name", "str", True, "Product name"),
        FieldDefinition("description", "text", False, "Detailed description"),
        FieldDefinition("price", "float", True, "Unit price"),
        FieldDefinition("sku", "str", False, "Stock keeping unit"),
        FieldDefinition("quantity", "int", True, "Available quantity"),
        FieldDefinition("category", "str", False, "Product category"),
    ],
    "supplier": [
        FieldDefinition("name", "str", True, "Supplier name"),
        FieldDefinition("contact", "str", False, "Contact person"),
        FieldDefinition("email", "str", False, "Email address"),
        FieldDefinition("phone", "str", False, "Phone number"),
        FieldDefinition("address", "text", False, "Physical address"),
    ],
    "order": [
        FieldDefinition("order_number", "str", True, "Unique order ID"),
        FieldDefinition("date", "datetime", True, "Order date"),
        FieldDefinition("status", "str", True, "Order status"),
        FieldDefinition("total", "float", True, "Total amount"),
        FieldDefinition("notes", "text", False, "Additional notes"),
    ],
    "inventory": [
        FieldDefinition("item_name", "str", True, "Item name"),
        FieldDefinition("quantity", "int", True, "Current quantity"),
        FieldDefinition("location", "str", False, "Storage location"),
        FieldDefinition("reorder_point", "int", False, "Reorder threshold"),
    ],
    "customer": [
        FieldDefinition("name", "str", True, "Customer name"),
        FieldDefinition("email", "str", True, "Email address"),
        FieldDefinition("phone", "str", False, "Phone number"),
        FieldDefinition("address", "text", False, "Mailing address"),
        FieldDefinition("notes", "text", False, "Customer notes"),
    ],
    "invoice": [
        FieldDefinition("invoice_number", "str", True, "Invoice ID"),
        FieldDefinition("date", "datetime", True, "Invoice date"),
        FieldDefinition("due_date", "datetime", False, "Payment due date"),
        FieldDefinition("amount", "float", True, "Total amount"),
        FieldDefinition("status", "str", True, "Payment status"),
    ],
    
    # Food & Recipes
    "recipe": [
        FieldDefinition("name", "str", True, "Recipe name"),
        FieldDefinition("description", "text", False, "Recipe description"),
        FieldDefinition("prep_time", "int", False, "Preparation time (minutes)"),
        FieldDefinition("cook_time", "int", False, "Cooking time (minutes)"),
        FieldDefinition("servings", "int", False, "Number of servings"),
        FieldDefinition("instructions", "text", True, "Cooking instructions"),
        FieldDefinition("rating", "int", False, "User rating"),
    ],
    "ingredient": [
        FieldDefinition("name", "str", True, "Ingredient name"),
        FieldDefinition("quantity", "float", False, "Amount needed"),
        FieldDefinition("unit", "str", False, "Measurement unit"),
        FieldDefinition("notes", "text", False, "Preparation notes"),
    ],
    "meal": [
        FieldDefinition("name", "str", True, "Meal name"),
        FieldDefinition("date", "datetime", True, "Meal date"),
        FieldDefinition("meal_type", "str", False, "Breakfast/Lunch/Dinner"),
        FieldDefinition("calories", "int", False, "Calorie count"),
    ],
    
    # Health & Fitness
    "workout": [
        FieldDefinition("name", "str", True, "Workout name"),
        FieldDefinition("date", "datetime", True, "Workout date"),
        FieldDefinition("duration", "int", False, "Duration (minutes)"),
        FieldDefinition("type", "str", False, "Workout type"),
        FieldDefinition("notes", "text", False, "Workout notes"),
    ],
    "exercise": [
        FieldDefinition("name", "str", True, "Exercise name"),
        FieldDefinition("sets", "int", False, "Number of sets"),
        FieldDefinition("reps", "int", False, "Reps per set"),
        FieldDefinition("weight", "float", False, "Weight used"),
        FieldDefinition("duration", "int", False, "Duration (seconds)"),
    ],
    "habit": [
        FieldDefinition("name", "str", True, "Habit name"),
        FieldDefinition("description", "text", False, "Habit description"),
        FieldDefinition("frequency", "str", False, "How often"),
        FieldDefinition("streak", "int", False, "Current streak"),
        FieldDefinition("completed", "bool", False, "Today's status"),
    ],
    
    # Education & Learning
    "course": [
        FieldDefinition("title", "str", True, "Course title"),
        FieldDefinition("description", "text", False, "Course description"),
        FieldDefinition("instructor", "str", False, "Instructor name"),
        FieldDefinition("duration", "int", False, "Duration (hours)"),
        FieldDefinition("status", "str", False, "Enrollment status"),
    ],
    "lesson": [
        FieldDefinition("title", "str", True, "Lesson title"),
        FieldDefinition("content", "text", True, "Lesson content"),
        FieldDefinition("order", "int", False, "Lesson order"),
        FieldDefinition("completed", "bool", False, "Completion status"),
    ],
    "quiz": [
        FieldDefinition("title", "str", True, "Quiz title"),
        FieldDefinition("description", "text", False, "Quiz description"),
        FieldDefinition("time_limit", "int", False, "Time limit (minutes)"),
        FieldDefinition("passing_score", "int", False, "Minimum score to pass"),
    ],
    "question": [
        FieldDefinition("text", "text", True, "Question text"),
        FieldDefinition("question_type", "str", False, "Multiple choice, etc."),
        FieldDefinition("points", "int", False, "Point value"),
        FieldDefinition("answer", "text", True, "Correct answer"),
    ],
    "flashcard": [
        FieldDefinition("front", "text", True, "Card front"),
        FieldDefinition("back", "text", True, "Card back"),
        FieldDefinition("category", "str", False, "Card category"),
        FieldDefinition("difficulty", "int", False, "Difficulty level"),
    ],
    
    # Project Management
    "project": [
        FieldDefinition("name", "str", True, "Project name"),
        FieldDefinition("description", "text", False, "Project description"),
        FieldDefinition("start_date", "datetime", False, "Start date"),
        FieldDefinition("end_date", "datetime", False, "End date"),
        FieldDefinition("status", "str", True, "Project status"),
    ],
    "task": [
        FieldDefinition("title", "str", True, "Task title"),
        FieldDefinition("description", "text", False, "Task description"),
        FieldDefinition("due_date", "datetime", False, "Due date"),
        FieldDefinition("priority", "str", False, "Task priority"),
        FieldDefinition("completed", "bool", True, "Completion status"),
    ],
    "todo": [
        FieldDefinition("title", "str", True, "Todo title"),
        FieldDefinition("description", "text", False, "Todo description"),
        FieldDefinition("completed", "bool", True, "Done?"),
        FieldDefinition("priority", "int", False, "Priority level"),
    ],
    
    # Media & Entertainment
    "movie": [
        FieldDefinition("title", "str", True, "Movie title"),
        FieldDefinition("director", "str", False, "Director name"),
        FieldDefinition("year", "int", False, "Release year"),
        FieldDefinition("genre", "str", False, "Movie genre"),
        FieldDefinition("rating", "int", False, "User rating"),
        FieldDefinition("watched", "bool", False, "Watched status"),
    ],
    "book": [
        FieldDefinition("title", "str", True, "Book title"),
        FieldDefinition("author", "str", True, "Author name"),
        FieldDefinition("isbn", "str", False, "ISBN number"),
        FieldDefinition("pages", "int", False, "Page count"),
        FieldDefinition("rating", "int", False, "User rating"),
        FieldDefinition("finished", "bool", False, "Reading status"),
    ],
    "song": [
        FieldDefinition("title", "str", True, "Song title"),
        FieldDefinition("artist", "str", True, "Artist name"),
        FieldDefinition("album", "str", False, "Album name"),
        FieldDefinition("duration", "int", False, "Duration (seconds)"),
        FieldDefinition("genre", "str", False, "Music genre"),
    ],
    "playlist": [
        FieldDefinition("name", "str", True, "Playlist name"),
        FieldDefinition("description", "text", False, "Playlist description"),
        FieldDefinition("public", "bool", False, "Public visibility"),
    ],
    
    # Scheduling & Events
    "event": [
        FieldDefinition("title", "str", True, "Event title"),
        FieldDefinition("description", "text", False, "Event description"),
        FieldDefinition("start_time", "datetime", True, "Start time"),
        FieldDefinition("end_time", "datetime", False, "End time"),
        FieldDefinition("location", "str", False, "Event location"),
    ],
    "appointment": [
        FieldDefinition("title", "str", True, "Appointment title"),
        FieldDefinition("date", "datetime", True, "Appointment date"),
        FieldDefinition("time", "str", True, "Appointment time"),
        FieldDefinition("duration", "int", False, "Duration (minutes)"),
        FieldDefinition("notes", "text", False, "Additional notes"),
    ],
    "meeting": [
        FieldDefinition("title", "str", True, "Meeting title"),
        FieldDefinition("date", "datetime", True, "Meeting date"),
        FieldDefinition("attendees", "text", False, "Attendee list"),
        FieldDefinition("agenda", "text", False, "Meeting agenda"),
        FieldDefinition("notes", "text", False, "Meeting notes"),
    ],
    
    # Finance
    "expense": [
        FieldDefinition("description", "str", True, "Expense description"),
        FieldDefinition("amount", "float", True, "Expense amount"),
        FieldDefinition("date", "datetime", True, "Expense date"),
        FieldDefinition("category", "str", False, "Expense category"),
        FieldDefinition("receipt", "str", False, "Receipt image URL"),
    ],
    "transaction": [
        FieldDefinition("description", "str", True, "Transaction description"),
        FieldDefinition("amount", "float", True, "Transaction amount"),
        FieldDefinition("date", "datetime", True, "Transaction date"),
        FieldDefinition("type", "str", True, "Debit/Credit"),
        FieldDefinition("category", "str", False, "Transaction category"),
    ],
    "budget": [
        FieldDefinition("name", "str", True, "Budget name"),
        FieldDefinition("amount", "float", True, "Budget amount"),
        FieldDefinition("period", "str", False, "Budget period"),
        FieldDefinition("category", "str", False, "Budget category"),
    ],
    
    # Documentation
    "note": [
        FieldDefinition("title", "str", True, "Note title"),
        FieldDefinition("content", "text", True, "Note content"),
        FieldDefinition("tags", "str", False, "Tags"),
        FieldDefinition("created", "datetime", False, "Creation date"),
    ],
    "document": [
        FieldDefinition("title", "str", True, "Document title"),
        FieldDefinition("content", "text", True, "Document content"),
        FieldDefinition("author", "str", False, "Author name"),
        FieldDefinition("version", "str", False, "Document version"),
    ],
    "wiki": [
        FieldDefinition("title", "str", True, "Page title"),
        FieldDefinition("content", "text", True, "Page content"),
        FieldDefinition("category", "str", False, "Page category"),
        FieldDefinition("slug", "str", False, "URL slug"),
    ],
    
    # Communication
    "message": [
        FieldDefinition("subject", "str", False, "Message subject"),
        FieldDefinition("body", "text", True, "Message body"),
        FieldDefinition("sender", "str", True, "Sender name"),
        FieldDefinition("timestamp", "datetime", True, "Sent time"),
        FieldDefinition("read", "bool", False, "Read status"),
    ],
    "comment": [
        FieldDefinition("text", "text", True, "Comment text"),
        FieldDefinition("author", "str", True, "Author name"),
        FieldDefinition("timestamp", "datetime", True, "Comment time"),
    ],
    
    # Location
    "location": [
        FieldDefinition("name", "str", True, "Location name"),
        FieldDefinition("address", "text", False, "Street address"),
        FieldDefinition("city", "str", False, "City"),
        FieldDefinition("latitude", "float", False, "Latitude coordinate"),
        FieldDefinition("longitude", "float", False, "Longitude coordinate"),
    ],
    "place": [
        FieldDefinition("name", "str", True, "Place name"),
        FieldDefinition("type", "str", False, "Place type"),
        FieldDefinition("address", "text", False, "Address"),
        FieldDefinition("rating", "int", False, "User rating"),
    ],
}


# Action Verbs → Feature Mapping
# What LLMs learn from REST API patterns and user stories
ACTION_FEATURES: Dict[str, Set[str]] = {
    # Data manipulation
    "save": {"database", "crud"},
    "store": {"database", "crud"},
    "track": {"database", "crud"},
    "manage": {"database", "crud"},
    "organize": {"database", "crud"},
    "collect": {"database", "crud"},
    "record": {"database", "crud"},
    "log": {"database", "crud"},
    "create": {"database", "crud"},
    "add": {"database", "crud"},
    "update": {"database", "crud"},
    "edit": {"database", "crud"},
    "delete": {"database", "crud"},
    "remove": {"database", "crud"},
    
    # Search & filter
    "search": {"search", "database"},
    "find": {"search", "database"},
    "filter": {"search", "database"},
    "query": {"search", "database"},
    "lookup": {"search", "database"},
    
    # Export & import
    "export": {"export", "database"},
    "download": {"export"},
    "import": {"database"},
    "upload": {"database"},
    
    # Authentication
    "login": {"auth", "database"},
    "register": {"auth", "database"},
    "authenticate": {"auth", "database"},
    "authorize": {"auth"},
    
    # Real-time features
    "chat": {"realtime", "database"},
    "message": {"realtime", "database"},
    "notify": {"realtime"},
    "stream": {"realtime"},
    "live": {"realtime"},
    
    # Games
    "play": {"game_loop"},
    "move": {"game_loop", "input_handler"},
    "click": {"input_handler"},
    "draw": {"game_loop"},
    "render": {"game_loop"},
    "score": {"scoring"},
    "countdown": {"timer"},
    "timed": {"timer"},
    
    # Miscellaneous
    "calculate": {"crud"},  # Usually just needs basic logic
    "convert": {"crud"},
    "generate": {"crud"},
    "validate": {"crud"},
    "rate": {"database", "crud"},
    "review": {"database", "crud"},
    "share": {"export", "auth"},
}


# Context words → Field type hints
# What LLMs learn from type systems
TYPE_HINTS: Dict[str, str] = {
    # String indicators
    "name": "str",
    "title": "str",
    "label": "str",
    "username": "str",
    "email": "str",
    "phone": "str",
    "url": "str",
    "slug": "str",
    "code": "str",
    "status": "str",
    "type": "str",
    "category": "str",
    "tag": "str",
    
    # Text indicators
    "description": "text",
    "content": "text",
    "body": "text",
    "message": "text",
    "comment": "text",
    "note": "text",
    "notes": "text",
    "instructions": "text",
    "details": "text",
    "bio": "text",
    "address": "text",
    
    # Integer indicators
    "count": "int",
    "quantity": "int",
    "amount": "int",
    "number": "int",
    "age": "int",
    "year": "int",
    "pages": "int",
    "level": "int",
    "score": "int",
    "points": "int",
    "rating": "int",
    "priority": "int",
    "order": "int",
    "position": "int",
    "rank": "int",
    "streak": "int",
    "sets": "int",
    "reps": "int",
    "duration": "int",
    "time": "int",
    "minutes": "int",
    "seconds": "int",
    "hours": "int",
    
    # Float indicators
    "price": "float",
    "cost": "float",
    "rate": "float",
    "percentage": "float",
    "ratio": "float",
    "weight": "float",
    "height": "float",
    "distance": "float",
    "latitude": "float",
    "longitude": "float",
    "temperature": "float",
    
    # Boolean indicators
    "completed": "bool",
    "finished": "bool",
    "done": "bool",
    "active": "bool",
    "enabled": "bool",
    "public": "bool",
    "private": "bool",
    "visible": "bool",
    "watched": "bool",
    "read": "bool",
    "sent": "bool",
    
    # Datetime indicators
    "date": "datetime",
    "time": "datetime",
    "timestamp": "datetime",
    "created": "datetime",
    "updated": "datetime",
    "modified": "datetime",
    "published": "datetime",
    "expires": "datetime",
    "due": "datetime",
    "start": "datetime",
    "end": "datetime",
}


# Relationship detection patterns
# What LLMs learn from foreign key conventions
RELATIONSHIP_PATTERNS: List[Tuple[str, str]] = [
    # One-to-many indicators
    ("have", "has_many"),
    ("has", "has_many"),
    ("contain", "has_many"),
    ("includes", "has_many"),
    ("with", "has_many"),
    
    # Belongs-to indicators
    ("belong", "belongs_to"),
    ("part of", "belongs_to"),
    ("in", "belongs_to"),
    ("under", "belongs_to"),
    ("for", "belongs_to"),
    
    # Many-to-many indicators
    ("share", "many_to_many"),
    ("entre", "many_to_many"),  # "between"
    ("across", "many_to_many"),
]


# Framework selection heuristics
# What LLMs learn from project patterns
FRAMEWORK_SIGNALS: Dict[str, List[str]] = {
    "flask": ["web", "app", "website", "api", "crud", "data", "dashboard", "backend"],
    "fastapi": ["api", "rest", "microservice", "endpoint", "json"],
    "html_canvas": ["game", "draw", "animation", "visual", "interactive"],
    "click": ["cli", "command", "tool", "script", "utility"],
    "sklearn": ["predict", "classify", "train", "model", "ml", "machine learning"],
}


def infer_framework(description: str, has_data: bool, is_interactive: bool) -> str:
    """Infer the best framework based on description."""
    desc_lower = description.lower()
    
    # Check for explicit signals
    if any(word in desc_lower for word in ["game", "canvas", "draw", "animation"]):
        return "html_canvas"
    
    if any(word in desc_lower for word in ["cli", "command line", "terminal", "script"]):
        return "click"
    
    if any(word in desc_lower for word in ["predict", "classify", "train", "model", "ml"]):
        return "sklearn"
    
    if any(word in desc_lower for word in ["api", "rest", "endpoint", "json", "microservice"]):
        return "fastapi"
    
    # Default to Flask for web/data apps
    if has_data or is_interactive:
        return "flask"
    
    return "flask"  # Default fallback


def get_entity_fields(entity_name: str) -> List[FieldDefinition]:
    """Get typical fields for an entity, with fallback to generic fields."""
    entity_lower = entity_name.lower()
    
    # Direct match
    if entity_lower in ENTITY_FIELDS:
        return ENTITY_FIELDS[entity_lower]
    
    # Pluralization handling
    if entity_lower.endswith('s'):
        singular = entity_lower[:-1]
        if singular in ENTITY_FIELDS:
            return ENTITY_FIELDS[singular]
    
    # Ies → y (categories → category)
    if entity_lower.endswith('ies'):
        singular = entity_lower[:-3] + 'y'
        if singular in ENTITY_FIELDS:
            return ENTITY_FIELDS[singular]
    
    # Default generic fields
    return [
        FieldDefinition("name", "str", True, f"{entity_name} name"),
        FieldDefinition("description", "text", False, f"{entity_name} description"),
        FieldDefinition("created_at", "datetime", False, "Creation timestamp"),
    ]


def infer_field_type(field_name: str) -> str:
    """Infer field type from field name."""
    field_lower = field_name.lower()
    
    # Check for exact matches
    if field_lower in TYPE_HINTS:
        return TYPE_HINTS[field_lower]
    
    # Check for partial matches (e.g., "user_name" → "name" → "str")
    for hint_key, hint_type in TYPE_HINTS.items():
        if hint_key in field_lower:
            return hint_type
    
    # Default to string
    return "str"


def extract_features_from_actions(description: str) -> Set[str]:
    """Extract features based on action verbs in description."""
    desc_lower = description.lower()
    features = set()
    
    for action, action_features in ACTION_FEATURES.items():
        if action in desc_lower:
            features.update(action_features)
    
    # Always add database if we detected CRUD
    if "crud" in features:
        features.add("database")
    
    return features
