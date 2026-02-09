"""
Cross-Validation
Essential technique for robust model evaluation.

Why: Single train/test split can be misleading.
How: Multiple splits, average the results.
"""
import random
from typing import List, Tuple, Callable, Any


def k_fold_split(data: List[Any], k: int = 5) -> List[Tuple[List[Any], List[Any]]]:
    """
    Split data into k folds for cross-validation.
    
    Returns list of (train, test) tuples.
    Each data point appears in exactly one test fold.
    """
    # Shuffle data
    data = data.copy()
    random.shuffle(data)
    
    # Calculate fold sizes
    n = len(data)
    fold_size = n // k
    
    folds = []
    for i in range(k):
        start = i * fold_size
        end = start + fold_size if i < k - 1 else n
        
        test = data[start:end]
        train = data[:start] + data[end:]
        folds.append((train, test))
    
    return folds


def cross_validate(
    data: List[Any],
    train_model: Callable,
    evaluate: Callable,
    k: int = 5
) -> dict:
    """
    Perform k-fold cross-validation.
    
    Parameters:
    - data: Full dataset
    - train_model: Function(train_data) -> model
    - evaluate: Function(model, test_data) -> score
    - k: Number of folds
    
    Returns dict with scores and statistics.
    """
    folds = k_fold_split(data, k)
    scores = []
    
    for i, (train, test) in enumerate(folds):
        model = train_model(train)
        score = evaluate(model, test)
        scores.append(score)
        print(f"  Fold {i + 1}: {score:.4f}")
    
    return {
        'scores': scores,
        'mean': sum(scores) / len(scores),
        'std': (sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)) ** 0.5,
        'min': min(scores),
        'max': max(scores)
    }


def leave_one_out(data: List[Any]) -> List[Tuple[List[Any], List[Any]]]:
    """
    Leave-One-Out Cross-Validation (LOOCV).
    
    Each sample is used once as test set.
    Most thorough but computationally expensive.
    """
    return [(data[:i] + data[i+1:], [data[i]]) for i in range(len(data))]


def stratified_k_fold(data: List[Tuple[Any, Any]], k: int = 5) -> List[Tuple[List, List]]:
    """
    Stratified K-Fold: Preserves class distribution in each fold.
    
    Important for imbalanced datasets!
    data: List of (features, label) tuples
    """
    # Group by label
    by_label = {}
    for item in data:
        label = item[1]
        if label not in by_label:
            by_label[label] = []
        by_label[label].append(item)
    
    # Shuffle each group
    for label in by_label:
        random.shuffle(by_label[label])
    
    # Distribute to folds
    folds = [[] for _ in range(k)]
    for label, items in by_label.items():
        for i, item in enumerate(items):
            folds[i % k].append(item)
    
    # Create train/test splits
    result = []
    for i in range(k):
        test = folds[i]
        train = [item for j, fold in enumerate(folds) if j != i for item in fold]
        result.append((train, test))
    
    return result


def demo():
    print("=== Cross-Validation Demo ===\n")
    
    # Simulate a dataset
    random.seed(42)
    data = [(random.random(), random.randint(0, 1)) for _ in range(100)]
    
    # Dummy model and evaluator for demo
    def dummy_train(train_data):
        # Returns "model" (just the training data mean)
        return sum(x[0] for x in train_data) / len(train_data)
    
    def dummy_evaluate(model, test_data):
        # Returns accuracy (random for demo)
        return 0.7 + random.random() * 0.2
    
    print("5-Fold Cross-Validation:")
    results = cross_validate(data, dummy_train, dummy_evaluate, k=5)
    print(f"\nResults:")
    print(f"  Mean: {results['mean']:.4f} ± {results['std']:.4f}")
    print(f"  Range: [{results['min']:.4f}, {results['max']:.4f}]")
    
    print("\n" + "=" * 50)
    print("\nWHEN TO USE WHAT:")
    print("-" * 50)
    print("  5 or 10-Fold: Default choice, good balance")
    print("  Leave-One-Out: Small datasets, expensive")
    print("  Stratified: Imbalanced classes (ALWAYS use!)")
    print("  Repeated: More stable estimates")


if __name__ == "__main__":
    demo()
