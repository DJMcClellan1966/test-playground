"""
GloVe Attention Kernel

A semantic perception engine using:
1. Domain-specific word embeddings (from domain_vectors.py)
2. Scaled dot-product attention (from "Attention Is All You Need")
3. Entity detection via embedding similarity

This bridges the gap between:
- Regex matching (brittle, exact match only)
- Full LLMs (slow, expensive, overkill)

Key insight: We don't need to understand language,
we need to detect WHICH domain concepts are present.
"""

import math
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set, Optional, Any

# Add embeddings directory to path
sys.path.insert(0, str(Path(__file__).parent / 'embeddings'))
from domain_vectors import get_embedding, similarity, most_similar, vocabulary_size

# ============================================================================
# ATTENTION MECHANISM
# ============================================================================

def dot_product(a: List[float], b: List[float]) -> float:
    """Compute dot product of two vectors."""
    return sum(x * y for x, y in zip(a, b))


def softmax(scores: List[float], temperature: float = 1.0) -> List[float]:
    """
    Softmax with temperature control.
    Lower temperature = more peaked distribution.
    """
    if not scores:
        return []
    max_score = max(scores)
    exp_scores = [math.exp((s - max_score) / temperature) for s in scores]
    total = sum(exp_scores) or 1.0
    return [e / total for e in exp_scores]


def scaled_dot_product_attention(
    query: List[float],
    keys: List[List[float]],
    values: List[str],
    scale: Optional[float] = None
) -> List[Tuple[str, float]]:
    """
    Core attention mechanism.
    
    Attention(Q, K, V) = softmax(QK^T / √d_k) × V
    
    Returns list of (value, attention_weight) pairs sorted by weight.
    """
    if not keys:
        return []
    
    d_k = len(query)
    scale = scale or math.sqrt(d_k)
    
    # Compute attention scores
    scores = [dot_product(query, key) / scale for key in keys]
    
    # Apply softmax
    weights = softmax(scores, temperature=0.5)  # Sharper distribution
    
    # Pair and sort
    weighted = list(zip(values, weights))
    weighted.sort(key=lambda x: -x[1])
    
    return weighted


# ============================================================================
# ENTITY DEFINITIONS (what we're looking for)
# ============================================================================

# Each entity has representative words whose embeddings define the concept
ENTITY_DEFINITIONS = {
    'recipe': {
        'representatives': ['recipe', 'meal', 'dish', 'food', 'cuisine', 'ingredient', 'cook'],
        'features': {'database', 'crud', 'search'},
        'description': 'Food/recipe management'
    },
    'todo': {
        'representatives': ['todo', 'task', 'checklist', 'reminder', 'deadline', 'item'],
        'features': {'database', 'crud', 'checkbox'},
        'description': 'Task/todo management'
    },
    'expense': {
        'representatives': ['expense', 'budget', 'money', 'cost', 'payment', 'transaction', 'financial'],
        'features': {'database', 'crud', 'charts'},
        'description': 'Financial tracking'
    },
    'workout': {
        'representatives': ['workout', 'exercise', 'fitness', 'gym', 'training', 'routine'],
        'features': {'database', 'crud', 'history', 'charts'},
        'description': 'Fitness tracking'
    },
    'event': {
        'representatives': ['event', 'calendar', 'schedule', 'appointment', 'meeting', 'booking'],
        'features': {'database', 'crud', 'calendar'},
        'description': 'Calendar/scheduling'
    },
    'note': {
        'representatives': ['note', 'memo', 'journal', 'diary', 'entry', 'write', 'document'],
        'features': {'database', 'crud', 'editor'},
        'description': 'Note taking'
    },
    'bookmark': {
        'representatives': ['bookmark', 'link', 'url', 'website', 'favorite', 'save'],
        'features': {'database', 'crud', 'search'},
        'description': 'Link/bookmark saving'
    },
    'contact': {
        'representatives': ['contact', 'person', 'friend', 'user', 'profile', 'people'],
        'features': {'database', 'crud', 'search'},
        'description': 'Contact management'
    },
    'photo': {
        'representatives': ['photo', 'image', 'picture', 'gallery', 'album', 'camera'],
        'features': {'upload', 'gallery', 'storage'},
        'description': 'Photo management'
    },
    'movie': {
        'representatives': ['movie', 'film', 'video', 'watch', 'show', 'streaming'],
        'features': {'database', 'crud', 'ratings', 'search'},
        'description': 'Movie/watch tracking'
    },
    'music': {
        'representatives': ['music', 'song', 'playlist', 'audio', 'listen', 'album'],
        'features': {'database', 'crud', 'player'},
        'description': 'Music management'
    },
    'flashcard': {
        'representatives': ['flashcard', 'card', 'study', 'learn', 'quiz', 'memorize', 'review'],
        'features': {'database', 'crud', 'quiz', 'spaced_repetition'},
        'description': 'Study/learning'
    },
    'game': {
        'representatives': ['game', 'play', 'score', 'level', 'player', 'win', 'challenge'],
        'features': {'state', 'interactive', 'score'},
        'description': 'Game/play'
    },
    'inventory': {
        'representatives': ['inventory', 'stock', 'item', 'quantity', 'warehouse', 'supply'],
        'features': {'database', 'crud', 'tracking'},
        'description': 'Inventory management'
    },
    'habit': {
        'representatives': ['habit', 'track', 'daily', 'routine', 'streak', 'goal'],
        'features': {'database', 'crud', 'charts', 'streak'},
        'description': 'Habit tracking'
    }
}

