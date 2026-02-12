"""
STRESS TEST: Try to Break the Universal Builder
Tests edge cases, contradictions, nonsense, and extreme scenarios.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from slot_generator import SlotBasedGenerator


def print_separator(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_case(description, test_name):
    """Run a single test case and catch errors."""
    print(f"\n🔥 {test_name}")
    print(f"   Input: '{description}'")
    
    try:
        generator = SlotBasedGenerator()
        result = generator.generate(description)
        
        print(f"   ✅ Generated: {result.name}")
        print(f"      Framework: {result.framework}")
        print(f"      Files: {len(result.files)}")
        print(f"      Category: {result.category}")
        
        # Check for potential issues
        warnings = []
        if len(result.files) == 0:
            warnings.append("NO FILES GENERATED")
        if not result.run_command:
            warnings.append("NO RUN COMMAND")
        if result.framework == "unknown":
            warnings.append("UNKNOWN FRAMEWORK")
            
        if warnings:
            print(f"   ⚠️  Issues: {', '.join(warnings)}")
        
        return True, None
        
    except Exception as e:
        print(f"   💥 CRASHED: {type(e).__name__}: {e}")
        return False, str(e)


def run_stress_tests():
    """Run comprehensive stress tests."""
    
    print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
    print("  UNIVERSAL BUILDER - STRESS TEST (TRY TO BREAK IT)")
    print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
    
    results = {"passed": 0, "failed": 0, "crashed": 0}
    crashes = []
    
    # ==================== CONTRADICTIONS ====================
    print_separator("CONTRADICTORY REQUIREMENTS")
    
    contradictions = [
        ("a CLI app with a beautiful graphical user interface", "CLI + GUI conflict"),
        ("a single page with multiple pages and navigation", "Single + Multiple pages"),
        ("a real-time multiplayer game for one player only", "Multiplayer + Solo"),
        ("a database-free app that stores user data permanently", "No DB + Persistent storage"),
        ("a static website with dynamic user authentication", "Static + Auth"),
        ("a read-only app where users can edit and delete items", "Read-only + CRUD"),
        ("a simple minimalist app with 50 complex features", "Simple + Complex"),
        ("a text-only app with video streaming", "Text-only + Video"),
    ]
    
    for desc, name in contradictions:
        success, error = test_case(desc, name)
        if success:
            results["passed"] += 1
        elif error:
            results["crashed"] += 1
            crashes.append((name, error))
        else:
            results["failed"] += 1
    
    # ==================== NONSENSE / GIBBERISH ====================
    print_separator("NONSENSE & GIBBERISH")
    
    nonsense = [
        ("asdf jkl; qwer tyuiop", "Random keyboard mashing"),
        ("", "Empty string"),
        ("          ", "Only whitespace"),
        ("a a a a a a a a a a", "Repeated word"),
        ("🎨🎮🎪🎭🎬🎯", "Only emojis"),
        ("app", "Single word"),
        ("make me rich", "Unrealistic goal"),
        ("something cool", "Extremely vague"),
    ]
    
    for desc, name in nonsense:
        success, error = test_case(desc, name)
        if success:
            results["passed"] += 1
        elif error:
            results["crashed"] += 1
            crashes.append((name, error))
        else:
            results["failed"] += 1
    
    # ==================== EXTREME COMPLEXITY ====================
    print_separator("EXTREME COMPLEXITY")
    
    complex_tests = [
        ("a social network with user profiles, posts, comments, likes, shares, messaging, groups, events, photo albums, video uploads, live streaming, stories, marketplace, job listings, dating features, gaming integration, and AR filters", 
         "Kitchen sink - 15+ features"),
        
        ("a recipe app for cooking blog todo list expense tracker game dashboard calendar notes timer calculator converter", 
         "Multiple apps mashed together"),
        
        ("an enterprise-grade microservices-based distributed cloud-native serverless event-driven CQRS event-sourced blockchain-enabled AI-powered machine learning real-time analytics big data processing system", 
         "Buzzword overload"),
    ]
    
    for desc, name in complex_tests:
        success, error = test_case(desc, name)
        if success:
            results["passed"] += 1
        elif error:
            results["crashed"] += 1
            crashes.append((name, error))
        else:
            results["failed"] += 1
    
    # ==================== UNUSUAL LANGUAGES / FORMATS ====================
    print_separator("UNUSUAL INPUT FORMATS")
    
    unusual = [
        ("CREATE TABLE apps (name VARCHAR(255), description TEXT);", "SQL injection attempt"),
        ("<script>alert('xss')</script>", "XSS attempt"),
        ("'; DROP TABLE users; --", "SQL injection classic"),
        ("../../../etc/passwd", "Path traversal"),
        ("A"*10000, "Extremely long input"),
        ("una aplicación de recetas en español", "Spanish language"),
        ("レシピアプリ", "Japanese characters"),
        ("app\nwith\nnewlines\nand\ttabs", "Special characters"),
    ]
    
    for desc, name in unusual:
        success, error = test_case(desc, name)
        if success:
            results["passed"] += 1
        elif error:
            results["crashed"] += 1
            crashes.append((name, error))
        else:
            results["failed"] += 1
    
    # ==================== IMPOSSIBLE REQUESTS ====================
    print_separator("IMPOSSIBLE / UNREALISTIC REQUESTS")
    
    impossible = [
        ("a time machine that lets me travel to the past", "Literally impossible"),
        ("an app that reads minds and predicts the future perfectly", "Sci-fi features"),
        ("a free app that makes me a millionaire instantly", "Get rich quick"),
        ("build me Windows 11", "Entire OS request"),
        ("create artificial general intelligence", "AGI request"),
        ("a game better than GTA 6 with better graphics", "AAA game request"),
        ("quantum computer simulator running on pocket calculator", "Hardware impossible"),
    ]
    
    for desc, name in impossible:
        success, error = test_case(desc, name)
        if success:
            results["passed"] += 1
        elif error:
            results["crashed"] += 1
            crashes.append((name, error))
        else:
            results["failed"] += 1
    
    # ==================== AMBIGUOUS / UNCLEAR ====================
    print_separator("AMBIGUOUS & UNCLEAR")
    
    ambiguous = [
        ("thing", "Ultra vague"),
        ("you know what I mean", "Assumes context"),
        ("like that other app but different", "Vague comparison"),
        ("the usual", "No information"),
        ("app thingy stuff", "Meaningless filler words"),
        ("it does things", "No specifics"),
        ("make it work", "No description"),
    ]
    
    for desc, name in ambiguous:
        success, error = test_case(desc, name)
        if success:
            results["passed"] += 1
        elif error:
            results["crashed"] += 1
            crashes.append((name, error))
        else:
            results["failed"] += 1
    
    # ==================== EDGE CASE FRAMEWORKS ====================
    print_separator("FRAMEWORK EDGE CASES")
    
    framework_edge = [
        ("a game that needs user login and database", "Game + Auth conflict"),
        ("a CLI todo list with drag and drop UI", "CLI + Drag-drop"),
        ("a REST API with HTML canvas graphics", "API + Canvas"),
        ("a calculator that needs a database of calculations", "Calculator + DB odd combo"),
        ("a timer with user accounts and social features", "Timer + Social"),
    ]
    
    for desc, name in framework_edge:
        success, error = test_case(desc, name)
        if success:
            results["passed"] += 1
        elif error:
            results["crashed"] += 1
            crashes.append((name, error))
        else:
            results["failed"] += 1
    
    # ==================== RESULTS ====================
    print_separator("STRESS TEST RESULTS")
    
    total = results["passed"] + results["failed"] + results["crashed"]
    
    print(f"\nTotal tests: {total}")
    print(f"  ✅ Handled gracefully: {results['passed']}/{total} ({results['passed']/total*100:.1f}%)")
    print(f"  ⚠️  Failed generation: {results['failed']}/{total} ({results['failed']/total*100:.1f}%)")
    print(f"  💥 CRASHED: {results['crashed']}/{total} ({results['crashed']/total*100:.1f}%)")
    
    if crashes:
        print("\n🚨 CRASHES FOUND:")
        for name, error in crashes:
            print(f"  - {name}")
            print(f"    {error[:100]}...")
    else:
        print("\n🎉 NO CRASHES! System is robust!")
    
    print("\n" + "="*70)
    
    # Determine pass/fail
    crash_rate = results['crashed'] / total
    if crash_rate == 0:
        print("🏆 EXCELLENT: No crashes at all!")
        return 0
    elif crash_rate < 0.1:
        print("✅ GOOD: Less than 10% crash rate")
        return 0
    elif crash_rate < 0.3:
        print("⚠️  FAIR: 10-30% crash rate - needs improvement")
        return 1
    else:
        print("❌ POOR: Over 30% crash rate - major issues")
        return 1


if __name__ == "__main__":
    exit_code = run_stress_tests()
    sys.exit(exit_code)
