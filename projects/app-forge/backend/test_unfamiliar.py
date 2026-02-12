"""
TEST: How the builder handles unfamiliar/novel domains
Domains that are NOT in its predefined traits or patterns.
"""

import sys
from pathlib import Path
import re
sys.path.insert(0, str(Path(__file__).parent))

from slot_generator import SlotBasedGenerator


def test_unfamiliar_domains():
    print("="*70)
    print("  HOW THE BUILDER HANDLES UNFAMILIAR DOMAINS")
    print("="*70)
    
    # Completely novel/niche domains
    unfamiliar = [
        "a fermentation tracking app for homebrewing kombucha",
        "a beehive inspection logger",
        "a sourdough starter feeding schedule",
        "a bird watching life list",
        "a knitting pattern stitch counter",
        "a plant watering reminder based on soil moisture",
        "a vinyl record collection with discogs integration",
        "a dungeon master campaign notes organizer",
        "an astrophotography session planner",
        "a mechanical keyboard switch tester log",
    ]
    
    generator = SlotBasedGenerator()
    
    print("\n🧠 Strategy: When encountering unfamiliar domains, the builder:")
    print("   1. Uses Semantic Kernel to understand the domain structure")
    print("   2. Falls back to 'generic' category with Flask framework")
    print("   3. Infers data models from the description")
    print("   4. Applies standard CRUD patterns")
    print()
    
    for desc in unfamiliar:
        print(f'\n🔍 "{desc}"')
        result = generator.generate(desc)
        print(f"   → Category: {result.category}")
        print(f"   → Framework: {result.framework}")
        print(f"   → Files: {len(result.files)}")
        
        # Show what it extracted
        main_file = next((f for f in result.files if 'app.py' in f.path), None)
        if main_file:
            # Look for model classes
            models = re.findall(r'class (\w+)\(.*Model\)', main_file.content)
            if models:
                print(f"   → Inferred models: {models}")
            
            # Look for routes
            routes = re.findall(r"@app\.route\('([^']+)'", main_file.content)
            if routes:
                print(f"   → Routes: {routes[:4]}{'...' if len(routes) > 4 else ''}")
    
    print("\n" + "="*70)
    print("  SUMMARY: Graceful Degradation Strategy")
    print("="*70)
    print("""
When the builder encounters an unfamiliar domain:

1. SEMANTIC UNDERSTANDING
   - Uses the Semantic Kernel to parse natural language
   - Extracts nouns as potential data models
   - Identifies verbs as potential actions/routes
   - Detects relationships between entities

2. FALLBACK TO GENERIC
   - Maps to 'generic' category (not a specific trait)
   - Uses Flask as the default web framework
   - Applies standard database patterns

3. MODEL INFERENCE
   - Converts domain concepts to SQLAlchemy models
   - Adds sensible default fields (id, name, created_at)
   - Creates relationships when detected

4. ROUTE GENERATION
   - Creates standard CRUD routes
   - Adds list/detail views
   - Includes search if applicable

5. CONSTRAINT VALIDATION
   - Still applies constraint rules
   - Catches incompatible feature combinations
   - Auto-fixes when possible

The result: A working app that may not be perfectly tailored,
but provides a solid foundation to customize.
""")


if __name__ == "__main__":
    test_unfamiliar_domains()
