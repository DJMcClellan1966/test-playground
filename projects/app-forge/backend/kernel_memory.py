"""
Kernel Memory Bridge - Connects Universal Kernel's memory to App Forge
=======================================================================

This module bridges the mathematical memory system from Universal Kernel
(projects/universal-kernel) into App Forge, giving apps:

1. BUILD MEMORY - Remember successful builds and their patterns
2. USER MEMORY - Learn user preferences over time  
3. DECISION MEMORY - Remember answers to skip redundant questions
4. TEMPLATE MEMORY - Associate descriptions → templates via experience

Unlike cloud AI agents that forget everything between sessions,
this memory persists and improves decision-making from the start.

Author: App Forge Project
"""

from __future__ import annotations
import sys
import os
import json
import time
import hashlib
import sqlite3
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

# Add universal-kernel to path
KERNEL_PATH = Path(__file__).parent.parent.parent / 'universal-kernel'
if str(KERNEL_PATH) not in sys.path:
    sys.path.insert(0, str(KERNEL_PATH))

# Import Universal Kernel's memory system
try:
    from kernel import MemorySystem, Memory, compression_distance, bayesian_update  # type: ignore
    KERNEL_AVAILABLE = True
except ImportError:
    # Fallback if kernel not available
    KERNEL_AVAILABLE = False
    MemorySystem = None
    Memory = None
    
    def compression_distance(a: str, b: str) -> float:
        """Fallback NCD implementation"""
        import zlib
        def C(s: str) -> int:
            return len(zlib.compress(s.encode()))
        ca, cb = C(a), C(b)
        cab = C(a + b)
        return (cab - min(ca, cb)) / max(ca, cb, 1)
    
    def bayesian_update(prior: float, likelihood: float, evidence: float) -> float:
        if evidence == 0:
            return prior
        return (likelihood * prior) / evidence


# =============================================================================
# DATABASE PERSISTENCE
# =============================================================================

DB_PATH = Path(__file__).parent / 'data' / 'kernel_memory.db'


