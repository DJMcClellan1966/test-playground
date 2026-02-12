"""Analogy Engine - Transfer Learning Without Neural Networks.

LLMs excel at transfer learning: "Make X like Y but with Z"
We replicate this through trait blending and modification application.

Examples:
- "Spotify clone for podcasts" → Take Spotify trait, swap media type
- "Instagram but for recipes" → Take Instagram trait, change content domain
- "Todo app like Trello but simpler" → Take Trello trait, reduce complexity
- "Twitter for code snippets" → Take Twitter trait, change post type
"""

import re
from typing import Optional, Tuple, Dict, Set, List, Any
from dataclasses import dataclass, field as datafield

from trait_store import trait_store, AppTrait, DomainModelSchema, DomainField


@dataclass
class AnalogyPattern:
    """Parsed analogy from description."""
    target: str  # What user wants
    base: str    # What it's similar to
    modification: str  # How it differs
    pattern_type: str  # "like_but", "clone_for", "based_on", etc.


@dataclass
class BlendedTrait:
    """Result of blend two or more traits."""
    base_trait_id: str
    modifications: List[str]
    models: List[DomainModelSchema]
    features: Set[str]
    framework: str
    confidence: float = 0.8


# =============================================================================
# ANALOGY PATTERN DETECTION
# =============================================================================

# Regex patterns for different analogy types
ANALOGY_PATTERNS = [
    # "X like Y but Z"
    (r'(.+?)\s+like\s+(.+?)\s+but\s+(.+)', "like_but"),
    
    # "Y clone for X"
    (r'(\w+)\s+clone\s+(?:for|with)\s+(.+)', "clone_for"),
    
    # "Y for X" (e.g., "Spotify for podcasts")
    (r'(\w+)\s+for\s+(.+)', "for_domain"),
    
    # "X similar to Y"
    (r'(.+?)\s+(?:similar to|like)\s+(.+)', "similar_to"),
    
    # "X based on Y"
    (r'(.+?)\s+based on\s+(.+)', "based_on"),
    
    # "Y style X"
    (r'(\w+)(?:-| )style\s+(.+)', "style_of"),
]


def detect_analogy(description: str) -> Optional[AnalogyPattern]:
    """Detect if description contains an analogy pattern."""
    desc_lower = description.lower().strip()
    
    for pattern, pattern_type in ANALOGY_PATTERNS:
        match = re.search(pattern, desc_lower)
        if match:
            groups = match.groups()
            
            if pattern_type == "like_but":
                target, base, modification = groups
                return AnalogyPattern(
                    target=target.strip(),
                    base=base.strip(),
                    modification=modification.strip(),
                    pattern_type=pattern_type
                )
            
            elif pattern_type == "clone_for":
                base, domain = groups
                return AnalogyPattern(
                    target=domain.strip(),
                    base=base.strip(),
                    modification=f"for {domain.strip()}",
                    pattern_type=pattern_type
                )
            
            elif pattern_type == "for_domain":
                base, domain = groups
                # Check if base looks like an app name (common apps)
                if base in ["spotify", "instagram", "twitter", "facebook", 
                            "youtube", "netflix", "uber", "airbnb", "slack",
                            "trello", "notion", "discord"]:
                    return AnalogyPattern(
                        target=f"{base} for {domain}",
                        base=base.strip(),
                        modification=f"for {domain.strip()}",
                        pattern_type=pattern_type
                    )
            
            elif pattern_type in ["similar_to", "based_on"]:
                target, base = groups
                return AnalogyPattern(
                    target=target.strip(),
                    base=base.strip(),
                    modification="",
                    pattern_type=pattern_type
                )
            
            elif pattern_type == "style_of":
                style, target = groups
                return AnalogyPattern(
                    target=target.strip(),
                    base=style.strip(),
                    modification=f"{style} style",
                    pattern_type=pattern_type
                )
    
    return None


# =============================================================================
# TRAIT BLENDING
# =============================================================================

