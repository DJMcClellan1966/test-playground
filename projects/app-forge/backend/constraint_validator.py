"""Constraint Validator - Feasibility Checking Without LLMs.

LLMs learn what combinations are invalid from seeing millions of codebases.
We replicate this with explicit constraint rules derived from software patterns.

This prevents nonsense combinations like:
- CLI app with responsive UI
- Game with authentication system
- ML pipeline with realtime websockets
"""

from typing import Set, List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ConstraintViolation:
    """A detected constraint violation."""
    severity: str  # "error" or "warning"
    message: str
    suggestion: Optional[str] = None


# =============================================================================
# INCOMPATIBILITY RULES (What LLMs learn from failed deployments)
# =============================================================================

# Features that don't make sense together
INCOMPATIBLE_PAIRS: Set[Tuple[str, str]] = {
    # CLI apps can't have browser-based UI features
    ("click", "responsive_ui"),
    ("click", "realtime"),
    ("click", "game_loop"),
    
    # Games rarely need these web app features
    ("game_loop", "auth"),
    ("game_loop", "database"),  # Most games don't need persistent storage
    ("game_loop", "export"),
    ("html_canvas", "database"),  # Most canvas games are stateless
    
    # Framework mismatches
    ("html_canvas", "crud"),  # Canvas is for rendering, not CRUD
    ("sklearn", "auth"),      # ML pipelines don't have user authentication
    ("sklearn", "realtime"),  # Training is batch, not realtime
    
    # Contradictory patterns
    ("stateless", "database"),  # Can't be stateless with persistent storage
    ("offline", "realtime"),    # Real-time requires connection
}


# Features that should never coexist (stronger than incompatible)
MUTUALLY_EXCLUSIVE: Set[Tuple[str, str]] = {
    ("flask", "fastapi"),      # Can't use both frameworks
    ("flask", "click"),
    ("flask", "html_canvas"),
    ("fastapi", "click"),
    ("fastapi", "html_canvas"),
    ("click", "html_canvas"),
}


# =============================================================================
# DEPENDENCY RULES (What LLMs learn from import errors)
# =============================================================================

# Features that require other features
REQUIRED_DEPENDENCIES: Dict[str, Set[str]] = {
    "auth": {"database"},           # Need to store user credentials
    "search": {"database"},         # Can't search without data
    "export": {"database"},         # Need data to export
    "crud": {"database"},           # CRUD operations require storage
    "realtime": {"database"},       # Usually need to persist messages/state
    "scoring": {"database"},        # Need to save high scores
}


# Features that work better with companions
RECOMMENDED_COMPANIONS: Dict[str, Set[str]] = {
    "database": {"crud"},           # If you have DB, you usually want CRUD
    "auth": {"database", "crud"},   # Auth usually comes with user management
    "crud": {"search"},             # Collections benefit from search
    "game_loop": {"input_handler", "scoring"},  # Games need these
    "responsive_ui": {"database"},  # Interactive UIs usually have data
}


# =============================================================================
# FRAMEWORK-SPECIFIC CONSTRAINTS
# =============================================================================

# Features incompatible with specific frameworks
FRAMEWORK_INCOMPATIBILITIES: Dict[str, Set[str]] = {
    "click": {"responsive_ui", "realtime", "game_loop"},
    "html_canvas": {"database", "crud", "auth", "export"},
    "sklearn": {"auth", "realtime", "game_loop", "responsive_ui"},
}


# Features required by framework choice
FRAMEWORK_REQUIREMENTS: Dict[str, Set[str]] = {
    "flask": set(),  # Flexible
    "fastapi": set(),  # Flexible
    "click": set(),  # Minimal
    "html_canvas": {"game_loop", "input_handler"},  # Need game basics
    "sklearn": set(),  # Depends on use case
}


# =============================================================================
# DATA CONSISTENCY RULES
# =============================================================================

# If you have these features, you probably have data
DATA_INDICATORS: Set[str] = {
    "database", "crud", "search", "export", "auth"
}


# If you have these, you're probably building a game
GAME_INDICATORS: Set[str] = {
    "game_loop", "input_handler", "scoring", "timer"
}


# =============================================================================
# VALIDATION LOGIC
# =============================================================================

def validate_feature_combination(features: Set[str], 
                                   framework: str) -> List[ConstraintViolation]:
    """Validate that feature combination is feasible.
    
    Returns list of violations (errors and warnings).
    """
    violations = []
    
    # Check incompatible pairs
    for feat1, feat2 in INCOMPATIBLE_PAIRS:
        if feat1 in features and feat2 in features:
            violations.append(ConstraintViolation(
                severity="warning",
                message=f"Unusual combination: '{feat1}' with '{feat2}'",
                suggestion=f"These features rarely work together. Consider removing one."
            ))
    
    # Check mutually exclusive
    for feat1, feat2 in MUTUALLY_EXCLUSIVE:
        if feat1 in features and feat2 in features:
            violations.append(ConstraintViolation(
                severity="error",
                message=f"Cannot use both '{feat1}' and '{feat2}'",
                suggestion=f"Choose either '{feat1}' or '{feat2}', not both."
            ))
    
    # Check required dependencies
    for feature, required in REQUIRED_DEPENDENCIES.items():
        if feature in features:
            missing = required - features
            if missing:
                violations.append(ConstraintViolation(
                    severity="error",
                    message=f"'{feature}' requires: {', '.join(missing)}",
                    suggestion=f"Add {', '.join(missing)} to support '{feature}'"
                ))
    
    # Check framework incompatibilities
    if framework in FRAMEWORK_INCOMPATIBILITIES:
        incompatible = FRAMEWORK_INCOMPATIBILITIES[framework] & features
        if incompatible:
            violations.append(ConstraintViolation(
                severity="error",
                message=f"Framework '{framework}' does not support: {', '.join(incompatible)}",
                suggestion=f"Remove {', '.join(incompatible)} or choose a different framework"
            ))
    
    # Check framework requirements
    if framework in FRAMEWORK_REQUIREMENTS:
        required = FRAMEWORK_REQUIREMENTS[framework]
        missing = required - features
        if missing:
            violations.append(ConstraintViolation(
                severity="warning",
                message=f"Framework '{framework}' typically requires: {', '.join(missing)}",
                suggestion=f"Consider adding {', '.join(missing)}"
            ))
    
    return violations


