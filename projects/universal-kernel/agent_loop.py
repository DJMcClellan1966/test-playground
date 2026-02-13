"""
Agent Loop - Unified Agentic System

Integrates Universal Reasoning Kernel + Agent Core into a complete
autonomous agent capable of:
- Perceiving natural language goals
- Planning multi-step solutions
- Executing actions (code generation, reasoning)
- Learning from feedback

NO LLMs - Pure mathematical reasoning.

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                      AGENTIC LOOP                           │
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ PERCEIVE│───▶│  MODEL  │───▶│  PLAN   │───▶│   ACT   │  │
│  │ (NLU)   │    │ (Belief)│    │ (Search)│    │(Generate)│  │
│  └────▲────┘    └─────────┘    └─────────┘    └────┬────┘  │
│       │                                             │       │
│       │         ┌─────────┐                         │       │
│       └─────────│  LEARN  │◀────────────────────────┘       │
│                 │(Feedback)│                                 │
│                 └─────────┘                                 │
└─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations
import math
import re
import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from collections import defaultdict
from abc import ABC, abstractmethod

# Import from our kernel modules
from kernel import (
    UniversalKernel, PatternRecognizer, BayesianReasoner,
    ConstraintPropagator, MemorySystem, CompositionalGenerator,
    entropy, kl_divergence, softmax
)
from agent_core import (
    MDP, value_iteration, q_learning_update,
    attention_weights, attend,
    ucb_select, thompson_sample, epsilon_greedy,
    temporal_difference, advantage_estimation,
    PredictiveCoder, HebbianNetwork,
    a_star, MCTS,
    UniversalAgent
)

# ============================================================================
# PERCEPTION LAYER - Natural Language Understanding
# ============================================================================

@dataclass
class Percept:
    """Structured representation of a natural language input."""
    raw: str
    entities: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    relations: List[Tuple[str, str, str]] = field(default_factory=list)  # (subj, rel, obj)
    intent: str = ""
    confidence: float = 0.0
    features: Dict[str, Any] = field(default_factory=dict)


class PerceptionEngine:
    """
    Extracts structured information from natural language.
    Replicates what LLMs do with attention + embeddings, using:
    - Pattern matching (regex)
    - GloVe-style word similarity (precomputed)
    - Spreading activation (intent graph)
    """
    
    def __init__(self):
        # Entity patterns (nouns that become models/objects)
        self.entity_patterns = [
            r'\b(recipe|task|todo|item|user|product|order|event|post|comment|'
            r'note|message|file|image|document|book|movie|song|playlist|'
            r'project|goal|habit|expense|budget|contact|appointment|'
            r'workout|exercise|meal|ingredient|category|tag)\b'
        ]
        
        # Action patterns (verbs that become features)
        self.action_patterns = [
            r'\b(create|add|edit|update|delete|remove|save|load|export|import|'
            r'search|find|filter|sort|track|manage|organize|schedule|plan|'
            r'calculate|compute|analyze|generate|build|make|rate|review|'
            r'share|send|receive|upload|download|play|pause|stop)\b'
        ]
        
        # Relation patterns (prepositions that show structure)
        self.relation_patterns = [
            (r'(\w+)\s+with\s+(\w+)', 'has'),
            (r'(\w+)\s+for\s+(\w+)', 'serves'),
            (r'(\w+)\s+from\s+(\w+)', 'derived_from'),
            (r'(\w+)\s+to\s+(\w+)', 'transforms_to'),
            (r'(\w+)\s+in\s+(\w+)', 'contained_in'),
        ]
        
        # Intent patterns (what the user wants to accomplish)
        self.intent_patterns = {
            'create_app': r'build|create|make|develop|generate',
            'query': r'find|search|lookup|query|get|show',
            'modify': r'edit|update|change|modify|fix',
            'delete': r'remove|delete|clear|reset',
            'analyze': r'analyze|compute|calculate|measure',
            'explain': r'explain|describe|tell|what|how|why',
        }
        
        # Word similarity (mini GloVe - words with similar meaning)
        self.synonyms = {
            'create': {'build', 'make', 'generate', 'develop', 'construct'},
            'delete': {'remove', 'clear', 'erase', 'drop'},
            'search': {'find', 'lookup', 'query', 'filter'},
            'track': {'monitor', 'follow', 'watch', 'observe'},
            'manage': {'organize', 'handle', 'administer', 'control'},
            'app': {'application', 'program', 'tool', 'system'},
            'recipe': {'meal', 'dish', 'food'},
            'task': {'todo', 'item', 'job', 'work'},
        }
        
        # Spreading activation graph (concept → related concepts)
        self.concept_graph = defaultdict(set)
        self._build_concept_graph()
    
    def _build_concept_graph(self):
        """Build semantic network for spreading activation."""
        # Domain connections
        domains = {
            'cooking': {'recipe', 'ingredient', 'meal', 'food', 'cook'},
            'productivity': {'task', 'todo', 'project', 'goal', 'schedule'},
            'social': {'user', 'friend', 'follower', 'post', 'comment', 'share'},
            'finance': {'expense', 'budget', 'income', 'transaction', 'money'},
            'health': {'workout', 'exercise', 'meal', 'habit', 'sleep', 'water'},
            'media': {'song', 'movie', 'book', 'playlist', 'album', 'play'},
        }
        
        # Connect concepts within domains
        for domain, concepts in domains.items():
            for c1 in concepts:
                for c2 in concepts:
                    if c1 != c2:
                        self.concept_graph[c1].add(c2)
        
        # Feature implications
        implications = {
            'user': {'auth', 'login', 'database'},
            'save': {'database', 'persistence'},
            'search': {'database', 'filter'},
            'track': {'database', 'history'},
            'share': {'auth', 'social'},
            'rate': {'database', 'scoring'},
        }
        
        for trigger, implied in implications.items():
            for imp in implied:
                self.concept_graph[trigger].add(imp)
    
    def perceive(self, text: str) -> Percept:
        """Extract structured percept from natural language."""
        text_lower = text.lower()
        
        # Extract entities
        entities = []
        for pattern in self.entity_patterns:
            entities.extend(re.findall(pattern, text_lower))
        
        # Extract actions
        actions = []
        for pattern in self.action_patterns:
            actions.extend(re.findall(pattern, text_lower))
        
        # Extract relations
        relations = []
        for pattern, rel_type in self.relation_patterns:
            for match in re.finditer(pattern, text_lower):
                relations.append((match.group(1), rel_type, match.group(2)))
        
        # Determine intent
        intent = 'create_app'  # default
        intent_scores = {}
        for intent_name, pattern in self.intent_patterns.items():
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                intent_scores[intent_name] = matches
        
        if intent_scores:
            intent = max(intent_scores, key=intent_scores.get)
        
        # Calculate confidence based on extraction success
        total_extractions = len(entities) + len(actions) + len(relations)
        confidence = min(1.0, total_extractions / 5)  # 5+ extractions = full confidence
        
        # Expand via spreading activation
        features = self._spread_activation(entities + actions)
        
        return Percept(
            raw=text,
            entities=list(set(entities)),
            actions=list(set(actions)),
            relations=relations,
            intent=intent,
            confidence=confidence,
            features=features
        )
    
    def _spread_activation(self, seeds: List[str], hops: int = 2, decay: float = 0.6) -> Dict[str, float]:
        """Spread activation from seed concepts through semantic graph."""
        activations = {s: 1.0 for s in seeds}
        frontier = list(seeds)
        
        for _ in range(hops):
            new_frontier = []
            for concept in frontier:
                current_activation = activations.get(concept, 0)
                for neighbor in self.concept_graph.get(concept, []):
                    new_activation = current_activation * decay
                    if neighbor not in activations or activations[neighbor] < new_activation:
                        activations[neighbor] = new_activation
                        new_frontier.append(neighbor)
            frontier = new_frontier
        
        return activations


# ============================================================================
# WORLD MODEL - Belief State
# ============================================================================

@dataclass
class WorldState:
    """Agent's belief about the current state of the world."""
    entities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relations: List[Tuple[str, str, str]] = field(default_factory=list)
    features: Set[str] = field(default_factory=set)
    constraints: List[Tuple[str, str]] = field(default_factory=list)  # (type, description)
    goal: str = ""
    plan: List[str] = field(default_factory=list)
    confidence: float = 0.5


