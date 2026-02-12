"""
Intent Classifier - Local algorithm inspired by LLM intent classification.

Categorizes user requests into action types without AI:
- BUILD: Create something new from scratch
- EXTEND: Add features to existing concept  
- FIX: Solve a problem or debug
- EXPLORE: Research or brainstorm ideas
- CONVERT: Transform between formats
- AUTOMATE: Create workflow/process

Uses verb patterns, phrase structures, and context signals.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Set
from enum import Enum
import re


class Intent(Enum):
    BUILD = "build"       # Create new app/system
    EXTEND = "extend"     # Add to existing
    FIX = "fix"           # Debug/repair
    EXPLORE = "explore"   # Research/brainstorm
    CONVERT = "convert"   # Transform formats
    AUTOMATE = "automate" # Workflow/process
    QUERY = "query"       # Look up information
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """Result of intent classification."""
    primary: Intent
    confidence: float  # 0.0 - 1.0
    secondary: Optional[Intent]  # Possible secondary intent
    action_verbs: List[str]  # Detected action words
    object_nouns: List[str]  # What they want to act on
    modifiers: List[str]  # Adjectives/conditions


# Verb patterns for each intent
INTENT_VERBS = {
    Intent.BUILD: {
        'strong': ['build', 'create', 'make', 'develop', 'generate', 'design', 'construct'],
        'medium': ['start', 'begin', 'launch', 'set up', 'setup', 'establish', 'implement'],
        'weak': ['want', 'need', 'give me', 'i want', 'i need']
    },
    Intent.EXTEND: {
        'strong': ['add', 'extend', 'expand', 'enhance', 'include', 'integrate', 'incorporate'],
        'medium': ['improve', 'upgrade', 'update', 'augment', 'supplement'],
        'weak': ['also', 'plus', 'with', 'and also', 'additionally']
    },
    Intent.FIX: {
        'strong': ['fix', 'repair', 'debug', 'solve', 'resolve', 'correct', 'patch'],
        'medium': ['troubleshoot', 'diagnose', 'investigate', 'handle', 'address'],
        'weak': ['broken', 'error', 'bug', 'wrong', 'issue', 'problem', 'not working']
    },
    Intent.EXPLORE: {
        'strong': ['explore', 'research', 'brainstorm', 'investigate', 'discover', 'learn'],
        'medium': ['consider', 'think about', 'what if', 'how would', 'could we'],
        'weak': ['maybe', 'perhaps', 'possibly', 'idea', 'concept', 'prototype']
    },
    Intent.CONVERT: {
        'strong': ['convert', 'transform', 'translate', 'migrate', 'export', 'import'],
        'medium': ['change to', 'turn into', 'switch to', 'move to', 'port'],
        'weak': ['from...to', 'into', 'as a', 'format']
    },
    Intent.AUTOMATE: {
        'strong': ['automate', 'schedule', 'trigger', 'orchestrate', 'pipeline'],
        'medium': ['whenever', 'every time', 'on change', 'automatically', 'auto'],
        'weak': ['workflow', 'process', 'routine', 'batch', 'cron']
    },
    Intent.QUERY: {
        'strong': ['find', 'search', 'look up', 'query', 'fetch', 'retrieve', 'get'],
        'medium': ['show', 'list', 'display', 'what is', 'where is', 'how many'],
        'weak': ['about', 'info', 'details', 'check']
    }
}

# Structural patterns that indicate intent
STRUCTURAL_PATTERNS = {
    Intent.BUILD: [
        r'^(a|an)\s+\w+\s+(app|application|system|tool|platform|service)',
        r'(app|system|tool)\s+(for|to|that)',
        r'^create\s+',
        r'^build\s+',
        r'^make\s+',
        r'^i\s+(want|need)\s+(a|an|to)',
    ],
    Intent.EXTEND: [
        r'add\s+\w+\s+to',
        r'with\s+(additional|extra|more)',
        r'also\s+(have|include|support)',
        r'extend\s+.*\s+(with|to)',
    ],
    Intent.FIX: [
        r"(doesn't|does not|won't|isn't|can't)\s+\w+",
        r'(error|bug|issue|problem)\s+(with|in|when)',
        r'not\s+(working|functioning|running)',
        r'(fix|repair|debug)\s+(the|my|this)',
    ],
    Intent.EXPLORE: [
        r'^(what|how|why|could|would|should)',
        r'\?$',
        r'(ideas?|concept|prototype|experiment)',
        r'(explore|research|investigate)',
    ],
    Intent.CONVERT: [
        r'from\s+\w+\s+to\s+\w+',
        r'convert\s+\w+\s+to',
        r'(export|import)\s+(to|from|as)',
        r'(change|transform)\s+.*\s+(to|into)',
    ],
    Intent.AUTOMATE: [
        r'(every|each)\s+(day|week|hour|minute|time)',
        r'(when|whenever|if)\s+.*\s+(then|do|trigger)',
        r'(schedule|cron|timer|interval)',
        r'automatic(ally)?\s+',
    ],
}

# Object extraction patterns (what are they building/fixing/etc)
OBJECT_PATTERNS = [
    r'(a|an|the|my)\s+(\w+(?:\s+\w+){0,2})\s+(app|application|system|tool|api|service|site|website)',
    r'(\w+(?:\s+\w+){0,2})\s+(manager|tracker|logger|organizer|planner|builder|generator)',
    r'(app|application|system|tool)\s+for\s+(\w+(?:\s+\w+){0,3})',
    r'to\s+(track|manage|organize|log|plan|generate|create)\s+(\w+(?:\s+\w+){0,2})',
]


def classify_intent(description: str) -> IntentResult:
    """
    Classify user intent from natural language description.
    
    Uses a scoring system based on:
    - Verb patterns (strong/medium/weak matches)
    - Structural patterns (sentence structure)
    - Context signals (question marks, etc.)
    """
    text = description.lower().strip()
    
    # Score each intent
    scores = {intent: 0.0 for intent in Intent}
    detected_verbs = []
    
    # 1. Score verb patterns
    for intent, patterns in INTENT_VERBS.items():
        for verb in patterns['strong']:
            if re.search(rf'\b{re.escape(verb)}\b', text):
                scores[intent] += 3.0
                detected_verbs.append(verb)
        for verb in patterns['medium']:
            if re.search(rf'\b{re.escape(verb)}\b', text):
                scores[intent] += 1.5
                detected_verbs.append(verb)
        for verb in patterns['weak']:
            if re.search(rf'\b{re.escape(verb)}\b', text):
                scores[intent] += 0.5
    
    # 2. Score structural patterns
    for intent, patterns in STRUCTURAL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                scores[intent] += 2.0
    
    # 3. Default to BUILD for app descriptions without explicit action
    if max(scores.values()) < 1.0:
        # Check if it looks like an app description
        if re.search(r'(app|application|system|tool|tracker|manager|organizer)', text):
            scores[Intent.BUILD] += 2.0
    
    # 4. Find primary and secondary intents
    sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary_intent = sorted_intents[0][0]
    primary_score = sorted_intents[0][1]
    
    secondary_intent = None
    if len(sorted_intents) > 1 and sorted_intents[1][1] > 0.5:
        secondary_intent = sorted_intents[1][0]
    
    # 5. Calculate confidence (normalized)
    total_score = sum(scores.values())
    if total_score > 0:
        confidence = min(1.0, primary_score / max(5.0, total_score))
    else:
        confidence = 0.3  # Low confidence default
        primary_intent = Intent.BUILD  # Default assumption
    
    # 6. Extract objects and modifiers
    objects = extract_objects(text)
    modifiers = extract_modifiers(text)
    
    return IntentResult(
        primary=primary_intent,
        confidence=confidence,
        secondary=secondary_intent,
        action_verbs=list(set(detected_verbs)),
        object_nouns=objects,
        modifiers=modifiers
    )


def extract_objects(text: str) -> List[str]:
    """Extract the main objects/nouns from the description."""
    objects = []
    
    for pattern in OBJECT_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Get the noun part (usually the 2nd group)
                for part in match:
                    if part and len(part) > 2 and part not in ['app', 'application', 'system', 'tool', 'a', 'an', 'the', 'my']:
                        objects.append(part.strip())
            else:
                objects.append(match.strip())
    
    # Fallback: extract nouns after key words
    fallback_patterns = [
        r'(?:for|to|with)\s+(\w+(?:\s+\w+){0,2})',
        r'^(?:a|an)\s+(\w+)',
    ]
    
    if not objects:
        for pattern in fallback_patterns:
            matches = re.findall(pattern, text)
            objects.extend(matches[:3])
    
    return list(set(objects))[:5]


def extract_modifiers(text: str) -> List[str]:
    """Extract adjectives and modifiers that describe requirements."""
    modifiers = []
    
    # Quality modifiers
    quality_words = ['simple', 'complex', 'basic', 'advanced', 'fast', 'secure', 
                     'scalable', 'responsive', 'minimal', 'full', 'complete',
                     'lightweight', 'powerful', 'easy', 'robust', 'flexible']
    
    for word in quality_words:
        if re.search(rf'\b{word}\b', text, re.IGNORECASE):
            modifiers.append(word)
    
    # Scope modifiers
    scope_words = ['personal', 'team', 'enterprise', 'small', 'large', 'local',
                   'cloud', 'offline', 'mobile', 'desktop', 'web']
    
    for word in scope_words:
        if re.search(rf'\b{word}\b', text, re.IGNORECASE):
            modifiers.append(word)
    
    return modifiers


def explain_intent(result: IntentResult) -> str:
    """Generate human-readable explanation of the classification."""
    lines = [
        f"Intent: {result.primary.value.upper()} (confidence: {result.confidence:.0%})"
    ]
    
    if result.secondary:
        lines.append(f"Secondary intent: {result.secondary.value}")
    
    if result.action_verbs:
        lines.append(f"Action words: {', '.join(result.action_verbs)}")
    
    if result.object_nouns:
        lines.append(f"Main objects: {', '.join(result.object_nouns)}")
    
    if result.modifiers:
        lines.append(f"Modifiers: {', '.join(result.modifiers)}")
    
    return '\n'.join(lines)


# Quick test
if __name__ == '__main__':
    test_cases = [
        "build a recipe tracking app",
        "create a todo list with reminders",
        "fix the login error on the dashboard",
        "add search functionality to the inventory system",
        "convert my CSV data to JSON format",
        "automate daily backup of the database",
        "what are some good patterns for authentication?",
        "a simple blog with comments",
        "i want an app to track my workouts",
        "schedule reports to run every Monday",
    ]
    
    print("=" * 60)
    print("INTENT CLASSIFIER - Local Algorithm Demo")
    print("=" * 60)
    
    for desc in test_cases:
        result = classify_intent(desc)
        print(f"\n📝 \"{desc}\"")
        print(f"   → {result.primary.value.upper()} ({result.confidence:.0%})")
        if result.secondary:
            print(f"   → Also: {result.secondary.value}")
        if result.object_nouns:
            print(f"   → Objects: {result.object_nouns}")
