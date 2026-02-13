"""Template Registry (App Store) + Feature Extractor (Feature Store).

This replaces flat regex matching with a scored approach:
 1. Extract structured features from the description
 2. Score every template against those features
 3. Apply user preference boost from build history
 4. Pick the highest-scoring template

Concepts used:
 - Feature Store:  extract_features() pulls structured signals from text
 - App Store:      TEMPLATE_REGISTRY is a searchable catalogue of templates
 - Attention:      score_template() weights features differently per template
 - Learning:       User preferences boost frequently-used templates
"""


import re
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
import threading

# User preference learning (AI-free)
try:
    from user_prefs import get_template_boost
    USER_PREFS_ENABLED = True
except ImportError:
    USER_PREFS_ENABLED = False
    def get_template_boost(template_id: str) -> float:
        return 0.0


# =====================================================================
# Fuzzy Typo Correction
# =====================================================================
# Known keywords that users commonly misspell. Maps correct -> [variants]
KNOWN_KEYWORDS = {
    # Templates
    "calculator": ["calculater", "calcualtor", "calulator", "calcultor"],
    "timer": ["timmer", "tmer", "timr"],
    "quiz": ["quize", "quis", "quix"],
    "memory": ["memroy", "memoyr", "memry", "mermory"],
    "puzzle": ["puzzel", "puzzl", "puzle", "puzzlle"],
    "reaction": ["recation", "reacton", "reacion", "rection"],
    "minesweeper": ["miensweper", "minesweep", "minseweeper"],
    "hangman": ["hangmna", "hanman", "hangmam"],
    "wordle": ["wordel", "wroddle", "wordel"],
    "converter": ["convertr", "convertor", "conveter"],
    # Game terms
    "tic": ["tik", "tick"],
    "tac": ["tak", "tack"],
    "toe": ["tow", "to"],
    "sliding": ["slidng", "slideing", "slidin"],
    "matching": ["matchng", "matchin", "matcing"],
    "guessing": ["guesing", "gussing", "guessing"],
    "trivia": ["trivia", "trivea", "tirvia"],
}

# Build reverse lookup: misspelling -> correct
_TYPO_MAP: Dict[str, str] = {}
for correct, typos in KNOWN_KEYWORDS.items():
    for typo in typos:
        _TYPO_MAP[typo] = correct


def fuzzy_correct(text: str, cutoff: float = 0.80) -> str:
    """Correct common typos in the input text.
    
    Uses two strategies:
    1. Direct lookup of known misspellings
    2. Fuzzy matching for unknown typos (Levenshtein-based)
    """
    # Common words that look like keywords but aren't typos
    BLOCKLIST = {
        "timed", "timing", "time", "times",  # not timer typos
        "thing", "things", "thinking",  # not matching typos
        "puzzle", "puzzles",  # already correct
        "match", "matches",  # already correct  
        "calculate", "calculated",  # not calculator typos
        "convert", "converted", "converting",  # not converter typos
        "react", "reacting", "reacted",  # not reaction typos
        "guess", "guessed",  # not guessing typos
        "memory", "memories",  # already correct
        "slide", "slides", "sliding",  # already correct
    }
    
    words = text.lower().split()
    corrected = []
    all_keywords = list(KNOWN_KEYWORDS.keys())
    
    for word in words:
        # Strip punctuation for matching
        clean = re.sub(r'[^\w]', '', word)
        
        # Skip blocklisted common words
        if clean in BLOCKLIST:
            corrected.append(word)
            continue
        
        # Strategy 1: Direct typo lookup
        if clean in _TYPO_MAP:
            corrected.append(word.replace(clean, _TYPO_MAP[clean]))
            continue
        
        # Strategy 2: Fuzzy match if word looks like a keyword attempt
        # Only apply if word is long enough and similar length to keywords
        if len(clean) >= 5:  # Longer minimum to avoid false positives
            matches = get_close_matches(clean, all_keywords, n=1, cutoff=cutoff)
            if matches and matches[0] != clean:
                # Only correct if lengths are similar (typo, not different word)
                if abs(len(clean) - len(matches[0])) <= 2:
                    corrected.append(word.replace(clean, matches[0]))
                    continue
        
        # No correction needed
        corrected.append(word)
    
    return ' '.join(corrected)


def normalize_input(text: str, max_length: int = 500) -> str:
    """Normalize input text for better matching.
    
    Handles:
    - Very long inputs (truncation)
    - Hyphenated variants (to-do -> todo)
    - Semantic synonyms (write down -> note)
    - Special characters (removal for cleaner matching)
    """
    # 1. Truncate very long inputs (keep first instance of key patterns)
    if len(text) > max_length:
        text = text[:max_length]
    
    # 2. Normalize common variations
    normalizations = [
        # Hyphenated -> single word
        (r'\bto-do\b', 'todo'),
        (r'\bto do\b', 'todo'),
        (r'\bto-dos\b', 'todos'),
        (r'\bto dos\b', 'todos'),
        (r'\bwork-out\b', 'workout'),
        (r'\bwork out\b', 'workout'),
        (r'\bbook-mark\b', 'bookmark'),
        (r'\bbook mark\b', 'bookmark'),
        
        # Semantic synonyms -> known keywords
        (r'\bwrite\s+down\s+(stuff|things|notes?|ideas?)\b', 'note'),
        (r'\bjot\s+down\b', 'note'),
        (r'\bkeep\s+track\s+of\b', 'tracker'),
        (r'\bremember\s+(stuff|things)\b', 'note'),
        (r'\bsave\s+(stuff|things|ideas?)\b', 'collection'),
        (r'\blist\s+(stuff|things|items?)\b', 'collection'),
        (r'\borganize\s+(stuff|things|items?)\b', 'collection'),
        (r'\bstore\s+(stuff|things|items?)\b', 'collection'),
    ]
    
    result = text.lower()
    for pattern, replacement in normalizations:
        result = re.sub(pattern, replacement, result)
    
    # 3. Remove excessive special characters (keep alphanumeric, spaces, basic punctuation)
    # This doesn't remove all special chars, just cleans up noise like "!!!" or "@#$%"
    result = re.sub(r'[^\w\s\-.,!?\'"]+', ' ', result)
    result = re.sub(r'[!?]{2,}', '!', result)  # Multiple !!! -> single !
    
    return result.strip()


# =====================================================================
# Feature Extractor  (Feature Store)
# =====================================================================
# Extracts structured features from a natural-language description.
# Each feature has a name, value, and confidence (0-1).

