from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


@dataclass
class User:
    """A user in the system"""

    id: str
    email: str
    name: str
    def validate(self) -> List[str]:
        """Validate all invariants."""
        errors = []
        return errors