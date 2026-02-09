"""
Constraint Solver for Blueprint System

Uses logical deduction to derive architectural decisions from requirements.
No AI - pure logic and rule propagation.

Example:
    solver = ConstraintSolver()
    solver.add_constraint("offline", True)
    solver.add_constraint("multi_user", True)
    
    solution = solver.solve()
    # Deduces: local_first_storage, crdt_sync, conflict_resolution, backend_required
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Callable, Any, Tuple
from enum import Enum


class Certainty(Enum):
    """How certain we are about a deduction."""
    REQUIRED = "required"      # Must be true
    PREFERRED = "preferred"    # Should be true unless conflicts
    DERIVED = "derived"        # Logically follows from other constraints
    DEFAULT = "default"        # Fallback value


@dataclass
class Constraint:
    """A single constraint or fact."""
    name: str
    value: Any
    certainty: Certainty = Certainty.REQUIRED
    reason: str = ""
    derived_from: List[str] = field(default_factory=list)


@dataclass
class Rule:
    """An inference rule: if conditions met, derive conclusions."""
    name: str
    conditions: Dict[str, Any]  # constraint_name -> expected_value
    conclusions: Dict[str, Any]  # constraint_name -> derived_value
    priority: int = 0  # Higher = applied first


# ============================================================================
# KNOWLEDGE BASE - Rules that encode architectural wisdom
# ============================================================================

RULES = [
    # Offline requirements
    Rule(
        name="offline_requires_local_storage",
        conditions={"offline": True},
        conclusions={"storage_type": "local_first", "needs_sync": True},
        priority=10
    ),
    Rule(
        name="offline_sync_needs_conflict_handling",
        conditions={"offline": True, "multi_user": True},
        conclusions={"sync_strategy": "crdt", "needs_conflict_ui": True},
        priority=10
    ),
    Rule(
        name="offline_single_user_simple_sync",
        conditions={"offline": True, "multi_user": False},
        conclusions={"sync_strategy": "last_write_wins"},
        priority=5
    ),
    
    # Multi-user requirements
    Rule(
        name="multi_user_needs_auth",
        conditions={"multi_user": True},
        conclusions={"needs_auth": True, "needs_backend": True},
        priority=10
    ),
    Rule(
        name="multi_user_needs_permissions",
        conditions={"multi_user": True, "shared_content": True},
        conclusions={"needs_permissions": True, "needs_roles": True},
        priority=8
    ),
    
    # Real-time requirements
    Rule(
        name="realtime_needs_websockets",
        conditions={"realtime": True},
        conclusions={"transport": "websocket", "needs_backend": True},
        priority=10
    ),
    Rule(
        name="realtime_with_offline_needs_queue",
        conditions={"realtime": True, "offline": True},
        conclusions={"needs_message_queue": True, "needs_retry_logic": True},
        priority=8
    ),
    
    # Scale requirements
    Rule(
        name="high_scale_needs_caching",
        conditions={"scale": "high"},
        conclusions={"needs_cache": True, "cache_type": "redis"},
        priority=7
    ),
    Rule(
        name="high_scale_needs_cdn",
        conditions={"scale": "high", "has_assets": True},
        conclusions={"needs_cdn": True},
        priority=6
    ),
    
    # Data requirements
    Rule(
        name="complex_queries_need_sql",
        conditions={"query_complexity": "high"},
        conclusions={"database_type": "sql", "needs_orm": True},
        priority=8
    ),
    Rule(
        name="simple_data_can_use_nosql",
        conditions={"query_complexity": "low"},
        conclusions={"database_type": "nosql_ok"},
        priority=3
    ),
    Rule(
        name="hierarchical_data_needs_tree_support",
        conditions={"data_structure": "hierarchical"},
        conclusions={"needs_tree_queries": True, "consider_closure_table": True},
        priority=6
    ),
    
    # Security requirements
    Rule(
        name="sensitive_data_needs_encryption",
        conditions={"sensitive_data": True},
        conclusions={"needs_encryption": True, "needs_audit_log": True},
        priority=10
    ),
    Rule(
        name="payment_needs_compliance",
        conditions={"handles_payment": True},
        conclusions={"needs_pci_compliance": True, "use_payment_provider": True},
        priority=10
    ),
    
    # Size/bundle requirements
    Rule(
        name="small_bundle_limits_framework",
        conditions={"max_bundle_kb": lambda x: x < 100},
        conclusions={"framework": "preact_or_vanilla", "avoid_heavy_deps": True},
        priority=9
    ),
    
    # Stack derivation
    Rule(
        name="python_backend_default",
        conditions={"needs_backend": True, "preferred_language": "python"},
        conclusions={"backend_framework": "fastapi"},
        priority=5
    ),
    Rule(
        name="node_backend",
        conditions={"needs_backend": True, "preferred_language": "javascript"},
        conclusions={"backend_framework": "express"},
        priority=5
    ),
    
    # Default fallbacks
    Rule(
        name="default_storage",
        conditions={},
        conclusions={"storage_type": "server_only"},
        priority=0
    ),
]


# ============================================================================
# SOLVER
# ============================================================================

class ConstraintSolver:
    """
    Deductive constraint solver.
    
    Add constraints, then solve() to get all derived conclusions.
    """
    
    def __init__(self):
        self.constraints: Dict[str, Constraint] = {}
        self.rules = sorted(RULES, key=lambda r: -r.priority)  # High priority first
        self.derivation_log: List[str] = []
    
    def add_constraint(
        self, 
        name: str, 
        value: Any, 
        certainty: Certainty = Certainty.REQUIRED,
        reason: str = "user input"
    ):
        """Add a constraint to the system."""
        self.constraints[name] = Constraint(
            name=name,
            value=value,
            certainty=certainty,
            reason=reason
        )
    
    def add_constraints(self, constraints: Dict[str, Any]):
        """Add multiple constraints at once."""
        for name, value in constraints.items():
            self.add_constraint(name, value)
    
    def get(self, name: str, default: Any = None) -> Any:
        """Get constraint value."""
        if name in self.constraints:
            return self.constraints[name].value
        return default
    
    def _check_condition(self, name: str, expected: Any) -> bool:
        """Check if a condition is satisfied."""
        if name not in self.constraints:
            return False
        
        actual = self.constraints[name].value
        
        # Handle callable conditions (lambdas)
        if callable(expected):
            try:
                return expected(actual)
            except:
                return False
        
        return actual == expected
    
    def _apply_rule(self, rule: Rule) -> bool:
        """
        Try to apply a rule. Returns True if any new conclusions were derived.
        """
        # Check all conditions
        for name, expected in rule.conditions.items():
            if not self._check_condition(name, expected):
                return False
        
        # All conditions met - derive conclusions
        derived_any = False
        
        for name, value in rule.conclusions.items():
            # Don't override higher-certainty constraints
            if name in self.constraints:
                existing = self.constraints[name]
                if existing.certainty.value in ("required", "preferred"):
                    continue  # Don't override user input
            
            # Add derived constraint
            condition_names = list(rule.conditions.keys())
            self.constraints[name] = Constraint(
                name=name,
                value=value,
                certainty=Certainty.DERIVED,
                reason=f"derived by rule '{rule.name}'",
                derived_from=condition_names
            )
            
            self.derivation_log.append(
                f"[{rule.name}] {' + '.join(condition_names)} → {name}={value}"
            )
            derived_any = True
        
        return derived_any
    
    def solve(self, max_iterations: int = 10) -> Dict[str, Any]:
        """
        Run inference until no new conclusions can be derived.
        
        Returns dict of all constraints (input + derived).
        """
        self.derivation_log = []
        
        for iteration in range(max_iterations):
            derived_any = False
            
            for rule in self.rules:
                if self._apply_rule(rule):
                    derived_any = True
            
            if not derived_any:
                break  # Fixed point reached
        
        # Return simplified dict
        return {name: c.value for name, c in self.constraints.items()}
    
    def explain(self) -> str:
        """Explain all derivations made."""
        lines = ["Derivation trace:"]
        for entry in self.derivation_log:
            lines.append(f"  {entry}")
        return "\n".join(lines) if self.derivation_log else "No derivations made."
    
    def get_architecture_summary(self) -> Dict[str, List[str]]:
        """
        Summarize the derived architecture in categories.
        """
        solution = self.solve()
        
        categories = {
            "storage": [],
            "backend": [],
            "frontend": [],
            "security": [],
            "infrastructure": [],
        }
        
        # Categorize results
        storage_keys = ["storage_type", "database_type", "cache_type", "sync_strategy"]
        backend_keys = ["needs_backend", "backend_framework", "transport"]
        frontend_keys = ["framework", "needs_conflict_ui", "avoid_heavy_deps"]
        security_keys = ["needs_auth", "needs_permissions", "needs_encryption", "needs_roles"]
        infra_keys = ["needs_cdn", "needs_cache", "needs_message_queue"]
        
        for key, value in solution.items():
            if value is True or (isinstance(value, str) and value):
                entry = f"{key}={value}" if value is not True else key
                
                if key in storage_keys:
                    categories["storage"].append(entry)
                elif key in backend_keys:
                    categories["backend"].append(entry)
                elif key in frontend_keys:
                    categories["frontend"].append(entry)
                elif key in security_keys:
                    categories["security"].append(entry)
                elif key in infra_keys:
                    categories["infrastructure"].append(entry)
        
        return {k: v for k, v in categories.items() if v}


# ============================================================================
# CONSTRAINT TEMPLATES - Common scenarios
# ============================================================================

SCENARIO_TEMPLATES = {
    "simple_crud": {
        "multi_user": False,
        "offline": False,
        "realtime": False,
        "query_complexity": "low",
    },
    "team_app": {
        "multi_user": True,
        "shared_content": True,
        "offline": False,
        "realtime": False,
    },
    "offline_first": {
        "offline": True,
        "multi_user": False,
    },
    "collaborative": {
        "multi_user": True,
        "realtime": True,
        "shared_content": True,
    },
    "offline_collaborative": {
        "multi_user": True,
        "realtime": True,
        "offline": True,
        "shared_content": True,
    },
}


def solve_for_scenario(scenario: str, **overrides) -> Tuple[Dict[str, Any], str]:
    """
    Solve constraints for a named scenario with optional overrides.
    
    Returns (solution_dict, explanation_string)
    """
    if scenario not in SCENARIO_TEMPLATES:
        raise ValueError(f"Unknown scenario: {scenario}")
    
    solver = ConstraintSolver()
    solver.add_constraints(SCENARIO_TEMPLATES[scenario])
    solver.add_constraints(overrides)
    
    solution = solver.solve()
    explanation = solver.explain()
    
    return solution, explanation


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Constraint solver for architecture decisions")
    parser.add_argument("--scenario", "-s", choices=list(SCENARIO_TEMPLATES.keys()),
                       help="Use a predefined scenario")
    parser.add_argument("--offline", action="store_true", help="Needs offline support")
    parser.add_argument("--multi-user", action="store_true", help="Multiple users")
    parser.add_argument("--realtime", action="store_true", help="Real-time updates")
    parser.add_argument("--sensitive", action="store_true", help="Sensitive data")
    parser.add_argument("--explain", "-e", action="store_true", help="Show derivation trace")
    
    args = parser.parse_args()
    
    solver = ConstraintSolver()
    
    # Load scenario if provided
    if args.scenario:
        solver.add_constraints(SCENARIO_TEMPLATES[args.scenario])
    
    # Add CLI flags
    if args.offline:
        solver.add_constraint("offline", True)
    if args.multi_user:
        solver.add_constraint("multi_user", True)
    if args.realtime:
        solver.add_constraint("realtime", True)
    if args.sensitive:
        solver.add_constraint("sensitive_data", True)
    
    # Solve
    solution = solver.solve()
    
    print("\n🔍 Constraint Solver Results")
    print("=" * 50)
    
    # Show input
    print("\nInput constraints:")
    for name, c in solver.constraints.items():
        if c.certainty == Certainty.REQUIRED:
            print(f"  • {name} = {c.value}")
    
    # Show derived
    print("\nDerived architecture:")
    summary = solver.get_architecture_summary()
    for category, items in summary.items():
        if items:
            print(f"\n  {category.upper()}:")
            for item in items:
                print(f"    ✓ {item}")
    
    # Show explanation
    if args.explain:
        print(f"\n{solver.explain()}")
    
    print()


if __name__ == "__main__":
    main()
