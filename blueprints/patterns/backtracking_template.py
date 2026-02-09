"""
Backtracking Template
From: Skiena's "Algorithm Design Manual"

A universal pattern for exploring solution spaces.
Use when: combinations, permutations, constraint satisfaction.
"""
from typing import List, Any


def backtrack_template(
    state: Any,
    choices: List[Any],
    results: List[Any],
    is_solution: callable,
    is_valid: callable
):
    """
    Universal backtracking template.
    
    Parameters:
    - state: Current partial solution
    - choices: Available choices at this step
    - results: Accumulator for all solutions
    - is_solution: Check if state is complete solution
    - is_valid: Check if choice is valid given current state
    """
    if is_solution(state):
        results.append(state.copy())
        return
    
    for choice in choices:
        if is_valid(state, choice):
            # Make choice
            state.append(choice)
            
            # Recurse
            backtrack_template(state, choices, results, is_solution, is_valid)
            
            # Undo choice (backtrack)
            state.pop()


# ============================================================================
# EXAMPLE 1: Generate all subsets
# ============================================================================

def subsets(nums: List[int]) -> List[List[int]]:
    """Generate all subsets (power set)"""
    results = []
    
    def backtrack(start: int, current: List[int]):
        results.append(current.copy())
        
        for i in range(start, len(nums)):
            current.append(nums[i])
            backtrack(i + 1, current)
            current.pop()
    
    backtrack(0, [])
    return results


# ============================================================================
# EXAMPLE 2: N-Queens Problem
# ============================================================================

def n_queens(n: int) -> List[List[str]]:
    """Solve N-Queens: place N queens on NxN board with no attacks"""
    results = []
    
    def is_safe(queens: List[int], row: int, col: int) -> bool:
        for r, c in enumerate(queens):
            if c == col:  # Same column
                return False
            if abs(r - row) == abs(c - col):  # Same diagonal
                return False
        return True
    
    def backtrack(queens: List[int]):
        row = len(queens)
        if row == n:
            # Convert to board representation
            board = []
            for c in queens:
                board.append("." * c + "Q" + "." * (n - c - 1))
            results.append(board)
            return
        
        for col in range(n):
            if is_safe(queens, row, col):
                queens.append(col)
                backtrack(queens)
                queens.pop()
    
    backtrack([])
    return results


def demo():
    print("=== Subsets ===")
    nums = [1, 2, 3]
    print(f"Subsets of {nums}:")
    for subset in subsets(nums):
        print(f"  {subset}")
    
    print("\n=== N-Queens (4x4) ===")
    solutions = n_queens(4)
    print(f"Found {len(solutions)} solutions")
    for i, board in enumerate(solutions[:2]):  # Show first 2
        print(f"\nSolution {i + 1}:")
        for row in board:
            print(f"  {row}")


if __name__ == "__main__":
    demo()
