"""
Optional AI-assist module for App Forge.
Uses NRI (Numerical Resonance Intelligence) from AI-Kernels-LLM for enhanced template matching.
This provides an alternative similarity engine when GloVe vectors don't find a match.

Import this module only when AI-enhanced matching is requested - keeps App Forge light.
"""
import math
from typing import Any, List, Dict, Tuple, Optional


class NumericalResonanceCore:
    """
    Prime-based encoding and harmonic similarity.
    Adapted from AI-Kernels-LLM for App Forge template matching.
    """

    def __init__(self):
        self.prime_cache = self._generate_primes(10000)
        self.golden_ratio = (1 + math.sqrt(5)) / 2

    def _generate_primes(self, n: int) -> List[int]:
        """Generate first n primes using Sieve of Eratosthenes."""
        if n < 2:
            return []
        size = max(n * 2, 100)
        sieve = [True] * size
        sieve[0] = sieve[1] = False
        for i in range(2, int(math.sqrt(size)) + 1):
            if sieve[i]:
                for j in range(i * i, size, i):
                    sieve[j] = False
        return [i for i, b in enumerate(sieve) if b][:n]

    def encode_to_primes(self, data: Any) -> List[int]:
        """Encode any data to a list of primes."""
        if isinstance(data, str):
            return [self.prime_cache[ord(c) % len(self.prime_cache)] for c in data]
        if isinstance(data, (int, float)):
            return [self.prime_cache[int(abs(data) * 1000) % len(self.prime_cache)]]
        if isinstance(data, (list, tuple)):
            out = []
            for x in data:
                out.extend(self.encode_to_primes(x))
            return out
        return [self.prime_cache[abs(hash(str(data))) % len(self.prime_cache)]]

    def compute_harmonic_signature(self, primes: List[int]) -> float:
        """Compute a harmonic signature from primes using golden ratio weighting."""
        if not primes:
            return 0.0
        s = 0.0
        for i, p in enumerate(primes):
            s += (self.golden_ratio ** -i) / (p + 1)
        n = len(primes)
        phi = self.golden_ratio
        fib_n = (phi**n - (-phi)**(-n)) / math.sqrt(5)
        return s / (1.0 + math.log(1 + abs(fib_n)))

    def compute_resonance(self, primes1: List[int], primes2: List[int]) -> float:
        """Compute similarity (resonance) between two prime encodings."""
        if not primes1 or not primes2:
            return 0.0
        a, b = set(primes1), set(primes2)
        inter, union = len(a & b), len(a | b)
        if not union:
            return 0.0
        base = inter / union
        h1 = self.compute_harmonic_signature(primes1)
        h2 = self.compute_harmonic_signature(primes2)
        sim = 1.0 / (1.0 + abs(h1 - h2))
        return (base * self.golden_ratio + sim) / (1 + self.golden_ratio)


