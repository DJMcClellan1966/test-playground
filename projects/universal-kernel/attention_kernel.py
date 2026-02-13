"""
Attention-Enhanced Kernel

Implements self-attention from "Attention Is All You Need" (Vaswani et al., 2017)
WITHOUT neural network training - using pre-computed embeddings and pure matrix math.

This bridges the gap between:
- Regex (fast, brittle, no understanding)
- LLMs (slow, expensive, but "understands")

Key insight: Attention is just matrix multiplication + softmax.
We don't need to TRAIN attention - we can USE it with existing word vectors.
"""

import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
import json

# ============================================================================
# SIMPLE WORD EMBEDDINGS (no external dependencies)
# These are learned co-occurrence patterns - "words that appear together"
# In production, you'd use word2vec/GloVe/fasttext
# ============================================================================

# Semantic clusters - words that should attend to each other
SEMANTIC_CLUSTERS = {
    'food': ['recipe', 'ingredient', 'meal', 'dish', 'cook', 'kitchen', 'food', 
             'pasta', 'sauce', 'spice', 'cuisine', 'breakfast', 'lunch', 'dinner',
             'bake', 'fry', 'grill', 'nutrition', 'calorie', 'serving'],
    
    'storage': ['save', 'store', 'keep', 'collection', 'organize', 'manage',
                'track', 'record', 'log', 'list', 'catalog', 'archive', 'library'],
    
    'fitness': ['workout', 'exercise', 'gym', 'fitness', 'training', 'rep', 'set',
                'weight', 'cardio', 'muscle', 'routine', 'health', 'body'],
    
    'finance': ['expense', 'budget', 'money', 'cost', 'payment', 'income', 'salary',
                'transaction', 'account', 'bank', 'saving', 'spending', 'financial'],
    
    'task': ['todo', 'task', 'item', 'checklist', 'reminder', 'deadline', 'due',
             'priority', 'project', 'goal', 'milestone', 'progress'],
    
    'time': ['schedule', 'calendar', 'event', 'appointment', 'date', 'time',
             'daily', 'weekly', 'monthly', 'recurring', 'reminder'],
    
    'media': ['photo', 'image', 'video', 'movie', 'music', 'audio', 'media',
              'gallery', 'album', 'playlist', 'stream', 'watch', 'listen'],
    
    'social': ['user', 'profile', 'friend', 'follow', 'share', 'comment', 'like',
               'post', 'message', 'chat', 'community', 'group'],
    
    'learning': ['study', 'learn', 'flashcard', 'quiz', 'test', 'practice',
                 'knowledge', 'memory', 'review', 'education', 'course', 'lesson'],
    
    'game': ['game', 'play', 'score', 'level', 'win', 'lose', 'player',
             'turn', 'move', 'round', 'match', 'compete', 'challenge'],
}

# Build word-to-cluster mapping
WORD_TO_CLUSTERS: Dict[str, Set[str]] = defaultdict(set)
for cluster, words in SEMANTIC_CLUSTERS.items():
    for word in words:
        WORD_TO_CLUSTERS[word].add(cluster)


def simple_embedding(word: str, dim: int = 64) -> List[float]:
    """
    Create a simple embedding based on semantic cluster membership.
    
    Each dimension corresponds to a semantic cluster.
    Words in the same cluster will have similar vectors.
    """
    word = word.lower()
    clusters = list(SEMANTIC_CLUSTERS.keys())
    
    # Pad or use first 'dim' clusters
    embedding = [0.0] * dim
    
    # Set dimensions based on cluster membership
    for i, cluster in enumerate(clusters[:dim]):
        if word in SEMANTIC_CLUSTERS[cluster]:
            embedding[i] = 1.0
        # Partial match for word stems
        elif any(word.startswith(w[:4]) or w.startswith(word[:4]) 
                 for w in SEMANTIC_CLUSTERS[cluster] if len(w) >= 4 and len(word) >= 4):
            embedding[i] = 0.5
    
    # If no cluster match, use hash-based embedding (fallback)
    if sum(embedding) == 0:
        # Distribute across dimensions based on character patterns
        for j, char in enumerate(word):
            embedding[(ord(char) + j) % dim] += 0.1
    
    # Normalize
    magnitude = math.sqrt(sum(x*x for x in embedding)) or 1.0
    return [x / magnitude for x in embedding]


