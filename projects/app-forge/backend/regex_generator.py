"""
Auto-generate regex patterns for semantic routing from template metadata.

This module:
1. Extracts tags, names, and IDs from TEMPLATE_REGISTRY
2. Generates regex patterns with space-tolerance and word boundaries
3. Expands synonyms using a built-in thesaurus
4. Learns from build history (accepted prompts → patterns)
5. Detects routing gaps and suggests new patterns
"""
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict


# ============================================================================
# Synonym Expansion Dictionary
# ============================================================================

SYNONYMS: Dict[str, List[str]] = {
    # Games
    "game": ["app", "play", "fun"],
    "puzzle": ["brain teaser", "challenge"],
    "quiz": ["trivia", "questions", "test your knowledge"],
    "memory": ["match", "pairs", "concentration", "flip"],
    "snake": ["worm", "eat and grow"],
    "tetris": ["falling blocks", "stack blocks", "block fall"],
    "pong": ["paddle", "ball bounce", "table tennis"],
    
    # Data apps
    "todo": ["task", "checklist", "to-do"],
    "recipe": ["cooking", "ingredients", "meal", "dish", "food"],
    "note": ["memo", "jot", "write down"],
    "journal": ["diary", "daily log", "log entries"],
    "expense": ["budget", "spending", "money track", "finance"],
    "contact": ["address book", "phone book", "people"],
    "bookmark": ["save link", "favorite", "saved url"],
    "inventory": ["stock", "warehouse", "items"],
    
    # Utilities
    "timer": ["countdown", "stopwatch", "clock"],
    "calculator": ["math", "arithmetic", "compute"],
    "converter": ["unit", "transform", "change"],
    "weather": ["forecast", "temperature", "climate"],
    
    # Actions
    "create": ["make", "build", "add", "new"],
    "delete": ["remove", "trash", "destroy"],
    "edit": ["update", "modify", "change"],
    "save": ["store", "keep", "persist"],
    "search": ["find", "lookup", "query"],
    "track": ["monitor", "log", "record"],
    "manage": ["organize", "handle", "control"],
    
    # App types
    "app": ["application", "tool", "utility"],
    "dashboard": ["panel", "control center", "overview"],
    "editor": ["writer", "composer"],
    "viewer": ["browser", "reader"],
    "generator": ["creator", "maker", "builder"],
}


@dataclass
class GeneratedPattern:
    """A generated regex pattern with metadata."""
    template_id: str
    pattern: str
    source: str  # "tag", "name", "synonym", "learned"
    confidence: float  # How confident we are this is a good pattern


@dataclass 
class RoutingGap:
    """A detected routing gap."""
    prompt: str
    fell_to: str  # "neural", "nri", "keyword", "fallback"
    matched_template: str
    suggested_patterns: List[str]


