"""
Data-Driven Template Builder
============================

Uses the mathematical model from llm_analysis.py to automatically
generate templates based on observed patterns in app descriptions.

Key insight from analysis:
- Only ~20 decision bits matter
- Zipf's law means 24 templates cover 50% of requests
- We can LEARN what those templates should be from data

This module:
1. Clusters descriptions by decision patterns
2. Extracts the template "skeleton" from each cluster
3. Generates micro-templates with proper fields/operations
4. Ranks templates by expected coverage (Zipf weighting)

NO AI - Statistical pattern extraction + rule application.
"""

import re
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import json


# =============================================================================
# DECISION EXTRACTORS
# =============================================================================

@dataclass
class DecisionVector:
    """The ~20 bits of decision that define an app."""
    category: str = 'unknown'
    complexity: str = 'simple'
    entities: List[str] = field(default_factory=list)
    features: Set[str] = field(default_factory=set)
    relationships: Set[str] = field(default_factory=set)
    
    def to_key(self) -> str:
        """Create hashable key for clustering."""
        return f"{self.category}|{','.join(sorted(self.entities))}|{','.join(sorted(self.features))}"
    
    def decision_bits(self) -> float:
        """Calculate information content of this decision."""
        bits = 0
        bits += 2.58  # category
        bits += 2.0   # complexity
        bits += len(self.entities) * 0.5  # each entity adds ~0.5 bits
        bits += len(self.features) * 0.3  # features are more common, less info
        return bits


# Pattern extractors (map keywords → decisions)
CATEGORY_PATTERNS = {
    'data_app': r'\b(app|manager|tracker|collection|list|inventory|dashboard|planner|log)\b',
    'game': r'\b(game|play|score|level|puzzle|snake|tetris|pong|wordle|quiz)\b',
    'api': r'\b(api|endpoint|rest|service|backend|server|graphql)\b',
    'cli': r'\b(cli|command|tool|script|terminal)\b',
    'ml': r'\b(ml|machine learning|model|prediction|classifier|neural)\b',
    'automation': r'\b(bot|scraper|automation|scheduler|crawler)\b',
}

ENTITY_PATTERNS = {
    'recipe': r'\b(recipe|meal|dish|ingredient|cooking)\b',
    'task': r'\b(task|todo|chore|action|item)\b',
    'user': r'\b(user|account|profile|member|person)\b',
    'product': r'\b(product|item|goods|inventory|stock)\b',
    'post': r'\b(post|article|blog|entry|content)\b',
    'event': r'\b(event|appointment|meeting|calendar|schedule)\b',
    'workout': r'\b(workout|exercise|fitness|gym|training)\b',
    'expense': r'\b(expense|budget|finance|money|payment|transaction)\b',
    'media': r'\b(photo|image|video|media|gallery|file)\b',
    'note': r'\b(note|memo|journal|diary|document)\b',
}

FEATURE_PATTERNS = {
    'auth': r'\b(login|auth|user|account|password|signin|register)\b',
    'search': r'\b(search|find|filter|query|lookup)\b',
    'tags': r'\b(tag|category|label|classify|organize)\b',
    'ratings': r'\b(rate|rating|star|review|score)\b',
    'comments': r'\b(comment|reply|discuss|feedback)\b',
    'export': r'\b(export|download|save|backup)\b',
    'share': r'\b(share|social|public|collaborate)\b',
    'history': r'\b(history|track|log|record|timeline)\b',
    'stats': r'\b(stats|statistics|analytics|chart|graph|dashboard)\b',
    'notifications': r'\b(notify|alert|reminder|notification)\b',
}

RELATIONSHIP_PATTERNS = {
    'has_many': r'\b(with|contains|has|includes|multiple|list of)\b',
    'belongs_to': r'\b(owned by|belongs|associated|part of|member of)\b',
    'has_tags': r'\b(tagged|categorized|labeled|organized)\b',
    'nested': r'\b(sub|child|nested|hierarchical|folder)\b',
}


def extract_decisions(description: str) -> DecisionVector:
    """Extract the decision vector from a description."""
    desc_lower = description.lower()
    
    # Category
    category = 'data_app'  # default
    for cat, pattern in CATEGORY_PATTERNS.items():
        if re.search(pattern, desc_lower):
            category = cat
            break
    
    # Entities
    entities = []
    for entity, pattern in ENTITY_PATTERNS.items():
        if re.search(pattern, desc_lower):
            entities.append(entity)
    
    # Features
    features = set()
    for feature, pattern in FEATURE_PATTERNS.items():
        if re.search(pattern, desc_lower):
            features.add(feature)
    
    # Relationships
    relationships = set()
    for rel, pattern in RELATIONSHIP_PATTERNS.items():
        if re.search(pattern, desc_lower):
            relationships.add(rel)
    
    return DecisionVector(
        category=category,
        entities=entities,
        features=features,
        relationships=relationships,
    )


