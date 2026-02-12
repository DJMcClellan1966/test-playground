"""
TEST: AI Assistant Prompts
Real-world prompts that users would typically send to an AI assistant.
Tests how the universal builder handles natural, conversational requests.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from slot_generator import SlotBasedGenerator


def print_separator(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_prompt(description, expected_type=None):
    """Test a single AI-style prompt."""
    print(f"\n🤖 User prompt: '{description}'")
    
    try:
        generator = SlotBasedGenerator()
        result = generator.generate(description)
        
        print(f"   ✅ Generated: {result.name}")
        print(f"      Category: {result.category}")
        print(f"      Framework: {result.framework}")
        print(f"      Files: {len(result.files)}")
        
        # Check if it matched expectation
        if expected_type:
            if expected_type.lower() in result.category.lower() or expected_type.lower() in result.framework.lower():
                print(f"      🎯 Correctly identified as {expected_type}!")
                return True, True
            else:
                print(f"      ⚠️  Expected {expected_type}, got {result.category}/{result.framework}")
                return True, False
        
        return True, True
        
    except Exception as e:
        print(f"   💥 CRASHED: {e}")
        return False, False


def run_ai_prompt_tests():
    """Test prompts that mimic real AI assistant interactions."""
    
    print("🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖")
    print("  TEST: How Well Does the Builder Understand AI-Style Prompts?")
    print("🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖")
    
    results = {"success": 0, "correct": 0, "total": 0}
    
    # ==================== CONVERSATIONAL REQUESTS ====================
    print_separator("CONVERSATIONAL REQUESTS (How users actually talk)")
    
    conversational = [
        ("Can you make me a simple todo app?", "todo"),
        ("I need something to track my expenses", "expense"),
        ("Help me build a recipe organizer", "recipe"),
        ("Create a game for me please", "game"),
        ("Build me a blog", "blog"),
        ("I want to make a calculator", "calculator"),
        ("Could you create a timer?", "timer"),
        ("Make a note taking app", "note"),
    ]
    
    for prompt, expected in conversational:
        results["total"] += 1
        success, correct = test_prompt(prompt, expected)
        if success:
            results["success"] += 1
        if correct:
            results["correct"] += 1
    
    # ==================== VAGUE BUT COMMON ====================
    print_separator("VAGUE BUT COMMON (Minimal info prompts)")
    
    vague = [
        ("todo app", "todo"),
        ("recipe app", "recipe"),
        ("game", "game"),
        ("blog", "blog"),
        ("calculator", "calculator"),
        ("timer", None),
        ("notes", None),
        ("budget tracker", None),
    ]
    
    for prompt, expected in vague:
        results["total"] += 1
        success, correct = test_prompt(prompt, expected)
        if success:
            results["success"] += 1
        if correct:
            results["correct"] += 1
    
    # ==================== DETAILED REQUIREMENTS ====================
    print_separator("DETAILED REQUIREMENTS (Specific prompts)")
    
    detailed = [
        ("I want a recipe app where I can add recipes with ingredients, cooking time, and difficulty level. I should be able to search recipes and organize them by category.", "recipe"),
        ("Build me a task manager with priorities, due dates, categories, and the ability to mark tasks complete. Include search functionality.", "todo"),
        ("Create a personal finance tracker that lets me log expenses, categorize them, set budgets, and see spending charts", "expense"),
        ("I need a simple game where the player guesses a number between 1 and 100", "game"),
        ("Make a blog platform where I can write posts, add tags, and let readers leave comments", "blog"),
    ]
    
    for prompt, expected in detailed:
        results["total"] += 1
        success, correct = test_prompt(prompt, expected)
        if success:
            results["success"] += 1
        if correct:
            results["correct"] += 1
    
    # ==================== FOLLOW-UP STYLE ====================
    print_separator("FOLLOW-UP STYLE (Context-dependent)")
    
    followup = [
        ("like the last one but with user accounts", None),
        ("same thing but for movies", None),
        ("add search to that", None),
        ("now make it mobile friendly", None),
        ("but without a database", None),
    ]
    
    for prompt, expected in followup:
        results["total"] += 1
        success, correct = test_prompt(prompt, expected)
        if success:
            results["success"] += 1
        if correct:
            results["correct"] += 1
    
    # ==================== ANALOGY-BASED ====================
    print_separator("ANALOGY-BASED (X for Y style)")
    
    analogies = [
        ("Spotify for podcasts", None),
        ("Instagram but for recipes", "recipe"),
        ("Trello clone", None),
        ("Netflix for books", None),
        ("Uber for food delivery", None),
        ("like Pinterest but for code snippets", None),
        ("Goodreads clone for movies", None),
    ]
    
    for prompt, expected in analogies:
        results["total"] += 1
        success, correct = test_prompt(prompt, expected)
        if success:
            results["success"] += 1
        if correct:
            results["correct"] += 1
    
    # ==================== PROBLEM-FOCUSED ====================
    print_separator("PROBLEM-FOCUSED (Describe the problem, not solution)")
    
    problems = [
        ("I keep forgetting what groceries to buy", None),
        ("I can never remember my passwords", None),
        ("I need to track how much water I drink", None),
        ("My recipes are scattered everywhere", "recipe"),
        ("I want to learn new vocabulary", None),
        ("I need to split bills with roommates", None),
    ]
    
    for prompt, expected in problems:
        results["total"] += 1
        success, correct = test_prompt(prompt, expected)
        if success:
            results["success"] += 1
        if correct:
            results["correct"] += 1
    
    # ==================== MULTI-FEATURE ====================
    print_separator("MULTI-FEATURE (Kitchen sink requests)")
    
    multi = [
        ("Build a full-stack web app with user authentication, database, REST API, search, pagination, export to CSV, dark mode, and responsive design", None),
        ("Create an app that combines todo lists, notes, calendar, and reminders all in one", "todo"),
        ("I want a social media app with profiles, posts, comments, likes, follows, messaging, and notifications", None),
    ]
    
    for prompt, expected in multi:
        results["total"] += 1
        success, correct = test_prompt(prompt, expected)
        if success:
            results["success"] += 1
        if correct:
            results["correct"] += 1
    
    # ==================== TYPOS AND INFORMAL ====================
    print_separator("TYPOS & INFORMAL (Real user input)")
    
    informal = [
        ("todoo app plz", "todo"),
        ("recipie organiser", "recipe"),
        ("calculater", "calculator"),
        ("gimme a game", "game"),
        ("make blog thing", "blog"),
        ("i want 2 track my workouts", None),
    ]
    
    for prompt, expected in informal:
        results["total"] += 1
        success, correct = test_prompt(prompt, expected)
        if success:
            results["success"] += 1
        if correct:
            results["correct"] += 1
    
    # ==================== RESULTS ====================
    print_separator("TEST RESULTS")
    
    print(f"\nTotal prompts tested: {results['total']}")
    print(f"  ✅ Successfully generated: {results['success']}/{results['total']} ({results['success']/results['total']*100:.1f}%)")
    print(f"  🎯 Correctly categorized: {results['correct']}/{results['total']} ({results['correct']/results['total']*100:.1f}%)")
    
    crash_rate = 1 - (results['success'] / results['total'])
    
    print("\n" + "="*70)
    
    if crash_rate == 0 and results['correct'] / results['total'] > 0.8:
        print("🏆 EXCELLENT: No crashes + high accuracy!")
        return 0
    elif crash_rate == 0:
        print("✅ GOOD: No crashes (accuracy could improve)")
        return 0
    elif crash_rate < 0.1:
        print("⚠️  FAIR: Some issues detected")
        return 1
    else:
        print("❌ POOR: Multiple failures")
        return 1


if __name__ == "__main__":
    exit_code = run_ai_prompt_tests()
    sys.exit(exit_code)
