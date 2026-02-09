"""
Usage Telemetry - Track feature usage for blueprint improvement.

The self-improving loop:
1. User builds app from blueprint
2. App tracks which features get used
3. Telemetry feeds back to improve blueprints:
   - Unused features demoted in priority
   - Heavily used features promoted to MVP
   - Usage patterns create new best practices

Privacy-first design:
- All data stays local by default
- Aggregated patterns only (no personal data)
- User controls what to share

This module provides:
- Decorators to instrument function usage
- Local storage of usage data
- Analysis tools to identify patterns
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from functools import wraps
from collections import defaultdict


# Default storage location
TELEMETRY_DIR = Path(__file__).parent.parent / "projects" / ".telemetry"


class UsageTracker:
    """
    Track feature usage in a generated app.
    
    Usage in generated code:
    
        from telemetry import tracker
        
        @tracker.track("library.view_book")
        def view_book(book_id):
            ...
        
        # Or manual tracking:
        tracker.record("search.execute", {"query_length": len(query)})
    """
    
    def __init__(self, app_name: str, storage_path: Optional[Path] = None):
        self.app_name = app_name
        self.storage_path = storage_path or TELEMETRY_DIR / f"{app_name}.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._events: List[Dict] = []
        self._session_start = datetime.now()
        self._session_id = self._session_start.strftime("%Y%m%d_%H%M%S")
        
        # Load existing data
        self._load()
    
    def _load(self):
        """Load existing telemetry data."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self._events = data.get("events", [])
            except (json.JSONDecodeError, KeyError):
                self._events = []
    
    def _save(self):
        """Save telemetry data."""
        data = {
            "app_name": self.app_name,
            "last_updated": datetime.now().isoformat(),
            "events": self._events
        }
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    def record(self, feature: str, metadata: Optional[Dict] = None):
        """
        Record a feature usage event.
        
        Args:
            feature: Dot-notation feature name (e.g., "library.add_book")
            metadata: Optional additional data about the usage
        """
        event = {
            "feature": feature,
            "timestamp": datetime.now().isoformat(),
            "session": self._session_id,
        }
        if metadata:
            event["metadata"] = metadata
        
        self._events.append(event)
        
        # Save periodically (every 10 events)
        if len(self._events) % 10 == 0:
            self._save()
    
    def track(self, feature: str):
        """
        Decorator to track function calls.
        
        Usage:
            @tracker.track("books.search")
            def search_books(query):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.record(feature)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def end_session(self):
        """End the current session and save all data."""
        session_duration = (datetime.now() - self._session_start).total_seconds()
        self.record("session.end", {"duration_seconds": session_duration})
        self._save()
    
    def get_summary(self) -> Dict:
        """Get a summary of usage patterns."""
        if not self._events:
            return {"total_events": 0}
        
        # Count feature usage
        feature_counts = defaultdict(int)
        for event in self._events:
            feature_counts[event["feature"]] += 1
        
        # Get sessions
        sessions = set(e.get("session", "unknown") for e in self._events)
        
        # Calculate time range
        timestamps = [e["timestamp"] for e in self._events]
        
        return {
            "total_events": len(self._events),
            "unique_features": len(feature_counts),
            "total_sessions": len(sessions),
            "feature_counts": dict(sorted(
                feature_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )),
            "first_event": min(timestamps),
            "last_event": max(timestamps),
        }


class BlueprintAnalyzer:
    """
    Analyze usage data to improve blueprints.
    
    Takes telemetry from multiple apps using the same blueprint
    and identifies patterns that should inform the blueprint.
    """
    
    def __init__(self, blueprint_name: str):
        self.blueprint_name = blueprint_name
        self.telemetry_dir = TELEMETRY_DIR
    
    def _load_apps_for_blueprint(self) -> List[Dict]:
        """Load telemetry from apps that used this blueprint."""
        apps_data = []
        
        for telemetry_file in self.telemetry_dir.glob("*.json"):
            try:
                data = json.loads(telemetry_file.read_text(encoding="utf-8"))
                # Check if this app was generated from our blueprint
                # (We'd need to store this in the telemetry - enhancement for later)
                apps_data.append(data)
            except (json.JSONDecodeError, KeyError):
                continue
        
        return apps_data
    
    def analyze(self) -> Dict:
        """
        Analyze usage patterns across all apps from this blueprint.
        
        Returns insights for blueprint improvement.
        """
        all_apps = self._load_apps_for_blueprint()
        
        if not all_apps:
            return {"status": "no_data"}
        
        # Aggregate feature usage across all apps
        total_usage = defaultdict(int)
        apps_using = defaultdict(int)  # How many apps use each feature
        
        for app in all_apps:
            app_features = set()
            for event in app.get("events", []):
                feature = event.get("feature", "")
                if feature and not feature.startswith("session."):
                    total_usage[feature] += 1
                    app_features.add(feature)
            
            for feature in app_features:
                apps_using[feature] += 1
        
        total_apps = len(all_apps)
        
        # Identify features to promote/demote
        widely_used = []
        rarely_used = []
        
        for feature, count in apps_using.items():
            adoption_rate = count / total_apps
            if adoption_rate >= 0.8:  # 80%+ apps use it
                widely_used.append((feature, adoption_rate, total_usage[feature]))
            elif adoption_rate <= 0.2:  # 20% or less
                rarely_used.append((feature, adoption_rate, total_usage[feature]))
        
        return {
            "status": "analyzed",
            "total_apps": total_apps,
            "total_events": sum(total_usage.values()),
            "feature_adoption": {f: count/total_apps for f, count in apps_using.items()},
            "recommendations": {
                "promote_to_mvp": [
                    f"{f} (used by {rate:.0%} of apps, {count} times)"
                    for f, rate, count in sorted(widely_used, key=lambda x: x[2], reverse=True)
                ],
                "consider_removing": [
                    f"{f} (only {rate:.0%} of apps, {count} total uses)"
                    for f, rate, count in sorted(rarely_used, key=lambda x: x[1])
                ],
            }
        }


def generate_telemetry_code(app_name: str) -> str:
    """
    Generate the telemetry integration code to add to a scaffolded app.
    
    This is called by scaffold.py when --generate is used.
    """
    return f'''"""
