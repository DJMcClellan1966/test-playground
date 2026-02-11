"""Build Memory — Persistent database for app build history.

Two stores:
  - GOOD: Accepted apps with descriptions, edits, revisions
  - BAD:  Rejected/failed apps with reasons

This creates a learning database that can:
  - Suggest features based on past successful builds
  - Avoid patterns that led to rejections
  - Track revision history for iterative improvement
  - Provide analytics on what works
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path

# Database location
DB_PATH = Path(__file__).parent / "data" / "build_memory.db"


@dataclass
class BuildRecord:
    """A single app build record."""
    id: Optional[int] = None
    description: str = ""
    template_used: str = ""
    components: List[str] = None  # List of component IDs used
    features: Dict[str, Any] = None  # Extracted features
    answers: Dict[str, bool] = None  # User answers to questions
    generated_code_hash: str = ""  # Hash of generated code
    status: str = "pending"  # pending, accepted, rejected, deleted
    rejection_reason: str = ""  # Why it was rejected/deleted
    created_at: str = ""
    updated_at: str = ""
    revision: int = 1
    parent_id: Optional[int] = None  # For tracking revisions
    user_edits: str = ""  # JSON of user modifications
    
    def __post_init__(self):
        if self.components is None:
            self.components = []
        if self.features is None:
            self.features = {}
        if self.answers is None:
            self.answers = {}
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class BuildMemory:
    """Manages the build history database."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS builds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    template_used TEXT,
                    components TEXT,  -- JSON array
                    features TEXT,    -- JSON object
                    answers TEXT,     -- JSON object
                    generated_code_hash TEXT,
                    status TEXT DEFAULT 'pending',
                    rejection_reason TEXT DEFAULT '',
                    created_at TEXT,
                    updated_at TEXT,
                    revision INTEGER DEFAULT 1,
                    parent_id INTEGER,
                    user_edits TEXT DEFAULT '',
                    FOREIGN KEY (parent_id) REFERENCES builds(id)
                )
            """)
            
            # Index for fast lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON builds(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_template ON builds(template_used)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_parent ON builds(parent_id)")
            
            # Feature patterns table — tracks which features lead to success
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feature_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_key TEXT NOT NULL,
                    feature_value TEXT,
                    template_used TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    UNIQUE(feature_key, feature_value, template_used)
                )
            """)
            
            # Component combinations — tracks which components work well together
            conn.execute("""
                CREATE TABLE IF NOT EXISTS component_combos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    combo_hash TEXT UNIQUE,  -- Hash of sorted component list
                    components TEXT,         -- JSON array
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    avg_revisions REAL DEFAULT 1.0,
                    last_used TEXT
                )
            """)
            
            conn.commit()
    
    def _record_to_row(self, record: BuildRecord) -> tuple:
        """Convert BuildRecord to database row."""
        return (
            record.description,
            record.template_used,
            json.dumps(record.components),
            json.dumps(record.features),
            json.dumps(record.answers),
            record.generated_code_hash,
            record.status,
            record.rejection_reason,
            record.created_at,
            record.updated_at,
            record.revision,
            record.parent_id,
            record.user_edits,
        )
    
    def _row_to_record(self, row: tuple) -> BuildRecord:
        """Convert database row to BuildRecord."""
        return BuildRecord(
            id=row[0],
            description=row[1],
            template_used=row[2],
            components=json.loads(row[3]) if row[3] else [],
            features=json.loads(row[4]) if row[4] else {},
            answers=json.loads(row[5]) if row[5] else {},
            generated_code_hash=row[6],
            status=row[7],
            rejection_reason=row[8],
            created_at=row[9],
            updated_at=row[10],
            revision=row[11],
            parent_id=row[12],
            user_edits=row[13] or "",
        )
    
    # =========================================================================
    # CRUD Operations
    # =========================================================================
    
    def save_build(self, record: BuildRecord) -> int:
        """Save a new build record. Returns the new ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO builds (
                    description, template_used, components, features, answers,
                    generated_code_hash, status, rejection_reason, created_at,
                    updated_at, revision, parent_id, user_edits
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, self._record_to_row(record))
            conn.commit()
            return cursor.lastrowid
    
    def get_build(self, build_id: int) -> Optional[BuildRecord]:
        """Get a build by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM builds WHERE id = ?", (build_id,))
            row = cursor.fetchone()
            return self._row_to_record(row) if row else None
    
    def update_build(self, record: BuildRecord):
        """Update an existing build."""
        record.updated_at = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE builds SET
                    description = ?, template_used = ?, components = ?, features = ?,
                    answers = ?, generated_code_hash = ?, status = ?, rejection_reason = ?,
                    created_at = ?, updated_at = ?, revision = ?, parent_id = ?, user_edits = ?
                WHERE id = ?
            """, (*self._record_to_row(record), record.id))
            conn.commit()
    
    # =========================================================================
    # Good Store — Accepted Apps
    # =========================================================================
    
    def accept_build(self, build_id: int) -> BuildRecord:
        """Mark a build as accepted (move to Good store)."""
        record = self.get_build(build_id)
        if record:
            record.status = "accepted"
            record.updated_at = datetime.utcnow().isoformat()
            self.update_build(record)
            self._update_patterns(record, success=True)
        return record
    
    def get_good_builds(self, limit: int = 100) -> List[BuildRecord]:
        """Get all accepted builds."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM builds WHERE status = 'accepted'
                ORDER BY updated_at DESC LIMIT ?
            """, (limit,))
            return [self._row_to_record(row) for row in cursor.fetchall()]
    
    def get_similar_good_builds(self, description: str, limit: int = 5) -> List[BuildRecord]:
        """Find accepted builds similar to a description (simple keyword match)."""
        keywords = set(description.lower().split())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM builds WHERE status = 'accepted'
            """)
            scored = []
            for row in cursor.fetchall():
                record = self._row_to_record(row)
                desc_words = set(record.description.lower().split())
                overlap = len(keywords & desc_words)
                if overlap > 0:
                    scored.append((overlap, record))
            scored.sort(key=lambda x: -x[0])
            return [r for _, r in scored[:limit]]
    
    # =========================================================================
    # Bad Store — Rejected/Deleted Apps
    # =========================================================================
    
    def reject_build(self, build_id: int, reason: str) -> BuildRecord:
        """Mark a build as rejected (move to Bad store) with reason."""
        record = self.get_build(build_id)
        if record:
            record.status = "rejected"
            record.rejection_reason = reason
            record.updated_at = datetime.utcnow().isoformat()
            self.update_build(record)
            self._update_patterns(record, success=False)
        return record
    
    def delete_build(self, build_id: int, reason: str) -> BuildRecord:
        """Mark a build as deleted with reason (soft delete to Bad store)."""
        record = self.get_build(build_id)
        if record:
            record.status = "deleted"
            record.rejection_reason = reason
            record.updated_at = datetime.utcnow().isoformat()
            self.update_build(record)
            self._update_patterns(record, success=False)
        return record
    
    def get_bad_builds(self, limit: int = 100) -> List[BuildRecord]:
        """Get all rejected/deleted builds."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM builds WHERE status IN ('rejected', 'deleted')
                ORDER BY updated_at DESC LIMIT ?
            """, (limit,))
            return [self._row_to_record(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # Revisions
    # =========================================================================
    
    def create_revision(self, parent_id: int, new_description: str = None,
                        user_edits: str = "") -> BuildRecord:
        """Create a new revision of an existing build."""
        parent = self.get_build(parent_id)
        if not parent:
            return None
        
        new_record = BuildRecord(
            description=new_description or parent.description,
            template_used=parent.template_used,
            components=parent.components.copy(),
            features=parent.features.copy(),
            answers=parent.answers.copy(),
            status="pending",
            revision=parent.revision + 1,
            parent_id=parent_id,
            user_edits=user_edits,
        )
        new_id = self.save_build(new_record)
        new_record.id = new_id
        return new_record
    
    def get_revision_chain(self, build_id: int) -> List[BuildRecord]:
        """Get the full revision history of a build."""
        chain = []
        current = self.get_build(build_id)
        while current:
            chain.append(current)
            current = self.get_build(current.parent_id) if current.parent_id else None
        chain.reverse()  # Oldest first
        return chain
    
    # =========================================================================
    # Pattern Learning
    # =========================================================================
    
    def _update_patterns(self, record: BuildRecord, success: bool):
        """Update feature and component patterns based on build outcome."""
        now = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Update feature patterns
            for key, value in record.features.items():
                val_str = str(value)
                conn.execute("""
                    INSERT INTO feature_patterns (feature_key, feature_value, template_used,
                        success_count, failure_count, last_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(feature_key, feature_value, template_used) DO UPDATE SET
                        success_count = success_count + ?,
                        failure_count = failure_count + ?,
                        last_used = ?
                """, (
                    key, val_str, record.template_used,
                    1 if success else 0, 0 if success else 1, now,
                    1 if success else 0, 0 if success else 1, now
                ))
            
            # Update component combinations
            if record.components:
                combo = sorted(record.components)
                combo_hash = hashlib.md5(json.dumps(combo).encode()).hexdigest()[:16]
                conn.execute("""
                    INSERT INTO component_combos (combo_hash, components,
                        success_count, failure_count, last_used)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(combo_hash) DO UPDATE SET
                        success_count = success_count + ?,
                        failure_count = failure_count + ?,
                        last_used = ?
                """, (
                    combo_hash, json.dumps(combo),
                    1 if success else 0, 0 if success else 1, now,
                    1 if success else 0, 0 if success else 1, now
                ))
            
            conn.commit()
    
    def get_feature_success_rate(self, feature_key: str, feature_value: str = None) -> float:
        """Get the success rate for a feature (0.0 to 1.0)."""
        with sqlite3.connect(self.db_path) as conn:
            if feature_value:
                cursor = conn.execute("""
                    SELECT SUM(success_count), SUM(failure_count)
                    FROM feature_patterns
                    WHERE feature_key = ? AND feature_value = ?
                """, (feature_key, str(feature_value)))
            else:
                cursor = conn.execute("""
                    SELECT SUM(success_count), SUM(failure_count)
                    FROM feature_patterns
                    WHERE feature_key = ?
                """, (feature_key,))
            
            row = cursor.fetchone()
            if row and (row[0] or row[1]):
                success = row[0] or 0
                failure = row[1] or 0
                total = success + failure
                return success / total if total > 0 else 0.5
            return 0.5  # Unknown → neutral
    
    def get_recommended_components(self, template: str, limit: int = 5) -> List[str]:
        """Get components that have high success rates with a template."""
        with sqlite3.connect(self.db_path) as conn:
            # Get feature patterns associated with this template
            cursor = conn.execute("""
                SELECT feature_key, feature_value, success_count, failure_count
                FROM feature_patterns
                WHERE template_used = ? AND success_count > 0
                ORDER BY (success_count * 1.0 / (success_count + failure_count + 1)) DESC
                LIMIT ?
            """, (template, limit))
            
            recommendations = []
            for row in cursor.fetchall():
                rate = row[2] / (row[2] + row[3] + 1)
                recommendations.append(f"{row[0]}={row[1]} ({rate:.0%} success)")
            return recommendations
    
    def get_patterns_to_avoid(self, limit: int = 10) -> List[Dict]:
        """Get patterns that frequently lead to rejection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT feature_key, feature_value, template_used,
                       success_count, failure_count
                FROM feature_patterns
                WHERE failure_count > success_count
                ORDER BY failure_count DESC
                LIMIT ?
            """, (limit,))
            
            return [{
                "feature": f"{row[0]}={row[1]}",
                "template": row[2],
                "failures": row[4],
                "successes": row[3],
            } for row in cursor.fetchall()]
    
    # =========================================================================
    # Analytics
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall build statistics."""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Counts by status
            cursor = conn.execute("""
                SELECT status, COUNT(*) FROM builds GROUP BY status
            """)
            for row in cursor.fetchall():
                stats[f"{row[0]}_count"] = row[1]
            
            # Most used templates
            cursor = conn.execute("""
                SELECT template_used, COUNT(*) as cnt
                FROM builds WHERE status = 'accepted'
                GROUP BY template_used
                ORDER BY cnt DESC LIMIT 5
            """)
            stats["top_templates"] = [
                {"template": row[0], "count": row[1]} for row in cursor.fetchall()
            ]
            
            # Average revisions for accepted builds
            cursor = conn.execute("""
                SELECT AVG(revision) FROM builds WHERE status = 'accepted'
            """)
            row = cursor.fetchone()
            stats["avg_revisions"] = round(row[0], 2) if row[0] else 1.0
            
            return stats
    
    def get_recent(self, limit: int = 50) -> List[BuildRecord]:
        """Get recent builds (excluding deleted)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM builds WHERE status != 'deleted'
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            return [self._row_to_record(row) for row in cursor.fetchall()]
    
    def save(self, record: BuildRecord) -> int:
        """Alias for save_build."""
        return self.save_build(record)
    
    def mark_status(self, build_id: int, status: str, reason: str = "") -> BuildRecord:
        """Mark a build with a specific status."""
        record = self.get_build(build_id)
        if record:
            record.status = status
            if reason:
                record.rejection_reason = reason
            record.updated_at = datetime.utcnow().isoformat()
            self.update_build(record)
        return record


# Singleton instance
memory = BuildMemory()
