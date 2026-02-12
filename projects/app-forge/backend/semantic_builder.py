"""
Semantic Game Builder - Reduce complexity through context-based composition

Instead of 30+ specific templates, we use:
1. Semantic extraction: Pull meaning from description
2. Archetype matching: Map to ~5 base patterns
3. Primitive composition: Add mechanics as layers

Archetypes:
  - CANVAS_ACTION: Real-time movement/physics (snake, pong, flappy)
  - GRID_TURN: Turn-based grid interaction (tictactoe, connect4, sudoku)
  - GRID_MATCH: Pattern matching on grid (memory, wordle)
  - CARD_GAME: Deck-based mechanics (blackjack)
  - WORD_GUESS: Letter/word guessing (hangman, wordle)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple


# ========== SEMANTIC CONTEXT CLUES ==========

CONTEXT_CLUES = {
    # Movement patterns
    "realtime_movement": [
        r"move\s*(around|left|right|up|down)", r"arrow\s*keys?", r"wasd",
        r"continuous", r"real.?time", r"chase", r"avoid", r"dodge"
    ],
    "gravity_physics": [
        r"fall(ing)?", r"jump", r"bounce", r"gravity", r"physics",
        r"fly", r"bird", r"flap", r"tap\s*to"
    ],
    "ball_paddle": [
        r"ball", r"paddle", r"pong", r"tennis", r"bounce\s*back", r"brick"
    ],
    
    # Grid patterns
    "grid_cells": [
        r"grid", r"cells?", r"squares?", r"tiles?", r"board",
        r"\d+\s*x\s*\d+", r"rows?\s*(and|&)?\s*columns?"
    ],
    "turn_based": [
        r"turns?", r"player\s*[12]", r"my\s*turn", r"alternate",
        r"vs\.?", r"opponent", r"two\s*player"
    ],
    "match_pairs": [
        r"match(ing)?", r"pairs?", r"memory", r"flip", r"reveal",
        r"same\s*(card|tile|image)"
    ],
    "win_line": [
        r"(3|4|5)\s*in\s*a?\s*row", r"line\s*of", r"connect",
        r"tic\s*tac", r"win\s*(line|condition)"
    ],
    
    # Word/letter patterns
    "word_guessing": [
        r"guess.*word", r"word.*guess", r"hangman", r"hidden\s*word",
        r"letter\s*by\s*letter", r"reveal\s*letters?"
    ],
    "letter_feedback": [
        r"wordle", r"green|yellow|gray", r"feedback", r"correct\s*position",
        r"wrong\s*position", r"5\s*letter"
    ],
    
    # Card patterns  
    "card_deck": [
        r"cards?", r"deck", r"deal", r"draw", r"suit", r"hearts?|diamonds?|clubs?|spades?",
        r"blackjack", r"poker", r"21"
    ],
    
    # Puzzle patterns
    "number_puzzle": [
        r"sudoku", r"9\s*x\s*9", r"1.?9", r"valid(ate)?.*numbers?",
        r"fill.*grid", r"logic\s*puzzle"
    ],
    "sliding": [
        r"slide", r"15\s*puzzle", r"sliding.*tiles?", r"rearrange",
        r"empty\s*(space|slot)"
    ],
    
    # Scoring patterns
    "score_points": [
        r"score", r"points?", r"high\s*score", r"best"
    ],
    "count_moves": [
        r"moves?", r"attempts?", r"tries?", r"guesses?"
    ],
    "timer": [
        r"time(r|d)?", r"countdown", r"seconds?", r"minutes?", r"clock"
    ],
}


@dataclass
class SemanticProfile:
    """Extracted semantic meaning from a description."""
    description: str
    detected_clues: Dict[str, float] = field(default_factory=dict)
    archetype: str = ""
    mechanics: List[str] = field(default_factory=list)
    render_type: str = "grid"  # canvas, grid, cards, text
    input_type: str = "click"  # click, keyboard, both
    scoring_type: str = "score"  # score, moves, timer, none


def extract_semantics(description: str) -> SemanticProfile:
    """Extract semantic meaning from a natural language description."""
    desc_lower = description.lower()
    profile = SemanticProfile(description=description)
    
    # Score each context clue category
    for clue_name, patterns in CONTEXT_CLUES.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, desc_lower):
                score += 1
        if score > 0:
            profile.detected_clues[clue_name] = score / len(patterns)
    
    # Determine archetype based on strongest signals
    clues = profile.detected_clues
    
    # Real-time canvas games
    if any(c in clues for c in ["realtime_movement", "gravity_physics", "ball_paddle"]):
        profile.archetype = "CANVAS_ACTION"
        profile.render_type = "canvas"
        profile.input_type = "keyboard"
        if "gravity_physics" in clues:
            profile.mechanics.append("gravity")
        if "ball_paddle" in clues:
            profile.mechanics.append("physics")
        if "realtime_movement" in clues:
            profile.mechanics.append("movement")
    
    # Match/memory games (check BEFORE cards since "flip cards" triggers both)
    elif "match_pairs" in clues:
        profile.archetype = "GRID_MATCH"
        profile.render_type = "grid"
        profile.input_type = "click"
        profile.mechanics.append("flip_match")
    
    # Card games
    elif "card_deck" in clues:
        profile.archetype = "CARD_GAME"
        profile.render_type = "cards"
        profile.input_type = "click"
        profile.mechanics.append("deck")
    
    # Word guessing
    elif any(c in clues for c in ["word_guessing", "letter_feedback"]):
        profile.archetype = "WORD_GUESS"
        profile.render_type = "text"
        profile.input_type = "keyboard"
        if "letter_feedback" in clues:
            profile.mechanics.append("position_feedback")
        else:
            profile.mechanics.append("reveal_letters")
    
    # Grid games (check win_line first since it implies grid)
    elif "win_line" in clues or "turn_based" in clues:
        profile.render_type = "grid"
        profile.input_type = "click"
        profile.archetype = "GRID_TURN"
        profile.mechanics.append("turns")
        profile.mechanics.append("win_line")
    
    # Number puzzles (sudoku etc)
    elif "number_puzzle" in clues:
        profile.render_type = "grid"
        profile.input_type = "click"
        profile.archetype = "GRID_PUZZLE"
        profile.mechanics.append("constraint_check")
    
    # Sliding puzzles
    elif "sliding" in clues:
        profile.render_type = "grid"
        profile.input_type = "click"
        profile.archetype = "GRID_SLIDE"
        profile.mechanics.append("tile_slide")
    
    # Generic grid
    elif "grid_cells" in clues:
        profile.render_type = "grid"
        profile.input_type = "click"
        profile.archetype = "GRID_TURN"
    
    # Default fallback
    else:
        profile.archetype = "GENERIC"
        profile.render_type = "grid"
    
    # Scoring type
    if "timer" in clues:
        profile.scoring_type = "timer"
    elif "count_moves" in clues:
        profile.scoring_type = "moves"
    elif "score_points" in clues:
        profile.scoring_type = "score"
    
    return profile


# ========== ARCHETYPE TEMPLATES ==========

ARCHETYPE_TEMPLATES = {
    "CANVAS_ACTION": {
        "description": "Real-time canvas game with movement/physics",
        "base_mechanics": ["game_loop", "collision", "score"],
        "variants": {
            "gravity": ["jump", "fall", "obstacles"],
            "physics": ["bounce", "velocity", "angles"],
            "movement": ["direction", "grow", "walls"],
        }
    },
    "GRID_TURN": {
        "description": "Turn-based grid game",
        "base_mechanics": ["grid_render", "click_handler", "turn_switch"],
        "variants": {
            "win_line": ["check_line", "highlight_winner"],
            "drop": ["gravity_drop", "column_fill"],
        }
    },
    "GRID_MATCH": {
        "description": "Pattern matching on grid",
        "base_mechanics": ["grid_render", "click_handler", "match_check"],
        "variants": {
            "flip_match": ["flip_animation", "pair_memory"],
            "position_match": ["color_feedback", "position_check"],
        }
    },
    "CARD_GAME": {
        "description": "Card-based game with deck",
        "base_mechanics": ["deck_shuffle", "deal", "card_render"],
        "variants": {
            "score_21": ["hit_stand", "dealer_ai", "bust_check"],
        }
    },
    "WORD_GUESS": {
        "description": "Word/letter guessing game",
        "base_mechanics": ["word_select", "letter_input", "win_check"],
        "variants": {
            "reveal_letters": ["wrong_count", "hangman_draw"],
            "position_feedback": ["color_letters", "row_submit"],
        }
    },
}


def map_to_archetype(profile: SemanticProfile) -> Tuple[str, List[str]]:
    """Map semantic profile to archetype and required mechanics."""
    archetype = profile.archetype
    if archetype not in ARCHETYPE_TEMPLATES:
        archetype = "GENERIC"
        return archetype, []
    
    template = ARCHETYPE_TEMPLATES[archetype]
    mechanics = list(template["base_mechanics"])
    
    # Add variant mechanics
    for mech in profile.mechanics:
        if mech in template.get("variants", {}):
            mechanics.extend(template["variants"][mech])
    
    return archetype, mechanics


# ========== TEST IT ==========

def analyze(desc: str) -> None:
    """Analyze a description and show semantic mapping."""
    print(f"\n{'='*60}")
    print(f"INPUT: {desc}")
    print('='*60)
    
    profile = extract_semantics(desc)
    archetype, mechanics = map_to_archetype(profile)
    
    print(f"Detected Clues: {list(profile.detected_clues.keys())}")
    print(f"Archetype:      {archetype}")
    print(f"Render Type:    {profile.render_type}")
    print(f"Input Type:     {profile.input_type}")
    print(f"Scoring:        {profile.scoring_type}")
    print(f"Mechanics:      {mechanics}")


if __name__ == "__main__":
    tests = [
        "a snake game where I move around and eat food",
        "pong with a ball that bounces between paddles",
        "flappy bird tap to fly avoid pipes",
        "tic tac toe 3 in a row",
        "memory matching game flip cards to find pairs",
        "connect four drop discs 4 in a row",
        "blackjack card game hit or stand to get 21",
        "wordle 5 letter word guessing with color feedback",
        "sudoku 9x9 number puzzle",
        "hangman guess the hidden word letter by letter",
        "a game with a grid",
        "some kind of fun game",
    ]
    
    for t in tests:
        analyze(t)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY: 12 games mapped to just 5 archetypes!")
    print("="*60)
    from collections import Counter
    archetypes = [extract_semantics(t).archetype for t in tests]
    for arch, count in Counter(archetypes).most_common():
        print(f"  {arch}: {count}")
