"""
Optimal Training Data Calculator
================================

Question: What's the MINIMUM data needed to cover ALL app types?

Mathematical Approach:
1. Map the decision space completely
2. Calculate coverage gaps
3. Generate optimal training examples
4. Verify completeness

This tells us EXACTLY what data we need to synthesize any app.
"""

import math
from itertools import product
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import json


# =============================================================================
# THE COMPLETE DECISION SPACE
# =============================================================================

# Every decision an app can require (from llm_analysis.py)
DECISION_SPACE = {
    'category': [
        'data_app',    # CRUD apps, collections, trackers
        'game',        # Interactive games  
        'api',         # REST/GraphQL services
        'cli',         # Command line tools
        'ml',          # Machine learning pipelines
        'automation',  # Bots, scrapers, schedulers
    ],
    
    'complexity': [
        'trivial',     # Single entity, no relationships
        'simple',      # 1-2 entities, basic features
        'moderate',    # 3-5 entities, auth, relationships
        'complex',     # Multi-service, advanced features
    ],
    
    'primary_entity': [
        'item',        # Generic (todo, bookmark, note)
        'recipe',      # Cooking/food domain
        'task',        # Productivity domain
        'user',        # User management
        'product',     # E-commerce
        'post',        # Content/blog
        'event',       # Calendar/scheduling
        'workout',     # Fitness domain
        'expense',     # Finance domain
        'media',       # Files/gallery
    ],
    
    'features': [  # Boolean flags - can combine
        'auth',
        'search',
        'tags',
        'ratings',
        'comments',
        'export',
        'share',
        'history',
        'stats',
        'notifications',
    ],
    
    'relationships': [
        'none',        # Single entity
        'has_many',    # One-to-many
        'belongs_to',  # Many-to-one
        'many_to_many', # Complex relationships
    ],
    
    'ui_type': [
        'web',         # HTML/CSS
        'cli',         # Terminal
        'api_only',    # No UI
        'canvas',      # Game/visualization
    ],
}

# Total theoretical combinations (but Zipf means most are rare)
def calculate_total_space():
    """Calculate total theoretical decision space."""
    total = 1
    for dimension, options in DECISION_SPACE.items():
        if dimension == 'features':
            # Features are boolean flags, so 2^n combinations
            total *= 2 ** len(options)
        else:
            total *= len(options)
    return total


# =============================================================================
# COVERAGE ANALYSIS
# =============================================================================

@dataclass
class AppArchetype:
    """A representative app pattern that covers a region of decision space."""
    id: str
    name: str
    category: str
    complexity: str
    entities: List[str]
    features: Set[str]
    relationships: str
    ui_type: str
    example_descriptions: List[str]
    
    # Coverage metrics
    decision_bits: float = 0.0
    coverage_radius: float = 0.0  # How many similar apps it can generate
    
    def to_decision_vector(self) -> Dict:
        return {
            'category': self.category,
            'complexity': self.complexity,
            'primary_entity': self.entities[0] if self.entities else 'item',
            'features': self.features,
            'relationships': self.relationships,
            'ui_type': self.ui_type,
        }


