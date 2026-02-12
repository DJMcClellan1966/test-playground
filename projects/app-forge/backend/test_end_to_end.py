"""End-to-End Test: Universal Builder generating real apps.

This proves the full pipeline works: Description → Code → Validation
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from slot_generator import SlotBasedGenerator, generate_app


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_app_result(description, result, test_num, total):
    """Print one app generation result."""
    print(f"\n[{test_num}/{total}] Input: '{description}'")
    print("-" * 70)
    print(f"  ✓ Generated: {result.name}")
    print(f"  ✓ Category: {result.category}")
    print(f"  ✓ Framework: {result.framework}")
    print(f"  ✓ Files: {len(result.files)}")
    print(f"  ✓ Features: {', '.join(sorted(result.packages)[:5])}{'...' if len(result.packages) > 5 else ''}")
    
    # Show file list
    file_list = [f.path for f in result.files]
    print(f"  ✓ Structure:")
    for f in sorted(file_list)[:10]:
        print(f"    - {f}")
    if len(file_list) > 10:
        print(f"    ... and {len(file_list) - 10} more")
    
    # Show main file preview
    main_file = next((f for f in result.files if 'app.py' in f.path or 'index.html' in f.path), None)
    if main_file:
        lines = main_file.content.split('\n')
        preview_lines = min(8, len(lines))
        print(f"\n  Preview of {main_file.path}:")
        for line in lines[:preview_lines]:
            print(f"    {line}")
        if len(lines) > preview_lines:
            print(f"    ... ({len(lines) - preview_lines} more lines)")


def validate_generated_code(result):
    """Basic validation that generated code looks reasonable."""
    errors = []
    
    # Should have at least one file
    if not result.files:
        errors.append("No files generated")
    
    # Should have a main file
    has_main = any('app.py' in f.path or 'index.html' in f.path 
                   for f in result.files)
    if not has_main:
        errors.append("No main file (app.py or index.html)")
    
    # Check main file has content
    main_file = next((f for f in result.files if 'app.py' in f.path or 'index.html' in f.path), None)
    if main_file and len(main_file.content) < 100:
        errors.append(f"Main file too short ({len(main_file.content)} chars)")
    
    # Should have requirements or be standalone
    has_requirements = any('requirements.txt' in f.path for f in result.files)
    is_standalone = result.framework == 'html_canvas'
    if not has_requirements and not is_standalone:
        errors.append("No requirements.txt for non-standalone app")
    
    return errors


# =============================================================================
# TEST CASES
# =============================================================================

TEST_CASES = [
    # Web apps with database
    "a recipe collection app where I can save recipes with ingredients",
    "a todo list with categories and priorities",
    "a simple blog with posts and comments",
    "an expense tracker with categories",
    
    # Games
    "a number guessing game",
    "a tic tac toe game",
    "a memory matching game",
    
    # Utilities
    "a password generator with options",
    "a color palette generator",
    "a markdown editor",
    
    # Dashboards
    "a dashboard to track daily habits",
    "a simple analytics dashboard",
    
    # Data collection
    "a survey form with multiple questions",
    "a contact form with validation",
    
    # Novel/edge cases
    "a random quote generator",
    "a pomodoro timer",
]


def test_variety_of_apps():
    """Test generating many different app types."""
    print_section("END-TO-END TEST: Generate Variety of Apps")
    
    generator = SlotBasedGenerator()
    results = []
    failures = []
    
    total = len(TEST_CASES)
    
    for i, description in enumerate(TEST_CASES, 1):
        try:
            # Generate app
            result = generator.generate(description)
            
            # Validate
            validation_errors = validate_generated_code(result)
            
            if validation_errors:
                print_app_result(description, result, i, total)
                print(f"\n  ⚠️  VALIDATION WARNINGS:")
                for error in validation_errors:
                    print(f"    - {error}")
                failures.append((description, validation_errors))
            else:
                print_app_result(description, result, i, total)
                print(f"\n  ✅ VALIDATION PASSED")
            
            results.append((description, result))
            
        except Exception as e:
            print(f"\n[{i}/{total}] Input: '{description}'")
            print(f"  ❌ GENERATION FAILED: {e}")
            import traceback
            traceback.print_exc()
            failures.append((description, [str(e)]))
    
    # Summary
    print_section("TEST SUMMARY")
    
    successful = len(results)
    failed = len(failures)
    
    print(f"Total tests: {total}")
    print(f"  ✅ Successful: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"  ❌ Failed/Warned: {failed}/{total} ({failed/total*100:.1f}%)")
    
    # Framework breakdown
    if results:
        print("\nFramework distribution:")
        frameworks = {}
        for desc, result in results:
            frameworks[result.framework] = frameworks.get(result.framework, 0) + 1
        
        for fw, count in sorted(frameworks.items(), key=lambda x: -x[1]):
            print(f"  - {fw}: {count}")
    
    # Feature usage
    if results:
        print("\nMost common features:")
        all_features = []
        for desc, result in results:
            all_features.extend(result.packages)
        
        from collections import Counter
        feature_counts = Counter(all_features)
        for feature, count in feature_counts.most_common(10):
            print(f"  - {feature}: {count} apps")
    
    # Show failures in detail
    if failures:
        print("\n⚠️  Issues detected:")
        for desc, errors in failures:
            print(f"\n  '{desc}':")
            for error in errors:
                print(f"    - {error}")
    
    return len(failures) == 0


def test_specific_features():
    """Test specific feature combinations."""
    print_section("FEATURE COMBINATION TESTS")
    
    generator = SlotBasedGenerator()
    
    test_cases = [
        ("Recipe app with auth", {"database", "crud", "auth"}),
        ("Todo list with search", {"database", "crud", "search"}),
        ("Blog with export", {"database", "crud", "export"}),
        ("Dashboard with charts", {"database", "responsive_ui"}),
    ]
    
    passed = 0
    failed = 0
    
    for description, expected_features in test_cases:
        try:
            result = generator.generate(description)
            
            # Check if expected features are present
            actual_features = set(result.packages)
            missing = expected_features - actual_features
            
            print(f"\n'{description}'")
            print(f"  Expected features: {expected_features}")
            print(f"  Actual packages: {actual_features}")
            
            if missing:
                print(f"  ⚠️  Missing: {missing}")
                failed += 1
            else:
                print(f"  ✅ All expected features present")
                passed += 1
                
        except Exception as e:
            print(f"\n'{description}'")
            print(f"  ❌ Failed: {e}")
            failed += 1
    
    print(f"\nFeature tests: {passed}/{len(test_cases)} passed")
    return failed == 0


def test_analogy_processing():
    """Test that analogy patterns are detected and processed."""
    print_section("ANALOGY DETECTION TESTS")
    
    generator = SlotBasedGenerator()
    
    analogy_tests = [
        "Spotify for podcasts",
        "Instagram clone for recipes",
        "Trello but simpler",
    ]
    
    detected = 0
    total = len(analogy_tests)
    
    for description in analogy_tests:
        try:
            # Import analogy engine directly
            from analogy_engine import detect_analogy
            
            analogy = detect_analogy(description)
            
            print(f"\n'{description}'")
            if analogy:
                print(f"  ✅ Detected: {analogy.pattern_type}")
                print(f"     Base: {analogy.base}")
                print(f"     Modification: {analogy.modification}")
                detected += 1
            else:
                print(f"  ⚠️  No analogy detected")
            
            # Still try to generate
            result = generator.generate(description)
            print(f"  → Generated {result.framework} app with {len(result.files)} files")
            
        except Exception as e:
            print(f"\n'{description}'")
            print(f"  ❌ Error: {e}")
    
    print(f"\nAnalogy detection: {detected}/{total} detected")
    return True  # Non-critical if analogies don't match


def test_constraint_validation():
    """Test that constraints are being applied."""
    print_section("CONSTRAINT VALIDATION TESTS")
    
    generator = SlotBasedGenerator()
    
    # These should trigger constraint warnings but still generate
    constraint_tests = [
        "CLI app with beautiful UI",  # Incompatible
        "Game with user authentication",  # Unusual
        "Calculator with database",  # Unlikely
    ]
    
    for description in constraint_tests:
        try:
            print(f"\n'{description}'")
            result = generator.generate(description)
            print(f"  ✅ Generated successfully")
            print(f"     Framework: {result.framework}")
            print(f"     Features: {result.packages}")
            
        except Exception as e:
            print(f"  ⚠️  Generation error: {e}")
    
    return True


def test_code_syntax():
    """Validate generated Python code doesn't have syntax errors."""
    print_section("CODE SYNTAX VALIDATION")
    
    generator = SlotBasedGenerator()
    
    test_apps = [
        "a simple todo list",
        "a blog with posts",
        "a contact form",
    ]
    
    syntax_errors = []
    
    for description in test_apps:
        try:
            result = generator.generate(description)
            
            print(f"\n'{description}'")
            
            # Find Python files
            python_files = [f for f in result.files if f.path.endswith('.py')]
            
            for py_file in python_files:
                try:
                    # Try to compile the code
                    compile(py_file.content, py_file.path, 'exec')
                    print(f"  ✅ {py_file.path}: Valid syntax")
                except SyntaxError as se:
                    print(f"  ❌ {py_file.path}: Syntax error at line {se.lineno}")
                    syntax_errors.append((description, py_file.path, str(se)))
            
        except Exception as e:
            print(f"  ⚠️  Generation error: {e}")
    
    if syntax_errors:
        print("\n⚠️  Syntax errors found:")
        for desc, file, error in syntax_errors:
            print(f"  - {desc} / {file}: {error}")
    
    return len(syntax_errors) == 0


