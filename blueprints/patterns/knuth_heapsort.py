"""
Heapsort Algorithm
From: Knuth's "The Art of Computer Programming"

Guarantees O(n log n) in ALL cases (unlike quicksort).
In-place, but not stable.
"""
from typing import List


def heapify(arr: List[int], n: int, i: int):
    """
    Maintain max-heap property for subtree rooted at index i.
    
    A max-heap has: parent >= both children
    For node at i:
        - Left child: 2*i + 1
        - Right child: 2*i + 2
        - Parent: (i-1) // 2
    """
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    
    # Check if left child exists and is greater than root
    if left < n and arr[left] > arr[largest]:
        largest = left
    
    # Check if right child exists and is greater than current largest
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    # If largest is not root, swap and continue heapifying
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)


def heapsort(arr: List[int]) -> List[int]:
    """
    Sort array using heapsort algorithm.
    
    Steps:
    1. Build max-heap from array
    2. Extract max (move to end), reduce heap size
    3. Repeat until sorted
    """
    arr = arr.copy()
    n = len(arr)
    
    # Build max-heap (start from last non-leaf node)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    
    # Extract elements one by one
    for i in range(n - 1, 0, -1):
        # Move current root (max) to end
        arr[0], arr[i] = arr[i], arr[0]
        # Heapify reduced heap
        heapify(arr, i, 0)
    
    return arr


def demo():
    arr = [64, 34, 25, 12, 22, 11, 90]
    print(f"Original: {arr}")
    print(f"Sorted:   {heapsort(arr)}")
    
    # Show heap building process
    print("\nHeap building visualization:")
    test = [4, 10, 3, 5, 1]
    print(f"  Input: {test}")
    
    # Build heap step by step
    for i in range((len(test) // 2) - 1, -1, -1):
        heapify(test, len(test), i)
        print(f"  After heapify({i}): {test}")


if __name__ == "__main__":
    demo()