def init_db():
    """Initialize the memory database"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # Build memories: description → template → success
    c.execute('''CREATE TABLE IF NOT EXISTS build_memories (
        id TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        template_id TEXT,
        features TEXT,  -- JSON list
        success INTEGER DEFAULT 1,
        timestamp REAL,
        access_count INTEGER DEFAULT 0
    )''')
    
    # Decision memories: question_hash → answer
    c.execute('''CREATE TABLE IF NOT EXISTS decision_memories (
        id TEXT PRIMARY KEY,
        context_hash TEXT NOT NULL,  -- Hash of description + previous answers
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        timestamp REAL,
        times_used INTEGER DEFAULT 1
    )''')
    
    # User preferences: learned patterns
    c.execute('''CREATE TABLE IF NOT EXISTS user_preferences (
        id TEXT PRIMARY KEY,
        preference_type TEXT NOT NULL,  -- 'framework', 'feature', 'style'
        value TEXT NOT NULL,
        weight REAL DEFAULT 1.0,
        evidence_count INTEGER DEFAULT 1,
        timestamp REAL
    )''')
    
    # Template associations: description patterns → templates
    c.execute('''CREATE TABLE IF NOT EXISTS template_associations (
        id TEXT PRIMARY KEY,
        pattern TEXT NOT NULL,  -- Key phrases from description
        template_id TEXT NOT NULL,
        strength REAL DEFAULT 1.0,
        times_seen INTEGER DEFAULT 1,
        timestamp REAL
    )''')
    
    conn.commit()
    conn.close()


# Initialize on import
init_db()


# =============================================================================
# APP FORGE MEMORY - Extends Universal Kernel Memory
# =============================================================================

@dataclass
class BuildExperience:
    """A remembered build with outcome"""
    description: str
    template_id: str
    features: List[str]
    success: bool
    timestamp: float
    
    def to_dict(self) -> dict:
        return {
            'description': self.description,
            'template_id': self.template_id,
            'features': self.features,
            'success': self.success,
            'timestamp': self.timestamp
        }


@dataclass  
class DecisionMemory:
    """A remembered Q&A decision"""
    context_hash: str
    question: str
    answer: str
    confidence: float = 1.0
    times_used: int = 1


class AppForgeMemory:
    """
    Memory system for App Forge that learns from builds.
    
    Integrates with Universal Kernel's MemorySystem for:
    - Compression-based similarity (find similar past builds)
    - Bayesian confidence updates (increase confidence with repeated success)
    - Working memory for current session context
    - Episodic memory for build history
    - Semantic memory for learned rules
    """
    
    def __init__(self):
        # Use Universal Kernel's memory if available
        if KERNEL_AVAILABLE:
            self.kernel_memory = MemorySystem()
        else:
            self.kernel_memory = None
        
        # Current session state
        self.current_description: str = ""
        self.current_inferences: Dict[str, Any] = {}
        self.session_decisions: List[Tuple[str, str]] = []
        
        # Load from database
        self._load_from_db()
    
    def _load_from_db(self):
        """Load memories from SQLite into kernel memory"""
        if not DB_PATH.exists():
            return
            
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        # Load build memories into semantic memory
        c.execute('SELECT description, template_id, features, success FROM build_memories')
        for row in c.fetchall():
            desc, template_id, features_json, success = row
            if self.kernel_memory:
                self.kernel_memory.store_semantic(
                    f"build:{hashlib.md5(desc.encode()).hexdigest()[:8]}",
                    {
                        'description': desc,
                        'template_id': template_id,
                        'features': json.loads(features_json) if features_json else [],
                        'success': bool(success)
                    }
                )
        
        conn.close()
    
    def _hash_context(self, description: str, answers: List[Tuple[str, str]] = None) -> str:
        """Create a context hash for decision memory lookup"""
        context = description.lower()
        if answers:
            context += "|" + "|".join(f"{q}:{a}" for q, a in sorted(answers))
        return hashlib.md5(context.encode()).hexdigest()[:16]
    
    # =========================================================================
    # BUILD MEMORY
    # =========================================================================
    
    def remember_build(self, description: str, template_id: str, 
                       features: List[str], success: bool = True):
        """
        Remember a build experience for future decisions.
        
        This is what makes App Forge learn - each build becomes
        training data for better template selection.
        """
        build = BuildExperience(
            description=description,
            template_id=template_id,
            features=features,
            success=success,
            timestamp=time.time()
        )
        
        # Store in kernel memory (working → episodic)
        if self.kernel_memory:
            self.kernel_memory.store_episodic(
                build.to_dict(),
                associations={template_id, *features}
            )
        
        # Persist to database
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        build_id = hashlib.md5(f"{description}{time.time()}".encode()).hexdigest()[:8]
        
        c.execute('''INSERT OR REPLACE INTO build_memories 
                     (id, description, template_id, features, success, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (build_id, description, template_id, json.dumps(features), 
                   1 if success else 0, time.time()))
        
        # Update template associations
        key_phrases = self._extract_key_phrases(description)
        for phrase in key_phrases:
            c.execute('''INSERT INTO template_associations 
                         (id, pattern, template_id, strength, times_seen, timestamp)
                         VALUES (?, ?, ?, 1.0, 1, ?)
                         ON CONFLICT(id) DO UPDATE SET
                         times_seen = times_seen + 1,
                         strength = strength + 0.1,
                         timestamp = ?''',
                      (f"{phrase}:{template_id}", phrase, template_id, 
                       time.time(), time.time()))
        
        conn.commit()
        conn.close()
    
    def recall_similar_builds(self, description: str, n: int = 5) -> List[BuildExperience]:
        """
        Find similar past builds using compression distance.
        
        This is how the agent "remembers" - instead of starting fresh,
        it uses past experience to make better decisions.
        """
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        c.execute('SELECT description, template_id, features, success, timestamp FROM build_memories')
        all_builds = c.fetchall()
        conn.close()
        
        if not all_builds:
            return []
        
        # Calculate similarity using compression distance
        similarities = []
        for row in all_builds:
            desc, template_id, features_json, success, ts = row
            similarity = 1.0 - compression_distance(description.lower(), desc.lower())
            if similarity > 0.3:  # Threshold for relevance
                similarities.append((BuildExperience(
                    description=desc,
                    template_id=template_id,
                    features=json.loads(features_json) if features_json else [],
                    success=bool(success),
                    timestamp=ts
                ), similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [b for b, _ in similarities[:n]]
    
    def suggest_template(self, description: str) -> Optional[Tuple[str, float]]:
        """
        Suggest a template based on memory.
        
        Returns (template_id, confidence) or None if no memory.
        This is "intelligent default" - the agent already has an opinion.
        """
        similar = self.recall_similar_builds(description, n=3)
        
        if not similar:
            return None
        
        # Vote by successful builds
        votes: Dict[str, float] = {}
        for build in similar:
            if build.success:
                if build.template_id not in votes:
                    votes[build.template_id] = 0
                votes[build.template_id] += 1.0
        
        if not votes:
            return None
        
        # Best template with confidence
        best = max(votes.items(), key=lambda x: x[1])
        confidence = best[1] / len(similar)
        
        return (best[0], confidence)
    
    # =========================================================================
    # DECISION MEMORY
    # =========================================================================
    
    def remember_decision(self, description: str, question: str, answer: str,
                          previous_answers: List[Tuple[str, str]] = None):
        """
        Remember a Q&A decision for auto-answering similar questions.
        
        This is how the agent learns to skip questions - if user always
        says "yes" to auth for social apps, suggest it automatically.
        """
        context_hash = self._hash_context(description, previous_answers)
        
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        decision_id = f"{context_hash}:{hashlib.md5(question.encode()).hexdigest()[:8]}"
        
        c.execute('''INSERT INTO decision_memories 
                     (id, context_hash, question, answer, confidence, timestamp, times_used)
                     VALUES (?, ?, ?, ?, 1.0, ?, 1)
                     ON CONFLICT(id) DO UPDATE SET
                     times_used = times_used + 1,
                     confidence = MIN(confidence + 0.1, 1.0),
                     answer = ?,
                     timestamp = ?''',
                  (decision_id, context_hash, question, answer, time.time(), 
                   answer, time.time()))
        
        conn.commit()
        conn.close()
        
        # Track in session
        self.session_decisions.append((question, answer))
    
    def recall_decision(self, description: str, question: str,
                        previous_answers: List[Tuple[str, str]] = None,
                        confidence_threshold: float = 0.7) -> Optional[Tuple[str, float]]:
        """
        Try to recall a previous decision for this context.
        
        Returns (answer, confidence) if memory exists and confidence > threshold.
        This is how questions are skipped - "I remember you always pick this."
        """
        context_hash = self._hash_context(description, previous_answers)
        
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        # Exact context match
        c.execute('''SELECT answer, confidence, times_used 
                     FROM decision_memories 
                     WHERE context_hash = ? AND question = ?''',
                  (context_hash, question))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            answer, confidence, times_used = row
            # Boost confidence with usage
            effective_confidence = min(confidence + (times_used * 0.05), 1.0)
            if effective_confidence >= confidence_threshold:
                return (answer, effective_confidence)
        
        return None
    
    # =========================================================================
    # USER PREFERENCE LEARNING
    # =========================================================================
    
    def learn_preference(self, pref_type: str, value: str):
        """
        Learn a user preference from observed behavior.
        
        Types: 'framework', 'feature', 'style', 'domain'
        """
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        pref_id = f"{pref_type}:{value}"
        
        c.execute('''INSERT INTO user_preferences 
                     (id, preference_type, value, weight, evidence_count, timestamp)
                     VALUES (?, ?, ?, 1.0, 1, ?)
                     ON CONFLICT(id) DO UPDATE SET
                     evidence_count = evidence_count + 1,
                     weight = MIN(weight + 0.1, 2.0),
                     timestamp = ?''',
                  (pref_id, pref_type, value, time.time(), time.time()))
        
        conn.commit()
        conn.close()
    
    def get_preferences(self, pref_type: str = None) -> List[Tuple[str, float]]:
        """
        Get learned preferences, optionally filtered by type.
        Returns (value, weight) pairs sorted by weight.
        """
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        if pref_type:
            c.execute('''SELECT value, weight FROM user_preferences 
                         WHERE preference_type = ? ORDER BY weight DESC''',
                      (pref_type,))
        else:
            c.execute('''SELECT value, weight FROM user_preferences 
                         ORDER BY weight DESC''')
        
        results = c.fetchall()
        conn.close()
        
        return results
    
    # =========================================================================
    # TEMPLATE ASSOCIATIONS
    # =========================================================================
    
    def boost_template(self, description: str, template_id: str):
        """
        Increase association between description patterns and template.
        Called when a build is accepted.
        """
        key_phrases = self._extract_key_phrases(description)
        
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        for phrase in key_phrases:
            c.execute('''UPDATE template_associations 
                         SET strength = strength + 0.2, times_seen = times_seen + 1
                         WHERE pattern = ? AND template_id = ?''',
                      (phrase, template_id))
        
        conn.commit()
        conn.close()
    
    def get_template_suggestions(self, description: str) -> List[Tuple[str, float]]:
        """
        Get template suggestions based on learned associations.
        Returns (template_id, score) pairs.
        """
        key_phrases = self._extract_key_phrases(description)
        
        if not key_phrases:
            return []
        
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        # Find associations for any phrase
        placeholders = ','.join('?' * len(key_phrases))
        c.execute(f'''SELECT template_id, SUM(strength * times_seen) as score
                      FROM template_associations 
                      WHERE pattern IN ({placeholders})
                      GROUP BY template_id
                      ORDER BY score DESC
                      LIMIT 5''',
                  key_phrases)
        
        results = c.fetchall()
        conn.close()
        
        return results
    
    def _extract_key_phrases(self, description: str) -> List[str]:
        """Extract key phrases for association"""
        import re
        
        # Normalize
        text = description.lower()
        
        # Remove stopwords, keep nouns/verbs
        stopwords = {'a', 'an', 'the', 'with', 'for', 'to', 'is', 'are', 'that', 
                     'this', 'and', 'or', 'i', 'want', 'need', 'can', 'where', 'app'}
        words = re.findall(r'\b[a-z]{3,}\b', text)
        key_words = [w for w in words if w not in stopwords]
        
        # Create bigrams too
        bigrams = [f"{key_words[i]}_{key_words[i+1]}" 
                   for i in range(len(key_words) - 1)]
        
        return key_words + bigrams
    
    # =========================================================================
    # MEMORY STATS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM build_memories')
        builds = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM decision_memories')
        decisions = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM user_preferences')
        prefs = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM template_associations')
        associations = c.fetchone()[0]
        
        c.execute('SELECT AVG(success) FROM build_memories')
        success_rate = c.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'build_memories': builds,
            'decision_memories': decisions,
            'user_preferences': prefs,
            'template_associations': associations,
            'success_rate': success_rate,
            'kernel_available': KERNEL_AVAILABLE
        }
    
    def clear_all(self):
        """Clear all memories (for testing)"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('DELETE FROM build_memories')
        c.execute('DELETE FROM decision_memories')
        c.execute('DELETE FROM user_preferences')
        c.execute('DELETE FROM template_associations')
        conn.commit()
        conn.close()
        
        if self.kernel_memory:
            self.kernel_memory = MemorySystem()


