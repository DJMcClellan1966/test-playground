"""Template Registry (App Store) + Feature Extractor (Feature Store).

This replaces flat regex matching with a scored approach:
 1. Extract structured features from the description
 2. Score every template against those features
 3. Pick the highest-scoring template

Concepts used:
 - Feature Store:  extract_features() pulls structured signals from text
 - App Store:      TEMPLATE_REGISTRY is a searchable catalogue of templates
 - Attention:      score_template() weights features differently per template
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# =====================================================================
# Feature Extractor  (Feature Store)
# =====================================================================
# Extracts structured features from a natural-language description.
# Each feature has a name, value, and confidence (0-1).

@dataclass
class Feature:
    name: str
    value: str          # e.g. "3" for grid_size, "numbers" for tile_content
    confidence: float   # 0.0 - 1.0

    def __repr__(self):
        return f"Feature({self.name}={self.value}, conf={self.confidence:.2f})"


# Extraction rules: (feature_name, pattern, value_extractor, confidence)
# value_extractor: either a static string, or a group index from the regex
FEATURE_RULES: List[Tuple[str, str, object, float]] = [
    # Grid / board games
    ("grid_size",    r"(\d+)\s*[x×]\s*(\d+)",                "group:1", 0.95),
    ("grid_game",    r"grid|board|tile|sliding|slide|swap",   "true",    0.80),
    ("numbered",     r"number|numbered|digit|\bN\b",          "true",    0.75),

    # Game mechanics
    ("sliding",      r"slid(e|ing)|shift|swap\s*(tile|piece|block)",  "true", 0.90),
    ("puzzle",       r"puzzle|solving|solve|brain\s*tease",    "true",   0.80),
    ("matching",     r"match(ing)?|pair|flip|memory",          "true",   0.80),
    ("guessing",     r"guess(ing)?|random\s*number",           "true",   0.85),
    ("trivia",       r"quiz|trivia|question\s*(and|&)\s*answer|flashcard", "true", 0.85),
    ("turn_based",   r"turn|player\s*[12]|two\s*player|vs\b", "true",   0.75),
    ("reaction",     r"reaction|reflex|speed\s*test|quick",    "true",   0.85),
    ("timing",       r"timer|countdown|stopwatch|pomodoro|clock", "true", 0.85),

    # Specific games
    ("tictactoe",    r"tic.?tac.?toe|noughts.*crosses|x.?and.?o", "true", 0.95),
    ("hangman",      r"hangman|word\s*guess",                  "true",   0.95),
    ("snake",        r"snake\s*game",                          "true",   0.90),
    ("wordle",       r"wordle|word\s*puzzle",                  "true",   0.85),

    # Tools
    ("calculator",   r"calculator|calc\b|arithmetic",          "true",   0.90),
    ("converter",    r"converter|convert\s+unit|unit\s+convert|bmi|mortgage", "true", 0.90),

    # Content types
    ("tile_content", r"(number|letter|color|image|emoji|picture)\s*(tile|block|piece|square)?", "group:1", 0.80),
    ("word_based",   r"word|letter|anagram|scrabble|crossword", "true",  0.75),

    # Data apps (not games)
    ("data_app",     r"recipe|cook|todo|task|inventory|product|blog|contact|event|"
                     r"calendar|note|movie|habit|collection|tracker|bookmark|catalog|"
                     r"library|portfolio|budget|expense|journal|diary|grocery|workout|log\b",
                     "true", 0.80),
]


def extract_features(description: str) -> Dict[str, Feature]:
    """Pull structured features from a description."""
    desc = description.lower()
    features: Dict[str, Feature] = {}

    for feat_name, pattern, value_extractor, conf in FEATURE_RULES:
        m = re.search(pattern, desc)
        if m:
            if isinstance(value_extractor, str) and value_extractor.startswith("group:"):
                gnum = int(value_extractor.split(":")[1])
                val = m.group(gnum)
            else:
                val = str(value_extractor)
            # Don't overwrite higher-confidence features
            if feat_name not in features or features[feat_name].confidence < conf:
                features[feat_name] = Feature(feat_name, val, conf)

    return features


# =====================================================================
# Template Registry  (App Store)
# =====================================================================
# Each template declares:
#   - id:          Unique key (maps to generator method)
#   - name:        Human-readable name
#   - tags:        Keywords for basic matching
#   - required:    Features that MUST be present (hard filter)
#   - boosted:     Features that increase score (soft preference)
#   - anti:        Features that decrease score (wrong match)
#   - base_score:  Starting score (specificity — higher = more specific)

@dataclass
class TemplateEntry:
    id: str
    name: str
    tags: List[str] = field(default_factory=list)
    required: List[str] = field(default_factory=list)
    boosted: List[str] = field(default_factory=list)
    anti: List[str] = field(default_factory=list)
    base_score: float = 0.0


TEMPLATE_REGISTRY: List[TemplateEntry] = [
    # --- Specific games (high base_score = more specific) ---
    TemplateEntry(
        id="sliding_puzzle",
        name="Sliding Tile Puzzle",
        tags=["sliding", "puzzle", "tile", "grid", "number", "15-puzzle"],
        required=[],
        boosted=["grid_game", "sliding", "puzzle", "numbered", "grid_size", "tile_content"],
        anti=["matching", "guessing", "trivia", "calculator", "converter", "data_app"],
        base_score=5.0,
    ),
    TemplateEntry(
        id="tictactoe",
        name="Tic Tac Toe",
        tags=["tictactoe", "grid", "turn", "two-player"],
        required=["tictactoe"],
        boosted=["turn_based", "grid_game"],
        anti=["sliding", "matching", "guessing", "data_app"],
        base_score=8.0,
    ),
    TemplateEntry(
        id="memory_game",
        name="Memory Match",
        tags=["memory", "match", "card", "flip", "pairs"],
        required=[],
        boosted=["matching", "grid_game"],
        anti=["sliding", "guessing", "trivia", "numbered", "data_app"],
        base_score=5.0,
    ),
    TemplateEntry(
        id="guess_game",
        name="Guess the Number",
        tags=["guess", "number", "random", "higher-lower"],
        required=[],
        boosted=["guessing", "numbered"],
        anti=["grid_game", "sliding", "matching", "trivia", "data_app"],
        base_score=4.0,
    ),
    TemplateEntry(
        id="quiz",
        name="Quiz / Trivia",
        tags=["quiz", "trivia", "flashcard", "question"],
        required=[],
        boosted=["trivia", "word_based"],
        anti=["grid_game", "sliding", "guessing", "calculator", "data_app"],
        base_score=5.0,
    ),
    TemplateEntry(
        id="hangman",
        name="Hangman",
        tags=["hangman", "word", "guess", "letters"],
        required=["hangman"],
        boosted=["word_based", "guessing"],
        anti=["grid_game", "numbered", "data_app"],
        base_score=8.0,
    ),
    TemplateEntry(
        id="wordle",
        name="Wordle-style Word Puzzle",
        tags=["wordle", "word", "guess", "puzzle"],
        required=["wordle"],
        boosted=["word_based", "puzzle", "guessing"],
        anti=["grid_game", "numbered", "data_app"],
        base_score=8.0,
    ),
    # --- Tools ---
    TemplateEntry(
        id="calculator",
        name="Calculator",
        tags=["calculator", "math", "arithmetic"],
        required=["calculator"],
        boosted=["numbered"],
        anti=["grid_game", "sliding", "matching", "data_app"],
        base_score=8.0,
    ),
    TemplateEntry(
        id="converter",
        name="Unit Converter",
        tags=["converter", "unit", "temperature", "weight", "length"],
        required=["converter"],
        boosted=["numbered"],
        anti=["grid_game", "sliding", "matching", "data_app"],
        base_score=8.0,
    ),
    TemplateEntry(
        id="timer",
        name="Timer / Pomodoro",
        tags=["timer", "countdown", "stopwatch", "pomodoro", "clock"],
        required=["timing"],
        boosted=[],
        anti=["grid_game", "sliding", "matching", "data_app"],
        base_score=7.0,
    ),
    TemplateEntry(
        id="reaction_game",
        name="Reaction Time Game",
        tags=["reaction", "reflex", "speed", "click"],
        required=[],
        boosted=["reaction"],
        anti=["grid_game", "sliding", "puzzle", "matching", "trivia", "guessing",
              "numbered", "calculator", "converter", "data_app"],
        base_score=1.0,  # Low: only pick if nothing else matches
    ),
    # --- Fallback ---
    TemplateEntry(
        id="generic_game",
        name="Generic Game",
        tags=["game", "play"],
        required=[],
        boosted=[],
        anti=["data_app", "calculator", "converter", "timing"],
        base_score=0.0,  # Absolute fallback for non-data
    ),
]


def score_template(template: TemplateEntry, features: Dict[str, Feature]) -> float:
    """Score a template against extracted features.  Higher = better match.

    Scoring (attention-like weighting):
     - Start with base_score (template specificity)
     - Required features: if missing → return -infinity
     - Boosted features: add  feature.confidence * 10  per match
     - Anti features:    subtract  feature.confidence * 8  per match
     - Tag overlap:      add 2 per tag found in description
    """
    score = template.base_score

    # Hard requirement check
    for req in template.required:
        if req not in features:
            return -999.0

    # Boosted features (feature-level attention)
    for boost in template.boosted:
        if boost in features:
            score += features[boost].confidence * 10.0

    # Anti features (negative attention)
    for anti in template.anti:
        if anti in features:
            score -= features[anti].confidence * 8.0

    return score


def match_template(description: str) -> Tuple[str, Dict[str, Feature], List[Tuple[str, float]]]:
    """Find the best template for a description.

    Returns:
        (best_template_id, features, all_scores)
    """
    features = extract_features(description)

    scores: List[Tuple[str, float]] = []
    for tmpl in TEMPLATE_REGISTRY:
        s = score_template(tmpl, features)
        scores.append((tmpl.id, round(s, 2)))

    scores.sort(key=lambda x: -x[1])

    best_id = scores[0][0] if scores else "generic_game"
    return best_id, features, scores


# =====================================================================
# Diagnostic helper  (for debugging / UI)
# =====================================================================
def explain_match(description: str) -> str:
    """Human-readable explanation of why a template was chosen."""
    best_id, features, scores = match_template(description)

    lines = [f"Description: \"{description}\"", ""]
    lines.append("Extracted Features:")
    for f in features.values():
        lines.append(f"  {f}")
    lines.append("")
    lines.append("Template Scores (top 5):")
    for tid, s in scores[:5]:
        marker = " ← SELECTED" if tid == best_id else ""
        # Look up template name
        name = tid
        for t in TEMPLATE_REGISTRY:
            if t.id == tid:
                name = t.name
                break
        lines.append(f"  {s:7.2f}  {name} ({tid}){marker}")

    return "\n".join(lines)
