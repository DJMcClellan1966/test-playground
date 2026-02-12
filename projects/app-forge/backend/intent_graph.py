"""Intent Graph for App Forge.

A semantic network that mimics how LLMs understand relationships between concepts.
When a word is "activated" by user input, related concepts also activate through
spreading activation - similar to how attention works in transformers.

Key concepts:
- Nodes: Concepts (words, ideas, features)
- Edges: Weighted relationships between concepts
- Activation: How strongly a concept is triggered
- Spreading: Activation flows through edges to related concepts

Example flow:
  "different colored tiles" 
    → activates: [colored, tiles, different]
    → spreads to: [visual, ui_element, variety, distractor]
    → spreads to: [reaction_game, game_mechanic]
    → matches: reaction_game template

This is hand-coded "attention" - what LLMs learn automatically from data.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
import math


# =====================================================================
# Graph Structure
# =====================================================================

@dataclass
class ConceptNode:
    """A concept in the intent graph."""
    id: str                          # Unique identifier
    aliases: Set[str] = field(default_factory=set)  # Alternative words
    category: str = "general"        # Category for organization
    template_affinity: Dict[str, float] = field(default_factory=dict)  # template_id → weight


@dataclass  
class ConceptEdge:
    """A weighted relationship between concepts."""
    source: str          # Source concept ID
    target: str          # Target concept ID
    weight: float        # 0.0 - 1.0, how strongly related
    relation: str        # Type of relationship (is_a, has_a, implies, etc.)


class IntentGraph:
    """Semantic network for understanding user intent."""
    
    def __init__(self):
        self.nodes: Dict[str, ConceptNode] = {}
        self.edges: List[ConceptEdge] = []
        self.adjacency: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.alias_map: Dict[str, str] = {}  # alias → node_id
        
    def add_node(self, node: ConceptNode) -> None:
        """Add a concept node."""
        self.nodes[node.id] = node
        # Register aliases
        for alias in node.aliases:
            self.alias_map[alias.lower()] = node.id
        self.alias_map[node.id.lower()] = node.id
    
    def add_edge(self, source: str, target: str, weight: float = 0.5, 
                 relation: str = "related", bidirectional: bool = True) -> None:
        """Add a relationship between concepts."""
        self.edges.append(ConceptEdge(source, target, weight, relation))
        self.adjacency[source].append((target, weight))
        if bidirectional:
            self.adjacency[target].append((source, weight))
    
    def resolve_alias(self, word: str) -> Optional[str]:
        """Find the concept ID for a word (including aliases)."""
        return self.alias_map.get(word.lower())
    
    def activate(self, words: List[str], initial_activation: float = 1.0) -> Dict[str, float]:
        """Activate concepts from input words."""
        activation: Dict[str, float] = defaultdict(float)
        
        for word in words:
            word_lower = word.lower()
            # Direct match
            node_id = self.resolve_alias(word_lower)
            if node_id:
                activation[node_id] = max(activation[node_id], initial_activation)
            
            # Partial match (word is substring of alias or vice versa)
            for alias, nid in self.alias_map.items():
                if len(alias) >= 3 and len(word_lower) >= 3:
                    if alias in word_lower or word_lower in alias:
                        activation[nid] = max(activation[nid], initial_activation * 0.7)
        
        return dict(activation)
    
    def spread(self, activation: Dict[str, float], 
               decay: float = 0.6, 
               iterations: int = 3,
               threshold: float = 0.1) -> Dict[str, float]:
        """Spread activation through the graph.
        
        Args:
            activation: Initial activation levels
            decay: How much activation decreases per hop (0-1)
            iterations: How many hops to spread
            threshold: Minimum activation to keep spreading
        
        Returns:
            Final activation levels for all reached concepts
        """
        current = dict(activation)
        
        for _ in range(iterations):
            new_activation: Dict[str, float] = defaultdict(float)
            
            for node_id, level in current.items():
                if level < threshold:
                    continue
                    
                # Spread to neighbors
                for neighbor, edge_weight in self.adjacency.get(node_id, []):
                    spread_amount = level * decay * edge_weight
                    new_activation[neighbor] = max(
                        new_activation[neighbor], 
                        spread_amount
                    )
            
            # Merge new activation (keep max, don't accumulate)
            for node_id, level in new_activation.items():
                current[node_id] = max(current.get(node_id, 0), level)
        
        return current
    
    def get_template_scores(self, activation: Dict[str, float]) -> Dict[str, float]:
        """Convert concept activation to template scores."""
        template_scores: Dict[str, float] = defaultdict(float)
        
        for node_id, level in activation.items():
            node = self.nodes.get(node_id)
            if node and node.template_affinity:
                for template_id, affinity in node.template_affinity.items():
                    template_scores[template_id] += level * affinity
        
        return dict(template_scores)
    
    def understand(self, text: str) -> Dict[str, float]:
        """Full understanding pipeline: tokenize → activate → spread → score.
        
        Returns template scores based on semantic understanding.
        """
        # Simple tokenization
        words = [w.strip().lower() for w in text.split() if len(w.strip()) >= 2]
        
        # Activate from words
        initial = self.activate(words)
        
        # Spread through graph
        final = self.spread(initial)
        
        # Convert to template scores
        return self.get_template_scores(final)
    
    def explain(self, text: str) -> Dict[str, any]:
        """Detailed explanation of understanding process."""
        words = [w.strip().lower() for w in text.split() if len(w.strip()) >= 2]
        initial = self.activate(words)
        final = self.spread(initial)
        scores = self.get_template_scores(final)
        
        return {
            "input_words": words,
            "initial_activation": dict(sorted(initial.items(), key=lambda x: -x[1])[:10]),
            "spread_activation": dict(sorted(final.items(), key=lambda x: -x[1])[:15]),
            "template_scores": dict(sorted(scores.items(), key=lambda x: -x[1])[:5]),
        }


# =====================================================================
# Build the Intent Graph
# =====================================================================

def build_intent_graph() -> IntentGraph:
    """Construct the semantic network for app understanding."""
    g = IntentGraph()
    
    # =========== GAME CONCEPTS ===========
    
    # Core game types
    g.add_node(ConceptNode("game", {"gaming", "play", "playing"}, "game_type",
                           {"generic_game": 0.5}))
    g.add_node(ConceptNode("puzzle", {"puzzles", "brain", "teaser", "solve", "solving"}, "game_type",
                           {"sliding_puzzle": 0.6, "wordle": 0.4}))
    g.add_node(ConceptNode("reaction", {"reflex", "reflexes", "quick", "fast", "speed", "speedy", "rapid"}, "game_type",
                           {"reaction_game": 1.0}))
    g.add_node(ConceptNode("memory", {"memorize", "remember", "recall"}, "game_type",
                           {"memory_game": 1.0}))
    g.add_node(ConceptNode("matching", {"match", "pairs", "pair", "flip", "flipping"}, "game_type",
                           {"memory_game": 0.8}))
    g.add_node(ConceptNode("guessing", {"guess", "random"}, "game_type",
                           {"guess_game": 0.9}))
    g.add_node(ConceptNode("trivia", {"quiz", "questions", "answers", "flashcard", "flashcards"}, "game_type",
                           {"quiz": 1.0}))
    g.add_node(ConceptNode("word_game", {"word", "words", "letter", "letters", "spelling"}, "game_type",
                           {"wordle": 0.7, "hangman": 0.7}))
    
    # Specific games
    g.add_node(ConceptNode("tictactoe", {"tic-tac-toe", "tic tac toe", "noughts", "crosses", "xo"}, "specific_game",
                           {"tictactoe": 1.0}))
    g.add_node(ConceptNode("sliding", {"slide", "sliding", "15-puzzle", "shifting", "swap"}, "mechanic",
                           {"sliding_puzzle": 0.9}))
    g.add_node(ConceptNode("hangman", {"hangman", "word guess"}, "specific_game",
                           {"hangman": 1.0}))
    g.add_node(ConceptNode("wordle", {"wordle"}, "specific_game",
                           {"wordle": 1.0}))
    g.add_node(ConceptNode("minesweeper", {"minesweeper", "mines", "bomb", "bombs", "flags"}, "specific_game",
                           {"minesweeper": 1.0}))
    g.add_node(ConceptNode("snake", {"snake"}, "specific_game",
                           {"snake": 1.0}))
    
    # =========== UI/VISUAL CONCEPTS ===========
    
    g.add_node(ConceptNode("grid", {"board", "cells", "matrix", "table"}, "ui",
                           {"sliding_puzzle": 0.5, "tictactoe": 0.5, "memory_game": 0.4, "minesweeper": 0.5}))
    g.add_node(ConceptNode("tile", {"tiles", "square", "squares", "block", "blocks", "cell"}, "ui",
                           {"sliding_puzzle": 0.5, "reaction_game": 0.4, "memory_game": 0.4}))
    g.add_node(ConceptNode("card", {"cards"}, "ui",
                           {"memory_game": 0.6}))
    g.add_node(ConceptNode("visual", {"color", "colored", "colours", "colorful", "hue", "shade"}, "ui",
                           {"reaction_game": 0.5}))  # Colors often mean visual feedback
    g.add_node(ConceptNode("click", {"tap", "press", "hit", "touch", "clicking"}, "interaction",
                           {"reaction_game": 0.6}))
    g.add_node(ConceptNode("target", {"goal", "objective", "correct", "right"}, "mechanic",
                           {"reaction_game": 0.5}))
    g.add_node(ConceptNode("distractor", {"distraction", "decoy", "fake", "wrong", "incorrect", "different"}, "mechanic",
                           {"reaction_game": 0.8}))  # KEY: "different" → distractor
    
    # =========== TIMING CONCEPTS ===========
    
    g.add_node(ConceptNode("timer", {"time", "timing", "timed", "countdown", "stopwatch", "clock"}, "mechanic",
                           {"timer": 0.9, "reaction_game": 0.4}))
    g.add_node(ConceptNode("pomodoro", {"pomodoro", "work timer", "focus"}, "specific_app",
                           {"timer": 0.8}))
    
    # =========== DATA/CRUD CONCEPTS ===========
    
    g.add_node(ConceptNode("data_app", {"track", "tracking", "log", "logging", "manage", "managing"}, "app_type",
                           {"crud": 0.7}))
    g.add_node(ConceptNode("recipe", {"recipes", "cooking", "cook", "meal", "meals", "food", "ingredient", "ingredients"}, "domain",
                           {"crud": 0.9}))
    g.add_node(ConceptNode("task", {"tasks", "todo", "to-do", "todos", "chore", "chores"}, "domain",
                           {"crud": 0.9}))
    g.add_node(ConceptNode("note", {"notes", "memo", "memos", "jot", "journal"}, "domain",
                           {"crud": 0.8}))
    g.add_node(ConceptNode("habit", {"habits", "routine", "daily", "streak"}, "domain",
                           {"crud": 0.8}))
    g.add_node(ConceptNode("expense", {"expenses", "budget", "money", "spending", "finance"}, "domain",
                           {"crud": 0.8}))
    g.add_node(ConceptNode("inventory", {"inventory", "stock", "items", "catalog", "catalogue"}, "domain",
                           {"crud": 0.8}))
    g.add_node(ConceptNode("collection", {"collect", "collections", "library", "archive"}, "domain",
                           {"crud": 0.7}))
    g.add_node(ConceptNode("movie", {"movies", "film", "films", "watch", "watched"}, "domain",
                           {"crud": 0.7}))
    g.add_node(ConceptNode("book", {"books", "reading", "read"}, "domain",
                           {"crud": 0.7}))
    g.add_node(ConceptNode("contact", {"contacts", "people", "address", "phone"}, "domain",
                           {"crud": 0.8}))
    g.add_node(ConceptNode("event", {"events", "calendar", "schedule", "appointment"}, "domain",
                           {"crud": 0.8}))
    g.add_node(ConceptNode("workout", {"workouts", "exercise", "gym", "fitness"}, "domain",
                           {"crud": 0.8}))
    g.add_node(ConceptNode("grocery", {"groceries", "shopping", "shop"}, "domain",
                           {"crud": 0.8}))
    
    # =========== TOOL CONCEPTS ===========
    
    g.add_node(ConceptNode("calculator", {"calc", "calculate", "math", "arithmetic", "compute"}, "tool",
                           {"calculator": 1.0}))
    g.add_node(ConceptNode("converter", {"convert", "conversion", "unit", "units", "bmi", "temperature"}, "tool",
                           {"converter": 1.0}))
    g.add_node(ConceptNode("generator", {"generate", "random", "password", "dice"}, "tool",
                           {"generator": 0.8}))
    
    # =========== API CONCEPTS ===========
    
    g.add_node(ConceptNode("api", {"apis", "backend", "service", "webservice"}, "app_type",
                           {"rest_api": 0.9, "fastapi": 0.8}))
    g.add_node(ConceptNode("rest_api", {"rest", "restful", "http", "endpoint", "endpoints"}, "tech",
                           {"rest_api": 1.0, "fastapi": 0.8}))
    g.add_node(ConceptNode("graphql", {"graphql", "graph"}, "tech",
                           {"graphql_api": 1.0}))
    g.add_node(ConceptNode("webhook", {"webhook", "webhooks", "callback"}, "tech",
                           {"webhook_handler": 0.9}))
    g.add_node(ConceptNode("jwt", {"jwt", "token", "tokens", "bearer", "oauth"}, "feature",
                           {"jwt_api": 0.9}))
    
    # =========== FEATURE CONCEPTS ===========
    
    g.add_node(ConceptNode("difficulty", {"level", "levels", "hard", "easy", "harder", "easier", "challenge"}, "feature",
                           {"reaction_game": 0.3, "quiz": 0.3}))
    g.add_node(ConceptNode("score", {"scoring", "points", "high score", "leaderboard"}, "feature",
                           {"generic_game": 0.4, "reaction_game": 0.3}))
    g.add_node(ConceptNode("number", {"numbers", "numbered", "digit", "digits", "numeric"}, "feature",
                           {"sliding_puzzle": 0.5, "guess_game": 0.4}))
    g.add_node(ConceptNode("authentication", {"login", "auth", "user", "account", "password"}, "feature",
                           {}))  # Feature modifier, not template specific
    
    # =========== RELATIONSHIPS (EDGES) ===========
    
    # Game mechanics
    g.add_edge("game", "puzzle", 0.6)
    g.add_edge("game", "reaction", 0.6)
    g.add_edge("game", "memory", 0.6)
    g.add_edge("game", "guessing", 0.6)
    g.add_edge("game", "trivia", 0.5)
    g.add_edge("game", "grid", 0.5)
    g.add_edge("game", "score", 0.6)
    
    # Reaction game connections (KEY for "colored tiles")
    g.add_edge("reaction", "timer", 0.7)
    g.add_edge("reaction", "click", 0.8)
    g.add_edge("reaction", "target", 0.8)
    g.add_edge("reaction", "visual", 0.7)  # Reaction games often use visual cues
    g.add_edge("visual", "distractor", 0.7)  # Colors can indicate distractors
    g.add_edge("distractor", "reaction", 0.8)  # Distractors are a reaction game concept
    g.add_edge("tile", "visual", 0.6)  # Tiles can be colored
    g.add_edge("tile", "grid", 0.7)
    g.add_edge("tile", "click", 0.6)
    
    # Puzzle connections
    g.add_edge("puzzle", "sliding", 0.8)
    g.add_edge("puzzle", "grid", 0.6)
    g.add_edge("puzzle", "tile", 0.7)
    g.add_edge("sliding", "tile", 0.8)
    g.add_edge("sliding", "number", 0.6)
    
    # Memory game connections
    g.add_edge("memory", "matching", 0.9)
    g.add_edge("memory", "card", 0.8)
    g.add_edge("memory", "flip", 0.7)
    g.add_edge("matching", "card", 0.7)
    g.add_edge("matching", "tile", 0.5)
    
    # Word game connections
    g.add_edge("word_game", "wordle", 0.7)
    g.add_edge("word_game", "hangman", 0.7)
    g.add_edge("word_game", "guessing", 0.6)
    g.add_edge("guessing", "number", 0.5)
    
    # Trivia/Quiz connections
    g.add_edge("trivia", "difficulty", 0.5)
    g.add_edge("trivia", "score", 0.6)
    
    # Data app connections
    g.add_edge("data_app", "recipe", 0.7)
    g.add_edge("data_app", "task", 0.8)
    g.add_edge("data_app", "note", 0.7)
    g.add_edge("data_app", "habit", 0.7)
    g.add_edge("data_app", "expense", 0.7)
    g.add_edge("data_app", "inventory", 0.6)
    g.add_edge("data_app", "collection", 0.6)
    g.add_edge("recipe", "ingredient", 0.9)
    g.add_edge("recipe", "collection", 0.5)
    g.add_edge("task", "habit", 0.4)
    g.add_edge("collection", "movie", 0.6)
    g.add_edge("collection", "book", 0.6)
    
    # Tool connections
    g.add_edge("calculator", "number", 0.7)
    g.add_edge("converter", "number", 0.5)
    g.add_edge("generator", "random", 0.8)
    
    return g


# =====================================================================
# Global Instance
# =====================================================================

_intent_graph: Optional[IntentGraph] = None


def get_intent_graph() -> IntentGraph:
    """Get or create the global intent graph."""
    global _intent_graph
    if _intent_graph is None:
        _intent_graph = build_intent_graph()
    return _intent_graph


def intent_match(description: str) -> Dict[str, float]:
    """Get template scores from intent understanding."""
    return get_intent_graph().understand(description)


def intent_explain(description: str) -> Dict[str, any]:
    """Get detailed explanation of intent understanding."""
    return get_intent_graph().explain(description)


def reset_intent_graph() -> None:
    """Reset the global intent graph."""
    global _intent_graph
    _intent_graph = None


# =====================================================================
# Testing
# =====================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Intent Graph Test")
    print("=" * 60)
    
    g = get_intent_graph()
    print(f"\nGraph stats: {len(g.nodes)} nodes, {len(g.edges)} edges")
    
    # Test cases
    test_cases = [
        "reaction time game with different colored tiles",
        "quick reflex test",
        "sliding number puzzle",
        "memory matching card game",
        "recipe app with ingredients",
        "track my daily habits",
        "tic tac toe game",
        "unit converter",
    ]
    
    print("\n" + "=" * 60)
    for desc in test_cases:
        print(f"\n[{desc}]")
        explanation = intent_explain(desc)
        
        print(f"  Activated: {list(explanation['initial_activation'].keys())[:5]}")
        print(f"  Spread to: {list(explanation['spread_activation'].keys())[:8]}")
        print(f"  Template scores:")
        for tid, score in list(explanation['template_scores'].items())[:3]:
            print(f"    {tid}: {score:.2f}")
