"""
Greedy Algorithms
Make locally optimal choices hoping for global optimum.

Works when problem has:
1. Greedy choice property (local optimal → global optimal)
2. Optimal substructure
"""
from typing import List, Tuple


# ============================================================================
# CLASSIC: Activity Selection
# ============================================================================

def activity_selection(activities: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Select maximum non-overlapping activities.
    
    activities: List of (start, end) tuples
    
    Greedy strategy: Always pick the activity that finishes earliest.
    Why it works: Leaves maximum room for future activities.
    """
    # Sort by end time
    sorted_acts = sorted(activities, key=lambda x: x[1])
    
    result = [sorted_acts[0]]
    last_end = sorted_acts[0][1]
    
    for start, end in sorted_acts[1:]:
        if start >= last_end:  # No overlap
            result.append((start, end))
            last_end = end
    
    return result


# ============================================================================
# CLASSIC: Coin Change (Greedy when denominations allow)
# ============================================================================

def coin_change_greedy(amount: int, coins: List[int] = [25, 10, 5, 1]) -> List[int]:
    """
    Make change using minimum coins (greedy).
    
    WARNING: Only works for certain coin systems!
    US coins [25,10,5,1] work, but [1,3,4] for amount 6 would fail.
    (Greedy gives 4+1+1=3 coins, optimal is 3+3=2 coins)
    """
    result = []
    coins = sorted(coins, reverse=True)  # Largest first
    
    for coin in coins:
        while amount >= coin:
            result.append(coin)
            amount -= coin
    
    return result


# ============================================================================
# CLASSIC: Fractional Knapsack
# ============================================================================

def fractional_knapsack(
    weights: List[float], 
    values: List[float], 
    capacity: float
) -> Tuple[float, List[Tuple[int, float]]]:
    """
    Fractional knapsack - can take fractions of items.
    
    Greedy strategy: Take items with highest value/weight ratio first.
    
    Unlike 0/1 knapsack, greedy IS optimal here!
    """
    n = len(weights)
    # (index, value_per_weight)
    ratios = [(i, values[i] / weights[i]) for i in range(n)]
    ratios.sort(key=lambda x: x[1], reverse=True)
    
    total_value = 0
    taken = []  # (item_index, fraction_taken)
    
    for idx, ratio in ratios:
        if capacity <= 0:
            break
        
        if weights[idx] <= capacity:
            # Take whole item
            taken.append((idx, 1.0))
            total_value += values[idx]
            capacity -= weights[idx]
        else:
            # Take fraction
            fraction = capacity / weights[idx]
            taken.append((idx, fraction))
            total_value += values[idx] * fraction
            capacity = 0
    
    return total_value, taken


# ============================================================================
# CLASSIC: Huffman Coding (build optimal prefix code)
# ============================================================================

def huffman_codes(freq: dict) -> dict:
    """
    Build Huffman codes for characters based on frequency.
    
    Greedy: Always merge two lowest-frequency nodes.
    Result: Optimal prefix-free code for compression.
    """
    import heapq
    
    # Create heap of (frequency, id, node)
    heap = [(f, i, (char, None, None)) for i, (char, f) in enumerate(freq.items())]
    heapq.heapify(heap)
    counter = len(heap)
    
    while len(heap) > 1:
        f1, _, left = heapq.heappop(heap)
        f2, _, right = heapq.heappop(heap)
        
        # Merge nodes
        merged = (None, left, right)
        heapq.heappush(heap, (f1 + f2, counter, merged))
        counter += 1
    
    # Build codes by traversing tree
    codes = {}
    
    def traverse(node, code=""):
        char, left, right = node
        if char is not None:
            codes[char] = code or "0"
        else:
            if left:
                traverse(left, code + "0")
            if right:
                traverse(right, code + "1")
    
    if heap:
        traverse(heap[0][2])
    
    return codes


def demo():
    print("=== Activity Selection ===")
    activities = [(1, 4), (3, 5), (0, 6), (5, 7), (3, 9), (5, 9), (6, 10), (8, 11)]
    selected = activity_selection(activities)
    print(f"Activities: {activities}")
    print(f"Selected {len(selected)}: {selected}")
    
    print("\n=== Coin Change ===")
    amount = 67
    coins = coin_change_greedy(amount)
    print(f"Change for {amount}¢: {coins}")
    print(f"Total coins: {len(coins)}")
    
    print("\n=== Fractional Knapsack ===")
    weights = [10, 20, 30]
    values = [60, 100, 120]
    capacity = 50
    value, taken = fractional_knapsack(weights, values, capacity)
    print(f"Weights: {weights}, Values: {values}, Capacity: {capacity}")
    print(f"Max value: {value}")
    print(f"Items taken: {taken}")
    
    print("\n=== Huffman Coding ===")
    freq = {'a': 45, 'b': 13, 'c': 12, 'd': 16, 'e': 9, 'f': 5}
    codes = huffman_codes(freq)
    print(f"Frequencies: {freq}")
    print("Huffman codes:")
    for char, code in sorted(codes.items()):
        print(f"  '{char}': {code}")


if __name__ == "__main__":
    demo()