# =============================================================================
# GLOBAL INSTANCE - Use this in App Forge
# =============================================================================

# Global memory instance for the application
app_memory = AppForgeMemory()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def remember_build(description: str, template_id: str, features: List[str], 
                   success: bool = True):
    """Shortcut to remember a build"""
    app_memory.remember_build(description, template_id, features, success)


def suggest_from_memory(description: str) -> Optional[Tuple[str, float]]:
    """Shortcut to get template suggestion"""
    return app_memory.suggest_template(description)


def remember_answer(description: str, question: str, answer: str):
    """Shortcut to remember a Q&A decision"""
    app_memory.remember_decision(description, question, answer)


def recall_answer(description: str, question: str) -> Optional[str]:
    """Shortcut to recall a previous answer"""
    result = app_memory.recall_decision(description, question)
    return result[0] if result else None


def learn(pref_type: str, value: str):
    """Shortcut to learn a preference"""
    app_memory.learn_preference(pref_type, value)


def get_memory_stats() -> Dict[str, Any]:
    """Shortcut to get stats"""
    return app_memory.get_stats()


# =============================================================================
# DEMO
# =============================================================================

if __name__ == '__main__':
    print("=== Kernel Memory Bridge Demo ===\n")
    
    print(f"Universal Kernel available: {KERNEL_AVAILABLE}")
    print(f"Database: {DB_PATH}\n")
    
    # Demo: Remember some builds
    print("1. Remembering builds...")
    remember_build("a recipe collection app", "crud", ["database", "crud", "search"], True)
    remember_build("a recipe manager with ratings", "crud", ["database", "crud", "ratings"], True)
    remember_build("a todo list app", "crud", ["database", "crud"], True)
    remember_build("a wordle game", "wordle", ["game"], True)
    
    # Demo: Get suggestion
    print("\n2. Testing memory recall...")
    suggestion = suggest_from_memory("a recipe app with ingredients")
    if suggestion:
        print(f"   Suggestion: {suggestion[0]} (confidence: {suggestion[1]:.2f})")
    else:
        print("   No suggestion (need more build history)")
    
    # Demo: Remember decisions
    print("\n3. Remembering decisions...")
    remember_answer("social network app", "Need user authentication?", "yes")
    remember_answer("calculator app", "Need user authentication?", "no")
    
    # Demo: Recall decisions
    print("4. Testing decision recall...")
    answer = recall_answer("social media clone", "Need user authentication?")
    print(f"   Auth for social app: {answer}")
    
    # Demo: Stats
    print("\n5. Memory stats:")
    stats = get_memory_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    print("\n=== Demo Complete ===")