def find_base_trait(base_name: str) -> Optional[AppTrait]:
    """Find the trait to use as base for analogy."""
    # Try exact match first
    matches = trait_store.match(base_name)
    if matches:
        return matches[0]
    
    # Try common app type mappings
    app_type_mapping = {
        "spotify": "music_player",
        "instagram": "photo_sharing",
        "twitter": "microblog",
        "facebook": "social_network",
        "youtube": "video_platform",
        "netflix": "streaming_service",
        "uber": "ride_sharing",
        "airbnb": "rental_marketplace",
        "slack": "team_chat",
        "trello": "board_manager",
        "notion": "document_workspace",
        "discord": "voice_chat",
        "reddit": "forum",
        "medium": "blog_platform",
        "github": "code_repository",
    }
    
    base_lower = base_name.lower()
    if base_lower in app_type_mapping:
        trait_type = app_type_mapping[base_lower]
        # Try to find similar trait
        matches = trait_store.match(trait_type)
        if matches:
            return matches[0]
    
    # Fallback: Try to infer from the name
    if "todo" in base_lower or "task" in base_lower:
        matches = trait_store.match("todo app")
        if matches:
            return matches[0]
    
    if "game" in base_lower:
        matches = trait_store.match("game")
        if matches:
            return matches[0]
    
    if "recipe" in base_lower or "cook" in base_lower:
        matches = trait_store.match("recipe app")
        if matches:
            return matches[0]
    
    return None


def apply_modification(base_trait: AppTrait, 
                        modification: str,
                        target: str) -> BlendedTrait:
    """Apply modification to base trait.
    
    Modifications can be:
    - Domain change: "for podcasts", "for code snippets"
    - Simplification: "simpler", "lighter", "minimal"
    - Enhancement: "with X", "plus Y"
    - Style change: "dark mode", "minimalist"
    """
    mod_lower = modification.lower()
    
    # Start with base trait
    models = base_trait.models.copy()
    features = base_trait.typical_features.copy()
    framework = base_trait.preferred_framework
    
    # Detect modification type
    modifications_applied = []
    
    # Domain change (e.g., "for podcasts")
    if "for " in mod_lower:
        domain = mod_lower.split("for ")[-1].strip()
        models = adapt_models_for_domain(models, domain)
        modifications_applied.append(f"domain_change:{domain}")
    
    # Simplification
    if any(word in mod_lower for word in ["simpler", "lighter", "minimal", "basic"]):
        features = simplify_features(features)
        modifications_applied.append("simplification")
    
    # Enhancement with specific feature
    if "with " in mod_lower or "plus " in mod_lower:
        addition = (mod_lower.split("with ")[-1] if "with " in mod_lower 
                   else mod_lower.split("plus ")[-1]).strip()
        new_features = infer_features_from_text(addition)
        features.update(new_features)
        modifications_applied.append(f"enhancement:{addition}")
    
    # Remove unwanted features
    if "without " in mod_lower or "no " in mod_lower:
        removal = (mod_lower.split("without ")[-1] if "without " in mod_lower
                  else mod_lower.split("no ")[-1]).strip()
        remove_features = infer_features_from_text(removal)
        features -= remove_features
        modifications_applied.append(f"removal:{removal}")
    
    # Framework override
    if any(fw in mod_lower for fw in ["flask", "fastapi", "react", "vue"]):
        for fw in ["flask", "fastapi"]:
            if fw in mod_lower:
                framework = fw
                modifications_applied.append(f"framework:{fw}")
                break
    
    return BlendedTrait(
        base_trait_id=base_trait.id,
        modifications=modifications_applied,
        models=models,
        features=features,
        framework=framework,
        confidence=0.7  # Analogies are decent but not perfect
    )