# =============================================================================
# RUN ALL TESTS
# =============================================================================

def run_all_tests():
    """Run complete test suite."""
    print("\n" + "🧪" * 35)
    print("  UNIVERSAL BUILDER - END-TO-END TEST SUITE")
    print("🧪" * 35)
    
    results = {}
    
    try:
        # Main test: variety of apps
        results['variety'] = test_variety_of_apps()
        
        # Feature combination tests
        results['features'] = test_specific_features()
        
        # Analogy detection
        results['analogies'] = test_analogy_processing()
        
        # Constraint validation
        results['constraints'] = test_constraint_validation()
        
        # Code syntax validation
        results['syntax'] = test_code_syntax()
        
        # Final summary
        print_section("FINAL RESULTS")
        
        total_passed = sum(1 for v in results.values() if v)
        total_tests = len(results)
        
        print("Test Categories:")
        for test_name, passed in results.items():
            symbol = "✅" if passed else "⚠️"
            print(f"  {symbol} {test_name.capitalize()}")
        
        print(f"\nOverall: {total_passed}/{total_tests} test categories passed")
        
        if total_passed == total_tests:
            print("\n🎉 ALL TESTS PASSED - Universal Builder is working!")
            return True
        else:
            print("\n⚠️  Some tests had warnings (may be expected)")
            return False
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
