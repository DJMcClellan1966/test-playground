"""
Template Updater
================

Periodically updates and improves templates based on:
1. Usage patterns (which templates get used most)
2. Build feedback (successful vs failed builds)
3. Field co-occurrence (which fields appear together)
4. New patterns discovered from descriptions

Runs as a background process or on-demand.

NO AI - pure statistical learning from observed data.
"""

import json
import sqlite3
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import Counter, defaultdict
import re

# Import existing systems
try:
    from optimal_50 import OPTIMAL_TRAINING_SET, TrainingExample, Category, Complexity
    from template_synthesis import (
        TemplateSynthesizer, SynthesizedTemplate, DOMAIN_FIELDS,
        CONCEPT_PATTERNS, smart_synth
    )
    from template_algebra import MICRO_TEMPLATES, MicroTemplate, algebra
except ImportError:
    OPTIMAL_TRAINING_SET = []
    MICRO_TEMPLATES = {}
    DOMAIN_FIELDS = {}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TemplateUsage:
    """Track how a template is being used."""
    template_id: str
    use_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    last_used: Optional[str] = None
    avg_confidence: float = 0.0
    common_features: List[str] = field(default_factory=list)
    common_fields: List[str] = field(default_factory=list)
    related_templates: List[str] = field(default_factory=list)


@dataclass
class FieldPattern:
    """Track field co-occurrence patterns."""
    field_name: str
    co_occurs_with: Dict[str, int] = field(default_factory=dict)
    domains: List[str] = field(default_factory=list)
    inferred_type: str = 'str'
    usage_count: int = 0


@dataclass
class DescriptionPattern:
    """Track description patterns that lead to specific templates."""
    pattern: str  # regex pattern
    leads_to: List[str] = field(default_factory=list)  # template IDs
    confidence: float = 0.0
    matches: int = 0


@dataclass
class UpdateReport:
    """Report of what was updated."""
    timestamp: str
    templates_updated: int
    new_patterns_found: int
    fields_added: int
    confidence_adjustments: int
    details: List[str] = field(default_factory=list)


# =============================================================================
# TEMPLATE UPDATER
# =============================================================================

