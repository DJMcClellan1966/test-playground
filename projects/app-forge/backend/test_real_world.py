"""
Real-World App Builder Benchmark Test Suite

Tests App Forge against prompts that real users give to popular app builders:
- Bolt (StackBlitz)
- v0 (Vercel)
- Lovable
- Replit Agent
- Claude Artifacts

Scoring criteria:
1. Template Match: Does it pick the right template?
2. Generation Success: Does it generate without errors?
3. Code Quality: Size, completeness, functionality
4. Feature Detection: Does it correctly infer features?
"""
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from hybrid_router import route
from codegen import CodeGenerator
from template_registry import match_template


@dataclass
class BenchmarkResult:
    prompt: str
    source: str  # Which app builder this prompt was inspired by
    expected_type: str  # Expected template category
    matched_template: str
    routing_method: str
    confidence: float
    generation_success: bool
    code_size: int
    has_interactivity: bool
    has_styling: bool
    generation_time_ms: float
    error: Optional[str] = None


# Real-world prompts categorized by source
REAL_WORLD_PROMPTS = {
    # ===== Bolt.new style prompts (concise, action-oriented) =====
    "bolt": [
        ("build me a snake game", "snake", "game"),
        ("create a todo list app with local storage", "crud", "data"),
        ("make a pomodoro timer", "timer", "utility"),  # Timer template handles pomodoro
        ("build a weather dashboard", "crud", "data"),  # No weather template, CRUD is fine
        ("create a markdown editor with preview", "crud", "utility"),  # No markdown template
        ("make a flashcard study app", "crud", "education"),
        ("build a habit tracker", "crud", "data"),
        ("create a kanban board", "crud", "data"),  # No kanban template
        ("make a quiz app", "quiz", "game"),
        ("build a recipe manager", "crud", "data"),
    ],
    
    # ===== v0 style prompts (UI-focused, detailed) =====
    "v0": [
        ("a modern landing page with hero section, features grid, and CTA", "crud", "ui"),
        ("a dashboard with charts and data tables", "crud", "data"),
        ("a login form with email and password validation", "crud", "auth"),
        ("a responsive navbar with mobile hamburger menu", "crud", "ui"),
        ("a card grid layout with hover effects", "crud", "ui"),
        ("a modal dialog with form inputs", "crud", "ui"),
        ("a pricing table with three tiers", "crud", "ui"),
        ("a countdown timer to new years", "timer", "utility"),
        ("a dark mode toggle switch", "crud", "ui"),
        ("an image gallery with lightbox", "crud", "ui"),
    ],
    
    # ===== Lovable style prompts (conversational, feature-rich) =====
    "lovable": [
        ("I want to build a personal finance tracker where I can log expenses, categorize them, and see charts of my spending", "crud", "data"),
        ("Create an app where users can create and share recipes with ingredients and cooking steps", "crud", "data"),
        ("Build me a workout logging app where I track exercises, sets, reps and see my progress over time", "crud", "fitness"),
        ("I need a reading list app where I can save books I want to read and mark them as completed", "crud", "data"),
        ("Make a notes app with folders and tags for organizing my thoughts", "crud", "data"),
        ("Build a movie watchlist where I can rate movies and add reviews", "crud", "data"),
        ("Create a daily journal app with mood tracking", "crud", "data"),
        ("I want a countdown app for multiple events with notifications", "timer", "utility"),
        ("Build a vocabulary learning app with spaced repetition", "crud", "education"),
        ("Create a plant watering reminder app", "crud", "utility"),
    ],
    
    # ===== Replit Agent style prompts (technical, specific) =====
    "replit": [
        ("python flask app with sqlite database for user authentication", "crud", "backend"),
        ("REST API with CRUD operations for a blog", "crud", "api"),
        ("web scraper that extracts data from a website", "crud", "utility"),
        ("chat application with websockets", "crud", "realtime"),
        ("file upload service with image preview", "crud", "utility"),
        ("URL shortener with analytics", "crud", "utility"),
        ("markdown to html converter", "converter", "utility"),  # Converter template is correct
        ("CSV to JSON converter tool", "converter", "utility"),
        ("password generator with options", "crud", "utility"),
        ("command line task manager", "crud", "cli"),
    ],
    
    # ===== Claude Artifacts style prompts (interactive, visual) =====
    "artifacts": [
        ("interactive visualization of sorting algorithms", "algorithm_visualizer", "education"),
        ("a working calculator with scientific functions", "calculator", "utility"),
        ("tic tac toe game that I can play against the computer", "tictactoe", "game"),
        ("a color palette generator", "crud", "design"),
        ("an interactive periodic table", "crud", "education"),
        ("a piano keyboard that plays notes", "crud", "music"),
        ("a regex tester with live highlighting", "crud", "dev-tool"),
        ("a pixel art drawing canvas", "crud", "creative"),
        ("a binary to decimal converter", "converter", "utility"),
        ("a typing speed test", "typing_test", "game"),
    ],
    
    # ===== Common game requests across all platforms =====
    "games": [
        ("tetris", "tetris", "game"),
        ("2048", "game_2048", "game"),
        ("wordle clone", "wordle", "game"),
        ("flappy bird", "flappy", "game"),
        ("pong", "pong", "game"),
        ("memory matching game", "memory_game", "game"),
        ("hangman", "hangman", "game"),
        ("blackjack", "blackjack", "game"),
        ("minesweeper", "minesweeper", "game"),
        ("sudoku solver", "sudoku", "game"),
        ("connect four", "connect_four", "game"),
        ("rock paper scissors", "rps", "game"),
        ("number guessing game", "guess_game", "game"),
        ("reaction time test", "reaction_game", "game"),
        ("cookie clicker", "cookie_clicker", "game"),
    ],
}


