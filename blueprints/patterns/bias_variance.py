"""
Bias-Variance Tradeoff
From: Bishop's "Pattern Recognition and Machine Learning"

Error = Bias² + Variance + Irreducible Noise

- High Bias: Model too simple, underfits (misses patterns)
- High Variance: Model too complex, overfits (memorizes noise)
"""
import random
from typing import List, Tuple


def generate_data(n: int = 50, noise: float = 0.3) -> Tuple[List[float], List[float]]:
    """Generate noisy data from y = sin(x)"""
    x = [random.uniform(0, 2 * 3.14159) for _ in range(n)]
    y = [math.sin(xi) + random.gauss(0, noise) for xi in x]
    return x, y


import math


def polynomial_fit(x: List[float], y: List[float], degree: int) -> List[float]:
    """
    Fit polynomial of given degree using least squares.
    Returns coefficients [a0, a1, a2, ...] for a0 + a1*x + a2*x² + ...
    
    Note: Simplified implementation - use numpy.polyfit in production.
    """
    n = len(x)
    
    # Build Vandermonde matrix
    X = [[xi ** d for d in range(degree + 1)] for xi in x]
    
    # Solve X.T @ X @ coeffs = X.T @ y (normal equations)
    # Simplified: just use polynomial approximation for demo
    
    # For demo, return rough fits
    if degree == 1:
        # Linear fit
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        numer = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        denom = sum((xi - x_mean) ** 2 for xi in x)
        slope = numer / denom if denom != 0 else 0
        intercept = y_mean - slope * x_mean
        return [intercept, slope]
    else:
        # For higher degrees, approximate
        return [0] * (degree + 1)  # Placeholder


def predict(x: float, coeffs: List[float]) -> float:
    """Evaluate polynomial at x"""
    return sum(c * (x ** i) for i, c in enumerate(coeffs))


def mse(y_true: List[float], y_pred: List[float]) -> float:
    """Mean squared error"""
    return sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true)


def demo():
    print("=== Bias-Variance Tradeoff Demo ===")
    print()
    
    # The theory
    print("KEY INSIGHT:")
    print("  Error = Bias² + Variance + Irreducible Noise")
    print()
    print("  Bias: Error from wrong assumptions")
    print("    → High when model is too simple")
    print("    → Leads to UNDERFITTING")
    print()
    print("  Variance: Error from sensitivity to training data")
    print("    → High when model is too complex")
    print("    → Leads to OVERFITTING")
    print()
    
    print("EXAMPLES:")
    print("-" * 50)
    
    models = [
        ("Linear (degree 1)", "High bias, Low variance", "Underfits"),
        ("Polynomial (degree 3)", "Balanced", "Often optimal"),
        ("Polynomial (degree 15)", "Low bias, High variance", "Overfits"),
    ]
    
    for name, bv, behavior in models:
        print(f"  {name}:")
        print(f"    {bv}")
        print(f"    → {behavior}")
        print()
    
    print("HOW TO DIAGNOSE:")
    print("-" * 50)
    print("  Underfitting (High Bias):")
    print("    - Training error is high")
    print("    - Training ≈ Validation error")
    print("    - Fix: More complex model, more features")
    print()
    print("  Overfitting (High Variance):")
    print("    - Training error is low")
    print("    - Validation error >> Training error")
    print("    - Fix: Regularization, more data, simpler model")
    print()
    
    print("REGULARIZATION TECHNIQUES:")
    print("  - L1 (Lasso): Promotes sparsity")
    print("  - L2 (Ridge): Shrinks all coefficients")
    print("  - Dropout: Random neuron deactivation")
    print("  - Early stopping: Stop before overfitting")


if __name__ == "__main__":
    demo()
