"""
Hybrid Semantic-Neural Game Builder

Combines:
1. Fast regex-based semantic extraction (handles 90% of cases)
2. GloVe embedding similarity (handles edge cases/novel descriptions)
3. Template-based generation (fast output)

This gives us:
- Speed of templates (sub-ms generation)
- Flexibility of neural similarity (handles "make a game like pac-man")
- Reduced complexity (6 archetypes instead of 30+ templates)
"""

import re
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

# Try to import existing GloVe matcher
try:
    from glove_matcher import glove_match, text_to_template_similarity
    GLOVE_AVAILABLE = True
except ImportError:
    GLOVE_AVAILABLE = False

# Template ID → Archetype mapping (bridges existing templates to archetypes)
TEMPLATE_TO_ARCHETYPE = {
    "snake": "CANVAS_ACTION",
    "pong": "CANVAS_ACTION", 
    "flappy": "CANVAS_ACTION",
    "reaction": "CANVAS_ACTION",
    "guess_number": "WORD_GUESS",
    "tic_tac_toe": "GRID_TURN",
    "connect_four": "GRID_TURN",
    "memory_game": "GRID_MATCH",
    "wordle": "WORD_GUESS",
    "hangman": "WORD_GUESS",
    "minesweeper": "GRID_PUZZLE",
    "sudoku": "GRID_PUZZLE",
    "blackjack": "CARD_GAME",
}


# ========== ARCHETYPE DEFINITIONS ==========

@dataclass 
class Archetype:
    """Game archetype with semantic anchors."""
    id: str
    name: str
    description: str
    keywords: List[str]  # For keyword-based fallback
    example_games: List[str]  # For embedding similarity
    render_type: str
    input_type: str
    base_mechanics: List[str]
    
    # Computed embedding (average of example games + keywords)
    _embedding: Optional[np.ndarray] = field(default=None, repr=False)


ARCHETYPES = [
    Archetype(
        id="CANVAS_ACTION",
        name="Real-time Action",
        description="Fast-paced canvas game with continuous movement and physics",
        keywords=["move", "avoid", "chase", "dodge", "physics", "bounce", "jump", 
                  "fly", "gravity", "real-time", "arcade", "action"],
        example_games=["snake", "pong", "flappy bird", "breakout", "asteroids",
                       "space invaders", "pac-man", "frogger", "doodle jump"],
        render_type="canvas",
        input_type="keyboard",
        base_mechanics=["game_loop", "collision", "score", "movement"],
    ),
    Archetype(
        id="GRID_TURN",
        name="Turn-based Grid",
        description="Strategic grid game with alternating turns and win conditions",
        keywords=["grid", "turn", "board", "strategy", "win", "row", "connect",
                  "player vs", "opponent", "versus", "two player"],
        example_games=["tic tac toe", "connect four", "checkers", "chess", 
                       "othello", "reversi", "gomoku", "mancala"],
        render_type="grid",
        input_type="click",
        base_mechanics=["grid_render", "turn_switch", "win_check"],
    ),
    Archetype(
        id="GRID_MATCH",
        name="Pattern Matching",
        description="Grid-based game focused on matching or revealing patterns",
        keywords=["match", "pair", "memory", "flip", "reveal", "same", "find",
                  "concentration", "pairs"],
        example_games=["memory game", "concentration", "matching pairs", 
                       "mahjong solitaire", "bejeweled", "candy crush"],
        render_type="grid",
        input_type="click",
        base_mechanics=["grid_render", "match_check", "flip_animation"],
    ),
    Archetype(
        id="GRID_PUZZLE",
        name="Logic Puzzle",
        description="Grid-based logic puzzle with constraints",
        keywords=["puzzle", "logic", "solve", "constraint", "numbers", "fill",
                  "valid", "rules", "deduce"],
        example_games=["sudoku", "nonogram", "picross", "kakuro", "kenken",
                       "minesweeper", "lights out"],
        render_type="grid",
        input_type="click",
        base_mechanics=["grid_render", "constraint_check", "validation"],
    ),
    Archetype(
        id="WORD_GUESS",
        name="Word Game",
        description="Letter or word-based guessing game",
        keywords=["word", "letter", "guess", "spell", "vocabulary", "hidden",
                  "reveal", "alphabet", "typing"],
        example_games=["hangman", "wordle", "wheel of fortune", "scrabble",
                       "boggle", "word search", "crossword"],
        render_type="text",
        input_type="keyboard",
        base_mechanics=["word_select", "letter_input", "feedback"],
    ),
    Archetype(
        id="CARD_GAME",
        name="Card Game",
        description="Deck-based card game",
        keywords=["card", "deck", "deal", "hand", "draw", "suit", "trump",
                  "bet", "fold", "hit", "stand"],
        example_games=["blackjack", "poker", "solitaire", "hearts", "spades",
                       "uno", "go fish", "war", "crazy eights"],
        render_type="cards",
        input_type="click",
        base_mechanics=["deck_shuffle", "deal", "card_render"],
    ),
]


