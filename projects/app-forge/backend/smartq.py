"""SmartQ - Intelligent question engine for app requirements."""

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