class WorldModel:
    """
    Maintains belief state about the world.
    Uses Bayesian updating + memory for state estimation.
    """
    
    def __init__(self):
        self.kernel = UniversalKernel()
        self.bayesian = BayesianReasoner()
        self.memory = MemorySystem()
        self.predictor = PredictiveCoder(levels=3)
        
        # Prior beliefs about feature relationships
        self.feature_priors = {
            'auth': 0.3,  # 30% of apps need auth
            'database': 0.7,  # 70% need database
            'search': 0.4,
            'export': 0.2,
            'realtime': 0.1,
        }
        
        # Feature dependencies
        self.dependencies = {
            'auth': {'database'},
            'search': {'database'},
            'export': {'database'},
        }
    
    def update(self, percept: Percept) -> WorldState:
        """Update world model based on new perception."""
        state = WorldState()
        state.goal = percept.raw
        
        # Build entity models
        for entity in percept.entities:
            state.entities[entity] = self._infer_fields(entity)
        
        # Copy relations
        state.relations = percept.relations.copy()
        
        # Infer features from actions and spreading activation
        state.features = self._infer_features(percept)
        
        # Apply constraints
        state.features, state.constraints = self._apply_constraints(state.features)
        
        # Calculate overall confidence
        state.confidence = self._calculate_confidence(percept, state)
        
        # Store in memory for learning
        self.memory.store_working(percept.raw)
        
        return state
    
    def _infer_fields(self, entity: str) -> Dict[str, Any]:
        """Infer likely fields for an entity based on domain knowledge."""
        field_templates = {
            'recipe': {'name': 'str', 'ingredients': 'list', 'instructions': 'text', 
                      'prep_time': 'int', 'rating': 'float'},
            'task': {'title': 'str', 'description': 'text', 'done': 'bool', 
                    'due_date': 'date', 'priority': 'int'},
            'user': {'username': 'str', 'email': 'str', 'password_hash': 'str'},
            'product': {'name': 'str', 'price': 'float', 'quantity': 'int', 'sku': 'str'},
            'expense': {'amount': 'float', 'category': 'str', 'date': 'date', 'notes': 'text'},
            'habit': {'name': 'str', 'frequency': 'str', 'streak': 'int', 'last_done': 'date'},
        }
        
        # Default fields for unknown entities
        default = {'id': 'int', 'name': 'str', 'created_at': 'datetime'}
        
        return field_templates.get(entity, default)
    
    def _infer_features(self, percept: Percept) -> Set[str]:
        """Infer required features from perception."""
        features = set()
        
        # Action → Feature mapping
        action_features = {
            'save': {'database'},
            'search': {'database', 'search'},
            'track': {'database'},
            'rate': {'database', 'ratings'},
            'share': {'auth', 'social'},
            'export': {'export'},
            'upload': {'file_upload'},
            'schedule': {'scheduling'},
        }
        
        for action in percept.actions:
            features.update(action_features.get(action, set()))
        
        # Add features from spreading activation
        for feature, activation in percept.features.items():
            if activation > 0.5 and feature in self.feature_priors:
                features.add(feature)
        
        # Bayesian update: if we have entities, likely need database
        if percept.entities:
            # P(database | entities) increases
            features.add('database')
        
        return features
    
    def _apply_constraints(self, features: Set[str]) -> Tuple[Set[str], List[Tuple[str, str]]]:
        """Apply dependency constraints and incompatibility checks."""
        constraints = []
        fixed_features = features.copy()
        
        # Add missing dependencies
        for feature in list(fixed_features):
            deps = self.dependencies.get(feature, set())
            for dep in deps:
                if dep not in fixed_features:
                    fixed_features.add(dep)
                    constraints.append(('dependency', f'{feature} requires {dep}'))
        
        # Check for incompatibilities
        incompatible = [
            ({'game_loop', 'database'}, 'games typically don\'t need database'),
            ({'cli', 'responsive_ui'}, 'CLI apps don\'t have browser UI'),
        ]
        
        for incompat_pair, reason in incompatible:
            if incompat_pair.issubset(fixed_features):
                constraints.append(('incompatibility', reason))
        
        return fixed_features, constraints
    
    def _calculate_confidence(self, percept: Percept, state: WorldState) -> float:
        """Calculate overall confidence in the world state."""
        factors = [
            percept.confidence,
            1.0 if state.entities else 0.5,
            1.0 if state.features else 0.5,
            1.0 - len(state.constraints) * 0.1,  # Constraints reduce confidence
        ]
        return sum(factors) / len(factors)


