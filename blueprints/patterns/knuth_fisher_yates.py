"""
Fisher-Yates Shuffle Algorithm
From: Knuth's "The Art of Computer Programming"

The only correct way to shuffle an array uniformly at random.
Each permutation has exactly 1/n! probability.
"""
import random


def fisher_yates_shuffle(arr: list) -> list:
    """
    Shuffle array in-place using Fisher-Yates algorithm.
    
    Algorithm:
    1. Start from the last element
    2. Swap it with a random element from [0, i]
    3. Move to i-1 and repeat
    
    Why it works: Each position has equal probability of any element.
    """
    arr = arr.copy()  # Don't modify original
    n = len(arr)
    
    for i in range(n - 1, 0, -1):
        # Pick random index from 0 to i (inclusive)
        j = random.randint(0, i)
        # Swap
        arr[i], arr[j] = arr[j], arr[i]
    
    return arr


def biased_shuffle_wrong(arr: list) -> list:
    """
    WRONG way to shuffle - creates biased distribution!
    Don't do this - shown for educational purposes.
    """
    arr = arr.copy()
    n = len(arr)
    for i in range(n):
        j = random.randint(0, n - 1)  # Bug: should be randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def demo():
    cards = ["A♠", "K♠", "Q♠", "J♠", "10♠"]
    
    print("Original deck:", cards)
    print("\nShuffled (Fisher-Yates):")
    for i in range(3):
        print(f"  {i+1}: {fisher_yates_shuffle(cards)}")
    
    # Test uniformity
    print("\nTesting uniformity (first position distribution for [0,1,2]):")
    counts = {0: 0, 1: 0, 2: 0}
    for _ in range(30000):
        shuffled = fisher_yates_shuffle([0, 1, 2])
        counts[shuffled[0]] += 1
    
    for val, count in counts.items():
        print(f"  {val} appeared first: {count/300:.1f}% (expected: 33.3%)")


if __name__ == "__main__":
    demo()
