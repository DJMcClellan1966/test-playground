"""Priority System - Feature Importance Without LLMs.

LLMs learn which features are critical vs optional by seeing patterns in code.
We replicate this with explicit priority rules based on app patterns.

This helps:
- Decide which features to include by default
- Determine what to ask vs what to infer
- Order implementation steps
- Allocate resources/complexity budget
"""

from typing import Dict, Set, List, Tuple
from dataclasses import dataclass
from enum import Enum


class Priority(Enum):
    """Feature priority levels."""
    CRITICAL = 10      # App won't work without it
    ESSENTIAL = 8      # Core functionality
    IMPORTANT = 6      # Significantly improves experience
    USEFUL = 4         # Nice to have
    OPTIONAL = 2       # Can skip entirely
    EXPERIMENTAL = 1   # Bleeding edge, might break


@dataclass
class FeaturePriority:
    """Priority information for a feature."""
    feature: str
    base_priority: Priority
    depends_on: Set[str]  # Blocking dependencies
    blocks: Set[str]  # What this feature blocks
    expensive: bool = False  # Computationally/complexity expensive
    description: str = ""


# =============================================================================
# FEATURE PRIORITY DEFINITIONS
# =============================================================================

FEATURE_PRIORITIES: Dict[str, FeaturePriority] = {
    # Data layer
    "database": FeaturePriority(
        feature="database",
        base_priority=Priority.CRITICAL,
        depends_on=set(),
        blocks={"crud", "auth", "search", "export"},
        description="Persistent storage for app data"
    ),
    
    "crud": FeaturePriority(
        feature="crud",
        base_priority=Priority.ESSENTIAL,
        depends_on={"database"},
        blocks=set(),
        description="Create, Read, Update, Delete operations"
    ),
    
    # Authentication
    "auth": FeaturePriority(
        feature="auth",
        base_priority=Priority.IMPORTANT,
        depends_on={"database"},
        blocks=set(),
        expensive=True,
        description="User authentication and authorization"
    ),
    
    # Search & discovery
    "search": FeaturePriority(
        feature="search",
        base_priority=Priority.USEFUL,
        depends_on={"database"},
        blocks=set(),
        description="Search and filter functionality"
    ),
    
    # Export
    "export": FeaturePriority(
        feature="export",
        base_priority=Priority.USEFUL,
        depends_on={"database"},
        blocks=set(),
        description="Export data to CSV/PDF/etc"
    ),
    
    # Real-time
    "realtime": FeaturePriority(
        feature="realtime",
        base_priority=Priority.USEFUL,
        depends_on={"database"},
        blocks=set(),
        expensive=True,
        description="WebSocket real-time updates"
    ),
    
    # UI
    "responsive_ui": FeaturePriority(
        feature="responsive_ui",
        base_priority=Priority.IMPORTANT,
        depends_on=set(),
        blocks=set(),
        description="Mobile-responsive interface"
    ),
    
    # Game features
    "game_loop": FeaturePriority(
        feature="game_loop",
        base_priority=Priority.CRITICAL,  # Critical for games
        depends_on=set(),
        blocks=set(),
        description="Main game loop (for games only)"
    ),
    
    "input_handler": FeaturePriority(
        feature="input_handler",
        base_priority=Priority.ESSENTIAL,
        depends_on={"game_loop"},
        blocks=set(),
        description="Handle keyboard/mouse input"
    ),
    
    "scoring": FeaturePriority(
        feature="scoring",
        base_priority=Priority.IMPORTANT,
        depends_on=set(),
        blocks=set(),
        description="Score tracking and high scores"
    ),
    
    "timer": FeaturePriority(
        feature="timer",
        base_priority=Priority.USEFUL,
        depends_on=set(),
        blocks=set(),
        description="Timer and countdown functionality"
    ),
}


# =============================================================================
# CONTEXT-BASED PRIORITY ADJUSTMENT
# =============================================================================