# ============================================================================
# PLANNING LAYER - Action Selection
# ============================================================================

@dataclass
class Action:
    """An action the agent can take."""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    preconditions: Set[str] = field(default_factory=set)
    effects: Set[str] = field(default_factory=set)
    cost: float = 1.0


@dataclass
class Plan:
    """A sequence of actions to achieve a goal."""
    actions: List[Action]
    expected_value: float
    confidence: float


class Planner:
    """
    Plans action sequences using:
    - A* search for optimal paths
    - MCTS for exploration
    - Value iteration for long-term planning
    """
    
    def __init__(self):
        self.mcts = MCTS(exploration=1.5)
        
        # Define available high-level actions
        self.action_templates = {
            'create_model': Action('create_model', effects={'has_model'}),
            'add_database': Action('add_database', effects={'has_database'}, cost=2.0),
            'add_auth': Action('add_auth', preconditions={'has_database'}, 
                             effects={'has_auth'}, cost=3.0),
            'add_crud': Action('add_crud', preconditions={'has_database'}, 
                              effects={'has_crud'}, cost=1.5),
            'add_search': Action('add_search', preconditions={'has_database'}, 
                                effects={'has_search'}, cost=1.5),
            'generate_code': Action('generate_code', preconditions={'has_model'}, 
                                   effects={'code_ready'}, cost=1.0),
            'add_ui': Action('add_ui', effects={'has_ui'}, cost=2.0),
        }
    
    def plan(self, state: WorldState) -> Plan:
        """Create a plan to achieve the goal."""
        # Determine required end state
        goal_effects = self._derive_goal_effects(state)
        
        # Use A* to find shortest path
        initial = frozenset()
        
        def goal_test(s):
            return goal_effects.issubset(s)
        
        # Track state->action mapping for plan reconstruction
        action_map = {}
        
        def successors(s):
            result = []
            for name, action in self.action_templates.items():
                if action.preconditions.issubset(s):
                    new_state = s | action.effects
                    action_map[new_state] = action
                    result.append((new_state, action.cost))
            return result
        
        def heuristic(s):
            # Estimate cost to goal
            missing = goal_effects - s
            return len(missing) * 1.5
        
        path = a_star(initial, goal_test, successors, heuristic)
        
        if path:
            # Reconstruct actions from path
            actions = []
            for i in range(1, len(path)):
                s = path[i]
                if s in action_map:
                    actions.append(action_map[s])
            
            expected_value = self._estimate_value(actions, state)
            confidence = state.confidence
            return Plan(actions, expected_value, confidence)
        
        # Fallback: minimal plan
        return Plan(
            [self.action_templates['create_model'], 
             self.action_templates['generate_code']],
            expected_value=0.5,
            confidence=0.3
        )
    
    def _derive_goal_effects(self, state: WorldState) -> Set[str]:
        """Derive required effects from world state."""
        effects = {'code_ready'}  # Always need code at the end
        
        if state.entities:
            effects.add('has_model')
        
        if 'database' in state.features:
            effects.add('has_database')
        
        if 'auth' in state.features:
            effects.add('has_auth')
        
        if 'search' in state.features:
            effects.add('has_search')
        
        return effects
    
    def _estimate_value(self, actions: List[Action], state: WorldState) -> float:
        """Estimate expected value of executing this plan."""
        # Lower cost = higher value
        total_cost = sum(a.cost for a in actions)
        # Scale by confidence
        return (10.0 / (total_cost + 1)) * state.confidence


