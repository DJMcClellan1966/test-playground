"""SmartQ - Intelligent question engine for app requirements."""

import re
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Question:
    """A yes/no question about app requirements."""
    id: str
    text: str
    category: str  # "auth", "data", "realtime", "mobile", etc.
    follow_up: bool = False  # Show only if previous question answered yes
    depends_on: str = ""  # Which question this depends on (e.g., "multi_user")


# Smart questions that guide users toward good architecture
QUESTIONS = [
    Question(
        id="multi_user",
        text="Will multiple users access this app (collaboratively)?",
        category="auth",
    ),
    Question(
        id="needs_auth",
        text="Do users need to log in with passwords?",
        category="auth",
        depends_on="multi_user",
    ),
    Question(
        id="realtime",
        text="Do you need real-time updates (e.g., live notifications)?",
        category="realtime",
    ),
    Question(
        id="has_data",
        text="Will this app store and manage data (not just content)?",
        category="data",
    ),
    Question(
        id="complex_queries",
        text="Will you need complex queries (filtering, sorting, aggregations)?",
        category="data",
        depends_on="has_data",
    ),
    Question(
        id="mobile",
        text="Do you need mobile app support?",
        category="mobile",
    ),
    Question(
        id="search",
        text="Do users need to search/filter content?",
        category="features",
    ),
    Question(
        id="export",
        text="Should users be able to export their data (CSV, PDF, etc.)?",
        category="features",
    ),
    Question(
        id="performance_critical",
        text="Is this performance-critical (e.g., real-time gaming)?",
        category="performance",
    ),
]


# ==========================================================================
# Description inference — auto-answer obvious questions from keywords
# ==========================================================================
INFERENCE_RULES = [
    # --- Data storage (strong yes) + typical personal app defaults ---
    (r"recipe|cook|meal|todo|task|inventory|product|blog|contact|event|calendar|"
     r"note|movie|habit|collection|tracker|bookmark|catalog|library|portfolio|"
     r"budget|expense|journal|diary|crm|warehouse|grocery|shopping|list\s*app|workout|log\b",
     {"has_data": True, "realtime": False, "performance_critical": False}),

    # --- No data / standalone apps (answer ALL questions to skip wizard) ---
    (r"calculator|calc\b|converter|unit\s+convert|bmi|tip\s+calc|mortgage",
     {"has_data": False, "complex_queries": False, "search": False, "export": False,
      "needs_auth": False, "multi_user": False, "realtime": False, "mobile": False,
      "performance_critical": False}),
    (r"game|puzzle|quiz|trivia|tic.?tac|guess|memory|hangman|wordle|snake|pong|"
     r"reaction\s*time|reflex\s*test|speed\s*test|sliding|tile\s*game",
     {"has_data": False, "complex_queries": False, "needs_auth": False, "multi_user": False,
      "realtime": False, "search": False, "export": False, "mobile": False,
      "performance_critical": False}),
    (r"timer|countdown|stopwatch|pomodoro|clock",
     {"has_data": False, "complex_queries": False, "needs_auth": False, "multi_user": False,
      "realtime": False, "search": False, "export": False, "mobile": False,
      "performance_critical": False}),

    # --- Component-assembler apps (generators, tools, creative) ---
    (r"password\s*(gen|creat|mak|random)|color\s*(palette|gen|pick)|palette\s*gen|"
     r"dice\s*(roll|throw)|roll\s*dice|coin\s*(flip|toss)|flip\s*coin|"
     r"quote\s*(gen|random|daily)|random\s*quote|lorem\s*ipsum|placeholder\s*text|"
     r"name\s*gen|random\s*name|typing\s*(speed|test)|speed\s*typ|wpm\s*test|"
     r"flashcard|study\s*card|kanban|task\s*board|project\s*board|"
     r"draw(ing)?\s*(app|tool|pad)?|whiteboard|sketch|paint|doodle|"
     r"(markdown|text|note|code)\s*(editor|writer|pad)|notepad|scratchpad|"
     r"chat\s*(room|app|interface)|messaging|messenger",
     {"has_data": False, "complex_queries": False, "needs_auth": False, "multi_user": False,
      "realtime": False, "search": False, "export": False, "mobile": False,
      "performance_critical": False}),

    # --- Multi-user / auth ---
    (r"team|collaborat|share\s+(with|between)|multi.?user|group|organization|members|workspace",
     {"multi_user": True}),
    (r"login|password|account|register|sign.?up|auth\b|secure\s+access",
     {"multi_user": True, "needs_auth": True}),

    # --- Single-user (personal indicators) ---
    (r"personal|my\s+own|just\s+(for\s+)?me|solo|private|individual|"
     r"where\s+i\s+can|i\s+want\s+(to|a)\b|for\s+myself|i\s+can\s+\w+",
     {"multi_user": False}),

    # --- Collections imply search, single purpose apps don't need export ---
    (r"collection|browse|catalog|library|bookmark",
     {"search": True}),

    # --- Realtime ---
    (r"real.?time|live\s+update|chat\b|notification|instant|socket|streaming",
     {"realtime": True}),

    # --- Search ---
    (r"search|filter|find\b|lookup|browse",
     {"search": True}),

    # --- Export ---
    (r"export|download|csv|pdf\b|report|backup",
     {"export": True}),

    # --- Mobile ---
    (r"mobile|phone|android|ios\b",
     {"mobile": True}),

    # --- Performance ---
    (r"performance.?critical|competitive|real.?time\s+gaming",
     {"performance_critical": True}),
]


def infer_from_description(description: str) -> Dict[str, bool]:
    """Auto-answer obvious questions based on description keywords."""
    desc_lower = description.lower()
    inferred: Dict[str, bool] = {}

    for pattern, answers in INFERENCE_RULES:
        if re.search(pattern, desc_lower):
            for qid, val in answers.items():
                if qid not in inferred:          # first-match wins for conflicts
                    inferred[qid] = val

    # Apply dependency logic
    if inferred.get("multi_user") is False:
        inferred.setdefault("needs_auth", False)
    if inferred.get("has_data") is False:
        inferred.setdefault("complex_queries", False)

    return inferred


def get_relevant_questions(answered: Dict[str, bool]) -> List[Question]:
    """Get questions that should be asked next based on answers."""
    relevant = []
    for q in QUESTIONS:
        # Skip if already answered
        if q.id in answered:
            continue
        
        # Skip if depends on a question that wasn't asked yet
        if q.depends_on and answered.get(q.depends_on, None) is False:
            continue
        
        relevant.append(q)
    
    return relevant


def total_relevant_count(answered: Dict[str, bool]) -> int:
    """Total questions that will be asked (answered + remaining). #10 fix."""
    count = 0
    for q in QUESTIONS:
        if q.depends_on and answered.get(q.depends_on, None) is False:
            continue
        count += 1
    return count


def get_next_question(answered: Dict[str, bool]) -> Question:
    """Get the very next question to ask."""
    relevant = get_relevant_questions(answered)
    return relevant[0] if relevant else None


def is_complete(answered: Dict[str, bool]) -> bool:
    """Check if we've asked all relevant questions."""
    return len(get_relevant_questions(answered)) == 0


class Profile:
    """User's app requirements profile."""
    
    def __init__(self, description: str, answers: Dict[str, bool] = None):
        self.description = description
        self.answers = answers or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "answers": self.answers,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Profile':
        return Profile(data["description"], data.get("answers", {}))
