"""Demo: Semantic Kernel in Action.

Shows how the kernel handles descriptions with NO pre-defined traits.
This demonstrates true semantic understanding without LLMs.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from semantic_kernel import understand, explain_inference


def demo_semantic_kernel():
    """Demonstrate semantic kernel with real-world examples."""
    
    print("\n" + "=" * 80)
    print(" " * 25 + "SEMANTIC KERNEL DEMO")
    print(" " * 20 + "(LLM Quality, Zero Neural Networks)")
    print("=" * 80)
    
    examples = [
        "inventory tracker for small business with products and suppliers",
        "expense tracker with categories and monthly budgets",
        "pet grooming appointment scheduler with customer records",
        "plant watering reminder with species information",
        "book club reading list with member ratings",
    ]
    
    for i, description in enumerate(examples, 1):
        print(f"\n{'─' * 80}")
        print(f"EXAMPLE {i}: {description}")
        print('─' * 80)
        
        # Get semantic understanding
        understanding = understand(description, verbose=False)
        
        # Show results
        print(f"\n🎯 FRAMEWORK: {understanding.framework}")
        print(f"💯 CONFIDENCE: {understanding.confidence:.2f}")
        
        if understanding.models:
            print(f"\n📦 INFERRED MODELS ({len(understanding.models)}):")
            for model in understanding.models:
                print(f"\n  {model.name}:")
                for field in model.fields[:5]:
                    req = "required" if field.required else "optional"
                    field_type = getattr(field, 'field_type', getattr(field, 'type', 'unknown'))
                    print(f"    • {field.name}: {field_type} ({req})")
                if len(model.fields) > 5:
                    print(f"    ... and {len(model.fields) - 5} more fields")
        
        if understanding.features:
            print(f"\n🔧 REQUIRED FEATURES:")
            for feature in sorted(understanding.features):
                print(f"  ✓ {feature}")
        
        print(f"\n📝 REASONING:")
        for line in understanding.reasoning.split('\n'):
            print(f"  {line}")
    
    print("\n" + "=" * 80)
    print("\nKey Points:")
    print("  • No LLM calls - 100% local processing")
    print("  • Entity extraction via regex + heuristics")
    print("  • Domain knowledge from curated dictionaries")
    print("  • Type inference from field name patterns")
    print("  • Framework selection via simple rules")
    print("\nResult: LLM-quality understanding at zero cost\n")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    demo_semantic_kernel()
