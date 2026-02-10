"""
Rigorous Test Suite for the Intelligent Scaffolding System

Goes beyond basic unit tests to include:
1. Property-based testing (constraint soundness)
2. Bidirectional round-trip verification
3. Generated code validity (syntax checks)
4. End-to-end pipeline tests
5. Fuzz testing (malformed inputs)
6. Snapshot/golden file tests
7. Performance tests
"""

import unittest
import tempfile
import shutil
import time
import random
import string
import py_compile
import ast
from pathlib import Path
from typing import Dict, List, Any, Set
import json

# Import our systems
from constraint_solver import ConstraintSolver, Rule, Constraint, Certainty, RULES
from blocks import Block, Port, BlockAssembler, BLOCKS
from contracts import Contract, Field, ContractRegistry
from intelligent_scaffold import IntelligentScaffolder


# ============================================================================
# PROPERTY-BASED TESTS: Constraint Soundness
# ============================================================================

class TestConstraintSoundness(unittest.TestCase):
    """Test that constraints behave correctly under all conditions."""
    
    def test_no_contradictory_rules(self):
        """Verify no two rules produce contradictory conclusions for same key."""
        # Group rules by their conclusion keys
        conclusions_by_key: Dict[str, List[tuple]] = {}
        
        for rule in RULES:
            for key, value in rule.conclusions.items():
                if key not in conclusions_by_key:
                    conclusions_by_key[key] = []
                conclusions_by_key[key].append((rule.name, rule.conditions, value))
        
        # Check for potential conflicts
        conflicts = []
        for key, entries in conclusions_by_key.items():
            values = set(e[2] for e in entries)
            if len(values) > 1:
                # Multiple values - check if conditions are mutually exclusive
                for i, (name1, cond1, val1) in enumerate(entries):
                    for name2, cond2, val2 in entries[i+1:]:
                        if val1 != val2:
                            # Check if conditions can both be true
                            if self._conditions_compatible(cond1, cond2):
                                conflicts.append(f"{name1} vs {name2} on '{key}': {val1} vs {val2}")
        
        # Allow known intentional conflicts (priority-based resolution)
        # But flag unexpected ones
        self.assertEqual(len(conflicts), 0, 
            f"Found potentially contradictory rules:\n" + "\n".join(conflicts))
    
    def _conditions_compatible(self, cond1: Dict, cond2: Dict) -> bool:
        """Check if two condition sets can both be true simultaneously."""
        for key in set(cond1.keys()) & set(cond2.keys()):
            if cond1[key] != cond2[key]:
                return False  # Mutually exclusive
        return True  # Could both be true
    
    def test_constraint_solving_terminates(self):
        """Verify solving terminates for all constraint combinations."""
        # Test with random constraint combinations
        possible_constraints = [
            ("offline", True),
            ("multi_user", True),
            ("realtime", True),
            ("sensitive_data", True),
            ("scale", "high"),
            ("shared_content", True),
        ]
        
        # Try all subsets up to size 4
        from itertools import combinations
        
        for r in range(len(possible_constraints) + 1):
            for combo in combinations(possible_constraints, r):
                solver = ConstraintSolver()
                for name, value in combo:
                    solver.add_constraint(name, value)
                
                start = time.time()
                solution = solver.solve()
                elapsed = time.time() - start
                
                self.assertLess(elapsed, 1.0, 
                    f"Solving took too long for {combo}: {elapsed:.2f}s")
                self.assertIsInstance(solution, dict)
    
    def test_constraints_are_deterministic(self):
        """Same inputs should always produce same outputs."""
        for _ in range(5):
            solver1 = ConstraintSolver()
            solver1.add_constraints({"offline": True, "multi_user": True})
            result1 = solver1.solve()
            
            solver2 = ConstraintSolver()
            solver2.add_constraints({"offline": True, "multi_user": True})
            result2 = solver2.solve()
            
            self.assertEqual(result1, result2)
    
    def test_priority_ordering_respected(self):
        """Higher priority rules should take precedence."""
        solver = ConstraintSolver()
        solver.add_constraint("offline", True)
        solver.add_constraint("multi_user", True)
        solution = solver.solve()
        
        # Should get CRDT (high priority) not last_write_wins (low priority)
        self.assertEqual(solution.get("sync_strategy"), "crdt")


# ============================================================================
# BIDIRECTIONAL ROUND-TRIP TESTS
# ============================================================================