# Template keywords for NRI matching (id → list of descriptive keywords)
NRI_TEMPLATE_KEYWORDS: Dict[str, str] = {
    "snake": "snake game eat food grow tail avoid walls speed arcade",
    "pong": "pong paddle ball bounce tennis arcade game two player",
    "flappy": "flappy bird tap fly jump avoid obstacles pipes",
    "tictactoe": "tic tac toe x o grid noughts crosses 3x3 two player",
    "connect_four": "connect four drop column 4 in a row checkers two player",
    "memory_game": "memory match pairs flip cards concentration matching",
    "wordle": "wordle guess word 5 letters daily word puzzle feedback colors",
    "hangman": "hangman guess letters hidden word spelling game",
    "minesweeper": "minesweeper mines bombs flags grid sweep puzzle",
    "sudoku": "sudoku 9x9 numbers puzzle grid constraints logic",
    "blackjack": "blackjack 21 cards hit stand dealer casino gambling",
    "cookie_clicker": "cookie clicker idle click increment counter game",
    "reaction_game": "reaction time test speed reflexes click fast",
    "guess_game": "guess number higher lower hot cold random",
    "tetris": "tetris falling blocks rotate stack clear lines",
    "breakout": "breakout bricks ball paddle arkanoid arcade",
    "platformer": "platformer jump run side scroller platform mario",
    "shooter": "shooter shoot enemies space invaders bullet arcade",
    "game_2048": "2048 slide merge tiles puzzle numbers power of two",
    "sliding_puzzle": "sliding puzzle 15 puzzle tile slide number grid",
    "jigsaw": "jigsaw puzzle image photo picture pieces assemble drag",
    "quiz": "quiz trivia questions answers multiple choice test",
    "typing_test": "typing test speed wpm words per minute keyboard",
    "rps": "rock paper scissors hand game chance rps",
    "coin_flip": "coin flip heads tails random chance flip",
    "dice_roller": "dice roll d6 d20 random number generator",
    "timer": "timer stopwatch countdown clock alarm pomodoro",
    "calculator": "calculator math arithmetic add subtract multiply divide",
    "converter": "converter unit celsius fahrenheit temperature currency",
    "crud": "crud create read update delete list manage data todo notes tasks",
    "kanban": "kanban board columns drag tasks workflow agile",
    "weather": "weather forecast temperature location rain sun",
    "markdown": "markdown editor preview text format wysiwyg",
    "pomodoro": "pomodoro timer focus work break productivity",
    "calendar": "calendar events schedule date planner appointments",
    "algorithm_visualizer": "algorithm visualizer sorting bubble quick merge animation step by step",
}


# Singleton NRI instance (lazy loaded)
_nri_instance: Optional[NumericalResonanceCore] = None


def get_nri() -> NumericalResonanceCore:
    """Get or create the NRI singleton."""
    global _nri_instance
    if _nri_instance is None:
        _nri_instance = NumericalResonanceCore()
    return _nri_instance


def nri_match_template(description: str, threshold: float = 0.35) -> Optional[Tuple[str, float]]:
    """
    Use NRI to find the best matching template for a description.
    Returns (template_id, confidence) or None if no match above threshold.
    """
    nri = get_nri()
    desc_primes = nri.encode_to_primes(description.lower())
    
    best_match: Optional[Tuple[str, float]] = None
    
    for template_id, keywords in NRI_TEMPLATE_KEYWORDS.items():
        keyword_primes = nri.encode_to_primes(keywords)
        resonance = nri.compute_resonance(desc_primes, keyword_primes)
        
        if resonance >= threshold:
            if best_match is None or resonance > best_match[1]:
                best_match = (template_id, resonance)
    
    return best_match


def ai_assist_suggestions(description: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Get top-k AI-assisted template suggestions with explanations.
    Returns list of {template_id, confidence, explanation}.
    """
    nri = get_nri()
    desc_primes = nri.encode_to_primes(description.lower())
    
    scores = []
    for template_id, keywords in NRI_TEMPLATE_KEYWORDS.items():
        keyword_primes = nri.encode_to_primes(keywords)
        resonance = nri.compute_resonance(desc_primes, keyword_primes)
        scores.append((template_id, resonance, keywords))
    
    # Sort by resonance descending
    scores.sort(key=lambda x: x[1], reverse=True)
    
    suggestions = []
    for template_id, confidence, keywords in scores[:top_k]:
        # Find overlapping words for explanation
        desc_words = set(description.lower().split())
        keyword_words = set(keywords.split())
        overlap = desc_words & keyword_words
        
        if overlap:
            explanation = f"Matches keywords: {', '.join(sorted(overlap)[:5])}"
        else:
            explanation = f"Similar concept (harmonic resonance: {confidence:.1%})"
        
        suggestions.append({
            "template_id": template_id,
            "confidence": round(confidence, 3),
            "explanation": explanation
        })
    
    return suggestions


def describe_capabilities() -> Dict[str, Any]:
    """Describe AI-assist capabilities for API response."""
    return {
        "enabled": True,
        "engine": "NRI (Numerical Resonance Intelligence)",
        "description": "Prime-based encoding with golden ratio harmonic similarity",
        "templates_indexed": len(NRI_TEMPLATE_KEYWORDS),
        "features": [
            "Enhanced template matching beyond keyword rules",
            "Harmonic similarity for fuzzy matching",
            "Top-k suggestions with explanations"
        ]
    }