# ========== NEURAL SIMILARITY ==========

class NeuralMatcher:
    """Uses existing GloVe matcher to find closest archetype via template mapping."""
    
    def __init__(self):
        self.archetypes = ARCHETYPES
        
    def find_closest_archetype(self, description: str) -> Tuple[str, float]:
        """Find closest archetype by mapping GloVe template matches to archetypes."""
        if not GLOVE_AVAILABLE:
            return "GENERIC", 0.0
        
        # Get best template matches from existing GloVe matcher
        matches = glove_match(description, top_k=5)
        
        if not matches or matches[0][1] < 0.3:
            return "GENERIC", 0.0
        
        # Map top template to archetype
        best_template, best_score = matches[0]
        archetype_id = TEMPLATE_TO_ARCHETYPE.get(best_template, "GENERIC")
        
        return archetype_id, best_score


# ========== HYBRID MATCHER ==========

class HybridMatcher:
    """
    Two-stage matching:
    1. Try fast semantic rules first (high confidence)
    2. Fall back to neural similarity for edge cases
    """
    
    def __init__(self, neural_threshold: float = 0.5):
        self.neural_threshold = neural_threshold
        self.neural_matcher = NeuralMatcher()
        
        # Fast semantic rules (high-confidence patterns)
        self.semantic_rules = [
            # (archetype_id, patterns, confidence)
            ("CANVAS_ACTION", [
                r"snake|pong|flappy|breakout|asteroids|space\s*invad",
                r"pac.?man|pacman|frogger|galaga|centipede|donkey\s*kong",
                r"tetris|falling\s*block|stack.*block|blocks?\s*fall",
                r"move\s*(around|left|right)|arrow\s*keys|wasd",
                r"dodge|avoid|chase|physics|bounce|gravity|jump|fly",
                r"real.?time|arcade|action\s*game|eat.*dots?|collect.*dots?",
            ], 0.9),
            
            ("GRID_TURN", [
                r"tic\s*tac|connect\s*(4|four)|checkers?|chess",
                r"battleship|naval|grid.*shoot|guess.*location",
                r"(3|4|5)\s*in\s*a?\s*row|turns?|two\s*player|vs\.?|versus",
                r"board\s*game|strategy",
            ], 0.9),
            
            ("GRID_MATCH", [
                r"memory\s*(game|match)|matching\s*pairs?|concentration",
                r"flip.*cards?|reveal.*same|find.*pairs?|flip.*tiles?",
                r"bejeweled|candy\s*crush|match.?3",
                r"simon\s*says|simon|pattern\s*memory|repeat.*pattern",
            ], 0.9),
            
            ("GRID_PUZZLE", [
                r"sudoku|minesweeper|nonogram|picross|kakuro",
                r"logic\s*puzzle|constraint|9\s*x\s*9|fill.*grid",
                r"puzzle.*numbers?|solve.*grid|lights?\s*out",
            ], 0.9),
            
            ("WORD_GUESS", [
                r"hangman|wordle|word\s*game|guess.*word",
                r"letter.*guess|hidden\s*word|spell",
                r"crossword|word\s*search|scrabble|boggle",
            ], 0.9),
            
            ("CARD_GAME", [
                r"blackjack|poker|solitaire|hearts|spades|uno",
                r"card\s*game|deck|deal|draw\s*cards?",
                r"hit.*stand|bet|fold|trump",
            ], 0.9),
        ]
    
    def match(self, description: str) -> Tuple[str, float, str]:
        """
        Match description to archetype.
        Returns: (archetype_id, confidence, method)
        """
        desc_lower = description.lower()
        
        # Stage 1: Try fast semantic rules
        for archetype_id, patterns, confidence in self.semantic_rules:
            for pattern in patterns:
                if re.search(pattern, desc_lower):
                    return archetype_id, confidence, "semantic"
        
        # Stage 2: Fall back to neural similarity
        if GLOVE_AVAILABLE:
            archetype_id, similarity = self.neural_matcher.find_closest_archetype(description)
            if similarity >= self.neural_threshold:
                return archetype_id, similarity, "neural"
        
        # Stage 3: Keyword fallback (no embeddings)
        best_match = "GENERIC"
        best_count = 0
        for arch in ARCHETYPES:
            count = sum(1 for kw in arch.keywords if kw in desc_lower)
            if count > best_count:
                best_count = count
                best_match = arch.id
        
        if best_count > 0:
            return best_match, best_count / 10, "keyword"
        
        return "GENERIC", 0.0, "fallback"


