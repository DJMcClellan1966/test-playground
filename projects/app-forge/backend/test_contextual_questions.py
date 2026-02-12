"""Test contextual question generation"""
import sys
sys.path.insert(0, '.')

from smartq import generate_contextual_questions, get_all_questions_with_context
from intent_graph import intent_match
from question_generator import ContextualQuestionGenerator

def test_contextual_questions():
    """Test contextual question generation"""
    test_cases = [
        ("a recipe collection app with meal planning", "crud"),
        ("a social workout tracker where users share progress", "crud"),
        ("a multiplayer trivia game with leaderboards", "quiz"),
        ("a mobile habit tracker with daily reminders", "crud"),
    ]
    
    print("="*70)
    print("CONTEXTUAL QUESTION GENERATION TESTS")
    print("="*70)
    
    gen = ContextualQuestionGenerator()
    
    for desc, template_id in test_cases:
        print(f"\n{desc}")
        print(f"Template: {template_id}")
        print("-"*70)
        
        # Get activated concepts
        activated = intent_match(desc)
        
        # Generate contextual questions
        contextual_qs = gen.generate(desc, template_id, activated)
        
        print(f"Generated {len(contextual_qs)} contextual questions:")
        for q in contextual_qs[:5]:
            print(f"  [{q['source']}] {q['text']}")
            print(f"      Relevance: {q['relevance']:.2f}")
        
        # Test integration
        answered = {'has_data': True}
        all_qs = get_all_questions_with_context(desc, template_id, answered)
        print(f"\nTotal questions (base + contextual): {len(all_qs)}")
    
    print("\n" + "="*70)
    print("✓ All tests completed successfully!")
    print("="*70)

if __name__ == '__main__':
    test_contextual_questions()