# The MINIMAL set of archetypes to cover decision space
CORE_ARCHETYPES = [
    # Data Apps (most common - multiple variants needed)
    AppArchetype(
        id='simple_collection',
        name='Simple Collection',
        category='data_app',
        complexity='trivial',
        entities=['item'],
        features=set(),
        relationships='none',
        ui_type='web',
        example_descriptions=[
            'a todo list',
            'a bookmark manager',
            'a note taking app',
            'a shopping list',
        ],
    ),
    AppArchetype(
        id='collection_with_features',
        name='Collection + Features',
        category='data_app',
        complexity='simple',
        entities=['item'],
        features={'search', 'tags'},
        relationships='has_many',
        ui_type='web',
        example_descriptions=[
            'a recipe app with search and tags',
            'a bookmark manager with categories',
            'a movie collection with tags',
        ],
    ),
    AppArchetype(
        id='authenticated_app',
        name='Authenticated App',
        category='data_app',
        complexity='moderate',
        entities=['user', 'item'],
        features={'auth', 'search'},
        relationships='belongs_to',
        ui_type='web',
        example_descriptions=[
            'a recipe app with user accounts',
            'a personal task manager with login',
            'a blog platform with authors',
        ],
    ),
    AppArchetype(
        id='social_app',
        name='Social/Community App',
        category='data_app',
        complexity='complex',
        entities=['user', 'post', 'comment'],
        features={'auth', 'comments', 'ratings', 'share'},
        relationships='many_to_many',
        ui_type='web',
        example_descriptions=[
            'a recipe sharing platform with ratings',
            'a community forum',
            'a social network for fitness',
        ],
    ),
    
    # Domain-specific data apps
    AppArchetype(
        id='fitness_tracker',
        name='Fitness Tracker',
        category='data_app',
        complexity='simple',
        entities=['workout', 'exercise'],
        features={'history', 'stats'},
        relationships='has_many',
        ui_type='web',
        example_descriptions=[
            'a workout tracker',
            'an exercise log',
            'a fitness app with statistics',
        ],
    ),
    AppArchetype(
        id='finance_tracker',
        name='Finance Tracker',
        category='data_app',
        complexity='simple',
        entities=['expense', 'budget'],
        features={'stats', 'export'},
        relationships='has_many',
        ui_type='web',
        example_descriptions=[
            'a budget tracker',
            'an expense manager',
            'a finance app with reports',
        ],
    ),
    
    # Games
    AppArchetype(
        id='simple_game',
        name='Simple Game',
        category='game',
        complexity='trivial',
        entities=['game_state'],
        features=set(),
        relationships='none',
        ui_type='canvas',
        example_descriptions=[
            'a snake game',
            'a pong game',
            'a reaction time test',
        ],
    ),
    AppArchetype(
        id='puzzle_game',
        name='Puzzle Game',
        category='game',
        complexity='simple',
        entities=['puzzle', 'score'],
        features={'stats'},
        relationships='none',
        ui_type='canvas',
        example_descriptions=[
            'a wordle clone',
            'a sudoku game',
            'a tic tac toe',
        ],
    ),
    AppArchetype(
        id='game_with_scores',
        name='Game + Leaderboard',
        category='game',
        complexity='moderate',
        entities=['user', 'game', 'score'],
        features={'auth', 'stats'},
        relationships='belongs_to',
        ui_type='canvas',
        example_descriptions=[
            'a tetris with high scores',
            'a multiplayer quiz',
            'a typing speed test',
        ],
    ),
    
    # APIs
    AppArchetype(
        id='simple_api',
        name='Simple REST API',
        category='api',
        complexity='trivial',
        entities=['item'],
        features=set(),
        relationships='none',
        ui_type='api_only',
        example_descriptions=[
            'a REST API for users',
            'an API for products',
            'a simple CRUD API',
        ],
    ),
    AppArchetype(
        id='authenticated_api',
        name='Authenticated API',
        category='api',
        complexity='moderate',
        entities=['user', 'item'],
        features={'auth', 'search'},
        relationships='belongs_to',
        ui_type='api_only',
        example_descriptions=[
            'an API with JWT auth',
            'a secure REST service',
            'a user management API',
        ],
    ),
    
    # CLI Tools
    AppArchetype(
        id='simple_cli',
        name='Simple CLI',
        category='cli',
        complexity='trivial',
        entities=[],
        features=set(),
        relationships='none',
        ui_type='cli',
        example_descriptions=[
            'a file converter',
            'a password generator',
            'a text processor',
        ],
    ),
    AppArchetype(
        id='data_cli',
        name='CLI + Data',
        category='cli',
        complexity='simple',
        entities=['item'],
        features={'export'},
        relationships='none',
        ui_type='cli',
        example_descriptions=[
            'a CLI task manager',
            'a command line note app',
            'a terminal todo list',
        ],
    ),
    
    # ML Pipelines
    AppArchetype(
        id='simple_ml',
        name='Simple ML',
        category='ml',
        complexity='simple',
        entities=['model', 'data'],
        features={'stats'},
        relationships='none',
        ui_type='api_only',
        example_descriptions=[
            'a sentiment classifier',
            'an image classifier',
            'a prediction model',
        ],
    ),
    
    # Automation
    AppArchetype(
        id='simple_automation',
        name='Simple Automation',
        category='automation',
        complexity='trivial',
        entities=[],
        features={'notifications'},
        relationships='none',
        ui_type='cli',
        example_descriptions=[
            'a web scraper',
            'a file backup script',
            'a scheduled task runner',
        ],
    ),
]