# ============================================================================
# ATTENTION MECHANISM (from "Attention Is All You Need")
# ============================================================================

def dot_product(a: List[float], b: List[float]) -> float:
    """Compute dot product of two vectors."""
    return sum(x * y for x, y in zip(a, b))


def softmax(scores: List[float], temperature: float = 1.0) -> List[float]:
    """
    Softmax function - converts scores to probabilities.
    Temperature controls sharpness (lower = more peaked).
    """
    # Subtract max for numerical stability
    max_score = max(scores) if scores else 0
    exp_scores = [math.exp((s - max_score) / temperature) for s in scores]
    total = sum(exp_scores) or 1.0
    return [e / total for e in exp_scores]


def scaled_dot_product_attention(
    query: List[float],
    keys: List[List[float]],
    values: List[str],
    d_k: Optional[int] = None
) -> Tuple[str, List[Tuple[str, float]]]:
    """
    Core attention mechanism from the Transformer paper.
    
    Attention(Q, K, V) = softmax(QK^T / √d_k) × V
    
    Args:
        query: What we're looking for (embedding)
        keys: What we have to search (embeddings)
        values: The actual content (words)
        d_k: Key dimension for scaling
    
    Returns:
        Tuple of (best_match, all_matches_with_weights)
    """
    if not keys:
        return "", []
    
    d_k = d_k or len(query)
    scale = math.sqrt(d_k)
    
    # Compute attention scores: QK^T / √d_k
    scores = [dot_product(query, key) / scale for key in keys]
    
    # Apply softmax to get attention weights
    weights = softmax(scores)
    
    # Pair values with weights
    weighted_values = list(zip(values, weights))
    weighted_values.sort(key=lambda x: x[1], reverse=True)
    
    return weighted_values[0][0] if weighted_values else "", weighted_values


def self_attention(tokens: List[str]) -> Dict[str, List[Tuple[str, float]]]:
    """
    Self-attention: each token attends to all other tokens.
    
    This lets us understand which words relate to which:
    "grandmother's secret pasta recipes" →
        "recipes" attends to: "pasta" (0.4), "grandmother's" (0.2), "secret" (0.2)
    
    Returns a dict mapping each token to its attention weights over other tokens.
    """
    if not tokens:
        return {}
    
    # Get embeddings for all tokens
    embeddings = [simple_embedding(t) for t in tokens]
    
    attention_map = {}
    for i, token in enumerate(tokens):
        query = embeddings[i]
        # Attend to all other tokens (excluding self)
        other_indices = [j for j in range(len(tokens)) if j != i]
        keys = [embeddings[j] for j in other_indices]
        values = [tokens[j] for j in other_indices]
        
        if keys:
            _, weighted = scaled_dot_product_attention(query, keys, values)
            attention_map[token] = weighted
    
    return attention_map


# ============================================================================
# ATTENTION-ENHANCED PERCEPTION
# ============================================================================

@dataclass
class AttentionPercept:
    """Enhanced percept using attention."""
    raw_input: str
    tokens: List[str]
    entities: Dict[str, float]  # entity -> confidence
    intent: str
    attention_map: Dict[str, List[Tuple[str, float]]]
    inferred_features: Set[str]