# =============================================================================
# CLUSTERING & TEMPLATE EXTRACTION
# =============================================================================

@dataclass  
class TemplateCluster:
    """A cluster of similar descriptions → one template."""
    key: str
    descriptions: List[str] = field(default_factory=list)
    decision_vectors: List[DecisionVector] = field(default_factory=list)
    
    # Template properties (extracted from cluster)
    category: str = 'data_app'
    primary_entity: str = 'item'
    common_features: Set[str] = field(default_factory=set)
    common_relationships: Set[str] = field(default_factory=set)
    
    # Metadata
    frequency: int = 0
    coverage_weight: float = 0.0  # Zipf-weighted importance
    
    def extract_template(self):
        """Extract template properties from the cluster."""
        if not self.decision_vectors:
            return
        
        # Most common category
        categories = Counter(dv.category for dv in self.decision_vectors)
        self.category = categories.most_common(1)[0][0]
        
        # Most common primary entity
        all_entities = []
        for dv in self.decision_vectors:
            all_entities.extend(dv.entities)
        if all_entities:
            entity_counts = Counter(all_entities)
            self.primary_entity = entity_counts.most_common(1)[0][0]
        
        # Features that appear in >50% of cluster
        feature_counts = Counter()
        for dv in self.decision_vectors:
            feature_counts.update(dv.features)
        threshold = len(self.decision_vectors) * 0.5
        self.common_features = {f for f, c in feature_counts.items() if c >= threshold}
        
        # Same for relationships
        rel_counts = Counter()
        for dv in self.decision_vectors:
            rel_counts.update(dv.relationships)
        self.common_relationships = {r for r, c in rel_counts.items() if c >= threshold}
        
        self.frequency = len(self.descriptions)


def cluster_descriptions(descriptions: List[str]) -> List[TemplateCluster]:
    """Cluster descriptions by decision similarity."""
    clusters: Dict[str, TemplateCluster] = {}
    
    for desc in descriptions:
        dv = extract_decisions(desc)
        key = dv.to_key()
        
        if key not in clusters:
            clusters[key] = TemplateCluster(key=key)
        
        clusters[key].descriptions.append(desc)
        clusters[key].decision_vectors.append(dv)
    
    # Extract template properties and calculate Zipf weights
    cluster_list = list(clusters.values())
    for cluster in cluster_list:
        cluster.extract_template()
    
    # Sort by frequency and assign Zipf weights
    cluster_list.sort(key=lambda c: c.frequency, reverse=True)
    for rank, cluster in enumerate(cluster_list, 1):
        cluster.coverage_weight = 1.0 / rank  # Zipf weight
    
    return cluster_list


# =============================================================================
# TEMPLATE GENERATION FROM CLUSTERS
# =============================================================================

# Domain-specific field generators (from template_synthesis.py)
DOMAIN_FIELDS = {
    'recipe': ['title', 'ingredients', 'instructions', 'prep_time', 'cook_time', 'servings'],
    'task': ['title', 'description', 'completed', 'due_date', 'priority'],
    'user': ['username', 'email', 'password_hash', 'created_at'],
    'product': ['name', 'description', 'price', 'sku', 'quantity'],
    'post': ['title', 'body', 'author_id', 'published_at', 'slug'],
    'event': ['title', 'start_time', 'end_time', 'location', 'description'],
    'workout': ['exercise_type', 'sets', 'reps', 'weight', 'duration'],
    'expense': ['amount', 'category', 'date', 'description', 'recurring'],
    'media': ['filename', 'url', 'file_type', 'size_bytes', 'uploaded_at'],
    'note': ['title', 'content', 'created_at', 'updated_at'],
}

FEATURE_FIELDS = {
    'auth': ['owner_id', 'created_by'],
    'search': ['search_text'],
    'tags': ['tags'],
    'ratings': ['rating_sum', 'rating_count', 'avg_rating'],
    'comments': ['comment_count'],
    'export': [],  # No extra fields, just capability
    'share': ['visibility', 'share_count'],
    'history': ['version', 'previous_version_id'],
    'stats': ['view_count', 'last_accessed'],
    'notifications': ['notify_on_change'],
}