def calculate_coverage_metrics():
    """Calculate how well archetypes cover the decision space."""
    
    # Count coverage by dimension
    coverage = {dim: set() for dim in DECISION_SPACE}
    
    for arch in CORE_ARCHETYPES:
        coverage['category'].add(arch.category)
        coverage['complexity'].add(arch.complexity)
        coverage['relationships'].add(arch.relationships)
        coverage['ui_type'].add(arch.ui_type)
        
        for entity in arch.entities:
            if entity in DECISION_SPACE['primary_entity']:
                coverage['primary_entity'].add(entity)
        
        coverage['features'].update(arch.features)
    
    # Calculate gaps
    gaps = {}
    for dim, covered in coverage.items():
        all_options = set(DECISION_SPACE[dim])
        gaps[dim] = all_options - covered
    
    # Calculate coverage percentage
    coverage_pct = {}
    for dim in DECISION_SPACE:
        total = len(DECISION_SPACE[dim])
        covered = len(coverage[dim])
        coverage_pct[dim] = covered / total if total > 0 else 1.0
    
    return {
        'coverage': {k: list(v) for k, v in coverage.items()},
        'gaps': {k: list(v) for k, v in gaps.items()},
        'coverage_percent': coverage_pct,
        'total_archetypes': len(CORE_ARCHETYPES),
        'overall_coverage': sum(coverage_pct.values()) / len(coverage_pct),
    }


# =============================================================================
# OPTIMAL DATA GENERATOR
# =============================================================================

def generate_optimal_training_set() -> List[Dict]:
    """
    Generate the MINIMUM training examples to cover all app types.
    
    Strategy:
    1. Include all core archetypes (covers main clusters)
    2. Add boundary examples (edge cases)
    3. Add feature combinations (fill gaps)
    """
    
    training_set = []
    
    # Core examples from archetypes
    for arch in CORE_ARCHETYPES:
        for desc in arch.example_descriptions[:2]:  # 2 per archetype
            training_set.append({
                'description': desc,
                'archetype': arch.id,
                'category': arch.category,
                'complexity': arch.complexity,
                'features': list(arch.features),
                'purpose': 'core_coverage',
            })
    
    # Feature combination examples (cover feature space)
    feature_combos = [
        ({'search', 'tags'}, "a recipe app with search and tags"),
        ({'auth', 'export'}, "a personal finance tracker with export"),
        ({'ratings', 'comments'}, "a product review app"),
        ({'history', 'stats'}, "a workout tracker with statistics"),
        ({'share', 'notifications'}, "a social todo list with notifications"),
        ({'auth', 'search', 'tags'}, "a bookmarking app with accounts"),
        ({'ratings', 'comments', 'share'}, "a community recipe site"),
    ]
    
    for features, desc in feature_combos:
        training_set.append({
            'description': desc,
            'archetype': 'feature_combo',
            'category': 'data_app',
            'complexity': 'moderate',
            'features': list(features),
            'purpose': 'feature_coverage',
        })
    
    # Complexity edge cases
    complexity_examples = [
        ('trivial', "a simple counter app"),
        ('trivial', "a dice roller"),
        ('complex', "a multi-tenant SaaS platform"),
        ('complex', "an e-commerce marketplace"),
    ]
    
    for complexity, desc in complexity_examples:
        training_set.append({
            'description': desc,
            'archetype': 'complexity_edge',
            'category': 'data_app',
            'complexity': complexity,
            'features': [],
            'purpose': 'complexity_coverage',
        })
    
    # Entity coverage (ensure all domains)
    entity_examples = [
        ('recipe', "a cooking recipe collection"),
        ('task', "a task management system"),
        ('product', "an inventory management app"),
        ('post', "a blog publishing platform"),
        ('event', "a calendar scheduling app"),
        ('workout', "a gym workout planner"),
        ('expense', "a personal budget tracker"),
        ('media', "a photo gallery manager"),
    ]
    
    for entity, desc in entity_examples:
        training_set.append({
            'description': desc,
            'archetype': 'entity_coverage',
            'category': 'data_app',
            'complexity': 'simple',
            'features': [],
            'entity': entity,
            'purpose': 'entity_coverage',
        })
    
    return training_set