@dataclass
class Feature:
    name: str
    value: str          # e.g. "3" for grid_size, "numbers" for tile_content
    confidence: float   # 0.0 - 1.0
    position: int = 0   # Character position in description (0 = start)

    def __repr__(self):
        return f"Feature({self.name}={self.value}, conf={self.confidence:.2f}, pos={self.position})"


# Extraction rules: (feature_name, pattern, value_extractor, confidence)
# value_extractor: either a static string, or a group index from the regex
FEATURE_RULES: List[Tuple[str, str, object, float]] = [
    # Grid / board games
    ("grid_size",    r"(\d+)\s*[x×]\s*(\d+)",                "group:1", 0.95),
    ("grid_game",    r"grid|board|tile|sliding|slide|swap",   "true",    0.80),
    ("numbered",     r"number|numbered|digit|\bN\b",          "true",    0.75),

    # Game mechanics
    ("sliding",      r"slid(e|ing)|shift|swap\s*(tile|piece|block)|15\s*puzzle|tile\s*puzzle|number\s*puzzle|move\s*(the\s*)?tiles?",  "true", 0.90),
    ("puzzle",       r"puzzle|solving|solve|brain\s*tease",    "true",   0.80),
    ("matching",     r"match(ing)?|pair|flip|memory",          "true",   0.80),
    ("guessing",     r"guess(ing)?|random\s*number",           "true",   0.85),
    ("trivia",       r"quiz|trivia|question\s*(and|&)\s*answer|flashcard|knowledge\s*test", "true", 0.85),
    ("turn_based",   r"turn|player\s*[12]|two\s*player|vs\b", "true",   0.75),
    ("reaction",     r"reaction|reflex|speed\s*test|quick|fast\s*(click|react|tap)|how\s*fast.*(react|click)|whack.*(button|fast)",    "true",   0.85),
    ("simon",        r"simon|whack.?a.?mole|click\s*(the\s*)?(target|green|tile)|randomly\s*(puts?|shows?|displays?)", "true", 0.95),
    ("click_target", r"click\s*(it|on|the)|tap\s*(the|on)|hit\s*the", "true", 0.80),
    ("timing",       r"timer|countdown|stopwatch|pomodoro|clock", "true", 0.85),

    # Specific games
    ("tictactoe",    r"tic.?tac.?toe|noughts.*crosses|x.?s?.?and.?o.?s?|x.?and.?o", "true", 0.95),
    ("snake",        r"snake\s*game|snake\b|moving\s*snake|eat.*(pellet|food)|grow.*eat|classic\s*snake", "true", 0.95),
    ("tetris",       r"tetris|falling\s*blocks?|tetromino|block\s*stacking|stack.*blocks?|clear.*lines?|line\s*clear", "true", 0.95),
    ("game_2048",    r"2048|twenty.?forty.?eight|tile\s*merge|merge\s*tiles?|slide.*numbers?|double.*numbers?", "true", 0.95),
    ("hangman",      r"hangman|word\s*guess|secret\s*word|spell\s*(out|a|the)?\s*word|"
                     r"letter\s*by\s*letter|guess\s*(the\s*)?letters?|"
                     r"reveal\s*(hidden\s*)?word", "true", 0.95),

    ("wordle",       r"wordle|word\s*puzzle",                  "true",   0.85),
    ("minesweeper",  r"minesweeper|mine\s*sweep|mines?\s*game|bomb\s*grid|flag\s*mines?|"
                     r"hidden\s*(bombs?|mines?)|find\s*(the\s*)?(bombs?|mines?)|"
                     r"bombs?\s*(on|in)\s*(a\s*)?grid|bomb.{0,10}(find|game|search)|"
                     r"(find|search).{0,10}bomb", "true", 0.95),

    # Phaser.js advanced games
    ("platformer",   r"platformer|platform\s*game|side.?scroll|jump.*(platform|game)|mario|"
                     r"run\s*and\s*jump|collect.*coins?|2d\s*platform", "true", 0.95),
    ("shooter",      r"space\s*shooter|shoot.?em.?up|shmup|bullet\s*hell|invaders?|"
                     r"shoot.*enemies?|enemies?.*shoot|galaga|asteroids?|"
                     r"shooting\s*game|bullet\s*game", "true", 0.95),
    ("breakout",     r"breakout|brick\s*break|arkanoid|paddle.*ball|ball.*paddle|"
                     r"bounce.*ball.*brick|break.*bricks?|pong.*bricks?", "true", 0.95),

    # Additional classic games
    ("pong",         r"\bpong\b|paddle\s*game|two\s*paddle|ping\s*pong|table\s*tennis\s*game", "true", 0.95),
    ("cookie_clicker", r"cookie\s*click|clicker\s*(game|with)|idle\s*(game|clicker)|incremental|tap.*earn|click.*earn|"
                     r"auto.?click|upgrades?\s*and\s*click", "true", 0.95),
    ("sudoku",       r"sudoku|9\s*x\s*9.*puzzle|number\s*grid\s*puzzle|logic\s*puzzle\s*9", "true", 0.95),
    ("connect_four", r"connect\s*(4|four)|four\s*in\s*a?\s*row|drop\s*disc|vertical\s*checkers", "true", 0.95),
    ("blackjack",    r"blackjack|black\s*jack|21\s*card|twenty.?one|hit\s*(or|and)\s*stand|card\s*game\s*21", "true", 0.95),
    ("flappy",       r"flappy|tap\s*to\s*fly|flying\s*bird|tap.*fly.*bird|pipe\s*dodge|avoid.*pipes?", "true", 0.95),
    ("jigsaw",       r"jigsaw|image\s*puzzle|picture\s*puzzle|photo\s*puzzle|"
                     r"(split|cut|divide).*(image|picture|photo).*pieces?|"
                     r"pieces?\s*(back\s*)?(together|reassemble)|"
                     r"(reassemble|rearrange).*(image|picture|photo|pieces?)|"
                     r"upload.*(image|picture|photo).*(puzzle|pieces?)|"
                     r"(image|picture|photo).*(into|to)\s*(a\s*)?puzzle", "true", 0.95),

    # Simple generators / utilities
    ("algorithm_vis", r"algorithm\s*visual|sorting\s*visual|sort.*animation|visualiz.*sort|binary\s*search.*visual|algorithm.*step|step.*through.*algorithm", "true", 0.95),
    ("coin_flip",    r"coin\s*flip|flip\s*(a\s*)?coin|heads\s*(or|and)\s*tails|coin\s*toss|toss.*coin", "true", 0.95),
    ("dice_roller",  r"dice\s*roll|roll(er|ing)?\s*(a\s*)?(die|dice)|die\s*roll|random\s*dice", "true", 0.95),
    ("typing_test",  r"typing\s*(speed\s*)?(test|game|practice)|speed\s*typ(e|ing)|wpm\s*test|word(s)?\s*per\s*minute", "true", 0.95),
    ("rps",          r"rock\s*paper\s*scissors|rps\b|roshambo", "true", 0.95),

    # NEW: Dashboard and analytics
    ("dashboard",    r"dashboard|analytics|metrics|kpi|charts?|graphs?|statistics|visualiz|report|monitor", "true", 0.90),
    
    # NEW: Weather
    ("weather",      r"weather|forecast|temperature|climate|rain|humidity|meteorolog", "true", 0.95),
    
    # NEW: Chat/messaging
    ("chat",         r"\bchat\b|messag|conversation|talk|instant\s*messag|dm\b|slack|discord", "true", 0.90),
    
    # NEW: File management
    ("file_manager", r"file\s*(manager|browser|upload|download)|folder|drive|storage\s*(app|manager)", "true", 0.90),
    
    # NEW: Kanban
    ("kanban",       r"kanban|trello|board.*columns?|cards?.*drag|project.*board|agile.*board", "true", 0.95),
    
    # NEW: Pomodoro
    ("pomodoro",     r"pomodoro|focus\s*timer|work.*break|25\s*min|productivity\s*timer", "true", 0.95),
    
    # NEW: Markdown editor
    ("markdown_editor", r"markdown|md\s*editor|write.*preview|document\s*editor|wysiwyg|rich\s*text", "true", 0.90),
    
    # NEW: Drawing
    ("drawing",      r"draw(ing)?|paint|canvas|sketch|doodle|whiteboard|art\s*app|pixel\s*art", "true", 0.90),
    
    # NEW: Music player
    ("music_player", r"music\s*player|audio|playlist|mp3|song|album|spotify|soundcloud", "true", 0.95),
    
    # NEW: Image gallery
    ("gallery",      r"gallery|photos?|images?|album|lightbox|slideshow|portfolio", "true", 0.85),
    
    # NEW: URL shortener
    ("url_shortener", r"url\s*shorten|link\s*shorten|bitly|short\s*link|redirect\s*service", "true", 0.95),
    
    # NEW: QR code
    ("qr_code",      r"qr\s*code|qrcode|barcode|scan\s*code|generate.*qr", "true", 0.95),
    
    # NEW: Countdown
    ("countdown",    r"countdown|event\s*timer|days?\s*until|remaining\s*time|launch\s*timer", "true", 0.90),
    
    # NEW: Invoice
    ("invoice",      r"invoice|billing|receipt|payment|pdf.*invoice|business.*invoice", "true", 0.90),
    
    # NEW: Poll/Survey
    ("poll",         r"poll|survey|vote|voting|questionnaire|form|feedback|opinion", "true", 0.85),
    
    # NEW: Habit
    ("habit",        r"habit|streak|daily\s*track|routine|goal\s*track|30\s*day", "true", 0.90),
    
    # NEW: Video player
    ("video_player", r"video\s*player|youtube|stream|watch.*video|movie\s*player", "true", 0.95),

    # Tools
    ("calculator",   r"calculator|calc\b|arithmetic|number\s*crunch|math\s*problems?",          "true",   0.90),
    ("converter",    r"converter|convert\s+unit|unit\s+convert|unit\s*transform|bmi|mortgage|"
                     r"celsius|fahrenheit|temperature|kelvin|"
                     r"kilometer|mile|inch|centimeter|meter|feet|yard|"
                     r"pound|kilogram|ounce|gram|"
                     r"gallon|liter|cup|pint|"
                     r"currency|dollar|euro|yen", "true", 0.90),

    # Content types
    ("tile_content", r"(number|letter|color|image|emoji|picture)\s*(tile|block|piece|square)?", "group:1", 0.80),
    ("word_based",   r"word|letter|anagram|scrabble|crossword", "true",  0.75),

    # Generic "game" or "app" (fallback indicator)
    ("generic_game", r"\bgame\b|\bplay\b|fun\s+(app|thing)|entertainment", "true", 0.50),
    ("generic_app",  r"\bapp\b|\bapplication\b|\btool\b", "true", 0.50),

    # Layout / responsiveness
    ("responsive",   r"responsive|fullscreen|full.?screen|mobile|resiz(e|es|ing)|"
                     r"fit\w*\s*(to|the)?\s*(screen|window)|fills?\s*(the)?\s*(window|screen)|"
                     r"adapt|scales?|any.?size|different.?screen|device.?size", "true", 0.90),
    ("fixed_size",   r"fixed.?size|exact\s*\d+|pixel|small\s*window|not\s*resize", "true", 0.85),

    # Common app features
    ("auth",         r"\bauth\b|login|log.?in|sign.?in|password|user\s*name|account|authentication|"
                     r"register|sign.?up|logged.?in|session", "true", 0.85),
    ("storage",      r"save|persist|store|local.?storage|database|remember|sync|backup|"
                     r"import|load|keep\s*(the\s*)?data", "true", 0.80),
    ("search",       r"search|searchable|find|filter|look\s*up|query|browse", "true", 0.85),
    ("tags",         r"\btags?\b|label|categoriz|categor(y|ies)|hashtag", "true", 0.85),
    ("export",       r"export|download|pdf|csv|print|backup", "true", 0.85),
    ("share",        r"shar(e|ing)|social|post\s*to|publish|collaborat", "true", 0.85),

    # Data apps (not games)
    ("data_app",     r"recipe|cooking|cookbook|\bcook\b|todo|task|inventory|product|blog|contact|event|"
                     r"calendar|note|movie|habit|collection|tracker|bookmark|catalog|"
                     r"library|portfolio|budget|expense|journal|diary|grocery|workout|log\b",
                     "true", 0.80),
]


