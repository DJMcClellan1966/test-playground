"""
Universal Kernel Bridge for App Forge

Bridges the Universal Kernel's semantic perception capabilities
to App Forge's inference pipeline.

This module:
1. Imports cluster perception from Universal Kernel
2. Enhances App Forge's entity detection with semantic clusters
3. Provides fallback when Universal Kernel isn't available
"""

import sys
from pathlib import Path
from typing import Dict, Set, List, Any, Optional
from dataclasses import dataclass

# Try to import Universal Kernel cluster perception
UNIVERSAL_KERNEL_PATH = Path(__file__).parent.parent.parent / 'universal-kernel'
sys.path.insert(0, str(UNIVERSAL_KERNEL_PATH))

try:
    from cluster_perception import (  # type: ignore
        SemanticClusterEngine, 
        ClusterPercept,
        perceive_for_app_forge,
        SEMANTIC_CLUSTERS
    )
    KERNEL_AVAILABLE = True
except ImportError:
    KERNEL_AVAILABLE = False
    SEMANTIC_CLUSTERS = {}


# ============================================================================
# BRIDGE FUNCTIONS
# ============================================================================

@dataclass
class SemanticInsight:
    """Semantic understanding from Universal Kernel."""
    clusters: Dict[str, float]  # Detected semantic clusters
    features: Set[str]  # Inferred features
    confidence: float
    matched_words: Dict[str, List[str]]
    reasoning: str


def get_semantic_insight(description: str) -> Optional[SemanticInsight]:
    """
    Get semantic understanding from Universal Kernel.
    
    Returns None if Universal Kernel is not available.
    """
    if not KERNEL_AVAILABLE:
        return None
    
    engine = SemanticClusterEngine()
    percept = engine.perceive(description)
    
    # Build reasoning
    reasoning_parts = []
    for cluster, matched in percept.matched_words.items():
        if cluster in percept.entities:
            reasoning_parts.append(
                f"'{', '.join(matched[:3])}' → {cluster} ({percept.entities[cluster]:.0%})"
            )
    
    reasoning = " | ".join(reasoning_parts) if reasoning_parts else "No semantic matches"
    
    return SemanticInsight(
        clusters=percept.entities,
        features=percept.features,
        confidence=max(percept.entities.values()) if percept.entities else 0.0,
        matched_words=percept.matched_words,
        reasoning=reasoning
    )


def enhance_feature_inference(description: str, base_features: Dict[str, bool]) -> Dict[str, bool]:
    """
    Enhance App Forge's feature inference with Universal Kernel insights.
    
    Args:
        description: The app description
        base_features: Features inferred by App Forge's regex patterns
    
    Returns:
        Enhanced feature dict with kernel-inferred features merged
    """
    insight = get_semantic_insight(description)
    if not insight:
        return base_features
    
    enhanced = dict(base_features)
    
    # Map semantic clusters to App Forge features
    cluster_to_features = {
        'recipe': {'has_data': True, 'search': True, 'categories': True},
        'todo': {'has_data': True, 'categories': True},
        'expense': {'has_data': True, 'export': True},
        'workout': {'has_data': True, 'history': True},
        'event': {'has_data': True},
        'note': {'has_data': True, 'search': True},
        'bookmark': {'has_data': True, 'search': True},
        'contact': {'has_data': True, 'search': True},
        'photo': {'has_data': True, 'upload': True},
        'movie': {'has_data': True, 'ratings': True},
        'music': {'has_data': True},
        'flashcard': {'has_data': True},
        'game': {'interactive': True},
        'inventory': {'has_data': True},
        'habit': {'has_data': True},
    }
    
    # Merge features from detected clusters
    for cluster, confidence in insight.clusters.items():
        if cluster in cluster_to_features and confidence > 0.5:
            for feature, value in cluster_to_features[cluster].items():
                if feature not in enhanced or not enhanced[feature]:
                    enhanced[feature] = value
    
    return enhanced


def detect_app_domain(description: str) -> Optional[str]:
    """
    Detect the primary domain/category of the app.
    
    Returns the highest-confidence cluster or None.
    """
    insight = get_semantic_insight(description)
    if not insight or not insight.clusters:
        return None
    
    # Get top cluster
    top_cluster = max(insight.clusters.items(), key=lambda x: x[1])
    return top_cluster[0]


def get_domain_template_hints(description: str) -> Dict[str, float]:
    """
    Get template matching hints based on semantic understanding.
    
    Returns a dict of template_id -> boost_score.
    """
    insight = get_semantic_insight(description)
    if not insight:
        return {}
    
    # Map clusters to template types
    cluster_to_templates = {
        'recipe': {'collection': 0.3, 'crud': 0.2},
        'todo': {'todo_list': 0.4, 'crud': 0.2},
        'expense': {'collection': 0.3, 'crud': 0.2},
        'workout': {'collection': 0.3, 'crud': 0.2},
        'event': {'calendar': 0.4, 'collection': 0.2},
        'note': {'editor': 0.3, 'collection': 0.2},
        'bookmark': {'collection': 0.3, 'crud': 0.2},
        'flashcard': {'quiz_app': 0.4, 'crud': 0.2},
        'game': {'game': 0.5, 'interactive': 0.3},
        'photo': {'gallery': 0.4, 'collection': 0.2},
    }
    
    hints = {}
    for cluster, confidence in insight.clusters.items():
        if cluster in cluster_to_templates:
            for template, boost in cluster_to_templates[cluster].items():
                current = hints.get(template, 0)
                hints[template] = max(current, boost * confidence)
    
    return hints


# ============================================================================
# STATUS AND DIAGNOSTICS
# ============================================================================

def kernel_status() -> Dict[str, Any]:
    """Get status of Universal Kernel integration."""
    return {
        'available': KERNEL_AVAILABLE,
        'kernel_path': str(UNIVERSAL_KERNEL_PATH),
        'clusters_loaded': len(SEMANTIC_CLUSTERS),
        'cluster_names': list(SEMANTIC_CLUSTERS.keys()) if KERNEL_AVAILABLE else []
    }


def test_kernel_perception(description: str) -> Dict[str, Any]:
    """Test kernel perception for diagnostics."""
    insight = get_semantic_insight(description)
    
    if not insight:
        return {
            'error': 'Universal Kernel not available',
            'kernel_available': False
        }
    
    return {
        'kernel_available': True,
        'description': description,
        'clusters': insight.clusters,
        'features': list(insight.features),
        'confidence': insight.confidence,
        'reasoning': insight.reasoning,
        'matched_words': insight.matched_words
    }


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("Universal Kernel Bridge Status")
    print("="*50)
    
    status = kernel_status()
    print(f"Available: {status['available']}")
    print(f"Path: {status['kernel_path']}")
    print(f"Clusters: {status['clusters_loaded']}")
    
    if status['available']:
        print("\n" + "="*50)
        print("Testing perception...")
        
        test_cases = [
            "recipe app with ingredients",
            "grandma's secret pasta dishes",
            "expense tracker with budget",
            "fitness journal with photos",
        ]
        
        for desc in test_cases:
            print(f"\n'{desc}'")
            result = test_kernel_perception(desc)
            print(f"  Clusters: {result['clusters']}")
            print(f"  Features: {result['features']}")
            print(f"  Reasoning: {result['reasoning']}")