class TemplateUpdater:
    """
    Learns and improves templates over time.
    
    Update Strategies:
    1. USAGE-BASED: Boost confidence of frequently used templates
    2. FEEDBACK-BASED: Adjust based on success/failure rates
    3. CO-OCCURRENCE: Discover field patterns from successful builds
    4. PATTERN-BASED: Learn new description→template mappings
    5. MERGE-BASED: Combine similar templates that co-occur
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent / 'data' / 'template_learning.db')
        self._init_db()
        
        # In-memory caches
        self.usage_cache: Dict[str, TemplateUsage] = {}
        self.field_patterns: Dict[str, FieldPattern] = {}
        self.description_patterns: List[DescriptionPattern] = []
        
        # Background thread control
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._update_interval = 300  # 5 minutes default
        
        # Load existing data
        self._load_from_db()
    
    def _init_db(self):
        """Initialize SQLite database for persistence."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS template_usage (
                    template_id TEXT PRIMARY KEY,
                    use_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    avg_confidence REAL DEFAULT 0.0,
                    common_features TEXT,
                    common_fields TEXT,
                    related_templates TEXT
                );
                
                CREATE TABLE IF NOT EXISTS field_patterns (
                    field_name TEXT PRIMARY KEY,
                    co_occurs_with TEXT,
                    domains TEXT,
                    inferred_type TEXT DEFAULT 'str',
                    usage_count INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS description_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT UNIQUE,
                    leads_to TEXT,
                    confidence REAL DEFAULT 0.0,
                    matches INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS build_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    description TEXT,
                    template_id TEXT,
                    features TEXT,
                    fields TEXT,
                    success INTEGER,
                    feedback TEXT
                );
                
                CREATE TABLE IF NOT EXISTS update_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    templates_updated INTEGER,
                    new_patterns INTEGER,
                    fields_added INTEGER,
                    confidence_adjustments INTEGER,
                    details TEXT
                );
            """)
    
    def _load_from_db(self):
        """Load cached data from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Load template usage
            for row in conn.execute("SELECT * FROM template_usage"):
                self.usage_cache[row['template_id']] = TemplateUsage(
                    template_id=row['template_id'],
                    use_count=row['use_count'],
                    success_count=row['success_count'],
                    fail_count=row['fail_count'],
                    last_used=row['last_used'],
                    avg_confidence=row['avg_confidence'],
                    common_features=json.loads(row['common_features'] or '[]'),
                    common_fields=json.loads(row['common_fields'] or '[]'),
                    related_templates=json.loads(row['related_templates'] or '[]'),
                )
            
            # Load field patterns
            for row in conn.execute("SELECT * FROM field_patterns"):
                self.field_patterns[row['field_name']] = FieldPattern(
                    field_name=row['field_name'],
                    co_occurs_with=json.loads(row['co_occurs_with'] or '{}'),
                    domains=json.loads(row['domains'] or '[]'),
                    inferred_type=row['inferred_type'],
                    usage_count=row['usage_count'],
                )
            
            # Load description patterns
            for row in conn.execute("SELECT * FROM description_patterns"):
                self.description_patterns.append(DescriptionPattern(
                    pattern=row['pattern'],
                    leads_to=json.loads(row['leads_to'] or '[]'),
                    confidence=row['confidence'],
                    matches=row['matches'],
                ))
    
    def _save_to_db(self):
        """Persist current state to database."""
        with sqlite3.connect(self.db_path) as conn:
            # Save template usage
            for usage in self.usage_cache.values():
                conn.execute("""
                    INSERT OR REPLACE INTO template_usage 
                    (template_id, use_count, success_count, fail_count, last_used,
                     avg_confidence, common_features, common_fields, related_templates)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage.template_id, usage.use_count, usage.success_count,
                    usage.fail_count, usage.last_used, usage.avg_confidence,
                    json.dumps(usage.common_features),
                    json.dumps(usage.common_fields),
                    json.dumps(usage.related_templates),
                ))
            
            # Save field patterns
            for fp in self.field_patterns.values():
                conn.execute("""
                    INSERT OR REPLACE INTO field_patterns
                    (field_name, co_occurs_with, domains, inferred_type, usage_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    fp.field_name, json.dumps(fp.co_occurs_with),
                    json.dumps(fp.domains), fp.inferred_type, fp.usage_count,
                ))
            
            # Save description patterns
            for dp in self.description_patterns:
                conn.execute("""
                    INSERT OR REPLACE INTO description_patterns
                    (pattern, leads_to, confidence, matches)
                    VALUES (?, ?, ?, ?)
                """, (dp.pattern, json.dumps(dp.leads_to), dp.confidence, dp.matches))
    
    # =========================================================================
    # RECORDING EVENTS
    # =========================================================================
    
    def record_build(self, description: str, template_id: str, 
                     features: List[str], fields: List[str],
                     success: bool = True, feedback: str = None):
        """Record a build event for learning."""
        timestamp = datetime.now().isoformat()
        
        # Update usage cache
        if template_id not in self.usage_cache:
            self.usage_cache[template_id] = TemplateUsage(template_id=template_id)
        
        usage = self.usage_cache[template_id]
        usage.use_count += 1
        usage.last_used = timestamp
        if success:
            usage.success_count += 1
        else:
            usage.fail_count += 1
        
        # Track common features
        for feat in features:
            if feat not in usage.common_features:
                usage.common_features.append(feat)
        usage.common_features = usage.common_features[:10]  # Keep top 10
        
        # Track common fields
        for f in fields:
            if f not in usage.common_fields:
                usage.common_fields.append(f)
        usage.common_fields = usage.common_fields[:15]  # Keep top 15
        
        # Update field co-occurrence
        for i, f1 in enumerate(fields):
            if f1 not in self.field_patterns:
                self.field_patterns[f1] = FieldPattern(field_name=f1)
            fp = self.field_patterns[f1]
            fp.usage_count += 1
            
            for f2 in fields[i+1:]:
                fp.co_occurs_with[f2] = fp.co_occurs_with.get(f2, 0) + 1
        
        # Record to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO build_history
                (timestamp, description, template_id, features, fields, success, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, description, template_id,
                json.dumps(features), json.dumps(fields),
                1 if success else 0, feedback
            ))
        
        # Update description patterns
        self._learn_description_pattern(description, template_id)
        
        # Persist
        self._save_to_db()
    
    def _learn_description_pattern(self, description: str, template_id: str):
        """Learn patterns from description→template mappings."""
        desc_lower = description.lower()
        
        # Extract key phrases
        patterns_to_try = []
        
        # Word combinations (2-3 words)
        words = re.findall(r'\b\w+\b', desc_lower)
        for i in range(len(words)):
            if i + 1 < len(words):
                patterns_to_try.append(r'\b' + words[i] + r'\s+' + words[i+1] + r'\b')
            if i + 2 < len(words):
                patterns_to_try.append(r'\b' + words[i] + r'\s+\w+\s+' + words[i+2] + r'\b')
        
        # Find or create pattern
        for pattern in patterns_to_try[:5]:  # Limit to avoid explosion
            found = False
            for dp in self.description_patterns:
                if dp.pattern == pattern:
                    if template_id not in dp.leads_to:
                        dp.leads_to.append(template_id)
                    dp.matches += 1
                    dp.confidence = min(0.95, dp.confidence + 0.05)
                    found = True
                    break
            
            if not found and len(self.description_patterns) < 1000:  # Limit total
                self.description_patterns.append(DescriptionPattern(
                    pattern=pattern,
                    leads_to=[template_id],
                    confidence=0.5,
                    matches=1,
                ))
    
    # =========================================================================
    # PERIODIC UPDATE
    # =========================================================================
    
    def run_update(self) -> UpdateReport:
        """Run a full update cycle. Can be called manually or by background thread."""
        report = UpdateReport(
            timestamp=datetime.now().isoformat(),
            templates_updated=0,
            new_patterns_found=0,
            fields_added=0,
            confidence_adjustments=0,
        )
        
        # 1. Confidence adjustments based on success rate
        report.confidence_adjustments = self._update_confidences()
        report.details.append(f"Adjusted confidence for {report.confidence_adjustments} templates")
        
        # 2. Discover field patterns
        new_fields = self._discover_field_patterns()
        report.fields_added = len(new_fields)
        if new_fields:
            report.details.append(f"Discovered fields: {new_fields[:5]}")
        
        # 3. Find related templates
        relations = self._find_template_relations()
        report.templates_updated = len(relations)
        report.details.append(f"Updated relations for {len(relations)} templates")
        
        # 4. Prune weak patterns
        pruned = self._prune_weak_patterns()
        report.details.append(f"Pruned {pruned} weak patterns")
        
        # 5. Synthesize missing templates from build history
        new_templates = self._synthesize_from_history()
        report.new_patterns_found = len(new_templates)
        if new_templates:
            report.details.append(f"Synthesized: {new_templates}")
        
        # Save report
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO update_reports
                (timestamp, templates_updated, new_patterns, fields_added,
                 confidence_adjustments, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report.timestamp, report.templates_updated,
                report.new_patterns_found, report.fields_added,
                report.confidence_adjustments, json.dumps(report.details)
            ))
        
        self._save_to_db()
        return report
    
    def _update_confidences(self) -> int:
        """Adjust template confidence based on success/fail rates."""
        adjusted = 0
        
        for usage in self.usage_cache.values():
            if usage.use_count < 3:
                continue  # Need enough data
            
            # Calculate success rate
            total = usage.success_count + usage.fail_count
            if total == 0:
                continue
            
            success_rate = usage.success_count / total
            
            # Adjust confidence (weighted moving average)
            old_conf = usage.avg_confidence
            new_conf = 0.7 * old_conf + 0.3 * success_rate if old_conf > 0 else success_rate
            
            if abs(new_conf - old_conf) > 0.01:
                usage.avg_confidence = new_conf
                adjusted += 1
        
        return adjusted
    
    def _discover_field_patterns(self) -> List[str]:
        """Discover new field patterns from co-occurrence data."""
        new_fields = []
        
        # Find highly co-occurring field pairs
        for field_name, fp in self.field_patterns.items():
            for co_field, count in fp.co_occurs_with.items():
                if count >= 3:  # Seen together at least 3 times
                    # Check if we should create a combined field
                    combined_name = f"{field_name}_with_{co_field}"
                    if combined_name not in self.field_patterns:
                        # Don't actually create it, just note it
                        new_fields.append(f"{field_name}+{co_field}")
        
        return new_fields[:10]  # Limit
    
    def _find_template_relations(self) -> List[str]:
        """Find templates that are often used together or substituted."""
        relations_found = []
        
        # Get templates that appear in same description patterns
        template_pairs = defaultdict(int)
        for dp in self.description_patterns:
            if len(dp.leads_to) > 1:
                for i, t1 in enumerate(dp.leads_to):
                    for t2 in dp.leads_to[i+1:]:
                        pair = tuple(sorted([t1, t2]))
                        template_pairs[pair] += dp.matches
        
        # Update related_templates
        for (t1, t2), count in template_pairs.items():
            if count >= 2:
                if t1 in self.usage_cache:
                    if t2 not in self.usage_cache[t1].related_templates:
                        self.usage_cache[t1].related_templates.append(t2)
                        relations_found.append(t1)
                if t2 in self.usage_cache:
                    if t1 not in self.usage_cache[t2].related_templates:
                        self.usage_cache[t2].related_templates.append(t1)
                        relations_found.append(t2)
        
        return list(set(relations_found))
    
    def _prune_weak_patterns(self) -> int:
        """Remove patterns with low confidence and few matches."""
        pruned = 0
        cutoff = datetime.now() - timedelta(days=7)
        
        self.description_patterns = [
            dp for dp in self.description_patterns
            if dp.matches >= 2 or dp.confidence >= 0.6
        ]
        
        # Also prune from DB
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                DELETE FROM description_patterns 
                WHERE matches < 2 AND confidence < 0.6
            """)
            pruned = result.rowcount
        
        return pruned
    
    def _synthesize_from_history(self) -> List[str]:
        """Synthesize new templates from successful builds."""
        new_templates = []
        
        # Get recent successful builds
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT description, template_id, fields 
                FROM build_history 
                WHERE success = 1
                ORDER BY timestamp DESC
                LIMIT 100
            """).fetchall()
        
        # Find descriptions that led to synthesized templates
        synth_pattern = re.compile(r'^(has_|tracks_|manages_)')
        
        for row in rows:
            if synth_pattern.match(row['template_id'] or ''):
                # This was a synthesized template - learn from it
                fields = json.loads(row['fields'] or '[]')
                if fields and row['template_id'] not in new_templates:
                    # Could register this as a permanent template
                    new_templates.append(row['template_id'])
        
        return new_templates[:5]
    
    # =========================================================================
    # BACKGROUND THREAD
    # =========================================================================
    
    def start_background(self, interval_seconds: int = 300):
        """Start background update thread."""
        if self._running:
            return
        
        self._running = True
        self._update_interval = interval_seconds
        
        def _run():
            while self._running:
                time.sleep(self._update_interval)
                if self._running:
                    try:
                        report = self.run_update()
                        print(f"[TemplateUpdater] Update complete: {report.templates_updated} updated")
                    except Exception as e:
                        print(f"[TemplateUpdater] Error: {e}")
        
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        print(f"[TemplateUpdater] Started background updates every {interval_seconds}s")
    
    def stop_background(self):
        """Stop background update thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        print("[TemplateUpdater] Stopped")
    
    # =========================================================================
    # QUERY METHODS
    # =========================================================================
    
    def get_template_stats(self, template_id: str) -> Optional[TemplateUsage]:
        """Get usage stats for a template."""
        return self.usage_cache.get(template_id)
    
    def get_top_templates(self, limit: int = 10) -> List[TemplateUsage]:
        """Get most used templates."""
        return sorted(
            self.usage_cache.values(),
            key=lambda x: x.use_count,
            reverse=True
        )[:limit]
    
    def suggest_fields(self, existing_fields: List[str]) -> List[str]:
        """Suggest additional fields based on co-occurrence patterns."""
        suggestions = Counter()
        
        for field in existing_fields:
            if field in self.field_patterns:
                fp = self.field_patterns[field]
                for co_field, count in fp.co_occurs_with.items():
                    if co_field not in existing_fields:
                        suggestions[co_field] += count
        
        return [f for f, _ in suggestions.most_common(5)]
    
    def predict_template(self, description: str) -> List[Tuple[str, float]]:
        """Predict likely templates from description using learned patterns."""
        predictions = Counter()
        desc_lower = description.lower()
        
        for dp in self.description_patterns:
            try:
                if re.search(dp.pattern, desc_lower):
                    for template_id in dp.leads_to:
                        predictions[template_id] += dp.confidence * dp.matches
            except re.error:
                continue  # Skip invalid patterns
        
        return predictions.most_common(5)
    
    def get_recent_reports(self, limit: int = 5) -> List[UpdateReport]:
        """Get recent update reports."""
        reports = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM update_reports 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,)).fetchall()
            
            for row in rows:
                reports.append(UpdateReport(
                    timestamp=row['timestamp'],
                    templates_updated=row['templates_updated'],
                    new_patterns_found=row['new_patterns'],
                    fields_added=row['fields_added'],
                    confidence_adjustments=row['confidence_adjustments'],
                    details=json.loads(row['details'] or '[]'),
                ))
        
        return reports
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total_builds = conn.execute("SELECT COUNT(*) FROM build_history").fetchone()[0]
            successful = conn.execute("SELECT COUNT(*) FROM build_history WHERE success=1").fetchone()[0]
            total_updates = conn.execute("SELECT COUNT(*) FROM update_reports").fetchone()[0]
        
        return {
            'total_templates_tracked': len(self.usage_cache),
            'total_field_patterns': len(self.field_patterns),
            'total_description_patterns': len(self.description_patterns),
            'total_builds_recorded': total_builds,
            'successful_builds': successful,
            'success_rate': successful / total_builds if total_builds > 0 else 0,
            'total_updates_run': total_updates,
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

updater = TemplateUpdater()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def record_build(description: str, template_id: str, 
                 features: List[str], fields: List[str],
                 success: bool = True, feedback: str = None):
    """Record a build event."""
    updater.record_build(description, template_id, features, fields, success, feedback)


def run_update() -> UpdateReport:
    """Run an update cycle."""
    return updater.run_update()


def start_background_updates(interval: int = 300):
    """Start background updates."""
    updater.start_background(interval)


def stop_background_updates():
    """Stop background updates."""
    updater.stop_background()


def get_statistics() -> Dict[str, Any]:
    """Get updater statistics."""
    return updater.get_statistics()


# =============================================================================
# DEMO
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("TEMPLATE UPDATER - PERIODIC IMPROVEMENT SYSTEM")
    print("=" * 60)
    
    # Simulate some builds
    test_builds = [
        ("a recipe app with ingredients", "recipe_searchable", ["search", "tags"], 
         ["title", "ingredients", "instructions", "prep_time"]),
        ("a workout tracker", "workout_tracker", ["history"],
         ["exercise_type", "sets", "reps", "weight"]),
        ("a todo list", "simple_todo", [],
         ["title", "completed", "due_date"]),
        ("a recipe collection with ratings", "recipe_social", ["auth", "ratings"],
         ["title", "ingredients", "rating", "comments"]),
        ("an expense tracker", "expense_manager", ["stats", "export"],
         ["amount", "category", "date", "description"]),
        ("a budget app", "budget_tracker", ["stats"],
         ["amount", "category", "budget_limit", "spent"]),
    ]
    
    print("\n--- Recording Simulated Builds ---")
    for desc, template, features, fields in test_builds:
        record_build(desc, template, features, fields, success=True)
        print(f"  Recorded: {template}")
    
    print("\n--- Running Update Cycle ---")
    report = run_update()
    print(f"  Timestamp: {report.timestamp}")
    print(f"  Templates updated: {report.templates_updated}")
    print(f"  New patterns: {report.new_patterns_found}")
    print(f"  Fields added: {report.fields_added}")
    print(f"  Confidence adjustments: {report.confidence_adjustments}")
    print(f"  Details: {report.details}")
    
    print("\n--- Statistics ---")
    stats = get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n--- Top Templates ---")
    for usage in updater.get_top_templates(5):
        print(f"  {usage.template_id}: {usage.use_count} uses, "
              f"{usage.success_count} successes, conf={usage.avg_confidence:.0%}")
    
    print("\n--- Field Suggestions ---")
    test_fields = ["title", "ingredients"]
    suggestions = updater.suggest_fields(test_fields)
    print(f"  Given: {test_fields}")
    print(f"  Suggested: {suggestions}")
    
    print("\n--- Template Predictions ---")
    test_desc = "a recipe app"
    predictions = updater.predict_template(test_desc)
    print(f"  For: '{test_desc}'")
    print(f"  Predictions: {predictions}")
    
    print("\n" + "=" * 60)
    print("Background mode available: start_background_updates(300)")
    print("=" * 60)
