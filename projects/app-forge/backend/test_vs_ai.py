"""
Head-to-head comparison: App Forge Intent Matching vs. AI Model (qwen3:8b)
Tests if our AI-free understanding engine matches LLM decisions.
"""

import sys
import json
import time
import urllib.request
from template_registry import match_template_intent, TEMPLATE_REGISTRY

# Test cases - mix of easy and edge cases
TEST_CASES = [
    # Clear cases
    "a wordle clone",
    "a tic tac toe game",
    "a timer app",
    
    # Harder cases (what we designed Intent Graph for)
    "reaction time game with different colored tiles",
    "click the correct color as fast as you can",
    "a quick reflex test",
    
    # Data apps
    "track my daily water intake",
    "a recipe collection app",
    
    # More games
    "a simple number guessing game",
    "memory matching cards game",
]

# Available templates for the AI to choose from
TEMPLATE_LIST = [t.id for t in TEMPLATE_REGISTRY]

def query_ollama(prompt: str, model: str = "phi3:mini") -> str:
    """Query local Ollama model."""
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 50}  # Low temp, limit output
    }).encode()
    
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.loads(r.read())
            return result.get("response", "")
    except Exception as e:
        return f"ERROR: {e}"

def get_ai_choice(description: str) -> str:
    """Ask AI to pick the best template for a description."""
    prompt = f"""You are classifying app descriptions into template categories.

Available templates:
{json.dumps(TEMPLATE_LIST, indent=2)}

User description: "{description}"

Which single template from the list above is the BEST match? 
Reply with ONLY the template name, nothing else. /no_think"""

    response = query_ollama(prompt).strip().lower()
    
    # Extract template name from response
    for template_id in TEMPLATE_LIST:
        if template_id in response:
            return template_id
    
    # If no match, return the raw response for debugging
    return f"[{response[:50]}...]"

def run_comparison():
    """Run head-to-head comparison."""
    print("=" * 70)
    print("APP FORGE vs. AI MODEL (qwen3:8b) - Template Matching Comparison")
    print("=" * 70)
    print(f"\nAvailable templates: {len(TEMPLATE_LIST)}")
    print(TEMPLATE_LIST)
    print("\n")
    
    results = []
    agreements = 0
    
    for i, desc in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] {desc[:50]}")
        
        # App Forge prediction
        t0 = time.time()
        forge_id, features, scores = match_template_intent(desc)
        forge_time = (time.time() - t0) * 1000
        forge_score = scores[0][1] if scores else 0
        
        # AI prediction
        t0 = time.time()
        ai_choice = get_ai_choice(desc)
        ai_time = (time.time() - t0) * 1000
        
        # Compare
        match = "✓" if forge_id == ai_choice else "✗"
        if forge_id == ai_choice:
            agreements += 1
        
        results.append({
            "description": desc,
            "forge": forge_id,
            "forge_score": round(forge_score, 2),
            "forge_ms": round(forge_time, 1),
            "ai": ai_choice,
            "ai_ms": round(ai_time, 1),
            "match": match
        })
        
        print(f"   Forge: {forge_id:20} ({forge_time:.0f}ms)")
        print(f"   AI:    {ai_choice:20} ({ai_time:.0f}ms)")
        print(f"   {match}")
        print()
    
    # Summary
    agreement_pct = (agreements / len(TEST_CASES)) * 100
    forge_avg_ms = sum(r["forge_ms"] for r in results) / len(results)
    ai_avg_ms = sum(r["ai_ms"] for r in results) / len(results)
    
    print("=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"\nAgreement: {agreements}/{len(TEST_CASES)} ({agreement_pct:.0f}%)")
    print(f"\nSpeed comparison:")
    print(f"  App Forge avg: {forge_avg_ms:.1f}ms")
    print(f"  AI model avg:  {ai_avg_ms:.1f}ms")
    print(f"  Speedup:       {ai_avg_ms/forge_avg_ms:.0f}x faster")
    
    print("\n" + "-" * 70)
    print("DETAILED RESULTS")
    print("-" * 70)
    
    print(f"\n{'Description':<45} {'Forge':<15} {'AI':<15} {'Match'}")
    print("-" * 80)
    for r in results:
        desc_short = r["description"][:43]
        print(f"{desc_short:<45} {r['forge']:<15} {r['ai']:<15} {r['match']}")
    
    # Disagreements analysis
    disagreements = [r for r in results if r["match"] == "✗"]
    if disagreements:
        print("\n" + "-" * 70)
        print("DISAGREEMENTS ANALYSIS")
        print("-" * 70)
        for r in disagreements:
            print(f"\n  \"{r['description']}\"")
            print(f"    Forge chose: {r['forge']} (score: {r['forge_score']})")
            print(f"    AI chose:    {r['ai']}")

if __name__ == "__main__":
    run_comparison()
