"""
Hybrid Router: Neural matching → Existing template generation

This is the "best of both worlds" approach:
- Stage 1: Fast semantic rules for common cases (0.1ms)
- Stage 2: GloVe neural similarity for edge cases (0.5ms)
- Stage 3: Routes to EXISTING hand-crafted templates (full control)

Result: Neural-level flexibility + Template-level control
"""

import re
from typing import Tuple, List, Optional
from dataclasses import dataclass

# Import existing matchers and generators
try:
    from glove_matcher import glove_match
    GLOVE_AVAILABLE = True
except ImportError:
    GLOVE_AVAILABLE = False

try:
    from template_registry import TEMPLATES
    TEMPLATES_AVAILABLE = True
except ImportError:
    TEMPLATES_AVAILABLE = False


# ========== SEMANTIC TRAPS (Prevent Wrong Routing) ==========

# Patterns that LOOK like games but are actually CRUD apps
# These take priority to prevent "snake oil" → snake game
SEMANTIC_TRAPS: List[Tuple[str, str]] = [
    # Business/productivity contexts with game words
    (r"\b(snake\s*oil|python\s*snake)\b", "crud"),  # Snake in non-game context
    (r"\b(breakout\s*session|breakout\s*room|breakout\s*group)\b", "crud"),  # Breakout meetings
    (r"\b(pong\s*meeting|pong\s*invite|pong\s*email)\b", "crud"),  # Ping-pong emails
    (r"\b2048[\s-]?(byte|kb|mb|gb|bit|file|size)\b", "crud"),  # 2048 as file size
    (r"\b(tetris\s*tournament|tetris\s*event|tetris\s*organiz)\b", "crud"),  # Organizing tetris events
    (r"\b(mario|kart)\s*(rental|business|shop)\b", "crud"),  # Mario kart rental
    (r"\bmemory\s*(manage|allocation|leak|usage|profil)\b", "crud"),  # Memory management
    (r"\bplatform\s*(for|to)\s*(shar|connect|build|launch)\b", "crud"),  # Platform as product
    
    # Tracking/organizing game-related things (not playing games)
    (r"\b(track|log|record|manag|organiz).*\b(game|match|score|tournament)\b", "crud"),
    (r"\b(game|match|score|tournament).*\b(track|log|record|manag|organiz)\b", "crud"),
    (r"\b(sighting|identification|species)\b", "crud"),  # Wildlife tracking
    
    # More semantic traps
    (r"\btrack\s+snake\b", "crud"),  # Track snake sightings
    (r"\bsnake\s+(sighting|track|identif|watch|spot)\b", "crud"),
    (r"\b(score|homework|assignment|grade)\b.*\b(track|manage|organiz)\b", "crud"),
    (r"\bwin\s+at\s+(organiz|manag|task)\b", "crud"),
    (r"\bgame\s*plan\b", "crud"),  # Game plan = strategy, not game
    
    # Misleading game words in productivity context
    (r"\bscore\s+(my|the|your)?\s*(homework|assignment|paper|essay|exam)", "crud"),
    (r"\b(play|playing)\s*around\s*with\s*(my|the)?\s*(recipe|data|file|code)", "crud"),
    (r"\blevel\s*up\s*(my|the|your)?\s*(skill|workout|routine|career)", "crud"),
    (r"\bwin\s*at\s*(organiz|manag|task|life|work)", "crud"),
    (r"\b(space\s*invader|costume|collect|tracker)\b", "crud"),  # Costume tracker
    (r"\bplatform\s+(for|to)\s+(shar|post|connect|discuss)", "crud"),  # Sharing platform != platformer
    
    # Common data/planning apps (not games)
    (r"\b(meal|menu)\s*(plan|schedul|organiz)", "crud"),  # Meal planner
    (r"\b(project|task|event)?\s*timeline\b", "crud"),  # Timeline/Gantt
    (r"\b(weekly|daily|monthly)\s*(plan|schedul|menu)", "crud"),  # Planning apps
]


# ========== WRONG DOMAIN DETECTION ==========

