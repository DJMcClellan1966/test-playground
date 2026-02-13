"""
connection_monitor.py

Tracks module interactions, template matches, and feature flows during app generation.
Logs connections, unused features, and emergent patterns for insight discovery.
"""

import threading
from typing import Any, Dict, List

class ConnectionMonitor:
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def log_interaction(self, module: str, action: str, details: Dict[str, Any]):
        with self.lock:
            self.logs.append({
                "module": module,
                "action": action,
                "details": details
            })

    def log_template_match(self, template_id: str, features: Dict[str, Any], score: float):
        with self.lock:
            self.logs.append({
                "module": "template_registry",
                "action": "match",
                "template_id": template_id,
                "features": features,
                "score": score
            })

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze logs for unused features, unexpected correlations, and emergent patterns.
        Returns a summary dict.
        """
        summary = {
            "unused_features": set(),
            "unexpected_connections": [],
            "hybrid_suggestions": []
        }
        used_features = set()
        for log in self.logs:
            if log.get("features"):
                used_features.update(log["features"].keys())
        # Find features that were logged but not used in final build
        for log in self.logs:
            if log.get("action") == "match":
                for f in log["features"]:
                    if f not in used_features:
                        summary["unused_features"].add(f)
        # Placeholder: Find unexpected connections (could use graph analysis)
        # Placeholder: Suggest hybrid templates if feature overlap is high
        summary["unused_features"] = list(summary["unused_features"])
        return summary

# Example usage:
# cm = ConnectionMonitor()
# cm.log_interaction("solver", "solve", {"input": "..."})
# cm.log_template_match("crud", {"has_data": True}, 9.5)
# print(cm.analyze())