class AttentionPerceptionEngine:
    """
    Perception engine that uses attention instead of regex.
    
    Process:
    1. Tokenize input
    2. Compute self-attention (which words relate?)
    3. Query attention to find entities (what concepts are present?)
    4. Aggregate to features (what should the app have?)
    """
    
    # Canonical entities we want to detect
    ENTITY_QUERIES = {
        'recipe': ['recipe', 'dish', 'meal', 'food', 'cuisine', 'ingredient'],
        'todo': ['todo', 'task', 'item', 'reminder', 'checklist'],
        'expense': ['expense', 'budget', 'money', 'cost', 'payment', 'spending'],
        'workout': ['workout', 'exercise', 'fitness', 'gym', 'training'],
        'event': ['event', 'calendar', 'schedule', 'appointment'],
        'note': ['note', 'memo', 'journal', 'diary', 'entry'],
        'bookmark': ['bookmark', 'link', 'url', 'website', 'favorite'],
        'contact': ['contact', 'person', 'friend', 'user', 'profile'],
        'photo': ['photo', 'image', 'picture', 'gallery', 'album'],
        'movie': ['movie', 'film', 'video', 'show', 'watch'],
        'music': ['music', 'song', 'playlist', 'audio', 'listen'],
        'flashcard': ['flashcard', 'card', 'study', 'learn', 'quiz'],
        'game': ['game', 'play', 'score', 'level', 'player'],
    }
    
    # Feature inference based on entity clusters
    ENTITY_TO_FEATURES = {
        'recipe': {'database', 'crud', 'search'},
        'todo': {'database', 'crud', 'checkbox'},
        'expense': {'database', 'crud', 'charts'},
        'workout': {'database', 'crud', 'history'},
        'event': {'database', 'crud', 'calendar'},
        'note': {'database', 'crud', 'editor'},
        'bookmark': {'database', 'crud', 'search'},
        'contact': {'database', 'crud', 'search'},
        'photo': {'upload', 'gallery', 'storage'},
        'movie': {'database', 'crud', 'ratings'},
        'music': {'database', 'crud', 'player'},
        'flashcard': {'database', 'crud', 'quiz'},
        'game': {'state', 'interactive', 'score'},
    }
    
    def tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Remove punctuation, lowercase, split on whitespace
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = text.split()
        # Filter very short tokens
        return [t for t in tokens if len(t) > 1]
    
    def perceive(self, text: str) -> AttentionPercept:
        """
        Main perception function using attention.
        """
        tokens = self.tokenize(text)
        
        # Compute self-attention
        attention_map = self_attention(tokens)
        
        # Detect entities using attention to canonical queries
        entities = self._detect_entities(tokens)
        
        # Infer intent
        intent = self._infer_intent(text, entities)
        
        # Infer features from entities
        features = self._infer_features(entities)
        
        return AttentionPercept(
            raw_input=text,
            tokens=tokens,
            entities=entities,
            intent=intent,
            attention_map=attention_map,
            inferred_features=features
        )
    
    def _detect_entities(self, tokens: List[str]) -> Dict[str, float]:
        """
        Detect entities by computing attention from input tokens to entity queries.
        """
        entities = {}
        
        for entity, query_words in self.ENTITY_QUERIES.items():
            # Create query embedding as average of query word embeddings
            query_embeddings = [simple_embedding(w) for w in query_words]
            query = [sum(x) / len(query_embeddings) 
                     for x in zip(*query_embeddings)]
            
            # Compute attention to input tokens
            token_embeddings = [simple_embedding(t) for t in tokens]
            
            if token_embeddings:
                _, weighted = scaled_dot_product_attention(
                    query, token_embeddings, tokens
                )
                
                # Sum weights of tokens that attended strongly
                confidence = sum(w for _, w in weighted if w > 0.1)
                
                # Check for direct matches (boost confidence)
                for token in tokens:
                    if token in query_words or any(
                        token.startswith(qw[:4]) or qw.startswith(token[:4])
                        for qw in query_words if len(qw) >= 4 and len(token) >= 4
                    ):
                        confidence += 0.5
                
                if confidence > 0.2:  # Threshold
                    entities[entity] = min(confidence, 1.0)
        
        return entities
    
    def _infer_intent(self, text: str, entities: Dict[str, float]) -> str:
        """Infer user intent."""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ['search', 'find', 'look for', 'query']):
            return 'query'
        elif any(w in text_lower for w in ['delete', 'remove', 'clear']):
            return 'delete'
        elif any(w in text_lower for w in ['update', 'edit', 'change', 'modify']):
            return 'update'
        elif entities:
            return 'create_app'
        else:
            return 'unknown'
    
    def _infer_features(self, entities: Dict[str, float]) -> Set[str]:
        """Infer app features from detected entities."""
        features = set()
        for entity in entities:
            if entity in self.ENTITY_TO_FEATURES:
                features.update(self.ENTITY_TO_FEATURES[entity])
        return features


# ============================================================================
# DEMO AND TESTING
# ============================================================================

