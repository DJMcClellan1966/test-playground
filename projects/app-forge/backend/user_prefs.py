"""User Preference Learning - AI-free build history tracking.

This module tracks what templates users build and adjusts scoring based on patterns.
No AI/LLM required - just simple frequency counting and recency weighting.

Features:
- Tracks successful builds (template, features, description)
- Boosts templates user builds frequently
- Decays old preferences over time
- Learns feature preferences (e.g., user often adds auth)
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Path to user preferences file
PREFS_FILE = os.path.join(os.path.dirname(__file__), "user_prefs.json")


@dataclass
class BuildRecord:
    """Record of a single build."""
    template_id: str
    features: List[str]
    description: str
    timestamp: str  # ISO format
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class UserPreferences:
    """Tracks and learns from user build history."""
    
    def __init__(self, prefs_file: str = PREFS_FILE):
        self.prefs_file = prefs_file
        self.builds: List[BuildRecord] = []
        self.load()
    
    def load(self):
        """Load preferences from file."""
        if os.path.exists(self.prefs_file):
            try:
                with open(self.prefs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.builds = [BuildRecord.from_dict(b) for b in data.get('builds', [])]
            except (json.JSONDecodeError, KeyError):
                self.builds = []
        else:
            self.builds = []
    
    def save(self):
        """Save preferences to file."""
        data = {
            'builds': [b.to_dict() for b in self.builds],
            'updated': datetime.now().isoformat()
        }
        with open(self.prefs_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def record_build(self, template_id: str, features: Dict, description: str):
        """Record a successful build."""
        record = BuildRecord(
            template_id=template_id,
            features=list(features.keys()) if isinstance(features, dict) else features,
            description=description,
            timestamp=datetime.now().isoformat()
        )
        self.builds.append(record)
        
        # Keep only last 100 builds to prevent file bloat
        if len(self.builds) > 100:
            self.builds = self.builds[-100:]
        
        self.save()
    
    def get_template_boost(self, template_id: str, decay_days: int = 30) -> float:
        """Get score boost for a template based on build history.
        
        Returns a value 0-5 based on how often this template was used recently.
        Recent builds count more than old ones (time decay).
        """
        if not self.builds:
            return 0.0
        
        now = datetime.now()
        score = 0.0
        
        for build in self.builds:
            if build.template_id == template_id:
                try:
                    build_time = datetime.fromisoformat(build.timestamp)
                    days_ago = (now - build_time).days
                    
                    # Decay factor: 1.0 for today, 0.5 at decay_days, 0.0 at 2*decay_days
                    decay = max(0.0, 1.0 - (days_ago / (2 * decay_days)))
                    score += decay
                except ValueError:
                    # Invalid timestamp, count as 0.5
                    score += 0.5
        
        # Cap at 5.0 max boost
        return min(5.0, score)
    
    def get_feature_preferences(self) -> Dict[str, float]:
        """Get learned feature preferences (0-1 for each feature).
        
        Returns dict mapping feature_name -> preference score (0-1).
        """
        if not self.builds:
            return {}
        
        feature_counts: Dict[str, int] = {}
        total = len(self.builds)
        
        for build in self.builds:
            for feat in build.features:
                feature_counts[feat] = feature_counts.get(feat, 0) + 1
        
        # Normalize to 0-1
        return {feat: count / total for feat, count in feature_counts.items()}
    
    def suggest_features(self, template_id: str) -> List[str]:
        """Suggest features based on what user typically adds to this template."""
        feature_with_template: Dict[str, int] = {}
        template_count = 0
        
        for build in self.builds:
            if build.template_id == template_id:
                template_count += 1
                for feat in build.features:
                    feature_with_template[feat] = feature_with_template.get(feat, 0) + 1
        
        if template_count == 0:
            return []
        
        # Features used in >50% of builds with this template
        suggestions = [
            feat for feat, count in feature_with_template.items()
            if count / template_count >= 0.5
        ]
        return suggestions
    
    def get_stats(self) -> Dict:
        """Get statistics about build history."""
        if not self.builds:
            return {'total_builds': 0}
        
        template_counts: Dict[str, int] = {}
        for build in self.builds:
            template_counts[build.template_id] = template_counts.get(build.template_id, 0) + 1
        
        most_used = max(template_counts.items(), key=lambda x: x[1]) if template_counts else (None, 0)
        
        return {
            'total_builds': len(self.builds),
            'template_counts': template_counts,
            'most_used': most_used[0],
            'most_used_count': most_used[1],
            'feature_prefs': self.get_feature_preferences(),
        }
    
    def clear(self):
        """Clear all preferences."""
        self.builds = []
        self.save()


# Singleton instance
_prefs: Optional[UserPreferences] = None

def get_prefs() -> UserPreferences:
    """Get user preferences singleton."""
    global _prefs
    if _prefs is None:
        _prefs = UserPreferences()
    return _prefs


def record_build(template_id: str, features: Dict, description: str):
    """Record a successful build (convenience function)."""
    get_prefs().record_build(template_id, features, description)


def get_template_boost(template_id: str) -> float:
    """Get score boost for template (convenience function)."""
    return get_prefs().get_template_boost(template_id)


def get_feature_preferences() -> Dict[str, float]:
    """Get feature preferences (convenience function)."""
    return get_prefs().get_feature_preferences()


# CLI for testing
if __name__ == "__main__":
    import sys
    
    prefs = get_prefs()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python user_prefs.py stats     # Show build statistics")
        print("  python user_prefs.py clear     # Clear all history")
        print("  python user_prefs.py boost <template_id>  # Get boost for template")
        print("  python user_prefs.py simulate  # Add some test builds")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "stats":
        stats = prefs.get_stats()
        print("Build Statistics:")
        print(f"  Total builds: {stats['total_builds']}")
        if stats['total_builds'] > 0:
            print(f"  Most used: {stats['most_used']} ({stats['most_used_count']} times)")
            print(f"  Template counts: {stats['template_counts']}")
            print(f"  Feature preferences: {stats['feature_prefs']}")
    
    elif cmd == "clear":
        prefs.clear()
        print("Preferences cleared.")
    
    elif cmd == "boost" and len(sys.argv) > 2:
        template_id = sys.argv[2]
        boost = prefs.get_template_boost(template_id)
        print(f"Boost for '{template_id}': {boost:.2f}")
    
    elif cmd == "simulate":
        # Add some test builds
        test_builds = [
            ("crud", {"auth": True, "storage": True}, "recipe tracker"),
            ("crud", {"auth": True}, "todo list"),
            ("crud", {"storage": True}, "movie collection"),
            ("quiz", {}, "trivia game"),
            ("timer", {}, "pomodoro timer"),
        ]
        for template_id, features, desc in test_builds:
            prefs.record_build(template_id, features, desc)
        print(f"Added {len(test_builds)} test builds.")
        print(prefs.get_stats())
    
    else:
        print(f"Unknown command: {cmd}")