class TestBidirectionalRoundTrip(unittest.TestCase):
    """Test that spec ↔ code conversions preserve information."""
    
    def test_contract_to_spec_roundtrip(self):
        """Contract → Spec → Contract preserves fields."""
        original = Contract(
            name="Task",
            description="A task entity",
            fields=[
                Field("id", "string", True),
                Field("title", "string", True, constraints=["min:1"]),
                Field("done", "boolean", False, default=False),
            ],
            invariants=["title cannot be empty"],
            relations={"user_id": "belongs_to:User"},
        )
        
        # Convert to spec
        spec_text = original.to_spec()
        
        # Parse back
        registry = ContractRegistry()
        parsed = registry.load_from_spec(spec_text)
        
        # Verify preservation
        self.assertEqual(parsed.name, original.name)
        self.assertEqual(len(parsed.fields), len(original.fields))
        self.assertEqual(len(parsed.invariants), len(original.invariants))
        
        # Check field names preserved
        original_names = {f.name for f in original.fields}
        parsed_names = {f.name for f in parsed.fields}
        self.assertEqual(original_names, parsed_names)
    
    def test_hash_stability(self):
        """Contract hash should be stable across identical definitions."""
        c1 = Contract(name="Widget", fields=[Field("x", "integer", True)])
        c2 = Contract(name="Widget", fields=[Field("x", "integer", True)])
        
        self.assertEqual(c1.compute_hash(), c2.compute_hash())
    
    def test_hash_changes_with_content(self):
        """Contract hash should change when content changes."""
        c1 = Contract(name="Widget", fields=[Field("x", "integer", True)])
        c2 = Contract(name="Widget", fields=[Field("y", "integer", True)])
        
        self.assertNotEqual(c1.compute_hash(), c2.compute_hash())
    
    def test_multiple_field_types_roundtrip(self):
        """Test all field types survive round-trip."""
        types = ["string", "text", "integer", "float", "boolean", "datetime", "list", "dict"]
        
        for field_type in types:
            contract = Contract(
                name="TypeTest",
                fields=[Field("value", field_type, True)],
            )
            
            spec = contract.to_spec()
            registry = ContractRegistry()
            parsed = registry.load_from_spec(spec)
            
            self.assertEqual(parsed.fields[0].type, field_type, 
                f"Type {field_type} not preserved")


# ============================================================================
# GENERATED CODE VALIDITY
# ============================================================================

