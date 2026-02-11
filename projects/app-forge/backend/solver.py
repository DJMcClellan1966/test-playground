"""Constraint solver - Maps app requirements to optimal tech stack."""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class TechStack:
    """A recommended tech stack."""
    backend: str
    database: str
    realtime: str
    frontend: str
    auth: str
    notes: List[str]
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "backend": self.backend,
            "database": self.database,
            "realtime": self.realtime,
            "frontend": self.frontend,
            "auth": self.auth,
            "notes": self.notes,
        }


class ConstraintSolver:
    """Solves for the best tech stack based on requirements."""
    
    def solve(self, answers: Dict[str, bool], description: str) -> TechStack:
        """Find optimal stack."""
        
        # Call heuristics
        needs_auth = answers.get("needs_auth", False)
        needs_realtime = answers.get("realtime", False)
        needs_db = answers.get("has_data", False)
        complex_queries = answers.get("complex_queries", False)
        is_mobile = answers.get("mobile", False)
        is_perf_critical = answers.get("performance_critical", False)
        
        notes = []
        
        # Backend choice (local-first = Flask always; codegen only produces Flask)
        backend = "Flask"
        if needs_realtime:
            notes.append("Flask + flask-socketio for WebSocket support")
        
        # Database choice
        if not needs_db:
            database = "None (in-memory)"
        elif complex_queries or is_perf_critical:
            database = "PostgreSQL"
            notes.append("PostgreSQL for complex queries and scale")
        else:
            database = "SQLite"
            notes.append("SQLite (local-first, no server needed)")
        
        # Realtime
        realtime = "WebSockets" if needs_realtime else "REST polling"
        
        # Frontend
        frontend = "HTML + JavaScript (Vanilla or Htmx)"
        if is_mobile:
            frontend = "React or React Native"
            notes.append("React recommended for web and mobile (React Native)")
        
        # Auth
        if needs_auth:
            auth = "Session-based (secure)"
        else:
            auth = "No auth needed"
        
        return TechStack(
            backend=backend,
            database=database,
            realtime=realtime,
            frontend=frontend,
            auth=auth,
            notes=notes,
        )


# Singleton
solver = ConstraintSolver()
