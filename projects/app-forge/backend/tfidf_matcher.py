"""TF-IDF Matcher for App Forge.

Pure Python implementation of TF-IDF (Term Frequency-Inverse Document Frequency)
with cosine similarity for semantic-ish matching without AI/ML dependencies.

How it works:
1. Each template becomes a "document" (its name + tags + keywords)
2. User input is another "document"
3. We convert both to TF-IDF vectors and measure cosine similarity
4. Higher similarity = better match

Bonus features:
- Synonym expansion: "colored" → {"colored", "colour", "hue", "tint"}
- Stemming-lite: strips common suffixes
- Compound word splitting: "reactiontime" → "reaction time"

This is 1970s search engine tech, but still beats pure regex for fuzzy matching.
"""

import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set, Optional

# =====================================================================
# Synonym Dictionary (Thesaurus-lite)
# =====================================================================
# Maps words to sets of related words. Symmetric - if A→B, then B→A.

SYNONYMS: Dict[str, Set[str]] = {
    # Colors
    "color": {"colour", "hue", "tint", "shade", "colored", "colorful"},
    "red": {"crimson", "scarlet", "ruby"},
    "blue": {"azure", "navy", "cobalt"},
    "green": {"emerald", "lime", "olive"},
    
    # Game mechanics
    "tile": {"cell", "square", "block", "piece", "box"},
    "grid": {"board", "matrix", "table", "cells"},
    "click": {"tap", "press", "hit", "touch"},
    "fast": {"quick", "rapid", "speed", "speedy"},
    "reaction": {"reflex", "response", "reflexes"},
    "distractor": {"decoy", "fake", "wrong", "false", "incorrect"},
    "target": {"goal", "objective", "correct", "right"},
    
    # App types
    "recipe": {"cooking", "cook", "meal", "dish", "food"},
    "task": {"todo", "to-do", "chore", "item"},
    "note": {"memo", "jot", "record"},
    "track": {"log", "record", "monitor", "follow"},
    
    # Actions
    "add": {"create", "new", "insert", "make"},
    "delete": {"remove", "erase", "trash"},
    "edit": {"modify", "change", "update", "alter"},
    "save": {"store", "keep", "persist"},
    "show": {"display", "view", "see", "present"},
    
    # Difficulty
    "hard": {"difficult", "tough", "challenging"},
    "easy": {"simple", "basic", "beginner"},
    "level": {"stage", "difficulty", "tier"},
    
    # Numbers
    "number": {"digit", "numeral", "count"},
    "random": {"random", "arbitrary", "shuffled", "mixed"},
}


def _build_symmetric_synonyms() -> Dict[str, Set[str]]:
    """Make synonym lookup symmetric (if A→B, then B→A)."""
    symmetric: Dict[str, Set[str]] = defaultdict(set)
    
    for key, values in SYNONYMS.items():
        # Add all values as synonyms of key
        symmetric[key].update(values)
        # Add key as synonym of each value
        for v in values:
            symmetric[v].add(key)
            # Also add all other values
            symmetric[v].update(values - {v})
    
    return dict(symmetric)


SYM_SYNONYMS = _build_symmetric_synonyms()


def expand_synonyms(word: str) -> Set[str]:
    """Expand a word to include all its synonyms."""
    word = word.lower()
    result = {word}
    if word in SYM_SYNONYMS:
        result.update(SYM_SYNONYMS[word])
    return result


# =====================================================================
# Text Preprocessing
# =====================================================================

# Common suffixes to strip (poor man's stemmer)
SUFFIX_RULES = [
    (r"ing$", ""),      # running → runn
    (r"ed$", ""),       # colored → color
    (r"'s$", ""),       # player's → player
    (r"s$", ""),        # tiles → tile
    (r"ly$", ""),       # quickly → quick
    (r"tion$", "t"),    # reaction → react
    (r"ness$", ""),     # darkness → dark
]


def stem(word: str) -> str:
    """Simple suffix stripping (not a real stemmer, but helps)."""
    if len(word) <= 3:
        return word
    for pattern, repl in SUFFIX_RULES:
        new = re.sub(pattern, repl, word)
        if new != word and len(new) >= 3:
            return new
    return word


def tokenize(text: str) -> List[str]:
    """Convert text to lowercase tokens, splitting on non-alphanumeric."""
    # Split camelCase and compound words
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    # Replace non-alpha with space
    text = re.sub(r"[^a-zA-Z0-9]", " ", text.lower())
    # Split and filter
    tokens = [t.strip() for t in text.split() if len(t.strip()) >= 2]
    return tokens


