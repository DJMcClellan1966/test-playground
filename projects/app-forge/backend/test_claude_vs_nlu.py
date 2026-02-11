#!/usr/bin/env python
"""Compare Claude's template picks vs App Forge NLU - Round 2."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from template_registry import match_template

# Available templates:
# sliding_puzzle, tictactoe, memory_game, guess_game, quiz, hangman,
# wordle, calculator, converter, timer, reaction_game, minesweeper, crud, generic_game

# Claude's picks (what I think is the best template for each description)
CLAUDE_PICKS = [
    # Games
    ("make a fun sliding number puzzle", "sliding_puzzle"),
    ("build me a word guessing game like hangman", "hangman"),
    ("create a 5-letter word puzzle game", "wordle"),
    ("I want a classic X and O game", "tictactoe"),
    ("make a card matching memory game", "memory_game"),
    ("create a bomb-finding grid game", "minesweeper"),
    ("random number guessing between 1-100", "guess_game"),
    ("a trivia game with questions and answers", "quiz"),
    ("test my reflexes with a click game", "reaction_game"),
    ("make a simple game for killing time", "generic_game"),
    
    # Tools
    ("basic arithmetic calculator", "calculator"),
    ("convert celsius to fahrenheit", "converter"),
    ("pomodoro timer for studying", "timer"),
    ("stopwatch for workouts", "timer"),
    ("BMI calculator", "calculator"),
    
    # Data Apps
    ("track my daily habits", "crud"),
    ("recipe book with ingredients", "crud"),
    ("personal movie collection", "crud"),
    ("workout log app", "crud"),
    ("budget tracker for expenses", "crud"),
]

def run_comparison():
    print("=" * 70)
    print("Claude vs App Forge NLU - Template Matching Comparison (Round 2)")
    print("=" * 70)
    
    matches = 0
    mismatches = []
    
    for desc, claude_pick in CLAUDE_PICKS:
        nlu_pick, features, scores = match_template(desc)
        
        if nlu_pick == claude_pick:
            matches += 1
            print(f"[MATCH] '{desc}'")
            print(f"        Both chose: {nlu_pick}")
        else:
            mismatches.append((desc, claude_pick, nlu_pick, scores[:3]))
            print(f"[DIFF]  '{desc}'")
            print(f"        Claude: {claude_pick}, NLU: {nlu_pick}")
            print(f"        Top scores: {[(s[0], round(s[1], 2)) for s in scores[:3]]}")
        print()
    
    print("=" * 70)
    accuracy = matches / len(CLAUDE_PICKS) * 100
    print(f"RESULTS: {matches}/{len(CLAUDE_PICKS)} matches ({accuracy:.0f}% agreement)")
    print("=" * 70)
    
    if mismatches:
        print("\nMismatches to analyze:")
        for desc, claude, nlu, scores in mismatches:
            print(f"  - '{desc}': Claude={claude}, NLU={nlu}")
    
    return matches, len(CLAUDE_PICKS)

if __name__ == "__main__":
    matches, total = run_comparison()
    sys.exit(0 if matches == total else 1)
