"""
Comprehensive Test Suite for the Intelligent Scaffolding System

Tests all three components:
1. Constraint Solver - Logical deduction
2. Compositional Blocks - Auto-assembly
3. Bidirectional Contracts - Spec/code sync
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import json

# Import our systems
from constraint_solver import ConstraintSolver, Rule, Constraint, Certainty, RULES, SCENARIO_TEMPLATES
from blocks import Block, Port, BlockAssembler, BLOCKS
from contracts import Contract, Field, ContractRegistry
from intelligent_scaffold import IntelligentScaffolder


class TestConstraintSolver(unittest.TestCase):
    """Test the constraint solver component."""
    
    def setUp(self):
        self.solver = ConstraintSolver()
    
    def test_add_constraint(self):
        """Test adding a constraint."""
        self.solver.add_constraint("offline", True)
        self.assertEqual(self.solver.get("offline"), True)
    
    def test_add_multiple_constraints(self):
        """Test adding multiple constraints at once."""
        self.solver.add_constraints({
            "offline": True,
            "multi_user": True,
        })
        self.assertEqual(self.solver.get("offline"), True)
        self.assertEqual(self.solver.get("multi_user"), True)
    
    def test_rule_propagation(self):
        """Test that rules propagate correctly."""
        # Need both offline AND multi_user to get CRDT sync strategy
        self.solver.add_constraint("offline", True)
        self.solver.add_constraint("multi_user", True)
        solution = self.solver.solve()
        
        # Offline + multi_user should derive sync_strategy: crdt
        self.assertEqual(solution.get("sync_strategy"), "crdt")
        # And should derive needs_conflict_ui
        self.assertEqual(solution.get("needs_conflict_ui"), True)
    
    def test_multi_user_derives_auth(self):
        """Test that multi_user derives needs_auth."""
        self.solver.add_constraint("multi_user", True)
        solution = self.solver.solve()
        
        self.assertEqual(solution.get("needs_auth"), True)
        self.assertEqual(solution.get("needs_backend"), True)
    
    def test_realtime_derives_websocket(self):
        """Test that realtime derives websocket transport."""
        self.solver.add_constraint("realtime", True)
        solution = self.solver.solve()
        
        self.assertEqual(solution.get("transport"), "websocket")
    
    def test_sensitive_data_derives_encryption(self):
        """Test that sensitive_data derives encryption."""
        self.solver.add_constraint("sensitive_data", True)
        solution = self.solver.solve()
        
        self.assertEqual(solution.get("needs_encryption"), True)
    
    def test_combined_constraints(self):
        """Test multiple constraints together."""
        self.solver.add_constraints({
            "offline": True,
            "multi_user": True,
            "realtime": True,
        })
        solution = self.solver.solve()
        
        # Should have derived many things
        self.assertEqual(solution.get("sync_strategy"), "crdt")
        self.assertEqual(solution.get("needs_auth"), True)
        self.assertEqual(solution.get("transport"), "websocket")
        self.assertEqual(solution.get("needs_message_queue"), True)
    
    def test_scenario_templates(self):
        """Test that scenario templates exist and have correct structure."""
        self.assertIn("simple_crud", SCENARIO_TEMPLATES)
        self.assertIn("team_app", SCENARIO_TEMPLATES)
        self.assertIn("offline_first", SCENARIO_TEMPLATES)
        
        # Templates are dictionaries of constraint key-value pairs
        for name, template in SCENARIO_TEMPLATES.items():
            self.assertIsInstance(template, dict)
            # Each template should have at least one constraint
            self.assertTrue(len(template) > 0)
    
    def test_explain_derivation(self):
        """Test that explanation is generated."""
        self.solver.add_constraint("offline", True)
        self.solver.solve()
        explanation = self.solver.explain()
        
        self.assertIn("offline", explanation)
        self.assertIsInstance(explanation, str)
        self.assertTrue(len(explanation) > 0)
    
    def test_rules_have_required_fields(self):
        """Test that all rules have required fields."""
        for rule in RULES:
            self.assertIsNotNone(rule.name)
            self.assertIsNotNone(rule.conditions)
            self.assertIsNotNone(rule.conclusions)
            self.assertIsInstance(rule.priority, int)


class TestCompositionalBlocks(unittest.TestCase):
    """Test the compositional blocks component."""
    
    def test_block_structure(self):
        """Test that blocks have required structure."""
        for block_id, block in BLOCKS.items():
            self.assertEqual(block.id, block_id)
            self.assertIsNotNone(block.name)
            self.assertIsNotNone(block.description)
            self.assertIsInstance(block.requires, list)
            self.assertIsInstance(block.provides, list)
    
    def test_port_structure(self):
        """Test that ports have required structure."""
        for block in BLOCKS.values():
            for port in block.requires + block.provides:
                self.assertIsNotNone(port.name)
                self.assertIsNotNone(port.type)
    
    def test_block_assembler_selection(self):
        """Test block selection based on constraints."""
        constraints = {"needs_auth": True}
        assembler = BlockAssembler(constraints)
        blocks = assembler.select_blocks()
        
        # Should select auth block
        block_ids = [b.id for b in blocks]
        self.assertIn("auth_basic", block_ids)
    
    def test_block_assembler_storage_selection(self):
        """Test storage block selection."""
        constraints = {"storage_type": "local_first"}
        assembler = BlockAssembler(constraints)
        blocks = assembler.select_blocks()
        
        block_ids = [b.id for b in blocks]
        self.assertTrue(
            "storage_json" in block_ids or "storage_sqlite" in block_ids,
            "Should select a storage block"
        )
    
    def test_block_assembler_dependency_resolution(self):
        """Test that dependencies are resolved."""
        constraints = {"needs_auth": True}
        assembler = BlockAssembler(constraints)
        assembler.select_blocks()
        unresolved = assembler.resolve_dependencies()
        
        # Check that ports are resolved
        self.assertIsInstance(assembler.resolved_ports, dict)
    
    def test_block_code_generation(self):
        """Test that code is generated for selected blocks."""
        constraints = {"storage_type": "local_first"}
        assembler = BlockAssembler(constraints, stack="flask")
        assembler.select_blocks()
        
        code = assembler.get_code()
        self.assertIsInstance(code, dict)
        self.assertTrue(len(code) > 0)
    
    def test_block_dependencies(self):
        """Test that dependencies are collected."""
        constraints = {"needs_auth": True}
        assembler = BlockAssembler(constraints, stack="flask")
        assembler.select_blocks()
        
        deps = assembler.get_dependencies()
        self.assertIsInstance(deps, list)
    
    def test_block_explanation(self):
        """Test that explanation is generated."""
        constraints = {"needs_auth": True}
        assembler = BlockAssembler(constraints)
        assembler.select_blocks()
        
        explanation = assembler.explain()
        self.assertIsInstance(explanation, str)
        self.assertIn("Selected blocks", explanation)
    
    def test_sync_block_constraints(self):
        """Test sync block selection."""
        constraints = {"sync_strategy": "crdt"}
        assembler = BlockAssembler(constraints)
        blocks = assembler.select_blocks()
        
        block_ids = [b.id for b in blocks]
        self.assertIn("sync_crdt", block_ids)


class TestBidirectionalContracts(unittest.TestCase):
    """Test the bidirectional contracts component."""
    
    def test_field_creation(self):
        """Test field creation."""
        field = Field(
            name="title",
            type="string",
            required=True,
            constraints=["min:1"]
        )
        
        self.assertEqual(field.name, "title")
        self.assertEqual(field.type, "string")
        self.assertTrue(field.required)
        self.assertIn("min:1", field.constraints)
    
    def test_field_to_spec(self):
        """Test field to spec conversion."""
        field = Field(name="title", type="string", required=True)
        spec = field.to_spec()
        
        self.assertIn("title", spec)
        self.assertIn("string", spec)
        self.assertIn("required", spec)
    
    def test_field_to_code(self):
        """Test field to Python code conversion."""
        field = Field(name="count", type="integer", required=True)
        code = field.to_code("python")
        
        self.assertIn("count", code)
        self.assertIn("int", code)
    
    def test_contract_creation(self):
        """Test contract creation."""
        contract = Contract(
            name="Task",
            description="A task entity",
            fields=[
                Field("id", "string", True),
                Field("title", "string", True),
            ],
            invariants=["title cannot be empty"]
        )
        
        self.assertEqual(contract.name, "Task")
        self.assertEqual(len(contract.fields), 2)
        self.assertEqual(len(contract.invariants), 1)
    
    def test_contract_to_spec(self):
        """Test contract to Markdown spec conversion."""
        contract = Contract(
            name="Task",
            fields=[Field("title", "string", True)],
            invariants=["title cannot be empty"]
        )
        
        spec = contract.to_spec()
        self.assertIn("# Contract: Task", spec)
        self.assertIn("## Fields", spec)
        self.assertIn("title", spec)
        self.assertIn("## Invariants", spec)
    
    def test_contract_to_python_dataclass(self):
        """Test contract to Python dataclass conversion."""
        contract = Contract(
            name="Task",
            fields=[
                Field("id", "string", True),
                Field("title", "string", True),
            ],
            invariants=["title cannot be empty"]
        )
        
        code = contract.to_python_dataclass()
        self.assertIn("@dataclass", code)
        self.assertIn("class Task:", code)
        self.assertIn("id: str", code)
        self.assertIn("title: str", code)
        self.assertIn("def validate(self)", code)
    
    def test_contract_to_flask_routes(self):
        """Test contract to Flask routes conversion."""
        contract = Contract(
            name="Task",
            fields=[Field("title", "string", True)],
        )
        
        routes = contract.to_flask_routes()
        self.assertIn("Blueprint", routes)
        self.assertIn("@task_bp.route", routes)
        self.assertIn("def create_task", routes)
        self.assertIn("def list_task", routes)
    
    def test_contract_to_typescript(self):
        """Test contract to TypeScript conversion."""
        contract = Contract(
            name="Task",
            fields=[
                Field("id", "string", True),
                Field("count", "integer", True),
                Field("done", "boolean", False),
            ],
        )
        
        ts = contract.to_typescript()
        self.assertIn("export interface Task", ts)
        self.assertIn("id: string", ts)
        self.assertIn("count: number", ts)
        self.assertIn("done?: boolean", ts)
    
    def test_contract_hash(self):
        """Test contract hash generation."""
        contract = Contract(
            name="Task",
            fields=[Field("title", "string", True)],
        )
        
        hash1 = contract.compute_hash()
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 8)
        
        # Same contract should have same hash
        hash2 = contract.compute_hash()
        self.assertEqual(hash1, hash2)
    
    def test_contract_registry(self):
        """Test contract registry."""
        registry = ContractRegistry()
        contract = Contract(name="Task", fields=[Field("title", "string", True)])
        
        registry.define(contract)
        self.assertIn("Task", registry.contracts)
    
    def test_contract_registry_generation(self):
        """Test contract registry file generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ContractRegistry()
            contract = Contract(
                name="Item",
                fields=[Field("name", "string", True)]
            )
            registry.define(contract)
            
            files = registry.generate_all(tmpdir)
            
            self.assertTrue(len(files) > 0)
            
            # Check files exist
            for f in files:
                self.assertTrue(Path(f).exists())


