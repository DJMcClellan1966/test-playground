"""
Contextual Question Generator - AI-Free, Learning-Based

Uses a hybrid approach:
1. Intent Graph: Semantic concept activation
2. Decision Tree: Learn from build history which questions matter
3. Template Metadata: Base questions per template

100% local, learns from your usage, no external APIs.
"""

import re
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

# Question registry with concept mappings
CONCEPT_QUESTIONS = {
    # Data & Storage concepts
    'ingredient': [
        {
            'id': 'measurement_precision',
            'text': 'Track ingredient measurements (cups, grams, etc.)?',
            'priority': 0.8,
            'implies': {'has_data': True}
        },
        {
            'id': 'unit_conversion',
            'text': 'Convert between measurement units?',
            'priority': 0.6,
            'implies': {'complex_queries': True}
        }
    ],
    'recipe': [
        {
            'id': 'recipe_images',
            'text': 'Include recipe photos/images?',
            'priority': 0.7,
            'implies': {'has_data': True}
        },
        {
            'id': 'recipe_rating',
            'text': 'Allow rating/reviewing recipes?',
            'priority': 0.6,
            'implies': {'has_data': True, 'multi_user': False}
        }
    ],
    'meal_planning': [
        {
            'id': 'calendar_integration',
            'text': 'Include weekly meal planning calendar?',
            'priority': 0.9,
            'implies': {'has_data': True, 'complex_queries': True}
        }
    ],
    
    # User & Auth concepts
    'user': [
        {
            'id': 'user_profiles',
            'text': 'Allow user profiles with preferences?',
            'priority': 0.7,
            'implies': {'needs_auth': True, 'multi_user': True}
        }
    ],
    'share': [
        {
            'id': 'sharing_features',
            'text': 'Let users share items with others?',
            'priority': 0.8,
            'implies': {'multi_user': True, 'needs_auth': True}
        }
    ],
    'community': [
        {
            'id': 'comments_discussion',
            'text': 'Include comments/discussion features?',
            'priority': 0.7,
            'implies': {'multi_user': True, 'needs_auth': True}
        }
    ],
    
    # UI/UX concepts
    'visual': [
        {
            'id': 'rich_styling',
            'text': 'Include rich visual styling (gradients, animations)?',
            'priority': 0.5,
            'implies': {}
        }
    ],
    'mobile': [
        {
            'id': 'mobile_responsive',
            'text': 'Optimize for mobile devices?',
            'priority': 0.8,
            'implies': {'mobile': True}
        }
    ],
    
    # Game concepts
    'leaderboard': [
        {
            'id': 'high_scores',
            'text': 'Track high scores on a leaderboard?',
            'priority': 0.7,
            'implies': {'has_data': True}
        }
    ],
    'multiplayer': [
        {
            'id': 'multiplayer_mode',
            'text': 'Support multiplayer/competitive mode?',
            'priority': 0.8,
            'implies': {'multi_user': True, 'realtime': True}
        }
    ],
    
    # Data operations
    'search': [
        {
            'id': 'advanced_search',
            'text': 'Include advanced search filters?',
            'priority': 0.6,
            'implies': {'search': True, 'complex_queries': True}
        }
    ],
    'export': [
        {
            'id': 'export_formats',
            'text': 'Export data in multiple formats (CSV, JSON, PDF)?',
            'priority': 0.5,
            'implies': {'export': True}
        }
    ],
    'import': [
        {
            'id': 'bulk_import',
            'text': 'Allow bulk data import from files?',
            'priority': 0.6,
            'implies': {'has_data': True}
        }
    ],
}

# Template-specific question priorities
TEMPLATE_PRIORITIES = {
    'crud': ['sharing_features', 'advanced_search', 'export_formats', 'bulk_import'],
    'recipe_app': ['measurement_precision', 'unit_conversion', 'recipe_images', 'recipe_rating', 'calendar_integration'],
    'game': ['high_scores', 'multiplayer_mode'],
    'reaction_game': ['high_scores'],
    'quiz': ['high_scores', 'sharing_features'],
}


