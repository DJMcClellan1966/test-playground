"""
Template Synthesis Engine
=========================

Auto-generates micro-templates based on app descriptions.
When the algebra can't find existing templates, synthesis creates new ones.

Key insight: Most app concepts follow predictable patterns:
- "with X" → has_X pattern (fields: X_list, X_count)
- "X tracking" → tracks_X pattern (fields: X_history, X_current)
- "X info/data" → has_X_info pattern (fields: X_*)
- Plurals → collection pattern (fields: items, count)

NO AI - pure pattern matching and rule application.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
import re
from template_algebra import (
    MicroTemplate, TemplateAlgebra, MICRO_TEMPLATES, 
    UniversalPattern, algebra
)


# =============================================================================
# SYNTHESIS PATTERNS
# =============================================================================

# Common field suffixes for different concept types
FIELD_PATTERNS = {
    'quantity': ['_count', '_total', '_amount'],
    'collection': ['_list', '_items', 's'],
    'temporal': ['_at', '_date', '_time', '_timestamp'],
    'identity': ['_id', '_name', '_title'],
    'state': ['_status', '_state', '_active'],
    'measure': ['_value', '_score', '_level'],
    'text': ['_text', '_content', '_description'],
    'reference': ['_id', '_ref', '_link'],
}

# Concept extraction patterns
CONCEPT_PATTERNS = [
    # "with X" → has_X
    (r'\bwith\s+(\w+(?:\s+\w+)?)\b', 'has_{concept}'),
    # "X tracking/tracker" → tracks_X
    (r'\b(\w+)\s+track(?:ing|er)?\b', 'tracks_{concept}'),
    # "track X" → tracks_X  
    (r'\btrack(?:s|ing)?\s+(\w+)\b', 'tracks_{concept}'),
    # "X info/information/data" → has_X_info
    (r'\b(\w+)\s+(?:info(?:rmation)?|data)\b', 'has_{concept}_info'),
    # "X history" → has_X_history
    (r'\b(\w+)\s+history\b', 'has_{concept}_history'),
    # "X management" → manages_X
    (r'\b(\w+)\s+manage(?:ment|r)?\b', 'manages_{concept}'),
    # "manage X" → manages_X
    (r'\bmanage(?:s|ment)?\s+(\w+)\b', 'manages_{concept}'),
    # "X settings/preferences" → has_X_settings
    (r'\b(\w+)\s+(?:settings?|preferences?|config)\b', 'has_{concept}_settings'),
    # "X stats/statistics" → has_X_stats
    (r'\b(\w+)\s+(?:stats?|statistics?|analytics?)\b', 'has_{concept}_stats'),
    # "X notifications/alerts" → has_X_alerts
    (r'\b(\w+)\s+(?:notification|alert|reminder)s?\b', 'has_{concept}_alerts'),
]

# Domain-specific field generators
DOMAIN_FIELDS = {
    # Food/Recipe domain
    'nutrition': ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sodium'],
    'ingredient': ['ingredient_name', 'ingredient_amount', 'ingredient_unit'],
    'recipe': ['prep_time', 'cook_time', 'servings', 'difficulty'],
    'meal': ['meal_type', 'meal_time', 'portion_size'],
    
    # Fitness domain
    'workout': ['exercise_type', 'sets', 'reps', 'weight', 'duration'],
    'exercise': ['exercise_name', 'muscle_group', 'equipment'],
    'fitness': ['current_weight', 'goal_weight', 'activity_level'],
    'health': ['heart_rate', 'blood_pressure', 'sleep_hours'],
    
    # Finance domain
    'expense': ['expense_amount', 'expense_category', 'expense_date'],
    'income': ['income_source', 'income_amount', 'income_frequency'],
    'budget': ['budget_limit', 'budget_category', 'budget_period'],
    'transaction': ['transaction_type', 'transaction_amount', 'transaction_date'],
    
    # Time/Planning domain
    'schedule': ['start_time', 'end_time', 'duration', 'recurring'],
    'deadline': ['due_date', 'priority', 'reminder_date'],
    'event': ['event_date', 'event_location', 'event_duration'],
    'habit': ['habit_frequency', 'streak_count', 'last_completed'],
    
    # Media domain
    'media': ['media_type', 'media_url', 'media_size'],
    'image': ['image_url', 'image_width', 'image_height', 'thumbnail_url'],
    'video': ['video_url', 'video_duration', 'video_thumbnail'],
    'audio': ['audio_url', 'audio_duration', 'audio_format'],
    
    # Social domain
    'profile': ['display_name', 'avatar_url', 'bio', 'location'],
    'contact': ['email', 'phone', 'address'],
    'message': ['message_content', 'sender_id', 'sent_at', 'read_at'],
    
    # Location domain
    'location': ['latitude', 'longitude', 'address', 'city', 'country'],
    'address': ['street', 'city', 'state', 'zip_code', 'country'],
    
    # Inventory domain
    'inventory': ['quantity', 'reorder_level', 'unit_price', 'sku'],
    'stock': ['stock_quantity', 'stock_location', 'last_restocked'],
    'product': ['product_name', 'product_price', 'product_sku', 'product_category'],
    
    # Learning domain
    'progress': ['progress_percent', 'completed_items', 'total_items'],
    'score': ['score_value', 'max_score', 'attempt_count'],
    'quiz': ['question_count', 'time_limit', 'passing_score'],
    'flashcard': ['front_text', 'back_text', 'difficulty', 'last_reviewed'],
}

# Operation templates for different template types
OPERATION_TEMPLATES = {
    'has': ['add_{name}', 'remove_{name}', 'get_{name}', 'update_{name}'],
    'tracks': ['record_{name}', 'get_{name}_history', 'get_current_{name}', 'clear_{name}'],
    'manages': ['create_{name}', 'delete_{name}', 'list_{name}s', 'update_{name}'],
    'is': ['check_if_{name}', 'set_{name}', 'toggle_{name}'],
}


@dataclass
class SynthesizedTemplate:
    """A dynamically generated micro-template."""
    id: str
    description: str
    fields: List[str]
    operations: List[str]
    source_concept: str
    pattern_used: str
    confidence: float  # 0-1, how confident we are in this synthesis
    
    def to_micro_template(self, pattern: UniversalPattern = UniversalPattern.STATE) -> MicroTemplate:
        """Convert to a proper MicroTemplate."""
        # Convert string fields to dict format expected by MicroTemplate
        field_dicts = [{'name': f, 'type': 'str'} for f in self.fields]
        
        return MicroTemplate(
            id=self.id,
            name=self.id.replace('_', ' ').title(),  # Convert id to readable name
            pattern=pattern,
            description=self.description,
            fields=field_dicts,
            operations=self.operations,
            keywords=[self.source_concept.replace('_', ' ')],
        )


class TemplateSynthesizer:
    """
    Synthesizes new micro-templates from app descriptions.
    
    Works in stages:
    1. Extract concepts not covered by existing templates
    2. Determine appropriate template pattern (has/tracks/manages/is)
    3. Generate fields based on domain knowledge
    4. Create operations from template
    """
    
    def __init__(self, existing_algebra: TemplateAlgebra = None):
        self.algebra = existing_algebra or algebra
        self.synthesized: Dict[str, SynthesizedTemplate] = {}
        self.synthesis_history: List[Tuple[str, List[str]]] = []
    
    def get_covered_concepts(self) -> Set[str]:
        """Get all concepts covered by existing templates."""
        covered = set()
        for template in MICRO_TEMPLATES.values():
            # Add keywords
            covered.update(kw.lower() for kw in template.keywords)
            # Add template id words
            covered.update(template.id.replace('_', ' ').split())
            # Add field name stems (fields can be dicts or strings)
            for f in template.fields:
                if isinstance(f, dict):
                    fname = f.get('name', '')
                else:
                    fname = str(f)
                stem = fname.replace('_', ' ').split()[0] if fname else ''
                if stem:
                    covered.add(stem)
        return covered
    
    def extract_uncovered_concepts(self, description: str) -> List[Tuple[str, str]]:
        """
        Find concepts in description not covered by existing templates.
        Returns list of (concept, suggested_template_name).
        """
        desc_lower = description.lower()
        covered = self.get_covered_concepts()
        uncovered = []
        seen_base_concepts = set()  # Track base concepts (first word) to avoid duplicates
        
        # Stopwords to skip
        stopwords = {'and', 'or', 'the', 'a', 'an', 'with', 'for', 'to', 'from', 'of', 'in', 'on', 'at', 'by', 'be'}
        
        for pattern, template_format in CONCEPT_PATTERNS:
            for match in re.finditer(pattern, desc_lower):
                concept = match.group(1).strip()
                
                # Skip if concept is a stopword
                if concept in stopwords:
                    continue
                
                # Get base concept (first meaningful word)
                concept_words = concept.split()
                base_concept = concept_words[0] if concept_words else concept
                
                # Skip if we've already handled this base concept
                if base_concept in seen_base_concepts:
                    continue
                
                # Normalize concept
                concept_normalized = concept.replace(' ', '_')
                
                # Check if already covered
                concept_word_set = set(concept.split())
                if not concept_word_set.intersection(covered):
                    template_name = template_format.format(concept=concept_normalized)
                    if template_name not in self.synthesized:
                        uncovered.append((concept, template_name))
                        seen_base_concepts.add(base_concept)
        
        return uncovered
    
    def infer_fields(self, concept: str, template_type: str) -> List[str]:
        """Infer fields for a concept based on domain knowledge."""
        concept_normalized = concept.replace(' ', '_').lower()
        fields = []
        
        # Check domain-specific fields first
        for domain, domain_fields in DOMAIN_FIELDS.items():
            if domain in concept_normalized or concept_normalized in domain:
                fields.extend(domain_fields[:4])  # Take up to 4 most relevant
                break
        
        # If no domain match, generate generic fields based on template type
        if not fields:
            if template_type.startswith('has_'):
                fields = [
                    f'{concept_normalized}_id',
                    f'{concept_normalized}_name',
                    f'{concept_normalized}_data',
                ]
            elif template_type.startswith('tracks_'):
                fields = [
                    f'current_{concept_normalized}',
                    f'{concept_normalized}_history',
                    f'{concept_normalized}_updated_at',
                ]
            elif template_type.startswith('manages_'):
                fields = [
                    f'{concept_normalized}_list',
                    f'{concept_normalized}_count',
                    f'active_{concept_normalized}',
                ]
            elif template_type.startswith('has_') and template_type.endswith('_info'):
                base = concept_normalized
                fields = [
                    f'{base}_summary',
                    f'{base}_details',
                    f'{base}_metadata',
                ]
            elif template_type.endswith('_history'):
                base = concept_normalized
                fields = [
                    f'{base}_entries',
                    f'{base}_first_entry',
                    f'{base}_last_entry',
                ]
            elif template_type.endswith('_stats'):
                base = concept_normalized
                fields = [
                    f'{base}_total',
                    f'{base}_average',
                    f'{base}_min',
                    f'{base}_max',
                ]
            else:
                # Fallback generic
                fields = [
                    f'{concept_normalized}_value',
                    f'{concept_normalized}_enabled',
                ]
        
        return fields
    
    def generate_operations(self, concept: str, template_type: str) -> List[str]:
        """Generate operations for a synthesized template."""
        concept_normalized = concept.replace(' ', '_').lower()
        
        # Determine operation prefix
        if template_type.startswith('has_'):
            ops_template = OPERATION_TEMPLATES['has']
        elif template_type.startswith('tracks_'):
            ops_template = OPERATION_TEMPLATES['tracks']
        elif template_type.startswith('manages_'):
            ops_template = OPERATION_TEMPLATES['manages']
        elif template_type.startswith('is_'):
            ops_template = OPERATION_TEMPLATES['is']
        else:
            ops_template = OPERATION_TEMPLATES['has']  # default
        
        return [op.format(name=concept_normalized) for op in ops_template]
    
    def synthesize_template(self, concept: str, template_name: str) -> SynthesizedTemplate:
        """Synthesize a new micro-template for a concept."""
        fields = self.infer_fields(concept, template_name)
        operations = self.generate_operations(concept, template_name)
        
        # Determine confidence based on domain match
        confidence = 0.5  # base confidence
        concept_lower = concept.lower()
        for domain in DOMAIN_FIELDS:
            if domain in concept_lower or concept_lower in domain:
                confidence = 0.85
                break
        
        # Higher confidence for common patterns
        if any(template_name.startswith(p) for p in ['has_', 'tracks_', 'manages_']):
            confidence += 0.1
        
        template = SynthesizedTemplate(
            id=template_name,
            description=f"Auto-generated template for '{concept}'",
            fields=fields,
            operations=operations,
            source_concept=concept,
            pattern_used=template_name.split('_')[0] if '_' in template_name else 'has',
            confidence=min(confidence, 1.0),
        )
        
        self.synthesized[template_name] = template
        return template
    
    def synthesize_for_description(self, description: str) -> List[SynthesizedTemplate]:
        """
        Synthesize all needed templates for an app description.
        
        Returns newly synthesized templates (doesn't include existing ones).
        """
        uncovered = self.extract_uncovered_concepts(description)
        new_templates = []
        
        for concept, template_name in uncovered:
            # Skip if we already have something similar
            if template_name not in self.synthesized:
                template = self.synthesize_template(concept, template_name)
                new_templates.append(template)
        
        # Record synthesis history
        if new_templates:
            self.synthesis_history.append((
                description,
                [t.id for t in new_templates]
            ))
        
        return new_templates
    
    def get_all_templates(self) -> List[SynthesizedTemplate]:
        """Get all synthesized templates."""
        return list(self.synthesized.values())
    
    def register_synthesized(self, synth_template: SynthesizedTemplate):
        """
        Register a synthesized template into the algebra for use.
        """
        micro = synth_template.to_micro_template()
        MICRO_TEMPLATES[synth_template.id] = micro
        self.algebra.templates[synth_template.id] = micro


# =============================================================================
# SMART SYNTHESIS
# =============================================================================

class SmartSynthesizer:
    """
    Higher-level synthesizer that combines extraction, synthesis, and algebra.
    
    Flow:
    1. Try existing algebra first
    2. If gaps found, synthesize new templates
    3. Register new templates
    4. Return complete composition
    """
    
    def __init__(self):
        self.synthesizer = TemplateSynthesizer()
        self.algebra = algebra
    
    def analyze_and_synthesize(self, description: str) -> Dict:
        """
        Full analysis: detect existing + synthesize new templates.
        
        Returns dict with:
        - existing_templates: templates from algebra
        - synthesized_templates: newly created templates
        - all_fields: combined fields
        - all_operations: combined operations
        - suggestions: what else might be useful
        """
        # Step 1: Get existing template matches
        existing = self.algebra.detect_templates(description)
        
        # Step 2: Synthesize new templates for uncovered concepts
        synthesized = self.synthesizer.synthesize_for_description(description)
        
        # Step 3: Register synthesized templates
        for synth in synthesized:
            self.synthesizer.register_synthesized(synth)
        
        # Step 4: Combine everything
        all_fields = []
        all_operations = []
        
        # Helper to extract field name
        def get_field_name(f):
            if isinstance(f, dict):
                return f.get('name', '')
            return str(f)
        
        # From existing
        for template_id in existing:
            if template_id in MICRO_TEMPLATES:
                t = MICRO_TEMPLATES[template_id]
                all_fields.extend(get_field_name(f) for f in t.fields if get_field_name(f))
                all_operations.extend(t.operations)
        
        # From synthesized
        for synth in synthesized:
            all_fields.extend(synth.fields)
            all_operations.extend(synth.operations)
        
        # Step 5: Get suggestions
        if existing:
            composed = self.algebra.compose('Entity', existing)
            # suggest_templates takes (description, current_templates)
            suggestions = self.algebra.suggest_templates(description, existing)
        else:
            suggestions = []
        
        return {
            'existing_templates': existing,
            'synthesized_templates': [s.id for s in synthesized],
            'synthesized_details': [{
                'id': s.id,
                'concept': s.source_concept,
                'fields': s.fields,
                'operations': s.operations,
                'confidence': s.confidence,
            } for s in synthesized],
            'all_fields': list(dict.fromkeys(all_fields)),  # dedupe, preserve order
            'all_operations': list(dict.fromkeys(all_operations))[:10],  # limit operations
            'suggestions': suggestions,
        }
    
    def generate_model_code(self, description: str) -> str:
        """Generate model code including synthesized fields."""
        analysis = self.analyze_and_synthesize(description)
        
        lines = ['# Auto-generated model with synthesized fields', '']
        
        # Add imports
        lines.append('from dataclasses import dataclass, field')
        lines.append('from typing import List, Optional, Dict, Any')
        lines.append('from datetime import datetime')
        lines.append('')
        
        # Generate model class
        model_name = 'GeneratedModel'
        lines.append('@dataclass')
        lines.append(f'class {model_name}:')
        lines.append('    """Model with fields from template algebra + synthesis."""')
        lines.append('    id: str')
        
        # Add fields
        for f in analysis['all_fields']:
            # Infer type from field name
            if any(f.endswith(s) for s in ['_at', '_date', '_time']):
                field_type = 'Optional[datetime] = None'
            elif any(f.endswith(s) for s in ['_list', '_items', 's', '_history']):
                field_type = 'List[Any] = field(default_factory=list)'
            elif any(f.endswith(s) for s in ['_count', '_total', '_amount', '_value']):
                field_type = 'int = 0'
            elif any(f.endswith(s) for s in ['_enabled', '_active']):
                field_type = 'bool = False'
            elif any(f.endswith(s) for s in ['_url', '_path']):
                field_type = 'Optional[str] = None'
            else:
                field_type = 'Optional[str] = None'
            
            lines.append(f'    {f}: {field_type}')
        
        # Add operation methods
        lines.append('')
        for op in analysis['all_operations'][:5]:  # limit to 5 ops
            method_name = op.replace(' ', '_')
            lines.append(f'    def {method_name}(self, *args, **kwargs):')
            lines.append(f'        """Auto-generated operation: {op}"""')
            lines.append('        pass')
            lines.append('')
        
        return '\n'.join(lines)


# Global instance
smart_synth = SmartSynthesizer()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def synthesize(description: str) -> Dict:
    """Analyze description and synthesize any needed templates."""
    return smart_synth.analyze_and_synthesize(description)


def generate_code(description: str) -> str:
    """Generate model code for a description."""
    return smart_synth.generate_model_code(description)


# =============================================================================
# DEMO / TEST
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("TEMPLATE SYNTHESIS ENGINE")
    print("=" * 60)
    
    test_cases = [
        "a recipe app with nutritional information and meal planning",
        "a workout tracker with exercise history and fitness goals",
        "a budget manager with expense tracking and income data",
        "a habit tracker with streak stats and progress history",
        "a photo gallery with location data and media management",
        "a flashcard app with quiz scores and learning progress",
    ]
    
    for desc in test_cases:
        print(f"\n--- {desc} ---")
        result = synthesize(desc)
        
        print(f"  Existing: {result['existing_templates']}")
        print(f"  Synthesized: {result['synthesized_templates']}")
        
        if result['synthesized_details']:
            print(f"  New template details:")
            for detail in result['synthesized_details']:
                print(f"    • {detail['id']}: {detail['fields'][:3]}... (conf: {detail['confidence']:.0%})")
        
        print(f"  All fields ({len(result['all_fields'])}): {result['all_fields'][:5]}...")
    
    print("\n" + "=" * 60)
    print("CODE GENERATION EXAMPLE")
    print("=" * 60)
    
    code = generate_code("a recipe app with nutritional information")
    print(code)
