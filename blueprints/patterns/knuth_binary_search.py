"""
Binary Search and Its Variations
From: Knuth's "The Art of Computer Programming"

The most important search algorithm - O(log n) complexity.
"""
from typing import List, Optional


def binary_search(arr: List[int], target: int) -> Optional[int]:
    """Find exact match, return index or None"""
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2  # Prevent overflow
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return None


def lower_bound(arr: List[int], target: int) -> int:
    """
    Find first position where target could be inserted.
    Returns index of first element >= target.
    """
    left, right = 0, len(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    
    return left


def upper_bound(arr: List[int], target: int) -> int:
    """
    Find last position where target could be inserted.
    Returns index of first element > target.
    """
    left, right = 0, len(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        if arr[mid] <= target:
            left = mid + 1
        else:
            right = mid
    
    return left


def count_occurrences(arr: List[int], target: int) -> int:
    """Count how many times target appears using bounds"""
    return upper_bound(arr, target) - lower_bound(arr, target)


def demo():
    arr = [1, 2, 2, 2, 3, 4, 4, 5, 6]
    print(f"Array: {arr}")
    
    # Basic search
    print(f"\nSearch for 4: index {binary_search(arr, 4)}")
    print(f"Search for 7: {binary_search(arr, 7)}")
    
    # Bounds
    print(f"\nLower bound of 2: {lower_bound(arr, 2)} (first 2)")
    print(f"Upper bound of 2: {upper_bound(arr, 2)} (after last 2)")
    print(f"Count of 2s: {count_occurrences(arr, 2)}")
    
    # Practical: find insertion point
    print(f"\nInsert 3.5 at position: {upper_bound(arr, 3)}")


if __name__ == "__main__":
    demo()
