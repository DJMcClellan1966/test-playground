"""
Property-Based Testing
Expert testing technique - describe properties, generate tests.

Instead of: assert sort([3,1,2]) == [1,2,3]
Property: For any list xs, sort(xs) is sorted and has same elements

Benefits:
- Finds edge cases humans miss
- Tests properties, not examples
- Automatic shrinking to minimal failing case
"""
import random
from typing import List, Any, Callable, TypeVar, Optional
from dataclasses import dataclass

T = TypeVar('T')


# ============================================================================
# GENERATORS
# ============================================================================

class Generator:
    """Generates random test data"""
    
    @staticmethod
    def integer(min_val: int = -1000, max_val: int = 1000) -> int:
        return random.randint(min_val, max_val)
    
    @staticmethod
    def positive_int(max_val: int = 1000) -> int:
        return random.randint(1, max_val)
    
    @staticmethod
    def string(max_length: int = 20) -> str:
        length = random.randint(0, max_length)
        chars = 'abcdefghijklmnopqrstuvwxyz '
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def list_of(gen: Callable[[], T], max_length: int = 20) -> List[T]:
        length = random.randint(0, max_length)
        return [gen() for _ in range(length)]
    
    @staticmethod
    def one_of(*values: T) -> T:
        return random.choice(values)


# ============================================================================
# PROPERTY TESTING ENGINE
# ============================================================================

@dataclass
class TestResult:
    passed: bool
    num_tests: int
    counterexample: Optional[Any] = None
    shrunk_example: Optional[Any] = None
    exception: Optional[Exception] = None


def shrink_int(n: int) -> List[int]:
    """Generate smaller integers to find minimal counterexample"""
    if n == 0:
        return []
    candidates = [0]
    if n > 0:
        candidates.extend([n // 2, n - 1])
    else:
        candidates.extend([n // 2, n + 1])
    return candidates


def shrink_list(xs: List[T]) -> List[List[T]]:
    """Generate smaller lists"""
    if not xs:
        return []
    
    candidates = []
    # Try removing elements
    for i in range(len(xs)):
        candidates.append(xs[:i] + xs[i+1:])
    # Try halving
    if len(xs) > 1:
        candidates.append(xs[:len(xs)//2])
        candidates.append(xs[len(xs)//2:])
    return candidates


def check_property(
    prop: Callable[..., bool],
    generators: List[Callable[[], Any]],
    num_tests: int = 100
) -> TestResult:
    """
    Run property-based test.
    
    Args:
        prop: Property function that returns True if property holds
        generators: List of generators for each argument
        num_tests: Number of random tests to run
    """
    for i in range(num_tests):
        # Generate random inputs
        inputs = tuple(gen() for gen in generators)
        
        try:
            result = prop(*inputs)
            if not result:
                # Property failed - try to shrink
                shrunk = shrink_counterexample(prop, inputs, generators)
                return TestResult(
                    passed=False,
                    num_tests=i + 1,
                    counterexample=inputs,
                    shrunk_example=shrunk
                )
        except Exception as e:
            return TestResult(
                passed=False,
                num_tests=i + 1,
                counterexample=inputs,
                exception=e
            )
    
    return TestResult(passed=True, num_tests=num_tests)


def shrink_counterexample(
    prop: Callable[..., bool],
    inputs: tuple,
    generators: List[Callable[[], Any]]
) -> tuple:
    """Try to find smaller failing input"""
    current = inputs
    
    # Try shrinking each input
    for idx in range(len(current)):
        val = current[idx]
        
        # Get shrink candidates based on type
        if isinstance(val, int):
            candidates = shrink_int(val)
        elif isinstance(val, list):
            candidates = shrink_list(val)
        else:
            candidates = []
        
        for candidate in candidates:
            new_inputs = current[:idx] + (candidate,) + current[idx+1:]
            try:
                if not prop(*new_inputs):
                    current = new_inputs
                    break
            except:
                current = new_inputs
                break
    
    return current


# ============================================================================
# EXAMPLE PROPERTIES
# ============================================================================

def is_sorted(xs: List[int]) -> bool:
    """Check if list is sorted"""
    return all(xs[i] <= xs[i+1] for i in range(len(xs) - 1))


def same_elements(xs: List[int], ys: List[int]) -> bool:
    """Check if two lists have same elements (as multiset)"""
    return sorted(xs) == sorted(ys)


# Properties to test

def prop_sort_is_sorted(xs: List[int]) -> bool:
    """Property: sorted list is actually sorted"""
    return is_sorted(sorted(xs))


def prop_sort_same_elements(xs: List[int]) -> bool:
    """Property: sorting preserves elements"""
    return same_elements(xs, sorted(xs))


def prop_sort_idempotent(xs: List[int]) -> bool:
    """Property: sorting twice equals sorting once"""
    return sorted(sorted(xs)) == sorted(xs)


def prop_reverse_involution(xs: List[int]) -> bool:
    """Property: reversing twice gives original"""
    return list(reversed(list(reversed(xs)))) == xs


def prop_append_length(xs: List[int], ys: List[int]) -> bool:
    """Property: length of concatenation equals sum of lengths"""
    return len(xs + ys) == len(xs) + len(ys)


# A buggy implementation to demonstrate failure detection
def buggy_sort(xs: List[int]) -> List[int]:
    """A sort that fails on lists > 5 elements"""
    if len(xs) <= 5:
        return sorted(xs)
    return xs  # Bug: doesn't actually sort long lists


def prop_buggy_sort_works(xs: List[int]) -> bool:
    """This property will fail and be shrunk"""
    return is_sorted(buggy_sort(xs))


def demo():
    print("=== Property-Based Testing Demo ===\n")
    
    # Test correct implementations
    print("Testing sorted():")
    tests = [
        ("is sorted", prop_sort_is_sorted),
        ("preserves elements", prop_sort_same_elements),
        ("is idempotent", prop_sort_idempotent),
    ]
    
    for name, prop in tests:
        result = check_property(
            prop,
            [lambda: Generator.list_of(Generator.integer, 15)],
            num_tests=100
        )
        status = "✓ PASSED" if result.passed else "✗ FAILED"
        print(f"  {name}: {status} ({result.num_tests} tests)")
    
    print("\nTesting list operations:")
    result = check_property(
        prop_reverse_involution,
        [lambda: Generator.list_of(Generator.integer)],
    )
    print(f"  reverse(reverse(x)) == x: {'✓' if result.passed else '✗'}")
    
    result = check_property(
        prop_append_length,
        [
            lambda: Generator.list_of(Generator.integer),
            lambda: Generator.list_of(Generator.integer)
        ]
    )
    print(f"  len(x ++ y) == len(x) + len(y): {'✓' if result.passed else '✗'}")
    
    # Test buggy implementation
    print("\nTesting buggy_sort (should fail):")
    result = check_property(
        prop_buggy_sort_works,
        [lambda: Generator.list_of(Generator.integer)],
        num_tests=50
    )
    if not result.passed:
        print(f"  ✗ Found counterexample after {result.num_tests} tests")
        print(f"    Original: {result.counterexample}")
        print(f"    Shrunk:   {result.shrunk_example}")
    
    print("\n=== Key Concepts ===")
    print("1. Properties > Examples: Describe invariants, not cases")
    print("2. Random generation: Explore input space automatically")
    print("3. Shrinking: Find minimal failing example")
    print("4. Common properties: idempotence, commutativity, round-trip")


if __name__ == "__main__":
    demo()