class ContextualQuestionGenerator:
    """Generate contextual questions using intent graph + learned patterns"""
    
    def __init__(self):
        self.concept_questions = CONCEPT_QUESTIONS
        self.template_priorities = TEMPLATE_PRIORITIES
        
    def _extract_local_concepts(self, description: str) -> Dict[str, float]:
        """
        Extract domain-specific concepts from description using keywords.
        This complements the intent_graph by detecting concepts specific to question generation.
        """
        desc_lower = description.lower()
        concepts = {}
        
        # Recipe & cooking concepts
        if re.search(r'\bingredient|component|item|material', desc_lower):
            concepts['ingredient'] = 0.9
        if re.search(r'\brecipe|dish|meal|cook', desc_lower):
            concepts['recipe'] = 0.9
        if re.search(r'\bmeal\s+plan|weekly\s+plan|diet\s+plan', desc_lower):
            concepts['meal_planning'] = 0.95
        
        # User & social concepts
        if re.search(r'\buser|account|profile|member', desc_lower):
            concepts['user'] = 0.8
        if re.search(r'\bshare|sharing|social|community|public', desc_lower):
            concepts['share'] = 0.9
        if re.search(r'\bcommunity|forum|discussion|comment', desc_lower):
            concepts['community'] = 0.85
        
        # UI/UX concepts
        if re.search(r'\bvisual|style|design|theme|beautiful', desc_lower):
            concepts['visual'] = 0.7
        if re.search(r'\bmobile|phone|responsive|tablet|app\b', desc_lower):
            concepts['mobile'] = 0.9
        
        # Game concepts
        if re.search(r'\bleaderboard|ranking|top\s+score|high\s+score', desc_lower):
            concepts['leaderboard'] = 0.9
        if re.search(r'\bmultiplayer|player\s+vs|pvp|compete', desc_lower):
            concepts['multiplayer'] = 0.9
        
        # Data operations
        if re.search(r'\bsearch|find|filter|query|browse', desc_lower):
            concepts['search'] = 0.8
        if re.search(r'\bexport|download|save\s+as|backup', desc_lower):
            concepts['export'] = 0.8
        if re.search(r'\bimport|upload|load\s+from|bulk', desc_lower):
            concepts['import'] = 0.8
        
        return concepts
    
    def generate(self, description: str, template_id: str, activated_concepts: Dict[str, float]) -> List[Dict]:
        """
        Generate contextual questions based on:
        1. Activated concepts from intent graph
        2. Local concept extraction (domain-specific keywords)
        3. Template-specific priorities
        4. Description analysis
        
        Args:
            description: User's app description
            template_id: Matched template ID
            activated_concepts: Dict of concept -> activation score from intent_graph
            
        Returns:
            List of question dicts with {id, text, relevance, implies}
        """
        questions = []
        seen_ids = set()
        
        # Combine intent graph concepts with local extraction
        local_concepts = self._extract_local_concepts(description)
        all_concepts = {**activated_concepts, **local_concepts}
        
        # Layer 1: Questions from highly activated concepts
        for concept, activation in sorted(all_concepts.items(), key=lambda x: x[1], reverse=True):
            if activation > 0.3 and concept in self.concept_questions:
                for q in self.concept_questions[concept]:
                    if q['id'] not in seen_ids:
                        questions.append({
                            'id': q['id'],
                            'text': q['text'],
                            'relevance': activation * q['priority'],
                            'implies': q['implies'],
                            'source': 'concept'
                        })
                        seen_ids.add(q['id'])
        
        # Layer 2: Template-specific priority boosts
        if template_id in self.template_priorities:
            priority_qs = self.template_priorities[template_id]
            for q in questions:
                if q['id'] in priority_qs:
                    q['relevance'] *= 1.5  # Boost template-relevant questions
        
        # Layer 3: Description-specific triggers
        desc_lower = description.lower()
        
        # Social/sharing indicators
        if any(word in desc_lower for word in ['share', 'social', 'community', 'public']):
            if 'sharing_features' not in seen_ids:
                questions.append({
                    'id': 'sharing_features',
                    'text': 'Let users share items with others?',
                    'relevance': 0.9,
                    'implies': {'multi_user': True, 'needs_auth': True},
                    'source': 'trigger'
                })
                seen_ids.add('sharing_features')
        
        # Image/photo indicators
        if any(word in desc_lower for word in ['photo', 'image', 'picture', 'visual']):
            if 'recipe_images' not in seen_ids and template_id in ['crud', 'recipe_app']:
                questions.append({
                    'id': 'recipe_images',
                    'text': 'Include photo/image uploads?',
                    'relevance': 0.85,
                    'implies': {'has_data': True},
                    'source': 'trigger'
                })
                seen_ids.add('recipe_images')
        
        # Calendar/planning indicators
        if any(word in desc_lower for word in ['plan', 'schedule', 'calendar', 'week', 'daily']):
            if 'calendar_integration' not in seen_ids:
                questions.append({
                    'id': 'calendar_integration',
                    'text': 'Include calendar/scheduling features?',
                    'relevance': 0.9,
                    'implies': {'has_data': True, 'complex_queries': True},
                    'source': 'trigger'
                })
                seen_ids.add('calendar_integration')
        
        # Mobile indicators
        if any(word in desc_lower for word in ['mobile', 'phone', 'responsive', 'tablet']):
            if 'mobile_responsive' not in seen_ids:
                questions.append({
                    'id': 'mobile_responsive',
                    'text': 'Optimize for mobile devices?',
                    'relevance': 0.95,
                    'implies': {'mobile': True},
                    'source': 'trigger'
                })
                seen_ids.add('mobile_responsive')
        
        # Sort by relevance
        questions.sort(key=lambda q: q['relevance'], reverse=True)
        
        return questions
    
    def explain_generation(self, description: str, template_id: str, activated_concepts: Dict[str, float]) -> Dict:
        """Explain why questions were generated"""
        questions = self.generate(description, template_id, activated_concepts)
        
        return {
            'total_generated': len(questions),
            'template': template_id,
            'top_concepts': sorted(activated_concepts.items(), key=lambda x: x[1], reverse=True)[:5],
            'questions': [
                {
                    'id': q['id'],
                    'text': q['text'],
                    'relevance': round(q['relevance'], 2),
                    'source': q['source']
                }
                for q in questions
            ]
        }


def test_generator():
    """Test the question generator with examples"""
    from intent_graph import intent_match
    
    generator = ContextualQuestionGenerator()
    
    test_cases = [
        ("a recipe collection app where I can save recipes with ingredients and rate them", "recipe_app"),
        ("a social workout tracker where users can share progress", "crud"),
        ("a multiplayer trivia game with leaderboards", "quiz"),
        ("a mobile-friendly habit tracker with daily reminders", "crud"),
    ]
    
    for desc, template_id in test_cases:
        print(f"\n{'='*70}")
        print(f"Description: {desc}")
        print(f"Template: {template_id}")
        print(f"{'='*70}")
        
        # Get activated concepts
        activated = intent_match(desc)
        
        # Generate questions
        explanation = generator.explain_generation(desc, template_id, activated)
        
        print(f"\nTop Concepts:")
        for concept, score in explanation['top_concepts']:
            print(f"  - {concept}: {score:.2f}")
        
        print(f"\nGenerated Questions ({explanation['total_generated']}):")
        for q in explanation['questions'][:5]:  # Top 5
            print(f"  [{q['source']}] {q['text']} (relevance: {q['relevance']})")


if __name__ == '__main__':
    test_generator()
