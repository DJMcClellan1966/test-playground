#!/usr/bin/env python
"""Advanced test suite for App Forge NLU - stress tests robustness."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from template_registry import match_template, extract_features

passed = 0
failed = 0

def check(condition, name):
    global passed, failed
    if condition:
        print(f"  [OK] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}")
        failed += 1

def get_match(desc):
    best_id, features, scores = match_template(desc)
    return best_id

def get_score(desc):
    best_id, features, scores = match_template(desc)
    return scores[0][1] if scores else 0

def get_top_n(desc, n=3):
    best_id, features, scores = match_template(desc)
    return [s[0] for s in scores[:n]]

# ============================================================
# TEST 1: TYPO TOLERANCE
# ============================================================
print("\n=== TEST 1: Typo Tolerance ===")

# Mild typos - should still work if close enough
typo_tests = [
    ("calculater app", "calculator"),       # common misspelling
    ("tik tak toe", "tictactoe"),           # phonetic spelling
    ("memroy game", "memory_game"),         # transposed letters
    ("recation game", "reaction_game"),     # missing letter
    ("puzzel game", "sliding_puzzle"),      # common misspelling
    ("quize app", "quiz"),                  # extra letter
    ("timmer app", "timer"),                # doubled letter
]

for desc, expected in typo_tests:
    result = get_match(desc)
    # Note: We're testing if typos break things, not expecting perfect handling
    if result == expected:
        check(True, f"'{desc}' -> {expected}")
    else:
        # Check if it's at least in top 3 (acceptable fallback)
        top3 = get_top_n(desc)
        if expected in top3:
            check(True, f"'{desc}' -> {result} (wanted {expected}, but it's in top 3)")
        else:
            check(False, f"'{desc}' -> {result} (wanted {expected})")

# ============================================================
# TEST 2: SLANG/INFORMAL LANGUAGE
# ============================================================
print("\n=== TEST 2: Slang/Informal Language ===")

slang_tests = [
    ("number cruncher", ["calculator", "converter"]),
    ("brain teaser", ["quiz", "sliding_puzzle", "wordle", "memory_game"]),
    ("clicky game", ["reaction_game", "generic_game"]),
    ("match two cards", ["memory_game"]),
    ("letter word puzzle", ["wordle", "hangman"]),
    ("guess the word", ["hangman", "wordle", "guess_game"]),
    ("whack the button fast", ["reaction_game"]),
    ("tick tock countdown", ["timer"]),
    ("secret word game", ["hangman", "wordle"]),
    ("X's and O's", ["tictactoe"]),
]

for desc, acceptable in slang_tests:
    result = get_match(desc)
    check(result in acceptable, f"'{desc}' -> {result} (acceptable: {acceptable})")

# ============================================================
# TEST 3: COMPOUND REQUESTS
# ============================================================
print("\n=== TEST 3: Compound Requests ===")

# When multiple intents collide, which should win?
compound_tests = [
    # Primary intent should win
    ("quiz game with a timer", "quiz"),           # quiz is primary
    ("timer with quiz questions", "timer"),       # timer is primary
    ("calculator that saves history", "calculator"),  # calculator primary
    ("memory game with scoring", "memory_game"),  # game primary  
    ("recipe tracker with calculations", "crud"), # data app primary
    ("timed reaction test", "reaction_game"),     # reaction is specific
    ("puzzle game for trivia", "quiz"),           # trivia = quiz
]

for desc, expected in compound_tests:
    result = get_match(desc)
    check(result == expected, f"'{desc}' -> {result} (expected {expected})")

# ============================================================
# TEST 4: NEGATION HANDLING
# ============================================================
print("\n=== TEST 4: Negation Handling ===")

# Negation is HARD for NLU - let's see what happens
negation_tests = [
    # These are challenging - NLU may or may not handle negation
    ("not a game, just a timer", ["timer", "generic_game"]),
    ("simple timer, not a game", ["timer", "generic_game"]),
    ("calculator without games", ["calculator"]),
    ("just data storage, nothing fancy", ["crud"]),
]

for desc, acceptable in negation_tests:
    result = get_match(desc)
    # Negation awareness is aspirational - check if result is reasonable
    check(result in acceptable, f"'{desc}' -> {result} (acceptable: {acceptable})")

# ============================================================
# TEST 5: SYNONYM RECOGNITION
# ============================================================
print("\n=== TEST 5: Synonym Recognition ===")

synonym_tests = [
    # Direct synonyms
    ("arithmetic tool", "calculator"),
    ("countdown clock", "timer"),
    ("unit transformer", "converter"),
    ("knowledge test", "quiz"),
    ("reflexes test", "reaction_game"),
    ("inventory tracker", "crud"),
    ("task manager", "crud"),
    ("notes application", "crud"),
    ("card matching", "memory_game"),
    ("noughts and crosses", "tictactoe"),
]

for desc, expected in synonym_tests:
    result = get_match(desc)
    top3 = get_top_n(desc)
    if result == expected:
        check(True, f"'{desc}' -> {expected}")
    elif expected in top3:
        check(True, f"'{desc}' -> {result} (wanted {expected}, in top 3)")
    else:
        check(False, f"'{desc}' -> {result} (wanted {expected})")

# ============================================================
# TEST 6: ADVERSARIAL INPUTS
# ============================================================
print("\n=== TEST 6: Adversarial Inputs ===")

adversarial_tests = [
    # Descriptions that LOOK like one thing but mean another
    ("I want to time how fast I can react", "reaction_game"),  # "time" doesn't mean timer
    ("calculate my quiz score", "quiz"),                        # calc doesn't mean calculator
    ("convert this quiz to digital", "quiz"),                   # convert != converter
    ("puzzle out these math problems", "calculator"),           # puzzle != sliding_puzzle
    ("match these numbers together", "memory_game"),            # match = memory
    ("slide into this quiz", "quiz"),                           # slide != sliding_puzzle
    ("mine some data", "crud"),                                 # mine != minesweeper
    ("hang on let me make a todo list", "crud"),                # hang != hangman
]

for desc, expected in adversarial_tests:
    result = get_match(desc)
    top3 = get_top_n(desc)
    if result == expected:
        check(True, f"'{desc}' -> {expected}")
    elif expected in top3:
        # Acceptable if in top 3 for adversarial cases
        check(True, f"'{desc}' -> {result} (wanted {expected}, in top 3)")
    else:
        check(False, f"'{desc}' -> {result} (wanted {expected})")

# ============================================================
# TEST 7: CONFIDENCE SCORING
# ============================================================
print("\n=== TEST 7: Confidence Scoring ===")

# High confidence matches should be correct
# Low confidence might indicate poor match

high_confidence_should_match = [
    ("calculator", "calculator", 8.0),
    ("timer", "timer", 8.0),
    ("sliding puzzle", "sliding_puzzle", 8.0),
    ("tic tac toe", "tictactoe", 8.0),
    ("minesweeper game", "minesweeper", 8.0),
]

for desc, expected, min_score in high_confidence_should_match:
    best_id, features, scores = match_template(desc)
    score = scores[0][1] if scores else 0
    check(best_id == expected and score >= min_score, 
          f"'{desc}' -> {best_id} (score {score:.1f}, min {min_score})")

# Ambiguous descriptions should have lower confidence gap
ambiguous_descs = [
    "make something fun",
    "app for stuff",
    "a useful tool",
]

for desc in ambiguous_descs:
    best_id, features, scores = match_template(desc)
    if len(scores) >= 2:
        gap = scores[0][1] - scores[1][1]
        # A small gap suggests the system is uncertain (which is correct!)
        check(gap < 5.0, f"'{desc}' -> {best_id} has uncertainty (gap={gap:.1f})")
    else:
        check(True, f"'{desc}' -> {best_id}")

# ============================================================
# TEST 8: FEATURE EXTRACTION EDGE CASES
# ============================================================
print("\n=== TEST 8: Feature Extraction Edge Cases ===")

feature_edge_cases = [
    # Multiple features
    ("todo list with login and dark mode and search", 
     ["auth", "storage"]),
    # Feature in weird position
    ("I want auth for my recipe app", ["auth"]),
    # Implicit features
    ("personal private app", []),  # might not detect explicit features
    # Feature synonyms
    ("sign in required", ["auth"]),
    ("password protected", ["auth"]),
    ("save everything", ["storage"]),
]

for desc, expected_features in feature_edge_cases:
    features = extract_features(desc)
    found = [f for f in expected_features if f in features]
    if len(expected_features) == 0:
        check(True, f"'{desc[:40]}...' -> no specific features expected")
    else:
        check(len(found) > 0, f"'{desc[:40]}...' -> found {list(features.keys())}")

# ============================================================
# TEST 9: EXTREME INPUT LENGTHS
# ============================================================
print("\n=== TEST 9: Extreme Input Lengths ===")

# Single word
single_word = "calculator"
check(get_match(single_word) == "calculator", f"Single word: '{single_word}'")

# Two words
two_words = "quiz app"
check(get_match(two_words) == "quiz", f"Two words: '{two_words}'")

# Very long description
long_desc = ("I want to build a comprehensive timer application that helps me "
             "track my time during work sessions using the pomodoro technique "
             "with breaks and notifications and maybe some statistics about "
             "how much time I spend on different tasks throughout the day")
check(get_match(long_desc) == "timer", f"Long description (~{len(long_desc)} chars)")

# Description with lots of filler
filler_desc = ("um so like I was thinking maybe if it's not too much trouble "
               "could you possibly help me make some kind of calculator thing "
               "you know for doing math and stuff like that please thank you")
result = get_match(filler_desc)
check(result == "calculator", f"Filler words: -> {result}")

# ============================================================
# TEST 10: UNICODE AND SPECIAL CHARACTERS
# ============================================================
print("\n=== TEST 10: Unicode and Special Characters ===")

unicode_tests = [
    ("calculator 🧮", "calculator"),
    ("⏱️ timer app", "timer"),
    ("quiz❓game", "quiz"),
    ("tic-tac-toe game", "tictactoe"),
    ("memory_game app", "memory_game"),
    ("calc @#$% app", "calculator"),
]

for desc, expected in unicode_tests:
    result = get_match(desc)
    check(result == expected, f"'{desc}' -> {result} (expected {expected})")

# ============================================================
# RESULTS
# ============================================================
print("\n" + "=" * 60)
print(f"ADVANCED TEST RESULTS: {passed} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    print(f"\n⚠️  {failed} tests need attention (some may be aspirational)")
else:
    print("\n✓ All tests passed!")

# Exit with warning if many failures (>20% is concerning)
failure_rate = failed / (passed + failed) if (passed + failed) > 0 else 0
if failure_rate > 0.20:
    print(f"\n⚠️  Failure rate is {failure_rate:.0%} - review needed")
    sys.exit(1)
else:
    print(f"\nFailure rate: {failure_rate:.0%} (acceptable)")
    sys.exit(0)
