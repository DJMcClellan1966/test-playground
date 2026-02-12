"""
SEMANTIC BRIDGE: Universal Language Model for Code Generation
Uses word embeddings for UNDERSTANDING without GENERATION.

Key insight: Use AI for matching/classification, NOT generation.
This avoids hallucination while gaining semantic understanding.
"""

import re
import math
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass


# =============================================================================
# CONCEPT ARCHETYPES: Universal patterns that map to code structures
# =============================================================================

@dataclass
class ConceptArchetype:
    """A universal pattern that maps to code."""
    id: str
    name: str
    synonyms: Set[str]           # Direct synonyms
    related: Set[str]            # Related concepts (weaker match)
    data_pattern: str            # "collection", "tracker", "log", "scheduler"
    typical_fields: List[str]    # Common fields for this archetype
    typical_actions: List[str]   # CRUD operations this implies


# Universal archetypes that appear across ALL domains
ARCHETYPES = {
    # Data structure patterns
    "collection": ConceptArchetype(
        id="collection",
        name="Collection/Inventory",
        synonyms={"collection", "inventory", "catalog", "library", "list", "database", "repository"},
        related={"store", "archive", "vault", "gallery", "portfolio"},
        data_pattern="collection",
        typical_fields=["id", "name", "description", "category", "created_at"],
        typical_actions=["create", "read", "update", "delete", "search", "filter"]
    ),
    
    "tracker": ConceptArchetype(
        id="tracker",
        name="Tracker/Monitor",
        synonyms={"tracker", "monitor", "logger", "recorder", "watcher"},
        related={"track", "follow", "observe", "measure", "log"},
        data_pattern="tracker",
        typical_fields=["id", "timestamp", "value", "status", "notes"],
        typical_actions=["create", "read", "chart", "history", "export"]
    ),
    
    "scheduler": ConceptArchetype(
        id="scheduler",
        name="Scheduler/Planner",
        synonyms={"scheduler", "planner", "calendar", "agenda", "schedule"},
        related={"plan", "reminder", "appointment", "event", "booking"},
        data_pattern="scheduler",
        typical_fields=["id", "title", "date", "time", "duration", "recurrence"],
        typical_actions=["create", "read", "upcoming", "past", "notify"]
    ),
    
    "workflow": ConceptArchetype(
        id="workflow",
        name="Workflow/Process",
        synonyms={"workflow", "process", "pipeline", "procedure", "flow"},
        related={"step", "stage", "phase", "task", "action"},
        data_pattern="workflow",
        typical_fields=["id", "name", "current_step", "status", "started_at"],
        typical_actions=["start", "advance", "complete", "abort", "history"]
    ),
    
    # Action patterns
    "generator": ConceptArchetype(
        id="generator",
        name="Generator/Creator",
        synonyms={"generator", "creator", "maker", "builder", "producer"},
        related={"create", "generate", "build", "produce", "random"},
        data_pattern="generator",
        typical_fields=["id", "output", "parameters", "created_at"],
        typical_actions=["generate", "configure", "save", "history"]
    ),
    
    "converter": ConceptArchetype(
        id="converter",
        name="Converter/Transformer",
        synonyms={"converter", "transformer", "translator", "encoder", "formatter"},
        related={"convert", "transform", "translate", "encode", "format"},
        data_pattern="converter",
        typical_fields=["input", "output", "format_from", "format_to"],
        typical_actions=["convert", "preview", "batch"]
    ),
    
    "calculator": ConceptArchetype(
        id="calculator",
        name="Calculator/Computer",
        synonyms={"calculator", "computer", "solver", "estimator"},
        related={"calculate", "compute", "solve", "estimate", "math"},
        data_pattern="calculator",
        typical_fields=["inputs", "result", "formula"],
        typical_actions=["calculate", "clear", "history"]
    ),
}


# =============================================================================
# SEMANTIC SIMILARITY: Lightweight word similarity without full LLM
# =============================================================================

# Pre-computed semantic clusters (could be generated from word2vec/GloVe)
# These represent words that are "close" in embedding space
SEMANTIC_CLUSTERS = {
    # Food/Cooking cluster
    "cooking": {"recipe", "ingredient", "meal", "dish", "food", "cook", "kitchen", "cuisine"},
    "fermentation": {"brewing", "kombucha", "sourdough", "beer", "wine", "yeast", "culture"},
    
    # Nature/Garden cluster  
    "gardening": {"plant", "garden", "soil", "water", "grow", "seed", "harvest"},
    "beekeeping": {"bee", "hive", "honey", "apiary", "inspection", "colony", "swarm"},
    "birding": {"bird", "species", "sighting", "nest", "migration", "watching"},
    
    # Hobbies/Crafts cluster
    "crafts": {"knitting", "sewing", "pattern", "stitch", "yarn", "fabric", "craft"},
    "music": {"vinyl", "record", "album", "song", "artist", "playlist", "audio"},
    "gaming": {"game", "dice", "card", "board", "player", "score", "dungeon", "campaign"},
    "photography": {"photo", "camera", "lens", "exposure", "astrophotography", "session"},
    
    # Tech/Computing cluster
    "computing": {"keyboard", "mouse", "switch", "mechanical", "typing", "hardware"},
    "programming": {"code", "api", "database", "server", "app", "software"},
    
    # Time/Organization cluster
    "scheduling": {"schedule", "calendar", "reminder", "appointment", "date", "time"},
    "tracking": {"track", "log", "record", "monitor", "history", "progress"},
}


