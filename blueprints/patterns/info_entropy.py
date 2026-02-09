"""
Information Entropy
From: Shannon's "A Mathematical Theory of Communication"

Entropy measures the average "surprise" or information content.
Fundamental to: compression, ML (cross-entropy loss), decision trees.
"""
import math
from typing import List, Dict
from collections import Counter


def entropy(probabilities: List[float]) -> float:
    """
    Calculate Shannon entropy: H = -Σ p(x) * log2(p(x))
    
    Entropy is maximized when all outcomes are equally likely.
    Entropy is 0 when outcome is certain.
    """
    return -sum(p * math.log2(p) for p in probabilities if p > 0)


def entropy_from_data(data: List) -> float:
    """Calculate entropy from a list of observations"""
    n = len(data)
    if n == 0:
        return 0.0
    
    counts = Counter(data)
    probabilities = [count / n for count in counts.values()]
    return entropy(probabilities)


def information_content(probability: float) -> float:
    """
    Information content (self-information) of single event.
    I(x) = -log2(p(x))
    
    Lower probability = higher information when it occurs.
    """
    if probability <= 0:
        return float('inf')
    return -math.log2(probability)


def cross_entropy(true_probs: List[float], pred_probs: List[float]) -> float:
    """
    Cross-entropy: H(p, q) = -Σ p(x) * log2(q(x))
    
    Used in ML as loss function - measures how well q predicts p.
    """
    return -sum(p * math.log2(q) for p, q in zip(true_probs, pred_probs) if p > 0 and q > 0)


def kl_divergence(p: List[float], q: List[float]) -> float:
    """
    Kullback-Leibler divergence: D_KL(P || Q)
    
    Measures how different Q is from P.
    Not symmetric: D_KL(P||Q) ≠ D_KL(Q||P)
    """
    return sum(pi * math.log2(pi / qi) for pi, qi in zip(p, q) if pi > 0 and qi > 0)


def demo():
    print("=== Information Content ===")
    print(f"Fair coin flip: {information_content(0.5):.2f} bits")
    print(f"Rolling a 6: {information_content(1/6):.2f} bits")
    print(f"Rare event (1%): {information_content(0.01):.2f} bits")
    
    print("\n=== Entropy ===")
    fair_coin = [0.5, 0.5]
    biased_coin = [0.9, 0.1]
    fair_die = [1/6] * 6
    
    print(f"Fair coin: {entropy(fair_coin):.3f} bits")
    print(f"Biased coin (90/10): {entropy(biased_coin):.3f} bits")
    print(f"Fair 6-sided die: {entropy(fair_die):.3f} bits")
    
    print("\n=== Entropy from Data ===")
    text = "AAABBC"
    print(f"String '{text}': {entropy_from_data(text):.3f} bits")
    
    print("\n=== Cross-Entropy (ML Loss) ===")
    true = [1.0, 0.0, 0.0]  # One-hot: class 0
    good_pred = [0.9, 0.05, 0.05]
    bad_pred = [0.1, 0.8, 0.1]
    print(f"Good prediction: {cross_entropy(true, good_pred):.3f}")
    print(f"Bad prediction: {cross_entropy(true, bad_pred):.3f}")


if __name__ == "__main__":
    demo()