# ========== MECHANIC INFERENCE ==========

MECHANIC_PATTERNS = {
    # Movement mechanics
    "gravity": r"gravity|fall|jump|fly|tap\s*to",
    "physics": r"physics|bounce|velocity|angle|ball",
    "direction": r"direction|arrow|wasd|move|steer",
    
    # Grid mechanics
    "win_line": r"(3|4|5)\s*in\s*a?\s*row|connect|line|win",
    "drop": r"drop|fall.*column|gravity.*column",
    "flip_match": r"flip|reveal|match|pairs?|memory",
    "constraint": r"valid|constraint|rule|9\s*x\s*9|sudoku",
    
    # Word mechanics
    "position_feedback": r"wordle|color.*feedback|green.*yellow|position",
    "reveal_letters": r"hangman|reveal|hidden.*word|blanks?",
    
    # Card mechanics
    "hit_stand": r"hit.*stand|blackjack|21|twenty.?one",
    "deck_draw": r"draw|deck|deal|shuffle",
    
    # Scoring
    "timer": r"timer?|countdown|seconds?|timed",
    "score": r"score|points?|high\s*score",
    "moves": r"moves?|attempts?|tries?|guesses?",
}


def infer_mechanics(description: str, archetype: Archetype) -> List[str]:
    """Infer specific mechanics from description, starting with archetype base."""
    mechanics = list(archetype.base_mechanics)
    desc_lower = description.lower()
    
    for mechanic, pattern in MECHANIC_PATTERNS.items():
        if re.search(pattern, desc_lower) and mechanic not in mechanics:
            mechanics.append(mechanic)
    
    return mechanics


# ========== FULL PIPELINE ==========

def analyze(description: str) -> Dict:
    """
    Full hybrid analysis pipeline.
    Returns dict with archetype, mechanics, render/input types, confidence.
    """
    matcher = HybridMatcher()
    archetype_id, confidence, method = matcher.match(description)
    
    # Find archetype object
    archetype = next((a for a in ARCHETYPES if a.id == archetype_id), None)
    
    if archetype is None:
        return {
            "description": description,
            "archetype": "GENERIC",
            "confidence": 0.0,
            "method": "fallback",
            "render_type": "grid",
            "input_type": "click",
            "mechanics": [],
        }
    
    mechanics = infer_mechanics(description, archetype)
    
    return {
        "description": description,
        "archetype": archetype.id,
        "archetype_name": archetype.name,
        "confidence": confidence,
        "method": method,
        "render_type": archetype.render_type,
        "input_type": archetype.input_type,
        "mechanics": mechanics,
    }


# ========== TEST ==========

if __name__ == "__main__":
    print(f"GloVe matcher available: {GLOVE_AVAILABLE}")
    
    tests = [
        # Clear matches (semantic rules)
        "a snake game",
        "tic tac toe",
        "memory matching game",
        "sudoku puzzle",
        "wordle clone",
        "blackjack card game",
        
        # Well-known games (added to semantic rules)
        "make something like pac-man",
        "a tetris-style falling blocks game",
        "simon says pattern game",
        "battleship style game",
        
        # Descriptive (should use semantic or neural)
        "a game where you eat dots and avoid ghosts",
        "I want to flip tiles to find matches",
        "create a game with gravity and jumping",
        
        # Ambiguous (test fallback)
        "a fun game",
        "something to play",
    ]
    
    print("=" * 70)
    print("HYBRID SEMANTIC-NEURAL GAME ANALYSIS")
    print("=" * 70)
    
    success_count = 0
    for desc in tests:
        result = analyze(desc)
        arch = result['archetype']
        conf = result['confidence']
        method = result['method']
        
        # Check if it found a real archetype (not GENERIC for specific requests)
        is_specific = any(word in desc.lower() for word in [
            'snake', 'tac', 'memory', 'sudoku', 'wordle', 'blackjack',
            'pac', 'tetris', 'simon', 'battleship', 'dots', 'ghost',
            'flip', 'tiles', 'gravity', 'jump'
        ])
        success = arch != "GENERIC" if is_specific else True
        success_count += 1 if success else 0
        status = "✓" if success else "✗"
        
        print(f"\n{status} {desc}")
        print(f"  → {arch} ({conf:.2f}) via {method}")
        print(f"    Mechanics: {result.get('mechanics', [])[:4]}...")
    
    print(f"\n{'='*70}")
    print(f"SUCCESS RATE: {success_count}/{len(tests)} ({100*success_count//len(tests)}%)")