# Features that become CRITICAL in certain contexts
CONTEXT_CRITICAL: Dict[str, Set[str]] = {
    "social_app": {"auth", "database"},
    "collaborative_app": {"auth", "database", "realtime"},
    "game": {"game_loop", "input_handler"},
    "data_collection": {"database", "crud"},
    "api_service": {"database"},
    "dashboard": {"database", "search"},
}


# Features that become OPTIONAL in certain contexts
CONTEXT_OPTIONAL: Dict[str, Set[str]] = {
    "simple_utility": {"database", "auth"},
    "calculator": {"database", "crud"},
    "game": {"database", "auth", "crud"},
    "read_only": {"crud", "auth"},
}


# Features that are expensive and should be asked explicitly
EXPENSIVE_FEATURES = {"auth", "realtime", "export"}


# =============================================================================
# PRIORITY CALCULATION
# =============================================================================

def calculate_priority(feature: str, 
                        context: Dict[str, any],
                        existing_features: Set[str]) -> Tuple[Priority, str]:
    """Calculate priority of a feature in given context.
    
    Args:
        feature: Feature to evaluate
        context: Dict with keys like app_type, has_users, is_collaborative, etc
        existing_features: Features already selected
        
    Returns:
        (priority_level, reasoning)
    """
    if feature not in FEATURE_PRIORITIES:
        return Priority.OPTIONAL, "Unknown feature"
    
    feat_info = FEATURE_PRIORITIES[feature]
    base_priority = feat_info.base_priority
    reasoning = []
    
    # Check if blocking dependency exists
    if feat_info.depends_on:
        missing = feat_info.depends_on - existing_features
        if missing:
            return Priority.OPTIONAL, f"Missing dependencies: {', '.join(missing)}"
    
    # Adjust based on context
    app_type = context.get("app_type", "")
    
    # Critical in certain contexts
    for context_type, critical_features in CONTEXT_CRITICAL.items():
        if context_type in app_type.lower() or context.get(context_type):
            if feature in critical_features:
                base_priority = Priority.CRITICAL
                reasoning.append(f"Critical for {context_type}")
                break
    
    # Optional in certain contexts
    for context_type, optional_features in CONTEXT_OPTIONAL.items():
        if context_type in app_type.lower() or context.get(context_type):
            if feature in optional_features:
                if base_priority.value > Priority.OPTIONAL.value:
                    base_priority = Priority.OPTIONAL
                    reasoning.append(f"Optional for {context_type}")
                break
    
    # Boost priority if it unblocks other wanted features
    if feat_info.blocks:
        unblocked = feat_info.blocks & existing_features
        if unblocked:
            if base_priority.value < Priority.ESSENTIAL.value:
                base_priority = Priority.ESSENTIAL
                reasoning.append(f"Required by {', '.join(unblocked)}")
    
    # User explicitly mentioned this feature
    if context.get(f"wants_{feature}"):
        base_priority = Priority.ESSENTIAL
        reasoning.append("Explicitly requested")
    
    # User explicitly doesn't want this
    if context.get(f"no_{feature}"):
        return Priority.OPTIONAL, "User opted out"
    
    reason_str = "; ".join(reasoning) if reasoning else feat_info.description
    return base_priority, reason_str


def rank_features(features: Set[str], 
                   context: Dict[str, any]) -> List[Tuple[str, Priority, str]]:
    """Rank features by priority in given context.
    
    Returns list of (feature, priority, reasoning) sorted by priority.
    """
    ranked = []
    
    for feature in features:
        priority, reasoning = calculate_priority(feature, context, features)
        ranked.append((feature, priority, reasoning))
    
    # Sort by priority (highest first)
    ranked.sort(key=lambda x: x[1].value, reverse=True)
    
    return ranked


def partition_features(features: Set[str],
                        context: Dict[str, any]) -> Dict[str, Set[str]]:
    """Partition features into priority groups.
    
    Returns:
        {
            "critical": {...},
            "essential": {...},
            "important": {...},
            "optional": {...}
        }
    """
    partitions = {
        "critical": set(),
        "essential": set(),
        "important": set(),
        "optional": set(),
    }
    
    for feature in features:
        priority, _ = calculate_priority(feature, context, features)
        
        if priority.value >= Priority.CRITICAL.value:
            partitions["critical"].add(feature)
        elif priority.value >= Priority.ESSENTIAL.value:
            partitions["essential"].add(feature)
        elif priority.value >= Priority.IMPORTANT.value:
            partitions["important"].add(feature)
        else:
            partitions["optional"].add(feature)
    
    return partitions


