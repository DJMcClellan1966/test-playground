
# sync.py - CRDT Sync Block

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import json


@dataclass
class VectorClock:
    """Logical vector clock for causality tracking."""
    clocks: Dict[str, int] = field(default_factory=dict)
    
    def increment(self, node_id: str):
        self.clocks[node_id] = self.clocks.get(node_id, 0) + 1
    
    def merge(self, other: "VectorClock"):
        for node, time in other.clocks.items():
            self.clocks[node] = max(self.clocks.get(node, 0), time)
    
    def happens_before(self, other: "VectorClock") -> bool:
        """Returns True if self happened before other."""
        dominated = False
        for node in set(self.clocks.keys()) | set(other.clocks.keys()):
            self_time = self.clocks.get(node, 0)
            other_time = other.clocks.get(node, 0)
            if self_time > other_time:
                return False
            if self_time < other_time:
                dominated = True
        return dominated


@dataclass
class CRDTItem:
    """A CRDT-wrapped item with version tracking."""
    id: str
    data: Dict[str, Any]
    clock: VectorClock
    deleted: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "data": self.data,
            "clock": self.clock.clocks,
            "deleted": self.deleted,
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> "CRDTItem":
        clock = VectorClock(clocks=d.get("clock", {}))
        return cls(
            id=d["id"],
            data=d.get("data", {}),
            clock=clock,
            deleted=d.get("deleted", False),
        )


class CRDTSync:
    """
    CRDT-based sync engine.
    
    Provides automatic conflict resolution using Last-Writer-Wins
    with vector clocks for causality.
    """
    
    def __init__(self, node_id: str, storage):
        self.node_id = node_id
        self.storage = storage
        self.pending_changes: List[CRDTItem] = []
    
    def local_update(self, entity: str, id: str, data: Dict) -> CRDTItem:
        """Record a local change."""
        existing = self.storage.get(entity, id)
        
        # Create or update clock
        if existing and "_clock" in existing:
            clock = VectorClock(clocks=existing["_clock"])
        else:
            clock = VectorClock()
        
        clock.increment(self.node_id)
        
        item = CRDTItem(id=id, data=data, clock=clock)
        
        # Save with clock metadata
        save_data = {**data, "_clock": clock.clocks}
        if existing:
            self.storage.update(entity, id, save_data)
        else:
            self.storage.create(entity, {"id": id, **save_data})
        
        self.pending_changes.append(item)
        return item
    
    def merge_remote(self, entity: str, remote_item: CRDTItem) -> str:
        """
        Merge a remote change.
        
        Returns: "applied", "rejected", or "conflict_resolved"
        """
        local = self.storage.get(entity, remote_item.id)
        
        if not local:
            # New item - just apply
            save_data = {**remote_item.data, "_clock": remote_item.clock.clocks}
            self.storage.create(entity, {"id": remote_item.id, **save_data})
            return "applied"
        
        local_clock = VectorClock(clocks=local.get("_clock", {}))
        
        if remote_item.clock.happens_before(local_clock):
            # Remote is older - reject
            return "rejected"
        
        if local_clock.happens_before(remote_item.clock):
            # Remote is newer - apply
            save_data = {**remote_item.data, "_clock": remote_item.clock.clocks}
            self.storage.update(entity, remote_item.id, save_data)
            return "applied"
        
        # Concurrent - need to merge (LWW based on node_id for determinism)
        local_clock.merge(remote_item.clock)
        
        # Use remote if its node_id is "greater" (deterministic tiebreaker)
        if max(remote_item.clock.clocks.keys()) > max(local_clock.clocks.keys()):
            merged_data = remote_item.data
        else:
            merged_data = {k: v for k, v in local.items() if not k.startswith("_")}
        
        merged_data["_clock"] = local_clock.clocks
        self.storage.update(entity, remote_item.id, merged_data)
        return "conflict_resolved"
    
    def get_pending_changes(self) -> List[Dict]:
        """Get changes to sync to server."""
        changes = [item.to_dict() for item in self.pending_changes]
        self.pending_changes = []
        return changes


# Usage:
# sync = CRDTSync(node_id="client_123", storage=storage)
# sync.local_update("task", "task_1", {"title": "Updated task"})
# changes = sync.get_pending_changes()  # Send these to server
