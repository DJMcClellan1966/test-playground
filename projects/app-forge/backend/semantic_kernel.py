"""Semantic Kernel - Local LLM-Free Understanding Engine.

Replicates what LLMs do through compositional semantics, without neural networks.
This kernel understands app descriptions by combining:
  1. PARSE: Syntax analysis (dependency parsing)
  2. UNDERSTAND: Semantic similarity (word embeddings)
  3. KNOWLEDGE: Domain patterns (entity/action mappings)
  4. COMPOSE: Feature assembly (dependency resolution)

No external APIs, no LLM calls - just algorithmic pattern matching.
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field

from knowledge_base import (
    FieldDefinition,
    get_entity_fields,
    infer_field_type,
    extract_features_from_actions,
    infer_framework,
    ACTION_FEATURES,
    RELATIONSHIP_PATTERNS,
)


# =============================================================================
# LAYER 1: PARSE (Syntax Analysis)
# =============================================================================

@dataclass
class ParsedEntity:
    """An entity extracted from description."""
    name: str
    singular: str
    confidence: float = 1.0
    

@dataclass
class ParsedRelationship:
    """A relationship between two entities."""
    source: str
    target: str
    relation_type: str  # has_many, belongs_to, many_to_many


@dataclass
class ParsedAction:
    """An action verb found in description."""
    verb: str
    object_entity: Optional[str] = None
    confidence: float = 1.0


def extract_entities(description: str) -> List[ParsedEntity]:
    """Extract nouns that likely represent data entities.
    
    Heuristics (mimics what LLMs learn):
    - Capitalized words (proper nouns)
    - Plural nouns (collections)
    - Nouns after articles (a/an/the)
    - Nouns in "tracker for X" patterns
    """
    entities = []
    desc_lower = description.lower()
    
    # Pattern 1: "X tracker" → X is entity
    match = re.search(r'(\w+)\s+(?:tracker|collection|manager|organizer|planner|log)', desc_lower)
    if match:
        entity_name = match.group(1)
        entities.append(ParsedEntity(
            name=entity_name,
            singular=singularize(entity_name),
            confidence=0.9
        ))
    
    # Pattern 2: "track/manage/save X" → X is entity
    for verb in ['track', 'manage', 'save', 'store', 'organize', 'collect', 'log', 'record']:
        pattern = rf'{verb}\s+(\w+)'
        matches = re.findall(pattern, desc_lower)
        for match in matches:
            if match not in ['a', 'an', 'the', 'my', 'your', 'their', 'all', 'some']:
                entities.append(ParsedEntity(
                    name=match,
                    singular=singularize(match),
                    confidence=0.8
                ))
    
    # Pattern 3: "with X and Y" → X and Y might be entities
    pattern = r'with\s+(\w+)(?:\s+and\s+(\w+))?'
    matches = re.findall(pattern, desc_lower)
    for match in matches:
        for entity in match:
            if entity and entity not in ['a', 'an', 'the', 'my', 'that']:
                entities.append(ParsedEntity(
                    name=entity,
                    singular=singularize(entity),
                    confidence=0.6
                ))
    
    # Pattern 4: "for X" → X might be entity
    pattern = r'\s+for\s+(\w+)'
    matches = re.findall(pattern, desc_lower)
    for match in matches:
        if match not in ['a', 'an', 'the', 'my', 'me', 'you']:
            entities.append(ParsedEntity(
                name=match,
                singular=singularize(match),
                confidence=0.5
            ))
    
    # Deduplicate by name, keeping highest confidence
    seen = {}
    for entity in entities:
        if entity.name not in seen or entity.confidence > seen[entity.name].confidence:
            seen[entity.name] = entity
    
    return list(seen.values())


def extract_relationships(description: str, entities: List[ParsedEntity]) -> List[ParsedRelationship]:
    """Detect relationships between entities using prepositions."""
    relationships = []
    desc_lower = description.lower()
    
    if len(entities) < 2:
        return relationships
    
    # Look for relationship patterns
    for source in entities:
        for target in entities:
            if source.name == target.name:
                continue
            
            # "X with Y" → X has_many Y
            if re.search(rf'{source.name}\s+with\s+{target.name}', desc_lower):
                relationships.append(ParsedRelationship(
                    source=source.singular,
                    target=target.singular,
                    relation_type="has_many"
                ))
            
            # "X for Y" → X belongs_to Y
            if re.search(rf'{source.name}\s+for\s+{target.name}', desc_lower):
                relationships.append(ParsedRelationship(
                    source=source.singular,
                    target=target.singular,
                    relation_type="belongs_to"
                ))
            
            # "X has Y" → X has_many Y
            if re.search(rf'{source.name}\s+(?:has|have|contains?)\s+{target.name}', desc_lower):
                relationships.append(ParsedRelationship(
                    source=source.singular,
                    target=target.singular,
                    relation_type="has_many"
                ))
    
    return relationships


def extract_actions(description: str) -> List[ParsedAction]:
    """Extract action verbs that indicate features."""
    actions = []
    desc_lower = description.lower()
    
    # Check for known action verbs
    for verb in ACTION_FEATURES.keys():
        if verb in desc_lower:
            actions.append(ParsedAction(verb=verb, confidence=0.9))
    
    return actions


def singularize(word: str) -> str:
    """Simple singularization (naive but effective for most cases)."""
    if word.endswith('ies'):
        return word[:-3] + 'y'
    elif word.endswith('es'):
        return word[:-2]
    elif word.endswith('s') and not word.endswith('ss'):
        return word[:-1]
    return word


# =============================================================================
# LAYER 2: UNDERSTAND (Semantic Similarity)
# =============================================================================

def get_semantic_context(description: str) -> Dict[str, float]:
    """Use GloVe embeddings to understand semantic context.
    
    Returns concept scores indicating what the description is about.
    """
    try:
        from glove_matcher import glove_match, TEMPLATE_KEYWORDS
        
        # Get top matches
        matches = glove_match(description, top_k=5)
        
        # Convert to concept scores
        context = {}
        for template_id, similarity in matches:
            # Get keywords for this template
            keywords = TEMPLATE_KEYWORDS.get(template_id, [])
            for keyword in keywords:
                if keyword not in context:
                    context[keyword] = 0.0
                context[keyword] = max(context[keyword], similarity)
        
        return context
    except ImportError:
        # Fallback if GloVe not available
        return {}


# =============================================================================
# LAYER 3: KNOWLEDGE (Domain Understanding)
# =============================================================================

@dataclass
class InferredModel:
    """A data model inferred from description."""
    name: str
    fields: List[FieldDefinition]
    relationships: List[str] = field(default_factory=list)


def infer_models_from_entities(entities: List[ParsedEntity], 
                                 relationships: List[ParsedRelationship]) -> List[InferredModel]:
    """Build data models from parsed entities using domain knowledge."""
    models = []
    
    for entity in entities:
        # Get typical fields for this entity type
        base_fields = get_entity_fields(entity.singular)
        
        # Add relationship fields
        related = []
        for rel in relationships:
            if rel.source == entity.singular:
                # This entity has a relationship
                if rel.relation_type == "has_many":
                    related.append(f"has_many {rel.target}s")
                elif rel.relation_type == "belongs_to":
                    related.append(f"belongs_to {rel.target}")
                    # Add foreign key field
                    base_fields.append(FieldDefinition(
                        name=f"{rel.target}_id",
                        field_type="int",
                        required=True,
                        description=f"Foreign key to {rel.target}"
                    ))
        
        models.append(InferredModel(
            name=entity.singular.capitalize(),
            fields=base_fields,
            relationships=related
        ))
    
    return models


def infer_features_from_context(description: str, 
                                  entities: List[ParsedEntity],
                                  actions: List[ParsedAction]) -> Set[str]:
    """Infer required features from description context."""
    features = set()
    
    # From actions
    for action in actions:
        if action.verb in ACTION_FEATURES:
            features.update(ACTION_FEATURES[action.verb])
    
    # From entities (if we have entities, we need CRUD + database)
    if entities:
        features.add("database")
        features.add("crud")
    
    # From semantic context
    desc_lower = description.lower()
    
    # Search indicators
    if any(word in desc_lower for word in ['search', 'find', 'filter', 'query']):
        features.add("search")
    
    # Auth indicators
    if any(word in desc_lower for word in ['login', 'user', 'account', 'register', 'auth']):
        features.add("auth")
    
    # Export indicators
    if any(word in desc_lower for word in ['export', 'download', 'csv', 'pdf']):
        features.add("export")
    
    # Game indicators
    if any(word in desc_lower for word in ['game', 'play', 'score', 'level']):
        features.add("game_loop")
        features.add("input_handler")
        features.add("scoring")
    
    # Timer indicators
    if any(word in desc_lower for word in ['timer', 'countdown', 'stopwatch', 'time']):
        features.add("timer")
    
    return features


# =============================================================================
# LAYER 4: COMPOSE (Full Understanding)
# =============================================================================

@dataclass
class SemanticUnderstanding:
    """Complete understanding of app description."""
    description: str
    framework: str
    models: List[InferredModel]
    features: Set[str]
    confidence: float
    reasoning: str


def infer_from_description(description: str) -> SemanticUnderstanding:
    """Complete semantic inference pipeline.
    
    This is the main entry point that orchestrates all 4 layers.
    """
    # LAYER 1: PARSE
    entities = extract_entities(description)
    relationships = extract_relationships(description, entities)
    actions = extract_actions(description)
    
    # LAYER 2: UNDERSTAND
    semantic_context = get_semantic_context(description)
    
    # LAYER 3: KNOWLEDGE
    models = infer_models_from_entities(entities, relationships)
    features = infer_features_from_context(description, entities, actions)
    
    # LAYER 4: COMPOSE
    has_data = len(models) > 0
    is_interactive = "game_loop" in features or "realtime" in features
    framework = infer_framework(description, has_data, is_interactive)
    
    # Calculate confidence
    confidence = calculate_confidence(entities, actions, semantic_context)
    
    # Build reasoning
    reasoning = build_reasoning(entities, actions, features, framework)
    
    return SemanticUnderstanding(
        description=description,
        framework=framework,
        models=models,
        features=features,
        confidence=confidence,
        reasoning=reasoning
    )


def calculate_confidence(entities: List[ParsedEntity], 
                          actions: List[ParsedAction],
                          semantic_context: Dict[str, float]) -> float:
    """Calculate confidence score for inference."""
    scores = []
    
    # Entity confidence
    if entities:
        avg_entity_confidence = sum(e.confidence for e in entities) / len(entities)
        scores.append(avg_entity_confidence)
    
    # Action confidence
    if actions:
        avg_action_confidence = sum(a.confidence for a in actions) / len(actions)
        scores.append(avg_action_confidence)
    
    # Semantic context (GloVe)
    if semantic_context:
        max_similarity = max(semantic_context.values())
        scores.append(max_similarity)
    
    # Overall confidence is average
    return sum(scores) / len(scores) if scores else 0.5


def build_reasoning(entities: List[ParsedEntity],
                     actions: List[ParsedAction],
                     features: Set[str],
                     framework: str) -> str:
    """Build human-readable reasoning for the inference."""
    lines = []
    
    if entities:
        entity_names = [e.name for e in entities]
        lines.append(f"📦 Detected entities: {', '.join(entity_names)}")
    
    if actions:
        action_names = [a.verb for a in actions]
        lines.append(f"⚡ Detected actions: {', '.join(action_names)}")
    
    if features:
        feature_list = sorted(features)
        lines.append(f"🔧 Required features: {', '.join(feature_list)}")
    
    lines.append(f"🏗️ Selected framework: {framework}")
    
    return '\n'.join(lines)


# =============================================================================
# UTILS
# =============================================================================

def explain_inference(understanding: SemanticUnderstanding) -> str:
    """Generate detailed explanation of how inference worked."""
    lines = [
        "=" * 60,
        "SEMANTIC KERNEL INFERENCE",
        "=" * 60,
        f"\nInput: {understanding.description}",
        f"\nConfidence: {understanding.confidence:.2f}",
        "\n" + understanding.reasoning,
        "\n📊 INFERRED MODELS:",
    ]
    
    if understanding.models:
        for model in understanding.models:
            lines.append(f"\n  {model.name}:")
            for field_def in model.fields[:5]:  # Show first 5 fields
                lines.append(f"    - {field_def.name}: {field_def.field_type}")
            if len(model.fields) > 5:
                lines.append(f"    ... and {len(model.fields) - 5} more fields")
            if model.relationships:
                for rel in model.relationships:
                    lines.append(f"    ~ {rel}")
    else:
        lines.append("  (no data models detected)")
    
    lines.append("\n" + "=" * 60)
    
    return '\n'.join(lines)


# =============================================================================
# PUBLIC API
# =============================================================================

def understand(description: str, verbose: bool = False) -> SemanticUnderstanding:
    """Main entry point for semantic understanding.
    
    Args:
        description: Natural language app description
        verbose: If True, print detailed reasoning
        
    Returns:
        SemanticUnderstanding with models, features, and framework
    """
    understanding = infer_from_description(description)
    
    if verbose:
        print(explain_inference(understanding))
    
    return understanding