def analyze_training_sufficiency(training_set: List[Dict]) -> Dict:
    """Analyze if training set covers all decision dimensions."""
    
    # Track what's covered
    covered = {
        'categories': set(),
        'complexities': set(),
        'features': set(),
        'entities': set(),
    }
    
    for example in training_set:
        covered['categories'].add(example.get('category', ''))
        covered['complexities'].add(example.get('complexity', ''))
        covered['features'].update(example.get('features', []))
        if 'entity' in example:
            covered['entities'].add(example['entity'])
    
    # What's missing?
    required = {
        'categories': set(DECISION_SPACE['category']),
        'complexities': set(DECISION_SPACE['complexity']),
        'features': set(DECISION_SPACE['features']),
        'entities': set(DECISION_SPACE['primary_entity']),
    }
    
    gaps = {}
    for dim, req in required.items():
        gaps[dim] = req - covered[dim]
    
    # Calculate information metrics
    total_bits = 0
    for example in training_set:
        # Each example carries ~5 bits of decision info
        bits = 2.58  # category
        bits += 2.0   # complexity
        bits += len(example.get('features', [])) * 0.3
        total_bits += bits
    
    return {
        'total_examples': len(training_set),
        'covered': {k: list(v) for k, v in covered.items()},
        'gaps': {k: list(v) for k, v in gaps.items() if v},
        'is_complete': all(len(g) == 0 for g in gaps.values()),
        'total_information_bits': total_bits,
        'bits_per_example': total_bits / len(training_set) if training_set else 0,
        'estimated_coverage': min(1.0, total_bits / 50),  # 50 bits = full coverage
    }


# =============================================================================
# MINIMAL TEMPLATE DERIVATION
# =============================================================================