# ============================================================================
# EXECUTION LAYER - Action Implementation
# ============================================================================

@dataclass
class ExecutionResult:
    """Result of executing an action."""
    success: bool
    output: Any
    error: Optional[str] = None
    learning_signal: float = 0.0  # Reward/punishment for learning


class Executor:
    """
    Executes planned actions using:
    - Template-based code generation
    - Compositional output construction
    """
    
    def __init__(self):
        self.generator = CompositionalGenerator()
        self.memory = MemorySystem()
        
        # Code templates for different actions
        self.templates = {
            'model': self._template_model,
            'database': self._template_database,
            'crud': self._template_crud,
            'auth': self._template_auth,
            'ui': self._template_ui,
        }
    
    def execute(self, plan: Plan, state: WorldState) -> ExecutionResult:
        """Execute a plan and return results."""
        outputs = []
        
        for action in plan.actions:
            result = self._execute_action(action, state)
            if not result.success:
                return result
            outputs.append(result.output)
        
        # Combine all outputs into final result
        combined = self._combine_outputs(outputs, state)
        
        return ExecutionResult(
            success=True,
            output=combined,
            learning_signal=plan.expected_value
        )
    
    def _execute_action(self, action: Action, state: WorldState) -> ExecutionResult:
        """Execute a single action."""
        try:
            if action.name == 'create_model':
                output = self._generate_models(state)
            elif action.name == 'add_database':
                output = self.templates['database'](state)
            elif action.name == 'add_crud':
                output = self.templates['crud'](state)
            elif action.name == 'add_auth':
                output = self.templates['auth'](state)
            elif action.name == 'add_ui':
                output = self.templates['ui'](state)
            elif action.name == 'generate_code':
                output = self._generate_final_code(state)
            else:
                output = f"# Action: {action.name}\n"
            
            return ExecutionResult(success=True, output=output)
        except Exception as e:
            return ExecutionResult(success=False, output=None, error=str(e))
    
    def _generate_models(self, state: WorldState) -> str:
        """Generate model definitions."""
        code = "# Models\n"
        for entity, fields in state.entities.items():
            code += f"\nclass {entity.title()}:\n"
            code += "    def __init__(self"
            for field_name, field_type in fields.items():
                code += f", {field_name}: {field_type} = None"
            code += "):\n"
            for field_name in fields:
                code += f"        self.{field_name} = {field_name}\n"
        return code
    
    def _template_model(self, state: WorldState) -> str:
        return self._generate_models(state)
    
    def _template_database(self, state: WorldState) -> str:
        code = '''
# Database Setup
import sqlite3
from contextlib import contextmanager

DATABASE = 'app.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
'''
        for entity, fields in state.entities.items():
            code += f"        conn.execute('''CREATE TABLE IF NOT EXISTS {entity} (\n"
            code += "            id INTEGER PRIMARY KEY AUTOINCREMENT"
            for field_name, field_type in fields.items():
                sql_type = {'str': 'TEXT', 'int': 'INTEGER', 'float': 'REAL', 
                           'bool': 'INTEGER', 'date': 'TEXT', 'datetime': 'TEXT',
                           'text': 'TEXT', 'list': 'TEXT'}.get(field_type, 'TEXT')
                if field_name != 'id':
                    code += f",\n            {field_name} {sql_type}"
            code += "\n        )''')\n"
        return code
    
    def _template_crud(self, state: WorldState) -> str:
        code = "\n# CRUD Operations\n"
        for entity, fields in state.entities.items():
            code += f'''
def create_{entity}({', '.join(fields.keys())}):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO {entity} ({', '.join(fields.keys())}) VALUES ({', '.join('?' * len(fields))})",
            ({', '.join(fields.keys())})
        )

def get_all_{entity}s():
    with get_db() as conn:
        return conn.execute("SELECT * FROM {entity}").fetchall()

def get_{entity}(id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM {entity} WHERE id = ?", (id,)).fetchone()

def delete_{entity}(id):
    with get_db() as conn:
        conn.execute("DELETE FROM {entity} WHERE id = ?", (id,))
'''
        return code
    
    def _template_auth(self, state: WorldState) -> str:
        return '''
# Authentication
import hashlib
import secrets

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + hash_obj.hex()

def verify_password(password: str, stored: str) -> bool:
    salt = stored[:32]
    stored_hash = stored[32:]
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hash_obj.hex() == stored_hash

def create_session():
    return secrets.token_urlsafe(32)
'''
    
    def _template_ui(self, state: WorldState) -> str:
        entities = list(state.entities.keys())
        entity = entities[0] if entities else 'item'
        return f'''
<!-- HTML Template -->
<!DOCTYPE html>
<html>
<head>
    <title>App</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-6">{entity.title()} Manager</h1>
        <div id="app"></div>
    </div>
</body>
</html>
'''
    
    def _generate_final_code(self, state: WorldState) -> str:
        """Generate the final assembled code."""
        return "# Final code assembled from all components\n# See component outputs above"
    
    def _combine_outputs(self, outputs: List[str], state: WorldState) -> Dict[str, str]:
        """Combine all outputs into a project structure."""
        combined = {
            'app.py': '',
            'models.py': '',
            'templates/index.html': '',
        }
        
        for output in outputs:
            if output.startswith('# Models'):
                combined['models.py'] += output
            elif output.startswith('# Database') or output.startswith('# CRUD'):
                combined['app.py'] += output
            elif output.startswith('# Authentication'):
                combined['app.py'] += output
            elif output.startswith('<!--'):
                combined['templates/index.html'] = output
            else:
                combined['app.py'] += output
        
        # Add Flask wrapper
        flask_header = '''from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

'''
        combined['app.py'] = flask_header + combined['app.py']
        
        # Add routes
        entities = list(state.entities.keys())
        if entities:
            entity = entities[0]
            combined['app.py'] += f'''
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/{entity}', methods=['GET', 'POST'])
def api_{entity}():
    if request.method == 'GET':
        return jsonify([dict(r) for r in get_all_{entity}s()])
    return jsonify({{'id': 1}})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
'''
        
        return combined