# Pre-compute entity embeddings (average of representative vectors)
_ENTITY_EMBEDDINGS: Dict[str, List[float]] = {}

def _compute_entity_embeddings():
    """Compute centroid embedding for each entity."""
    for entity, info in ENTITY_DEFINITIONS.items():
        vecs = [get_embedding(word) for word in info['representatives']]
        # Average the vectors
        dim = len(vecs[0])
        centroid = [sum(v[i] for v in vecs) / len(vecs) for i in range(dim)]
        # Normalize
        magnitude = math.sqrt(sum(x*x for x in centroid))
        _ENTITY_EMBEDDINGS[entity] = [x/magnitude for x in centroid]

_compute_entity_embeddings()


# ============================================================================
# GLOVE ATTENTION PERCEPTION ENGINE
# ============================================================================

@dataclass
class SemanticPercept:
    """Result of semantic perception."""
    raw_input: str
    tokens: List[str]
    entities: Dict[str, float]  # entity -> confidence (0-1)
    intent: str
    features: Set[str]
    attention_details: Dict[str, Any] = field(default_factory=dict)


class GloVeAttentionEngine:
    """
    Semantic perception using GloVe embeddings + attention.
    
    Process:
    1. Tokenize input
    2. Embed each token
    3. For each entity: compute attention from entity embedding to token embeddings
    4. Aggregate attention scores to detect entities
    5. Infer features from detected entities
    """
    
    # Minimum confidence to report an entity
    ENTITY_THRESHOLD = 0.25
    
    # Intent detection patterns (still use simple rules for intent)
    INTENT_PATTERNS = {
        'query': ['search', 'find', 'look', 'query', 'get', 'show', 'list', 'filter'],
        'create': ['create', 'add', 'new', 'make', 'build', 'start'],
        'delete': ['delete', 'remove', 'clear', 'erase', 'drop'],
        'update': ['update', 'edit', 'change', 'modify', 'fix'],
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize input text."""
        # Remove punctuation, lowercase, split
        text = re.sub(r"[^\w\s']", ' ', text.lower())
        text = re.sub(r"'s\b", '', text)  # Remove possessives
        tokens = text.split()
        # Filter very short tokens and stopwords
        stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
                     'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                     'as', 'into', 'and', 'or', 'but', 'if', 'i', 'me', 'my',
                     'we', 'our', 'you', 'your', 'it', 'its', 'this', 'that'}
        return [t for t in tokens if len(t) > 1 and t not in stopwords]
    
    def perceive(self, text: str) -> SemanticPercept:
        """
        Main perception function.
        
        Uses attention to detect which entities are present in the input.
        """
        tokens = self.tokenize(text)
        
        if not tokens:
            return SemanticPercept(
                raw_input=text,
                tokens=[],
                entities={},
                intent='unknown',
                features=set()
            )
        
        # Get embeddings for all tokens
        token_embeddings = [get_embedding(t) for t in tokens]
        
        # Detect entities using semantic similarity
        entities = {}
        attention_details = {}
        
        for entity_name, entity_embedding in _ENTITY_EMBEDDINGS.items():
            entity_info = ENTITY_DEFINITIONS[entity_name]
            
            # Compute max similarity between any token and entity representatives
            max_sim = 0.0
            best_token = None
            
            for token, token_emb in zip(tokens, token_embeddings):
                # Direct cosine similarity to entity centroid
                sim = dot_product(token_emb, entity_embedding)
                
                # Also check similarity to individual representatives
                for rep in entity_info['representatives']:
                    rep_sim = similarity(token, rep)
                    sim = max(sim, rep_sim)
                
                if sim > max_sim:
                    max_sim = sim
                    best_token = token
            
            # Confidence based on similarity
            # Similarity > 0.8 = strong match, 0.5-0.8 = partial, < 0.5 = weak
            confidence = 0.0
            
            # Exact match in representatives
            for token in tokens:
                if token in entity_info['representatives']:
                    confidence = max(confidence, 0.95)
                elif any(token.startswith(rep[:4]) for rep in entity_info['representatives'] if len(rep) >= 4):
                    confidence = max(confidence, 0.7)
            
            # Semantic match (only count if similarity is strong)
            if max_sim > 0.75:
                confidence = max(confidence, max_sim * 0.8)
            elif max_sim > 0.5:
                confidence = max(confidence, max_sim * 0.4)
            
            attention_details[entity_name] = [(best_token, max_sim)] if best_token else []
            
            if confidence > self.ENTITY_THRESHOLD:
                entities[entity_name] = confidence
        
        # Only keep entities with meaningful confidence
        if entities:
            max_conf = max(entities.values())
            # Only keep entities that are at least 70% of max confidence
            # This ensures we don't get lots of low-confidence matches
            entities = {k: v for k, v in entities.items() if v >= max_conf * 0.7}
        
        # Detect intent
        intent = self._detect_intent(tokens, entities)
        
        # Collect features from detected entities
        features = self._collect_features(entities)
        
        percept = SemanticPercept(
            raw_input=text,
            tokens=tokens,
            entities=entities,
            intent=intent,
            features=features,
            attention_details=attention_details if self.verbose else {}
        )
        
        if self.verbose:
            self._print_debug(percept)
        
        return percept
    
    def _detect_intent(self, tokens: List[str], entities: Dict[str, float]) -> str:
        """Detect user intent from tokens."""
        for intent, keywords in self.INTENT_PATTERNS.items():
            for token in tokens:
                if token in keywords:
                    return intent
        
        # Default: if we detected entities, probably building an app
        if entities:
            return 'create_app'
        return 'unknown'
    
    def _collect_features(self, entities: Dict[str, float]) -> Set[str]:
        """Collect features from detected entities."""
        features = set()
        for entity_name in entities:
            if entity_name in ENTITY_DEFINITIONS:
                features.update(ENTITY_DEFINITIONS[entity_name]['features'])
        return features
    
    def _print_debug(self, percept: SemanticPercept):
        """Print debug info."""
        print(f"\n{'='*60}")
        print(f"Input: {percept.raw_input}")
        print(f"Tokens: {percept.tokens}")
        print(f"Intent: {percept.intent}")
        print(f"\nEntities detected:")
        for entity, conf in sorted(percept.entities.items(), key=lambda x: -x[1]):
            bar = "█" * int(conf * 20)
            print(f"  {entity:12} {bar} ({conf:.2f})")
            if entity in percept.attention_details:
                top = percept.attention_details[entity][:3]
                print(f"               └─ attended to: {', '.join(f'{w}({s:.2f})' for w,s in top)}")
        print(f"\nFeatures: {percept.features}")


# ============================================================================
# APP FORGE BRIDGE
# ============================================================================

def perceive_for_app_forge(description: str) -> Dict[str, Any]:
    """
    Bridge function for App Forge integration.
    
    Returns a dict compatible with App Forge's expected format:
    {
        'entities': {'recipe': 0.95, 'ingredient': 0.8},
        'features': {'database', 'crud', 'search'},
        'intent': 'create_app',
        'confidence': 0.9
    }
    """
    engine = GloVeAttentionEngine()
    percept = engine.perceive(description)
    
    return {
        'entities': percept.entities,
        'features': list(percept.features),
        'intent': percept.intent,
        'confidence': max(percept.entities.values()) if percept.entities else 0.0,
        'tokens': percept.tokens
    }


def enhance_template_matching(description: str, template_scores: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Use semantic understanding to re-rank template matches.
    
    Called from App Forge's template_registry.py to improve matching.
    """
    percept = GloVeAttentionEngine().perceive(description)
    
    # Map entities to likely templates
    entity_to_template = {
        'recipe': 'collection',
        'todo': 'todo_list',
        'expense': 'collection',
        'workout': 'collection',
        'event': 'collection',
        'note': 'collection',
        'bookmark': 'collection',
        'contact': 'collection',
        'photo': 'collection',
        'movie': 'collection',
        'music': 'collection',
        'flashcard': 'quiz_app',
        'game': 'game',
        'habit': 'collection',
    }
    
    # Boost templates that match detected entities
    boosted_scores = []
    for template_id, score in template_scores:
        boost = 0.0
        for entity, conf in percept.entities.items():
            if entity in entity_to_template:
                expected_template = entity_to_template[entity]
                if expected_template in template_id.lower():
                    boost += conf * 0.2  # 20% boost per matching entity
        
        boosted_scores.append((template_id, score + boost))
    
    boosted_scores.sort(key=lambda x: -x[1])
    return boosted_scores


# ============================================================================
# DEMO AND TESTING
# ============================================================================

def demo():
    """Demonstrate the GloVe attention engine."""
    print(f"Vocabulary size: {vocabulary_size()} words")
    print(f"Entity definitions: {len(ENTITY_DEFINITIONS)}")
    
    engine = GloVeAttentionEngine(verbose=True)
    
    test_inputs = [
        # Standard inputs
        "a recipe collection app with ingredients",
        "todo list with categories and due dates",
        "expense tracker with budget goals",
        
        # Novel phrasing (would fail with regex)
        "I want to keep track of grandma's secret pasta dishes",
        "something to organize my workout routines at the gym",
        "help me remember what movies I've watched",
        "a way to study for my exams with cards",
        
        # Mixed/ambiguous
        "meal planning with grocery budget tracking",
        "fitness journal with progress photos",
        "family recipe collection that grandma would love",
    ]
    
    print("\n" + "="*60)
    print("GLOVE ATTENTION PERCEPTION DEMO")
    print("="*60)
    
    for text in test_inputs:
        engine.perceive(text)
    
    # Test App Forge bridge
    print("\n" + "="*60)
    print("APP FORGE BRIDGE TEST")
    print("="*60)
    
    result = perceive_for_app_forge("I want something to catalog my grandmother's traditional Italian cuisine")
    print(f"\nResult: {result}")


def benchmark():
    """Benchmark against expected results."""
    engine = GloVeAttentionEngine()
    
    test_cases = [
        # (input, expected_entities, description)
        ("recipe app with ingredients", {'recipe'}, "Standard recipe"),
        ("todo list with categories", {'todo'}, "Standard todo"),
        ("expense tracker with budget", {'expense'}, "Standard expense"),
        ("grandma's secret pasta dishes", {'recipe'}, "Novel: grandma's recipes"),
        ("organize workout routines", {'workout'}, "Novel: workout"),
        ("remember movies watched", {'movie'}, "Novel: movies"),
        ("study with flashcards", {'flashcard'}, "Novel: flashcards"),
        ("meal planning budget", {'recipe', 'expense'}, "Mixed: meal + budget"),
        ("fitness journal photos", {'workout', 'photo'}, "Mixed: fitness + photo"),
        ("track daily habits", {'habit'}, "Habit tracking"),
    ]
    
    print("\n" + "="*60)
    print("BENCHMARK RESULTS")
    print("="*60)
    
    passed = 0
    for text, expected, desc in test_cases:
        result = engine.perceive(text)
        detected = set(result.entities.keys())
        
        # Pass if we detected at least one expected entity
        hit = bool(expected & detected)
        passed += hit
        
        status = "✓" if hit else "✗"
        print(f"[{status}] {desc}")
        print(f"    Input: {text}")
        print(f"    Expected: {expected}")
        print(f"    Detected: {detected}")
        print()
    
    accuracy = passed / len(test_cases) * 100
    print(f"Accuracy: {passed}/{len(test_cases)} ({accuracy:.0f}%)")
    return accuracy


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'benchmark':
        benchmark()
    else:
        demo()
        benchmark()