def _extract_features(description: str) -> Dict[str, Feature]:
    """Pull structured features from a description.
    
    Tracks position of each feature for attention-based scoring.
    """
    # Apply normalization to handle edge cases (long input, special chars, synonyms)
    normalized = normalize_input(description)
    desc = fuzzy_correct(normalized)
    features: Dict[str, Feature] = {}
    for feat_name, pattern, value_extractor, conf in FEATURE_RULES:
        m = re.search(pattern, desc)
        if m:
            if isinstance(value_extractor, str) and value_extractor.startswith("group:"):
                gnum = int(value_extractor.split(":")[1])
                val = m.group(gnum)
            else:
                val = str(value_extractor)
            pos = m.start()
            if feat_name not in features or features[feat_name].confidence < conf:
                features[feat_name] = Feature(feat_name, val, conf, pos)
    return features

# Memoized version for repeated calls
@lru_cache(maxsize=128)
def extract_features(description: str) -> Dict[str, Feature]:
    # lru_cache requires hashable return, so convert to tuple and back
    feats = _extract_features(description)
    return {k: v for k, v in feats.items()}


# =====================================================================
# Template Registry  (App Store)
# =====================================================================
# Each template declares:
#   - id:          Unique key (maps to generator method)
#   - name:        Human-readable name
#   - tags:        Keywords for basic matching
#   - required:    Features that MUST be present (hard filter)
#   - boosted:     Features that increase score (soft preference)
#   - anti:        Features that decrease score (wrong match)
#   - base_score:  Starting score (specificity — higher = more specific)

