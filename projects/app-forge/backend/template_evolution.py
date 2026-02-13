"""
Template Evolution Engine

Uses matrix factorization (like LLMs' implicit compression) to:
1. Discover latent archetypes from existing templates
2. Generate new templates by combining archetypes
3. Transform templates continuously as needs change

The key insight: just as LLMs compress billions of words into
statistical patterns (latent factors), we can compress templates
into ~5-10 fundamental archetypes and recombine them.

Math: SVD decomposes template-feature matrix into:
    M ≈ U × Σ × V^T
    
Where:
    M = templates × features (binary: has feature or not)
    U = templates × archetypes (how much each template uses each archetype)
    Σ = archetype strengths (diagonal)
    V = archetypes × features (what features define each archetype)
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path

# ============================================================================
# TEMPLATE REPRESENTATION
# ============================================================================

@dataclass
class TemplateVector:
    """A template represented as a feature vector."""
    id: str
    name: str
    features: Dict[str, float]  # feature_name -> weight (0.0 to 1.0)
    source: str = "original"  # original, synthesized, evolved
    generation: int = 0  # evolution generation
    parent_ids: List[str] = field(default_factory=list)


# All features we track (binary or weighted)
ALL_FEATURES = [
    # Data operations
    "crud", "list", "database", "search", "filter", "sort", "export", "import_data",
    # UI components  
    "cards", "table", "form", "modal", "tabs", "canvas", "editor", "grid",
    # Data types
    "text", "numbers", "dates", "images", "files", "categories", "tags",
    # Behaviors
    "timer", "animation", "realtime", "notifications", "drag_drop",
    # Features
    "auth", "charts", "calendar", "ratings", "comments", "sharing",
    "scoring", "streaks", "progress", "history", "undo_redo",
    # Game mechanics
    "turns", "lives", "levels", "powerups", "leaderboard", "multiplayer",
    # App types
    "productivity", "game", "utility", "creative", "learning", "social",
]

FEATURE_INDEX = {f: i for i, f in enumerate(ALL_FEATURES)}
N_FEATURES = len(ALL_FEATURES)


# ============================================================================
# EXISTING TEMPLATES (seed data)
# ============================================================================

# These are the templates we already have — encoded as feature vectors
SEED_TEMPLATES = {
    "todo_list": {
        "crud": 1.0, "list": 1.0, "checkbox": 0.8, "dates": 0.6, 
        "categories": 0.5, "database": 0.8, "productivity": 1.0
    },
    "recipe_app": {
        "crud": 1.0, "list": 1.0, "categories": 0.9, "search": 0.8,
        "ratings": 0.7, "images": 0.5, "database": 0.9
    },
    "expense_tracker": {
        "crud": 1.0, "list": 1.0, "categories": 0.9, "charts": 0.9,
        "numbers": 1.0, "dates": 0.8, "database": 0.9, "export": 0.6
    },
    "quiz_app": {
        "list": 0.6, "scoring": 1.0, "timer": 0.7, "progress": 0.8,
        "game": 0.7, "learning": 0.9, "categories": 0.5
    },
    "calculator": {
        "numbers": 1.0, "utility": 1.0, "form": 0.5
    },
    "timer": {
        "timer": 1.0, "utility": 1.0, "notifications": 0.6, "animation": 0.5
    },
    "memory_game": {
        "grid": 1.0, "game": 1.0, "scoring": 0.8, "timer": 0.5,
        "turns": 0.7, "animation": 0.6, "levels": 0.5
    },
    "snake_game": {
        "canvas": 1.0, "game": 1.0, "scoring": 0.9, "realtime": 1.0,
        "animation": 1.0, "levels": 0.6, "lives": 0.7, "leaderboard": 0.5
    },
    "wordle": {
        "grid": 0.8, "game": 1.0, "text": 0.9, "turns": 0.8,
        "scoring": 0.5, "animation": 0.4
    },
    "markdown_editor": {
        "editor": 1.0, "text": 1.0, "creative": 0.8, "export": 0.6,
        "undo_redo": 0.7
    },
    "drawing_app": {
        "canvas": 1.0, "creative": 1.0, "export": 0.5, "undo_redo": 0.8
    },
    "flashcard_app": {
        "cards": 1.0, "learning": 1.0, "scoring": 0.5, "progress": 0.7,
        "categories": 0.6, "crud": 0.7
    },
    "habit_tracker": {
        "crud": 0.8, "streaks": 1.0, "calendar": 0.8, "progress": 0.9,
        "charts": 0.6, "productivity": 1.0, "dates": 0.9
    },
    "bookmark_manager": {
        "crud": 1.0, "list": 1.0, "categories": 0.9, "tags": 0.8,
        "search": 0.9, "database": 0.8, "import_data": 0.5, "export": 0.5
    },
    "password_generator": {
        "utility": 1.0, "text": 0.6, "form": 0.5
    },
    "color_picker": {
        "utility": 1.0, "creative": 0.5, "form": 0.6
    },
    "pomodoro": {
        "timer": 1.0, "productivity": 1.0, "notifications": 0.8,
        "streaks": 0.5, "progress": 0.6
    },
    "reaction_test": {
        "timer": 0.8, "game": 1.0, "scoring": 0.9, "realtime": 0.7,
        "animation": 0.5, "leaderboard": 0.6
    },
}


# ============================================================================
# MATRIX FACTORIZATION ENGINE
# ============================================================================

class TemplateEvolver:
    """
    Uses SVD to discover latent archetypes and evolve templates.
    
    The core idea: templates that share features are "nearby" in latent space.
    We can interpolate between templates or extrapolate to create new ones.
    """
    
    def __init__(self, n_archetypes: int = 6):
        self.n_archetypes = n_archetypes
        self.templates: Dict[str, TemplateVector] = {}
        self.matrix: np.ndarray = None  # templates × features
        self.U: np.ndarray = None  # templates × archetypes
        self.S: np.ndarray = None  # archetype strengths
        self.Vt: np.ndarray = None  # archetypes × features
        self.template_ids: List[str] = []  # row order in matrix
        self._fitted = False
    
    def load_seed_templates(self):
        """Load the built-in template definitions."""
        for tid, features in SEED_TEMPLATES.items():
            vec = TemplateVector(
                id=tid,
                name=tid.replace("_", " ").title(),
                features=features,
                source="original"
            )
            self.templates[tid] = vec
    
    def _build_matrix(self) -> np.ndarray:
        """Build the template × feature matrix."""
        self.template_ids = list(self.templates.keys())
        n_templates = len(self.template_ids)
        
        M = np.zeros((n_templates, N_FEATURES))
        for i, tid in enumerate(self.template_ids):
            for feat, weight in self.templates[tid].features.items():
                if feat in FEATURE_INDEX:
                    M[i, FEATURE_INDEX[feat]] = weight
        
        return M
    
    def fit(self):
        """
        Perform SVD to discover latent archetypes.
        
        After fitting:
        - U[i, :] = template i's position in archetype space
        - Vt[:, j] = feature j's loadings on each archetype
        - S = how important each archetype is
        """
        self.matrix = self._build_matrix()
        
        # SVD decomposition
        # M ≈ U @ diag(S) @ Vt
        self.U, self.S, self.Vt = np.linalg.svd(self.matrix, full_matrices=False)
        
        # Truncate to n_archetypes
        k = min(self.n_archetypes, len(self.S))
        self.U = self.U[:, :k]
        self.S = self.S[:k]
        self.Vt = self.Vt[:k, :]
        
        self._fitted = True
        return self
    
    def get_archetype_names(self) -> List[str]:
        """
        Infer archetype names from their top features.
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")
        
        names = []
        for i in range(len(self.S)):
            # Get top 3 features for this archetype
            top_indices = np.argsort(np.abs(self.Vt[i]))[-3:][::-1]
            top_features = [ALL_FEATURES[j] for j in top_indices]
            names.append(f"Archetype_{i}: {'+'.join(top_features)}")
        
        return names
    
    def get_archetype_loadings(self) -> Dict[str, Dict[str, float]]:
        """
        Get feature loadings for each archetype.
        
        Returns dict of archetype_name -> {feature: loading}
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")
        
        result = {}
        for i in range(len(self.S)):
            loadings = {}
            for j, feat in enumerate(ALL_FEATURES):
                if abs(self.Vt[i, j]) > 0.1:  # Only significant loadings
                    loadings[feat] = round(self.Vt[i, j], 3)
            
            # Sort by absolute value
            loadings = dict(sorted(loadings.items(), 
                                   key=lambda x: abs(x[1]), reverse=True))
            result[f"archetype_{i}"] = loadings
        
        return result
    
    def template_to_archetype_space(self, features: Dict[str, float]) -> np.ndarray:
        """
        Project a feature vector into archetype space.
        
        This is how we convert user requirements → latent representation.
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")
        
        # Build feature vector
        vec = np.zeros(N_FEATURES)
        for feat, weight in features.items():
            if feat in FEATURE_INDEX:
                vec[FEATURE_INDEX[feat]] = weight
        
        # Project: archetype_coords = vec @ V^T.T @ inv(diag(S))
        # Simplified: archetype_coords = vec @ Vt.T / S
        archetype_coords = (vec @ self.Vt.T) / self.S
        
        return archetype_coords
    
    def archetype_to_features(self, archetype_coords: np.ndarray) -> Dict[str, float]:
        """
        Convert archetype space coordinates back to features.
        
        This is how we generate templates from latent representations.
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")
        
        # Reconstruct: features = archetype_coords @ diag(S) @ Vt
        feature_vec = archetype_coords @ np.diag(self.S) @ self.Vt
        
        # Convert to dict, only keeping positive values
        features = {}
        for i, val in enumerate(feature_vec):
            if val > 0.1:  # Threshold
                features[ALL_FEATURES[i]] = round(min(val, 1.0), 2)
        
        return features
    
    def find_nearest_templates(self, features: Dict[str, float], n: int = 3) -> List[Tuple[str, float]]:
        """
        Find the n nearest existing templates to a feature set.
        
        Uses cosine similarity in archetype space.
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")
        
        # Project query to archetype space
        query_arch = self.template_to_archetype_space(features)
        
        # Compare to all templates
        similarities = []
        for i, tid in enumerate(self.template_ids):
            template_arch = self.U[i, :]
            
            # Cosine similarity
            dot = np.dot(query_arch, template_arch)
            norm = np.linalg.norm(query_arch) * np.linalg.norm(template_arch)
            sim = dot / norm if norm > 0 else 0
            
            similarities.append((tid, float(sim)))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:n]
    
    def interpolate_templates(self, 
                              template_a: str, 
                              template_b: str, 
                              alpha: float = 0.5) -> Dict[str, float]:
        """
        Create a new template by interpolating between two existing ones.
        
        alpha=0.0 → pure template_a
        alpha=0.5 → halfway blend
        alpha=1.0 → pure template_b
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")
        
        idx_a = self.template_ids.index(template_a)
        idx_b = self.template_ids.index(template_b)
        
        # Interpolate in archetype space
        arch_a = self.U[idx_a, :]
        arch_b = self.U[idx_b, :]
        arch_blend = (1 - alpha) * arch_a + alpha * arch_b
        
        # Convert back to features
        return self.archetype_to_features(arch_blend)
    
    def evolve_template(self, 
                        template_id: str, 
                        direction: Dict[str, float],
                        strength: float = 0.3) -> Dict[str, float]:
        """
        Evolve a template in a direction defined by features.
        
        Example: evolve("todo_list", {"charts": 1, "progress": 1}, 0.5)
                 → todo_list with more visualization features
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")
        
        idx = self.template_ids.index(template_id)
        original_arch = self.U[idx, :]
        
        # Project direction into archetype space
        direction_arch = self.template_to_archetype_space(direction)
        
        # Move in that direction
        evolved_arch = original_arch + strength * direction_arch
        
        # Convert back to features
        return self.archetype_to_features(evolved_arch)
    
    def synthesize_from_description(self, 
                                    detected_features: Dict[str, float]) -> Tuple[Dict[str, float], str]:
        """
        Given detected features from a description, synthesize a complete template.
        
        This is the key function: partial features → complete template.
        
        Returns (full_features, reasoning)
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")
        
        # Project to archetype space
        arch_coords = self.template_to_archetype_space(detected_features)
        
        # Find nearest templates for reasoning
        nearest = self.find_nearest_templates(detected_features, n=2)
        
        # Reconstruct full features
        full_features = self.archetype_to_features(arch_coords)
        
        # Build reasoning
        reasoning = f"Projected to archetype space, nearest: {nearest[0][0]} ({nearest[0][1]:.0%})"
        if len(nearest) > 1:
            reasoning += f", {nearest[1][0]} ({nearest[1][1]:.0%})"
        
        return full_features, reasoning
    
    def explain_template(self, template_id: str) -> Dict:
        """
        Explain a template in terms of archetypes.
        """
        if not self._fitted:
            raise ValueError("Must call fit() first")
        
        idx = self.template_ids.index(template_id)
        arch_coords = self.U[idx, :]
        
        # Get archetype contributions
        contributions = []
        for i, coord in enumerate(arch_coords):
            # Get top features of this archetype
            top_indices = np.argsort(np.abs(self.Vt[i]))[-3:][::-1]
            top_features = [ALL_FEATURES[j] for j in top_indices]
            
            contributions.append({
                "archetype": i,
                "weight": round(coord * self.S[i], 2),  # Include singular value
                "top_features": top_features
            })
        
        # Sort by absolute weight
        contributions.sort(key=lambda x: abs(x["weight"]), reverse=True)
        
        return {
            "template_id": template_id,
            "archetype_coords": [round(x, 3) for x in arch_coords],
            "contributions": contributions
        }


# ============================================================================
# CONTINUOUS EVOLUTION
# ============================================================================

class TemplateGrower:
    """
    Continuously grows the template library by:
    1. Learning from user builds
    2. Synthesizing templates for gaps
    3. Refining archetypes as patterns emerge
    """
    
    def __init__(self, evolver: TemplateEvolver):
        self.evolver = evolver
        self.build_history: List[Dict] = []
        self.synthesis_count = 0
    
    def record_build(self, description: str, features: Dict[str, float], 
                     success: bool, template_used: str = None):
        """Record a build for learning."""
        self.build_history.append({
            "description": description,
            "features": features,
            "success": success,
            "template": template_used
        })
    
    def find_coverage_gaps(self, n: int = 5) -> List[Dict]:
        """
        Find feature combinations not well covered by existing templates.
        
        These are candidates for new template synthesis.
        """
        if not self.evolver._fitted:
            raise ValueError("Evolver must be fitted")
        
        gaps = []
        
        # Sample random feature combinations
        rng = np.random.default_rng(42)
        for _ in range(100):
            # Random sparse feature vector
            n_features = rng.integers(3, 8)
            indices = rng.choice(N_FEATURES, size=n_features, replace=False)
            features = {ALL_FEATURES[i]: 0.8 for i in indices}
            
            # Find nearest template
            nearest = self.evolver.find_nearest_templates(features, n=1)
            
            if nearest and nearest[0][1] < 0.5:  # Low similarity = gap
                gaps.append({
                    "features": features,
                    "nearest_template": nearest[0][0],
                    "similarity": nearest[0][1]
                })
        
        # Sort by lowest similarity (biggest gaps)
        gaps.sort(key=lambda x: x["similarity"])
        return gaps[:n]
    
    def synthesize_gap_template(self, gap: Dict) -> TemplateVector:
        """
        Synthesize a new template to fill a coverage gap.
        """
        features = gap["features"]
        full_features, reasoning = self.evolver.synthesize_from_description(features)
        
        self.synthesis_count += 1
        
        return TemplateVector(
            id=f"synth_{self.synthesis_count:03d}",
            name=f"Synthesized Template {self.synthesis_count}",
            features=full_features,
            source="synthesized",
            generation=1,
            parent_ids=[gap["nearest_template"]]
        )


# ============================================================================
# DEMO
# ============================================================================

def demo():
    print("=" * 60)
    print("TEMPLATE EVOLUTION ENGINE")
    print("Matrix Factorization for Template Discovery")
    print("=" * 60)
    
    # Initialize and fit
    evolver = TemplateEvolver(n_archetypes=6)
    evolver.load_seed_templates()
    evolver.fit()
    
    print(f"\nLoaded {len(evolver.templates)} templates")
    print(f"Matrix shape: {evolver.matrix.shape}")
    print(f"Discovered {len(evolver.S)} archetypes")
    
    # Show discovered archetypes
    print("\n" + "-" * 40)
    print("DISCOVERED ARCHETYPES (Latent Factors)")
    print("-" * 40)
    
    archetype_loadings = evolver.get_archetype_loadings()
    for name, loadings in archetype_loadings.items():
        top_3 = list(loadings.items())[:5]
        print(f"\n{name}:")
        for feat, val in top_3:
            bar = "█" * int(abs(val) * 10)
            sign = "+" if val > 0 else "-"
            print(f"  {sign}{feat:15s} {bar} ({val:+.2f})")
    
    # Explain variance
    print("\n" + "-" * 40)
    print("VARIANCE EXPLAINED BY EACH ARCHETYPE")
    print("-" * 40)
    
    total_var = np.sum(evolver.S ** 2)
    for i, s in enumerate(evolver.S):
        pct = (s ** 2 / total_var) * 100
        bar = "█" * int(pct / 2)
        print(f"  Archetype {i}: {bar} {pct:.1f}%")
    
    # Demo: Interpolation
    print("\n" + "-" * 40)
    print("TEMPLATE INTERPOLATION")
    print("-" * 40)
    
    print("\nBlending todo_list + expense_tracker (50/50):")
    blend = evolver.interpolate_templates("todo_list", "expense_tracker", 0.5)
    print(f"  Result: {blend}")
    
    # Demo: Evolution
    print("\n" + "-" * 40)
    print("TEMPLATE EVOLUTION")
    print("-" * 40)
    
    print("\nEvolving todo_list toward charts & progress:")
    evolved = evolver.evolve_template(
        "todo_list", 
        {"charts": 1.0, "progress": 1.0, "streaks": 0.8},
        strength=0.5
    )
    print(f"  Original: {evolver.templates['todo_list'].features}")
    print(f"  Evolved:  {evolved}")
    
    # Demo: Synthesis from description
    print("\n" + "-" * 40)
    print("SYNTHESIS FROM PARTIAL FEATURES")
    print("-" * 40)
    
    partial = {"canvas": 0.9, "creative": 0.8, "export": 0.5}
    print(f"\nInput features: {partial}")
    full, reasoning = evolver.synthesize_from_description(partial)
    print(f"Synthesized: {full}")
    print(f"Reasoning: {reasoning}")
    
    # Demo: Gap finding
    print("\n" + "-" * 40)
    print("COVERAGE GAP ANALYSIS")
    print("-" * 40)
    
    grower = TemplateGrower(evolver)
    gaps = grower.find_coverage_gaps(n=3)
    print("\nTop 3 gaps (feature combos not well covered):")
    for gap in gaps:
        print(f"\n  Features: {list(gap['features'].keys())}")
        print(f"  Nearest: {gap['nearest_template']} ({gap['similarity']:.0%} similar)")
    
    print("\n" + "=" * 60)
    print("This is how LLM-style compression works for templates!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