def blend_multiple_traits(trait1: AppTrait, 
                           trait2: AppTrait,
                           emphasis: float = 0.5) -> BlendedTrait:
    """Blend two traits together (e.g., "recipe app with workout tracking").
    
    Args:
        trait1: Primary trait
        trait2: Secondary trait
        emphasis: Weight towards trait1 (0.5 = equal, 1.0 = all trait1)
    """
    # Merge models
    models = trait1.models.copy()
    # Add models from trait2 that don't conflict
    existing_names = {m.name.lower() for m in models}
    for model in trait2.models:
        if model.name.lower() not in existing_names:
            models.append(model)
    
    # Merge features (union) - convert lists to sets first
    features = set(trait1.typical_features) | set(trait2.typical_features)
    
    # Choose framework (prefer trait1's if emphasis > 0.5)
    framework = trait1.preferred_framework if emphasis >= 0.5 else trait2.preferred_framework
    
    return BlendedTrait(
        base_trait_id=f"{trait1.id}+{trait2.id}",
        modifications=[f"blended with {trait2.id}"],
        models=models,
        features=features,
        framework=framework,
        confidence=0.6  # Blending is more uncertain
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def adapt_models_for_domain(models: List[DomainModelSchema], 
                              domain: str) -> List[DomainModelSchema]:
    """Adapt model names/fields for different domain.
    
    E.g., "Song" → "Podcast", "Photo" → "Recipe"
    """
    # Simple heuristic: keep structure, potentially rename
    # For now, just return as-is since structure is usually valid
    # This could be expanded with domain-specific transformations
    return models


def simplify_features(features: Set[str]) -> Set[str]:
    """Remove optional/advanced features to simplify."""
    optional_features = {"export", "search", "realtime", "auth"}
    # Keep only core features
    return features - optional_features


def infer_features_from_text(text: str) -> Set[str]:
    """Infer features from text description."""
    features = set()
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["auth", "login", "user"]):
        features.add("auth")
    if any(word in text_lower for word in ["search", "find", "filter"]):
        features.add("search")
    if any(word in text_lower for word in ["export", "download", "csv"]):
        features.add("export")
    if any(word in text_lower for word in ["real-time", "live", "websocket"]):
        features.add("realtime")
    if any(word in text_lower for word in ["responsive", "mobile"]):
        features.add("responsive_ui")
    
    return features


# =============================================================================
# MAIN API
# =============================================================================

def process_analogy(description: str) -> Optional[BlendedTrait]:
    """Main entry point: detect and process analogy.
    
    Returns BlendedTrait if analogy detected, None otherwise.
    """
    analogy = detect_analogy(description)
    
    if not analogy:
        return None
    
    # Find base trait
    base_trait = find_base_trait(analogy.base)
    
    if not base_trait:
        # Can't process without base trait
        return None
    
    # Apply modifications
    blended = apply_modification(base_trait, analogy.modification, analogy.target)
    
    return blended


def explain_analogy(description: str, blended: BlendedTrait) -> str:
    """Generate explanation of how analogy was processed."""
    lines = [
        "🔄 ANALOGY DETECTED",
        "=" * 60,
        f"Input: {description}",
        f"Base: {blended.base_trait_id}",
        f"Modifications: {', '.join(blended.modifications)}",
        f"Confidence: {blended.confidence:.0%}",
        "",
        f"📦 Models: {len(blended.models)} ({', '.join(m.name for m in blended.models)})",
        f"🔧 Features: {', '.join(sorted(blended.features))}",
        f"🏗️  Framework: {blended.framework}",
        "=" * 60,
    ]
    return "\n".join(lines)


# =============================================================================
# EXAMPLES FOR TESTING
# =============================================================================

if __name__ == "__main__":
    test_cases = [
        "Spotify clone for podcasts",
        "Instagram but for recipes",
        "Todo app like Trello but simpler",
        "Twitter for code snippets",
        "recipe app similar to todo list",
    ]
    
    print("ANALOGY ENGINE TEST")
    print("=" * 60)
    
    for desc in test_cases:
        print(f"\n📝 Input: {desc}")
        analogy = detect_analogy(desc)
        if analogy:
            print(f"   Pattern: {analogy.pattern_type}")
            print(f"   Target: {analogy.target}")
            print(f"   Base: {analogy.base}")
            print(f"   Modification: {analogy.modification}")
            
            blended = process_analogy(desc)
            if blended:
                print(f"   ✓ Blended successfully")
                print(f"   Features: {list(blended.features)[:3]}...")
            else:
                print(f"   ✗ Could not find base trait")
        else:
            print("   (no analogy detected)")
