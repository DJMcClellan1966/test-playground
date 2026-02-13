"""
Local Error Fixer for App Forge
================================
AI-free error detection and automatic fixing using:
1. Pattern matching (~60 common error patterns)
2. AST analysis for deeper issues
3. Fuzzy matching for typo detection

Usage:
    fixer = ErrorFixer()
    result = fixer.validate_and_fix(code, filename="app.py")
    if result.fixed:
        print(f"Fixed {len(result.fixes)} issues")
        print(result.fixed_code)
"""

import ast
import re
import difflib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path


@dataclass
class Fix:
    """A single fix applied to code."""
    error_type: str
    line: int
    message: str
    original: str
    replacement: str
    confidence: float  # 0.0 to 1.0


@dataclass
class FixResult:
    """Result of validation and fixing."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    fixes: List[Fix] = field(default_factory=list)
    fixed_code: Optional[str] = None
    
    @property
    def fixed(self) -> bool:
        return len(self.fixes) > 0


# =============================================================================
# ERROR PATTERNS - Common Python errors with regex matching
# =============================================================================

ERROR_PATTERNS: Dict[str, List[Tuple[str, str, float]]] = {
    # (regex, explanation, confidence)
    
    "NameError": [
        (r"name '(json)' is not defined", "Add 'import json' at top", 0.95),
        (r"name '(os)' is not defined", "Add 'import os' at top", 0.95),
        (r"name '(re)' is not defined", "Add 'import re' at top", 0.95),
        (r"name '(sys)' is not defined", "Add 'import sys' at top", 0.95),
        (r"name '(datetime)' is not defined", "Add 'from datetime import datetime' at top", 0.95),
        (r"name '(Path)' is not defined", "Add 'from pathlib import Path' at top", 0.95),
        (r"name '(Dict|List|Optional|Tuple|Set)' is not defined", "Add 'from typing import {match}' at top", 0.95),
        (r"name '(Flask)' is not defined", "Add 'from flask import Flask' at top", 0.95),
        (r"name '(jsonify)' is not defined", "Add 'from flask import jsonify' at top", 0.95),
        (r"name '(request)' is not defined", "Add 'from flask import request' at top", 0.95),
        (r"name '(db)' is not defined", "Add SQLAlchemy db import or initialization", 0.8),
    ],
    
    "SyntaxError": [
        (r"expected ':'", "Missing colon after def/if/for/while/class", 0.9),
        (r"invalid syntax.*'='", "Possibly using = instead of == in condition", 0.7),
        (r"unmatched '\)'", "Unbalanced parentheses - extra closing paren", 0.85),
        (r"unmatched '\('", "Unbalanced parentheses - extra opening paren", 0.85),
        (r"unexpected EOF", "Incomplete statement - missing closing bracket/quote", 0.8),
        (r"EOL while scanning string", "Unclosed string literal", 0.9),
        (r"f-string.*empty expression", "f-string has empty {} brackets", 0.95),
    ],
    
    "IndentationError": [
        (r"expected an indented block", "Add indentation after colon", 0.95),
        (r"unexpected indent", "Remove extra indentation", 0.9),
        (r"unindent does not match", "Fix inconsistent indentation (tabs vs spaces)", 0.85),
    ],
    
    "TypeError": [
        (r"'NoneType' object is not subscriptable", "Add null check before indexing", 0.8),
        (r"'NoneType' object is not iterable", "Add null check before iterating", 0.8),
        (r"'str' object does not support item assignment", "Strings are immutable - convert to list", 0.85),
        (r"unsupported operand type\(s\) for \+: '(\w+)' and '(\w+)'", "Type mismatch in addition", 0.75),
        (r"'(\w+)' object is not callable", "Missing operator or wrong type", 0.7),
    ],
    
    "AttributeError": [
        (r"'str' object has no attribute 'get'", "Expected dict, got string", 0.9),
        (r"'list' object has no attribute 'get'", "Expected dict, got list", 0.9),
        (r"'NoneType' object has no attribute '(\w+)'", "Object is None - add null check", 0.85),
        (r"module '(\w+)' has no attribute '(\w+)'", "Wrong import or method name", 0.7),
    ],
    
    "ImportError": [
        (r"No module named '(\w+)'", "Module not installed or wrong name", 0.8),
        (r"cannot import name '(\w+)' from '(\w+)'", "Name doesn't exist in module", 0.85),
    ],
    
    "ValueError": [
        (r"invalid literal for int\(\) with base 10", "String can't be converted to int", 0.9),
        (r"not enough values to unpack", "Tuple/list has fewer items than expected", 0.85),
        (r"too many values to unpack", "Tuple/list has more items than expected", 0.85),
    ],
    
    "KeyError": [
        (r"KeyError: '(\w+)'", "Key doesn't exist in dict - use .get() or check first", 0.85),
    ],
}

# Stdlib modules for auto-import
STDLIB_MODULES = {
    'os', 'sys', 're', 'json', 'math', 'random', 'datetime', 'time',
    'pathlib', 'collections', 'itertools', 'functools', 'typing',
    'io', 'csv', 'sqlite3', 'threading', 'subprocess', 'shutil',
    'hashlib', 'base64', 'urllib', 'http', 'email', 'html',
    'logging', 'unittest', 'dataclasses', 'enum', 'copy',
}

# Common Flask imports
FLASK_IMPORTS = {
    'Flask', 'request', 'jsonify', 'render_template', 'redirect',
    'url_for', 'session', 'flash', 'Blueprint', 'g', 'current_app',
}

# Common typing imports
TYPING_IMPORTS = {
    'Dict', 'List', 'Optional', 'Tuple', 'Set', 'Any', 'Union',
    'Callable', 'TypeVar', 'Generic', 'Sequence', 'Mapping',
}


class ErrorFixer:
    """AI-free error detection and fixing for Python code."""
    
    def __init__(self):
        self.patterns = ERROR_PATTERNS
        
    def validate_and_fix(self, code: str, filename: str = "<string>", 
                         max_attempts: int = 3) -> FixResult:
        """Validate code and attempt automatic fixes.
        
        Args:
            code: Python source code
            filename: For error messages
            max_attempts: Max fix iterations (for cascading fixes)
            
        Returns:
            FixResult with validation status and any fixes applied
        """
        all_fixes: List[Fix] = []
        current_code = code
        
        for attempt in range(max_attempts):
            # Try to compile
            try:
                compile(current_code, filename, 'exec')
                # No syntax errors - try AST parse for deeper analysis
                try:
                    tree = ast.parse(current_code)
                    
                    # Check for missing imports (proactive fix before runtime)
                    missing_fixes = self._fix_missing_imports(current_code, tree)
                    if missing_fixes:
                        all_fixes.extend(missing_fixes)
                        for fix in missing_fixes:
                            current_code = self._apply_fix(current_code, fix)
                    
                    return FixResult(
                        valid=True,
                        fixes=all_fixes,
                        fixed_code=current_code if all_fixes else None
                    )
                except SyntaxError as e:
                    error_info = self._parse_syntax_error(e, current_code)
                    
            except SyntaxError as e:
                error_info = self._parse_syntax_error(e, current_code)
                
            # Try to fix
            fix = self._attempt_fix(error_info, current_code)
            if fix:
                all_fixes.append(fix)
                current_code = self._apply_fix(current_code, fix)
            else:
                # Can't fix this error
                return FixResult(
                    valid=False,
                    errors=[f"{error_info['type']}: {error_info['message']} (line {error_info['line']})"],
                    fixes=all_fixes,
                    fixed_code=current_code if all_fixes else None
                )
        
        # Max attempts reached
        return FixResult(
            valid=False,
            errors=["Max fix attempts reached"],
            fixes=all_fixes,
            fixed_code=current_code if all_fixes else None
        )
    
    def _parse_syntax_error(self, e: SyntaxError, code: str) -> Dict:
        """Extract error info from SyntaxError."""
        return {
            'type': type(e).__name__,
            'message': str(e.msg) if hasattr(e, 'msg') else str(e),
            'line': e.lineno or 1,
            'offset': e.offset or 0,
            'text': e.text or "",
            'code': code,
        }
    
    def _attempt_fix(self, error_info: Dict, code: str) -> Optional[Fix]:
        """Try to fix an error using patterns and heuristics."""
        error_type = error_info['type']
        message = error_info['message']
        line = error_info['line']
        
        # Check pattern-based fixes
        if error_type in self.patterns:
            for pattern, explanation, confidence in self.patterns[error_type]:
                match = re.search(pattern, message)
                if match:
                    fix = self._create_fix_from_pattern(
                        error_type, pattern, match, explanation, 
                        confidence, code, line
                    )
                    if fix:
                        return fix
        
        # Try AST-based fixes
        if error_type == 'SyntaxError':
            fix = self._fix_syntax_error(error_info, code)
            if fix:
                return fix
                
        return None
    
    def _create_fix_from_pattern(self, error_type: str, pattern: str, 
                                  match: re.Match, explanation: str,
                                  confidence: float, code: str, 
                                  line: int) -> Optional[Fix]:
        """Create a fix based on matched pattern."""
        lines = code.split('\n')
        
        # Handle missing imports
        if 'import' in explanation.lower():
            name = match.group(1) if match.groups() else ""
            
            if name in STDLIB_MODULES:
                import_line = f"import {name}"
            elif name in FLASK_IMPORTS:
                # Check if flask is already imported
                existing = self._find_flask_import(code)
                if existing:
                    # Add to existing import
                    return self._add_to_existing_import(code, existing, name)
                import_line = f"from flask import {name}"
            elif name in TYPING_IMPORTS:
                existing = self._find_typing_import(code)
                if existing:
                    return self._add_to_existing_import(code, existing, name)
                import_line = f"from typing import {name}"
            elif name == 'datetime':
                import_line = "from datetime import datetime"
            elif name == 'Path':
                import_line = "from pathlib import Path"
            else:
                return None
                
            # Find best insertion point
            insert_line = self._find_import_insertion_point(lines)
            
            return Fix(
                error_type=error_type,
                line=insert_line,
                message=f"Add missing import: {import_line}",
                original="",
                replacement=import_line + "\n",
                confidence=confidence
            )
        
        return None
    
    def _fix_syntax_error(self, error_info: Dict, code: str) -> Optional[Fix]:
        """Try to fix common syntax errors."""
        message = error_info['message']
        line = error_info['line']
        lines = code.split('\n')
        
        if line > len(lines):
            return None
            
        problem_line = lines[line - 1]
        
        # Missing colon after def/if/for/while/class
        if 'expected' in message and ':' in message:
            if re.match(r'\s*(def|if|elif|else|for|while|class|try|except|finally|with)\b', problem_line):
                if not problem_line.rstrip().endswith(':'):
                    return Fix(
                        error_type='SyntaxError',
                        line=line,
                        message="Add missing colon",
                        original=problem_line,
                        replacement=problem_line.rstrip() + ':',
                        confidence=0.9
                    )
        
        # Unclosed parenthesis
        if 'unmatched' in message or 'EOF' in message:
            open_count = problem_line.count('(') - problem_line.count(')')
            if open_count > 0:
                return Fix(
                    error_type='SyntaxError',
                    line=line,
                    message="Add missing closing parenthesis",
                    original=problem_line,
                    replacement=problem_line.rstrip() + ')' * open_count,
                    confidence=0.7
                )
        
        return None
    
    def _find_flask_import(self, code: str) -> Optional[Tuple[int, str]]:
        """Find existing flask import line."""
        for i, line in enumerate(code.split('\n')):
            if re.match(r'from flask import', line):
                return (i + 1, line)
        return None
    
    def _find_typing_import(self, code: str) -> Optional[Tuple[int, str]]:
        """Find existing typing import line."""
        for i, line in enumerate(code.split('\n')):
            if re.match(r'from typing import', line):
                return (i + 1, line)
        return None
    
    def _add_to_existing_import(self, code: str, existing: Tuple[int, str], 
                                name: str) -> Fix:
        """Add name to existing import line."""
        line_num, line = existing
        # from flask import A, B -> from flask import A, B, C
        if name not in line:
            new_line = line.rstrip() + f", {name}"
            return Fix(
                error_type='NameError',
                line=line_num,
                message=f"Add {name} to existing import",
                original=line,
                replacement=new_line,
                confidence=0.9
            )
        return None
    
    def _find_import_insertion_point(self, lines: List[str]) -> int:
        """Find best line to insert new import."""
        last_import = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import = i + 1
        return last_import + 1 if last_import else 1
    
    def _apply_fix(self, code: str, fix: Fix) -> str:
        """Apply a fix to code."""
        lines = code.split('\n')
        
        if fix.original == "":
            # Insert new line
            lines.insert(fix.line - 1, fix.replacement.rstrip())
        else:
            # Replace existing line
            if fix.line <= len(lines):
                lines[fix.line - 1] = fix.replacement
        
        return '\n'.join(lines)
    
    def _fix_missing_imports(self, code: str, tree: ast.AST) -> List[Fix]:
        """Proactively fix missing imports before runtime using AST analysis."""
        fixes = []
        lines = code.split('\n')
        
        # Collect defined names (imports, assignments, function defs, etc.)
        defined = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined.add(node.name)
                for arg in node.args.args:
                    defined.add(arg.arg)
            elif isinstance(node, ast.ClassDef):
                defined.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined.add(target.id)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    defined.add(alias.asname or alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    defined.add(alias.asname or alias.name)
            elif isinstance(node, (ast.For, ast.comprehension)):
                if hasattr(node, 'target') and isinstance(node.target, ast.Name):
                    defined.add(node.target.id)
            elif isinstance(node, ast.ExceptHandler) and node.name:
                defined.add(node.name)
            elif isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        defined.add(item.optional_vars.id)
        
        # Collect used names
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                # Track the base of attribute access (e.g., json in json.loads)
                used.add(node.value.id)
        
        # Python builtins
        builtins_set = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
        builtins_set.update({'True', 'False', 'None', 'self', 'cls'})
        
        # Find undefined names that we can fix
        undefined = used - defined - builtins_set
        
        # Import mappings for common names
        import_map = {
            # Stdlib
            'json': 'import json',
            'os': 'import os',
            're': 'import re',
            'sys': 'import sys',
            'math': 'import math',
            'random': 'import random',
            'time': 'import time',
            'datetime': 'from datetime import datetime',
            'timedelta': 'from datetime import timedelta',
            'Path': 'from pathlib import Path',
            'dataclass': 'from dataclasses import dataclass',
            'field': 'from dataclasses import field',
            'Enum': 'from enum import Enum',
            'Optional': 'from typing import Optional',
            'List': 'from typing import List',
            'Dict': 'from typing import Dict',
            'Tuple': 'from typing import Tuple',
            'Set': 'from typing import Set',
            'Any': 'from typing import Any',
            'Union': 'from typing import Union',
            'Callable': 'from typing import Callable',
            # Flask
            'Flask': 'from flask import Flask',
            'request': 'from flask import request',
            'jsonify': 'from flask import jsonify',
            'render_template': 'from flask import render_template',
            'redirect': 'from flask import redirect',
            'url_for': 'from flask import url_for',
            'session': 'from flask import session',
            'flash': 'from flask import flash',
            'Blueprint': 'from flask import Blueprint',
            'g': 'from flask import g',
            'current_app': 'from flask import current_app',
            # SQLAlchemy
            'SQLAlchemy': 'from flask_sqlalchemy import SQLAlchemy',
            # Common others
            'wraps': 'from functools import wraps',
            'check_password_hash': 'from werkzeug.security import check_password_hash',
            'generate_password_hash': 'from werkzeug.security import generate_password_hash',
            'csv': 'import csv',
            'io': 'import io',
        }
        
        insert_line = self._find_import_insertion_point(lines)
        
        for name in undefined:
            if name in import_map:
                import_stmt = import_map[name]
                # Don't add if already present
                if import_stmt not in code and f"import {name}" not in code:
                    fixes.append(Fix(
                        error_type='NameError',
                        line=insert_line,
                        message=f"Add missing import: {import_stmt}",
                        original="",
                        replacement=import_stmt,
                        confidence=0.95
                    ))
                    insert_line += 1  # Next import goes after this one
        
        return fixes
    
    def check_undefined_names(self, code: str) -> List[str]:
        """Find potentially undefined names using AST."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        defined = set()
        used = set()
        
        for node in ast.walk(tree):
            # Track definitions
            if isinstance(node, ast.FunctionDef):
                defined.add(node.name)
                for arg in node.args.args:
                    defined.add(arg.arg)
            elif isinstance(node, ast.ClassDef):
                defined.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined.add(target.id)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    defined.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    defined.add(alias.asname or alias.name)
            
            # Track usage
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
        
        # Builtins are always defined
        builtins = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
        
        undefined = used - defined - builtins - {'True', 'False', 'None'}
        return list(undefined)
    
    def suggest_typo_fix(self, name: str, available: List[str]) -> Optional[str]:
        """Suggest fix for typo using fuzzy matching."""
        matches = difflib.get_close_matches(name, available, n=1, cutoff=0.6)
        return matches[0] if matches else None