class TestGeneratedCodeValidity(unittest.TestCase):
    """Test that generated code is syntactically valid."""
    
    def test_python_dataclass_compiles(self):
        """Generated Python dataclass should be valid Python."""
        contract = Contract(
            name="ValidPython",
            fields=[
                Field("id", "string", True),
                Field("count", "integer", True, default=0),
                Field("data", "dict", False),
            ],
            invariants=["count >= 0"],
        )
        
        code = contract.to_python_dataclass()
        
        # Should parse as valid Python AST
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.fail(f"Generated Python has syntax error: {e}\n\nCode:\n{code}")
    
    def test_flask_routes_compile(self):
        """Generated Flask routes should be valid Python."""
        contract = Contract(
            name="ValidFlask",
            fields=[
                Field("id", "string", True),
                Field("name", "string", True),
            ],
        )
        
        routes = contract.to_flask_routes()
        
        try:
            ast.parse(routes)
        except SyntaxError as e:
            self.fail(f"Generated Flask routes have syntax error: {e}\n\nCode:\n{routes}")
    
    def test_all_block_code_compiles(self):
        """All block code templates should be valid Python."""
        for block_id, block in BLOCKS.items():
            if "flask" in block.code:
                code = block.code["flask"]
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    self.fail(f"Block {block_id} has invalid Python: {e}")
    
    def test_generated_project_files_compile(self):
        """Full generated project should have valid Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scaffolder = IntelligentScaffolder(tmpdir)
            scaffolder.understand_requirements(["needs offline"])
            scaffolder.select_components()
            scaffolder.define_entities([
                {"name": "Item", "fields": [{"name": "name", "type": "string"}]}
            ])
            files = scaffolder.generate_project()
            scaffolder.write_files(files)
            
            # Check all .py files compile
            for path in Path(tmpdir).rglob("*.py"):
                try:
                    py_compile.compile(str(path), doraise=True)
                except py_compile.PyCompileError as e:
                    self.fail(f"File {path} failed to compile: {e}")
    
    def test_typescript_syntax_valid(self):
        """Generated TypeScript should have valid syntax (basic check)."""
        contract = Contract(
            name="ValidTS",
            fields=[
                Field("id", "string", True),
                Field("count", "integer", True),
                Field("active", "boolean", False),
            ],
        )
        
        ts_code = contract.to_typescript()
        
        # Basic syntax checks (no full TS parser, but check structure)
        self.assertIn("export interface ValidTS", ts_code)
        self.assertIn("id: string", ts_code)
        self.assertIn("count: number", ts_code)
        self.assertIn("active?: boolean", ts_code)
        
        # Check balanced braces
        self.assertEqual(ts_code.count("{"), ts_code.count("}"))


# ============================================================================
# FUZZ TESTING
# ============================================================================

class TestFuzzInputs(unittest.TestCase):
    """Test system handles malformed and edge-case inputs."""
    
    def test_empty_requirements(self):
        """Empty requirements should not crash."""
        scaffolder = IntelligentScaffolder()
        constraints = scaffolder.understand_requirements([])
        self.assertIsInstance(constraints, dict)
    
    def test_unicode_in_entity_names(self):
        """Unicode entity names should be handled."""
        scaffolder = IntelligentScaffolder()
        scaffolder.define_entities([
            {"name": "Tâche", "fields": [{"name": "título", "type": "string"}]}
        ])
        # Should not crash
        self.assertIn("Tâche", scaffolder.entities)
    
    def test_very_long_field_names(self):
        """Long field names should not crash."""
        long_name = "a" * 500
        contract = Contract(
            name="LongFields",
            fields=[Field(long_name, "string", True)],
        )
        
        # Should generate code without crashing
        code = contract.to_python_dataclass()
        self.assertIn(long_name, code)
    
    def test_special_characters_in_description(self):
        """Special characters in description should not break generation."""
        contract = Contract(
            name="Special",
            description='Contains "quotes", \\backslash, and <html>',
            fields=[Field("x", "string", True)],
        )
        
        code = contract.to_python_dataclass()
        try:
            ast.parse(code)
        except SyntaxError:
            self.fail("Special characters broke Python generation")
    
    def test_sql_injection_in_field_name(self):
        """SQL-like strings in field names should be safe."""
        contract = Contract(
            name="SQLTest",
            fields=[Field("'; DROP TABLE users; --", "string", True)],
        )
        
        # Should still produce code (possibly invalid but not crash)
        code = contract.to_python_dataclass()
        self.assertIsNotNone(code)
    
    def test_many_constraints(self):
        """Many constraints should not cause performance issues."""
        solver = ConstraintSolver()
        
        for i in range(100):
            solver.add_constraint(f"custom_{i}", True)
        
        start = time.time()
        solution = solver.solve()
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 5.0, "Too slow with many constraints")
    
    def test_many_entities(self):
        """Many entities should not cause performance issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scaffolder = IntelligentScaffolder(tmpdir)
            scaffolder.understand_requirements(["offline"])
            scaffolder.select_components()
            
            entities = [
                {"name": f"Entity{i}", "fields": [{"name": "id", "type": "string"}]}
                for i in range(50)
            ]
            
            start = time.time()
            scaffolder.define_entities(entities)
            files = scaffolder.generate_project()
            elapsed = time.time() - start
            
            self.assertLess(elapsed, 10.0, "Too slow with many entities")
            self.assertEqual(len(scaffolder.entities), 50)
    
    def test_empty_entity(self):
        """Entity with no fields should not crash."""
        scaffolder = IntelligentScaffolder()
        scaffolder.define_entities([
            {"name": "Empty", "fields": []}
        ])
        
        files = scaffolder.generate_project()
        self.assertIn("models/empty.py", files)


# ============================================================================
# END-TO-END PIPELINE TESTS
# ============================================================================