def find_semantic_cluster(word: str) -> Optional[str]:
    """Find which semantic cluster a word belongs to."""
    word_lower = word.lower()
    for cluster_name, words in SEMANTIC_CLUSTERS.items():
        if word_lower in words:
            return cluster_name
    return None


def get_related_words(word: str) -> Set[str]:
    """Get words semantically related to the input."""
    word_lower = word.lower()
    related = set()
    for cluster_name, words in SEMANTIC_CLUSTERS.items():
        if word_lower in words:
            related.update(words)
    return related - {word_lower}


# =============================================================================
# UNIVERSAL NOUN/VERB EXTRACTION
# =============================================================================

# Common verbs and their implied operations
VERB_TO_OPERATION = {
    # CRUD verbs
    "add": "create", "create": "create", "new": "create", "make": "create",
    "save": "create", "store": "create", "record": "create", "log": "create",
    "view": "read", "show": "read", "display": "read", "list": "read",
    "get": "read", "find": "read", "search": "read", "browse": "read",
    "edit": "update", "modify": "update", "change": "update", "update": "update",
    "delete": "delete", "remove": "delete", "clear": "delete",
    
    # Domain verbs
    "track": "tracker", "monitor": "tracker", "watch": "tracker",
    "schedule": "scheduler", "plan": "scheduler", "remind": "scheduler",
    "generate": "generator", "random": "generator", "create": "generator",
    "convert": "converter", "transform": "converter", "translate": "converter",
    "calculate": "calculator", "compute": "calculator", "solve": "calculator",
    "collect": "collection", "organize": "collection", "catalog": "collection",
}


def extract_concepts(description: str) -> Dict[str, any]:
    """Extract universal concepts from natural language."""
    words = re.findall(r'\b[a-z]+\b', description.lower())
    
    result = {
        "raw_words": words,
        "archetypes_matched": [],
        "semantic_clusters": set(),
        "implied_operations": set(),
        "inferred_fields": set(),
        "domain_nouns": [],
    }
    
    # 1. Direct archetype matching
    for word in words:
        for arch_id, archetype in ARCHETYPES.items():
            if word in archetype.synonyms:
                result["archetypes_matched"].append((arch_id, "direct", 1.0))
            elif word in archetype.related:
                result["archetypes_matched"].append((arch_id, "related", 0.7))
    
    # 2. Semantic cluster detection
    for word in words:
        cluster = find_semantic_cluster(word)
        if cluster:
            result["semantic_clusters"].add(cluster)
    
    # 3. Verb → Operation mapping
    for word in words:
        if word in VERB_TO_OPERATION:
            result["implied_operations"].add(VERB_TO_OPERATION[word])
    
    # 4. Domain noun extraction (nouns not in our known vocabulary)
    known_words = set()
    for arch in ARCHETYPES.values():
        known_words.update(arch.synonyms)
        known_words.update(arch.related)
    for cluster in SEMANTIC_CLUSTERS.values():
        known_words.update(cluster)
    
    # Words that aren't in our vocabulary are likely domain-specific nouns
    for word in words:
        if word not in known_words and len(word) > 3:
            # Check if it's probably a noun (not a common word)
            common = {"with", "that", "this", "from", "have", "been", "were", "they"}
            if word not in common:
                result["domain_nouns"].append(word)
    
    return result


# =============================================================================
# SEMANTIC BRIDGE: Map unfamiliar domains to code structures
# =============================================================================

@dataclass
class SemanticMapping:
    """Maps extracted concepts to code generation decisions."""
    primary_archetype: str
    confidence: float
    data_model_name: str
    suggested_fields: List[str]
    suggested_routes: List[str]
    semantic_context: str  # Human-readable explanation