# =============================================================================
# QUESTION GENERATION
# =============================================================================

def should_ask_about_feature(feature: str, context: Dict[str, any]) -> Tuple[bool, str]:
    """Decide if we should ask user about a feature.
    
    Returns (should_ask, reason)
    """
    if feature not in FEATURE_PRIORITIES:
        return False, "Unknown feature"
    
    feat_info = FEATURE_PRIORITIES[feature]
    existing_features = context.get("existing_features", set())
    
    priority, _ = calculate_priority(feature, context, existing_features)
    
    # Always auto-include CRITICAL features
    if priority == Priority.CRITICAL:
        return False, "Auto-included (critical)"
    
    # Ask about EXPENSIVE features before adding
    if feat_info.expensive and feature not in existing_features:
        return True, "Expensive feature"
    
    # Ask about IMPORTANT but not ESSENTIAL
    if priority == Priority.IMPORTANT:
        return True, "Important but not essential"
    
    # Auto-include ESSENTIAL
    if priority == Priority.ESSENTIAL:
        return False, "Auto-included (essential)"
    
    # Ask about USEFUL/OPTIONAL
    if priority.value <= Priority.USEFUL.value:
        return True, "Nice-to-have feature"
    
    return False, "Default behavior"


def generate_priority_questions(inferred_features: Set[str],
                                  context: Dict[str, any]) -> List[Dict[str, any]]:
    """Generate questions for features based on priority.
    
    Returns list of question dicts for SmartQ integration.
    """
    questions = []
    
    for feature in inferred_features:
        should_ask, reason = should_ask_about_feature(feature, context)
        
        if should_ask:
            feat_info = FEATURE_PRIORITIES.get(feature)
            if feat_info:
                questions.append({
                    "feature": feature,
                    "text": f"Include {feature}?",
                    "description": feat_info.description,
                    "priority": calculate_priority(feature, context, inferred_features)[0].name,
                    "expensive": feat_info.expensive,
                })
    
    # Sort questions by priority (ask about important things first)
    questions.sort(key=lambda q: Priority[q["priority"]].value, reverse=True)
    
    return questions


# =============================================================================
# IMPLEMENTATION ORDERING
# =============================================================================

def get_implementation_order(features: Set[str]) -> List[str]:
    """Get optimal order to implement features (respecting dependencies)."""
    implemented = set()
    order = []
    
    max_iterations = len(features) * 2  # Prevent infinite loop
    iteration = 0
    
    while len(implemented) < len(features) and iteration < max_iterations:
        iteration += 1
        
        for feature in features:
            if feature in implemented:
                continue
            
            # Check if dependencies are met
            if feature in FEATURE_PRIORITIES:
                deps = FEATURE_PRIORITIES[feature].depends_on
                if deps.issubset(implemented):
                    order.append(feature)
                    implemented.add(feature)
            else:
                # Unknown feature, add at end
                order.append(feature)
                implemented.add(feature)
    
    return order


# =============================================================================
# REPORTING
# =============================================================================

def explain_priorities(features: Set[str], context: Dict[str, any]) -> str:
    """Generate human-readable explanation of feature priorities."""
    lines = ["=" * 60, "FEATURE PRIORITY ANALYSIS", "=" * 60]
    
    partitions = partition_features(features, context)
    
    for level in ["critical", "essential", "important", "optional"]:
        feats = partitions[level]
        if feats:
            lines.append(f"\n{level.upper()}:")
            for feat in sorted(feats):
                priority, reasoning = calculate_priority(feat, context, features)
                lines.append(f"  • {feat}: {reasoning}")
    
    lines.append("\n" + "=" * 60)
    
    return "\n".join(lines)