class RegexPatternGenerator:
    """Generate regex patterns from template metadata."""
    
    def __init__(self, history_path: Optional[Path] = None):
        self.history_path = history_path or Path(__file__).parent / "data" / "learned_patterns.json"
        self.learned_patterns: Dict[str, List[Tuple[str, int]]] = {}  # template_id -> [(prompt, count)]
        self._load_history()
    
    def _load_history(self):
        """Load learned patterns from build history."""
        if self.history_path.exists():
            try:
                with open(self.history_path) as f:
                    self.learned_patterns = json.load(f)
            except:
                pass
    
    def _save_history(self):
        """Save learned patterns."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "w") as f:
            json.dump(self.learned_patterns, f, indent=2)
    
    def learn_from_prompt(self, prompt: str, template_id: str):
        """Learn a successful prompt → template mapping."""
        if template_id not in self.learned_patterns:
            self.learned_patterns[template_id] = []
        
        # Check if we already have this prompt
        for i, (p, count) in enumerate(self.learned_patterns[template_id]):
            if p.lower() == prompt.lower():
                self.learned_patterns[template_id][i] = (p, count + 1)
                self._save_history()
                return
        
        self.learned_patterns[template_id].append((prompt, 1))
        self._save_history()
    
    def _escape_for_regex(self, word: str) -> str:
        """Escape special regex characters."""
        return re.escape(word)
    
    def _add_space_tolerance(self, word: str) -> str:
        """Add optional space tolerance for compound words."""
        # Split camelCase and compound words
        if len(word) > 6 and '_' not in word and ' ' not in word:
            # Add optional space in middle of long words
            mid = len(word) // 2
            return f"{word[:mid]}\\s*{word[mid:]}"
        return word.replace(" ", "\\s+").replace("_", "[\\s_]*")
    
    def generate_pattern_from_tag(self, tag: str) -> str:
        """Generate a regex pattern from a single tag."""
        # Handle multi-word tags
        if "-" in tag:
            words = tag.split("-")
            return r"[\s\-]*".join(self._escape_for_regex(w) for w in words)
        if "_" in tag:
            words = tag.split("_")
            return r"[\s_]*".join(self._escape_for_regex(w) for w in words)
        
        # Add space tolerance for long words
        return self._add_space_tolerance(self._escape_for_regex(tag))
    
    def generate_patterns_from_template(self, template_id: str, name: str, 
                                         tags: List[str]) -> List[GeneratedPattern]:
        """Generate all patterns for a template."""
        patterns = []
        
        # 1. Pattern from ID
        id_pattern = self.generate_pattern_from_tag(template_id)
        patterns.append(GeneratedPattern(
            template_id=template_id,
            pattern=id_pattern,
            source="id",
            confidence=0.95
        ))
        
        # 2. Patterns from each tag
        for tag in tags:
            tag_pattern = self.generate_pattern_from_tag(tag)
            patterns.append(GeneratedPattern(
                template_id=template_id,
                pattern=tag_pattern,
                source="tag",
                confidence=0.85
            ))
            
            # 3. Expand synonyms for this tag
            if tag in SYNONYMS:
                for syn in SYNONYMS[tag]:
                    syn_pattern = self.generate_pattern_from_tag(syn)
                    patterns.append(GeneratedPattern(
                        template_id=template_id,
                        pattern=syn_pattern,
                        source="synonym",
                        confidence=0.75
                    ))
        
        # 4. Pattern from name (split into words)
        name_words = name.lower().replace("/", " ").split()
        for word in name_words:
            if len(word) > 3 and word not in ["game", "app", "the"]:
                word_pattern = self.generate_pattern_from_tag(word)
                patterns.append(GeneratedPattern(
                    template_id=template_id,
                    pattern=word_pattern,
                    source="name",
                    confidence=0.70
                ))
        
        # 5. Learned patterns from history
        if template_id in self.learned_patterns:
            for prompt, count in self.learned_patterns[template_id]:
                if count >= 2:  # Only use patterns seen 2+ times
                    # Extract key phrases from prompt
                    words = prompt.lower().split()
                    # Use 2-3 word ngrams
                    for n in [2, 3]:
                        for i in range(len(words) - n + 1):
                            ngram = " ".join(words[i:i+n])
                            if len(ngram) > 5:
                                ngram_pattern = self._add_space_tolerance(ngram)
                                patterns.append(GeneratedPattern(
                                    template_id=template_id,
                                    pattern=ngram_pattern,
                                    source="learned",
                                    confidence=min(0.60 + count * 0.05, 0.90)
                                ))
        
        return patterns
    
    def generate_all_patterns(self) -> Dict[str, List[GeneratedPattern]]:
        """Generate patterns for all templates in registry."""
        from template_registry import TEMPLATE_REGISTRY
        
        all_patterns: Dict[str, List[GeneratedPattern]] = {}
        
        for entry in TEMPLATE_REGISTRY:
            patterns = self.generate_patterns_from_template(
                entry.id, entry.name, entry.tags
            )
            all_patterns[entry.id] = patterns
        
        return all_patterns
    
    def to_semantic_routes_format(self) -> str:
        """Generate Python code for SEMANTIC_ROUTES."""
        all_patterns = self.generate_all_patterns()
        
        lines = ["# Auto-generated SEMANTIC_ROUTES from template metadata", 
                 "AUTO_SEMANTIC_ROUTES = ["]
        
        for template_id, patterns in sorted(all_patterns.items()):
            # Deduplicate and sort by confidence
            seen = set()
            unique_patterns = []
            for p in sorted(patterns, key=lambda x: -x.confidence):
                if p.pattern not in seen:
                    seen.add(p.pattern)
                    unique_patterns.append(p)
            
            # Take top 5 patterns per template
            top_patterns = unique_patterns[:5]
            if top_patterns:
                pattern_strs = [f'r"{p.pattern}"' for p in top_patterns]
                lines.append(f'    ("{template_id}", [{", ".join(pattern_strs)}]),')
        
        lines.append("]")
        return "\n".join(lines)
    
    def detect_gaps(self, test_prompts: List[str]) -> List[RoutingGap]:
        """Detect prompts that don't route via semantic matching."""
        from hybrid_router import route
        
        gaps = []
        for prompt in test_prompts:
            result = route(prompt)
            if result.method != "semantic":
                # Generate suggested patterns
                words = prompt.lower().split()
                suggestions = []
                
                # Suggest word patterns
                for word in words:
                    if len(word) > 3:
                        suggestions.append(f'r"{self._escape_for_regex(word)}"')
                
                # Suggest 2-word ngrams
                for i in range(len(words) - 1):
                    ngram = f"{words[i]}.*{words[i+1]}"
                    suggestions.append(f'r"{ngram}"')
                
                gaps.append(RoutingGap(
                    prompt=prompt,
                    fell_to=result.method,
                    matched_template=result.template_id,
                    suggested_patterns=suggestions[:5]
                ))
        
        return gaps
    
    def suggest_patterns_for_prompt(self, prompt: str, template_id: str) -> List[str]:
        """Suggest patterns that would match a prompt to a template."""
        words = prompt.lower().split()
        suggestions = []
        
        # 1. Individual significant words
        for word in words:
            if len(word) > 3 and word not in ["game", "app", "the", "with", "for", "and"]:
                suggestions.append(f'r"\\b{self._escape_for_regex(word)}\\b"')
        
        # 2. Two-word combinations
        for i in range(len(words) - 1):
            if len(words[i]) > 2 and len(words[i+1]) > 2:
                suggestions.append(f'r"{words[i]}\\s+{words[i+1]}"')
        
        # 3. Key phrase pattern
        key_words = [w for w in words if len(w) > 4][:3]
        if len(key_words) >= 2:
            suggestions.append(f'r"{key_words[0]}.*{key_words[1]}"')
        
        return suggestions


