"""Integration test for the Universal App Builder.

Tests the complete pipeline:
  Description → Category → Framework → Components → Files
"""

import sys
sys.path.insert(0, '.')

from universal_builder import (
    universal_builder, build_app, get_questions, categorize,
    AppCategory, Project
)

# Import registries to trigger registration
import category_registry
import component_library
import framework_registry


def test_categorization():
    """Test that descriptions are correctly categorized."""
    print("\n" + "=" * 60)
    print("TEST: Category Detection")
    print("=" * 60)
    
    tests = [
        ("a recipe collection app", AppCategory.DATA_APP),
        ("snake game", AppCategory.GAME),
        ("REST API for users", AppCategory.API_SERVICE),
        ("ML model for predictions", AppCategory.ML_PIPELINE),
        ("CLI tool for files", AppCategory.CLI_TOOL),
        ("web scraper bot", AppCategory.AUTOMATION),
    ]
    
    passed = 0
    for desc, expected in tests:
        actual = categorize(desc)
        status = "✓" if actual == expected else "✗"
        if actual == expected:
            passed += 1
        print(f"  {status} '{desc}' → {actual.value} (expected: {expected.value})")
    
    print(f"\n  {passed}/{len(tests)} passed")
    return passed == len(tests)


def test_question_generation():
    """Test that appropriate questions are generated."""
    print("\n" + "=" * 60)
    print("TEST: Question Generation")
    print("=" * 60)
    
    tests = [
        ("recipe app", ["needs_auth", "search"]),  # Data app questions
        ("snake game", ["game_type", "multiplayer"]),  # Game questions
        ("REST API", ["api_style", "auth_type"]),  # API questions
    ]
    
    passed = 0
    for desc, expected_ids in tests:
        questions = get_questions(desc)
        q_ids = [q.id for q in questions]
        
        has_expected = all(eid in q_ids for eid in expected_ids)
        status = "✓" if has_expected else "✗"
        if has_expected:
            passed += 1
        
        print(f"  {status} '{desc}' → {len(questions)} questions")
        print(f"      IDs: {q_ids[:5]}{'...' if len(q_ids) > 5 else ''}")
    
    print(f"\n  {passed}/{len(tests)} passed")
    return passed == len(tests)


def test_constraint_propagation():
    """Test that constraints propagate correctly."""
    print("\n" + "=" * 60)
    print("TEST: Constraint Propagation")
    print("=" * 60)
    
    from universal_builder import ConstraintSolver
    solver = ConstraintSolver()
    
    tests = [
        ({"multi_user": True}, {"multi_user", "needs_auth", "has_data"}),
        ({"needs_auth": True}, {"needs_auth", "has_data"}),
        ({"ml_features": True}, {"ml_features", "has_data", "python_preferred"}),
    ]
    
    passed = 0
    for input_answers, expected_keys in tests:
        result = solver.propagate(input_answers)
        
        has_all = all(k in result for k in expected_keys)
        status = "✓" if has_all else "✗"
        if has_all:
            passed += 1
        
        print(f"  {status} {input_answers} → {dict(result)}")
    
    print(f"\n  {passed}/{len(tests)} passed")
    return passed == len(tests)


def test_component_selection():
    """Test that components are selected correctly."""
    print("\n" + "=" * 60)
    print("TEST: Component Selection")
    print("=" * 60)
    
    from template_registry import extract_features
    
    tests = [
        ("recipe app with login", ["crud", "auth"]),
        ("game with scoring", ["game_loop"]),  # Basic game components
        ("API with search", ["endpoints", "search"]),
    ]
    
    passed = 0
    for desc, expected_comps in tests:
        category = categorize(desc)
        features = extract_features(desc)
        
        # Simulate some answers
        answers = {"has_data": True, "needs_auth": "login" in desc}
        if "leaderboard" in desc:
            answers["leaderboard"] = True
        if "search" in desc:
            answers["search"] = True
        
        components = universal_builder.select_components(category, answers, features)
        comp_ids = [c.id for c in components]
        
        has_expected = all(ec in comp_ids for ec in expected_comps)
        status = "✓" if has_expected else "✗"
        if has_expected:
            passed += 1
        
        print(f"  {status} '{desc}' → {comp_ids}")
    
    print(f"\n  {passed}/{len(tests)} passed")
    return passed == len(tests)