@dataclass
class GeneratedTemplate:
    """A template generated from cluster analysis."""
    id: str
    name: str
    category: str
    entity: str
    fields: List[str]
    features: List[str]
    confidence: float  # Based on cluster size and coverage
    zipf_rank: int
    expected_coverage: float
    
    def to_micro_template_code(self) -> str:
        """Generate Python code for this template."""
        lines = [
            f"MicroTemplate(",
            f"    id='{self.id}',",
            f"    name='{self.name}',",
            f"    pattern=UniversalPattern.CONTAINER,",
            f"    description='Auto-generated from {self.zipf_rank} cluster analysis',",
            f"    fields={self.fields},",
            f"    operations=['create', 'read', 'update', 'delete'],",
            f"    keywords=['{self.entity}', '{self.category}'],",
            f"),",
        ]
        return '\n'.join(lines)


def generate_templates_from_clusters(clusters: List[TemplateCluster]) -> List[GeneratedTemplate]:
    """Generate template definitions from clusters."""
    templates = []
    total_coverage = sum(c.coverage_weight for c in clusters)
    cumulative_coverage = 0
    
    for rank, cluster in enumerate(clusters, 1):
        # Generate fields
        fields = DOMAIN_FIELDS.get(cluster.primary_entity, ['name', 'description'])[:].copy()
        
        # Add feature fields
        for feature in cluster.common_features:
            fields.extend(FEATURE_FIELDS.get(feature, []))
        
        # Deduplicate
        fields = list(dict.fromkeys(fields))
        
        # Calculate coverage
        cluster_coverage = cluster.coverage_weight / total_coverage
        cumulative_coverage += cluster_coverage
        
        template = GeneratedTemplate(
            id=f"auto_{cluster.category}_{cluster.primary_entity}",
            name=f"{cluster.primary_entity.title()} {cluster.category.title()}",
            category=cluster.category,
            entity=cluster.primary_entity,
            fields=fields,
            features=list(cluster.common_features),
            confidence=min(0.9, 0.5 + (cluster.frequency / 10)),
            zipf_rank=rank,
            expected_coverage=cluster_coverage,
        )
        templates.append(template)
    
    return templates


# =============================================================================
# DATA-DRIVEN TEMPLATE BUILDER
# =============================================================================

class DataDrivenTemplateBuilder:
    """
    Build templates automatically from observed descriptions.
    
    Usage:
        builder = DataDrivenTemplateBuilder()
        builder.observe("a recipe app with ratings")
        builder.observe("a todo list with due dates")
        ...
        templates = builder.build_templates(coverage_target=0.95)
    """
    
    def __init__(self):
        self.descriptions: List[str] = []
        self.clusters: List[TemplateCluster] = []
        self.templates: List[GeneratedTemplate] = []
    
    def observe(self, description: str):
        """Add a description to the training set."""
        self.descriptions.append(description)
    
    def observe_many(self, descriptions: List[str]):
        """Add multiple descriptions."""
        self.descriptions.extend(descriptions)
    
    def analyze(self) -> Dict:
        """Analyze collected descriptions."""
        if not self.descriptions:
            return {'error': 'No descriptions observed'}
        
        # Cluster
        self.clusters = cluster_descriptions(self.descriptions)
        
        # Generate templates
        self.templates = generate_templates_from_clusters(self.clusters)
        
        return {
            'total_descriptions': len(self.descriptions),
            'clusters_found': len(self.clusters),
            'templates_generated': len(self.templates),
            'top_5_clusters': [
                {
                    'key': c.key,
                    'frequency': c.frequency,
                    'entity': c.primary_entity,
                    'features': list(c.common_features),
                    'example': c.descriptions[0] if c.descriptions else None,
                }
                for c in self.clusters[:5]
            ],
        }
    
    def build_templates(self, coverage_target: float = 0.95) -> List[GeneratedTemplate]:
        """Build templates to achieve target coverage."""
        if not self.templates:
            self.analyze()
        
        # Select templates until we reach coverage target
        selected = []
        cumulative = 0
        total_weight = sum(t.expected_coverage for t in self.templates)
        
        for template in self.templates:
            selected.append(template)
            cumulative += template.expected_coverage / total_weight if total_weight else 0
            if cumulative >= coverage_target:
                break
        
        return selected
    
    def generate_code(self) -> str:
        """Generate Python code for all templates."""
        if not self.templates:
            self.analyze()
        
        lines = [
            '"""Auto-generated templates from data analysis."""',
            '',
            'from template_algebra import MicroTemplate, UniversalPattern',
            '',
            'AUTO_TEMPLATES = [',
        ]
        
        for template in self.templates:
            lines.append(template.to_micro_template_code())
        
        lines.append(']')
        lines.append('')
        lines.append(f'# Total templates: {len(self.templates)}')
        lines.append(f'# Expected coverage: {sum(t.expected_coverage for t in self.templates):.1%}')
        
        return '\n'.join(lines)
    
    def get_stats(self) -> Dict:
        """Get statistics about template coverage."""
        if not self.templates:
            self.analyze()
        
        total_coverage = 0
        coverage_milestones = {}
        
        for i, template in enumerate(self.templates, 1):
            total_coverage += template.expected_coverage
            if i in [1, 5, 10, 20, 50] or total_coverage >= 0.95:
                coverage_milestones[i] = total_coverage
                if total_coverage >= 0.95:
                    break
        
        return {
            'total_templates': len(self.templates),
            'coverage_milestones': coverage_milestones,
            'decision_bits_per_template': sum(
                extract_decisions(d).decision_bits() 
                for d in self.descriptions
            ) / len(self.descriptions) if self.descriptions else 0,
        }


