"""
Beyond Belief: Revolutionary Code Intelligence Without AI

This module contains features that push the boundaries of what's possible
without machine learning:

1. Cross-Language Synthesis - Same contract → Python, TypeScript, Go, Rust, Java
2. Refinement Types - Types that encode invariants: `count: int where count >= 0`
3. Program Synthesis from Tests - Give examples, system infers the pattern
4. Inverse Scaffolding - Extract contracts from existing code
5. Executable Specifications - The spec IS the program

Each feature works through pure logic, pattern matching, and deduction.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from pathlib import Path
import re
import ast
import json
from abc import ABC, abstractmethod

# Import our contract system
from contracts import Contract, Field, ContractRegistry


# ============================================================================
# 1. CROSS-LANGUAGE SYNTHESIS
# ============================================================================

class LanguageTarget(ABC):
    """Base class for language-specific code generators."""
    
    name: str = "base"
    extension: str = ".txt"
    
    @abstractmethod
    def generate_model(self, contract: Contract) -> str:
        """Generate a model/struct/class from contract."""
        pass
    
    @abstractmethod
    def generate_validation(self, contract: Contract) -> str:
        """Generate validation logic from invariants."""
        pass
    
    def type_map(self, field_type: str) -> str:
        """Map abstract types to language-specific types."""
        return field_type


class PythonTarget(LanguageTarget):
    """Python code generator."""
    
    name = "python"
    extension = ".py"
    
    TYPE_MAP = {
        "string": "str",
        "text": "str",
        "integer": "int",
        "float": "float",
        "boolean": "bool",
        "datetime": "datetime",
        "date": "date",
        "list": "List[Any]",
        "dict": "Dict[str, Any]",
        "uuid": "str",
    }
    
    def type_map(self, field_type: str) -> str:
        return self.TYPE_MAP.get(field_type, field_type)
    
    def generate_model(self, contract: Contract) -> str:
        lines = [
            "from dataclasses import dataclass, field",
            "from typing import Optional, List, Dict, Any",
            "from datetime import datetime, date",
            "",
            "",
            "@dataclass",
            f"class {contract.name}:",
            f'    """{contract.description}"""' if contract.description else "",
            "",
        ]
        
        for f in contract.fields:
            py_type = self.type_map(f.type)
            if not f.required:
                py_type = f"Optional[{py_type}]"
            
            if f.default is not None:
                lines.append(f"    {f.name}: {py_type} = {repr(f.default)}")
            elif not f.required:
                lines.append(f"    {f.name}: {py_type} = None")
            else:
                lines.append(f"    {f.name}: {py_type}")
        
        return "\n".join(lines)
    
    def generate_validation(self, contract: Contract) -> str:
        lines = [
            "",
            "    def validate(self) -> List[str]:",
            '        """Validate all invariants."""',
            "        errors = []",
        ]
        
        for inv in contract.invariants:
            cond = self._invariant_to_code(inv)
            lines.append(f"        if not ({cond}):")
            lines.append(f'            errors.append("{inv}")')
        
        lines.append("        return errors")
        return "\n".join(lines)
    
    def _invariant_to_code(self, inv: str) -> str:
        patterns = [
            (r"(\w+) cannot be empty", r"len(self.\1) > 0"),
            (r"(\w+) must be positive", r"self.\1 > 0"),
            (r"(\w+) >= (\d+)", r"self.\1 >= \2"),
            (r"(\w+) <= (\d+)", r"self.\1 <= \2"),
            (r"(\w+) > (\d+)", r"self.\1 > \2"),
            (r"(\w+) < (\d+)", r"self.\1 < \2"),
        ]
        for pattern, replacement in patterns:
            if re.match(pattern, inv, re.IGNORECASE):
                return re.sub(pattern, replacement, inv, flags=re.IGNORECASE)
        return "True  # TODO: " + inv


class TypeScriptTarget(LanguageTarget):
    """TypeScript code generator."""
    
    name = "typescript"
    extension = ".ts"
    
    TYPE_MAP = {
        "string": "string",
        "text": "string",
        "integer": "number",
        "float": "number",
        "boolean": "boolean",
        "datetime": "Date",
        "date": "Date",
        "list": "any[]",
        "dict": "Record<string, any>",
        "uuid": "string",
    }
    
    def type_map(self, field_type: str) -> str:
        return self.TYPE_MAP.get(field_type, field_type)
    
    def generate_model(self, contract: Contract) -> str:
        lines = [
            f"// {contract.name} - {contract.description}",
            "",
            f"export interface {contract.name} {{",
        ]
        
        for f in contract.fields:
            ts_type = self.type_map(f.type)
            opt = "" if f.required else "?"
            lines.append(f"  {f.name}{opt}: {ts_type};")
        
        lines.append("}")
        return "\n".join(lines)
    
    def generate_validation(self, contract: Contract) -> str:
        lines = [
            "",
            f"export function validate{contract.name}(obj: {contract.name}): string[] {{",
            "  const errors: string[] = [];",
        ]
        
        for inv in contract.invariants:
            cond = self._invariant_to_code(inv)
            lines.append(f"  if (!({cond})) {{")
            lines.append(f'    errors.push("{inv}");')
            lines.append("  }")
        
        lines.append("  return errors;")
        lines.append("}")
        return "\n".join(lines)
    
    def _invariant_to_code(self, inv: str) -> str:
        patterns = [
            (r"(\w+) cannot be empty", r"obj.\1.length > 0"),
            (r"(\w+) must be positive", r"obj.\1 > 0"),
            (r"(\w+) >= (\d+)", r"obj.\1 >= \2"),
            (r"(\w+) <= (\d+)", r"obj.\1 <= \2"),
        ]
        for pattern, replacement in patterns:
            if re.match(pattern, inv, re.IGNORECASE):
                return re.sub(pattern, replacement, inv, flags=re.IGNORECASE)
        return "true"


class GoTarget(LanguageTarget):
    """Go code generator."""
    
    name = "go"
    extension = ".go"
    
    TYPE_MAP = {
        "string": "string",
        "text": "string",
        "integer": "int",
        "float": "float64",
        "boolean": "bool",
        "datetime": "time.Time",
        "date": "time.Time",
        "list": "[]interface{}",
        "dict": "map[string]interface{}",
        "uuid": "string",
    }
    
    def type_map(self, field_type: str) -> str:
        return self.TYPE_MAP.get(field_type, field_type)
    
    def generate_model(self, contract: Contract) -> str:
        lines = [
            "package models",
            "",
            "import (",
            '    "time"',
            ")",
            "",
            f"// {contract.name} - {contract.description}",
            f"type {contract.name} struct {{",
        ]
        
        for f in contract.fields:
            go_type = self.type_map(f.type)
            if not f.required:
                go_type = "*" + go_type
            
            # Go uses PascalCase for exported fields
            field_name = f.name[0].upper() + f.name[1:]
            json_tag = f'`json:"{f.name}"`'
            lines.append(f"    {field_name} {go_type} {json_tag}")
        
        lines.append("}")
        return "\n".join(lines)
    
    def generate_validation(self, contract: Contract) -> str:
        lines = [
            "",
            f"// Validate checks all invariants for {contract.name}",
            f"func (m *{contract.name}) Validate() []string {{",
            "    var errors []string",
        ]
        
        for inv in contract.invariants:
            cond = self._invariant_to_code(inv)
            lines.append(f"    if !({cond}) {{")
            lines.append(f'        errors = append(errors, "{inv}")')
            lines.append("    }")
        
        lines.append("    return errors")
        lines.append("}")
        return "\n".join(lines)
    
    def _invariant_to_code(self, inv: str) -> str:
        patterns = [
            (r"(\w+) cannot be empty", lambda m: f"len(m.{m.group(1).title()}) > 0"),
            (r"(\w+) >= (\d+)", lambda m: f"m.{m.group(1).title()} >= {m.group(2)}"),
            (r"(\w+) <= (\d+)", lambda m: f"m.{m.group(1).title()} <= {m.group(2)}"),
        ]
        for pattern, replacement in patterns:
            match = re.match(pattern, inv, re.IGNORECASE)
            if match:
                if callable(replacement):
                    return replacement(match)
                return re.sub(pattern, replacement, inv, flags=re.IGNORECASE)
        return "true"


class RustTarget(LanguageTarget):
    """Rust code generator."""
    
    name = "rust"
    extension = ".rs"
    
    TYPE_MAP = {
        "string": "String",
        "text": "String",
        "integer": "i64",
        "float": "f64",
        "boolean": "bool",
        "datetime": "chrono::DateTime<chrono::Utc>",
        "date": "chrono::NaiveDate",
        "list": "Vec<serde_json::Value>",
        "dict": "std::collections::HashMap<String, serde_json::Value>",
        "uuid": "String",
    }
    
    def type_map(self, field_type: str) -> str:
        return self.TYPE_MAP.get(field_type, field_type)
    
    def generate_model(self, contract: Contract) -> str:
        lines = [
            "use serde::{Deserialize, Serialize};",
            "",
            f"/// {contract.description}",
            "#[derive(Debug, Clone, Serialize, Deserialize)]",
            f"pub struct {contract.name} {{",
        ]
        
        for f in contract.fields:
            rust_type = self.type_map(f.type)
            if not f.required:
                rust_type = f"Option<{rust_type}>"
            
            lines.append(f"    pub {f.name}: {rust_type},")
        
        lines.append("}")
        return "\n".join(lines)
    
    def generate_validation(self, contract: Contract) -> str:
        lines = [
            "",
            f"impl {contract.name} {{",
            "    /// Validate all invariants",
            "    pub fn validate(&self) -> Vec<String> {",
            "        let mut errors = Vec::new();",
        ]
        
        for inv in contract.invariants:
            cond = self._invariant_to_code(inv)
            lines.append(f"        if !({cond}) {{")
            lines.append(f'            errors.push("{inv}".to_string());')
            lines.append("        }")
        
        lines.append("        errors")
        lines.append("    }")
        lines.append("}")
        return "\n".join(lines)
    
    def _invariant_to_code(self, inv: str) -> str:
        patterns = [
            (r"(\w+) cannot be empty", r"!self.\1.is_empty()"),
            (r"(\w+) >= (\d+)", r"self.\1 >= \2"),
            (r"(\w+) <= (\d+)", r"self.\1 <= \2"),
        ]
        for pattern, replacement in patterns:
            if re.match(pattern, inv, re.IGNORECASE):
                return re.sub(pattern, replacement, inv, flags=re.IGNORECASE)
        return "true"


class JavaTarget(LanguageTarget):
    """Java code generator."""
    
    name = "java"
    extension = ".java"
    
    TYPE_MAP = {
        "string": "String",
        "text": "String",
        "integer": "Long",
        "float": "Double",
        "boolean": "Boolean",
        "datetime": "LocalDateTime",
        "date": "LocalDate",
        "list": "List<Object>",
        "dict": "Map<String, Object>",
        "uuid": "String",
    }
    
    def type_map(self, field_type: str) -> str:
        return self.TYPE_MAP.get(field_type, field_type)
    
    def generate_model(self, contract: Contract) -> str:
        lines = [
            "import java.time.*;",
            "import java.util.*;",
            "",
            f"/**",
            f" * {contract.description}",
            f" */",
            f"public class {contract.name} {{",
        ]
        
        # Fields
        for f in contract.fields:
            java_type = self.type_map(f.type)
            lines.append(f"    private {java_type} {f.name};")
        
        lines.append("")
        
        # Constructor
        params = ", ".join(f"{self.type_map(f.type)} {f.name}" for f in contract.fields if f.required)
        lines.append(f"    public {contract.name}({params}) {{")
        for f in contract.fields:
            if f.required:
                lines.append(f"        this.{f.name} = {f.name};")
        lines.append("    }")
        lines.append("")
        
        # Getters/Setters
        for f in contract.fields:
            java_type = self.type_map(f.type)
            cap_name = f.name[0].upper() + f.name[1:]
            lines.append(f"    public {java_type} get{cap_name}() {{ return {f.name}; }}")
            lines.append(f"    public void set{cap_name}({java_type} {f.name}) {{ this.{f.name} = {f.name}; }}")
        
        lines.append("}")
        return "\n".join(lines)
    
    def generate_validation(self, contract: Contract) -> str:
        lines = [
            "",
            "    public List<String> validate() {",
            "        List<String> errors = new ArrayList<>();",
        ]
        
        for inv in contract.invariants:
            cond = self._invariant_to_code(inv)
            lines.append(f"        if (!({cond})) {{")
            lines.append(f'            errors.add("{inv}");')
            lines.append("        }")
        
        lines.append("        return errors;")
        lines.append("    }")
        return "\n".join(lines)
    
    def _invariant_to_code(self, inv: str) -> str:
        patterns = [
            (r"(\w+) cannot be empty", r"this.\1 != null && !this.\1.isEmpty()"),
            (r"(\w+) >= (\d+)", r"this.\1 >= \2"),
            (r"(\w+) <= (\d+)", r"this.\1 <= \2"),
        ]
        for pattern, replacement in patterns:
            if re.match(pattern, inv, re.IGNORECASE):
                return re.sub(pattern, replacement, inv, flags=re.IGNORECASE)
        return "true"


# Registry of all language targets
LANGUAGE_TARGETS = {
    "python": PythonTarget(),
    "typescript": TypeScriptTarget(),
    "go": GoTarget(),
    "rust": RustTarget(),
    "java": JavaTarget(),
}


class CrossLanguageSynthesizer:
    """
    Generate code for any language from a single contract.
    
    Usage:
        synth = CrossLanguageSynthesizer(contract)
        synth.generate_all("output/")
    """
    
    def __init__(self, contract: Contract):
        self.contract = contract
    
    def generate(self, language: str) -> str:
        """Generate code for a specific language."""
        if language not in LANGUAGE_TARGETS:
            raise ValueError(f"Unknown language: {language}. Available: {list(LANGUAGE_TARGETS.keys())}")
        
        target = LANGUAGE_TARGETS[language]
        model = target.generate_model(self.contract)
        validation = target.generate_validation(self.contract)
        return model + validation
    
    def generate_all(self, output_dir: str) -> Dict[str, str]:
        """Generate code for all supported languages."""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        
        files = {}
        name_lower = self.contract.name.lower()
        
        for lang, target in LANGUAGE_TARGETS.items():
            code = self.generate(lang)
            filename = f"{name_lower}{target.extension}"
            filepath = output / lang / filename
            filepath.parent.mkdir(exist_ok=True)
            filepath.write_text(code)
            files[f"{lang}/{filename}"] = code
        
        return files


# ============================================================================
# 2. REFINEMENT TYPES
# ============================================================================

@dataclass
class RefinementType:
    """
    A type with embedded constraints/refinements.
    
    Example: `count: int where count >= 0 and count <= 100`
    
    Refinement types let us express constraints that are PART of the type,
    not separate validation logic. This means invalid values are literally
    impossible to construct.
    """
    base_type: str
    name: str
    refinements: List[str] = field(default_factory=list)
    
    def to_python(self) -> str:
        """Generate Python NewType with runtime validation."""
        type_map = {"int": "int", "float": "float", "str": "str", "bool": "bool"}
        base = type_map.get(self.base_type, self.base_type)
        
        lines = [
            f"class {self.name}({base}):",
            f'    """Refined {base} with constraints: {", ".join(self.refinements)}"""',
            "",
            "    def __new__(cls, value):",
        ]
        
        for ref in self.refinements:
            condition = self._refinement_to_condition(ref, "value")
            lines.append(f"        if not ({condition}):")
            lines.append(f'            raise ValueError(f"{self.name} constraint violated: {ref}")')
        
        lines.append(f"        return super().__new__(cls, value)")
        return "\n".join(lines)
    
    def to_typescript(self) -> str:
        """Generate TypeScript branded type with validation."""
        type_map = {"int": "number", "float": "number", "str": "string", "bool": "boolean"}
        base = type_map.get(self.base_type, self.base_type)
        
        lines = [
            f"// Branded type for {self.name}",
            f"type {self.name} = {base} & {{ readonly __{self.name}: unique symbol }};",
            "",
            f"function create{self.name}(value: {base}): {self.name} {{",
        ]
        
        for ref in self.refinements:
            condition = self._refinement_to_condition(ref, "value")
            lines.append(f"  if (!({condition})) {{")
            lines.append(f'    throw new Error("{self.name} constraint violated: {ref}");')
            lines.append("  }")
        
        lines.append(f"  return value as {self.name};")
        lines.append("}")
        return "\n".join(lines)
    
    def to_rust(self) -> str:
        """Generate Rust newtype with validation."""
        type_map = {"int": "i64", "float": "f64", "str": "String", "bool": "bool"}
        base = type_map.get(self.base_type, type_map.get(self.base_type, self.base_type))
        
        lines = [
            f"/// Refined {base} with constraints: {', '.join(self.refinements)}",
            "#[derive(Debug, Clone, PartialEq)]",
            f"pub struct {self.name}({base});",
            "",
            f"impl {self.name} {{",
            f"    pub fn new(value: {base}) -> Result<Self, String> {{",
        ]
        
        for ref in self.refinements:
            condition = self._refinement_to_condition(ref, "value")
            lines.append(f"        if !({condition}) {{")
            lines.append(f'            return Err(format!("{self.name} constraint violated: {ref}"));')
            lines.append("        }")
        
        lines.append(f"        Ok(Self(value))")
        lines.append("    }")
        lines.append("")
        lines.append(f"    pub fn value(&self) -> &{base} {{")
        lines.append("        &self.0")
        lines.append("    }")
        lines.append("}")
        return "\n".join(lines)
    
    def _refinement_to_condition(self, refinement: str, var: str) -> str:
        """Convert a refinement to a condition expression."""
        # Replace 'self' or field name with var
        ref = refinement.strip()
        
        # Handle common patterns
        patterns = [
            (r"^>= (\d+)$", f"{var} >= \\1"),
            (r"^<= (\d+)$", f"{var} <= \\1"),
            (r"^> (\d+)$", f"{var} > \\1"),
            (r"^< (\d+)$", f"{var} < \\1"),
            (r"^!= (\d+)$", f"{var} != \\1"),
            (r"^positive$", f"{var} > 0"),
            (r"^non-negative$", f"{var} >= 0"),
            (r"^not empty$", f"len({var}) > 0"),
        ]
        
        for pattern, replacement in patterns:
            if re.match(pattern, ref, re.IGNORECASE):
                return re.sub(pattern, replacement, ref, flags=re.IGNORECASE)
        
        return ref  # Return as-is if no pattern matches


def parse_refined_type(spec: str) -> RefinementType:
    """
    Parse a refinement type specification.
    
    Format: "name: type where condition [and condition]*"
    Example: "age: int where >= 0 and <= 150"
    """
    match = re.match(r"(\w+):\s*(\w+)(?:\s+where\s+(.+))?", spec)
    if not match:
        raise ValueError(f"Invalid refinement type spec: {spec}")
    
    name, base_type, conditions = match.groups()
    
    refinements = []
    if conditions:
        # Split on 'and' but not inside parentheses
        refinements = [c.strip() for c in re.split(r"\s+and\s+", conditions)]
    
    return RefinementType(base_type=base_type, name=name, refinements=refinements)


# ============================================================================
# 3. PROGRAM SYNTHESIS FROM TESTS
# ============================================================================

@dataclass
class Example:
    """An input-output example for synthesis."""
    inputs: Dict[str, Any]
    output: Any


class ProgramSynthesizer:
    """
    Synthesize programs from input-output examples.
    
    Uses enumeration and constraint-based synthesis to find
    programs that match all examples.
    
    Currently supports:
    - Arithmetic expressions
    - String transformations
    - List operations
    """
    
    OPERATIONS = {
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: a / b if b != 0 else None,
        "mod": lambda a, b: a % b if b != 0 else None,
        "concat": lambda a, b: str(a) + str(b),
        "upper": lambda a: a.upper() if isinstance(a, str) else None,
        "lower": lambda a: a.lower() if isinstance(a, str) else None,
        "length": lambda a: len(a) if hasattr(a, "__len__") else None,
        "first": lambda a: a[0] if a else None,
        "last": lambda a: a[-1] if a else None,
        "reverse": lambda a: a[::-1] if hasattr(a, "__getitem__") else None,
        "double": lambda a: a * 2,
        "negate": lambda a: -a if isinstance(a, (int, float)) else None,
        "abs": lambda a: abs(a) if isinstance(a, (int, float)) else None,
    }
    
    def __init__(self, examples: List[Example]):
        self.examples = examples
        self.input_names = list(examples[0].inputs.keys()) if examples else []
    
    def synthesize(self, max_depth: int = 3) -> Optional[str]:
        """
        Try to find a program that matches all examples.
        
        Returns a string representation of the program or None.
        """
        # Try direct input
        for name in self.input_names:
            if self._matches_all(lambda e: e.inputs[name]):
                return f"return {name}"
        
        # Try single operations on inputs
        for op_name, op in self.OPERATIONS.items():
            for name in self.input_names:
                if self._matches_all(lambda e, o=op, n=name: self._safe_call(o, e.inputs[n])):
                    return f"return {op_name}({name})"
        
        # Try binary operations
        if len(self.input_names) >= 2:
            for op_name in ["add", "sub", "mul", "div", "mod", "concat"]:
                op = self.OPERATIONS[op_name]
                for n1 in self.input_names:
                    for n2 in self.input_names:
                        if self._matches_all(lambda e, o=op, a=n1, b=n2: 
                                           self._safe_call(o, e.inputs[a], e.inputs[b])):
                            return f"return {op_name}({n1}, {n2})"
        
        # Try constant combinations
        for name in self.input_names:
            for const in [0, 1, 2, 10, 100]:
                for op_name in ["add", "sub", "mul"]:
                    op = self.OPERATIONS[op_name]
                    if self._matches_all(lambda e, o=op, n=name, c=const: 
                                       self._safe_call(o, e.inputs[n], c)):
                        return f"return {op_name}({name}, {const})"
                    if self._matches_all(lambda e, o=op, n=name, c=const: 
                                       self._safe_call(o, c, e.inputs[n])):
                        return f"return {op_name}({const}, {name})"
        
        # Try composed operations
        for op1_name, op1 in self.OPERATIONS.items():
            for op2_name, op2 in self.OPERATIONS.items():
                for name in self.input_names:
                    if self._matches_all(lambda e, o1=op1, o2=op2, n=name:
                                       self._safe_call(o2, self._safe_call(o1, e.inputs[n]))):
                        return f"return {op2_name}({op1_name}({name}))"
        
        return None
    
    def _matches_all(self, program: Callable) -> bool:
        """Check if program produces correct output for all examples."""
        for ex in self.examples:
            try:
                result = program(ex)
                if result != ex.output:
                    return False
            except:
                return False
        return True
    
    def _safe_call(self, op: Callable, *args) -> Any:
        """Safely call an operation, returning None on error."""
        try:
            return op(*args)
        except:
            return None
    
    def to_python_function(self, name: str = "synthesized") -> Optional[str]:
        """Generate a Python function from synthesized program."""
        program = self.synthesize()
        if not program:
            return None
        
        params = ", ".join(self.input_names)
        
        # Transform the program string to valid Python
        body = program.replace("return ", "")
        
        # Replace our operation names with Python equivalents
        replacements = {
            "add(": "(",
            ", ": " + ",  # for add
            "sub(": "(",
            "mul(": "(",
            "div(": "(",
            "concat(": "str(",
            "upper(": "(",
            "lower(": "(",
            "length(": "len(",
            "double(": "2 * (",
            "negate(": "-(",
            "abs(": "abs(",
        }
        
        for old, new in replacements.items():
            body = body.replace(old, new)
        
        return f"""def {name}({params}):
    return {body}"""


# ============================================================================
# 4. INVERSE SCAFFOLDING - Extract Contracts from Code
# ============================================================================

class CodeAnalyzer:
    """
    Analyze existing Python code to extract implicit contracts.
    
    This is the "inverse scaffolding" - reverse engineer code
    into specifications.
    """
    
    def analyze_file(self, filepath: str) -> List[Contract]:
        """Analyze a Python file and extract contracts."""
        with open(filepath) as f:
            source = f.read()
        return self.analyze_source(source)
    
    def analyze_source(self, source: str) -> List[Contract]:
        """Analyze Python source code and extract contracts."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        
        contracts = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                contract = self._extract_from_class(node)
                if contract:
                    contracts.append(contract)
        
        return contracts
    
    def _extract_from_class(self, node: ast.ClassDef) -> Optional[Contract]:
        """Extract a contract from a class definition."""
        fields = []
        invariants = []
        description = ""
        
        # Get docstring
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            description = node.body[0].value.value.strip()
        
        # Check if it's a dataclass
        is_dataclass = any(
            isinstance(d, ast.Name) and d.id == "dataclass"
            for d in node.decorator_list
        ) or any(
            isinstance(d, ast.Call) and 
            isinstance(d.func, ast.Name) and 
            d.func.id == "dataclass"
            for d in node.decorator_list
        )
        
        # Extract fields from annotations
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field = self._extract_field(item)
                if field:
                    fields.append(field)
            
            # Look for validation methods to extract invariants
            if isinstance(item, ast.FunctionDef) and item.name == "validate":
                invariants.extend(self._extract_invariants(item))
            
            # Look for __init__ to extract fields
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                fields.extend(self._extract_init_fields(item))
        
        if fields:
            return Contract(
                name=node.name,
                description=description,
                fields=fields,
                invariants=invariants,
            )
        return None
    
    def _extract_field(self, node: ast.AnnAssign) -> Optional[Field]:
        """Extract a field from an annotated assignment."""
        name = node.target.id
        
        # Get type
        field_type = self._annotation_to_type(node.annotation)
        
        # Check if optional
        required = True
        if isinstance(node.annotation, ast.Subscript):
            if isinstance(node.annotation.value, ast.Name):
                if node.annotation.value.id == "Optional":
                    required = False
        
        # Get default
        default = None
        if node.value is not None:
            default = self._get_literal_value(node.value)
        
        return Field(
            name=name,
            type=field_type,
            required=required,
            default=default,
        )
    
    def _annotation_to_type(self, node: ast.expr) -> str:
        """Convert a type annotation to our type string."""
        if isinstance(node, ast.Name):
            type_map = {
                "str": "string",
                "int": "integer",
                "float": "float",
                "bool": "boolean",
                "datetime": "datetime",
                "date": "date",
                "list": "list",
                "dict": "dict",
            }
            return type_map.get(node.id, node.id)
        
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                if node.value.id == "Optional":
                    return self._annotation_to_type(node.slice)
                elif node.value.id == "List":
                    return "list"
                elif node.value.id == "Dict":
                    return "dict"
        
        return "string"  # Default fallback
    
    def _get_literal_value(self, node: ast.expr) -> Any:
        """Extract a literal value from an AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name) and node.id == "None":
            return None
        if isinstance(node, ast.List):
            return []
        if isinstance(node, ast.Dict):
            return {}
        return None
    
    def _extract_invariants(self, node: ast.FunctionDef) -> List[str]:
        """Extract invariants from a validate method."""
        invariants = []
        
        for item in ast.walk(node):
            if isinstance(item, ast.If):
                # Look for "if not (condition)"
                if isinstance(item.test, ast.UnaryOp) and isinstance(item.test.op, ast.Not):
                    inv = self._condition_to_invariant(item.test.operand)
                    if inv:
                        invariants.append(inv)
        
        return invariants
    
    def _condition_to_invariant(self, node: ast.expr) -> Optional[str]:
        """Convert a condition AST to an invariant string."""
        if isinstance(node, ast.Compare):
            # Handle: self.x >= 0
            if isinstance(node.left, ast.Attribute):
                field = node.left.attr
                if node.ops and isinstance(node.comparators[0], ast.Constant):
                    op_map = {
                        ast.GtE: ">=",
                        ast.LtE: "<=",
                        ast.Gt: ">",
                        ast.Lt: "<",
                        ast.Eq: "==",
                        ast.NotEq: "!=",
                    }
                    op = op_map.get(type(node.ops[0]))
                    val = node.comparators[0].value
                    if op:
                        return f"{field} {op} {val}"
        
        if isinstance(node, ast.Call):
            # Handle: len(self.x) > 0
            if isinstance(node.func, ast.Name) and node.func.id == "len":
                if node.args and isinstance(node.args[0], ast.Attribute):
                    return f"{node.args[0].attr} cannot be empty"
        
        return None
    
    def _extract_init_fields(self, node: ast.FunctionDef) -> List[Field]:
        """Extract fields from __init__ assignments."""
        fields = []
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Attribute) and target.attr != "__class__":
                        # self.x = something
                        if isinstance(target.value, ast.Name) and target.value.id == "self":
                            field = Field(
                                name=target.attr,
                                type="string",  # Can't infer type well
                                required=True,
                            )
                            fields.append(field)
        
        return fields


# ============================================================================
# 5. EXECUTABLE SPECIFICATIONS
# ============================================================================

class ExecutableSpec:
    """
    An executable specification - the spec IS the program.
    
    Inspired by Prolog and constraint programming. Instead of generating
    code from a spec, we directly execute the spec as if it were code.
    
    This is real magic - specifications that run.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.fields: Dict[str, RefinementType] = {}
        self.relations: Dict[str, Callable] = {}
        self.rules: List[Tuple[str, Callable]] = []
        self.data: List[Dict[str, Any]] = []
    
    def field(self, name: str, type_spec: str) -> "ExecutableSpec":
        """Define a field with refinement type."""
        ref_type = parse_refined_type(f"{name}: {type_spec}")
        self.fields[name] = ref_type
        return self
    
    def relation(self, name: str, fn: Callable) -> "ExecutableSpec":
        """Define a relation between fields."""
        self.relations[name] = fn
        return self
    
    def rule(self, name: str, predicate: Callable) -> "ExecutableSpec":
        """Define a rule that must hold for all instances."""
        self.rules.append((name, predicate))
        return self
    
    def create(self, **kwargs) -> Dict[str, Any]:
        """Create an instance, enforcing all constraints."""
        instance = {}
        
        # Validate fields
        for name, ref_type in self.fields.items():
            if name in kwargs:
                value = kwargs[name]
                # Check refinements
                for ref in ref_type.refinements:
                    if not self._check_refinement(ref, value):
                        raise ValueError(f"Field {name} violates: {ref}")
                instance[name] = value
            elif ref_type.refinements:
                raise ValueError(f"Required field missing: {name}")
        
        # Add any extra fields
        for name, value in kwargs.items():
            if name not in instance:
                instance[name] = value
        
        # Check rules
        for rule_name, predicate in self.rules:
            if not predicate(instance):
                raise ValueError(f"Rule violated: {rule_name}")
        
        self.data.append(instance)
        return instance
    
    def query(self, predicate: Callable) -> List[Dict[str, Any]]:
        """Query instances matching a predicate."""
        return [d for d in self.data if predicate(d)]
    
    def _check_refinement(self, refinement: str, value: Any) -> bool:
        """Check if a value satisfies a refinement."""
        ref = refinement.strip()
        
        if ref.startswith(">="):
            return value >= int(ref[2:].strip())
        if ref.startswith("<="):
            return value <= int(ref[2:].strip())
        if ref.startswith(">"):
            return value > int(ref[1:].strip())
        if ref.startswith("<"):
            return value < int(ref[1:].strip())
        if ref == "positive":
            return value > 0
        if ref == "non-negative":
            return value >= 0
        if ref == "not empty":
            return len(value) > 0
        
        return True
    
    def to_python(self) -> str:
        """Generate equivalent Python class."""
        lines = [
            "from dataclasses import dataclass",
            "from typing import List, Any",
            "",
            "@dataclass",
            f"class {self.name}:",
        ]
        
        for name, ref_type in self.fields.items():
            py_type = {"int": "int", "str": "str", "float": "float", "bool": "bool"}.get(
                ref_type.base_type, "Any"
            )
            lines.append(f"    {name}: {py_type}")
        
        lines.append("")
        lines.append("    def __post_init__(self):")
        lines.append("        self._validate()")
        lines.append("")
        lines.append("    def _validate(self):")
        
        for name, ref_type in self.fields.items():
            for ref in ref_type.refinements:
                cond = self._refinement_to_python(ref, f"self.{name}")
                lines.append(f"        if not ({cond}):")
                lines.append(f'            raise ValueError(f"{name} violates: {ref}")')
        
        for rule_name, _ in self.rules:
            lines.append(f"        # Rule: {rule_name}")
        
        return "\n".join(lines)
    
    def _refinement_to_python(self, ref: str, var: str) -> str:
        """Convert refinement to Python condition."""
        if ref.startswith(">="):
            return f"{var} >= {ref[2:].strip()}"
        if ref.startswith("<="):
            return f"{var} <= {ref[2:].strip()}"
        if ref == "positive":
            return f"{var} > 0"
        if ref == "non-negative":
            return f"{var} >= 0"
        if ref == "not empty":
            return f"len({var}) > 0"
        return "True"