# ============================================================================
# LEARNING LAYER - Feedback Integration
# ============================================================================

class LearningSystem:
    """
    Updates agent knowledge based on feedback:
    - Hebbian learning for associations
    - TD learning for value estimates
    - Bayesian updating for beliefs
    """
    
    def __init__(self):
        self.hebbian = HebbianNetwork(size=100)  # Concept associations
        self.predictor = PredictiveCoder(levels=3)
        self.bayesian = BayesianReasoner()
        
        # Value estimates for different features/actions
        self.q_values: Dict[str, float] = defaultdict(float)
        self.counts: Dict[str, int] = defaultdict(int)
        
        # Track prediction accuracy
        self.prediction_history: List[Tuple[str, bool]] = []
    
    def learn(self, state: WorldState, result: ExecutionResult, feedback: float):
        """Update all learning systems based on outcome."""
        # 1. Update Q-values for features used
        for feature in state.features:
            old_q = self.q_values[feature]
            self.counts[feature] += 1
            alpha = 1.0 / self.counts[feature]  # Learning rate decays
            self.q_values[feature] = old_q + alpha * (feedback - old_q)
        
        # 2. Update Hebbian associations
        # Features that appear together get associated
        feature_list = list(state.features)
        if len(feature_list) >= 2:
            # Create a pattern vector (simplified)
            pattern = [1.0 if f in state.features else 0.0 
                      for f in sorted(self.q_values.keys())[:100]]
            if len(pattern) >= 5 and feedback > 0:
                self.hebbian.learn(pattern[:self.hebbian.size])
        
        # 3. Update predictive model
        # Did our predictions match reality?
        if result.success:
            self.predictor.observe(0, 1.0)  # Success
        else:
            self.predictor.observe(0, 0.0)  # Failure
        
        # 4. Store outcome for pattern learning
        self.prediction_history.append((state.goal, result.success))
    
    def suggest_features(self, partial_features: Set[str]) -> List[Tuple[str, float]]:
        """Suggest additional features based on learned associations."""
        suggestions = []
        
        for feature, q_value in self.q_values.items():
            if feature not in partial_features:
                # UCB-style exploration bonus
                count = max(1, self.counts[feature])
                total = max(1, sum(self.counts.values()))
                exploration = math.sqrt(2 * math.log(total) / count)
                score = q_value + 0.5 * exploration
                suggestions.append((feature, score))
        
        return sorted(suggestions, key=lambda x: -x[1])[:5]
    
    def get_confidence(self) -> float:
        """Get overall system confidence based on learning history."""
        if len(self.prediction_history) < 5:
            return 0.5  # Not enough data
        
        recent = self.prediction_history[-10:]
        success_rate = sum(1 for _, s in recent if s) / len(recent)
        return success_rate


