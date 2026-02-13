import time
from template_registry import extract_features, match_template

def test_feature_extraction():
    desc = "a recipe collection app where I can save recipes with ingredients and rate them"
    t0 = time.time()
    for _ in range(100):
        extract_features(desc)
    t1 = time.time()
    print(f"Feature extraction (memoized) 100x: {t1-t0:.4f}s")

def test_template_matching():
    desc = "a workout tracker with progress graphs"
    t0 = time.time()
    for _ in range(20):
        match_template(desc)
    t1 = time.time()
    print(f"Template matching (parallel) 20x: {t1-t0:.4f}s")

if __name__ == "__main__":
    print("--- Optimization Benchmarks ---")
    test_feature_extraction()
    test_template_matching()