def preprocess(text: str, expand_syns: bool = True) -> List[str]:
    """Full preprocessing: tokenize, stem, optionally expand synonyms."""
    tokens = tokenize(text)
    stemmed = [stem(t) for t in tokens]
    
    if expand_syns:
        expanded = []
        for t in stemmed:
            expanded.append(t)
            # Add synonyms of original (unstemmed) token
            for tok in tokens:
                for syn in expand_synonyms(tok):
                    expanded.append(stem(syn))
        return list(set(expanded))  # Dedupe
    
    return stemmed


# =====================================================================
# TF-IDF Engine
# =====================================================================

class TFIDFMatcher:
    """TF-IDF based document matcher."""
    
    def __init__(self):
        self.documents: Dict[str, List[str]] = {}  # doc_id → tokens
        self.idf: Dict[str, float] = {}            # term → IDF score
        self.tfidf_vectors: Dict[str, Dict[str, float]] = {}  # doc_id → {term: tfidf}
        self.vocab: Set[str] = set()
    
    def add_document(self, doc_id: str, text: str) -> None:
        """Add a document to the corpus."""
        tokens = preprocess(text, expand_syns=True)
        self.documents[doc_id] = tokens
        self.vocab.update(tokens)
    
    def build_index(self) -> None:
        """Compute IDF scores and TF-IDF vectors after all docs are added."""
        n_docs = len(self.documents)
        if n_docs == 0:
            return
        
        # Document frequency for each term
        df: Dict[str, int] = defaultdict(int)
        for tokens in self.documents.values():
            seen = set(tokens)
            for term in seen:
                df[term] += 1
        
        # IDF = log(N / df) with smoothing
        for term in self.vocab:
            self.idf[term] = math.log((n_docs + 1) / (df.get(term, 0) + 1)) + 1
        
        # TF-IDF vectors for each document
        for doc_id, tokens in self.documents.items():
            tf = Counter(tokens)
            max_tf = max(tf.values()) if tf else 1
            
            vec: Dict[str, float] = {}
            for term, count in tf.items():
                # Normalized TF * IDF
                vec[term] = (0.5 + 0.5 * count / max_tf) * self.idf.get(term, 1)
            
            self.tfidf_vectors[doc_id] = vec
    
    def query_vector(self, text: str) -> Dict[str, float]:
        """Convert query text to TF-IDF vector using corpus IDF."""
        tokens = preprocess(text, expand_syns=True)
        tf = Counter(tokens)
        max_tf = max(tf.values()) if tf else 1
        
        vec: Dict[str, float] = {}
        for term, count in tf.items():
            idf = self.idf.get(term, 1.0)  # Default IDF for unseen terms
            vec[term] = (0.5 + 0.5 * count / max_tf) * idf
        
        return vec
    
    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Compute cosine similarity between two sparse vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        # Dot product
        common = set(vec1.keys()) & set(vec2.keys())
        dot = sum(vec1[k] * vec2[k] for k in common)
        
        # Magnitudes
        mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot / (mag1 * mag2)
    
    def match(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find top-k documents matching the query."""
        query_vec = self.query_vector(query)
        
        scores = []
        for doc_id, doc_vec in self.tfidf_vectors.items():
            sim = self.cosine_similarity(query_vec, doc_vec)
            scores.append((doc_id, sim))
        
        # Sort by similarity descending
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]
    
    def explain_match(self, query: str, doc_id: str) -> Dict[str, float]:
        """Show which terms contributed to the match."""
        query_vec = self.query_vector(query)
        doc_vec = self.tfidf_vectors.get(doc_id, {})
        
        common = set(query_vec.keys()) & set(doc_vec.keys())
        contributions = {
            term: query_vec[term] * doc_vec[term]
            for term in common
        }
        return dict(sorted(contributions.items(), key=lambda x: -x[1]))


# =====================================================================
# BM25 Engine (Okapi BM25 - improved TF-IDF)
# =====================================================================
# BM25 improves on TF-IDF by:
# 1. Using a saturation function for TF (diminishing returns for repeated terms)
# 2. Normalizing by document length (short docs aren't penalized)
# 3. Tunable parameters k1 (term saturation) and b (length normalization)

class BM25Matcher:
    """BM25 (Best Match 25) ranking function."""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Term frequency saturation parameter (1.2-2.0 typical)
            b: Document length normalization (0=no normalization, 1=full)
        """
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, List[str]] = {}  # doc_id → tokens
        self.doc_lengths: Dict[str, int] = {}      # doc_id → token count
        self.avg_doc_length: float = 0.0
        self.idf: Dict[str, float] = {}            # term → IDF
        self.doc_term_freqs: Dict[str, Counter] = {}  # doc_id → term frequencies
    
    def add_document(self, doc_id: str, text: str) -> None:
        """Add a document to the corpus."""
        tokens = preprocess(text, expand_syns=True)
        self.documents[doc_id] = tokens
        self.doc_lengths[doc_id] = len(tokens)
        self.doc_term_freqs[doc_id] = Counter(tokens)
    
    def build_index(self) -> None:
        """Compute IDF scores after all docs are added."""
        n_docs = len(self.documents)
        if n_docs == 0:
            return
        
        # Average document length
        self.avg_doc_length = sum(self.doc_lengths.values()) / n_docs
        
        # Document frequency for each term
        df: Dict[str, int] = defaultdict(int)
        for tokens in self.documents.values():
            seen = set(tokens)
            for term in seen:
                df[term] += 1
        
        # IDF with Robertson-Sparck Jones formula
        # IDF = log((N - df + 0.5) / (df + 0.5))
        for term, doc_freq in df.items():
            self.idf[term] = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def score(self, query: str, doc_id: str) -> float:
        """Compute BM25 score for a query against a document."""
        query_tokens = preprocess(query, expand_syns=True)
        doc_tf = self.doc_term_freqs.get(doc_id, Counter())
        doc_len = self.doc_lengths.get(doc_id, 0)
        
        if doc_len == 0 or self.avg_doc_length == 0:
            return 0.0
        
        score = 0.0
        for term in query_tokens:
            if term not in doc_tf:
                continue
            
            tf = doc_tf[term]
            idf = self.idf.get(term, 0)
            
            # BM25 formula
            # score += IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl/avgdl))
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
            score += idf * (numerator / denominator)
        
        return score
    
    def match(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find top-k documents matching the query using BM25."""
        scores = []
        for doc_id in self.documents:
            s = self.score(query, doc_id)
            scores.append((doc_id, s))
        
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]


# =====================================================================
# Jaccard Similarity on N-grams
# =====================================================================
# Jaccard is great for catching partial matches:
# - "colored" vs "multicolored" share many character n-grams
# - Handles typos and word variations well

def ngrams(text: str, n: int = 3) -> Set[str]:
    """Extract character n-grams from text."""
    text = text.lower().replace(" ", "_")  # Use _ for word boundaries
    if len(text) < n:
        return {text}
    return {text[i:i+n] for i in range(len(text) - n + 1)}


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Compute Jaccard similarity: |A ∩ B| / |A ∪ B|."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def dice_coefficient(set1: Set[str], set2: Set[str]) -> float:
    """Compute Dice coefficient: 2 * |A ∩ B| / (|A| + |B|).
    
    Similar to Jaccard but gives more weight to shared elements.
    """
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    return 2 * intersection / (len(set1) + len(set2))


class JaccardMatcher:
    """N-gram based Jaccard similarity matcher."""
    
    def __init__(self, n: int = 3):
        """
        Args:
            n: N-gram size (2=bigrams, 3=trigrams, etc.)
        """
        self.n = n
        self.documents: Dict[str, str] = {}       # doc_id → raw text
        self.doc_ngrams: Dict[str, Set[str]] = {} # doc_id → n-gram set
    
    def add_document(self, doc_id: str, text: str) -> None:
        """Add a document to the corpus."""
        self.documents[doc_id] = text.lower()
        self.doc_ngrams[doc_id] = ngrams(text, self.n)
    
    def build_index(self) -> None:
        """No index needed for Jaccard (computed on-the-fly)."""
        pass
    
    def match(self, query: str, top_k: int = 5, use_dice: bool = False) -> List[Tuple[str, float]]:
        """Find top-k documents using Jaccard or Dice similarity."""
        query_ngrams = ngrams(query, self.n)
        
        sim_func = dice_coefficient if use_dice else jaccard_similarity
        
        scores = []
        for doc_id, doc_ngs in self.doc_ngrams.items():
            sim = sim_func(query_ngrams, doc_ngs)
            scores.append((doc_id, sim))
        
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]
    
    def explain_match(self, query: str, doc_id: str) -> Dict[str, any]:
        """Show which n-grams matched."""
        query_ngs = ngrams(query, self.n)
        doc_ngs = self.doc_ngrams.get(doc_id, set())
        
        shared = query_ngs & doc_ngs
        return {
            "query_ngrams": len(query_ngs),
            "doc_ngrams": len(doc_ngs),
            "shared": len(shared),
            "jaccard": jaccard_similarity(query_ngs, doc_ngs),
            "shared_examples": list(shared)[:10],
        }


# =====================================================================
# Combined Matcher (TF-IDF + BM25 + Jaccard)
# =====================================================================
# Ensemble approach: combine scores from multiple methods

class CombinedMatcher:
    """Combines TF-IDF, BM25, and Jaccard for robust matching."""
    
    def __init__(self, 
                 tfidf_weight: float = 0.4,
                 bm25_weight: float = 0.4,
                 jaccard_weight: float = 0.2):
        """
        Args:
            tfidf_weight: Weight for TF-IDF cosine similarity
            bm25_weight: Weight for BM25 score
            jaccard_weight: Weight for Jaccard n-gram similarity
        """
        self.weights = {
            'tfidf': tfidf_weight,
            'bm25': bm25_weight,
            'jaccard': jaccard_weight
        }
        self.tfidf = TFIDFMatcher()
        self.bm25 = BM25Matcher()
        self.jaccard = JaccardMatcher(n=3)
    
    def add_document(self, doc_id: str, text: str) -> None:
        """Add a document to all matchers."""
        self.tfidf.add_document(doc_id, text)
        self.bm25.add_document(doc_id, text)
        self.jaccard.add_document(doc_id, text)
    
    def build_index(self) -> None:
        """Build indices for all matchers."""
        self.tfidf.build_index()
        self.bm25.build_index()
        self.jaccard.build_index()
    
    def match(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find top-k documents using combined scoring."""
        # Get scores from each method
        tfidf_scores = {doc_id: score for doc_id, score in self.tfidf.match(query, top_k=100)}
        bm25_scores = {doc_id: score for doc_id, score in self.bm25.match(query, top_k=100)}
        jaccard_scores = {doc_id: score for doc_id, score in self.jaccard.match(query, top_k=100)}
        
        # Normalize scores to 0-1 range
        def normalize(scores: Dict[str, float]) -> Dict[str, float]:
            if not scores:
                return {}
            max_s = max(scores.values())
            min_s = min(scores.values())
            if max_s == min_s:
                return {k: 1.0 for k in scores}
            return {k: (v - min_s) / (max_s - min_s) for k, v in scores.items()}
        
        tfidf_norm = normalize(tfidf_scores)
        bm25_norm = normalize(bm25_scores)
        jaccard_norm = normalize(jaccard_scores)
        
        # Combine scores
        all_docs = set(tfidf_scores.keys()) | set(bm25_scores.keys()) | set(jaccard_scores.keys())
        combined = []
        
        for doc_id in all_docs:
            score = (
                self.weights['tfidf'] * tfidf_norm.get(doc_id, 0) +
                self.weights['bm25'] * bm25_norm.get(doc_id, 0) +
                self.weights['jaccard'] * jaccard_norm.get(doc_id, 0)
            )
            combined.append((doc_id, score))
        
        combined.sort(key=lambda x: -x[1])
        return combined[:top_k]
    
    def explain_match(self, query: str, doc_id: str) -> Dict[str, any]:
        """Detailed breakdown of why a document matched."""
        tfidf_results = dict(self.tfidf.match(query, top_k=100))
        bm25_results = dict(self.bm25.match(query, top_k=100))
        jaccard_results = dict(self.jaccard.match(query, top_k=100))
        
        return {
            "tfidf_score": tfidf_results.get(doc_id, 0),
            "bm25_score": bm25_results.get(doc_id, 0),
            "jaccard_score": jaccard_results.get(doc_id, 0),
            "tfidf_terms": self.tfidf.explain_match(query, doc_id),
            "jaccard_detail": self.jaccard.explain_match(query, doc_id),
        }


# =====================================================================
# Template Integration
# =====================================================================

# Global matcher instances
_matcher: Optional[TFIDFMatcher] = None
_bm25_matcher: Optional[BM25Matcher] = None
_combined_matcher: Optional[CombinedMatcher] = None


def get_matcher() -> TFIDFMatcher:
    """Get or create the global TF-IDF matcher, populated with templates."""
    global _matcher
    if _matcher is None:
        _matcher = TFIDFMatcher()
        _load_templates(_matcher)
        _matcher.build_index()
    return _matcher


def get_bm25_matcher() -> BM25Matcher:
    """Get or create the global BM25 matcher, populated with templates."""
    global _bm25_matcher
    if _bm25_matcher is None:
        _bm25_matcher = BM25Matcher()
        _load_templates(_bm25_matcher)
        _bm25_matcher.build_index()
    return _bm25_matcher


def get_combined_matcher() -> CombinedMatcher:
    """Get or create the global combined matcher."""
    global _combined_matcher
    if _combined_matcher is None:
        _combined_matcher = CombinedMatcher()
        _load_templates(_combined_matcher)
        _combined_matcher.build_index()
    return _combined_matcher


def _load_templates(matcher: TFIDFMatcher) -> None:
    """Load templates from template_registry into the matcher."""
    try:
        from template_registry import TEMPLATE_REGISTRY
        
        for template in TEMPLATE_REGISTRY:
            # Build document text from template metadata
            doc_parts = [
                template.name,
                " ".join(template.tags),
                template.id.replace("_", " "),
            ]
            # Add boosted features as extra weight
            doc_parts.extend(template.boosted)
            
            doc_text = " ".join(doc_parts)
            matcher.add_document(template.id, doc_text)
            
    except ImportError:
        # Fallback if template_registry not available
        pass


def tfidf_match(description: str, top_k: int = 5) -> List[Tuple[str, float]]:
    """Match a description using TF-IDF. Returns [(template_id, score), ...]."""
    matcher = get_matcher()
    return matcher.match(description, top_k)


def tfidf_explain(description: str, template_id: str) -> Dict[str, float]:
    """Explain why a template matched a description."""
    matcher = get_matcher()
    return matcher.explain_match(description, template_id)


def bm25_match(description: str, top_k: int = 5) -> List[Tuple[str, float]]:
    """Match a description using BM25. Returns [(template_id, score), ...]."""
    matcher = get_bm25_matcher()
    return matcher.match(description, top_k)


def combined_match(description: str, top_k: int = 5) -> List[Tuple[str, float]]:
    """Match using TF-IDF + BM25 + Jaccard ensemble. Returns [(template_id, score), ...]."""
    matcher = get_combined_matcher()
    return matcher.match(description, top_k)


def combined_explain(description: str, template_id: str) -> Dict[str, any]:
    """Detailed explanation of combined match scores."""
    matcher = get_combined_matcher()
    return matcher.explain_match(description, template_id)


def reset_matcher() -> None:
    """Reset all global matchers (useful after adding new templates)."""
    global _matcher, _bm25_matcher, _combined_matcher
    _matcher = None
    _bm25_matcher = None
    _combined_matcher = None


# =====================================================================
# Debugging / Testing
# =====================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  TF-IDF + BM25 + Jaccard Matcher Test")
    print("=" * 60)
    
    # Test synonym expansion
    print("\n[Synonym Expansion]")
    print("  'colored':", expand_synonyms("colored"))
    print("  'tile':", expand_synonyms("tile"))
    
    # Test n-grams
    print("\n[N-gram Extraction]")
    test_word = "colored"
    print(f"  '{test_word}' trigrams:", ngrams(test_word, 3))
    
    # Test Jaccard similarity between similar words
    print("\n[Jaccard Similarity]")
    pairs = [
        ("colored", "multicolored"),
        ("reaction", "react"),
        ("puzzle", "puzzles"),
        ("game", "gaming"),
    ]
    for w1, w2 in pairs:
        sim = jaccard_similarity(ngrams(w1, 3), ngrams(w2, 3))
        print(f"  '{w1}' vs '{w2}': {sim:.3f}")
    
    # Test all three matchers
    print("\n[Matcher Comparison]")
    test_queries = [
        "reaction time game with different colored tiles",
        "quick reflex test",
        "sliding number puzzle 3x3",
        "memory matching card game",
        "a recipe app with ingredients",
    ]
    
    for query in test_queries:
        print(f"\n  Query: '{query}'")
        
        tfidf_results = tfidf_match(query, top_k=3)
        bm25_results = bm25_match(query, top_k=3)
        combined_results = combined_match(query, top_k=3)
        
        print(f"    TF-IDF:   {[(tid, f'{s:.3f}') for tid, s in tfidf_results]}")
        print(f"    BM25:     {[(tid, f'{s:.3f}') for tid, s in bm25_results]}")
        print(f"    Combined: {[(tid, f'{s:.3f}') for tid, s in combined_results]}")
    
    # Show detailed explanation for one query
    print("\n[Detailed Explanation]")
    query = "reaction time game with different colored tiles"
    best_id = combined_match(query, top_k=1)[0][0]
    explanation = combined_explain(query, best_id)
    print(f"  Query: '{query}'")
    print(f"  Best match: {best_id}")
    print(f"  TF-IDF score: {explanation['tfidf_score']:.3f}")
    print(f"  BM25 score: {explanation['bm25_score']:.3f}")
    print(f"  Jaccard score: {explanation['jaccard_score']:.3f}")
    print(f"  Top TF-IDF terms: {list(explanation['tfidf_terms'].items())[:5]}")