# ============================================================================
# AGENT - Main Orchestrator
# ============================================================================

class LocalAgent(UniversalAgent):
    """
    Complete autonomous agent combining all components.
    
    The loop:
    1. PERCEIVE: Parse natural language → structured percept
    2. MODEL: Update world state with Bayesian inference
    3. PLAN: Find optimal action sequence via search
    4. ACT: Execute actions, generate output
    5. LEARN: Update from feedback
    """
    
    def __init__(self):
        self.perception = PerceptionEngine()
        self.world_model = WorldModel()
        self.planner = Planner()
        self.executor = Executor()
        self.learner = LearningSystem()
        
        self.current_state: Optional[WorldState] = None
        self.last_result: Optional[ExecutionResult] = None
    
    def perceive(self, observation: Any) -> None:
        """Process incoming observation (natural language goal)."""
        if isinstance(observation, str):
            percept = self.perception.perceive(observation)
            self.current_state = self.world_model.update(percept)
    
    def decide(self, options: List[Any] = None) -> Any:
        """Decide on an action (create a plan)."""
        if self.current_state is None:
            return None
        return self.planner.plan(self.current_state)
    
    def act(self, action: Any) -> Any:
        """Execute the plan."""
        if isinstance(action, Plan) and self.current_state:
            self.last_result = self.executor.execute(action, self.current_state)
            return self.last_result.output
        return None
    
    def learn(self, feedback: float) -> None:
        """Learn from feedback."""
        if self.current_state and self.last_result:
            self.learner.learn(self.current_state, self.last_result, feedback)
    
    def predict(self, query: Any) -> Any:
        """Predict outcome or suggest next steps."""
        if isinstance(query, str) and query == 'features':
            features = self.current_state.features if self.current_state else set()
            return self.learner.suggest_features(features)
        return None
    
    # High-level API
    def process(self, goal: str) -> Dict[str, str]:
        """
        Main entry point: process a natural language goal.
        
        Returns dict of generated files.
        """
        # 1. Perceive
        self.perceive(goal)
        
        # 2. Decide
        plan = self.decide()
        
        # 3. Act
        output = self.act(plan)
        
        return output if isinstance(output, dict) else {'output.txt': str(output)}
    
    def feedback(self, is_good: bool):
        """Provide feedback on the last result."""
        self.learn(1.0 if is_good else -1.0)
    
    def explain(self) -> str:
        """Explain current state and reasoning."""
        if not self.current_state:
            return "No goal processed yet."
        
        lines = [
            f"Goal: {self.current_state.goal}",
            f"Entities: {list(self.current_state.entities.keys())}",
            f"Features: {self.current_state.features}",
            f"Constraints: {self.current_state.constraints}",
            f"Confidence: {self.current_state.confidence:.2f}",
            f"Learning confidence: {self.learner.get_confidence():.2f}",
        ]
        
        suggestions = self.learner.suggest_features(self.current_state.features)
        if suggestions:
            lines.append(f"Suggested features: {[f for f, _ in suggestions[:3]]}")
        
        return "\n".join(lines)


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Demonstrate the complete agentic system."""
    print("=" * 60)
    print("LOCAL AGENT DEMO - No LLMs, Pure Mathematical Reasoning")
    print("=" * 60)
    
    agent = LocalAgent()
    
    # Test goals
    goals = [
        "a recipe collection app where I can save recipes with ingredients and rate them",
        "todo list with categories",
        "expense tracker for personal budgeting",
    ]
    
    for goal in goals:
        print(f"\n{'='*60}")
        print(f"GOAL: {goal}")
        print("=" * 60)
        
        # Process the goal
        output = agent.process(goal)
        
        # Show explanation
        print("\n--- Agent Reasoning ---")
        print(agent.explain())
        
        # Show output
        print("\n--- Generated Files ---")
        for filename, content in output.items():
            lines = content.split('\n')[:10]
            print(f"\n{filename}:")
            print('\n'.join(lines))
            if len(content.split('\n')) > 10:
                print("  ... (truncated)")
        
        # Simulate positive feedback
        agent.feedback(is_good=True)
        print("\n[Feedback: Good] - Agent learns from success")
    
    # Show learning progress
    print("\n" + "=" * 60)
    print("LEARNING SUMMARY")
    print("=" * 60)
    print(f"System confidence: {agent.learner.get_confidence():.2f}")
    print(f"Feature Q-values: {dict(agent.learner.q_values)}")
    print(f"Feature counts: {dict(agent.learner.counts)}")


if __name__ == '__main__':
    demo()