# ============================================================================
# CLI
# ============================================================================

def demo_cross_language():
    """Demo cross-language synthesis."""
    print("\n" + "=" * 60)
    print("  CROSS-LANGUAGE SYNTHESIS")
    print("  One contract → Python, TypeScript, Go, Rust, Java")
    print("=" * 60)
    
    contract = Contract(
        name="Task",
        description="A task in a todo application",
        fields=[
            Field("id", "string", True),
            Field("title", "string", True),
            Field("priority", "integer", True, default=1),
            Field("completed", "boolean", False, default=False),
        ],
        invariants=[
            "title cannot be empty",
            "priority >= 1",
            "priority <= 5",
        ],
    )
    
    synth = CrossLanguageSynthesizer(contract)
    
    for lang in ["python", "typescript", "go", "rust", "java"]:
        print(f"\n--- {lang.upper()} ---\n")
        print(synth.generate(lang))


def demo_refinement_types():
    """Demo refinement types."""
    print("\n" + "=" * 60)
    print("  REFINEMENT TYPES")
    print("  Types with built-in constraints")
    print("=" * 60)
    
    specs = [
        "Age: int where >= 0 and <= 150",
        "Percentage: float where >= 0 and <= 100",
        "NonEmptyString: str where not empty",
    ]
    
    for spec in specs:
        print(f"\n--- {spec} ---")
        ref = parse_refined_type(spec)
        print("\nPython:")
        print(ref.to_python())
        print("\nTypeScript:")
        print(ref.to_typescript())
        print("\nRust:")
        print(ref.to_rust())