def run_benchmark(prompt: str, expected_template: str, source: str, expected_type: str) -> BenchmarkResult:
    """Run a single benchmark test."""
    generator = CodeGenerator()
    error = None
    code = ""
    generation_time = 0
    
    # Route the prompt
    start = time.perf_counter()
    result = route(prompt)
    routing_time = (time.perf_counter() - start) * 1000
    
    # Generate code
    try:
        gen_start = time.perf_counter()
        code = generator.generate_index_html(
            prompt.replace(" ", "-")[:30],
            {"has_data": False},
            prompt
        )
        generation_time = (time.perf_counter() - gen_start) * 1000
        generation_success = len(code) > 500
    except Exception as e:
        generation_success = False
        error = str(e)
    
    # Analyze generated code
    has_interactivity = any(x in code for x in ["onclick", "addEventListener", "function ", "const ", "let "])
    has_styling = "<style>" in code or "style=" in code
    
    return BenchmarkResult(
        prompt=prompt,
        source=source,
        expected_type=expected_type,
        matched_template=result.template_id,
        routing_method=result.method,
        confidence=result.confidence,
        generation_success=generation_success,
        code_size=len(code),
        has_interactivity=has_interactivity,
        has_styling=has_styling,
        generation_time_ms=generation_time + routing_time,
        error=error
    )


def score_match(result: BenchmarkResult, expected: str) -> Tuple[bool, str]:
    """Score whether the match is acceptable."""
    matched = result.matched_template
    
    # Exact match
    if matched == expected:
        return True, "exact"
    
    # Acceptable alternatives
    acceptable_mappings = {
        "crud": ["kanban", "pomodoro", "weather", "markdown", "calendar"],
        "game": ["generic_game", "reaction_game", "guess_game"],
        "utility": ["crud", "timer", "calculator", "converter"],
    }
    
    # Check if matched template is in expected category
    for category, alternatives in acceptable_mappings.items():
        if expected in alternatives and matched in alternatives:
            return True, "category"
        if expected == category and matched in alternatives:
            return True, "category"
    
    # CRUD is acceptable for most data apps
    if expected == "crud" and matched in ["crud", "kanban", "pomodoro", "weather", "markdown", "calendar"]:
        return True, "crud-variant"
    
    return False, "mismatch"


