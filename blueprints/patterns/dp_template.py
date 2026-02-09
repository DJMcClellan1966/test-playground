"""
Dynamic Programming Templates
Essential patterns for optimization problems.

When to use DP:
1. Optimal substructure (optimal solution uses optimal sub-solutions)
2. Overlapping subproblems (same computation repeated)
"""
from functools import lru_cache
from typing import List


# ============================================================================
# PATTERN 1: Top-Down (Memoization)
# ============================================================================

@lru_cache(maxsize=None)
def fibonacci_memo(n: int) -> int:
    """Classic example - O(n) with memoization vs O(2^n) naive"""
    if n <= 1:
        return n
    return fibonacci_memo(n - 1) + fibonacci_memo(n - 2)


# ============================================================================
# PATTERN 2: Bottom-Up (Tabulation)
# ============================================================================

def fibonacci_tab(n: int) -> int:
    """Bottom-up - explicit table, often faster"""
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    
    return dp[n]


# ============================================================================
# PATTERN 3: Space Optimized
# ============================================================================

def fibonacci_opt(n: int) -> int:
    """O(1) space - when only previous states matter"""
    if n <= 1:
        return n
    
    prev, curr = 0, 1
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    
    return curr


# ============================================================================
# CLASSIC: Longest Common Subsequence (LCS)
# ============================================================================

def lcs(s1: str, s2: str) -> str:
    """Find longest common subsequence"""
    m, n = len(s1), len(s2)
    
    # Build DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    # Reconstruct solution
    result = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            result.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    
    return "".join(reversed(result))


# ============================================================================
# CLASSIC: 0/1 Knapsack
# ============================================================================

def knapsack(weights: List[int], values: List[int], capacity: int) -> int:
    """Classic 0/1 knapsack - O(n * capacity)"""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Don't take item i
            dp[i][w] = dp[i - 1][w]
            
            # Take item i (if it fits)
            if weights[i - 1] <= w:
                dp[i][w] = max(
                    dp[i][w],
                    dp[i - 1][w - weights[i - 1]] + values[i - 1]
                )
    
    return dp[n][capacity]


def demo():
    print("=== Fibonacci (3 approaches, same result) ===")
    n = 20
    print(f"fib({n}) = {fibonacci_memo(n)} = {fibonacci_tab(n)} = {fibonacci_opt(n)}")
    
    print("\n=== Longest Common Subsequence ===")
    s1, s2 = "ABCDGH", "AEDFHR"
    print(f"LCS('{s1}', '{s2}') = '{lcs(s1, s2)}'")
    
    print("\n=== 0/1 Knapsack ===")
    weights = [1, 3, 4, 5]
    values = [1, 4, 5, 7]
    capacity = 7
    print(f"Weights: {weights}, Values: {values}, Capacity: {capacity}")
    print(f"Max value: {knapsack(weights, values, capacity)}")


if __name__ == "__main__":
    demo()
