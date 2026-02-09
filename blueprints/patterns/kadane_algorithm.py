"""
Kadane's Algorithm - Maximum Subarray Sum
From: Bentley's "Programming Pearls"

Find the contiguous subarray with the largest sum.
This is the OPTIMAL solution: O(n) time, O(1) space.
"""
from typing import List, Tuple


def kadane(arr: List[int]) -> int:
    """
    Find maximum subarray sum.
    
    Key insight: At each position, either:
    1. Extend the previous subarray, OR
    2. Start a new subarray here
    
    max_ending_here = max(arr[i], max_ending_here + arr[i])
    """
    if not arr:
        return 0
    
    max_so_far = arr[0]
    max_ending_here = arr[0]
    
    for i in range(1, len(arr)):
        # Either extend or start fresh
        max_ending_here = max(arr[i], max_ending_here + arr[i])
        max_so_far = max(max_so_far, max_ending_here)
    
    return max_so_far


def kadane_with_indices(arr: List[int]) -> Tuple[int, int, int]:
    """Find maximum subarray sum AND the indices"""
    if not arr:
        return 0, 0, 0
    
    max_so_far = arr[0]
    max_ending_here = arr[0]
    
    start = end = 0
    temp_start = 0
    
    for i in range(1, len(arr)):
        if arr[i] > max_ending_here + arr[i]:
            max_ending_here = arr[i]
            temp_start = i
        else:
            max_ending_here = max_ending_here + arr[i]
        
        if max_ending_here > max_so_far:
            max_so_far = max_ending_here
            start = temp_start
            end = i
    
    return max_so_far, start, end


def demo():
    arr = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    print(f"Array: {arr}")
    
    max_sum = kadane(arr)
    print(f"\nMaximum subarray sum: {max_sum}")
    
    total, start, end = kadane_with_indices(arr)
    subarray = arr[start:end + 1]
    print(f"Subarray: {subarray} (indices {start} to {end})")
    
    # Edge cases
    print("\nEdge cases:")
    print(f"  All negative [-3, -1, -2]: {kadane([-3, -1, -2])}")
    print(f"  Single element [5]: {kadane([5])}")
    print(f"  All positive [1, 2, 3]: {kadane([1, 2, 3])}")


if __name__ == "__main__":
    demo()
