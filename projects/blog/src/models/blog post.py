"""
Blog Post Model

Auto-generated from Personal Website / Portfolio Blueprint blueprint.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4


@dataclass
class Blog Post:
    """
    Blog Post entity.
    
    Generated from blueprint data model.
   *   id: string
   *   title: string
   *   slug: string
   *   content: string (markdown)
   *   excerpt: string
   *   date: date
   *   tags: string[]
   *   published: boolean
    """
    
    # Core fields
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Entity-specific fields
    id: str = ''
    title: str = ''
    slug: str = ''
    content: str = ''
    excerpt: str = ''
    date: datetime = field(default_factory=datetime.now)
    tags: str = ''
    published: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Blog Post":
        """Create instance from dictionary."""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)
    
    def update(self, **kwargs):
        """Update fields and set updated_at timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()


class Blog PostRepository:
    """
    Simple in-memory repository for Blog Post.
    
    Replace with database implementation for production.
    """
    
    def __init__(self):
        self._items: Dict[str, Blog Post] = {}
    
    def create(self, item: Blog Post) -> Blog Post:
        """Add a new item to the repository."""
        self._items[item.id] = item
        return item
    
    def get(self, item_id: str) -> Optional[Blog Post]:
        """Get an item by ID."""
        return self._items.get(item_id)
    
    def get_all(self) -> List[Blog Post]:
        """Get all items."""
        return list(self._items.values())
    
    def update(self, item_id: str, **kwargs) -> Optional[Blog Post]:
        """Update an item by ID."""
        item = self._items.get(item_id)
        if item:
            item.update(**kwargs)
        return item
    
    def delete(self, item_id: str) -> bool:
        """Delete an item by ID."""
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False
    
    def find(self, **criteria) -> List[Blog Post]:
        """Find items matching criteria."""
        results = []
        for item in self._items.values():
            match = True
            for key, value in criteria.items():
                if not hasattr(item, key) or getattr(item, key) != value:
                    match = False
                    break
            if match:
                results.append(item)
        return results


# Singleton repository instance
blog post_repo = Blog PostRepository()