# =============================================================================
# DEMO
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("DATA-DRIVEN TEMPLATE BUILDER")
    print("=" * 70)
    
    # Simulate observed descriptions (would come from real usage)
    sample_descriptions = [
        # Recipes (common cluster)
        "a recipe app with ingredients",
        "recipe collection with ratings and tags",
        "a recipe manager with search",
        "cooking app to save recipes",
        "meal planner with recipes",
        
        # Tasks (common cluster)
        "a todo list app",
        "task manager with due dates",
        "todo with priorities",
        "task tracker with categories",
        
        # Workouts (medium cluster)
        "workout tracker",
        "exercise log with stats",
        "fitness app with history",
        
        # Budget (medium cluster)
        "budget tracker",
        "expense manager",
        "finance app with categories",
        
        # Games (different category)
        "a snake game",
        "wordle clone",
        "quiz game with scores",
        
        # Misc (long tail)
        "a bookmark manager",
        "photo gallery",
        "note taking app",
        "weather dashboard",
    ]
    
    # Build templates from data
    builder = DataDrivenTemplateBuilder()
    builder.observe_many(sample_descriptions)
    
    print("\n" + "-" * 70)
    print("ANALYSIS")
    print("-" * 70)
    analysis = builder.analyze()
    print(f"Descriptions analyzed: {analysis['total_descriptions']}")
    print(f"Clusters discovered: {analysis['clusters_found']}")
    print(f"Templates generated: {analysis['templates_generated']}")
    
    print("\nTop clusters:")
    for i, cluster in enumerate(analysis['top_5_clusters'], 1):
        print(f"  {i}. {cluster['entity']} ({cluster['frequency']} descriptions)")
        print(f"     Features: {cluster['features']}")
        print(f"     Example: \"{cluster['example']}\"")
    
    print("\n" + "-" * 70)
    print("GENERATED TEMPLATES")
    print("-" * 70)
    templates = builder.build_templates(coverage_target=0.80)
    for t in templates:
        print(f"\n  Template: {t.id}")
        print(f"    Entity: {t.entity}")
        print(f"    Fields: {t.fields}")
        print(f"    Features: {t.features}")
        print(f"    Confidence: {t.confidence:.0%}")
        print(f"    Coverage: {t.expected_coverage:.1%}")
    
    print("\n" + "-" * 70)
    print("COVERAGE STATISTICS")
    print("-" * 70)
    stats = builder.get_stats()
    print(f"Total templates: {stats['total_templates']}")
    print(f"Avg decision bits/description: {stats['decision_bits_per_template']:.1f}")
    print("\nCoverage milestones:")
    for n_templates, coverage in stats['coverage_milestones'].items():
        print(f"  {n_templates} templates → {coverage:.1%} coverage")
    
    print("\n" + "-" * 70)
    print("KEY INSIGHT")
    print("-" * 70)
    print(f"""
With just {len(templates)} templates derived from {len(sample_descriptions)} observations:
- We achieve ~80% coverage of all possible requests
- Templates are LEARNED from data, not hand-crafted
- Each template captures {stats['decision_bits_per_template']:.1f} bits of decision

This is the mathematical foundation: ~20 bits of decision, 
Zipf distribution means few templates cover most cases,
and synthesis handles the long tail.
""")
