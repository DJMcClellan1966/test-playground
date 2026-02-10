"""
Blueprint Advisor - Keyword-Based Recommendation Engine

Helps users find the right blueprint through simple keyword matching.
No LLM required - uses predefined rules and keyword analysis.

Usage:
    python advisor.py                    # Interactive mode
    python advisor.py --keywords "todo tasks deadlines"
    python advisor.py --project-type api
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Blueprint directory
BLUEPRINTS_DIR = Path(__file__).parent


# ============================================================================
# BLUEPRINT KNOWLEDGE BASE
# ============================================================================

BLUEPRINT_PROFILES = {
    "task-manager": {
        "title": "Task Manager / Todo App",
        "keywords": [
            "task", "todo", "checklist", "deadline", "reminder", "priority",
            "project", "productivity", "organize", "schedule", "recurring",
            "subtask", "progress", "complete", "due date", "assign", "track"
        ],
        "project_types": ["productivity", "personal", "team", "mobile"],
        "features": ["CRUD tasks", "deadlines", "priorities", "projects", "recurring tasks"],
        "complexity": "medium",
        "best_for": "Personal productivity, team coordination, project tracking"
    },
    
    "learning-app": {
        "title": "Learning App",
        "keywords": [
            "learn", "study", "education", "course", "lesson", "quiz",
            "flashcard", "spaced repetition", "progress", "skill", "knowledge",
            "tutorial", "training", "practice", "test", "memory", "retention"
        ],
        "project_types": ["education", "personal", "corporate", "mobile"],
        "features": ["Content library", "progress tracking", "quizzes", "spaced repetition"],
        "complexity": "medium-high",
        "best_for": "Educational apps, skill training, personal learning"
    },
    
    "notes-app": {
        "title": "Note-Taking App",
        "keywords": [
            "note", "write", "document", "markdown", "organize", "tag",
            "folder", "search", "sync", "rich text", "link", "attachment",
            "journal", "diary", "memo", "capture", "idea", "thought"
        ],
        "project_types": ["productivity", "personal", "creative", "mobile"],
        "features": ["Rich text editing", "organization", "search", "sync", "markdown"],
        "complexity": "medium",
        "best_for": "Personal notes, documentation, journaling"
    },
    
    "dashboard": {
        "title": "Dashboard / Analytics",
        "keywords": [
            "dashboard", "analytics", "chart", "graph", "metrics", "kpi",
            "report", "visualization", "data", "statistics", "monitor",
            "widget", "real-time", "trend", "insight", "overview"
        ],
        "project_types": ["business", "analytics", "enterprise", "web"],
        "features": ["Charts/graphs", "KPI widgets", "filters", "real-time updates"],
        "complexity": "medium-high",
        "best_for": "Business intelligence, monitoring, data visualization"
    },
    
    "api-backend": {
        "title": "API / Backend",
        "keywords": [
            "api", "backend", "rest", "graphql", "endpoint", "server",
            "database", "authentication", "authorization", "microservice",
            "crud", "webhook", "integration", "rate limit", "cache"
        ],
        "project_types": ["api", "backend", "microservice", "enterprise"],
        "features": ["REST/GraphQL", "Auth", "Database", "Caching", "Rate limiting"],
        "complexity": "medium-high",
        "best_for": "Backend services, APIs, microservices"
    },
    
    "personal-website": {
        "title": "Personal Website / Portfolio",
        "keywords": [
            "portfolio", "website", "personal", "blog", "resume", "cv",
            "showcase", "project", "contact", "about", "gallery", "bio",
            "landing page", "profile", "professional"
        ],
        "project_types": ["portfolio", "personal", "creative", "web"],
        "features": ["Project showcase", "About page", "Contact form", "Blog"],
        "complexity": "low-medium",
        "best_for": "Personal branding, job search, freelance"
    },
    
    "intelligent-tutoring-system": {
        "title": "Intelligent Tutoring System",
        "keywords": [
            "tutor", "adaptive", "personalized", "ai", "intelligent",
            "assessment", "curriculum", "skill", "mastery", "recommendation",
            "learning path", "prerequisite", "concept", "knowledge graph"
        ],
        "project_types": ["education", "ai", "enterprise", "research"],
        "features": ["Adaptive learning", "Knowledge mapping", "Personalized paths"],
        "complexity": "high",
        "best_for": "Advanced education platforms, AI-powered learning"
    },
    
    "research-knowledge-platform": {
        "title": "Research & Knowledge Platform",
        "keywords": [
            "research", "knowledge", "wiki", "documentation", "reference",
            "citation", "paper", "article", "annotation", "highlight",
            "bibliography", "academic", "collaborate", "version"
        ],
        "project_types": ["research", "academic", "enterprise", "collaborative"],
        "features": ["Document management", "Citations", "Collaboration", "Search"],
        "complexity": "high",
        "best_for": "Research teams, documentation hubs, knowledge management"
    }
}


# ============================================================================
# MATCHING ENGINE
# ============================================================================

def tokenize(text: str) -> List[str]:
    """Convert text to lowercase tokens."""
    return re.findall(r'\b\w+\b', text.lower())


def calculate_match_score(keywords: List[str], profile: Dict) -> float:
    """
    Calculate how well keywords match a blueprint profile.
    
    Returns a score from 0 to 1.
    """
    if not keywords:
        return 0.0
    
    profile_keywords = set(profile.get("keywords", []))
    input_keywords = set(keywords)
    
    # Direct matches
    matches = input_keywords & profile_keywords
    
    # Partial matches (check if input word is in any profile keyword)
    partial_matches = 0
    for word in input_keywords:
        for pk in profile_keywords:
            if word in pk or pk in word:
                partial_matches += 0.5
                break
    
    # Calculate score
    total_possible = len(input_keywords)
    match_count = len(matches) + partial_matches
    
    return min(1.0, match_count / total_possible) if total_possible > 0 else 0.0


def recommend_blueprints(
    keywords: Optional[List[str]] = None,
    project_type: Optional[str] = None,
    complexity: Optional[str] = None,
    limit: int = 3
) -> List[Tuple[str, Dict, float]]:
    """
    Recommend blueprints based on criteria.
    
    Args:
        keywords: List of relevant keywords
        project_type: Type of project (web, mobile, api, etc.)
        complexity: Desired complexity (low, medium, high)
        limit: Maximum recommendations to return
        
    Returns:
        List of (blueprint_name, profile, score) tuples
    """
    scores = []
    
    for name, profile in BLUEPRINT_PROFILES.items():
        score = 0.0
        
        # Keyword matching
        if keywords:
            keyword_score = calculate_match_score(keywords, profile)
            score += keyword_score * 0.6  # 60% weight
        
        # Project type matching
        if project_type:
            project_type_lower = project_type.lower()
            if project_type_lower in profile.get("project_types", []):
                score += 0.25  # 25% weight
            elif any(project_type_lower in pt for pt in profile.get("project_types", [])):
                score += 0.15  # Partial match
        
        # Complexity matching
        if complexity:
            complexity_lower = complexity.lower()
            profile_complexity = profile.get("complexity", "medium").lower()
            if complexity_lower in profile_complexity:
                score += 0.15  # 15% weight
        
        # Ensure minimum score for display
        if score > 0.1 or (not keywords and not project_type):
            scores.append((name, profile, score))
    
    # Sort by score descending
    scores.sort(key=lambda x: x[2], reverse=True)
    
    return scores[:limit]


def explain_recommendation(name: str, profile: Dict, score: float, keywords: List[str]) -> str:
    """Generate explanation for why a blueprint was recommended."""
    explanations = []
    
    # Find matching keywords
    if keywords:
        profile_kw = set(profile.get("keywords", []))
        matches = [k for k in keywords if k in profile_kw]
        if matches:
            explanations.append(f"Matches keywords: {', '.join(matches)}")
    
    explanations.append(f"Best for: {profile.get('best_for', 'General use')}")
    explanations.append(f"Complexity: {profile.get('complexity', 'medium')}")
    
    features = profile.get("features", [])
    if features:
        explanations.append(f"Key features: {', '.join(features[:3])}")
    
    return "\n    ".join(explanations)


# ============================================================================
# INTERACTIVE MODE
# ============================================================================

QUESTIONS = [
    {
        "id": "description",
        "question": "Describe your project in a few words:",
        "type": "text",
        "weight": "keywords"
    },
    {
        "id": "type",
        "question": "What type of project is this?",
        "type": "choice",
        "options": [
            ("1", "Personal / Side project", "personal"),
            ("2", "Business / Enterprise", "enterprise"),
            ("3", "API / Backend service", "api"),
            ("4", "Educational / Learning", "education"),
            ("5", "Portfolio / Website", "portfolio"),
        ],
        "weight": "project_type"
    },
    {
        "id": "complexity",
        "question": "Desired complexity level?",
        "type": "choice",
        "options": [
            ("1", "Simple - Just the basics", "low"),
            ("2", "Medium - Standard features", "medium"),
            ("3", "Complex - Full-featured", "high"),
        ],
        "weight": "complexity"
    }
]


def run_interactive():
    """Run interactive advisor session."""
    print("\n" + "=" * 60)
    print("🎯 Blueprint Advisor - Find Your Perfect Starting Point")
    print("=" * 60)
    print("\nAnswer a few questions to get personalized recommendations.\n")
    
    collected = {
        "keywords": [],
        "project_type": None,
        "complexity": None
    }
    
    for q in QUESTIONS:
        print(f"\n{q['question']}")
        
        if q["type"] == "text":
            response = input("> ").strip()
            if response:
                collected["keywords"] = tokenize(response)
        
        elif q["type"] == "choice":
            for key, label, value in q["options"]:
                print(f"  {key}. {label}")
            
            response = input("> ").strip()
            for key, label, value in q["options"]:
                if response == key or response.lower() == value.lower():
                    collected[q["weight"]] = value
                    break
    
    # Get recommendations
    print("\n" + "=" * 60)
    print("📋 Recommendations")
    print("=" * 60)
    
    recommendations = recommend_blueprints(
        keywords=collected["keywords"],
        project_type=collected["project_type"],
        complexity=collected["complexity"],
        limit=3
    )
    
    if not recommendations:
        print("\nNo strong matches found. Here are all available blueprints:\n")
        recommendations = [(name, profile, 0) for name, profile in BLUEPRINT_PROFILES.items()]
    
    for i, (name, profile, score) in enumerate(recommendations, 1):
        confidence = "High" if score > 0.5 else "Medium" if score > 0.2 else "Low"
        print(f"\n{i}. {profile['title']}")
        print(f"   Blueprint: {name}")
        print(f"   Match confidence: {confidence} ({score:.0%})")
        print(f"   {explain_recommendation(name, profile, score, collected['keywords'])}")
    
    print("\n" + "-" * 60)
    print("💡 Generate a project with:")
    print(f"   python scaffold.py {recommendations[0][0]} --name YourProject --generate")
    print()


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Find the right blueprint for your project"
    )
    
    parser.add_argument(
        "--keywords", "-k",
        help="Keywords describing your project (space-separated)"
    )
    
    parser.add_argument(
        "--project-type", "-t",
        choices=["personal", "business", "api", "education", "portfolio", 
                 "enterprise", "mobile", "web", "research"],
        help="Type of project"
    )
    
    parser.add_argument(
        "--complexity", "-c",
        choices=["low", "medium", "high"],
        help="Desired complexity level"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all blueprint profiles"
    )
    
    args = parser.parse_args()
    
    # List mode
    if args.list:
        print("\n📚 Available Blueprint Profiles:\n")
        for name, profile in BLUEPRINT_PROFILES.items():
            print(f"  {name}")
            print(f"    Title: {profile['title']}")
            print(f"    Best for: {profile['best_for']}")
            print(f"    Complexity: {profile['complexity']}")
            print()
        return
    
    # Quick recommendation mode
    if args.keywords or args.project_type or args.complexity:
        keywords = tokenize(args.keywords) if args.keywords else None
        
        recommendations = recommend_blueprints(
            keywords=keywords,
            project_type=args.project_type,
            complexity=args.complexity
        )
        
        print("\n📋 Recommendations:\n")
        for i, (name, profile, score) in enumerate(recommendations, 1):
            print(f"{i}. {profile['title']} ({name}) - {score:.0%} match")
            print(f"   {profile['best_for']}")
        print()
        return
    
    # Interactive mode
    run_interactive()


if __name__ == "__main__":
    main()