# Requests that are physically impossible or clearly non-software
WRONG_DOMAIN_PATTERNS = [
    r"\b(build|make|construct)\s+(me\s+)?(a\s+)?house\b",
    r"\b(make|cook|prepare)\s+(me\s+)?dinner\b",
    r"\b(fix|repair)\s+(my\s+)?car\b",
    r"\bfly\s+(me\s+)?to\b",
    r"\b(create|build|make)\s+(a\s+)?robot\b",
    r"\bdesign\s+(a\s+)?circuit\b",
    r"\b3d\s*print\b",
    r"\b(write|create|build)\s+(an?\s+)?operating\s*system\b",
    r"\bcompile\s+.*(kernel|linux)\b",
    r"\b(create|build)\s+(a\s+)?database\s*server\b",
]


def is_wrong_domain(description: str) -> bool:
    """Check if request is for something impossible (physical, hardware, etc)."""
    desc_lower = description.lower()
    for pattern in WRONG_DOMAIN_PATTERNS:
        if re.search(pattern, desc_lower):
            return True
    return False


# ========== AMBIGUOUS DETECTION ==========

# Very vague inputs that should go to generic_game
AMBIGUOUS_PATTERNS = [
    r"^(app|game|thing|stuff|something)$",
    r"^(build|make|create)\s+(me\s+)?(something|anything|stuff)$",
    r"^(surprise|whatever|idk|dunno)(\s+me)?$",
    r"^(whatever|any(thing)?)\s+works?$",
    r"^i\s*(don.?t|dont)\s*know\b",
    r"^(something|anything)\s+(fun|cool|nice|good)$",
    r"^idk\s+what\b",  # "idk what i want"
]

# Tech buzzwords that don't map to real apps - route to generic_game
BUZZWORD_PATTERNS = [
    r"\b(quantum|blockchain|nft|web3|metaverse|ai\s+synergy|decentralized)\b.*\b(app|system|platform)\b",
    r"\bflurble\b|\bwibble\b",  # Nonsense words
]


# ========== MULTI-LANGUAGE SUPPORT ==========

# Common app/game words in other languages -> English equivalent
MULTI_LANGUAGE_MAP: List[Tuple[str, str]] = [
    # Spanish
    (r"\bjuego\s*de\s*la\s*serpiente\b", "snake"),  # Snake game
    (r"\bcalculadora\b", "calculator"),
    (r"\btarea\b", "crud"),  # Todo/task
    (r"\blista\s*de\s*tareas\b", "crud"),  # Todo list
    (r"\bjuego\b", "generic_game"),  # Game
    
    # French
    (r"\bcalculatrice\b", "calculator"),
    (r"\bjeu\s*de\s*tetris\b", "tetris"),
    (r"\bjeu\s*de\s*serpent\b", "snake"),
    (r"\bjeu\b", "generic_game"),  # Game
    
    # German
    (r"\bschlangenspiel\b", "snake"),  # Snake game
    (r"\brechner\b", "calculator"),
    (r"\btaschenrechner\b", "calculator"),
    (r"\btodo\s*liste\b", "crud"),
    (r"\bspiel\b", "generic_game"),  # Game
    
    # Italian
    (r"\bcalcolatrice\b", "calculator"),
    (r"\bgioco\s*del\s*serpente\b", "snake"),
    
    # Portuguese
    (r"\bjogo\s*da\s*cobra\b", "snake"),
    (r"\bcalculadora\b", "calculator"),
    
    # Japanese (katakana/common)
    (r"ゲーム", "generic_game"),  # Game
    (r"計算機", "calculator"),
    
    # Russian
    (r"приложение", "generic_game"),  # Application
    (r"игра", "generic_game"),  # Game
    (r"калькулятор", "calculator"),
]


# ========== CONTRADICTION DETECTION ==========

# Patterns that indicate contradictory/confusing input
CONTRADICTION_PATTERNS = [
    r"\b(isn.?t|not|but\s*not|without)\s+(a\s+)?game\b",  # "game that isn't a game"
    r"\bgame\s+(but|that).*(isn.?t|not|never)\b",
    r"\b(simple|minimal)\s+.*(100|many|lots|complex)\b",  # "simple with 100 features"
    r"\bthat.?s\s+(really|actually)\s+a\s+\w+\b",  # "that's really a platformer"
    r"\b(but|yet|however)\s+(it.?s|is)\s+(really|actually)\b",
]


