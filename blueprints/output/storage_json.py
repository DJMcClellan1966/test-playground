
# storage.py - JSON File Storage Block

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class JSONStorage:
    """Simple JSON file-based storage."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, List[Dict]] = {}
    
    def _get_path(self, entity: str) -> Path:
        return self.data_dir / f"{entity}.json"
    
    def _load(self, entity: str) -> List[Dict]:
        if entity in self._cache:
            return self._cache[entity]
        
        path = self._get_path(entity)
        if path.exists():
            with open(path, "r") as f:
                self._cache[entity] = json.load(f)
        else:
            self._cache[entity] = []
        return self._cache[entity]
    
    def _save(self, entity: str):
        with open(self._get_path(entity), "w") as f:
            json.dump(self._cache.get(entity, []), f, indent=2, default=str)
    
    def _next_id(self, entity: str) -> str:
        items = self._load(entity)
        return str(len(items) + 1).zfill(4)
    
    # CRUD Operations
    
    def create(self, entity: str, data: Dict) -> Dict:
        items = self._load(entity)
        now = datetime.now().isoformat()
        
        item = {
            "id": self._next_id(entity),
            "created_at": now,
            "updated_at": now,
            **data
        }
        items.append(item)
        self._save(entity)
        return item
    
    def get(self, entity: str, id: str) -> Optional[Dict]:
        items = self._load(entity)
        for item in items:
            if item.get("id") == id:
                return item
        return None
    
    def list(self, entity: str, **filters) -> List[Dict]:
        items = self._load(entity)
        if not filters:
            return items
        
        result = []
        for item in items:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                result.append(item)
        return result
    
    def update(self, entity: str, id: str, data: Dict) -> Optional[Dict]:
        items = self._load(entity)
        for item in items:
            if item.get("id") == id:
                item.update(data)
                item["updated_at"] = datetime.now().isoformat()
                self._save(entity)
                return item
        return None
    
    def delete(self, entity: str, id: str) -> bool:
        items = self._load(entity)
        original_len = len(items)
        self._cache[entity] = [i for i in items if i.get("id") != id]
        if len(self._cache[entity]) < original_len:
            self._save(entity)
            return True
        return False
    
    def find_by_email(self, email: str) -> Optional[Dict]:
        """Helper for auth - find user by email."""
        users = self._load("user")
        for user in users:
            if user.get("email") == email:
                return user
        return None


# Singleton instance
storage = JSONStorage()
