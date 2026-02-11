#!/usr/bin/env python
"""Extensive App Forge tests - finds gaps and edge cases."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from template_registry import match_template, extract_features, TEMPLATE_REGISTRY
from codegen import CodeGenerator
from domain_parser import parse_description
from smartq import infer_from_description, get_relevant_questions

# Test counters
passed = 0
failed = 0

def run_test(name, condition, details=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [OK] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")
        if details:
            print(f"        {details}")

def get_template(desc):
    """Helper to get just template name from match_template result."""
    result = match_template(desc)
    return result[0]  # Returns (template_name, features, scores)

def test_edge_case_inputs():
    """Test unusual/edge case inputs."""
    print("\n=== TEST 1: Edge Case Inputs ===")
    
    tmpl = get_template("")
    run_test("Empty string -> fallback", tmpl in ["generic_game", "crud"], f"Got: {tmpl}")
    
    tmpl = get_template("   ")
    run_test("Whitespace only -> fallback", tmpl in ["generic_game", "crud"], f"Got: {tmpl}")
    
    long_desc = "I want a to-do list app " * 50
    tmpl = get_template(long_desc)
    run_test("Very long input -> still matches crud", tmpl == "crud", f"Got: {tmpl}")
    
    tmpl = get_template("create a to-do list!!! @#$%")
    run_test("Special chars -> still works", tmpl == "crud", f"Got: {tmpl}")
    
    tmpl = get_template("MAKE ME A TODO LIST APP")
    run_test("All caps -> still matches", tmpl == "crud", f"Got: {tmpl}")
    
    tmpl = get_template("make a calculator app for 2+2")
    run_test("Numbers in input -> calculator", tmpl == "calculator", f"Got: {tmpl}")

def test_ambiguous_requests():
    """Test inputs that could match multiple templates."""
    print("\n=== TEST 2: Ambiguous Requests ===")
    
    tmpl = get_template("game with timing")
    run_test("Game with timing -> game not timer", 
             tmpl in ["reaction_game", "generic_game"],
             f"Got: {tmpl}")
    
    tmpl = get_template("timer for cooking")
    run_test("Timer for cooking -> timer", tmpl == "timer", f"Got: {tmpl}")
    
    tmpl = get_template("quiz me on math")
    run_test("Quiz on math -> quiz not calculator", tmpl == "quiz", f"Got: {tmpl}")
    
    tmpl = get_template("app to write down stuff")
    run_test("Write down stuff -> matches crud", 
             tmpl == "crud", f"Got: {tmpl}")

def test_feature_extraction():
    """Test feature extraction edge cases."""
    print("\n=== TEST 3: Feature Extraction ===")
    
    features = extract_features("app with login and password")
    # Features can be Feature objects or dicts/strings - handle all cases
    feature_names = []
    for f in features:
        if hasattr(f, 'name'):
            feature_names.append(f.name)
        elif isinstance(f, dict):
            feature_names.append(f.get('name', ''))
        elif isinstance(f, str):
            feature_names.append(f)
    run_test("Login/password -> auth detected", "auth" in feature_names, f"Got: {feature_names}")
    
    features = extract_features("save data to disk")
    feature_names = []
    for f in features:
        if hasattr(f, 'name'):
            feature_names.append(f.name)
        elif isinstance(f, dict):
            feature_names.append(f.get('name', ''))
        elif isinstance(f, str):
            feature_names.append(f)
    run_test("Save data -> storage detected", "storage" in feature_names, f"Got: {feature_names}")
    
    features = extract_features("fullscreen mobile app")
    feature_names = []
    for f in features:
        if hasattr(f, 'name'):
            feature_names.append(f.name)
        elif isinstance(f, dict):
            feature_names.append(f.get('name', ''))
        elif isinstance(f, str):
            feature_names.append(f)
    run_test("Fullscreen mobile -> responsive", "responsive" in feature_names, f"Got: {feature_names}")
    
    features = extract_features("quiz app with login that saves progress")
    feature_names = []
    for f in features:
        if hasattr(f, 'name'):
            feature_names.append(f.name)
        elif isinstance(f, dict):
            feature_names.append(f.get('name', ''))
        elif isinstance(f, str):
            feature_names.append(f)
    run_test("Multi-feature detection", 
             "auth" in feature_names or "storage" in feature_names, f"Got: {feature_names}")

def test_codegen_smoke():
    """Smoke test code generation."""
    print("\n=== TEST 4: Code Generation Smoke Test ===")
    
    generator = CodeGenerator()
    # Use only templates that actually exist in the registry
    templates = ["calculator", "quiz", "timer", 
                 "sliding_puzzle", "reaction_game", "generic_game", "crud"]
    
    for tmpl in templates:
        try:
            html = generator.generate_index_html("Test", {}, f"test {tmpl}")
            has_doctype = html.strip().lower().startswith("<!doctype")
            run_test(f"{tmpl} -> valid HTML", has_doctype, f"HTML start: {html[:50]}...")
        except Exception as e:
            run_test(f"{tmpl} -> no crash", False, str(e))

def test_domain_parser():
    """Test domain parser edge cases."""
    print("\n=== TEST 5: Domain Parser ===")
    
    result = parse_description("todo app for groceries")
    run_test("Parse grocery todo", result is not None, f"Result: {result}")
    
    result = parse_description("game where you click fast")
    run_test("Parse game domain", result is not None, f"Result: {result}")
    
    inferred = infer_from_description("todo app")
    questions = get_relevant_questions(inferred)
    run_test("Todo -> gets questions", len(questions) > 0, f"Got {len(questions)} questions")

def test_question_generation():
    """Test smart question generation."""
    print("\n=== TEST 6: Question Generation ===")
    
    inferred = infer_from_description("shopping list app")
    run_test("Shopping list -> infers something", len(inferred) > 0, f"Inferred: {inferred}")
    
    inferred = infer_from_description("make me an app")
    questions = get_relevant_questions(inferred)
    run_test("Vague request -> asks questions", len(questions) > 0, f"Got {len(questions)} questions")

def test_template_coverage():
    """Verify all templates are reachable."""
    print("\n=== TEST 7: Template Coverage ===")
    
    # Map of templates to trigger phrases (only use actual templates)
    template_triggers = {
        "crud": "todo list app",
        "calculator": "calculator app",
        "quiz": "quiz app",
        "timer": "timer app",
        "reaction_game": "reaction time game",
        "sliding_puzzle": "sliding puzzle game",
        "generic_game": "a game",
        "tictactoe": "tic tac toe game",
        "memory_game": "memory matching game",
        "guess_game": "number guessing game",
        "hangman": "hangman game",
        "wordle": "wordle game",
        "converter": "unit converter",
        "minesweeper": "minesweeper game",
    }
    
    for template, trigger in template_triggers.items():
        if template in [e.id for e in TEMPLATE_REGISTRY]:
            tmpl = get_template(trigger)
            run_test(f"'{trigger}' -> {template}", tmpl == template, f"Got: {tmpl}")

def test_discrimination():
    """Test that similar inputs get different templates."""
    print("\n=== TEST 8: Input Discrimination ===")
    
    pairs = [
        ("math quiz", "calculator", "quiz", "calculator"),
        ("reaction game", "sliding puzzle", "reaction_game", "sliding_puzzle"),
        ("timer app", "reaction game", "timer", "reaction_game"),
        ("tic tac toe", "memory game", "tictactoe", "memory_game"),
    ]
    
    template_ids = [e.id for e in TEMPLATE_REGISTRY]
    for input1, input2, exp1, exp2 in pairs:
        if exp1 in template_ids and exp2 in template_ids:
            tmpl1 = get_template(input1)
            tmpl2 = get_template(input2)
            run_test(f"'{input1}' vs '{input2}'", tmpl1 != tmpl2, f"Got: {tmpl1} vs {tmpl2}")

if __name__ == "__main__":
    print("=" * 60)
    print("App Forge Extensive Test Suite")
    print("=" * 60)
    
    test_edge_case_inputs()
    test_ambiguous_requests()
    test_feature_extraction()
    test_codegen_smoke()
    test_domain_parser()
    test_question_generation()
    test_template_coverage()
    test_discrimination()
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        print("\nFailed tests indicate gaps to address.")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)