def is_contradiction(description: str) -> bool:
    """Check if the description contains contradictions."""
    desc_lower = description.lower()
    for pattern in CONTRADICTION_PATTERNS:
        if re.search(pattern, desc_lower):
            return True
    return False


def translate_multi_language(description: str) -> Optional[Tuple[str, float]]:
    """Try to match non-English game/app words."""
    desc_lower = description.lower()
    for pattern, template_id in MULTI_LANGUAGE_MAP:
        if re.search(pattern, desc_lower):
            return template_id, 0.85
    return None


# ========== PROMPT INJECTION DETECTION ==========

# Patterns that look like prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    r"^ignore\s+(previous|all)\s+instructions?",
    r"^system\s*:",
    r"^(forget|disregard|override)\s+(everything|all|templates?)",
    r"\{\{.*\}\}",  # Template injection
    r"```\s*(python|javascript|bash|sh)\b",  # Code blocks
    r"\$\{.*\}",  # Variable interpolation
    r"\bimport\s+(os|sys|subprocess)",  # Python imports
    r"\b(rm|del)\s+(-rf?|/[sf])?",  # Delete commands (with word boundary)
]


def is_prompt_injection(description: str) -> bool:
    """Detect potential prompt injection attempts."""
    desc_lower = description.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, desc_lower):
            return True
    return False


def is_ambiguous(description: str) -> bool:
    """Check if input is too vague to route meaningfully."""
    cleaned = description.lower().strip()
    # Very short single words
    if len(cleaned.split()) <= 2 and cleaned in ("app", "game", "thing", "stuff", "fun", "play"):
        return True
    for pattern in AMBIGUOUS_PATTERNS:
        if re.match(pattern, cleaned):
            return True
    return False


def is_buzzword_nonsense(description: str) -> bool:
    """Check if input is just tech buzzwords with no real meaning."""
    desc_lower = description.lower()
    for pattern in BUZZWORD_PATTERNS:
        if re.search(pattern, desc_lower):
            return True
    return False


def sanitize_input(description: str) -> str:
    """Clean up input by removing special characters that confuse routing."""
    # Remove URLs
    cleaned = re.sub(r'https?://[^\s]+', '', description)
    # Remove file paths (Windows and Unix)
    cleaned = re.sub(r'[A-Za-z]:\\[^\s]*', '', cleaned)
    cleaned = re.sub(r'/[a-z]+(/[a-z]+)+', '', cleaned, flags=re.IGNORECASE)
    # Remove quotes and brackets for cleaner matching
    cleaned = re.sub(r'[\'"\[\](){}]', ' ', cleaned)
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else description


def check_semantic_trap(description: str) -> Optional[str]:
    """Check if description matches a semantic trap (game words in non-game context)."""
    desc_lower = description.lower()
    for pattern, template_id in SEMANTIC_TRAPS:
        if re.search(pattern, desc_lower):
            return template_id
    return None


# ========== NONSENSE/EMPTY DETECTION ==========

# Known valid inputs that might look like nonsense (game names with numbers)
KNOWN_VALID_INPUTS = {"2048", "4096", "15 puzzle", "15-puzzle", "9x9", "d20", "d6"}


def is_nonsense_or_empty(description: str) -> bool:
    """Detect empty, whitespace-only, or nonsense input."""
    if not description or not description.strip():
        return True
    
    # Only whitespace/control characters
    cleaned = description.strip()
    if len(cleaned) < 2:
        return True
    
    # Check for known valid inputs first
    if cleaned.lower() in KNOWN_VALID_INPUTS:
        return False
    
    # Check if mostly non-alphabetic (emojis, symbols, numbers only)
    alpha_chars = sum(1 for c in cleaned if c.isalpha())
    if alpha_chars < 3 and len(cleaned) > 2:
        return True
    
    # Known gibberish patterns
    gibberish = [r"^[aeiou]+$", r"^asdf", r"^qwer", r"^zxcv", r"^[\W\d\s]+$"]
    for pattern in gibberish:
        if re.match(pattern, cleaned.lower()):
            return True
    
    return False