class TestEndToEndPipeline(unittest.TestCase):
    """Test complete workflows from requirements to usable project."""
    
    def test_full_pipeline_creates_valid_structure(self):
        """Complete pipeline produces expected file structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scaffolder = IntelligentScaffolder(tmpdir)
            
            # Full workflow
            scaffolder.understand_requirements([
                "needs offline support",
                "multiple users",
                "authentication",
            ])
            scaffolder.select_components()
            scaffolder.define_entities([
                {
                    "name": "Task",
                    "fields": [
                        {"name": "id", "type": "string"},
                        {"name": "title", "type": "string"},
                    ]
                }
            ])
            files = scaffolder.generate_project()
            scaffolder.write_files(files)
            
            # Verify structure
            output = Path(tmpdir)
            self.assertTrue((output / "app.py").exists())
            self.assertTrue((output / "requirements.txt").exists())
            self.assertTrue((output / "models" / "task.py").exists())
            self.assertTrue((output / "routes" / "task_routes.py").exists())
            self.assertTrue((output / "types" / "task.ts").exists())
            self.assertTrue((output / "specs" / "task.spec.md").exists())
    
    def test_project_json_is_valid(self):
        """Generated project.json should be valid JSON with expected keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scaffolder = IntelligentScaffolder(tmpdir)
            scaffolder.understand_requirements(["offline"])
            scaffolder.select_components()
            scaffolder.define_entities([
                {"name": "Note", "fields": [{"name": "text", "type": "text"}]}
            ])
            files = scaffolder.generate_project()
            scaffolder.write_files(files)
            
            project_json = Path(tmpdir) / "project.json"
            with open(project_json) as f:
                data = json.load(f)
            
            self.assertIn("constraints", data)
            self.assertIn("blocks", data)
            self.assertIn("entities", data)
            self.assertIn("stack", data)
    
    def test_requirements_to_blocks_coherence(self):
        """Requirements should lead to appropriate block selection."""
        scaffolder = IntelligentScaffolder()
        
        # Offline + auth requirements
        scaffolder.understand_requirements([
            "needs offline support",
            "requires authentication",
        ])
        blocks = scaffolder.select_components()
        
        block_ids = [b.id for b in blocks]
        
        # Should have sync and auth blocks
        self.assertIn("auth_basic", block_ids)
        self.assertTrue(
            any(b.startswith("storage_") for b in block_ids),
            "Should have storage block"
        )


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance(unittest.TestCase):
    """Test system performance under load."""
    
    def test_constraint_solving_performance(self):
        """Constraint solving should be fast."""
        solver = ConstraintSolver()
        
        # Add all standard constraints
        solver.add_constraints({
            "offline": True,
            "multi_user": True,
            "realtime": True,
            "sensitive_data": True,
            "scale": "high",
            "shared_content": True,
        })
        
        times = []
        for _ in range(10):
            solver2 = ConstraintSolver()
            solver2.constraints = solver.constraints.copy()
            
            start = time.time()
            solver2.solve()
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        self.assertLess(avg_time, 0.1, f"Avg solve time too slow: {avg_time:.4f}s")
    
    def test_contract_generation_performance(self):
        """Contract code generation should be fast."""
        contract = Contract(
            name="BigContract",
            fields=[
                Field(f"field_{i}", "string", True)
                for i in range(50)
            ],
            invariants=[f"field_{i} is required" for i in range(25)],
        )
        
        times = []
        for _ in range(10):
            start = time.time()
            contract.to_python_dataclass()
            contract.to_flask_routes()
            contract.to_typescript()
            contract.to_spec()
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        self.assertLess(avg_time, 0.5, f"Avg generation time too slow: {avg_time:.4f}s")
    
    def test_block_assembly_performance(self):
        """Block assembly should scale well."""
        constraints = {
            "needs_auth": True,
            "sync_strategy": "crdt",
            "storage_type": "local_first",
        }
        
        times = []
        for _ in range(10):
            assembler = BlockAssembler(constraints)
            
            start = time.time()
            assembler.select_blocks()
            assembler.resolve_dependencies()
            assembler.get_code()
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        self.assertLess(avg_time, 0.1, f"Avg assembly time too slow: {avg_time:.4f}s")


# ============================================================================
# SNAPSHOT TESTS (Golden Files)
# ============================================================================

class TestSnapshots(unittest.TestCase):
    """Test that generated code matches expected patterns."""
    
    def test_dataclass_structure(self):
        """Generated dataclass should have expected structure."""
        contract = Contract(
            name="Snapshot",
            description="Test entity",
            fields=[Field("id", "string", True)],
        )
        
        code = contract.to_python_dataclass()
        
        # Required elements
        self.assertIn("@dataclass", code)
        self.assertIn("class Snapshot:", code)
        self.assertIn("id: str", code)
    
    def test_flask_route_patterns(self):
        """Generated Flask routes should follow patterns."""
        contract = Contract(
            name="Widget",
            fields=[Field("name", "string", True)],
        )
        
        routes = contract.to_flask_routes()
        
        # Required patterns
        self.assertIn("@widget_bp.route", routes)
        self.assertIn('methods=["GET"]', routes)
        self.assertIn('methods=["POST"]', routes)
        self.assertIn("request.get_json()", routes)
        self.assertIn("jsonify", routes)
    
    def test_typescript_interface_pattern(self):
        """Generated TypeScript should follow patterns."""
        contract = Contract(
            name="Item",
            fields=[
                Field("required_field", "string", True),
                Field("optional_field", "string", False),
            ],
        )
        
        ts = contract.to_typescript()
        
        # Required field has no ?
        self.assertIn("required_field: string;", ts)
        # Optional field has ?
        self.assertIn("optional_field?: string;", ts)


# ============================================================================
# RUNNER
# ============================================================================

def run_rigorous_tests():
    """Run all rigorous tests with detailed output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestConstraintSoundness,
        TestBidirectionalRoundTrip,
        TestGeneratedCodeValidity,
        TestFuzzInputs,
        TestEndToEndPipeline,
        TestPerformance,
        TestSnapshots,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    print(f"\n{'='*60}")
    print("RIGOROUS TEST SUITE")
    print(f"{'='*60}\n")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"{'='*60}\n")
    
    return result


if __name__ == "__main__":
    run_rigorous_tests()
