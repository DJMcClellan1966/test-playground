"""
Imagination Module - Creative Template Synthesis

The hypothesis: Creativity comes not from finding the ONE template that fits,
but from the TENSION between multiple templates that partially fit.

Traditional approach:
    Description → Best Match → Single Template → Code

Imagination approach:
    Description → ALL Matches → Resonance Map → Tension Detection
                             → What DOESN'T fit is the creative signal
                             → Synthesize hybrid from contradictions

The key insight: When "recipe app with game scoring" doesn't perfectly fit
either recipe_app OR quiz_app, the MISMATCH itself suggests something new -
a gamified cooking challenge app that neither template alone would produce.

This is bisociation (Koestler): creativity at the intersection of 
incompatible frames of reference.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
import math

# Import our existing systems
try:
    from template_registry import TEMPLATE_REGISTRY, TemplateEntry, extract_features
    from template_evolution import TemplateEvolver, TemplateVector, ALL_FEATURES, FEATURE_INDEX
    HAS_SYSTEMS = True
    # Build a dict for easier access
    TEMPLATES = {t.id: t for t in TEMPLATE_REGISTRY}
except ImportError as e:
    print(f"Import error: {e}")
    HAS_SYSTEMS = False
    TEMPLATES = {}
    TEMPLATE_REGISTRY = []


# ============================================================================
# RESONANCE: How an idea "vibrates" against each template
# ============================================================================

@dataclass
class TemplateResonance:
    """How an idea resonates with a single template."""
    template_id: str
    
    # What matches (the comfortable fit)
    matching_features: Set[str] = field(default_factory=set)
    match_strength: float = 0.0
    
    # What DOESN'T match (the tension - the creative signal!)
    missing_features: Set[str] = field(default_factory=set)  # Template has, idea doesn't need
    extra_features: Set[str] = field(default_factory=set)     # Idea needs, template doesn't have
    tension_strength: float = 0.0
    
    # Combined resonance (match - tension, can be negative)
    resonance: float = 0.0
    
    def __repr__(self):
        return f"Resonance({self.template_id}: match={self.match_strength:.2f}, tension={self.tension_strength:.2f})"


@dataclass 
class CreativeTension:
    """The productive tensions between an idea and the template space."""
    
    # The original idea
    description: str
    detected_features: Dict[str, float] = field(default_factory=dict)
    
    # How it resonates with each template
    resonances: List[TemplateResonance] = field(default_factory=list)
    
    # The interesting bits - tensions that could be creative
    productive_tensions: List[Tuple[str, str, str]] = field(default_factory=list)
    # Format: (feature, "missing from template X", "but present in template Y")
    
    # Cross-template bridges - features that connect unlikely templates
    bridges: List[Tuple[str, str, str]] = field(default_factory=list)
    # Format: (template_a, template_b, bridging_feature)
    
    # The "shouldn't work but might" combinations
    unlikely_combinations: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================================
# THE IMAGINATION ENGINE
# ============================================================================

class Imagination:
    """
    The creative counterpart to the logical UnifiedAgent.
    
    While UnifiedAgent finds the BEST template, Imagination explores
    the SPACE of all templates and finds creative potential in:
    - Template combinations that seem incompatible
    - Features that appear in unexpected contexts
    - Gaps that suggest novel functionality
    
    This is the "voice" that talks to the agent about possibilities.
    """
    
    def __init__(self):
        self.evolver = None
        if HAS_SYSTEMS:
            self.evolver = TemplateEvolver(n_archetypes=6)
            self.evolver.load_seed_templates()
            self.evolver.fit()
    
    def explore(self, description: str) -> CreativeTension:
        """
        Main entry point: explore how an idea resonates with all templates.
        
        Returns a CreativeTension object containing:
        - How the idea fits each template
        - Where tensions exist
        - What creative possibilities emerge from those tensions
        """
        tension = CreativeTension(description=description)
        
        # Step 1: Detect features from description
        if HAS_SYSTEMS:
            # Use optimized extract_features
            tension.detected_features = extract_features(description)
        
        # Step 2: Calculate resonance with EVERY template (not just best)
        self._calculate_all_resonances(tension)
        
        # Step 3: Find productive tensions
        self._find_productive_tensions(tension)
        
        # Step 4: Find cross-template bridges
        self._find_bridges(tension)
        
        # Step 5: Generate unlikely combinations
        self._generate_unlikely_combinations(tension)
        
        return tension
    
    def _calculate_all_resonances(self, tension: CreativeTension):
        """Calculate how the idea resonates with every template."""
        
        idea_features = set(tension.detected_features.keys())
        
        for template_id, template in TEMPLATES.items():
            # TemplateEntry has tags, boosted, required, anti - combine them
            template_features = set(template.tags + template.boosted + template.required)
            template_anti = set(template.anti)
            
            resonance = TemplateResonance(template_id=template_id)
            
            # What matches
            resonance.matching_features = idea_features & template_features
            resonance.match_strength = len(resonance.matching_features) / max(len(idea_features), 1)
            
            # What doesn't match - THE CREATIVE SIGNALS
            resonance.missing_features = template_features - idea_features  # Template has extra
            resonance.extra_features = idea_features - template_features    # Idea needs more
            
            # Anti-features: idea has features the template explicitly rejects
            anti_match = idea_features & template_anti
            
            # Tension strength: how much doesn't fit (boosted by anti-matches)
            total_features = len(template_features | idea_features)
            mismatch = len(resonance.missing_features) + len(resonance.extra_features) + len(anti_match) * 2
            resonance.tension_strength = mismatch / max(total_features, 1)
            
            # Combined resonance (can be negative if more tension than match)
            resonance.resonance = resonance.match_strength - (resonance.tension_strength * 0.5)
            
            tension.resonances.append(resonance)
        
        # Sort by resonance (but keep all - even negatives are interesting!)
        tension.resonances.sort(key=lambda r: r.resonance, reverse=True)
    
    def _find_productive_tensions(self, tension: CreativeTension):
        """
        Find tensions that could be productive.
        
        A productive tension is when:
        - Feature is extra in one template (doesn't fit)
        - But matches in another template (does fit there)
        
        This suggests the idea SPANS multiple template categories.
        """
        # Get all extra features across all resonances
        extras: Dict[str, List[str]] = {}  # feature -> [templates where it doesn't fit]
        matches: Dict[str, List[str]] = {}  # feature -> [templates where it fits]
        
        for res in tension.resonances:
            for feat in res.extra_features:
                extras.setdefault(feat, []).append(res.template_id)
            for feat in res.matching_features:
                matches.setdefault(feat, []).append(res.template_id)
        
        # Find features that are extra somewhere but match elsewhere
        for feat, extra_in in extras.items():
            if feat in matches:
                match_in = matches[feat]
                # This feature creates tension - it fits some templates but not others
                tension.productive_tensions.append((
                    feat,
                    f"missing from: {', '.join(extra_in[:2])}",
                    f"but present in: {', '.join(match_in[:2])}"
                ))
    
    def _find_bridges(self, tension: CreativeTension):
        """
        Find features that could bridge unlikely template combinations.
        
        A bridge is a feature that:
        - Appears in two templates that don't normally go together
        - Could allow cross-pollination of ideas
        """
        # Helper to get all features from a TemplateEntry
        def get_template_feats(t):
            return set(t.tags + t.boosted + t.required)
        
        # Build feature -> templates map
        feature_to_templates: Dict[str, Set[str]] = {}
        for template_id, template in TEMPLATES.items():
            for feat in get_template_feats(template):
                feature_to_templates.setdefault(feat, set()).add(template_id)
        
        # Find features shared by "distant" templates
        # Distance = low co-occurrence in other features
        idea_features = set(tension.detected_features.keys())
        
        for feat in idea_features:
            if feat not in feature_to_templates:
                continue
            templates_with_feat = list(feature_to_templates[feat])
            
            # Check pairs of templates that share this feature
            for i, t1 in enumerate(templates_with_feat):
                for t2 in templates_with_feat[i+1:]:
                    # How different are these templates?
                    t1_feats = get_template_feats(TEMPLATES[t1]) if t1 in TEMPLATES else set()
                    t2_feats = get_template_feats(TEMPLATES[t2]) if t2 in TEMPLATES else set()
                    
                    overlap = len(t1_feats & t2_feats)
                    union = len(t1_feats | t2_feats)
                    
                    if union > 0:
                        similarity = overlap / union
                        # Low similarity = distant templates = interesting bridge!
                        if similarity < 0.3:
                            tension.bridges.append((t1, t2, feat))
    
    def _generate_unlikely_combinations(self, tension: CreativeTension):
        """
        Generate "shouldn't work but might" combinations.
        
        These are hybrid templates that combine:
        - Features from the top matching template
        - Features from templates where we have tension
        - The bridging features that connect them
        """
        if len(tension.resonances) < 2:
            return
        
        best = tension.resonances[0]
        
        # Find templates with high tension but some match
        for res in tension.resonances[1:6]:  # Top 6
            if res.tension_strength > 0.3 and res.match_strength > 0.2:
                # This template has significant tension - interesting!
                combination = {
                    "primary": best.template_id,
                    "secondary": res.template_id,
                    "borrowed_features": list(res.matching_features - best.matching_features),
                    "tension_features": list(res.extra_features),
                    "rationale": f"Combine {best.template_id}'s structure with {res.template_id}'s {', '.join(list(res.matching_features)[:2])}",
                    "risk_level": "medium" if res.tension_strength < 0.5 else "high",
                    "creative_potential": min(res.tension_strength + res.match_strength, 1.0)
                }
                
                # Higher creative potential for higher tension + decent match
                if combination["creative_potential"] > 0.4:
                    tension.unlikely_combinations.append(combination)
        
        # Sort by creative potential
        tension.unlikely_combinations.sort(
            key=lambda x: x["creative_potential"], 
            reverse=True
        )


# ============================================================================
# THE DIALOGUE: Imagination talking to the Agent
# ============================================================================

@dataclass
class CreativeDialogue:
    """
    A structured dialogue between Imagination and the logical Agent.
    
    This represents the "conversation" about possibilities.
    """
    description: str
    
    # Imagination's exploration
    exploration: Optional[CreativeTension] = None
    
    # The dialogue steps
    observations: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Final synthesis
    hybrid_proposal: Optional[Dict[str, Any]] = None


class ImaginativeDialogue:
    """
    Facilitates dialogue between Imagination and the logical agent.
    
    The key insight: Instead of just returning "best template", 
    we return a conversation about possibilities.
    """
    
    def __init__(self):
        self.imagination = Imagination()
    
    def converse(self, description: str) -> CreativeDialogue:
        """
        Generate a creative dialogue about the app idea.
        
        This is NOT about finding the answer - it's about
        exploring the space of possibilities.
        """
        dialogue = CreativeDialogue(description=description)
        
        # Let imagination explore
        dialogue.exploration = self.imagination.explore(description)
        
        # Generate observations (what imagination notices)
        self._generate_observations(dialogue)
        
        # Generate questions (what's interesting to explore)
        self._generate_questions(dialogue)
        
        # Generate suggestions (creative possibilities)
        self._generate_suggestions(dialogue)
        
        # Synthesize a hybrid proposal
        self._synthesize_proposal(dialogue)
        
        return dialogue
    
    def _generate_observations(self, dialogue: CreativeDialogue):
        """What does Imagination notice about this idea?"""
        exp = dialogue.exploration
        
        # How many templates resonate?
        resonating = [r for r in exp.resonances if r.resonance > 0]
        dialogue.observations.append(
            f"This idea resonates with {len(resonating)} templates, "
            f"strongest: {resonating[0].template_id if resonating else 'none'}"
        )
        
        # Is there creative tension?
        if exp.productive_tensions:
            dialogue.observations.append(
                f"Interesting tension: {len(exp.productive_tensions)} features "
                "fit some templates but not others"
            )
        
        # Are there bridges?
        if exp.bridges:
            dialogue.observations.append(
                f"Found {len(exp.bridges)} bridges connecting distant template types"
            )
        
        # What features are unexpected?
        top_res = exp.resonances[0] if exp.resonances else None
        if top_res and top_res.extra_features:
            dialogue.observations.append(
                f"The idea wants: {', '.join(list(top_res.extra_features)[:3])} - "
                f"not typical for {top_res.template_id}"
            )
    
    def _generate_questions(self, dialogue: CreativeDialogue):
        """What questions arise from the tensions?"""
        exp = dialogue.exploration
        
        # Question about bridges
        for t1, t2, feat in exp.bridges[:2]:
            dialogue.questions.append(
                f"What if we combined {t1}'s approach with {t2}'s {feat}?"
            )
        
        # Questions about tensions
        for feat, missing, present in exp.productive_tensions[:2]:
            dialogue.questions.append(
                f"The '{feat}' feature is {missing} - should we break that expectation?"
            )
        
        # Questions about unlikely combinations
        for combo in exp.unlikely_combinations[:1]:
            dialogue.questions.append(
                f"Risk level '{combo['risk_level']}': What if this is actually "
                f"a {combo['primary']}-{combo['secondary']} hybrid?"
            )
    
    def _generate_suggestions(self, dialogue: CreativeDialogue):
        """Creative suggestions from the exploration."""
        exp = dialogue.exploration
        
        if exp.unlikely_combinations:
            combo = exp.unlikely_combinations[0]
            dialogue.suggestions.append(
                f"Try: Start with {combo['primary']} template, "
                f"but add {', '.join(combo['borrowed_features'][:2])} from {combo['secondary']}"
            )
        
        # Suggest based on tensions
        for feat, missing, present in exp.productive_tensions[:1]:
            dialogue.suggestions.append(
                f"Consider: Add '{feat}' even though it's unconventional here"
            )
        
        # Suggest based on bridges
        for t1, t2, feat in exp.bridges[:1]:
            dialogue.suggestions.append(
                f"Experiment: The '{feat}' feature suggests this could be a new "
                f"category between {t1} and {t2}"
            )
    
    def _synthesize_proposal(self, dialogue: CreativeDialogue):
        """Create a hybrid template proposal."""
        exp = dialogue.exploration
        
        if not exp.resonances:
            return
        
        best = exp.resonances[0]
        
        # Gather features from multiple sources
        hybrid_features = dict(exp.detected_features)
        
        # Add features from unlikely combinations
        for combo in exp.unlikely_combinations[:2]:
            for feat in combo.get("borrowed_features", [])[:2]:
                hybrid_features[feat] = 0.6  # Medium confidence for borrowed
        
        # Add features from tensions (the "shouldn't work" features)
        for res in exp.resonances[1:3]:
            for feat in res.matching_features:
                if feat not in hybrid_features:
                    hybrid_features[feat] = 0.4  # Lower confidence for tension-sourced
        
        dialogue.hybrid_proposal = {
            "base_template": best.template_id,
            "confidence_in_base": best.match_strength,
            "borrowed_from": [r.template_id for r in exp.resonances[1:3]],
            "hybrid_features": hybrid_features,
            "creative_risk": "low" if not exp.unlikely_combinations else 
                            exp.unlikely_combinations[0]["risk_level"],
            "rationale": (
                f"Start with {best.template_id} (matches {len(best.matching_features)} features), "
                f"augment with elements from {len(exp.resonances)-1} other templates "
                f"based on {len(exp.productive_tensions)} productive tensions"
            )
        }


# ============================================================================
# DEMO / TEST
# ============================================================================

def demo_imagination():
    """Demonstrate the Imagination system."""
    
    dialogue = ImaginativeDialogue()
    
    test_ideas = [
        "recipe app with game scoring and leaderboards",
        "expense tracker that gamifies saving money",
        "todo list with social sharing and competitions",
        "meditation app with data visualization",
        "code snippet manager with flashcard-style review",
    ]
    
    print("=" * 70)
    print("IMAGINATION MODULE: Exploring Creative Tensions")
    print("=" * 70)
    
    for idea in test_ideas:
        print(f"\n{'='*70}")
        print(f"IDEA: {idea}")
        print("=" * 70)
        
        convo = dialogue.converse(idea)
        
        print("\n📡 OBSERVATIONS:")
        for obs in convo.observations:
            print(f"  • {obs}")
        
        print("\n❓ QUESTIONS (Creative Tensions):")
        for q in convo.questions:
            print(f"  • {q}")
        
        print("\n💡 SUGGESTIONS:")
        for s in convo.suggestions:
            print(f"  • {s}")
        
        if convo.hybrid_proposal:
            print("\n🧬 HYBRID PROPOSAL:")
            hp = convo.hybrid_proposal
            print(f"  Base: {hp['base_template']} ({hp['confidence_in_base']:.0%} match)")
            print(f"  Borrows from: {', '.join(hp['borrowed_from'])}")
            print(f"  Risk level: {hp['creative_risk']}")
            print(f"  Features: {len(hp['hybrid_features'])}")
            print(f"  Rationale: {hp['rationale']}")


if __name__ == "__main__":
    demo_imagination()


# ============================================================================
# THE FAILURE MEMORY: Learning from what DOESN'T work
# ============================================================================

@dataclass
class CreativeFailure:
    """
    A record of a creative tension that was explored.
    
    The key insight: We learn as much (or more) from failures as successes.
    LLMs optimize for "least resistance" patterns - the safe paths.
    But creativity often comes from the WRONG paths that accidentally work.
    """
    description: str
    attempted_hybrid: Dict[str, Any]
    
    # What didn't work
    incompatible_features: Set[str] = field(default_factory=set)
    why_failed: str = ""
    
    # But what was interesting about the failure?
    unexpected_synergies: List[str] = field(default_factory=list)
    # e.g., "combining timer with recipe created a cooking challenge concept"
    
    # The "shouldn't work but did" discoveries
    productive_accidents: List[str] = field(default_factory=list)


class FailureMemory:
    """
    Memory of creative explorations - especially the failures.
    
    Unlike typical ML which optimizes for success, this system
    specifically tracks and learns from:
    - Template combinations that seemed wrong
    - Features that clashed unexpectedly  
    - Accidents that produced novel results
    
    The hypothesis: Over time, this builds a map of "creative edges" -
    the boundaries where standard templates break down and new
    categories emerge.
    """
    
    def __init__(self):
        self.failures: List[CreativeFailure] = []
        self.synergy_map: Dict[Tuple[str, str], float] = {}  # (feat1, feat2) -> synergy score
        self.accident_patterns: Dict[str, List[str]] = {}  # feature -> [unexpected applications]
    
    def record_exploration(self, 
                           description: str,
                           hybrid: Dict[str, Any],
                           worked: bool,
                           notes: str = ""):
        """
        Record the result of a creative exploration.
        
        worked=False is just as valuable as worked=True.
        """
        failure = CreativeFailure(
            description=description,
            attempted_hybrid=hybrid
        )
        
        if not worked:
            failure.why_failed = notes
            # Extract which feature combinations clashed
            features = list(hybrid.get('hybrid_features', {}).keys())
            for i, f1 in enumerate(features):
                for f2 in features[i+1:]:
                    # Lower synergy score for failed combinations
                    key = tuple(sorted([f1, f2]))
                    current = self.synergy_map.get(key, 0.5)
                    self.synergy_map[key] = current * 0.8  # Decay
        else:
            # It worked! Record the synergies
            features = list(hybrid.get('hybrid_features', {}).keys())
            for i, f1 in enumerate(features):
                for f2 in features[i+1:]:
                    key = tuple(sorted([f1, f2]))
                    current = self.synergy_map.get(key, 0.5)
                    self.synergy_map[key] = min(current * 1.2, 1.0)  # Boost
            
            # Check if this was an "accident" - unlikely combination that worked
            base = hybrid.get('base_template', '')
            borrowed = hybrid.get('borrowed_from', [])
            if borrowed:
                accident_note = f"{base} + {borrowed[0]} worked for '{description}'"
                self.accident_patterns.setdefault(base, []).append(accident_note)
        
        self.failures.append(failure)
    
    def suggest_from_failures(self, features: Set[str]) -> List[str]:
        """
        Given a set of features, suggest creative directions
        based on learned failure patterns.
        """
        suggestions = []
        
        # High-synergy combinations we've discovered
        for (f1, f2), synergy in sorted(self.synergy_map.items(), 
                                         key=lambda x: x[1], reverse=True)[:5]:
            if f1 in features or f2 in features:
                if synergy > 0.7:
                    other = f2 if f1 in features else f1
                    suggestions.append(
                        f"Try adding '{other}' - high synergy ({synergy:.0%}) observed"
                    )
        
        # Anti-suggestions: combinations that failed
        for (f1, f2), synergy in sorted(self.synergy_map.items(), 
                                         key=lambda x: x[1])[:3]:
            if f1 in features and f2 in features:
                if synergy < 0.3:
                    suggestions.append(
                        f"Warning: '{f1}' + '{f2}' has low synergy ({synergy:.0%})"
                    )
        
        return suggestions


# ============================================================================
# IMAGINATION + DIALOGUE + FAILURE MEMORY = CREATIVE SYSTEM
# ============================================================================

class CreativeSystem:
    """
    The complete creative system:
    
    1. Imagination - explores tension space
    2. Dialogue - generates questions and suggestions
    3. Failure Memory - learns from attempts
    
    This is the "voice" that talks to the UnifiedAgent, providing
    a creative counterpoint to its logical template matching.
    
    The system embodies the idea that:
    - Creativity is NOT just finding the best pattern
    - Creativity is exploring the space BETWEEN patterns
    - We learn as much from failures as successes
    - The "wrong" combination sometimes reveals new categories
    """
    
    def __init__(self):
        self.imagination = Imagination()
        self.dialogue = ImaginativeDialogue()
        self.memory = FailureMemory()
    
    def explore_idea(self, description: str) -> Dict[str, Any]:
        """
        Full creative exploration of an app idea.
        
        Returns a rich structure with:
        - Standard template match
        - Creative tensions found
        - Hybrid possibilities
        - Suggestions from failure memory
        - Questions for the user
        """
        # Get creative dialogue
        convo = self.dialogue.converse(description)
        
        # Enhance with failure memory suggestions
        detected = set(convo.exploration.detected_features.keys())
        memory_suggestions = self.memory.suggest_from_failures(detected)
        
        return {
            "description": description,
            "exploration": {
                "templates_resonated": len([r for r in convo.exploration.resonances if r.resonance > 0]),
                "tensions_found": len(convo.exploration.productive_tensions),
                "bridges_found": len(convo.exploration.bridges),
            },
            "observations": convo.observations,
            "questions": convo.questions,
            "suggestions": convo.suggestions + memory_suggestions,
            "hybrid_proposal": convo.hybrid_proposal,
            "memory_insights": memory_suggestions,
        }
    
    def record_outcome(self, description: str, hybrid: Dict[str, Any], 
                       worked: bool, notes: str = ""):
        """Record whether a creative exploration worked."""
        self.memory.record_exploration(description, hybrid, worked, notes)
    
    def get_creative_edges(self) -> Dict[str, Any]:
        """
        Return the "creative edges" discovered so far.
        
        These are the boundaries where templates break down
        and new categories might emerge.
        """
        # Find feature pairs with extreme synergy scores
        high_synergy = [(k, v) for k, v in self.memory.synergy_map.items() if v > 0.8]
        low_synergy = [(k, v) for k, v in self.memory.synergy_map.items() if v < 0.3]
        
        return {
            "total_explorations": len(self.memory.failures),
            "high_synergy_pairs": high_synergy,
            "low_synergy_pairs": low_synergy,
            "accident_patterns": self.memory.accident_patterns,
        }


# Create a global instance
creative_system = CreativeSystem()


def demo_creative_system():
    """Demonstrate the full creative system with failure learning."""
    
    print("\n" + "=" * 70)
    print("CREATIVE SYSTEM DEMO: Learning from Tensions & Failures")
    print("=" * 70)
    
    # Simulate a series of creative explorations
    explorations = [
        ("recipe app with game scoring", True, "gamified cooking works!"),
        ("expense tracker with puzzle elements", False, "puzzle + finance confused users"),
        ("todo list with drawing canvas", False, "visual todos too complex"),
        ("flashcard quiz with recipe database", True, "cooking flashcards popular!"),
        ("timer with social sharing", True, "productivity sharing works"),
        ("meditation app with game scoring", False, "gamification conflicts with calm"),
    ]
    
    print("\n📚 SIMULATING PAST EXPLORATIONS:")
    print("-" * 50)
    
    for desc, worked, notes in explorations:
        # Explore the idea
        result = creative_system.explore_idea(desc)
        hybrid = result.get('hybrid_proposal', {})
        
        # Record outcome
        creative_system.record_outcome(desc, hybrid, worked, notes)
        
        status = "✅" if worked else "❌"
        print(f"  {status} {desc}")
        print(f"      → {notes}")
    
    # Now show what the system has learned
    print("\n🧠 LEARNED CREATIVE EDGES:")
    print("-" * 50)
    
    edges = creative_system.get_creative_edges()
    print(f"  Total explorations: {edges['total_explorations']}")
    
    if edges['high_synergy_pairs']:
        print("\n  📈 High synergy combinations:")
        for (f1, f2), score in edges['high_synergy_pairs'][:5]:
            print(f"      {f1} + {f2} = {score:.0%}")
    
    if edges['low_synergy_pairs']:
        print("\n  📉 Low synergy (avoid or experiment?):")
        for (f1, f2), score in edges['low_synergy_pairs'][:5]:
            print(f"      {f1} + {f2} = {score:.0%}")
    
    if edges['accident_patterns']:
        print("\n  🎲 Accidental discoveries:")
        for base, accidents in edges['accident_patterns'].items():
            for a in accidents[:2]:
                print(f"      {a}")
    
    # Now try a new idea with the learned memory
    print("\n\n🆕 NEW IDEA with learned memory:")
    print("-" * 50)
    
    new_idea = "cooking challenge app with timers and sharing"
    result = creative_system.explore_idea(new_idea)
    
    print(f"  Idea: {new_idea}")
    print(f"\n  📡 Observations:")
    for obs in result['observations'][:3]:
        print(f"      • {obs}")
    
    print(f"\n  💡 Suggestions (including memory insights):")
    for sug in result['suggestions'][:4]:
        print(f"      • {sug}")
    
    if result['memory_insights']:
        print(f"\n  🧠 From failure memory:")
        for insight in result['memory_insights']:
            print(f"      • {insight}")


if __name__ == "__main__":
    demo_imagination()
    print("\n" + "=" * 70)
    demo_creative_system()