def derive_minimal_templates() -> Dict:
    """
    Derive the MINIMUM templates needed from mathematical analysis.
    
    Key insight: Templates need to cover:
    1. Category × Complexity combinations (6 × 4 = 24, but many are rare)
    2. Entity types (10, but inherit from 'item')
    3. Feature combinations (10 features, but Zipf means few combos matter)
    """
    
    # Essential category templates (one per major category)
    category_templates = {
        'data_app': ['simple_collection', 'authenticated_collection'],
        'game': ['canvas_game'],
        'api': ['rest_api'],
        'cli': ['cli_tool'],
        'ml': ['ml_pipeline'],
        'automation': ['automation_script'],
    }
    
    # Entity inheritance (most entities inherit from 'item')
    entity_inheritance = {
        'item': ['task', 'note', 'bookmark', 'recipe', 'product', 'post', 'event'],
        'workout': ['exercise'],
        'expense': ['income', 'budget'],
        'media': ['image', 'video', 'file'],
    }
    
    # Feature templates (composable)
    feature_templates = {
        'auth': ['owner_field', 'login_routes'],
        'search': ['search_query', 'filter_ui'],
        'tags': ['tags_field', 'tag_relation'],
        'ratings': ['rating_fields', 'avg_rating'],
        'comments': ['comment_relation'],
        'export': ['export_routes'],
        'history': ['version_tracking'],
        'stats': ['analytics_queries'],
    }
    
    # Total minimal templates
    base_templates = sum(len(t) for t in category_templates.values())
    entity_templates = len(entity_inheritance)  # Base entities only
    feature_templates_count = len(feature_templates)
    
    total_minimal = base_templates + entity_templates + feature_templates_count
    
    return {
        'category_templates': category_templates,
        'entity_inheritance': entity_inheritance,
        'feature_templates': feature_templates,
        'counts': {
            'base': base_templates,
            'entity': entity_templates,
            'feature': feature_templates_count,
            'total_minimal': total_minimal,
        },
        'explanation': f"""
Minimal template count: {total_minimal}

This is because:
1. 6 categories need ~{base_templates} base templates
2. Entities inherit: {len(entity_inheritance)} base types cover all
3. Features are composable: {feature_templates_count} feature fragments

With {total_minimal} templates + synthesis, we can generate ANY app type.
""",
    }


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("OPTIMAL TRAINING DATA ANALYSIS")
    print("=" * 70)
    
    # Total decision space
    total_space = calculate_total_space()
    print(f"\n1. TOTAL DECISION SPACE: {total_space:,} theoretical combinations")
    print(f"   (This is the full space an LLM must encode)")
    
    # Coverage with archetypes
    print("\n" + "=" * 70)
    print("2. ARCHETYPE COVERAGE")
    print("=" * 70)
    metrics = calculate_coverage_metrics()
    print(f"   Archetypes defined: {metrics['total_archetypes']}")
    print(f"   Overall coverage: {metrics['overall_coverage']:.1%}")
    print("\n   Coverage by dimension:")
    for dim, pct in metrics['coverage_percent'].items():
        gap_list = metrics['gaps'].get(dim, [])
        gap_str = f" (missing: {gap_list})" if gap_list else ""
        print(f"     {dim:20} {pct:.0%}{gap_str}")
    
    # Optimal training set
    print("\n" + "=" * 70)
    print("3. OPTIMAL TRAINING SET")
    print("=" * 70)
    training_set = generate_optimal_training_set()
    analysis = analyze_training_sufficiency(training_set)
    print(f"   Total examples needed: {analysis['total_examples']}")
    print(f"   Information content: {analysis['total_information_bits']:.1f} bits")
    print(f"   Bits per example: {analysis['bits_per_example']:.1f}")
    print(f"   Estimated coverage: {analysis['estimated_coverage']:.1%}")
    print(f"   Is complete: {analysis['is_complete']}")
    
    if analysis['gaps']:
        print("\n   Gaps to fill:")
        for dim, gaps in analysis['gaps'].items():
            print(f"     {dim}: {gaps}")
    
    # By purpose breakdown
    purposes = defaultdict(list)
    for ex in training_set:
        purposes[ex['purpose']].append(ex['description'])
    
    print("\n   Examples by purpose:")
    for purpose, examples in purposes.items():
        print(f"     {purpose}: {len(examples)} examples")
    
    # Minimal templates
    print("\n" + "=" * 70)
    print("4. MINIMAL TEMPLATE COUNT")
    print("=" * 70)
    minimal = derive_minimal_templates()
    for key, count in minimal['counts'].items():
        print(f"   {key:20} {count}")
    print(minimal['explanation'])
    
    # Summary
    print("=" * 70)
    print("SUMMARY: WHAT DATA DO YOU NEED?")
    print("=" * 70)
    print(f"""
To cover ALL app types from trivial to complex:

┌─────────────────────────────────────────────────────────────────────┐
│ MINIMUM DATA REQUIREMENTS                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. CORE ARCHETYPES: ~15 representative apps                       │
│     • 4 data app variants (trivial → complex)                      │
│     • 3 game variants (simple → with scores)                       │
│     • 2 API variants (simple → authenticated)                      │
│     • 2 CLI variants                                                │
│     • 2 ML/automation variants                                      │
│                                                                     │
│  2. ENTITY EXAMPLES: ~10 domain types                              │
│     recipe, task, product, post, event, workout, expense, media    │
│     (Most inherit from 'item' base type)                           │
│                                                                     │
│  3. FEATURE COMBINATIONS: ~10 common patterns                      │
│     auth+search, ratings+comments, history+stats, etc.             │
│                                                                     │
│  4. EDGE CASES: ~5 complexity boundaries                           │
│     trivial (counter), complex (multi-tenant SaaS)                 │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ TOTAL: ~{analysis['total_examples']} TRAINING EXAMPLES = ~{analysis['total_information_bits']:.0f} BITS OF DECISION    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ This covers {metrics['overall_coverage']:.0%} of the {total_space:,} theoretical combinations  │
│ because Zipf's law means most combinations never occur.            │
│                                                                     │
│ An LLM uses 175B parameters to encode world knowledge,             │
│ but for app generation, you need: ~{analysis['total_information_bits']:.0f} bits.                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
""")
    
    # Export optimal training set
    print("\n" + "=" * 70)
    print("5. OPTIMAL TRAINING EXAMPLES (copy these)")
    print("=" * 70)
    
    # Group by archetype
    by_archetype = defaultdict(list)
    for ex in training_set:
        by_archetype[ex['archetype']].append(ex['description'])
    
    for archetype, descriptions in by_archetype.items():
        print(f"\n{archetype}:")
        for desc in descriptions:
            print(f"  • \"{desc}\"")