def validate_generated_code(code: str, filename: str = "generated.py") -> FixResult:
    """Convenience function to validate generated code.
    
    Example:
        result = validate_generated_code(generated_app_py)
        if not result.valid:
            print("Errors:", result.errors)
        elif result.fixed:
            print("Auto-fixed issues:", result.fixes)
            code = result.fixed_code
    """
    fixer = ErrorFixer()
    return fixer.validate_and_fix(code, filename)


# =============================================================================
# INTEGRATION WITH APP FORGE
# =============================================================================

def validate_and_fix_files(files: Dict[str, str]) -> Tuple[Dict[str, str], List[str]]:
    """Validate all generated files and attempt to fix errors.
    
    Args:
        files: Dict of filename -> content
        
    Returns:
        (fixed_files, error_messages)
    """
    fixer = ErrorFixer()
    fixed_files = {}
    all_errors = []
    
    for filename, content in files.items():
        if filename.endswith('.py'):
            result = fixer.validate_and_fix(content, filename)
            
            if result.fixed_code:
                fixed_files[filename] = result.fixed_code
                for fix in result.fixes:
                    all_errors.append(f"[AUTO-FIXED] {filename}: {fix.message}")
            else:
                fixed_files[filename] = content
                
            if not result.valid:
                for err in result.errors:
                    all_errors.append(f"[ERROR] {filename}: {err}")
        else:
            # Non-Python files pass through
            fixed_files[filename] = content
    
    return fixed_files, all_errors


