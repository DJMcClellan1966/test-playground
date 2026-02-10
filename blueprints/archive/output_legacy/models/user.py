from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class User:
    """Application user"""

    id: str
    email: str
    username: str
    password_hash: str

    def validate(self) -> List[str]:
        """Validate invariants."""
        errors = []
        if not (self.email is not None):
            errors.append("email is required")
        if not (len(self.username) >= 3 characters):
            errors.append("username must be at least 3 characters")
        return errors