def demo_program_synthesis():
    """Demo program synthesis from examples."""
    print("\n" + "=" * 60)
    print("  PROGRAM SYNTHESIS FROM EXAMPLES")
    print("  Give examples, get programs")
    print("=" * 60)
    
    # Example 1: Double
    examples = [
        Example({"x": 1}, 2),
        Example({"x": 5}, 10),
        Example({"x": 0}, 0),
    ]
    
    synth = ProgramSynthesizer(examples)
    print("\n--- Examples: (1→2), (5→10), (0→0) ---")
    print(f"Synthesized: {synth.synthesize()}")
    print(synth.to_python_function("double"))
    
    # Example 2: Add
    examples = [
        Example({"a": 1, "b": 2}, 3),
        Example({"a": 5, "b": 5}, 10),
        Example({"a": 0, "b": 7}, 7),
    ]
    
    synth = ProgramSynthesizer(examples)
    print("\n--- Examples: (1,2→3), (5,5→10), (0,7→7) ---")
    print(f"Synthesized: {synth.synthesize()}")
    print(synth.to_python_function("add"))
    
    # Example 3: String length
    examples = [
        Example({"s": "hello"}, 5),
        Example({"s": "a"}, 1),
        Example({"s": ""}, 0),
    ]
    
    synth = ProgramSynthesizer(examples)
    print("\n--- Examples: ('hello'→5), ('a'→1), (''→0) ---")
    print(f"Synthesized: {synth.synthesize()}")
    print(synth.to_python_function("string_length"))


