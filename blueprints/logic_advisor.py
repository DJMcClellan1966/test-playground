"""
Logic Advisor - Deterministic Guidance Without AI

Uses constraint propagation and pattern matching to provide
instant recommendations. Never times out, never hallucinates.

The key insight: Most "intelligent" guidance is actually
rule-based pattern matching. AI is overkill for structured domains.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple
import json


@dataclass
class Suggestion:
    """A single recommendation."""
    category: str  # "add_block", "warning", "next_step", "pattern"
    title: str
    reason: str
    action: Optional[str] = None  # e.g., block_id to add
    priority: int = 5  # 1-10, higher = more important
    

@dataclass
class Analysis:
    """Complete analysis of current state."""
    suggestions: List[Suggestion]
    missing_requirements: List[str]
    satisfied_capabilities: List[str]
    warnings: List[str]
    next_steps: List[str]
    completeness_score: int  # 0-100


# ============================================================================
# PATTERN LIBRARY - Common architectural patterns
# ============================================================================

PATTERNS = {
    "crud_app": {
        "name": "CRUD Application",
        "description": "Basic create-read-update-delete app",
        "required_blocks": ["storage_sqlite", "crud_routes"],
        "suggested_blocks": ["auth_basic"],
        "min_entities": 1,
    },
    "realtime_app": {
        "name": "Real-time Application",
        "description": "Live updates, collaborative features",
        "required_blocks": ["crdt_sync", "storage_sqlite", "auth_basic"],
        "suggested_blocks": [],
        "min_entities": 1,
    },
    "offline_first": {
        "name": "Offline-First Application",
        "description": "Works without network, syncs when online",
        "required_blocks": ["storage_json", "crdt_sync"],
        "suggested_blocks": ["auth_basic"],
        "min_entities": 1,
    },
    "api_backend": {
        "name": "API Backend",
        "description": "RESTful service with database",
        "required_blocks": ["storage_sqlite", "crud_routes"],
        "suggested_blocks": ["auth_basic"],
        "min_entities": 1,
    },
}


# ============================================================================
# BLOCK COMPATIBILITY RULES
# ============================================================================

BLOCK_RULES = {
    # What each block requires
    "crud_routes": {
        "requires": ["storage"],  # Any storage block
        "message": "CRUD routes need a storage backend",
    },
    "crdt_sync": {
        "requires": ["storage"],
        "message": "CRDT sync needs local storage to cache data",
    },
    "auth_basic": {
        "requires": ["storage"],
        "message": "Auth needs storage for user credentials",
    },
}

# What provides what
BLOCK_PROVIDES = {
    "storage_sqlite": ["storage", "queries", "transactions"],
    "storage_json": ["storage", "simple_persistence"],
    "crud_routes": ["api", "endpoints"],
    "crdt_sync": ["sync", "realtime", "offline"],
    "auth_basic": ["auth", "users", "sessions"],
}


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

class LogicAdvisor:
    """
    Deterministic advisor using constraint propagation.
    
    No AI, no timeouts, no surprises.
    """
    
    def __init__(self):
        self.block_provides = BLOCK_PROVIDES
        self.block_rules = BLOCK_RULES
        self.patterns = PATTERNS
        
    def analyze(
        self,
        placed_blocks: List[str],
        entities: List[Dict],
        project_name: str = ""
    ) -> Analysis:
        """
        Analyze current state and generate recommendations.
        
        Args:
            placed_blocks: List of block IDs on canvas
            entities: List of entity definitions
            project_name: Name of the project
            
        Returns:
            Complete analysis with suggestions
        """
        suggestions = []
        warnings = []
        missing = []
        satisfied = []
        next_steps = []
        
        # Collect what we have
        provided = set()
        for block in placed_blocks:
            if block in self.block_provides:
                provided.update(self.block_provides[block])
                satisfied.extend(self.block_provides[block])
        
        # Check what's missing
        for block in placed_blocks:
            if block in self.block_rules:
                rule = self.block_rules[block]
                for req in rule["requires"]:
                    if req not in provided:
                        missing.append(req)
                        suggestions.append(Suggestion(
                            category="missing_dependency",
                            title=f"Missing: {req}",
                            reason=rule["message"],
                            action=self._suggest_block_for(req),
                            priority=9
                        ))
        
        # Empty canvas guidance
        if not placed_blocks and not entities:
            suggestions.append(Suggestion(
                category="getting_started",
                title="Start with an entity",
                reason="Define your data model first. What 'things' does your app work with? (e.g., Task, User, Post)",
                priority=10
            ))
            suggestions.append(Suggestion(
                category="getting_started",
                title="Or start with storage",
                reason="Drag a storage block to establish your data persistence strategy",
                action="storage_sqlite",
                priority=8
            ))
        
        # Has entities but no blocks
        elif entities and not placed_blocks:
            suggestions.append(Suggestion(
                category="add_block",
                title="Add storage for your entities",
                reason=f"You have {len(entities)} entity(ies) but no way to persist them",
                action="storage_sqlite",
                priority=9
            ))
        
        # Has storage but no routes
        elif "storage" in provided and "api" not in provided:
            suggestions.append(Suggestion(
                category="add_block",
                title="Add CRUD routes",
                reason="You have storage but no API endpoints to access the data",
                action="crud_routes",
                priority=8
            ))
        
        # Pattern detection
        detected_pattern = self._detect_pattern(placed_blocks, entities)
        if detected_pattern:
            pattern = self.patterns[detected_pattern]
            for block in pattern["suggested_blocks"]:
                if block not in placed_blocks:
                    suggestions.append(Suggestion(
                        category="pattern_suggestion",
                        title=f"Consider adding: {block}",
                        reason=f"Common for {pattern['name']} pattern",
                        action=block,
                        priority=5
                    ))
        
        # Entity count warnings
        if entities:
            for entity in entities:
                if not entity.get("fields") or len(entity.get("fields", [])) == 0:
                    warnings.append(f"Entity '{entity.get('name', 'unnamed')}' has no fields")
                    
        # Has auth but nothing to protect
        if "auth" in provided and "api" not in provided:
            warnings.append("Auth is set up but there are no routes to protect")
        
        # Compute completeness
        completeness = self._compute_completeness(placed_blocks, entities, provided)
        
        # Generate next steps
        next_steps = self._generate_next_steps(placed_blocks, entities, provided, completeness)
        
        return Analysis(
            suggestions=sorted(suggestions, key=lambda s: -s.priority),
            missing_requirements=list(set(missing)),
            satisfied_capabilities=list(set(satisfied)),
            warnings=warnings,
            next_steps=next_steps,
            completeness_score=completeness
        )
    
    def _suggest_block_for(self, requirement: str) -> Optional[str]:
        """Find a block that provides the requirement."""
        for block_id, provides in self.block_provides.items():
            if requirement in provides:
                return block_id
        return None
    
    def _detect_pattern(self, blocks: List[str], entities: List[Dict]) -> Optional[str]:
        """Detect which architectural pattern best matches current state."""
        best_match = None
        best_score = 0
        
        for pattern_id, pattern in self.patterns.items():
            score = 0
            required = set(pattern["required_blocks"])
            present = set(blocks)
            
            # Score based on overlap
            overlap = len(required.intersection(present))
            if overlap > 0:
                score = overlap / len(required) * 100
                
            # Bonus for having entities
            if entities and pattern["min_entities"] > 0:
                score += 20
                
            if score > best_score:
                best_score = score
                best_match = pattern_id
                
        return best_match if best_score > 30 else None
    
    def _compute_completeness(
        self, 
        blocks: List[str], 
        entities: List[Dict],
        provided: Set[str]
    ) -> int:
        """Score from 0-100 how complete the project is."""
        score = 0
        
        # Has entities (30 points)
        if entities:
            score += min(30, len(entities) * 10)
        
        # Has storage (20 points)
        if "storage" in provided:
            score += 20
            
        # Has API routes (20 points)
        if "api" in provided:
            score += 20
            
        # Has auth (15 points)
        if "auth" in provided:
            score += 15
            
        # Has sync (15 points)
        if "sync" in provided:
            score += 15
            
        return min(100, score)
    
    def _generate_next_steps(
        self,
        blocks: List[str],
        entities: List[Dict],
        provided: Set[str],
        completeness: int
    ) -> List[str]:
        """Generate ordered next steps."""
        steps = []
        
        if completeness == 0:
            steps.append("1. Create an entity to define your data model")
            steps.append("2. Add a storage block (SQLite recommended)")
            steps.append("3. Add CRUD routes to expose an API")
            
        elif completeness < 50:
            if "storage" not in provided:
                steps.append("Add a storage block to persist data")
            if "api" not in provided:
                steps.append("Add CRUD routes to create endpoints")
            if not entities:
                steps.append("Create at least one entity")
                
        elif completeness < 80:
            if "auth" not in provided:
                steps.append("Consider adding authentication")
            steps.append("Click Generate to create your project")
            
        else:
            steps.append("Your project is ready! Click Generate.")
            steps.append("Output will be in the workspace/ folder")
            
        return steps

    def ask(self, question: str, context: Dict[str, Any]) -> str:
        """
        Answer a question using pattern matching.
        
        No AI - just smart keyword matching and rule lookup.
        """
        q_lower = question.lower()
        
        # Block-related questions
        if "what block" in q_lower or "which block" in q_lower:
            if "auth" in q_lower or "login" in q_lower or "user" in q_lower:
                return self._explain_block("auth_basic")
            if "storage" in q_lower or "database" in q_lower or "save" in q_lower:
                return self._explain_block("storage_sqlite")
            if "api" in q_lower or "route" in q_lower or "endpoint" in q_lower:
                return self._explain_block("crud_routes")
            if "sync" in q_lower or "offline" in q_lower or "realtime" in q_lower:
                return self._explain_block("crdt_sync")
        
        # How-to questions
        if "how" in q_lower:
            if "start" in q_lower or "begin" in q_lower:
                return (
                    "Getting started:\n\n"
                    "1. Define your entities in the Entities tab (e.g., Task, User)\n"
                    "2. Add fields to each entity (name, type)\n"
                    "3. Drag storage_sqlite to the canvas\n"
                    "4. Drag crud_routes to add API endpoints\n"
                    "5. Click Generate to create your project\n\n"
                    "The blocks auto-connect based on what they require/provide."
                )
            if "add" in q_lower and ("field" in q_lower or "column" in q_lower):
                return (
                    "Adding fields:\n\n"
                    "1. Go to the Entities tab\n"
                    "2. Click on your entity or create one\n"
                    "3. Use the + Field button\n"
                    "4. Enter name and choose type (string, int, boolean, etc.)\n\n"
                    "Common fields: id (auto), title (string), created_at (datetime)"
                )
        
        # What-is questions
        if "what is" in q_lower or "what's" in q_lower:
            if "crdt" in q_lower:
                return (
                    "CRDT = Conflict-free Replicated Data Type\n\n"
                    "It's a data structure that can be edited on multiple devices "
                    "simultaneously and merged without conflicts. Perfect for:\n"
                    "- Offline-first apps\n"
                    "- Collaborative editing\n"
                    "- Real-time sync\n\n"
                    "The crdt_sync block handles this for you."
                )
            if "contract" in q_lower:
                return (
                    "A contract defines WHAT your data looks like:\n\n"
                    "- Field names and types\n"
                    "- Validation rules\n"
                    "- API shape\n\n"
                    "From one contract definition, we generate:\n"
                    "- Python dataclasses\n"
                    "- TypeScript interfaces\n"
                    "- API routes\n"
                    "- Markdown specs\n\n"
                    "The spec and code are the SAME thing - they can't disagree."
                )
        
        # Pattern questions
        if "pattern" in q_lower or "best practice" in q_lower:
            if "offline" in q_lower:
                return self._explain_pattern("offline_first")
            if "api" in q_lower or "backend" in q_lower:
                return self._explain_pattern("api_backend")
            if "crud" in q_lower or "todo" in q_lower:
                return self._explain_pattern("crud_app")
        
        # Why questions - use constraint reasoning
        if "why" in q_lower:
            if "storage" in q_lower:
                return (
                    "Why storage is fundamental:\n\n"
                    "Rule chain:\n"
                    "1. You want to persist data → need storage\n"
                    "2. crud_routes REQUIRES storage (can't save without it)\n"
                    "3. auth_basic REQUIRES storage (users need to be saved)\n"
                    "4. crdt_sync REQUIRES storage (sync needs local cache)\n\n"
                    "Storage is the foundation that other blocks build on."
                )
            if "auth" in q_lower:
                return (
                    "Why add authentication:\n\n"
                    "Rule chain:\n"
                    "1. Multiple users → need to identify who's who\n"
                    "2. User-specific data → need to filter by user\n"
                    "3. Security → need to protect routes\n\n"
                    "Add auth_basic if your app has any user-specific features."
                )
        
        # Fallback - analyze current state
        blocks = context.get("blocks", [])
        entities = context.get("entities", [])
        
        analysis = self.analyze(blocks, entities)
        
        if analysis.suggestions:
            return (
                f"Based on your current setup:\n\n"
                f"Completeness: {analysis.completeness_score}%\n\n"
                f"Top suggestion: {analysis.suggestions[0].title}\n"
                f"Reason: {analysis.suggestions[0].reason}\n\n"
                f"Next steps:\n" + "\n".join(f"- {s}" for s in analysis.next_steps)
            )
        
        return (
            "I can help with:\n\n"
            "- 'What block should I use for auth?'\n"
            "- 'How do I start a new project?'\n"
            "- 'What is CRDT?'\n"
            "- 'Why do I need storage?'\n"
            "- 'What pattern for offline apps?'\n\n"
            "Ask about blocks, patterns, or how-to questions."
        )
    
    def _explain_block(self, block_id: str) -> str:
        """Detailed explanation of a block."""
        explanations = {
            "auth_basic": (
                "**auth_basic** - Basic Authentication\n\n"
                "Provides:\n"
                "- User registration/login/logout\n"
                "- Session management\n"
                "- @login_required decorator\n"
                "- get_current_user() helper\n\n"
                "Requires: storage (for user credentials)\n\n"
                "Use when: Your app has user accounts or needs to protect routes."
            ),
            "storage_sqlite": (
                "**storage_sqlite** - SQLite Database\n\n"
                "Provides:\n"
                "- Persistent storage\n"
                "- SQL queries\n"
                "- Transactions\n"
                "- Works offline\n\n"
                "Requires: nothing (foundation block)\n\n"
                "Use when: You need a real database. Good for most apps."
            ),
            "storage_json": (
                "**storage_json** - JSON File Storage\n\n"
                "Provides:\n"
                "- Simple file-based persistence\n"
                "- No setup required\n"
                "- Human-readable data\n\n"
                "Requires: nothing\n\n"
                "Use when: Simple apps, prototypes, or local-only tools."
            ),
            "crud_routes": (
                "**crud_routes** - CRUD API Routes\n\n"
                "Provides:\n"
                "- GET /entity - list all\n"
                "- GET /entity/:id - get one\n"
                "- POST /entity - create\n"
                "- PUT /entity/:id - update\n"
                "- DELETE /entity/:id - delete\n\n"
                "Requires: storage\n\n"
                "Use when: You need a REST API for your entities."
            ),
            "crdt_sync": (
                "**crdt_sync** - CRDT Sync Engine\n\n"
                "Provides:\n"
                "- Offline-first operation\n"
                "- Automatic sync when online\n"
                "- Conflict-free merging\n"
                "- Real-time updates\n\n"
                "Requires: storage (for local cache)\n\n"
                "Use when: Offline support or collaborative editing needed."
            ),
        }
        return explanations.get(block_id, f"Block {block_id} not found in knowledge base.")
    
    def _explain_pattern(self, pattern_id: str) -> str:
        """Explain an architectural pattern."""
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return f"Pattern {pattern_id} not found."
            
        return (
            f"**{pattern['name']}**\n\n"
            f"{pattern['description']}\n\n"
            f"Required blocks: {', '.join(pattern['required_blocks'])}\n"
            f"Suggested blocks: {', '.join(pattern['suggested_blocks']) or 'none'}\n"
            f"Entities needed: {pattern['min_entities']}+\n\n"
            f"Drag the required blocks to the canvas and create at least one entity."
        )


def get_advisor() -> LogicAdvisor:
    """Get the singleton advisor instance."""
    return LogicAdvisor()


# API for the builder server
def analyze_state(blocks: List[str], entities: List[Dict]) -> Dict:
    """API-friendly analysis function."""
    advisor = LogicAdvisor()
    analysis = advisor.analyze(blocks, entities)
    
    return {
        "completeness": analysis.completeness_score,
        "suggestions": [
            {
                "category": s.category,
                "title": s.title,
                "reason": s.reason,
                "action": s.action,
                "priority": s.priority
            }
            for s in analysis.suggestions
        ],
        "warnings": analysis.warnings,
        "next_steps": analysis.next_steps,
        "satisfied": analysis.satisfied_capabilities,
        "missing": analysis.missing_requirements
    }


def ask_question(question: str, context: Dict) -> str:
    """API-friendly question answering."""
    advisor = LogicAdvisor()
    return advisor.ask(question, context)


# CLI demo
if __name__ == "__main__":
    import sys
    
    advisor = LogicAdvisor()
    
    print("=" * 60)
    print("LOGIC ADVISOR - Deterministic Guidance")
    print("=" * 60)
    print()
    
    # Demo 1: Empty state
    print("## Scenario 1: Empty canvas")
    analysis = advisor.analyze([], [])
    print(f"Completeness: {analysis.completeness_score}%")
    print(f"Suggestions: {len(analysis.suggestions)}")
    for s in analysis.suggestions:
        print(f"  [{s.priority}] {s.title}")
        print(f"      {s.reason}")
    print()
    
    # Demo 2: Has entities, no blocks
    print("## Scenario 2: Entity but no blocks")
    analysis = advisor.analyze([], [{"name": "Task", "fields": [{"name": "title", "type": "string"}]}])
    print(f"Completeness: {analysis.completeness_score}%")
    for s in analysis.suggestions[:2]:
        print(f"  [{s.priority}] {s.title}")
    print()
    
    # Demo 3: Missing dependency
    print("## Scenario 3: CRUD routes without storage")
    analysis = advisor.analyze(["crud_routes"], [])
    print(f"Completeness: {analysis.completeness_score}%")
    print(f"Warnings: {analysis.warnings}")
    for s in analysis.suggestions[:2]:
        print(f"  [{s.priority}] {s.title}: {s.reason}")
    print()
    
    # Demo 4: Complete setup
    print("## Scenario 4: Complete CRUD app")
    analysis = advisor.analyze(
        ["storage_sqlite", "crud_routes", "auth_basic"],
        [{"name": "Task", "fields": [{"name": "title", "type": "string"}]}]
    )
    print(f"Completeness: {analysis.completeness_score}%")
    print(f"Satisfied: {analysis.satisfied_capabilities}")
    print(f"Next steps: {analysis.next_steps}")
    print()
    
    # Demo 5: Question answering
    print("## Question Answering Demo")
    questions = [
        "What block should I use for auth?",
        "How do I start?",
        "What is CRDT?",
        "Why do I need storage?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        print(f"A: {advisor.ask(q, {})[:200]}...")
    
    print("\n" + "=" * 60)
    print("All analysis done with ZERO AI calls.")
    print("Instant. Deterministic. Explainable.")
    print("=" * 60)