def demo_attention():
    """Demonstrate attention mechanism."""
    engine = AttentionPerceptionEngine()
    
    test_inputs = [
        # Standard - should work with regex too
        "a recipe collection app with ingredients",
        "todo list with categories",
        "expense tracker with budget goals",
        
        # Novel phrasing - regex would fail, attention should work
        "I want to keep track of grandma's secret pasta dishes",
        "something to organize my workout routines at the gym",
        "help me remember what movies I've watched",
        "a way to study for my exams with cards",
        
        # Mixed domains
        "meal planning with grocery budget tracking",
        "fitness journal with progress photos",
    ]
    
    print("=" * 70)
    print("ATTENTION-ENHANCED PERCEPTION DEMO")
    print("=" * 70)
    
    for text in test_inputs:
        print(f"\nInput: {text}")
        print("-" * 50)
        
        result = engine.perceive(text)
        
        print(f"Entities: {dict(sorted(result.entities.items(), key=lambda x: -x[1]))}")
        print(f"Intent: {result.intent}")
        print(f"Features: {result.inferred_features}")
        
        if result.attention_map:
            # Show most interesting attention patterns
            print("Attention highlights:")
            for token, attended in list(result.attention_map.items())[:3]:
                top_3 = attended[:3]
                if top_3:
                    attn_str = ", ".join(f"{w}:{s:.2f}" for w, s in top_3)
                    print(f"  '{token}' → [{attn_str}]")
    
    print("\n" + "=" * 70)
    print("COMPARISON: Novel Input Handling")
    print("=" * 70)
    
    # Test that would fail with regex
    novel = "I want something to catalog my grandmother's traditional Italian cuisine"
    print(f"\nInput: {novel}")
    
    result = engine.perceive(novel)
    print(f"Entities detected: {result.entities}")
    print(f"Features inferred: {result.inferred_features}")
    
    # Show the attention flow
    print("\nAttention flow (how 'cuisine' connects):")
    if 'cuisine' in result.attention_map:
        for word, weight in result.attention_map['cuisine'][:5]:
            bar = "█" * int(weight * 20)
            print(f"  cuisine → {word}: {bar} ({weight:.3f})")


def benchmark_vs_regex():
    """Compare attention-based perception to regex."""
    from agent_loop import PerceptionEngine as RegexEngine
    
    attention_engine = AttentionPerceptionEngine()
    regex_engine = RegexEngine()
    
    # Test cases with expected entities
    test_cases = [
        # (input, expected_entities)
        ("recipe app with ingredients", {"recipe", "ingredient"}),
        ("todo list with categories", {"todo", "category"}),
        ("grandma's secret pasta dishes", {"recipe"}),  # Novel phrasing
        ("organize workout routines", {"workout"}),
        ("remember movies watched", {"movie"}),
        ("study with flashcards", {"flashcard"}),
        ("meal planning budget", {"recipe", "expense"}),  # Mixed
    ]
    
    print("\n" + "=" * 70)
    print("BENCHMARK: Attention vs Regex")
    print("=" * 70)
    
    attention_correct = 0
    regex_correct = 0
    
    for text, expected in test_cases:
        # Attention
        attn_result = attention_engine.perceive(text)
        attn_entities = set(attn_result.entities.keys())
        attn_hit = bool(expected & attn_entities)
        
        # Regex
        regex_result = regex_engine.perceive(text)
        regex_entities = set(regex_result.entities.keys())
        regex_hit = bool(expected & regex_entities)
        
        attention_correct += attn_hit
        regex_correct += regex_hit
        
        status = "✓" if attn_hit else "✗"
        regex_status = "✓" if regex_hit else "✗"
        
        print(f"\n'{text}'")
        print(f"  Expected: {expected}")
        print(f"  Attention [{status}]: {attn_entities}")
        print(f"  Regex    [{regex_status}]: {regex_entities}")
    
    print(f"\n{'='*70}")
    print(f"Attention accuracy: {attention_correct}/{len(test_cases)} ({100*attention_correct/len(test_cases):.0f}%)")
    print(f"Regex accuracy: {regex_correct}/{len(test_cases)} ({100*regex_correct/len(test_cases):.0f}%)")


if __name__ == "__main__":
    demo_attention()
    
    # Only run comparison if regex engine exists
    try:
        benchmark_vs_regex()
    except ImportError:
        print("\n(Skipping regex comparison - agent_loop not available)")
