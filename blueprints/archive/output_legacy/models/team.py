from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Team:
    """A team of users"""

    id: str
    name: str
    member_ids: List[Any]

    def validate(self) -> List[str]:
        """Validate invariants."""
        errors = []
        if not (len(self.name) > 0):
            errors.append("name cannot be empty")
        return errors