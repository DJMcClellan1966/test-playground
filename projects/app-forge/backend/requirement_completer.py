"""
Requirement Completer - Local algorithm inspired by LLM completion/prediction.

Given partial requirements, predicts what's likely needed based on:
- Domain co-occurrence statistics (recipes usually have ingredients)
- App type patterns (trackers usually need timestamps)
- Feature dependencies (auth usually implies users)

No AI - uses pre-computed statistical relationships.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import re


@dataclass
class CompletedRequirement:
    """A predicted/inferred requirement."""
    name: str
    field_type: str
    confidence: float  # 0.0 - 1.0
    reason: str  # Why we inferred this
    source: str  # What triggered the inference


@dataclass
class RequirementCompletion:
    """Result of requirement completion."""
    explicit: List[str]  # What user explicitly mentioned
    inferred: List[CompletedRequirement]  # What we predict they need
    features: Set[str]  # Inferred feature flags
    relationships: List[Tuple[str, str, str]]  # (entity1, relation, entity2)


# Domain co-occurrence: when users mention X, they usually need Y
# Format: trigger_word -> [(inferred_field, type, confidence, reason)]
DOMAIN_COOCCURRENCE = {
    # Food/Recipe domain
    'recipe': [
        ('ingredients', 'list', 0.95, 'recipes always have ingredients'),
        ('instructions', 'text', 0.90, 'recipes need preparation steps'),
        ('servings', 'integer', 0.75, 'helpful for scaling recipes'),
        ('prep_time', 'integer', 0.70, 'users often filter by time'),
        ('cook_time', 'integer', 0.70, 'cooking time is essential'),
        ('cuisine', 'string', 0.60, 'helps categorize recipes'),
        ('difficulty', 'string', 0.55, 'skill level indicator'),
    ],
    'ingredient': [
        ('quantity', 'float', 0.90, 'ingredients need amounts'),
        ('unit', 'string', 0.85, 'measurement units required'),
        ('name', 'string', 0.95, 'ingredient name required'),
    ],
    'meal': [
        ('meal_type', 'string', 0.80, 'breakfast/lunch/dinner'),
        ('date', 'date', 0.85, 'meal planning uses dates'),
        ('calories', 'integer', 0.60, 'nutrition tracking'),
    ],
    
    # Task/Productivity domain
    'task': [
        ('due_date', 'datetime', 0.85, 'tasks usually have deadlines'),
        ('priority', 'string', 0.80, 'prioritization is common'),
        ('completed', 'boolean', 0.90, 'track completion status'),
        ('description', 'text', 0.70, 'task details'),
    ],
    'todo': [
        ('due_date', 'datetime', 0.80, 'todos often have deadlines'),
        ('completed', 'boolean', 0.95, 'completion tracking'),
        ('priority', 'string', 0.65, 'optional prioritization'),
    ],
    'reminder': [
        ('remind_at', 'datetime', 0.95, 'reminders need time'),
        ('repeat', 'string', 0.60, 'recurring reminders'),
        ('acknowledged', 'boolean', 0.75, 'dismissal tracking'),
    ],
    
    # Health/Fitness domain
    'workout': [
        ('duration', 'integer', 0.90, 'workout length'),
        ('date', 'date', 0.85, 'when it happened'),
        ('exercise_type', 'string', 0.80, 'type of exercise'),
        ('calories_burned', 'integer', 0.65, 'energy tracking'),
        ('notes', 'text', 0.50, 'optional notes'),
    ],
    'exercise': [
        ('sets', 'integer', 0.85, 'strength training uses sets'),
        ('reps', 'integer', 0.85, 'repetitions per set'),
        ('weight', 'float', 0.75, 'weight used'),
        ('duration', 'integer', 0.70, 'for cardio exercises'),
    ],
    'weight': [
        ('weight_value', 'float', 0.95, 'the weight measurement'),
        ('date', 'date', 0.90, 'when measured'),
        ('unit', 'string', 0.60, 'kg/lbs'),
    ],
    
    # Finance domain  
    'expense': [
        ('amount', 'float', 0.95, 'cost is essential'),
        ('category', 'string', 0.85, 'categorization'),
        ('date', 'date', 0.90, 'when spent'),
        ('description', 'string', 0.70, 'what it was for'),
        ('receipt', 'string', 0.40, 'optional receipt image'),
    ],
    'budget': [
        ('amount', 'float', 0.95, 'budget limit'),
        ('category', 'string', 0.90, 'what it covers'),
        ('period', 'string', 0.80, 'weekly/monthly/yearly'),
        ('spent', 'float', 0.75, 'tracking current spend'),
    ],
    'invoice': [
        ('amount', 'float', 0.95, 'invoice total'),
        ('due_date', 'date', 0.90, 'payment deadline'),
        ('client', 'string', 0.85, 'who to bill'),
        ('paid', 'boolean', 0.80, 'payment status'),
        ('invoice_number', 'string', 0.75, 'unique identifier'),
    ],
    
    # Collection/Inventory domain
    'book': [
        ('author', 'string', 0.90, 'books have authors'),
        ('isbn', 'string', 0.60, 'optional identifier'),
        ('genre', 'string', 0.70, 'categorization'),
        ('read', 'boolean', 0.75, 'reading status'),
        ('rating', 'integer', 0.65, 'personal rating'),
    ],
    'movie': [
        ('director', 'string', 0.75, 'movie director'),
        ('year', 'integer', 0.80, 'release year'),
        ('genre', 'string', 0.85, 'categorization'),
        ('rating', 'integer', 0.80, 'user rating'),
        ('watched', 'boolean', 0.70, 'watch status'),
    ],
    'inventory': [
        ('quantity', 'integer', 0.95, 'stock count'),
        ('sku', 'string', 0.70, 'product identifier'),
        ('location', 'string', 0.65, 'where stored'),
        ('reorder_level', 'integer', 0.60, 'when to reorder'),
    ],
    
    # Event/Scheduling domain
    'event': [
        ('start_time', 'datetime', 0.95, 'when it starts'),
        ('end_time', 'datetime', 0.85, 'when it ends'),
        ('location', 'string', 0.75, 'where it happens'),
        ('attendees', 'list', 0.55, 'who is invited'),
    ],
    'appointment': [
        ('datetime', 'datetime', 0.95, 'when scheduled'),
        ('duration', 'integer', 0.80, 'how long'),
        ('with_person', 'string', 0.75, 'who with'),
        ('notes', 'text', 0.50, 'appointment notes'),
    ],
    'meeting': [
        ('datetime', 'datetime', 0.95, 'meeting time'),
        ('attendees', 'list', 0.80, 'who attends'),
        ('agenda', 'text', 0.70, 'meeting topics'),
        ('location', 'string', 0.65, 'meeting room/link'),
    ],
    
    # Tracking/Logging domain
    'log': [
        ('timestamp', 'datetime', 0.95, 'when logged'),
        ('entry', 'text', 0.85, 'log content'),
        ('category', 'string', 0.60, 'log type'),
    ],
    'entry': [
        ('timestamp', 'datetime', 0.90, 'entry time'),
        ('content', 'text', 0.85, 'entry content'),
    ],
    'habit': [
        ('completed_at', 'datetime', 0.90, 'when completed'),
        ('streak', 'integer', 0.75, 'consecutive days'),
        ('target', 'string', 0.65, 'daily/weekly target'),
    ],
}

# Feature inference: when app has X characteristic, it likely needs Y feature
FEATURE_INFERENCE = {
    # User-related features
    'personal': {'auth': 0.3},  # Personal might not need auth
    'team': {'auth': 0.90, 'roles': 0.70},
    'multi-user': {'auth': 0.95, 'roles': 0.75},
    'login': {'auth': 0.95, 'sessions': 0.85},
    'user': {'auth': 0.80},
    'account': {'auth': 0.90, 'profile': 0.75},
    
    # Data features
    'search': {'search': 0.90, 'indexing': 0.70},
    'filter': {'filtering': 0.90},
    'sort': {'sorting': 0.85},
    'export': {'export': 0.90},
    'import': {'import': 0.85},
    'report': {'reporting': 0.85, 'export': 0.70},
    'analytics': {'analytics': 0.90, 'charts': 0.75},
    'dashboard': {'dashboard': 0.90, 'charts': 0.70},
    
    # Communication features
    'notify': {'notifications': 0.90},
    'reminder': {'notifications': 0.85, 'scheduling': 0.80},
    'email': {'email': 0.90},
    'sms': {'sms': 0.85},
    
    # Storage features
    'image': {'file_upload': 0.90, 'image_processing': 0.60},
    'photo': {'file_upload': 0.90, 'image_processing': 0.65},
    'file': {'file_upload': 0.90},
    'upload': {'file_upload': 0.95},
    'attachment': {'file_upload': 0.85},
    
    # Platform features
    'mobile': {'responsive': 0.90, 'pwa': 0.60},
    'offline': {'offline': 0.90, 'sync': 0.75},
    'sync': {'sync': 0.90, 'real_time': 0.60},
    'share': {'sharing': 0.90},
    'collaborate': {'real_time': 0.80, 'multi_user': 0.85},
}

# Entity relationships: when A exists, relationship to B is common
RELATIONSHIP_PATTERNS = {
    'recipe': [('recipe', 'has_many', 'ingredients')],
    'ingredient': [('ingredient', 'belongs_to', 'recipe')],
    'task': [('task', 'belongs_to', 'user'), ('task', 'has_many', 'subtasks')],
    'project': [('project', 'has_many', 'tasks')],
    'user': [('user', 'has_many', 'tasks'), ('user', 'has_many', 'notes')],
    'order': [('order', 'has_many', 'items'), ('order', 'belongs_to', 'customer')],
    'category': [('category', 'has_many', 'items')],
    'tag': [('item', 'has_many', 'tags')],
    'comment': [('comment', 'belongs_to', 'post'), ('comment', 'belongs_to', 'user')],
    'post': [('post', 'has_many', 'comments'), ('post', 'belongs_to', 'user')],
}


def complete_requirements(description: str, explicit_fields: Optional[List[str]] = None) -> RequirementCompletion:
    """
    Complete partial requirements based on domain knowledge.
    
    Args:
        description: Natural language description from user
        explicit_fields: Fields the user explicitly mentioned (optional)
    
    Returns:
        RequirementCompletion with inferred requirements
    """
    text = description.lower()
    explicit = explicit_fields or []
    explicit_set = {f.lower() for f in explicit}
    
    inferred = []
    features = set()
    relationships = []
    
    # 1. Find domain triggers and infer fields
    for trigger, field_defs in DOMAIN_COOCCURRENCE.items():
        if re.search(rf'\b{trigger}s?\b', text):  # Match singular and plural
            for field_name, field_type, confidence, reason in field_defs:
                # Don't infer if already explicit
                if field_name.lower() not in explicit_set:
                    inferred.append(CompletedRequirement(
                        name=field_name,
                        field_type=field_type,
                        confidence=confidence,
                        reason=reason,
                        source=trigger
                    ))
    
    # 2. Infer features
    for trigger, feature_map in FEATURE_INFERENCE.items():
        if re.search(rf'\b{trigger}\b', text):
            for feature, conf in feature_map.items():
                features.add(feature)
    
    # 3. Infer relationships
    for trigger, rels in RELATIONSHIP_PATTERNS.items():
        if re.search(rf'\b{trigger}s?\b', text):
            relationships.extend(rels)
    
    # 4. Deduplicate and sort by confidence
    seen_fields = set()
    unique_inferred = []
    for req in sorted(inferred, key=lambda x: x.confidence, reverse=True):
        if req.name not in seen_fields:
            seen_fields.add(req.name)
            unique_inferred.append(req)
    
    # Extract explicit mentions
    explicit_words = extract_explicit_requirements(text)
    
    return RequirementCompletion(
        explicit=list(set(explicit + explicit_words)),
        inferred=unique_inferred,
        features=features,
        relationships=list(set(relationships))
    )


def extract_explicit_requirements(text: str) -> List[str]:
    """Extract explicitly mentioned requirements from text."""
    explicit = []
    
    # "with X" pattern
    with_matches = re.findall(r'with\s+(\w+(?:\s+\w+)?)', text)
    explicit.extend(with_matches)
    
    # "track X" pattern  
    track_matches = re.findall(r'track(?:ing)?\s+(\w+)', text)
    explicit.extend(track_matches)
    
    # "store X" pattern
    store_matches = re.findall(r'stor(?:e|ing)\s+(\w+)', text)
    explicit.extend(store_matches)
    
    # "manage X" pattern
    manage_matches = re.findall(r'manag(?:e|ing)\s+(\w+)', text)
    explicit.extend(manage_matches)
    
    return explicit


def get_high_confidence_fields(completion: RequirementCompletion, threshold: float = 0.70) -> List[CompletedRequirement]:
    """Get only high-confidence inferred fields."""
    return [req for req in completion.inferred if req.confidence >= threshold]


def explain_completion(completion: RequirementCompletion) -> str:
    """Generate human-readable explanation of the completion."""
    lines = []
    
    if completion.explicit:
        lines.append(f"Explicit requirements: {', '.join(completion.explicit)}")
    
    if completion.inferred:
        lines.append("\nInferred requirements:")
        for req in completion.inferred[:10]:  # Top 10
            conf_bar = '█' * int(req.confidence * 5)
            lines.append(f"  [{conf_bar:<5}] {req.name}: {req.field_type} - {req.reason}")
    
    if completion.features:
        lines.append(f"\nSuggested features: {', '.join(completion.features)}")
    
    if completion.relationships:
        lines.append("\nInferred relationships:")
        for e1, rel, e2 in completion.relationships:
            lines.append(f"  {e1} --{rel}--> {e2}")
    
    return '\n'.join(lines)


# Quick test
if __name__ == '__main__':
    test_cases = [
        "a recipe collection app",
        "expense tracker with categories",
        "workout log for gym",
        "todo app with reminders",
        "inventory management system for team",
        "meal planner with shopping list",
        "book collection with ratings",
        "habit tracker for personal goals",
    ]
    
    print("=" * 70)
    print("REQUIREMENT COMPLETER - Local Algorithm Demo")
    print("=" * 70)
    
    for desc in test_cases:
        completion = complete_requirements(desc)
        high_conf = get_high_confidence_fields(completion)
        
        print(f"\n📝 \"{desc}\"")
        print(f"   Explicit: {completion.explicit}")
        print(f"   Inferred ({len(high_conf)} high-conf):")
        for req in high_conf[:5]:
            print(f"      • {req.name} ({req.field_type}) - {req.confidence:.0%}")
        if completion.features:
            print(f"   Features: {completion.features}")