def generate_routes_report():
    """Generate a full report of patterns and gaps."""
    generator = RegexPatternGenerator()
    
    print("=" * 70)
    print("REGEX PATTERN GENERATOR REPORT")
    print("=" * 70)
    
    # Generate patterns
    all_patterns = generator.generate_all_patterns()
    
    print(f"\nTemplates analyzed: {len(all_patterns)}")
    print(f"Total patterns generated: {sum(len(p) for p in all_patterns.values())}")
    
    print("\n--- Patterns per template ---")
    for template_id, patterns in sorted(all_patterns.items()):
        print(f"\n{template_id}:")
        seen = set()
        for p in sorted(patterns, key=lambda x: -x.confidence)[:5]:
            if p.pattern not in seen:
                seen.add(p.pattern)
                print(f"  [{p.source:8}] {p.pattern} ({p.confidence:.0%})")
    
    # Test gap detection
    print("\n" + "=" * 70)
    print("GAP DETECTION TEST")
    print("=" * 70)
    
    test_prompts = [
        "make me a virtual pet app",
        "create a meditation timer",
        "build a habit tracking dashboard",
        "design a music playlist manager",
        "code a simple blog engine",
    ]
    
    gaps = generator.detect_gaps(test_prompts)
    
    if gaps:
        print(f"\nFound {len(gaps)} gaps:")
        for gap in gaps:
            print(f"\n  \"{gap.prompt}\"")
            print(f"    Fell to: {gap.fell_to} → {gap.matched_template}")
            print(f"    Suggestions: {gap.suggested_patterns[:3]}")
    else:
        print("\nNo gaps found - all prompts routed semantically!")
    
    # Output code
    print("\n" + "=" * 70)
    print("GENERATED SEMANTIC_ROUTES CODE (partial)")
    print("=" * 70)
    code = generator.to_semantic_routes_format()
    print(code[:1500] + "..." if len(code) > 1500 else code)


if __name__ == "__main__":
    generate_routes_report()
