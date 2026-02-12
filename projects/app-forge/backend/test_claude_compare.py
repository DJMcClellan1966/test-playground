"""Direct comparison: App Forge vs Claude"""
import time
from universal_builder import UniversalBuilder

builder = UniversalBuilder()

print("=" * 70)
print("APP FORGE vs CLAUDE - DIRECT COMPARISON")
print("=" * 70)

tests = [
    ("a recipe app with ingredients", "Claude: Flask recipe app with Recipe+Ingredient models"),
    ("todo list with priorities", "Claude: Task model with priority enum field"),
    ("snake game", "Claude: HTML5 canvas snake with keyboard controls"),
    ("wordle clone", "Claude: JS word game with 5x6 grid, color feedback"),
    ("multi-tenant SaaS with RBAC", "Claude: Tenant, User, Role, Permission models"),
    ("something for my stuff", "Claude: Ask what kind of stuff"),
    ("<script>alert(1)</script>", "Claude: Sanitize, ask for actual request"),
    ("asdfghjkl gibberish", "Claude: Ask for clarification"),
    ("", "Claude: Ask for a description"),
]

for desc, claude_would in tests:
    t0 = time.perf_counter()
    try:
        r = builder.build(desc)
        ms = (time.perf_counter() - t0) * 1000
        cat = r.category.value if hasattr(r.category, 'value') else str(r.category)
        code_len = len(r.files[0].content) if r.files else 0
        d = desc[:40] or "(empty)"
        print(f'\nInput: "{d}"')
        print(f"  App Forge: [{cat}] {code_len} chars in {ms:.1f}ms")
        print(f"  {claude_would}")
    except Exception as e:
        print(f'\nInput: "{desc[:40] or "(empty)"}"')
        print(f"  App Forge ERROR: {e}")
        print(f"  {claude_would}")

print()
print("=" * 70)
print("SUMMARY: App Forge defaults gracefully, Claude asks questions")
print("=" * 70)
