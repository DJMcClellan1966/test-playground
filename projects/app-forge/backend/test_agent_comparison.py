import sys
import os
import subprocess
import json
from imagination import creative_system

# Test cases: app descriptions
test_cases = [
    "a recipe collection app where I can save recipes with ingredients and rate them"
]

# Ollama models to compare
models = ["phi3:mini"]

def run_ollama_model(model, prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode('utf-8'),
            capture_output=True,
            timeout=30
        )
        return result.stdout.decode('utf-8').strip()
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_output(output):
    # Simple analysis: count words, lines, unique features
    lines = output.split('\n')
    words = output.split()
    # Assume features are listed with bullets or numbers
    features = [line.strip() for line in lines if line.strip().startswith(('- ', '* ', '1. ', '• '))]
    return {
        'word_count': len(words),
        'line_count': len(lines),
        'feature_count': len(features),
        'features': features[:5]  # top 5
    }

def run_comparison():
    results = {}
    for desc in test_cases:
        print(f"\n=== Testing: {desc} ===")
        case_results = {}

        # Run imagination system
        try:
            img_result = creative_system.explore_idea(desc)
            img_exp = img_result.get('exploration', {})
            img_features = list(img_exp.get('tensions_found', {}).keys()) + list(img_exp.get('bridges_found', {}).keys())
            case_results['imagination'] = {
                'tensions': len(img_exp.get('tensions_found', {})),
                'bridges': len(img_exp.get('bridges_found', {})),
                'hybrid': img_result.get('hybrid_proposal', {}).get('base_template') if img_result.get('hybrid_proposal') else None,
                'features': img_features
            }
        except Exception as e:
            case_results['imagination'] = {'error': str(e)}

        # Run Ollama models
        for model in models:
            prompt = f"Generate creative features and ideas for an app described as: {desc}. List at least 5 features."
            output = run_ollama_model(model, prompt)
            analysis = analyze_output(output)
            case_results[model] = {
                'output': output[:500],  # truncate
                'analysis': analysis
            }

        results[desc] = case_results

    return results

def print_comparisons(results):
    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)

    for desc, case in results.items():
        print(f"\nApp: {desc}")
        print("-" * 50)

        img = case.get('imagination', {})
        if 'error' in img:
            print(f"Imagination Error: {img['error']}")
        else:
            print(f"Imagination - Tensions: {img.get('tensions', 0)}, Bridges: {img.get('bridges', 0)}, Hybrid: {img.get('hybrid', 'None')}")
            print(f"  Features: {len(img.get('features', []))}")

        for model in models:
            mod = case.get(model, {})
            if 'analysis' in mod:
                an = mod['analysis']
                print(f"{model} - Words: {an['word_count']}, Lines: {an['line_count']}, Features: {an['feature_count']}")
            else:
                print(f"{model} - Error")

    print("\n" + "="*80)
    print("AREAS FOR IMPROVEMENT")
    print("="*80)

    # Calculate averages
    img_avg_features = sum(len(case.get('imagination', {}).get('features', [])) for case in results.values()) / len(results)
    model_avgs = {}
    for model in models:
        avg_features = sum(case.get(model, {}).get('analysis', {}).get('feature_count', 0) for case in results.values()) / len(results)
        model_avgs[model] = avg_features

    print(f"Imagination average features: {img_avg_features:.1f}")
    for model, avg in model_avgs.items():
        print(f"{model} average features: {avg:.1f}")

    print("\nObservations:")
    print("- Imagination provides structured tensions/bridges but fewer raw features")
    print("- LLMs generate more verbose outputs with more listed features")
    print("- Imagination is symbolic/rule-based, LLMs are generative")
    print("- Improvement areas: Add more feature generation rules, integrate LLM creativity selectively")

if __name__ == "__main__":
    results = run_comparison()
    print_comparisons(results)