def auto_fix_constraints(features: Set[str], 
                          framework: str,
                          aggressive: bool = False) -> Tuple[Set[str], List[str]]:
    """Automatically fix constraint violations.
    
    Args:
        features: Set of requested features
        framework: Target framework
        aggressive: If True, remove problematic features. If False, only add missing deps.
        
    Returns:
        (fixed_features, changes_made)
    """
    fixed_features = features.copy()
    changes = []
    
    # Add missing dependencies
    for feature in list(fixed_features):
        if feature in REQUIRED_DEPENDENCIES:
            missing = REQUIRED_DEPENDENCIES[feature] - fixed_features
            if missing:
                fixed_features.update(missing)
                changes.append(f"Added {', '.join(missing)} (required by {feature})")
    
    # Remove framework incompatibilities (if aggressive)
    if aggressive and framework in FRAMEWORK_INCOMPATIBILITIES:
        incompatible = FRAMEWORK_INCOMPATIBILITIES[framework] & fixed_features
        if incompatible:
            fixed_features -= incompatible
            changes.append(f"Removed {', '.join(incompatible)} (incompatible with {framework})")
    
    # Remove mutually exclusive conflicts (keep first, remove second)
    for feat1, feat2 in MUTUALLY_EXCLUSIVE:
        if feat1 in fixed_features and feat2 in fixed_features:
            if aggressive:
                # Keep the one that appears first in original features
                if feat2 in features:
                    fixed_features.discard(feat2)
                    changes.append(f"Removed {feat2} (conflicts with {feat1})")
    
    # Add recommended companions (if not aggressive)
    if not aggressive:
        for feature in list(fixed_features):
            if feature in RECOMMENDED_COMPANIONS:
                recommended = RECOMMENDED_COMPANIONS[feature] - fixed_features
                # Only add if it's a strong recommendation (in top 2)
                if recommended and len(recommended) <= 2:
                    fixed_features.update(recommended)
                    changes.append(f"Added {', '.join(recommended)} (recommended with {feature})")
    
    return fixed_features, changes


def suggest_better_framework(features: Set[str], 
                               current_framework: str) -> Optional[Tuple[str, str]]:
    """Suggest a better framework if current one has issues.
    
    Returns (suggested_framework, reason) or None
    """
    # Check if current framework is incompatible
    if current_framework in FRAMEWORK_INCOMPATIBILITIES:
        incompatible = FRAMEWORK_INCOMPATIBILITIES[current_framework] & features
        if incompatible:
            # Suggest alternative
            has_data = bool(DATA_INDICATORS & features)
            has_game = bool(GAME_INDICATORS & features)
            
            if has_game:
                return ("html_canvas", "Games work best with HTML Canvas")
            elif has_data and "realtime" in features:
                return ("flask", "Real-time data apps work well with Flask")
            elif has_data:
                return ("fastapi", "Data APIs work well with FastAPI")
            else:
                return ("flask", "Flask is versatile for most apps")
    
    return None


def explain_constraint_violation(violation: ConstraintViolation) -> str:
    """Generate user-friendly explanation of why constraint failed."""
    lines = [f"{'❌ ERROR' if violation.severity == 'error' else '⚠️  WARNING'}: {violation.message}"]
    
    if violation.suggestion:
        lines.append(f"   💡 {violation.suggestion}")
    
    return "\n".join(lines)


def validate_and_fix(features: Set[str], 
                      framework: str,
                      auto_fix: bool = True,
                      verbose: bool = False) -> Tuple[Set[str], List[ConstraintViolation]]:
    """One-stop validation and fixing.
    
    Returns (final_features, remaining_violations)
    """
    # First pass: check violations
    violations = validate_feature_combination(features, framework)
    
    if not violations:
        if verbose:
            print("✅ No constraint violations detected")
        return features, []
    
    if verbose:
        print(f"🔍 Found {len(violations)} constraint issues")
        for v in violations:
            print(f"  {explain_constraint_violation(v)}")
    
    # Auto-fix if requested
    if auto_fix:
        fixed_features, changes = auto_fix_constraints(features, framework, aggressive=True)
        
        if verbose and changes:
            print(f"\n🔧 Applied {len(changes)} fixes:")
            for change in changes:
                print(f"  • {change}")
        
        # Validate again
        remaining = validate_feature_combination(fixed_features, framework)
        
        if verbose:
            if remaining:
                print(f"\n⚠️  {len(remaining)} issues remain after auto-fix")
            else:
                print("\n✅ All issues resolved!")
        
        return fixed_features, remaining
    
    return features, violations


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def is_valid_combination(features: Set[str], framework: str) -> bool:
    """Quick check if combination is valid."""
    violations = validate_feature_combination(features, framework)
    # Only count errors, not warnings
    errors = [v for v in violations if v.severity == "error"]
    return len(errors) == 0


def get_missing_dependencies(features: Set[str]) -> Dict[str, Set[str]]:
    """Get all missing dependencies for features."""
    missing = {}
    for feature in features:
        if feature in REQUIRED_DEPENDENCIES:
            deps = REQUIRED_DEPENDENCIES[feature] - features
            if deps:
                missing[feature] = deps
    return missing
