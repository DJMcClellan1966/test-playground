from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Task:
    """A task in the system"""

    id: str
    title: str
    user_id: str
    description: Optional[str] = None
    priority: int = 1
    completed: bool = False

    def validate(self) -> List[str]:
        """Validate invariants."""
        errors = []
        if not (len(self.title) > 0):
            errors.append("title cannot be empty")
        if not (self.priority >= 1):
            errors.append("priority >= 1")
        if not (self.priority <= 5):
            errors.append("priority <= 5")
        return errors