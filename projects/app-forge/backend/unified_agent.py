"""
Unified Inference Agent

Bridges all App Forge intelligence systems into a single pipeline:

1. Universal Kernel (cluster perception) - Semantic understanding
2. Template Evolution (SVD archetypes) - Latent space operations
3. Memory System (build history) - Learning from past builds
4. Regex inference (rules) - Fast pattern matching

Pipeline:
  Description → Cluster Perception → Feature Detection
                                   ↓
              Template Evolution → Find/Synthesize Template
                                   ↓
              Memory System → Apply learned patterns
                                   ↓
              Generate → Code Output

This agent can:
- Transform templates on-the-fly using SVD operations
- Fill gaps when no exact template matches
- Learn and improve from each build
- Explain its reasoning at each step
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
import json

# ============================================================================
# IMPORT ALL INTELLIGENCE MODULES
# ============================================================================

# Template Evolution (SVD archetypes)
try:
    from template_evolution import (
        TemplateEvolver, TemplateGrower, TemplateVector,
        ALL_FEATURES, FEATURE_INDEX, N_FEATURES, SEED_TEMPLATES
    )
    HAS_EVOLUTION = True
except ImportError:
    HAS_EVOLUTION = False
    print("Warning: template_evolution not available")

# Universal Kernel (cluster perception)
KERNEL_PATH = Path(__file__).parent.parent.parent / 'universal-kernel'
sys.path.insert(0, str(KERNEL_PATH))

try:
    from cluster_perception import (  # type: ignore
        SemanticClusterEngine, ClusterPercept, 
        perceive_for_app_forge, SEMANTIC_CLUSTERS
    )
    HAS_KERNEL = True
except ImportError:
    HAS_KERNEL = False
    print("Warning: cluster_perception not available")

# Memory System
try:
    from kernel_memory import app_memory, learn, suggest_from_memory
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False
    app_memory = None

# Template Registry (existing)
try:
    from template_registry import match_template, TEMPLATES
    HAS_REGISTRY = True
except ImportError:
    HAS_REGISTRY = False


# ============================================================================
# UNIFIED INFERENCE RESULT
# ============================================================================

@dataclass
class InferenceResult:
    """Complete inference result from the unified agent."""
    
    # Core outputs
    template_id: str
    features: Dict[str, float]
    confidence: float
    
    # Sources used
    used_kernel: bool = False
    used_evolution: bool = False
    used_memory: bool = False
    used_registry: bool = False
    
    # Semantic understanding
    clusters: Dict[str, float] = field(default_factory=dict)
    matched_words: Dict[str, List[str]] = field(default_factory=dict)
    
    # Archetype analysis
    archetype_coords: List[float] = field(default_factory=list)
    nearest_templates: List[Tuple[str, float]] = field(default_factory=list)
    
    # Memory
    similar_builds: int = 0
    learned_features: Set[str] = field(default_factory=set)
    
    # Evolution
    was_synthesized: bool = False
    was_evolved: bool = False
    evolution_direction: Dict[str, float] = field(default_factory=dict)
    
    # Reasoning chain
    reasoning: List[str] = field(default_factory=list)
    
    def add_reasoning(self, step: str):
        self.reasoning.append(step)
    
    def to_dict(self) -> Dict:
        return {
            "template_id": self.template_id,
            "features": {k: round(v, 2) if isinstance(v, float) else v 
                        for k, v in self.features.items()},
            "confidence": round(self.confidence, 2),
            "sources": {
                "kernel": self.used_kernel,
                "evolution": self.used_evolution,
                "memory": self.used_memory,
                "registry": self.used_registry,
            },
            "clusters": {k: round(v, 2) for k, v in self.clusters.items()},
            "archetypes": [round(x, 3) for x in self.archetype_coords],
            "nearest": self.nearest_templates[:3],
            "reasoning": self.reasoning,
            "synthesized": self.was_synthesized,
            "evolved": self.was_evolved,
        }


# ============================================================================
# CLUSTER → FEATURE MAPPING
# ============================================================================

# Maps semantic clusters to template features
CLUSTER_TO_FEATURES = {
    "recipe": {"crud": 0.9, "list": 0.8, "categories": 0.9, "search": 0.7, 
               "database": 0.8, "ratings": 0.5, "images": 0.4},
    "task": {"crud": 0.9, "list": 0.9, "dates": 0.8, "database": 0.7,
             "productivity": 0.9},
    "expense": {"crud": 0.9, "numbers": 1.0, "charts": 0.8, "categories": 0.8,
                "dates": 0.7, "database": 0.9, "export": 0.6},
    "workout": {"crud": 0.8, "progress": 0.9, "charts": 0.7, "dates": 0.8,
                "streaks": 0.7, "productivity": 0.8},
    "habit": {"streaks": 1.0, "calendar": 0.8, "progress": 0.9, "dates": 0.9,
              "productivity": 1.0, "crud": 0.7},
    "quiz": {"scoring": 1.0, "timer": 0.7, "progress": 0.8, "game": 0.7,
             "learning": 0.9, "categories": 0.5},
    "game": {"game": 1.0, "scoring": 0.8, "animation": 0.7, "realtime": 0.6},
    "timer": {"timer": 1.0, "utility": 1.0, "notifications": 0.6},
    "generator": {"utility": 1.0, "form": 0.6, "text": 0.5},
    "editor": {"editor": 1.0, "text": 0.9, "creative": 0.8, "undo_redo": 0.7},
    "drawing": {"canvas": 1.0, "creative": 1.0, "undo_redo": 0.8},
    "note": {"editor": 0.8, "text": 0.9, "crud": 0.7, "creative": 0.6},
    "bookmark": {"crud": 0.9, "list": 0.9, "categories": 0.9, "tags": 0.8,
                 "search": 0.9, "database": 0.8, "import_data": 0.5},
    "photo": {"images": 1.0, "crud": 0.6, "creative": 0.7},
    "event": {"calendar": 1.0, "dates": 1.0, "crud": 0.8, "notifications": 0.6},
    
    # New clusters for novel domains
    "investment": {"crud": 0.9, "numbers": 1.0, "charts": 1.0, "realtime": 0.9,
                   "database": 0.9, "categories": 0.7, "progress": 0.8},
    "science": {"canvas": 0.8, "charts": 1.0, "numbers": 0.9, "animation": 0.6,
                "export": 0.8, "categories": 0.5, "utility": 0.7},
    "medical": {"crud": 0.9, "database": 1.0, "dates": 0.8, "progress": 0.7,
                "categories": 0.8, "notifications": 0.6, "charts": 0.6},
    "developer": {"editor": 1.0, "text": 0.9, "crud": 0.7, "search": 0.9,
                  "categories": 0.7, "export": 0.8, "utility": 0.8},
    "analytics": {"charts": 1.0, "numbers": 1.0, "database": 0.9, "realtime": 0.7,
                  "export": 0.9, "progress": 0.8, "categories": 0.6},
    "social": {"auth": 1.0, "crud": 0.9, "realtime": 0.9, "notifications": 0.8,
               "database": 0.9, "images": 0.6},
    "ecommerce": {"crud": 0.9, "database": 1.0, "numbers": 0.8, "categories": 0.9,
                  "search": 0.8, "images": 0.7, "form": 0.7},
    "travel": {"crud": 0.9, "database": 0.8, "calendar": 0.9, "dates": 1.0,
               "search": 0.8, "categories": 0.7, "images": 0.5},
}


# ============================================================================
# UNIFIED INFERENCE AGENT
# ============================================================================

class UnifiedAgent:
    """
    The main inference agent that orchestrates all intelligence systems.
    
    Flow:
    1. Semantic perception (Universal Kernel clusters)
    2. Feature mapping (clusters → template features)
    3. Archetype projection (SVD → latent space)
    4. Template matching/synthesis
    5. Memory augmentation
    6. Result with full reasoning
    """
    
    def __init__(self):
        # Initialize subsystems
        self.evolver = None
        self.grower = None
        self.kernel = None
        self.agentic_loop = None
        self.world_model = None
        self.memory_system = None
        self.feedback_enabled = False
        self.socratic_advisor = None
        self.socratic_dialogue = None
        
        if HAS_EVOLUTION:
            self.evolver = TemplateEvolver(n_archetypes=6)
            self.evolver.load_seed_templates()
            self.evolver.fit()
            self.grower = TemplateGrower(self.evolver)
        
        if HAS_KERNEL:
            self.kernel = SemanticClusterEngine()
            try:
                import sys, os
                uk_path = str(Path(__file__).parent.parent.parent / 'projects' / 'universal-kernel')
                if os.path.isdir(uk_path):
                    sys.path.insert(0, uk_path)
                    try:
                        import importlib
                        agent_loop = importlib.import_module('agent_loop')
                        self.agentic_loop = agent_loop.LocalAgent()
                        self.world_model = agent_loop.WorldModel()
                        self.feedback_enabled = True
                    except Exception:
                        self.agentic_loop = None
                        self.world_model = None
                        self.feedback_enabled = False
                else:
                    self.agentic_loop = None
                    self.world_model = None
                    self.feedback_enabled = False
            except Exception:
                self.agentic_loop = None
                self.world_model = None
                self.feedback_enabled = False
        
        try:
            import sys, os
            uk_path = str(Path(__file__).parent.parent.parent / 'projects' / 'universal-kernel')
            if os.path.isdir(uk_path):
                sys.path.insert(0, uk_path)
                try:
                    import importlib
                    kernel_mod = importlib.import_module('kernel')
                    self.memory_system = kernel_mod.MemorySystem()
                except Exception:
                    self.memory_system = None
            else:
                self.memory_system = None
        except Exception:
            self.memory_system = None
        # Integrate Socratic-Learner
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'projects' / 'socratic-learner'))
            import sys, os
            sl_path = str(Path(__file__).parent.parent.parent / 'projects' / 'socratic-learner')
            if os.path.isdir(sl_path):
                sys.path.insert(0, sl_path)
                try:
                    import importlib
                    blueprint_advisor_mod = importlib.import_module('blueprint_advisor')
                    socrates_mod = importlib.import_module('socrates')
                    self.socratic_advisor = blueprint_advisor_mod.BlueprintAdvisor()
                    self.socratic_dialogue = socrates_mod.Socrates()
                except Exception:
                    self.socratic_advisor = None
                    self.socratic_dialogue = None
            else:
                self.socratic_advisor = None
                self.socratic_dialogue = None
        except Exception:
            self.socratic_advisor = None
            self.socratic_dialogue = None
        # ...existing code...
    
    def infer(self, description: str) -> InferenceResult:
        """
        Main inference entry point.
        Integrates universal-kernel agentic loop, semantic cluster perception, world model, memory, template evolution, and Socratic-Learner.
        """
        result = InferenceResult(
            template_id="generic",
            features={},
            confidence=0.0
        )
        # Step 1: Semantic Perception (Universal Kernel)
        detected_features = self._perceive(description, result)
        # Step 2: World Model feature inference
        if self.world_model:
            try:
                import sys, os
                uk_path = str(Path(__file__).parent.parent.parent / 'projects' / 'universal-kernel')
                if os.path.isdir(uk_path):
                    sys.path.insert(0, uk_path)
                    try:
                        import importlib
                        agent_loop = importlib.import_module('agent_loop')
                        percept = agent_loop.Percept(raw=description)
                        agent_features = self.world_model._infer_features(percept)
                        for feat in agent_features:
                            detected_features[feat] = max(detected_features.get(feat, 0), 0.7)
                        result.add_reasoning(f"WorldModel inferred features: {list(agent_features)}")
                    except Exception:
                        result.add_reasoning("WorldModel not available")
                else:
                    result.add_reasoning("WorldModel not available")
            except Exception:
                result.add_reasoning("WorldModel not available")
        # Step 3: Socratic-Learner feature discovery
        if self.socratic_advisor:
            try:
                advisor_response = self.socratic_advisor.start_discovery(description)
                result.add_reasoning(f"Socratic Advisor: {advisor_response}")
                # Optionally probe for MVP scoping
                mvp_question = self.socratic_advisor._handle_mvp(description)
                result.add_reasoning(f"Socratic MVP Scoping: {mvp_question}")
            except Exception:
                result.add_reasoning("Socratic Advisor not available")
        # Step 4: Socratic dialogue for feedback
        if self.socratic_dialogue:
            try:
                socratic_response = self.socratic_dialogue.respond(description)
                result.add_reasoning(f"Socratic Dialogue: {socratic_response}")
            except Exception:
                result.add_reasoning("Socratic Dialogue not available")
        # Step 5: Memory Augmentation
        self._augment_from_memory(description, detected_features, result)
        # Step 6: Archetype Projection & Template Match
        self._find_or_synthesize_template(detected_features, result)
        # Step 7: Agentic Loop planning/learning
        if self.agentic_loop:
            try:
                self.agentic_loop.perceive(description)
                plan = self.agentic_loop.decide()
                act_result = self.agentic_loop.act(plan)
                result.add_reasoning(f"Agentic loop planned and acted: {plan}")
                # Optionally learn from feedback
                if self.feedback_enabled:
                    self.agentic_loop.learn(1.0)  # Dummy positive feedback
                    result.add_reasoning("Agentic loop learned from feedback")
            except Exception:
                result.add_reasoning("Agentic loop not available")
        # Step 8: Fill in final features
        result.features = detected_features
        return result
    
    def _perceive(self, description: str, result: InferenceResult) -> Dict[str, float]:
        """
        Step 1: Use Universal Kernel to understand the description.
        """
        features: Dict[str, float] = {}
        
        if self.kernel:
            percept = self.kernel.perceive(description)
            
            result.clusters = percept.entities
            result.matched_words = percept.matched_words
            result.used_kernel = True
            
            # Map clusters to features
            for cluster, conf in percept.entities.items():
                if cluster in CLUSTER_TO_FEATURES:
                    for feat, weight in CLUSTER_TO_FEATURES[cluster].items():
                        # Combine: multiply by cluster confidence
                        combined = weight * conf
                        features[feat] = max(features.get(feat, 0), combined)
            
            result.add_reasoning(
                f"Kernel detected clusters: {list(percept.entities.keys())} → "
                f"mapped to {len(features)} features"
            )
        else:
            result.add_reasoning("Kernel not available, using fallback")
        
        return features
    
    def _augment_from_memory(self, description: str, 
                              features: Dict[str, float], 
                              result: InferenceResult):
        """
        Step 2: Apply learned patterns from memory.
        """
        if not HAS_MEMORY or not app_memory:
            return
        
        similar = app_memory.recall_similar_builds(description, n=3)
        if not similar:
            return
        
        result.similar_builds = len(similar)
        result.used_memory = True
        
        # Vote on features from successful builds
        feature_votes: Dict[str, int] = {}
        successful = [b for b in similar if b.success]
        
        for build in successful:
            for feat in build.features:
                feature_votes[feat] = feature_votes.get(feat, 0) + 1
        
        # Apply high-confidence features
        if successful:
            for feat, votes in feature_votes.items():
                ratio = votes / len(successful)
                if ratio >= 0.6:
                    # Map to our feature names
                    if feat in ALL_FEATURES or feat in features:
                        current = features.get(feat, 0)
                        features[feat] = max(current, ratio)
                        result.learned_features.add(feat)
        
        result.add_reasoning(
            f"Memory found {len(similar)} similar builds, "
            f"learned {len(result.learned_features)} features"
        )
    
    def _find_or_synthesize_template(self, features: Dict[str, float], 
                                      result: InferenceResult):
        """
        Step 3: Find best template or synthesize a new one.
        
        Uses SVD archetype space for matching and synthesis.
        """
        if not self.evolver:
            # Fallback to registry
            if HAS_REGISTRY:
                # Convert features to description for registry
                desc = " ".join(features.keys())
                template_id, reg_features, scores = match_template(desc)
                result.template_id = template_id
                result.used_registry = True
                result.confidence = scores[0][1] if scores else 0.5
                result.add_reasoning(f"Registry match: {template_id}")
            return
        
        result.used_evolution = True
        
        # Project to archetype space
        if features:
            arch_coords = self.evolver.template_to_archetype_space(features)
            result.archetype_coords = list(arch_coords)
        
        # Find nearest templates
        nearest = self.evolver.find_nearest_templates(features, n=3)
        result.nearest_templates = nearest
        
        if nearest:
            best_id, best_sim = nearest[0]
            result.confidence = best_sim
            
            if best_sim >= 0.8:
                # Good match
                result.template_id = best_id
                result.add_reasoning(
                    f"Strong archetype match: {best_id} ({best_sim:.0%})"
                )
            
            elif best_sim >= 0.5:
                # Partial match — evolve template
                result.template_id = best_id
                result.was_evolved = True
                
                # Calculate evolution direction
                base_features = self.evolver.templates[best_id].features
                direction = {}
                for feat, val in features.items():
                    base_val = base_features.get(feat, 0)
                    if val > base_val + 0.2:
                        direction[feat] = val - base_val
                
                result.evolution_direction = direction
                
                # Evolve in archetype space
                if direction:
                    evolved = self.evolver.evolve_template(
                        best_id, direction, strength=0.4
                    )
                    # Merge evolved features
                    for feat, val in evolved.items():
                        features[feat] = max(features.get(feat, 0), val)
                
                result.add_reasoning(
                    f"Evolved {best_id} ({best_sim:.0%}) toward {list(direction.keys())}"
                )
            
            else:
                # Low match — synthesize new template
                result.was_synthesized = True
                synth_features, reasoning = self.evolver.synthesize_from_description(features)
                
                # Use synthesized features
                for feat, val in synth_features.items():
                    features[feat] = max(features.get(feat, 0), val)
                
                result.template_id = f"synthesized_from_{best_id}"
                result.add_reasoning(f"Synthesized new template: {reasoning}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global agent instance
_agent: Optional[UnifiedAgent] = None

def get_agent() -> UnifiedAgent:
    """Get or create the global agent instance."""
    global _agent
    if _agent is None:
        _agent = UnifiedAgent()
    return _agent


def unified_infer(description: str) -> InferenceResult:
    """
    Main entry point for unified inference.
    
    Usage:
        result = unified_infer("a recipe collection app")
        print(result.template_id)  # "recipe_app" or similar
        print(result.features)     # {"crud": 0.9, "categories": 0.8, ...}
        print(result.reasoning)    # Step-by-step explanation
    """
    return get_agent().infer(description)


def infer_features(description: str) -> Dict[str, float]:
    """Get just the features dict."""
    return get_agent().infer(description).features


def explain_inference(description: str) -> str:
    """Get a human-readable explanation."""
    result = get_agent().infer(description)
    
    lines = ["=" * 50]
    lines.append(f"Input: {description}")
    lines.append("=" * 50)
    
    lines.append(f"\nTemplate: {result.template_id}")
    lines.append(f"Confidence: {result.confidence:.0%}")
    
    lines.append(f"\nClusters: {result.clusters}")
    lines.append(f"Features: {dict(list(result.features.items())[:8])}")
    
    lines.append("\nReasoning:")
    for i, step in enumerate(result.reasoning, 1):
        lines.append(f"  {i}. {step}")
    
    lines.append("\nSources Used:")
    lines.append(f"  Kernel: {'✓' if result.used_kernel else '✗'}")
    lines.append(f"  Evolution: {'✓' if result.used_evolution else '✗'}")
    lines.append(f"  Memory: {'✓' if result.used_memory else '✗'}")
    lines.append(f"  Registry: {'✓' if result.used_registry else '✗'}")
    
    if result.was_synthesized:
        lines.append("\n⚡ Template was SYNTHESIZED (no close match)")
    elif result.was_evolved:
        lines.append(f"\n⚡ Template was EVOLVED toward: {list(result.evolution_direction.keys())}")
    
    return "\n".join(lines)


# ============================================================================
# FOR SMARTQ INTEGRATION
# ============================================================================

def enhance_smartq_inference(description: str, 
                              base_inferred: Dict[str, bool]) -> Dict[str, bool]:
    """
    Enhance smartq's regex-based inference with unified agent.
    
    Call this from smartq.infer_from_description() to add
    semantic understanding without breaking existing logic.
    """
    result = get_agent().infer(description)
    enhanced = dict(base_inferred)
    
    # Map unified features to smartq question IDs
    FEATURE_TO_QUESTION = {
        "crud": "has_data",
        "database": "has_data",
        "list": "has_data",
        "auth": "needs_auth",
        "realtime": "realtime",
        "search": "search",
        "export": "export",
        "charts": "has_data",  # charts imply data
        "calendar": "has_data",
    }
    
    for feat, weight in result.features.items():
        if feat in FEATURE_TO_QUESTION and weight >= 0.6:
            qid = FEATURE_TO_QUESTION[feat]
            if qid not in enhanced:
                enhanced[qid] = True
    
    return enhanced


# ============================================================================
# DEMO
# ============================================================================

def demo():
    print("=" * 60)
    print("UNIFIED INFERENCE AGENT")
    print("Kernel + Evolution + Memory + Registry")
    print("=" * 60)
    
    test_cases = [
        "a recipe collection app with ingredients and ratings",
        "expense tracker with budget charts",
        "a fitness journal to log my workouts",
        "something to manage my bookmarks with tags",
        "a quantum physics simulation tool",  # Novel domain
        "grandma's secret pasta dishes",  # Implicit recipe
    ]
    
    agent = get_agent()
    
    for desc in test_cases:
        print(f"\n{'─' * 60}")
        print(explain_inference(desc))
    
    print("\n" + "=" * 60)
    print("Agent Status:")
    print(f"  Kernel: {'✓' if HAS_KERNEL else '✗'}")
    print(f"  Evolution: {'✓' if HAS_EVOLUTION else '✗'}")
    print(f"  Memory: {'✓' if HAS_MEMORY else '✗'}")
    print(f"  Registry: {'✓' if HAS_REGISTRY else '✗'}")
    print("=" * 60)


if __name__ == "__main__":
    demo()
