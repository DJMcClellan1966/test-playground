"""SmartQ - Intelligent question engine for app requirements.

Now with Universal Kernel memory integration - remembers past builds
and decisions to make better inferences from the start.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Try to import compliance module for detection
try:
    from compliance import detect_data_collection, get_compliance_questions
    HAS_COMPLIANCE = True
except ImportError:
    HAS_COMPLIANCE = False

# Import kernel memory for learning-based inference
try:
    from kernel_memory import (
        app_memory, suggest_from_memory, recall_answer, 
        remember_answer, remember_build, learn
    )
    HAS_KERNEL_MEMORY = True
except ImportError:
    HAS_KERNEL_MEMORY = False
    app_memory = None

# Import unified agent for semantic inference + template evolution
try:
    from unified_agent import enhance_smartq_inference, unified_infer
    HAS_UNIFIED_AGENT = True
except ImportError:
    HAS_UNIFIED_AGENT = False


@dataclass
class Question:
    """A yes/no question about app requirements."""
    id: str
    text: str
    category: str  # "auth", "data", "realtime", "mobile", "compliance" etc.
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
    # Compliance questions (only asked when personal data detected)
    Question(
        id="compliance_eu",
        text="Will users from the EU access this app?",
        category="compliance",
        depends_on="needs_auth",  # Only ask if auth is needed
    ),
    Question(
        id="compliance_analytics",
        text="Will you use analytics or third-party tracking?",
        category="compliance",
        depends_on="has_data",  # Only ask if data is stored
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
     r"reaction\s*time|reaction\s*test|reflex|speed\s*test|sliding|tile\s*game|"
     r"dice\s*(roll|game)?|tetris|sudoku|minesweeper|cards?|board\s*game",
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

    # --- Compliance / Privacy ---
    (r"eu\b|europe|european|gdpr|germany|france|spain|italy",
     {"compliance_eu": True}),
    (r"uk\b|united\s*kingdom|britain",
     {"compliance_eu": True}),  # UK GDPR similar to EU
    (r"california|ccpa|cpra",
     {"compliance_eu": False}),  # CCPA handled differently, but still privacy-aware
    (r"analytics|tracking|google\s*analytics|gtag|mixpanel|amplitude",
     {"compliance_analytics": True}),
]


def infer_from_description(description: str) -> Dict[str, bool]:
    """
    Auto-answer obvious questions based on description keywords + memory.
    
    Now uses Universal Kernel memory to:
    1. Find similar past builds and learn from their patterns
    2. Recall past decisions for similar contexts
    3. Apply Bayesian confidence from accumulated experience
    """
    desc_lower = description.lower()
    inferred: Dict[str, bool] = {}
    
    # NEW: Check memory for similar builds first
    if HAS_KERNEL_MEMORY and app_memory:
        similar_builds = app_memory.recall_similar_builds(description, n=3)
        
        if similar_builds:
            # Learn from what successful builds had
            feature_votes: Dict[str, int] = {}
            for build in similar_builds:
                if build.success:
                    for feature in build.features:
                        feature_votes[feature] = feature_votes.get(feature, 0) + 1
            
            # Apply high-confidence features
            total = len([b for b in similar_builds if b.success])
            if total > 0:
                for feature, count in feature_votes.items():
                    if count / total >= 0.7:  # 70% threshold
                        # Map feature to question
                        feature_to_question = {
                            'database': 'has_data',
                            'crud': 'has_data',
                            'auth': 'needs_auth',
                            'search': 'search',
                            'export': 'export',
                            'realtime': 'realtime',
                        }
                        if feature in feature_to_question:
                            q_id = feature_to_question[feature]
                            inferred[q_id] = True
    
    # Apply regex rules (first-match wins for conflicts)
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

    # NEW: Enhance with unified agent (semantic + evolution + memory)
    if HAS_UNIFIED_AGENT:
        try:
            inferred = enhance_smartq_inference(description, inferred)
        except Exception:
            pass  # Graceful fallback if agent has issues

    return inferred


def infer_answer_from_memory(description: str, question_id: str, 
                              previous_answers: List[tuple] = None) -> Optional[bool]:
    """
    Try to infer an answer from past decisions.
    
    Returns True/False if confident, None if should ask user.
    """
    if not HAS_KERNEL_MEMORY or not app_memory:
        return None
    
    # Convert question_id to question text for lookup
    question_text = next((q.text for q in QUESTIONS if q.id == question_id), question_id)
    
    result = app_memory.recall_decision(
        description, 
        question_text,
        previous_answers,
        confidence_threshold=0.8  # High threshold for auto-answering
    )
    
    if result:
        answer_text, confidence = result
        # Convert "yes"/"no" to bool
        return answer_text.lower() in ('yes', 'true', '1')


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


# ==========================================================================
# Contextual Question Generation (AI-Free, Learning-Based)
# ==========================================================================

def generate_contextual_questions(description: str, template_id: str, base_answered: Dict[str, bool]) -> List[Question]:
    """
    Generate contextual follow-up questions using intent graph + learned patterns.
    
    This function augments the base QUESTIONS with contextual questions specific
    to the user's description and matched template.
    
    Args:
        description: User's app description
        template_id: Matched template ID (e.g., 'recipe_app', 'crud')
        base_answered: Base answers already inferred
        
    Returns:
        List of additional contextual Question objects
    """
    try:
        from intent_graph import intent_match
        from question_generator import ContextualQuestionGenerator
        
        # Get activated concepts from semantic graph
        activated_concepts = intent_match(description)
        
        # Generate contextual questions
        generator = ContextualQuestionGenerator()
        contextual_qs = generator.generate(description, template_id, activated_concepts)
        
        # Convert to Question objects
        questions = []
        for cq in contextual_qs[:5]:  # Limit to top 5 contextual questions
            # Skip if already covered by base questions or inferred
            if cq['id'] not in [q.id for q in QUESTIONS] and cq['id'] not in base_answered:
                questions.append(Question(
                    id=cq['id'],
                    text=cq['text'],
                    category='contextual',
                    follow_up=True
                ))
        
        return questions
    except ImportError:
        # Fallback if modules not available
        return []


def get_all_questions_with_context(description: str, template_id: str, answered: Dict[str, bool]) -> List[Question]:
    """
    Get all questions (base + contextual) that should be asked.
    
    Args:
        description: User's app description
        template_id: Matched template ID
        answered: Already answered questions
        
    Returns:
        Combined list of base + contextual questions
    """
    # Start with base questions
    all_questions = list(QUESTIONS)
    
    # Add contextual questions
    contextual = generate_contextual_questions(description, template_id, answered)
    all_questions.extend(contextual)
    
    # Filter out already answered
    relevant = []
    for q in all_questions:
        if q.id in answered:
            continue
        if q.depends_on and answered.get(q.depends_on, None) is False:
            continue
        relevant.append(q)
    
    return relevant