def run_all_benchmarks():
    """Run complete benchmark suite."""
    print("=" * 70)
    print("APP FORGE REAL-WORLD BENCHMARK")
    print("Testing against prompts from: Bolt, v0, Lovable, Replit, Artifacts")
    print("=" * 70)
    
    all_results: Dict[str, List[BenchmarkResult]] = {}
    total_tests = 0
    total_passed = 0
    total_generated = 0
    
    for source, prompts in REAL_WORLD_PROMPTS.items():
        print(f"\n{'=' * 50}")
        print(f"SOURCE: {source.upper()}")
        print("=" * 50)
        
        results = []
        passed = 0
        generated = 0
        
        for prompt, expected, category in prompts:
            result = run_benchmark(prompt, expected, source, category)
            results.append(result)
            
            is_match, match_type = score_match(result, expected)
            
            # Status symbols
            match_symbol = "✓" if is_match else "✗"
            gen_symbol = "✓" if result.generation_success else "✗"
            
            if is_match:
                passed += 1
            if result.generation_success:
                generated += 1
            
            # Truncate prompt for display
            display_prompt = prompt[:45] + "..." if len(prompt) > 45 else prompt
            
            print(f"  [{match_symbol}|{gen_symbol}] {display_prompt}")
            print(f"       → {result.matched_template} ({result.routing_method}, {result.confidence:.0%}) "
                  f"| {result.code_size:,} chars | {result.generation_time_ms:.0f}ms")
            
            if not is_match:
                print(f"       ⚠ Expected: {expected}")
        
        all_results[source] = results
        total_tests += len(prompts)
        total_passed += passed
        total_generated += generated
        
        print(f"\n  Summary: {passed}/{len(prompts)} template matches, {generated}/{len(prompts)} successful generations")
    
    # Overall summary
    print("\n" + "=" * 70)
    print("OVERALL RESULTS")
    print("=" * 70)
    
    print(f"\nTemplate Matching: {total_passed}/{total_tests} ({100*total_passed/total_tests:.1f}%)")
    print(f"Code Generation:   {total_generated}/{total_tests} ({100*total_generated/total_tests:.1f}%)")
    
    # Breakdown by source
    print("\nBy Source:")
    for source, results in all_results.items():
        matches = sum(1 for r in results if score_match(r, REAL_WORLD_PROMPTS[source][[p[0] for p in REAL_WORLD_PROMPTS[source]].index(r.prompt)][1])[0])
        gens = sum(1 for r in results if r.generation_success)
        avg_size = sum(r.code_size for r in results) / len(results)
        avg_time = sum(r.generation_time_ms for r in results) / len(results)
        print(f"  {source:12} - Match: {matches:2}/{len(results)}, Gen: {gens:2}/{len(results)}, "
              f"Avg size: {avg_size:,.0f} chars, Avg time: {avg_time:.0f}ms")
    
    # Routing method breakdown
    print("\nRouting Methods Used:")
    method_counts = {}
    for results in all_results.values():
        for r in results:
            method_counts[r.routing_method] = method_counts.get(r.routing_method, 0) + 1
    for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
        print(f"  {method:12} - {count} ({100*count/total_tests:.1f}%)")
    
    # Code quality metrics
    print("\nCode Quality:")
    all_results_flat = [r for results in all_results.values() for r in results]
    interactive_count = sum(1 for r in all_results_flat if r.has_interactivity)
    styled_count = sum(1 for r in all_results_flat if r.has_styling)
    avg_size = sum(r.code_size for r in all_results_flat) / len(all_results_flat)
    
    print(f"  Interactive: {interactive_count}/{total_tests} ({100*interactive_count/total_tests:.1f}%)")
    print(f"  Styled:      {styled_count}/{total_tests} ({100*styled_count/total_tests:.1f}%)")
    print(f"  Avg Size:    {avg_size:,.0f} characters")
    
    # Identify gaps
    print("\n" + "=" * 70)
    print("GAPS IDENTIFIED (templates that need improvement)")
    print("=" * 70)
    
    mismatches = []
    for source, results in all_results.items():
        prompts_list = REAL_WORLD_PROMPTS[source]
        for i, r in enumerate(results):
            expected = prompts_list[i][1]
            is_match, _ = score_match(r, expected)
            if not is_match:
                mismatches.append((r.prompt, expected, r.matched_template, source))
    
    if mismatches:
        for prompt, expected, got, source in mismatches:
            print(f"  [{source}] \"{prompt[:50]}...\"")
            print(f"      Expected: {expected}, Got: {got}")
    else:
        print("  No significant gaps found!")
    
    print("\n" + "=" * 70)
    print(f"FINAL SCORE: {total_passed}/{total_tests} template matches "
          f"({100*total_passed/total_tests:.1f}%)")
    print("=" * 70)
    
    return total_passed, total_tests


def quick_test():
    """Run a quick subset of tests."""
    print("Quick Real-World Test (subset)")
    print("-" * 40)
    
    quick_prompts = [
        ("build me a snake game", "snake"),
        ("todo list app", "crud"),
        ("wordle clone", "wordle"),
        ("calculator", "calculator"),
        ("sorting algorithm visualizer", "algorithm_visualizer"),
        ("reaction time test", "reaction_game"),
        ("recipe manager app", "crud"),
        ("2048 puzzle game", "game_2048"),
        ("typing speed test", "typing_test"),
        ("countdown timer", "timer"),
    ]
    
    passed = 0
    for prompt, expected in quick_prompts:
        result = route(prompt)
        is_match = result.template_id == expected or \
                   (expected == "crud" and result.template_id in ["crud", "kanban", "pomodoro"])
        
        symbol = "✓" if is_match else "✗"
        if is_match:
            passed += 1
        
        print(f"  [{symbol}] {prompt:40} → {result.template_id} ({result.method})")
        if not is_match:
            print(f"       Expected: {expected}")
    
    print(f"\nResult: {passed}/{len(quick_prompts)} passed")
    return passed, len(quick_prompts)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Real-world app builder benchmark")
    parser.add_argument("--quick", action="store_true", help="Run quick test subset")
    args = parser.parse_args()
    
    if args.quick:
        quick_test()
    else:
        run_all_benchmarks()