# =============================================================================
# CLI / TESTING
# =============================================================================

if __name__ == "__main__":
    # Test the error fixer
    print("=" * 60)
    print("Error Fixer Test Suite")
    print("=" * 60)
    
    # Test 1: Missing import
    code1 = """
def greet():
    data = json.loads('{"name": "test"}')
    return data['name']
"""
    print("\nTest 1: Missing import (json)")
    result = validate_generated_code(code1)
    print(f"  Valid: {result.valid}, Fixed: {result.fixed}")
    if result.fixes:
        print(f"  Fix: {result.fixes[0].message}")
    
    # Test 2: Missing colon
    code2 = """
def greet()
    return "Hello"
"""
    print("\nTest 2: Missing colon")
    result = validate_generated_code(code2)
    print(f"  Valid: {result.valid}, Fixed: {result.fixed}")
    if result.fixes:
        print(f"  Fix: {result.fixes[0].message}")
    
    # Test 3: Valid code
    code3 = """
def greet():
    return "Hello"
"""
    print("\nTest 3: Valid code")
    result = validate_generated_code(code3)
    print(f"  Valid: {result.valid}, Fixed: {result.fixed}")
    
    # Test 4: Multiple issues
    code4 = """
def process()
    data = json.loads('{}')
    return data
"""
    print("\nTest 4: Multiple issues (missing colon + import)")
    result = validate_generated_code(code4)
    print(f"  Valid: {result.valid}, Fixed: {result.fixed}")
    print(f"  Fixes applied: {len(result.fixes)}")
    for fix in result.fixes:
        print(f"    - {fix.message}")
    
    # Test 5: App Forge integration
    print("\n" + "=" * 60)
    print("App Forge Integration Test")
    print("=" * 60)
    
    files = {
        "app.py": '''
from flask import Flask
app = Flask(__name__)

@app.route('/')
def index()
    data = json.dumps({"status": "ok"})
    return data
''',
        "README.md": "# Test App"
    }
    
    fixed, errors = validate_and_fix_files(files)
    print(f"\nProcessed {len(files)} files")
    print(f"Errors/Fixes: {errors}")
    if fixed.get('app.py'):
        print("\nFixed app.py:")
        print(fixed['app.py'][:200] + "..." if len(fixed['app.py']) > 200 else fixed['app.py'])
    
    print("\n" + "=" * 60)
    print("All tests complete!")