class TestIntelligentScaffolder(unittest.TestCase):
    """Test the unified intelligent scaffolder."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.scaffolder = IntelligentScaffolder(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_requirement_parsing(self):
        """Test that requirements are parsed to constraints."""
        parsed = self.scaffolder._parse_requirement("needs multiple users")
        
        self.assertTrue(len(parsed) > 0)
        names = [p[0] for p in parsed]
        self.assertIn("multi_user", names)
    
    def test_understand_requirements(self):
        """Test requirement understanding."""
        requirements = ["needs offline support", "multiple users"]
        constraints = self.scaffolder.understand_requirements(requirements)
        
        self.assertIn("offline", constraints)
        self.assertIn("multi_user", constraints)
    
    def test_select_components(self):
        """Test component selection."""
        self.scaffolder.understand_requirements(["needs authentication"])
        blocks = self.scaffolder.select_components()
        
        self.assertTrue(len(blocks) > 0)
    
    def test_define_entities(self):
        """Test entity definition."""
        entities = [
            {
                "name": "Task",
                "fields": [
                    {"name": "title", "type": "string"},
                ],
            }
        ]
        
        self.scaffolder.define_entities(entities)
        self.assertIn("Task", self.scaffolder.entities)
        self.assertIn("Task", self.scaffolder.registry.contracts)
    
    def test_generate_project(self):
        """Test complete project generation."""
        self.scaffolder.understand_requirements(["offline", "authentication"])
        self.scaffolder.select_components()
        self.scaffolder.define_entities([
            {"name": "Item", "fields": [{"name": "name", "type": "string"}]}
        ])
        
        files = self.scaffolder.generate_project()
        
        self.assertIn("app.py", files)
        self.assertIn("requirements.txt", files)
        self.assertIn("project.json", files)
    
    def test_write_files(self):
        """Test file writing."""
        self.scaffolder.understand_requirements(["offline"])
        self.scaffolder.select_components()
        self.scaffolder.define_entities([
            {"name": "Note", "fields": [{"name": "text", "type": "text"}]}
        ])
        
        files = self.scaffolder.generate_project()
        self.scaffolder.write_files(files)
        
        # Check files were written
        self.assertTrue((Path(self.temp_dir) / "app.py").exists())
        self.assertTrue((Path(self.temp_dir) / "requirements.txt").exists())
    
    def test_explain(self):
        """Test explanation generation."""
        self.scaffolder.understand_requirements(["offline", "multi-user"])
        self.scaffolder.select_components()
        
        explanation = self.scaffolder.explain()
        
        self.assertIn("Constraint Solving", explanation)
        self.assertIn("Block Selection", explanation)
    
    def test_full_pipeline(self):
        """Test the complete pipeline end-to-end."""
        requirements = [
            "needs offline support",
            "multiple users",
            "needs sync",
        ]
        
        entities = [
            {
                "name": "Document",
                "description": "A collaborative document",
                "fields": [
                    {"name": "id", "type": "string"},
                    {"name": "title", "type": "string", "constraints": ["min:1"]},
                    {"name": "content", "type": "text"},
                    {"name": "author_id", "type": "string"},
                ],
                "invariants": ["title cannot be empty"],
            }
        ]
        
        # Run pipeline
        self.scaffolder.understand_requirements(requirements)
        self.scaffolder.select_components()
        self.scaffolder.define_entities(entities)
        files = self.scaffolder.generate_project()
        self.scaffolder.write_files(files)
        
        # Verify output
        output_path = Path(self.temp_dir)
        
        # Core files
        self.assertTrue((output_path / "app.py").exists())
        self.assertTrue((output_path / "requirements.txt").exists())
        self.assertTrue((output_path / "project.json").exists())
        
        # Model files
        self.assertTrue((output_path / "models" / "document.py").exists())
        
        # Route files
        self.assertTrue((output_path / "routes" / "document_routes.py").exists())
        
        # Type files
        self.assertTrue((output_path / "types" / "document.ts").exists())
        
        # Spec files
        self.assertTrue((output_path / "specs" / "document.spec.md").exists())
        
        # Verify project.json content
        with open(output_path / "project.json") as f:
            project = json.load(f)
            self.assertIn("constraints", project)
            self.assertIn("blocks", project)
            self.assertIn("entities", project)


class TestIntegration(unittest.TestCase):
    """Integration tests across all components."""
    
    def test_constraints_to_blocks(self):
        """Test that constraints correctly select blocks."""
        solver = ConstraintSolver()
        solver.add_constraints({
            "offline": True,
            "multi_user": True,
        })
        constraints = solver.solve()
        
        assembler = BlockAssembler(constraints)
        blocks = assembler.select_blocks()
        
        block_ids = [b.id for b in blocks]
        
        # Should have auth (from multi_user -> needs_auth)
        self.assertIn("auth_basic", block_ids)
        # Should have sync (from offline -> crdt)
        self.assertIn("sync_crdt", block_ids)
    
    def test_contracts_to_files(self):
        """Test that contracts generate all expected file types."""
        contract = Contract(
            name="Widget",
            description="A widget thing",
            fields=[
                Field("id", "string", True),
                Field("name", "string", True),
                Field("count", "integer", True, default=0),
            ],
            invariants=["name cannot be empty", "count >= 0"],
        )
        
        # All generations should work
        spec = contract.to_spec()
        self.assertIn("Widget", spec)
        
        py = contract.to_python_dataclass()
        self.assertIn("class Widget", py)
        
        routes = contract.to_flask_routes()
        self.assertIn("widget_bp", routes)
        
        ts = contract.to_typescript()
        self.assertIn("interface Widget", ts)
    
    def test_bidirectional_sync(self):
        """Test spec parsing for bidirectional sync."""
        original = Contract(
            name="Task",
            description="A task",
            fields=[
                Field("id", "string", True),
                Field("title", "string", True),
            ],
            invariants=["title cannot be empty"],
        )
        
        # Generate spec
        spec_text = original.to_spec()
        
        # Parse it back
        registry = ContractRegistry()
        parsed = registry.load_from_spec(spec_text)
        
        # Should match
        self.assertEqual(parsed.name, original.name)
        self.assertEqual(len(parsed.fields), len(original.fields))
        self.assertEqual(len(parsed.invariants), len(original.invariants))


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConstraintSolver))
    suite.addTests(loader.loadTestsFromTestCase(TestCompositionalBlocks))
    suite.addTests(loader.loadTestsFromTestCase(TestBidirectionalContracts))
    suite.addTests(loader.loadTestsFromTestCase(TestIntelligentScaffolder))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    run_tests()
