"""
Developer Profile - Personalized generation based on your coding patterns.

Reads from prompt_twin's profile to personalize app generation:
- Framework preferences (Python → Flask/FastAPI, not Express)
- Feature defaults (you use Auth often → auto-suggest)
- Technology coherence (you use SQLite → default to it)
- Language preferences (infer from your codebase)

This makes the builder adapt to YOUR style, not generic templates.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path


# Path to prompt_twin profile
PROMPT_TWIN_PROFILE = Path(__file__).parent.parent.parent.parent / 'blueprints' / '.prompt_twin' / 'profile.json'


@dataclass
class DeveloperPreferences:
    """Extracted developer preferences from profile."""
    preferred_framework: str = 'flask'  # Default
    preferred_language: str = 'python'
    preferred_database: str = 'sqlite'
    common_technologies: Set[str] = field(default_factory=set)
    common_project_types: Set[str] = field(default_factory=set)
    feature_tendencies: Dict[str, float] = field(default_factory=dict)  # feature → weight
    confidence: float = 0.0  # How confident we are in these preferences


class DeveloperProfile:
    """Reads and interprets developer profile from prompt_twin."""
    
    def __init__(self, profile_path: Path = PROMPT_TWIN_PROFILE):
        self.profile_path = profile_path
        self.profile = self._load_profile()
        self.preferences = self._extract_preferences()
    
    def _load_profile(self) -> Dict:
        """Load prompt_twin profile if available."""
        if self.profile_path.exists():
            try:
                return json.loads(self.profile_path.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}
    
    def _extract_preferences(self) -> DeveloperPreferences:
        """Extract preferences from profile data."""
        prefs = DeveloperPreferences()
        
        if not self.profile:
            return prefs
        
        # Extract language preferences
        languages = self.profile.get('languages', {})
        if languages:
            # Find most used language
            sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
            if sorted_langs:
                top_lang = sorted_langs[0][0]
                prefs.preferred_language = self._map_extension_to_language(top_lang)
                prefs.confidence += 0.2
        
        # Extract framework preferences
        technologies = self.profile.get('technologies', {})
        if technologies:
            prefs.common_technologies = set(technologies.keys())
            prefs.preferred_framework = self._infer_framework(technologies)
            prefs.confidence += 0.2
        
        # Extract project type patterns
        project_types = self.profile.get('project_types', {})
        if project_types:
            prefs.common_project_types = set(project_types.keys())
            prefs.confidence += 0.1
        
        # Extract feature tendencies from technologies
        prefs.feature_tendencies = self._infer_feature_tendencies(technologies)
        if prefs.feature_tendencies:
            prefs.confidence += 0.2
        
        # Extract database preference
        prefs.preferred_database = self._infer_database(technologies)
        if prefs.preferred_database != 'sqlite':
            prefs.confidence += 0.1
        
        return prefs
    
    def _map_extension_to_language(self, ext: str) -> str:
        """Map file extension to language name."""
        mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.cs': 'csharp',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
        }
        return mapping.get(ext, 'python')
    
    def _infer_framework(self, technologies: Dict) -> str:
        """Infer preferred framework from technologies."""
        # Priority order for Python frameworks
        if 'FastAPI' in technologies:
            return 'fastapi'
        if 'Flask' in technologies:
            return 'flask'
        if 'Django' in technologies:
            return 'django'
        
        # JS frameworks
        if 'React' in technologies:
            return 'react'
        if 'Vue' in technologies:
            return 'vue'
        if 'Express' in technologies:
            return 'express'
        
        return 'flask'  # Default
    
    def _infer_database(self, technologies: Dict) -> str:
        """Infer preferred database from technologies."""
        if 'PostgreSQL' in technologies:
            return 'postgresql'
        if 'MongoDB' in technologies:
            return 'mongodb'
        if 'SQLite' in technologies:
            return 'sqlite'
        
        return 'sqlite'  # Default (local-first)
    
    def _infer_feature_tendencies(self, technologies: Dict) -> Dict[str, float]:
        """Infer which features the developer commonly uses."""
        tendencies = {}
        
        # Map technologies to features
        tech_to_feature = {
            'Auth': ('auth', 0.9),
            'Machine Learning': ('ml_integration', 0.7),
            'WebSocket': ('realtime', 0.8),
            'RAG': ('search', 0.85),
            'OpenAI': ('ai_features', 0.7),
            'Ollama': ('ai_features', 0.8),
        }
        
        for tech, (feature, weight) in tech_to_feature.items():
            if tech in technologies:
                tendencies[feature] = weight
        
        return tendencies
    
    def get_framework_for_description(self, description: str) -> Tuple[str, float]:
        """Get recommended framework for a description, considering developer preferences."""
        desc_lower = description.lower()
        
        # Check if description explicitly mentions a framework
        explicit_frameworks = {
            'fastapi': 'fastapi',
            'flask': 'flask',
            'django': 'django',
            'react': 'react',
            'express': 'express',
        }
        
        for keyword, framework in explicit_frameworks.items():
            if keyword in desc_lower:
                return (framework, 1.0)  # Explicit mention = high confidence
        
        # Otherwise, use developer preference
        return (self.preferences.preferred_framework, self.preferences.confidence)
    
    def get_suggested_features(self) -> List[str]:
        """Get features the developer commonly uses."""
        return [f for f, weight in self.preferences.feature_tendencies.items() if weight > 0.5]
    
    def should_include_feature(self, feature: str) -> Tuple[bool, float]:
        """Check if a feature should be included based on developer patterns."""
        if feature in self.preferences.feature_tendencies:
            weight = self.preferences.feature_tendencies[feature]
            return (weight > 0.6, weight)
        return (False, 0.0)
    
    def explain_preferences(self) -> str:
        """Generate human-readable explanation of preferences."""
        if not self.profile:
            return "No developer profile found. Using defaults."
        
        lines = [
            f"Developer Profile (confidence: {self.preferences.confidence:.0%})",
            f"  Preferred framework: {self.preferences.preferred_framework}",
            f"  Preferred language: {self.preferences.preferred_language}",
            f"  Preferred database: {self.preferences.preferred_database}",
        ]
        
        if self.preferences.common_technologies:
            techs = list(self.preferences.common_technologies)[:5]
            lines.append(f"  Common technologies: {', '.join(techs)}")
        
        if self.preferences.feature_tendencies:
            features = [f for f in self.preferences.feature_tendencies.keys()][:4]
            lines.append(f"  Feature tendencies: {', '.join(features)}")
        
        return '\n'.join(lines)
    
    def personalize_context(self, context: Dict) -> Dict:
        """Add personalization to a generation context."""
        context['developer_profile'] = {
            'preferred_framework': self.preferences.preferred_framework,
            'preferred_language': self.preferences.preferred_language,
            'preferred_database': self.preferences.preferred_database,
            'technologies': list(self.preferences.common_technologies),
            'confidence': self.preferences.confidence,
        }
        return context


# Singleton instance
_developer_profile = None

def get_developer_profile() -> DeveloperProfile:
    """Get or create the developer profile singleton."""
    global _developer_profile
    if _developer_profile is None:
        _developer_profile = DeveloperProfile()
    return _developer_profile


# Quick test
if __name__ == '__main__':
    profile = get_developer_profile()
    
    print("=" * 60)
    print("DEVELOPER PROFILE - Personalization from prompt_twin")
    print("=" * 60)
    print()
    print(profile.explain_preferences())
    print()
    
    # Test framework inference
    test_descriptions = [
        "a recipe collection app",
        "a fastapi microservice",
        "a react dashboard",
        "a workout tracker",
    ]
    
    print("\nFramework Recommendations:")
    for desc in test_descriptions:
        framework, confidence = profile.get_framework_for_description(desc)
        print(f"  '{desc}' → {framework} ({confidence:.0%})")
    
    print("\nSuggested Features:", profile.get_suggested_features())