def demo_inverse_scaffolding():
    """Demo inverse scaffolding - extract contracts from code."""
    print("\n" + "=" * 60)
    print("  INVERSE SCAFFOLDING")
    print("  Extract contracts from existing code")
    print("=" * 60)
    
    code = '''
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class User:
    """A user in the system."""
    id: str
    email: str
    name: str
    age: Optional[int] = None
    active: bool = True
    
    def validate(self) -> List[str]:
        errors = []
        if not (len(self.name) > 0):
            errors.append("name required")
        if not (self.age >= 0):
            errors.append("age must be non-negative")
        return errors

@dataclass
class Post:
    """A blog post."""
    id: str
    title: str
    content: str
    author_id: str
    likes: int = 0
'''
    
    print("\n--- Original Code ---\n")
    print(code)
    
    analyzer = CodeAnalyzer()
    contracts = analyzer.analyze_source(code)
    
    print("\n--- Extracted Contracts ---\n")
    for contract in contracts:
        print(contract.to_spec())
        print()


def demo_executable_spec():
    """Demo executable specifications."""
    print("\n" + "=" * 60)
    print("  EXECUTABLE SPECIFICATIONS")
    print("  The spec IS the program")
    print("=" * 60)
    
    # Define spec
    task_spec = (
        ExecutableSpec("Task")
        .field("title", "str where not empty")
        .field("priority", "int where >= 1 and <= 5")
        .rule("high_priority_needs_due_date", 
              lambda t: t.get("priority", 0) < 4 or t.get("due_date") is not None)
    )
    
    print("\n--- Executable Spec Definition ---")
    print("  Task")
    print("    title: str where not empty")
    print("    priority: int where >= 1 and <= 5")
    print("    rule: high_priority_needs_due_date")
    
    print("\n--- Creating Instances ---")
    
    # Create valid instances
    try:
        t1 = task_spec.create(title="Buy groceries", priority=2)
        print(f"  Created: {t1}")
    except ValueError as e:
        print(f"  Error: {e}")
    
    try:
        t2 = task_spec.create(title="Urgent meeting", priority=5, due_date="2024-01-15")
        print(f"  Created: {t2}")
    except ValueError as e:
        print(f"  Error: {e}")
    
    # Create invalid instance
    try:
        t3 = task_spec.create(title="", priority=3)
        print(f"  Created: {t3}")
    except ValueError as e:
        print(f"  Rejected (expected): {e}")
    
    try:
        t4 = task_spec.create(title="Test", priority=6)
        print(f"  Created: {t4}")
    except ValueError as e:
        print(f"  Rejected (expected): {e}")
    
    print("\n--- Query: priority < 3 ---")
    results = task_spec.query(lambda t: t.get("priority", 0) < 3)
    for r in results:
        print(f"  {r}")
    
    print("\n--- Generated Python Class ---")
    print(task_spec.to_python())


def main():
    """Run all demos."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Beyond Belief Features")
    parser.add_argument("--all", action="store_true", help="Run all demos")
    parser.add_argument("--cross-lang", action="store_true", help="Cross-language synthesis")
    parser.add_argument("--refinement", action="store_true", help="Refinement types")
    parser.add_argument("--synthesis", action="store_true", help="Program synthesis")
    parser.add_argument("--inverse", action="store_true", help="Inverse scaffolding")
    parser.add_argument("--executable", action="store_true", help="Executable specs")
    
    args = parser.parse_args()
    
    if args.all or not any([args.cross_lang, args.refinement, args.synthesis, 
                           args.inverse, args.executable]):
        demo_cross_language()
        demo_refinement_types()
        demo_program_synthesis()
        demo_inverse_scaffolding()
        demo_executable_spec()
    else:
        if args.cross_lang:
            demo_cross_language()
        if args.refinement:
            demo_refinement_types()
        if args.synthesis:
            demo_program_synthesis()
        if args.inverse:
            demo_inverse_scaffolding()
        if args.executable:
            demo_executable_spec()


if __name__ == "__main__":
    main()
