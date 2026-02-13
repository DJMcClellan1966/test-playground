"""Test brittleness and vocabulary issues."""
from unified_agent import unified_infer

print('=' * 60)
print('BRITTLENESS TEST: Typos, Variants, Novel Phrasings')
print('=' * 60)

tests = [
    # Typos
    ('recipie tracker', 'typo: recipie'),
    ('expence budjet app', 'typos: expence, budjet'),
    ('todoo list', 'typo: todoo'),
    
    # Novel phrasings (implicit meaning)
    ('grandmas secret pasta dishes', 'implicit recipe'),
    ('my collection of favorite meals', 'implicit recipe'),
    ('track my daily spending habits', 'implicit expense'),
    
    # Novel domains (not in vocabulary)
    ('cryptocurrency portfolio', 'novel: crypto'),
    ('quantum simulation tool', 'novel: quantum'),
    ('dna sequence analyzer', 'novel: biotech'),
]

print()
for desc, test_type in tests:
    result = unified_infer(desc)
    clusters = list(result.clusters.keys()) if result.clusters else ['none']
    print(f'{test_type}')
    print(f'  Input: "{desc}"')
    print(f'  Clusters: {clusters}')
    print(f'  Template: {result.template_id} ({result.confidence:.0%})')
    print(f'  Synthesized: {result.was_synthesized}, Evolved: {result.was_evolved}')
    print()

print('=' * 60)
print('VOCABULARY TEST: Do we handle these?')
print('=' * 60)

vocab_tests = [
    'recipe',           # Direct match
    'recipes',          # Plural
    'recipie',          # Typo
    'cooking',          # Synonym
    'culinary',         # Related
    'pasta dishes',     # Compound
]

from cluster_perception import SemanticClusterEngine  # type: ignore
engine = SemanticClusterEngine()

print()
for word in vocab_tests:
    percept = engine.perceive(word)
    clusters = {k: f'{v:.0%}' for k, v in percept.entities.items()}
    print(f'  "{word}" -> {clusters or "no match"}')