# ========== SEMANTIC RULES (Fast, High Confidence) ==========

# Maps regex patterns directly to template IDs (not archetypes)
SEMANTIC_ROUTES: List[Tuple[str, List[str]]] = [
    # Games - use EXACT template IDs from TEMPLATE_REGISTRY
    ("snake", [r"snake", r"eat.*grow", r"tail.*follow"]),
    ("pong", [r"pong", r"paddle.*ball", r"ball.*paddle", r"bounce.*sides"]),
    ("flappy", [r"flappy", r"tap.*fly|fly.*tap", r"avoid.*pipes?|pipes?.*avoid"]),
    ("tictactoe", [r"tic\s*tac", r"x.*o.*grid|noughts?\s*and\s*crosses"]),
    ("connect_four", [r"connect\s*(4|four)", r"4\s*in\s*a?\s*row|drop.*column"]),
    ("memory_game", [r"memory\s*(game|match)", r"matching\s*pairs?", r"flip.*find", r"concentration"]),
    ("wordle", [r"wordle", r"5\s*letter.*guess", r"daily\s*word", r"color.*feedback.*word", r"word.*color.*feedback", r"letter.*word.*color"]),
    ("hangman", [r"hangman", r"guess.*letter(?!.*color)|letter.*guess(?!.*color)", r"hidden\s*word(?!.*color)"]),
    ("minesweeper", [r"minesweeper", r"bomb.*grid|mine.*sweep", r"hidden.*flag"]),
    ("sudoku", [r"sudoku", r"9\s*x\s*9.*numbers?", r"fill.*grid.*constraint"]),
    ("blackjack", [r"blackjack|21|twenty.?one", r"hit.*stand", r"card.*dealer"]),
    ("cookie_clicker", [r"cookie\s*click|click.*cookie", r"idle.*click", r"click.*count"]),
    ("reaction_game", [r"reaction\s*time|reaction\s*test", r"click.*fast|reflex"]),
    ("guess_game", [r"guess.*number|number.*guess", r"higher.*lower", r"hot.*cold"]),
    ("tetris", [r"tetris", r"falling\s*blocks?", r"stack.*blocks?", r"rotate.*blocks"]),
    ("breakout", [r"breakout|arkanoid", r"brick.*ball", r"ball.*brick"]),
    ("platformer", [r"platformer", r"jump.*platform", r"side.?scrol"]),
    ("shooter", [r"shooter|shooting\s*game", r"shoot.*enemies?", r"space.*shoot"]),
    ("game_2048", [r"2048", r"slide.*merge|merge.*tiles?"]),
    ("sliding_puzzle", [r"sliding\s*puzzle|15.?puzzle|tile.*slide|number.*slide"]),
    ("jigsaw", [r"jigsaw", r"image.*puzzle|picture.*puzzle|photo.*puzzle", 
               r"(upload|take).*image.*(puzzle|pieces?)", r"pieces?.*together", 
               r"(split|cut|divide).*(image|picture|photo)", r"reassemble.*(image|picture|photo)"]),
    ("quiz", [r"quiz|trivia", r"multiple\s*choice|question.*answer"]),
    ("typing_test", [r"typing\s*test|typing\s*speed|type.*speed|wpm|words?\s*per\s*minute", r"speed\s*typing"]),
    ("rps", [r"rock.*paper|paper.*scissors|rps"]),
    ("coin_flip", [r"coin\s*flip|flip.*coin|heads.*tails"]),
    ("dice_roller", [r"dice\s*roll|roll.*dice|d20|d6"]),
    ("timer", [r"timer|stopwatch|countdown", r"multiple\s*events?", r"alarm|time.*track"]),
    ("calculator", [r"calculator|math|arithmetic"]),
    ("converter", [r"convert|celsius|fahrenheit|unit"]),
    ("algorithm_visualizer", [r"algorithm\s*visual", r"sorting\s*visual", r"bubble\s*sort|quick\s*sort|merge\s*sort",
                              r"visualize\s*(algorithm|sorting)", r"algorithm\s*animation", r"sort.*step.*by.*step",
                              r"visual.*sorting|sorting.*visual", r"interactive\s*visual.*algorithm"]),
    
    # Well-known game aliases (neural-like matching via explicit patterns)
    ("snake", [r"pac.?man|pacman", r"eat.*dots?.*avoid", r"maze.*collect", r"eat.*dots", r"collect.*dots"]),
    ("flappy", [r"doodle\s*jump", r"infinite.*runner"]),
    ("memory_game", [r"simon\s*says|simon", r"pattern\s*memory", r"repeat.*sequence"]),
    ("minesweeper", [r"battleship", r"grid.*guess|guess.*grid"]),
    
    # Utility apps (before CRUD to catch specific patterns)
    ("timer", [r"pomodoro", r"focus\s*timer|work\s*timer", r"25\s*min|tomato\s*timer"]),
    ("qr_generator", [r"qr\s*(code|generator)", r"barcode\s*generator", r"generate\s*qr"]),
    ("markdown_editor", [r"text\s*editor|code\s*editor|notepad", r"plain\s*text|rich\s*text"]),
    ("crud", [r"weather", r"forecast|temperature|rain\s*(today|tomorrow)"]),
    ("crud", [r"markdown\s*editor|markdown\s*preview", r"md\s*editor|wysiwyg"]),
    ("crud", [r"kanban", r"board.*column|column.*card|drag.*column|trello"]),
    ("crud", [r"calendar|schedule|event.*date|appointment"]),
    
    # Data apps / CRUD - expanded patterns
    ("crud", [r"todo|task\s*list|checklist", r"note.*app|notes?(?!\s*and)|memo"]),
    ("crud", [r"recipe|cooking|ingredients?"]),
    ("crud", [r"inventory|stock|warehouse"]),
    ("crud", [r"expense|budget|spending|finance\s*track"]),
    ("crud", [r"bookmark|links?(?!\s*page)|urls?"]),
    ("crud", [r"contact|address\s*book|phone\s*book"]),
    ("crud", [r"journal|diary|daily\s*log"]),
    # Web services / utilities → CRUD
    ("crud", [r"scraper|web\s*scrap|extract.*data.*website", r"file\s*upload|upload.*service|image\s*preview"]),
    ("crud", [r"card\s*grid|grid\s*layout|hover\s*effect", r"toggle\s*switch|dark\s*mode"]),
    # Learning/study apps → CRUD
    ("crud", [r"flashcard|flash\s*card|study\s*(app|cards?)", r"vocabulary|vocab\s*learn", r"spaced\s*repetition"]),
    # Watchlist/collection apps → CRUD  
    ("crud", [r"watchlist|watch\s*list|movie.*list|movie.*collection", r"reading\s*list|book.*list"]),
    ("crud", [r"playlist|music\s*collection|album.*list"]),
    # Reminder/tracking apps → CRUD
    ("crud", [r"reminder|water\s*track|habit\s*track|plant\s*water", r"workout.*log|exercise.*log|fitness.*track"]),
    # UI components that need CRUD (v0-style)
    ("crud", [r"landing\s*page|hero\s*section|pricing\s*table"]),
    ("crud", [r"dashboard|admin\s*panel|control\s*panel"]),
    ("crud", [r"login\s*form|signup\s*form|auth.*form|registration"]),
    ("crud", [r"modal|dialog|popup\s*form"]),
    ("crud", [r"gallery|image\s*gallery|photo\s*gallery|lightbox"]),
    ("crud", [r"navbar|navigation|sidebar"]),
    # Chat/messaging apps
    ("crud", [r"chat\s*app|chat.*websocket|messaging|instant\s*messag", r"realtime\s*chat|live\s*chat"]),
    # Generic data apps
    ("crud", [r"manager|tracker|list\s*app|collection\s*app", r"log\s*app|crud|database\s*app"]),
    # API/Backend patterns → CRUD
    ("crud", [r"rest\s*api|api.*crud|flask.*app|backend"]),
    ("crud", [r"blog|post.*comment|article"]),
    # Creative tools → CRUD
    ("crud", [r"color\s*palette|palette\s*generator", r"drawing\s*(app|canvas)|pixel\s*art"]),
    ("crud", [r"regex\s*test|code\s*test", r"periodic\s*table"]),
    ("crud", [r"piano|keyboard.*notes?|music.*play"]),
    # Password/generator tools → CRUD
    ("crud", [r"password\s*generat|random\s*generat", r"url\s*shorten"]),
]