Usage telemetry for {app_name}.

Auto-generated to track feature usage and improve the blueprint.
All data stays local. Remove this file to disable tracking.
"""

from pathlib import Path
import sys

# Add telemetry module to path
TELEMETRY_PATH = Path(__file__).parent.parent.parent / "blueprints"
sys.path.insert(0, str(TELEMETRY_PATH))

try:
    from telemetry import UsageTracker
    tracker = UsageTracker("{app_name}")
except ImportError:
    # Telemetry not available - use no-op tracker
    class NoOpTracker:
        def track(self, name):
            def decorator(func):
                return func
            return decorator
        def record(self, *args, **kwargs):
            pass
        def end_session(self):
            pass
    tracker = NoOpTracker()


# Usage in your code:
#
# @tracker.track("feature.name")
# def my_feature():
#     ...
#
# Or: tracker.record("feature.name", {{"key": "value"}})
'''


# ============================================================================
# CLI 
# ============================================================================

def main():
    """CLI for viewing telemetry data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="View usage telemetry")
    parser.add_argument("app", nargs="?", help="App name to view")
    parser.add_argument("--list", "-l", action="store_true", help="List all tracked apps")
    parser.add_argument("--analyze", "-a", help="Analyze usage for a blueprint")
    
    args = parser.parse_args()
    
    if args.list or (not args.app and not args.analyze):
        print("\n📊 Tracked Applications:\n")
        if not TELEMETRY_DIR.exists():
            print("   No telemetry data yet.")
            print(f"   Data will appear in: {TELEMETRY_DIR}")
        else:
            for f in sorted(TELEMETRY_DIR.glob("*.json")):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    events = len(data.get("events", []))
                    print(f"   {f.stem}: {events} events")
                except:
                    print(f"   {f.stem}: (error reading)")
        print()
        return
    
    if args.analyze:
        analyzer = BlueprintAnalyzer(args.analyze)
        results = analyzer.analyze()
        
        print(f"\n📊 Blueprint Analysis: {args.analyze}\n")
        if results["status"] == "no_data":
            print("   No usage data available yet.")
        else:
            print(f"   Apps analyzed: {results['total_apps']}")
            print(f"   Total events: {results['total_events']}")
            print()
            
            recs = results.get("recommendations", {})
            if recs.get("promote_to_mvp"):
                print("   ⬆️ Promote to MVP (widely used):")
                for r in recs["promote_to_mvp"][:5]:
                    print(f"      • {r}")
            
            if recs.get("consider_removing"):
                print("\n   ⬇️ Consider removing (rarely used):")
                for r in recs["consider_removing"][:5]:
                    print(f"      • {r}")
        print()
        return
    
    if args.app:
        tracker = UsageTracker(args.app)
        summary = tracker.get_summary()
        
        print(f"\n📊 Usage Summary: {args.app}\n")
        print(f"   Total events: {summary.get('total_events', 0)}")
        print(f"   Unique features: {summary.get('unique_features', 0)}")
        print(f"   Sessions: {summary.get('total_sessions', 0)}")
        
        if summary.get("feature_counts"):
            print("\n   Top features:")
            for feature, count in list(summary["feature_counts"].items())[:10]:
                print(f"      {feature}: {count}")
        print()


if __name__ == "__main__":
    main()