@dataclass
class TemplateEntry:
    id: str
    name: str
    tags: List[str] = field(default_factory=list)
    required: List[str] = field(default_factory=list)
    boosted: List[str] = field(default_factory=list)
    anti: List[str] = field(default_factory=list)
    base_score: float = 0.0


TEMPLATE_REGISTRY: List[TemplateEntry] = [
    # --- Specific games (high base_score = more specific) ---
    TemplateEntry(
        id="jigsaw",
        name="Image Puzzle / Jigsaw",
        tags=["jigsaw", "puzzle", "image", "picture", "photo", "drag", "reassemble"],
        required=["jigsaw"],  # Require specific jigsaw-related keywords
        boosted=["jigsaw", "puzzle", "drag"],
        anti=["sliding", "numbered", "calculator", "converter", "data_app", "text_based"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="sliding_puzzle",
        name="Sliding Tile Puzzle",
        tags=["sliding", "puzzle", "tile", "grid", "number", "15-puzzle"],
        required=["sliding"],  # Must have 'sliding', '15 puzzle', 'tile puzzle', etc.
        boosted=["grid_game", "sliding", "puzzle", "numbered", "grid_size", "tile_content"],
        anti=["matching", "guessing", "trivia", "calculator", "converter", "data_app", "game_2048", "jigsaw"],
        base_score=8.0,
    ),
    TemplateEntry(
        id="tictactoe",
        name="Tic Tac Toe",
        tags=["tictactoe", "grid", "turn", "two-player"],
        required=["tictactoe"],
        boosted=["turn_based", "grid_game"],
        anti=["sliding", "matching", "guessing", "data_app"],
        base_score=8.0,
    ),
    TemplateEntry(
        id="memory_game",
        name="Memory Match",
        tags=["memory", "match", "card", "flip", "pairs"],
        required=["matching"],  # Must mention match/memory/flip/pairs
        boosted=["matching", "grid_game"],
        anti=["sliding", "guessing", "trivia", "numbered", "data_app", "coin_flip", "dice_roller"],
        base_score=5.0,
    ),
    TemplateEntry(
        id="guess_game",
        name="Guess the Number",
        tags=["guess", "number", "random", "higher-lower"],
        required=["guessing"],  # Must mention guess/random
        boosted=["guessing", "numbered"],
        anti=["grid_game", "sliding", "matching", "trivia", "data_app"],
        base_score=4.0,
    ),
    TemplateEntry(
        id="quiz",
        name="Quiz / Trivia",
        tags=["quiz", "trivia", "flashcard", "question"],
        required=["trivia"],  # Must mention quiz/trivia/question
        boosted=["trivia", "word_based"],
        anti=["grid_game", "sliding", "guessing", "calculator", "data_app"],
        base_score=5.0,
    ),
    TemplateEntry(
        id="hangman",
        name="Hangman",
        tags=["hangman", "word", "guess", "letters"],
        required=["hangman"],
        boosted=["word_based", "guessing"],
        anti=["grid_game", "numbered", "data_app"],
        base_score=8.0,
    ),
    TemplateEntry(
        id="wordle",
        name="Wordle-style Word Puzzle",
        tags=["wordle", "word", "guess", "puzzle"],
        required=["wordle"],
        boosted=["word_based", "puzzle", "guessing"],
        anti=["grid_game", "numbered", "data_app"],
        base_score=8.0,
    ),
    # --- Tools ---
    TemplateEntry(
        id="calculator",
        name="Calculator",
        tags=["calculator", "math", "arithmetic"],
        required=["calculator"],
        boosted=["numbered", "tile_content"],  # Added tile_content - numbers are calc inputs too
        anti=["grid_game", "sliding", "matching", "data_app"],
        base_score=8.0,
    ),
    TemplateEntry(
        id="converter",
        name="Unit Converter",
        tags=["converter", "unit", "temperature", "weight", "length"],
        required=["converter"],
        boosted=["numbered"],
        anti=["grid_game", "sliding", "matching", "data_app"],
        base_score=8.0,
    ),
    TemplateEntry(
        id="timer",
        name="Timer / Pomodoro",
        tags=["timer", "countdown", "stopwatch", "pomodoro", "clock"],
        required=["timing"],
        boosted=["timing"],
        anti=["grid_game", "sliding", "matching", "reaction", "generic_game"],  # Removed data_app - timers often used for cooking etc
        base_score=10.0,
    ),
    TemplateEntry(
        id="reaction_game",
        name="Reaction Time Game",
        tags=["reaction", "reflex", "speed", "click", "simon", "whack", "mole", "target", "green"],
        required=["reaction"],  # Must mention reaction/reflex/speed/simon
        boosted=["reaction", "simon", "reflex", "click_target"],
        anti=["sliding", "puzzle", "numbered", "calculator", "converter", "data_app", "timing"],
        base_score=5.0,  # Lowered - should only win with boosted features
    ),
    TemplateEntry(
        id="minesweeper",
        name="Minesweeper",
        tags=["minesweeper", "mines", "bomb", "grid", "flag"],
        required=["minesweeper"],
        boosted=["grid_game"],
        anti=["sliding", "matching", "trivia", "guessing", "data_app"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="snake",
        name="Snake Game",
        tags=["snake", "eat", "grow", "pellet", "food", "classic"],
        required=["snake"],
        boosted=["grid_game"],
        anti=["sliding", "matching", "trivia", "guessing", "data_app", "puzzle"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="tetris",
        name="Tetris",
        tags=["tetris", "falling", "blocks", "tetromino", "stack", "line", "clear"],
        required=["tetris"],
        boosted=["grid_game"],
        anti=["sliding", "matching", "trivia", "guessing", "data_app"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="game_2048",
        name="2048",
        tags=["2048", "merge", "tiles", "slide", "numbers", "double"],
        required=["game_2048"],
        boosted=["grid_game", "numbered"],
        anti=["matching", "trivia", "guessing", "data_app"],
        base_score=12.0,
    ),
    # --- Simple Generators / Utilities ---
    TemplateEntry(
        id="coin_flip",
        name="Coin Flipper",
        tags=["coin", "flip", "heads", "tails", "random"],
        required=["coin_flip"],
        boosted=[],
        anti=["data_app", "grid_game", "puzzle"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="dice_roller",
        name="Dice Roller",
        tags=["dice", "die", "roll", "random", "d6", "d20"],
        required=["dice_roller"],
        boosted=[],
        anti=["data_app", "grid_game", "puzzle"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="typing_test",
        name="Typing Speed Test",
        tags=["typing", "speed", "wpm", "keyboard", "words"],
        required=["typing_test"],
        boosted=["reaction"],
        anti=["data_app", "grid_game", "puzzle"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="rps",
        name="Rock Paper Scissors",
        tags=["rock", "paper", "scissors", "rps", "game"],
        required=["rps"],
        boosted=["generic_game"],
        anti=["data_app", "grid_game", "puzzle"],
        base_score=12.0,
    ),
    # --- Phaser.js Advanced Games ---
    TemplateEntry(
        id="platformer",
        name="Platformer Game",
        tags=["platformer", "platform", "jump", "side-scroll", "mario", "coins", "run"],
        required=["platformer"],
        boosted=["generic_game"],
        anti=["data_app", "calculator", "converter", "timing", "trivia", "puzzle"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="shooter",
        name="Space Shooter",
        tags=["shooter", "space", "shoot", "invaders", "galaga", "asteroids", "bullets", "enemies"],
        required=["shooter"],
        boosted=["generic_game"],
        anti=["data_app", "calculator", "converter", "timing", "trivia", "puzzle"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="breakout",
        name="Breakout / Brick Breaker",
        tags=["breakout", "arkanoid", "brick", "paddle", "ball", "bounce", "pong"],
        required=["breakout"],
        boosted=["generic_game"],
        anti=["data_app", "calculator", "converter", "timing", "trivia", "puzzle"],
        base_score=12.0,
    ),
    # --- Additional Classic Games ---
    TemplateEntry(
        id="pong",
        name="Pong",
        tags=["pong", "paddle", "ping pong", "table tennis", "two player"],
        required=["pong"],
        boosted=["generic_game"],
        anti=["data_app", "breakout"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="cookie_clicker",
        name="Cookie Clicker / Idle Game",
        tags=["clicker", "idle", "incremental", "tap", "upgrade", "cookie"],
        required=["cookie_clicker"],
        boosted=["generic_game"],
        anti=["data_app", "puzzle"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="sudoku",
        name="Sudoku",
        tags=["sudoku", "9x9", "logic", "number puzzle"],
        required=["sudoku"],
        boosted=["puzzle", "grid_game"],
        anti=["data_app", "matching"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="connect_four",
        name="Connect Four",
        tags=["connect four", "four in a row", "disc", "vertical"],
        required=["connect_four"],
        boosted=["grid_game", "turn_based"],
        anti=["data_app"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="blackjack",
        name="Blackjack",
        tags=["blackjack", "21", "cards", "hit", "stand", "casino"],
        required=["blackjack"],
        boosted=["generic_game"],
        anti=["data_app", "puzzle"],
        base_score=12.0,
    ),
    TemplateEntry(
        id="flappy",
        name="Flappy Bird",
        tags=["flappy", "bird", "fly", "pipes", "tap"],
        required=["flappy"],
        boosted=["generic_game"],
        anti=["data_app", "puzzle"],
        base_score=12.0,
    ),
    # --- CRUD / Data Apps ---
    TemplateEntry(
        id="crud",
        name="Data Collection App",
        tags=["recipe", "task", "todo", "note", "habit", "inventory", "collection", 
              "tracker", "log", "budget", "expense", "contact", "event", "calendar",
              "movie", "book", "workout", "grocery", "journal"],
        required=["data_app"],  # Must mention data-related keywords
        boosted=["data_app"],
        anti=["grid_game", "sliding", "matching", "guessing", "reaction", "puzzle", 
              "calculator", "converter", "simon", "minesweeper", "hangman", "wordle", "timing"],  # Added timing
        base_score=6.0,
    ),
    # --- Educational / Visualization ---
    TemplateEntry(
        id="algorithm_visualizer",
        name="Algorithm Visualizer",
        tags=["algorithm", "visualizer", "sorting", "searching", "animation", "step", "learn"],
        required=["algorithm_vis"],
        boosted=["algorithm_vis"],
        anti=["data_app", "calculator", "puzzle", "game"],
        base_score=12.0,
    ),
    # --- NEW: Dashboard / Analytics ---
    TemplateEntry(
        id="dashboard",
        name="Dashboard / Analytics",
        tags=["dashboard", "analytics", "metrics", "charts", "graphs", "statistics", "kpi", "report"],
        required=["dashboard"],
        boosted=["data_app", "storage"],
        anti=["generic_game", "puzzle", "reaction"],
        base_score=10.0,
    ),
    # --- NEW: Weather App ---
    TemplateEntry(
        id="weather",
        name="Weather App",
        tags=["weather", "forecast", "temperature", "climate", "rain", "humidity"],
        required=["weather"],
        boosted=["data_app"],
        anti=["generic_game", "puzzle"],
        base_score=12.0,
    ),
    # --- NEW: Chat / Messaging ---
    TemplateEntry(
        id="chat_app",
        name="Chat / Messaging",
        tags=["chat", "message", "messaging", "conversation", "talk", "dm", "instant"],
        required=["chat"],
        boosted=["auth", "storage"],
        anti=["generic_game", "puzzle", "calculator"],
        base_score=10.0,
    ),
    # --- NEW: File Manager ---
    TemplateEntry(
        id="file_manager",
        name="File Manager",
        tags=["file", "files", "folder", "upload", "download", "browser", "storage", "drive"],
        required=["file_manager"],
        boosted=["storage", "auth"],
        anti=["generic_game", "puzzle"],
        base_score=10.0,
    ),
    # --- NEW: Kanban Board ---
    TemplateEntry(
        id="kanban",
        name="Kanban Board",
        tags=["kanban", "board", "trello", "cards", "columns", "drag", "project"],
        required=["kanban"],
        boosted=["data_app", "auth"],
        anti=["generic_game", "puzzle", "calculator"],
        base_score=10.0,
    ),
    # --- NEW: Pomodoro Timer ---
    TemplateEntry(
        id="pomodoro",
        name="Pomodoro Timer",
        tags=["pomodoro", "focus", "productivity", "work", "break", "session"],
        required=["pomodoro"],
        boosted=["timing"],
        anti=["generic_game", "puzzle", "data_app"],
        base_score=12.0,
    ),
    # --- NEW: Markdown Editor ---
    TemplateEntry(
        id="markdown_editor",
        name="Markdown Editor",
        tags=["markdown", "md", "editor", "preview", "write", "document", "notes"],
        required=["markdown_editor"],
        boosted=["storage"],
        anti=["generic_game", "puzzle", "calculator"],
        base_score=10.0,
    ),
    # --- NEW: Drawing Canvas ---
    TemplateEntry(
        id="drawing_canvas",
        name="Drawing Canvas",
        tags=["draw", "drawing", "paint", "canvas", "sketch", "doodle", "art", "whiteboard"],
        required=["drawing"],
        boosted=["generic_game"],
        anti=["data_app", "calculator", "puzzle"],
        base_score=10.0,
    ),
    # --- NEW: Music Player ---
    TemplateEntry(
        id="music_player",
        name="Music Player",
        tags=["music", "player", "audio", "playlist", "mp3", "song", "album"],
        required=["music_player"],
        boosted=["storage"],
        anti=["generic_game", "puzzle"],
        base_score=12.0,
    ),
    # --- NEW: Image Gallery ---
    TemplateEntry(
        id="image_gallery",
        name="Image Gallery",
        tags=["gallery", "photos", "images", "album", "lightbox", "slideshow"],
        required=["gallery"],
        boosted=["storage", "tags"],
        anti=["generic_game", "puzzle", "calculator"],
        base_score=10.0,
    ),
    # --- NEW: URL Shortener ---
    TemplateEntry(
        id="url_shortener",
        name="URL Shortener",
        tags=["shortener", "url", "link", "shorten", "redirect", "bitly"],
        required=["url_shortener"],
        boosted=["storage"],
        anti=["generic_game", "puzzle"],
        base_score=12.0,
    ),
    # --- NEW: QR Code Generator ---
    TemplateEntry(
        id="qr_generator",
        name="QR Code Generator",
        tags=["qr", "qrcode", "barcode", "scan", "generate"],
        required=["qr_code"],
        boosted=[],
        anti=["generic_game", "puzzle", "data_app"],
        base_score=12.0,
    ),
    # --- NEW: Countdown Timer ---
    TemplateEntry(
        id="countdown",
        name="Countdown Timer",
        tags=["countdown", "event", "timer", "until", "days", "remaining"],
        required=["countdown"],
        boosted=["timing"],
        anti=["generic_game", "puzzle"],
        base_score=10.0,
    ),
    # --- NEW: Invoice Generator ---
    TemplateEntry(
        id="invoice_generator",
        name="Invoice Generator",
        tags=["invoice", "billing", "receipt", "payment", "pdf", "business"],
        required=["invoice"],
        boosted=["data_app", "export"],
        anti=["generic_game", "puzzle"],
        base_score=10.0,
    ),
    # --- NEW: Flashcard Study ---
    TemplateEntry(
        id="flashcards",
        name="Flashcard Study App",
        tags=["flashcard", "study", "learn", "memorize", "spaced", "repetition", "anki"],
        required=["trivia"],
        boosted=["data_app", "storage"],
        anti=["generic_game", "puzzle", "calculator"],
        base_score=8.0,
    ),
    # --- NEW: Poll / Survey ---
    TemplateEntry(
        id="poll_survey",
        name="Poll / Survey App",
        tags=["poll", "survey", "vote", "voting", "questionnaire", "form", "feedback"],
        required=["poll"],
        boosted=["data_app", "auth"],
        anti=["generic_game", "puzzle"],
        base_score=10.0,
    ),
    # --- NEW: Habit Tracker ---
    TemplateEntry(
        id="habit_tracker",
        name="Habit Tracker",
        tags=["habit", "streak", "daily", "track", "routine", "goals"],
        required=["habit"],
        boosted=["data_app", "storage"],
        anti=["generic_game", "puzzle"],
        base_score=10.0,
    ),
    # --- NEW: Video Player ---
    TemplateEntry(
        id="video_player",
        name="Video Player",
        tags=["video", "player", "youtube", "stream", "watch", "movie"],
        required=["video_player"],
        boosted=["storage"],
        anti=["generic_game", "puzzle"],
        base_score=12.0,
    ),
    # --- Fallback ---
    TemplateEntry(
        id="generic_game",
        name="Generic Game",
        tags=["game", "play", "fun", "entertainment"],
        required=[],
        boosted=["generic_game"],
        anti=["data_app", "calculator", "converter", "timing", 
              "sliding", "matching", "guessing", "trivia", "tictactoe",
              "hangman", "wordle", "minesweeper", "simon", "reaction"],
        base_score=4.0,  # Low but not zero - used when no specific game matches
    ),
]


@lru_cache(maxsize=256)
def score_template_cached(template_id: str, features_hash: int, desc_len: int = 100, position_weight: float = 3.0) -> float:
    template = next(t for t in TEMPLATE_REGISTRY if t.id == template_id)
    # Unpack features from hash (for cache)
    # This is a simple optimization; in practice, use a better hash/serialization
    features = features_hash_map[features_hash]
    return score_template(template, features, desc_len, position_weight)

def score_template(template: TemplateEntry, features: Dict[str, Feature], desc_len: int = 100, position_weight: float = 3.0) -> float:
    """Score a template against extracted features.  Higher = better match.

    Scoring (attention-like weighting):
     - Start with base_score (template specificity)
     - Required features: if missing → return -infinity
     - Boosted features: add  feature.confidence * 10  per match
     - Position attention: earlier features get bonus (first-mentioned wins ties)
     - Anti features:    subtract  feature.confidence * 8  per match
    """
    score = template.base_score

    # Hard requirement check
    for req in template.required:
        if req not in features:
            return -999.0

    # Boosted features (feature-level attention with position bonus)
    for boost in template.boosted:
        if boost in features:
            feat = features[boost]
            # Base boost from confidence
            score += feat.confidence * 10.0
            # Position attention: earlier = higher bonus
            # Formula: bonus = weight * (1 - pos/desc_len)
            # At position 0: full bonus; at end: ~0 bonus
            if desc_len > 0:
                position_bonus = position_weight * (1.0 - min(feat.position / desc_len, 1.0))
                score += position_bonus

    # Anti features (negative attention)
    for anti in template.anti:
        if anti in features:
            score -= features[anti].confidence * 8.0

    return score


def match_template(description: str, use_prefs: bool = True) -> Tuple[str, Dict[str, Feature], List[Tuple[str, float]]]:
    """Find the best template for a description.

    Args:
        description: Natural language app description
        use_prefs: If True, apply user preference boosts from build history

    Returns:
        (best_template_id, features, all_scores)
    """
    features = extract_features(description)
    desc_len = len(description)
    # For caching, hash features dict
    features_hash = hash(tuple(sorted(features.items())))
    global features_hash_map
    if 'features_hash_map' not in globals():
        features_hash_map = {}
    features_hash_map[features_hash] = features

    scores: List[Tuple[str, float]] = []
    threads = []
    results = [None] * len(TEMPLATE_REGISTRY)

    def score_worker(idx, tmpl):
        s = score_template_cached(tmpl.id, features_hash, desc_len=desc_len)
        if use_prefs and USER_PREFS_ENABLED:
            pref_boost = get_template_boost(tmpl.id)
            s += pref_boost
        results[idx] = (tmpl.id, round(s, 2))

    # Parallelize scoring for speed
    for idx, tmpl in enumerate(TEMPLATE_REGISTRY):
        t = threading.Thread(target=score_worker, args=(idx, tmpl))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    scores = [r for r in results if r is not None]
    scores.sort(key=lambda x: -x[1])
    best_id = scores[0][0] if scores else "generic_game"
    return best_id, features, scores


# =====================================================================
# Diagnostic helper  (for debugging / UI)
# =====================================================================
def explain_match(description: str) -> str:
    """Human-readable explanation of why a template was chosen."""
    best_id, features, scores = match_template(description)

    lines = [f"Description: \"{description}\"", ""]
    lines.append("Extracted Features:")
    for f in features.values():
        lines.append(f"  {f}")
    lines.append("")
    lines.append("Template Scores (top 5):")
    for tid, s in scores[:5]:
        marker = " ← SELECTED" if tid == best_id else ""
        # Look up template name
        name = tid
        for t in TEMPLATE_REGISTRY:
            if t.id == tid:
                name = t.name
                break
        lines.append(f"  {s:7.2f}  {name} ({tid}){marker}")

    return "\n".join(lines)


# =====================================================================
# Hybrid Matching (Regex + TF-IDF + BM25 + Jaccard)
# =====================================================================
def match_template_hybrid(description: str, semantic_weight: float = 0.5) -> Tuple[str, Dict[str, Feature], List[Tuple[str, float]]]:
    """Enhanced matching combining regex features with semantic similarity.
    
    Args:
        description: Natural language app description
        semantic_weight: Weight for TF-IDF+BM25+Jaccard (0.0 = regex only, 1.0 = semantic only)
    
    Returns:
        (best_template_id, features, all_scores)
    
    The hybrid score combines:
      - Regex-based feature matching (structured, precise)
      - Combined semantic similarity (TF-IDF + BM25 + Jaccard)
    
    This catches cases like "different colored tiles" that regex misses,
    while still respecting hard requirements from regex.
    """
    # Get regex-based scores
    features = extract_features(description)
    regex_scores: Dict[str, float] = {}
    for tmpl in TEMPLATE_REGISTRY:
        regex_scores[tmpl.id] = score_template(tmpl, features)
    
    # Get combined semantic scores (TF-IDF + BM25 + Jaccard)
    semantic_scores: Dict[str, float] = {}
    try:
        from tfidf_matcher import combined_match
        semantic_results = combined_match(description, top_k=len(TEMPLATE_REGISTRY))
        
        # Combined scores are normalized 0-1, scale to match regex range (~0-30)
        max_regex = max(regex_scores.values()) if regex_scores else 1
        max_regex = max(max_regex, 10)  # Minimum scale factor
        
        for tid, sim in semantic_results:
            semantic_scores[tid] = sim * max_regex
    except ImportError:
        # Semantic matcher not available, use regex only
        semantic_weight = 0.0
    
    # Combine scores
    combined: List[Tuple[str, float]] = []
    for tmpl in TEMPLATE_REGISTRY:
        r_score = regex_scores.get(tmpl.id, 0)
        s_score = semantic_scores.get(tmpl.id, 0)
        
        # Skip if regex gave -999 (hard requirement failed)
        if r_score < -100:
            combined.append((tmpl.id, r_score))
        else:
            final = (1 - semantic_weight) * r_score + semantic_weight * s_score
            combined.append((tmpl.id, round(final, 2)))
    
    combined.sort(key=lambda x: -x[1])
    best_id = combined[0][0] if combined else "generic_game"
    
    return best_id, features, combined


# =====================================================================
# Full Intent Matching (Regex + Semantic + Intent Graph)
# =====================================================================
def match_template_intent(description: str, 
                          regex_weight: float = 0.3,
                          semantic_weight: float = 0.3,
                          intent_weight: float = 0.3,
                          glove_weight: float = 0.2) -> Tuple[str, Dict[str, Feature], List[Tuple[str, float]]]:
    """Most advanced matching: combines regex, semantic, intent graph, and GloVe.
    
    Args:
        description: Natural language app description
        regex_weight: Weight for regex-based feature matching
        semantic_weight: Weight for TF-IDF+BM25+Jaccard
        intent_weight: Weight for Intent Graph (spreading activation)
        glove_weight: Weight for GloVe word embeddings
    
    Returns:
        (best_template_id, features, all_scores)
    
    The 4-layer system:
      1. Regex: Precise keyword/pattern matching
      2. TF-IDF/BM25: Term frequency and document similarity
      3. Intent Graph: Multi-hop semantic reasoning
      4. GloVe: Word embedding similarity (bomb ≈ mine)
    """
    # Normalize weights
    total = regex_weight + semantic_weight + intent_weight + glove_weight
    regex_weight /= total
    semantic_weight /= total
    intent_weight /= total
    glove_weight /= total
    
    # Get regex-based scores
    features = extract_features(description)
    regex_scores: Dict[str, float] = {}
    for tmpl in TEMPLATE_REGISTRY:
        regex_scores[tmpl.id] = score_template(tmpl, features)
    
    # Get scale factor from regex scores
    max_regex = max(regex_scores.values()) if regex_scores else 1
    max_regex = max(max_regex, 10)  # Minimum scale factor
    
    # Get semantic scores (TF-IDF + BM25 + Jaccard)
    semantic_scores: Dict[str, float] = {}
    try:
        from tfidf_matcher import combined_match
        semantic_results = combined_match(description, top_k=len(TEMPLATE_REGISTRY))
        for tid, sim in semantic_results:
            semantic_scores[tid] = sim * max_regex
    except ImportError:
        # Redistribute semantic weight before zeroing (bug fix: was zeroing first)
        old_semantic = semantic_weight
        semantic_weight = 0
        regex_weight += old_semantic / 2
        intent_weight += old_semantic / 2
    
    # Get intent graph scores
    intent_scores: Dict[str, float] = {}
    try:
        from intent_graph import intent_match
        intent_results = intent_match(description)
        
        # Scale intent scores to match regex range
        max_intent = max(intent_results.values()) if intent_results else 1
        for tid, score in intent_results.items():
            intent_scores[tid] = (score / max_intent) * max_regex if max_intent > 0 else 0
    except ImportError:
        # Redistribute intent weight before zeroing (bug fix: was zeroing first)
        old_intent = intent_weight
        intent_weight = 0
        regex_weight += old_intent / 2
        semantic_weight += old_intent / 2
    
    # Get GloVe embedding scores
    glove_scores: Dict[str, float] = {}
    try:
        from glove_matcher import glove_match
        glove_results = glove_match(description, top_k=len(TEMPLATE_REGISTRY))
        for tid, sim in glove_results:
            glove_scores[tid] = sim * max_regex
    except ImportError:
        # Redistribute glove weight before zeroing (bug fix: was zeroing first)
        old_glove = glove_weight
        glove_weight = 0
        intent_weight += old_glove / 3
        semantic_weight += old_glove / 3
        regex_weight += old_glove / 3
    
    # Combine all four scores
    combined: List[Tuple[str, float]] = []
    for tmpl in TEMPLATE_REGISTRY:
        r_score = regex_scores.get(tmpl.id, 0)
        s_score = semantic_scores.get(tmpl.id, 0)
        i_score = intent_scores.get(tmpl.id, 0)
        g_score = glove_scores.get(tmpl.id, 0)
        
        # Skip if regex gave -999 (hard requirement failed)
        if r_score < -100:
            combined.append((tmpl.id, r_score))
        else:
            final = (
                regex_weight * r_score +
                semantic_weight * s_score +
                intent_weight * i_score +
                glove_weight * g_score
            )
            combined.append((tmpl.id, round(final, 2)))
    
    combined.sort(key=lambda x: -x[1])
    best_id = combined[0][0] if combined else "generic_game"
    
    return best_id, features, combined


def explain_intent_match(description: str) -> str:
    """Human-readable explanation of intent-based matching."""
    best_id, features, scores = match_template_intent(description)
    
    lines = [f"Description: \"{description}\"", ""]
    
    # Regex features
    lines.append("Regex Features Extracted:")
    for f in list(features.values())[:5]:
        lines.append(f"  {f}")
    
    # Intent graph activation
    try:
        from intent_graph import intent_explain
        intent_info = intent_explain(description)
        lines.append("")
        lines.append("Intent Graph Activation:")
        lines.append(f"  Initial: {list(intent_info['initial_activation'].keys())[:5]}")
        lines.append(f"  Spread:  {list(intent_info['spread_activation'].keys())[:8]}")
    except ImportError:
        pass
    
    # Final scores
    lines.append("")
    lines.append("Combined Template Scores (top 5):")
    for tid, s in scores[:5]:
        marker = " ← SELECTED" if tid == best_id else ""
        name = tid
        for t in TEMPLATE_REGISTRY:
            if t.id == tid:
                name = t.name
                break
        lines.append(f"  {s:7.2f}  {name} ({tid}){marker}")
    
    return "\n".join(lines)


# =====================================================================
# Neural-Hybrid Matching (Fast Semantic + GloVe Neural + Traditional)
# =====================================================================

# Try to import hybrid router
try:
    from .hybrid_router import route, RouteResult
    HYBRID_ROUTER_AVAILABLE = True
except ImportError:
    try:
        from hybrid_router import route, RouteResult
        HYBRID_ROUTER_AVAILABLE = True
    except ImportError:
        HYBRID_ROUTER_AVAILABLE = False


def match_template_neural(description: str, use_prefs: bool = True, 
                          neural_threshold: float = 0.7) -> Tuple[str, Dict[str, Feature], List[Tuple[str, float]]]:
    """
    Neural-enhanced matching: uses fast hybrid router first, falls back to full scoring.
    
    Pipeline:
    1. Hybrid Router (semantic rules + GloVe neural) - fast, high confidence
    2. If low confidence → full traditional scoring
    3. Combine with user preferences
    
    Args:
        description: Natural language app description
        use_prefs: Apply user preference boosts
        neural_threshold: Minimum confidence from hybrid router to trust (0.0-1.0)
    
    Returns:
        (best_template_id, features, all_scores)
    """
    features = extract_features(description)
    
    # Stage 1: Try hybrid router (fast path)
    if HYBRID_ROUTER_AVAILABLE:
        result = route(description)
        
        # If high confidence from semantic/neural, use it directly
        if result.confidence >= neural_threshold:
            # Build scores list with hybrid result on top
            scores: List[Tuple[str, float]] = []
            for tmpl in TEMPLATE_REGISTRY:
                if tmpl.id == result.template_id:
                    # Hybrid match gets high score
                    s = 30.0 * result.confidence
                else:
                    # Score others normally for transparency
                    s = score_template(tmpl, features)
                
                # Apply user preferences
                if use_prefs and USER_PREFS_ENABLED:
                    s += get_template_boost(tmpl.id)
                
                scores.append((tmpl.id, round(s, 2)))
            
            scores.sort(key=lambda x: -x[1])
            return result.template_id, features, scores
    
    # Stage 2: Fall back to traditional matching
    return match_template(description, use_prefs=use_prefs)