def semantic_route(description: str) -> Optional[Tuple[str, float]]:
    """
    Try to match description to a template using fast regex rules.
    Returns (template_id, confidence) or None if no match.
    """
    desc_lower = description.lower()
    
    for template_id, patterns in SEMANTIC_ROUTES:
        for pattern in patterns:
            if re.search(pattern, desc_lower):
                return template_id, 0.95
    
    return None


# ========== NEURAL ROUTE (Edge Cases) ==========

def neural_route(description: str) -> Optional[Tuple[str, float]]:
    """
    Use GloVe embeddings to find closest template.
    Returns (template_id, confidence) or None if low confidence.
    """
    if not GLOVE_AVAILABLE:
        return None
    
    matches = glove_match(description, top_k=3)
    
    if not matches:
        return None
    
    best_template, best_score = matches[0]
    
    # Only accept if reasonably confident
    if best_score >= 0.4:
        return best_template, best_score
    
    return None


# ========== KEYWORD FALLBACK ==========

# Simple keyword → template mapping for last resort
# Use generic_game for vague game-related terms
KEYWORD_MAP = {
    "game": "generic_game",  # Vague → generic
    "app": "generic_game",   # Vague → generic
    "click": "reaction_game", 
    "card": "blackjack",
    "word": "hangman",
    "puzzle": "sliding_puzzle",
    "match": "memory_game",
    "grid": "tictactoe",
    "fun": "generic_game",    # Vague → generic
    "play": "generic_game",   # Vague → generic
    "list": "crud",
    "track": "crud",
    "note": "crud",
    "manage": "crud",
    "organize": "crud",
    "schedule": "crud",
}