def test_full_build():
    """Test full app generation."""
    print("\n" + "=" * 60)
    print("TEST: Full App Generation")
    print("=" * 60)
    
    tests = [
        {
            "description": "a todo list app",
            "answers": {"has_data": True, "needs_auth": False},
            "expected_files": ["app.py", "requirements.txt"],
        },
        {
            "description": "a snake game",
            "answers": {},
            "expected_files": ["index.html"],
        },
        {
            "description": "a CLI converter tool",
            "answers": {"subcommands": "No"},
            "expected_files": ["cli.py", "requirements.txt"],
        },
    ]
    
    passed = 0
    for test in tests:
        try:
            project = build_app(test["description"], test["answers"])
            file_paths = [f.path for f in project.files]
            
            has_expected = all(ef in file_paths for ef in test["expected_files"])
            status = "✓" if has_expected else "✗"
            if has_expected:
                passed += 1
            
            print(f"  {status} '{test['description']}'")
            print(f"      Category: {project.category.value}")
            print(f"      Framework: {project.framework}")
            print(f"      Files: {file_paths}")
            print(f"      Run: {project.run_command}")
            
        except Exception as e:
            print(f"  ✗ '{test['description']}' - ERROR: {e}")
    
    print(f"\n  {passed}/{len(tests)} passed")
    return passed == len(tests)


def test_file_content():
    """Test that generated file content is valid."""
    print("\n" + "=" * 60)
    print("TEST: File Content Validation")
    print("=" * 60)
    
    tests = [
        {
            "description": "recipe app",
            "answers": {"has_data": True},
            "checks": [
                ("app.py", "Flask", "Has Flask import"),
                ("app.py", "def ", "Has function definitions"),
            ],
        },
        {
            "description": "snake game",
            "answers": {},
            "checks": [
                ("index.html", "<canvas", "Has canvas element"),
                ("index.html", "gameLoop", "Has game loop"),
            ],
        },
    ]
    
    passed = 0
    total = 0
    
    for test in tests:
        project = build_app(test["description"], test["answers"])
        files_dict = {f.path: f.content for f in project.files}
        
        for filename, check_str, check_desc in test["checks"]:
            total += 1
            if filename in files_dict and check_str in files_dict[filename]:
                passed += 1
                print(f"  ✓ {check_desc} in {filename}")
            else:
                print(f"  ✗ {check_desc} in {filename}")
    
    print(f"\n  {passed}/{total} checks passed")
    return passed == total


def test_kernel_composer():
    """Test kernel composer for algorithm apps."""
    print("\n" + "=" * 60)
    print("TEST: Kernel Composer")
    print("=" * 60)
    
    # Import the slot generator which has kernel composer
    from slot_generator import generate_app
    
    # These should use the kernel composer
    kernel_apps = [
        ("Conway's Game of Life", "kernel:grid2d", "Grid2D"),
        ("a pathfinding visualizer", "kernel:graph", "Graph"),
        ("particle physics simulation", "kernel:particles", "Particles"),
        ("sorting algorithm visualizer", "kernel:sequence", "Sequence"),
    ]
    
    # These should NOT use the kernel composer
    template_apps = [
        "a recipe app",
        "a todo list",
        "REST API for users",
    ]
    
    passed = 0
    total = len(kernel_apps) + len(template_apps)
    
    for desc, expected_trait, expected_prim in kernel_apps:
        project = generate_app(desc, {})
        if project.trait_id and project.trait_id.startswith("kernel:"):
            passed += 1
            print(f"  ✓ '{desc}' → {project.trait_id} ({expected_prim})")
        else:
            print(f"  ✗ '{desc}' expected {expected_trait}, got {project.trait_id}")
    
    for desc in template_apps:
        project = generate_app(desc, {})
        if not project.trait_id or not project.trait_id.startswith("kernel:"):
            passed += 1
            print(f"  ✓ '{desc}' → {project.trait_id} (template, not kernel)")
        else:
            print(f"  ✗ '{desc}' should use templates, got {project.trait_id}")
    
    print(f"\n  {passed}/{total} passed")
    return passed == total


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("UNIVERSAL APP BUILDER - INTEGRATION TESTS")
    print("=" * 60)
    
    results = {
        "Categorization": test_categorization(),
        "Question Generation": test_question_generation(),
        "Constraint Propagation": test_constraint_propagation(),
        "Component Selection": test_component_selection(),
        "Full Build": test_full_build(),
        "File Content": test_file_content(),
        "Kernel Composer": test_kernel_composer(),
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