def build_semantic_bridge(description: str) -> SemanticMapping:
    """
    The core algorithm: map ANY description to code generation decisions.
    Uses semantic understanding without LLM generation.
    """
    concepts = extract_concepts(description)
    
    # Score each archetype
    archetype_scores = {}
    for arch_id, match_type, score in concepts["archetypes_matched"]:
        if arch_id not in archetype_scores:
            archetype_scores[arch_id] = 0
        archetype_scores[arch_id] += score
    
    # Boost based on semantic clusters
    cluster_to_archetype = {
        "tracking": "tracker",
        "scheduling": "scheduler", 
        "crafts": "collection",
        "music": "collection",
        "gaming": "workflow",
        "cooking": "collection",
        "fermentation": "tracker",
        "beekeeping": "tracker",
        "birding": "collection",
        "gardening": "tracker",
        "photography": "scheduler",
        "computing": "collection",
    }
    
    for cluster in concepts["semantic_clusters"]:
        if cluster in cluster_to_archetype:
            arch_id = cluster_to_archetype[cluster]
            archetype_scores[arch_id] = archetype_scores.get(arch_id, 0) + 0.5
    
    # Select best archetype
    if archetype_scores:
        best_arch = max(archetype_scores.items(), key=lambda x: x[1])
        primary_archetype = best_arch[0]
        confidence = min(1.0, best_arch[1] / 2.0)
    else:
        primary_archetype = "collection"  # Safe default
        confidence = 0.3
    
    archetype = ARCHETYPES[primary_archetype]
    
    # Generate model name from domain nouns
    if concepts["domain_nouns"]:
        model_name = concepts["domain_nouns"][0].title()
    else:
        # Use first significant word
        for word in concepts["raw_words"]:
            if len(word) > 3 and word not in {"with", "that", "this", "from"}:
                model_name = word.title()
                break
        else:
            model_name = "Item"
    
    # Build suggested fields
    suggested_fields = archetype.typical_fields.copy()
    
    # Add domain-specific field hints
    domain_field_hints = {
        "fermentation": ["temperature", "ph_level", "fermentation_day"],
        "beekeeping": ["hive_number", "queen_status", "population_estimate"],
        "birding": ["species", "location", "date_spotted", "notes"],
        "cooking": ["ingredients", "cook_time", "difficulty", "rating"],
        "photography": ["exposure_time", "iso", "focal_length", "location"],
        "gardening": ["plant_type", "water_schedule", "sunlight_needs"],
        "music": ["artist", "album", "year", "format", "condition"],
    }
    
    for cluster in concepts["semantic_clusters"]:
        if cluster in domain_field_hints:
            suggested_fields.extend(domain_field_hints[cluster])
    
    # Build explanation
    context = f"Detected {primary_archetype} pattern"
    if concepts["semantic_clusters"]:
        context += f" in {', '.join(concepts['semantic_clusters'])} domain(s)"
    
    return SemanticMapping(
        primary_archetype=primary_archetype,
        confidence=confidence,
        data_model_name=model_name,
        suggested_fields=list(set(suggested_fields)),
        suggested_routes=archetype.typical_actions,
        semantic_context=context
    )


# =============================================================================
# DEMONSTRATION
# =============================================================================

def demo_semantic_bridge():
    print("="*70)
    print("  SEMANTIC BRIDGE: Universal Language Understanding for Code Gen")
    print("="*70)
    
    print("\n🧠 KEY INSIGHT: Use AI for UNDERSTANDING, not GENERATION")
    print("   This avoids hallucination while gaining semantic awareness.")
    print()
    
    test_cases = [
        "a fermentation tracking app for homebrewing kombucha",
        "a beehive inspection logger",
        "a sourdough starter feeding schedule",
        "a bird watching life list",
        "a knitting pattern stitch counter",
        "a vinyl record collection with discogs integration",
        "a dungeon master campaign notes organizer",
        "an astrophotography session planner",
        "a mechanical keyboard switch tester log",
        "a plant watering reminder based on soil moisture",
    ]
    
    for desc in test_cases:
        print(f'\n📝 "{desc}"')
        mapping = build_semantic_bridge(desc)
        print(f"   🎯 Archetype: {mapping.primary_archetype} (confidence: {mapping.confidence:.2f})")
        print(f"   📊 Model: {mapping.data_model_name}")
        print(f"   📋 Fields: {mapping.suggested_fields[:5]}...")
        print(f"   🔧 Routes: {mapping.suggested_routes}")
        print(f"   💡 {mapping.semantic_context}")
    
    print("\n" + "="*70)
    print("  WHY THIS APPROACH WORKS")
    print("="*70)
    print("""
1. NO HALLUCINATION
   - We never generate text from an LLM
   - All outputs come from predefined templates
   - Semantic understanding only guides SELECTION

2. DOMAIN AGNOSTIC
   - Universal archetypes apply to ANY domain
   - "Collection" works for recipes, records, birds, etc.
   - "Tracker" works for fermentation, exercise, habits, etc.

3. GRACEFUL DEGRADATION
   - Unknown words → domain-specific model names
   - No matches → safe "collection" fallback
   - Always produces valid code structure

4. LIGHTWEIGHT
   - No LLM API calls needed
   - Pre-computed semantic clusters (could use word2vec offline)
   - Sub-millisecond execution

5. EXTENSIBLE
   - Add new archetypes for new code patterns
   - Add semantic clusters for new domains
   - No retraining required

IMPLEMENTATION OPTIONS:
- Level 1: Keyword clusters (current demo) - ~50KB
- Level 2: Word2Vec embeddings - ~1MB compressed
- Level 3: Sentence transformers - ~100MB, works offline
- Level 4: LLM classification only (no generation) - API calls

The key principle: CLASSIFY don't GENERATE.
""")


if __name__ == "__main__":
    demo_semantic_bridge()