def keyword_route(description: str) -> Optional[Tuple[str, float]]:
    """Last resort: simple keyword matching."""
    desc_lower = description.lower()
    
    for keyword, template_id in KEYWORD_MAP.items():
        if keyword in desc_lower:
            return template_id, 0.3
    
    return None


# ========== AI-ASSIST (NRI) ROUTE ==========

def nri_route(description: str) -> Optional[Tuple[str, float]]:
    """
    Use NRI (Numerical Resonance Intelligence) for AI-enhanced matching.
    This is an optional fallback when semantic and neural routes fail.
    """
    try:
        from ai_assist import nri_match_template
        return nri_match_template(description, threshold=0.35)
    except ImportError:
        return None


# ========== HYBRID ROUTER ==========

@dataclass
class RouteResult:
    """Result of hybrid routing."""
    template_id: str
    confidence: float
    method: str  # "semantic", "neural", "keyword", "fallback"
    
    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.5


def route(description: str) -> RouteResult:
    """
    Route a description to the best template using hybrid matching.
    
    Pipeline:
    0. Empty/nonsense detection → generic_game
    0.1. Prompt injection detection → generic_game
    0.2. Wrong domain detection (physical/impossible) → generic_game
    0.3. Ambiguous detection (too vague) → generic_game
    0.35. Buzzword nonsense detection → generic_game
    0.4. Contradiction detection → generic_game
    0.5. Semantic trap detection → CRUD (prevent wrong game matches)
    0.6. Multi-language support → translate then route
    1. Semantic rules (fast, high confidence)
    2. GloVe neural (handles edge cases)
    3. NRI AI-assist (harmonic resonance matching)
    4. Keyword fallback
    5. Default fallback
    """
    original = description  # Keep original for injection check
    
    # Stage 0: Handle empty/nonsense input
    if is_nonsense_or_empty(description):
        return RouteResult("generic_game", 0.2, "fallback")
    
    # Stage 0.1: Handle prompt injection attempts (check BEFORE sanitization)
    if is_prompt_injection(original):
        return RouteResult("generic_game", 0.1, "fallback")
    
    # NOW sanitize for remaining routing
    description = sanitize_input(description)
    
    # Stage 0.2: Handle wrong domain (physical/impossible requests)
    if is_wrong_domain(description):
        return RouteResult("generic_game", 0.2, "fallback")
    
    # Stage 0.3: Handle ambiguous input (too vague to route)
    if is_ambiguous(description):
        return RouteResult("generic_game", 0.3, "fallback")
    
    # Stage 0.35: Handle tech buzzword nonsense
    if is_buzzword_nonsense(description):
        return RouteResult("generic_game", 0.2, "fallback")
    
    # Stage 0.4: Handle contradictions ("game that isn't a game")
    if is_contradiction(description):
        return RouteResult("generic_game", 0.3, "fallback")
    
    # Stage 0.5: Check semantic traps (game words in non-game contexts)
    trap_result = check_semantic_trap(description)
    if trap_result:
        return RouteResult(trap_result, 0.9, "semantic")
    
    # Stage 0.6: Try multi-language translation
    result = translate_multi_language(description)
    if result:
        return RouteResult(result[0], result[1], "multilang")
    
    # Stage 1: Try semantic rules (fast path)
    result = semantic_route(description)
    if result:
        return RouteResult(result[0], result[1], "semantic")
    
    # Stage 2: Try neural matching (flexible path)
    result = neural_route(description)
    if result:
        return RouteResult(result[0], result[1], "neural")
    
    # Stage 3: Try NRI AI-assist (harmonic resonance)
    result = nri_route(description)
    if result:
        return RouteResult(result[0], result[1], "nri")
    
    # Stage 4: Try keyword fallback
    result = keyword_route(description)
    if result:
        return RouteResult(result[0], result[1], "keyword")
    
    # Stage 5: Default fallback
    return RouteResult("generic_game", 0.1, "fallback")


# ========== INTEGRATION HELPER ==========

def route_to_template(description: str) -> dict:
    """
    Route description and return full template info.
    This is what you'd call from the main app.
    """
    result = route(description)
    
    return {
        "template_id": result.template_id,
        "confidence": result.confidence,
        "method": result.method,
        "is_confident": result.is_confident,
        "description": description,
    }


# ========== TEST ==========

if __name__ == "__main__":
    print(f"GloVe available: {GLOVE_AVAILABLE}")
    print(f"Templates available: {TEMPLATES_AVAILABLE}")
    print()
    
    tests = [
        # Direct matches (semantic)
        ("a snake game", "snake"),
        ("tic tac toe", "tic_tac_toe"),
        ("memory matching game", "memory_game"),
        ("blackjack card game", "blackjack"),
        
        # Well-known aliases (semantic expanded)
        ("something like pac-man", "snake"),
        ("a tetris clone", "snake"),
        ("simon says game", "memory_game"),
        ("battleship style game", "tic_tac_toe"),
        
        # Descriptive (semantic if patterns match, else neural)
        ("a game where you eat dots and avoid ghosts", "snake"),
        ("flip tiles to find matching pairs", "memory_game"),
        ("guess a 5-letter word with color feedback", "wordle"),
        
        # Data apps
        ("a recipe collection app", "recipe"),
        ("track my expenses", "expense_tracker"),
        ("simple todo list", "todo"),
        
        # Edge cases (should use neural or keyword)
        ("a fun activity", None),  # Very vague
        ("something with cards", "blackjack"),  # Keyword
    ]
    
    print("=" * 70)
    print("HYBRID ROUTER TEST")
    print("(Routing to EXISTING templates = full control)")
    print("=" * 70)
    
    correct = 0
    for desc, expected in tests:
        result = route(desc)
        
        # Check if match is reasonable
        if expected is None:
            is_ok = True  # Vague inputs are fine with any result
        else:
            is_ok = result.template_id == expected
        
        correct += 1 if is_ok else 0
        status = "[OK]" if is_ok else "[X]"
        
        print(f"\n{status} \"{desc}\"")
        print(f"   → {result.template_id} ({result.confidence:.2f}) via {result.method}")
        if expected and not is_ok:
            print(f"   Expected: {expected}")
    
    print(f"\n{'='*70}")
    print(f"ACCURACY: {correct}/{len(tests)} ({100*correct//len(tests)}%)")
    print()
    print("Key insight: Routes to existing templates, so you keep FULL control")
    print("over the generated code. The neural part just helps with classification.")
