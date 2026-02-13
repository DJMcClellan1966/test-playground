"""
Universal Reasoning Kernel (URK)
================================
A mathematically-grounded AI system without LLMs.

Based on:
- Solomonoff Induction: Intelligence as optimal compression
- Free Energy Principle: Minimize prediction error
- Information Theory: Shannon entropy for uncertainty
- Bayesian Inference: Belief updating with evidence
- Constraint Satisfaction: Logical consistency

Author: App Forge Project
License: MIT
"""

from __future__ import annotations
import re
import math
import json
import zlib
import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict
from functools import lru_cache
import random


# =============================================================================
# CORE MATHEMATICAL FUNCTIONS
# =============================================================================

def entropy(probs: List[float]) -> float:
    """Shannon entropy: H(X) = -Σ p(x) log₂ p(x)"""
    return -sum(p * math.log2(p) for p in probs if p > 0)


def information_gain(prior: List[float], posteriors: List[List[float]], 
                     weights: List[float]) -> float:
    """IG = H(prior) - Σ w_i * H(posterior_i)"""
    return entropy(prior) - sum(w * entropy(p) for w, p in zip(weights, posteriors))


def kl_divergence(p: List[float], q: List[float]) -> float:
    """KL(P||Q) = Σ p(x) * log(p(x)/q(x)) - measures belief distance"""
    eps = 1e-10
    return sum(px * math.log((px + eps) / (qx + eps)) for px, qx in zip(p, q) if px > 0)


def compression_distance(a: str, b: str) -> float:
    """
    Normalized Compression Distance (NCD) - approximates Kolmogorov complexity.
    NCD(a,b) = (C(ab) - min(C(a),C(b))) / max(C(a),C(b))
    Lower = more similar
    """
    def C(s: str) -> int:
        return len(zlib.compress(s.encode()))
    
    ca, cb = C(a), C(b)
    cab = C(a + b)
    return (cab - min(ca, cb)) / max(ca, cb, 1)


def bayesian_update(prior: float, likelihood: float, evidence: float) -> float:
    """P(H|E) = P(E|H) * P(H) / P(E)"""
    if evidence == 0:
        return prior
    return (likelihood * prior) / evidence


def softmax(values: List[float], temperature: float = 1.0) -> List[float]:
    """Convert scores to probabilities with temperature control"""
    if not values:
        return []
    max_v = max(values)
    exp_v = [math.exp((v - max_v) / temperature) for v in values]
    total = sum(exp_v)
    return [e / total for e in exp_v]


# =============================================================================
# PATTERN RECOGNIZER
# =============================================================================

@dataclass
class Pattern:
    """A learnable pattern with regex and semantic components"""
    id: str
    regex: str
    semantic_tags: Set[str]
    examples: List[str] = field(default_factory=list)
    weight: float = 1.0
    
    def matches(self, text: str) -> Optional[re.Match]:
        try:
            return re.search(self.regex, text, re.IGNORECASE)
        except re.error:
            return None
    
    def similarity(self, text: str) -> float:
        """Combined regex + compression similarity"""
        # Regex match score
        match = self.matches(text)
        regex_score = 0.5 if match else 0.0
        
        # Compression-based similarity to examples
        if self.examples:
            comp_scores = [1.0 - compression_distance(text, ex) for ex in self.examples]
            comp_score = max(comp_scores) * 0.5
        else:
            comp_score = 0.0
        
        return (regex_score + comp_score) * self.weight


class PatternRecognizer:
    """
    Recognizes patterns using:
    1. Regex matching
    2. Compression-based similarity
    3. Analogical mapping
    """
    
    def __init__(self):
        self.patterns: Dict[str, Pattern] = {}
        self.analogy_cache: Dict[str, List[Tuple[str, float]]] = {}
    
    def add_pattern(self, pattern: Pattern):
        self.patterns[pattern.id] = pattern
    
    def learn_pattern(self, id: str, examples: List[str], tags: Set[str] = None):
        """Learn a pattern from examples (extract common structure)"""
        if not examples:
            return
        
        # Find common substrings
        common = self._find_common_structure(examples)
        
        # Generate flexible regex
        regex = self._examples_to_regex(examples, common)
        
        self.patterns[id] = Pattern(
            id=id,
            regex=regex,
            semantic_tags=tags or set(),
            examples=examples
        )
    
    def _find_common_structure(self, examples: List[str]) -> List[str]:
        """Extract common substrings from examples"""
        if len(examples) < 2:
            return []
        
        # Find longest common substrings
        common = []
        first = examples[0].lower()
        
        for length in range(3, min(20, len(first))):
            for i in range(len(first) - length + 1):
                substring = first[i:i+length]
                if all(substring in ex.lower() for ex in examples[1:]):
                    if not any(substring in c for c in common):
                        common.append(substring)
        
        return sorted(common, key=len, reverse=True)[:5]
    
    def _examples_to_regex(self, examples: List[str], common: List[str]) -> str:
        """Generate regex from examples"""
        if common:
            # Use common substrings as anchors
            parts = [re.escape(c) for c in common[:3]]
            return r'.*?'.join(parts)
        else:
            # Fallback: word-based OR pattern
            words = set()
            for ex in examples:
                words.update(w.lower() for w in re.findall(r'\b\w{3,}\b', ex))
            if words:
                return r'\b(' + '|'.join(re.escape(w) for w in list(words)[:10]) + r')\b'
            return r'.*'
    
    def recognize(self, text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Recognize patterns in text, return (pattern_id, score) pairs"""
        scores = []
        for pid, pattern in self.patterns.items():
            score = pattern.similarity(text)
            if score > 0:
                scores.append((pid, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def analogical_match(self, a: str, b: str, c: str) -> List[Tuple[str, float]]:
        """
        Analogical reasoning: A:B :: C:?
        Find D such that the relationship A→B is similar to C→D
        """
        # Extract transformation from A to B
        transform = self._extract_transform(a, b)
        
        # Apply to C
        candidates = self._apply_transform(c, transform)
        
        # Score by compression distance to expected pattern
        scored = []
        for d in candidates:
            # The relationship c→d should be similar to a→b
            ab_dist = compression_distance(a + b, c + d)
            scored.append((d, 1.0 - ab_dist))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:5]
    
    def _extract_transform(self, a: str, b: str) -> Dict[str, Any]:
        """Extract transformation rules from A to B"""
        transform = {
            'prefix_add': '',
            'suffix_add': '',
            'replacements': [],
            'case_change': None
        }
        
        a_lower, b_lower = a.lower(), b.lower()
        
        # Check for prefix/suffix operations
        if b_lower.startswith(a_lower):
            transform['suffix_add'] = b[len(a):]
        elif b_lower.endswith(a_lower):
            transform['prefix_add'] = b[:-len(a)]
        
        # Check case transformations
        if a.islower() and b.isupper():
            transform['case_change'] = 'upper'
        elif a.isupper() and b.islower():
            transform['case_change'] = 'lower'
        elif a.islower() and b.istitle():
            transform['case_change'] = 'title'
        
        # Character-level replacements
        if len(a) == len(b):
            for i, (ca, cb) in enumerate(zip(a, b)):
                if ca != cb:
                    transform['replacements'].append((ca, cb))
        
        return transform
    
    def _apply_transform(self, c: str, transform: Dict[str, Any]) -> List[str]:
        """Apply transformation to C to generate candidates"""
        candidates = [c]
        
        # Apply prefix/suffix
        if transform['prefix_add']:
            candidates.append(transform['prefix_add'] + c)
        if transform['suffix_add']:
            candidates.append(c + transform['suffix_add'])
        
        # Apply case change
        if transform['case_change'] == 'upper':
            candidates.append(c.upper())
        elif transform['case_change'] == 'lower':
            candidates.append(c.lower())
        elif transform['case_change'] == 'title':
            candidates.append(c.title())
        
        # Apply replacements
        for old, new in transform['replacements']:
            candidates.append(c.replace(old, new))
        
        return list(set(candidates))


# =============================================================================
# BAYESIAN REASONER
# =============================================================================

@dataclass
class Belief:
    """A belief with probability and supporting evidence"""
    proposition: str
    probability: float
    evidence: List[str] = field(default_factory=list)
    contrary_evidence: List[str] = field(default_factory=list)
    
    def confidence(self) -> float:
        """How confident are we? Based on evidence amount"""
        total_evidence = len(self.evidence) + len(self.contrary_evidence)
        if total_evidence == 0:
            return 0.0  # No evidence = no confidence
        return min(1.0, total_evidence / 10)  # Cap at 10 pieces of evidence


class BayesianReasoner:
    """
    Bayesian belief network with:
    1. Prior beliefs
    2. Evidence updating
    3. Information-theoretic question selection
    """
    
    def __init__(self):
        self.beliefs: Dict[str, Belief] = {}
        self.conditionals: Dict[Tuple[str, str], float] = {}  # P(A|B)
        self.observation_history: List[Tuple[str, Any]] = []
    
    def add_belief(self, proposition: str, prior: float = 0.5):
        """Add a belief with initial prior probability"""
        self.beliefs[proposition] = Belief(
            proposition=proposition,
            probability=prior
        )
    
    def add_conditional(self, a: str, given_b: str, probability: float):
        """Set P(A|B) - probability of A given B"""
        self.conditionals[(a, given_b)] = probability
    
    def observe(self, evidence: str, supports: List[str] = None, opposes: List[str] = None):
        """Record evidence and update beliefs"""
        supports = supports or []
        opposes = opposes or []
        
        self.observation_history.append((evidence, {'supports': supports, 'opposes': opposes}))
        
        for prop in supports:
            if prop in self.beliefs:
                belief = self.beliefs[prop]
                belief.evidence.append(evidence)
                # Bayesian update: increase probability
                belief.probability = self._update_probability(belief.probability, 0.8, positive=True)
        
        for prop in opposes:
            if prop in self.beliefs:
                belief = self.beliefs[prop]
                belief.contrary_evidence.append(evidence)
                # Bayesian update: decrease probability
                belief.probability = self._update_probability(belief.probability, 0.8, positive=False)
    
    def _update_probability(self, prior: float, strength: float, positive: bool) -> float:
        """Update probability based on evidence"""
        if positive:
            # Move toward 1
            return prior + (1 - prior) * strength * 0.2
        else:
            # Move toward 0
            return prior * (1 - strength * 0.2)
    
    def most_uncertain(self) -> Optional[str]:
        """Find the belief with highest entropy (most uncertain)"""
        if not self.beliefs:
            return None
        
        # Entropy is maximized at p=0.5
        def uncertainty(b: Belief) -> float:
            p = b.probability
            if p <= 0 or p >= 1:
                return 0
            return -p * math.log2(p) - (1-p) * math.log2(1-p)
        
        return max(self.beliefs.keys(), key=lambda k: uncertainty(self.beliefs[k]))
    
    def best_question(self, candidates: List[str]) -> Optional[str]:
        """
        Select the question with maximum expected information gain.
        Used for optimal questioning strategy.
        """
        if not candidates or not self.beliefs:
            return None
        
        best = None
        best_gain = -1
        
        for question in candidates:
            # Estimate which beliefs this question could affect
            related_beliefs = self._related_beliefs(question)
            if not related_beliefs:
                continue
            
            # Calculate expected information gain
            gain = self._expected_gain(question, related_beliefs)
            if gain > best_gain:
                best_gain = gain
                best = question
        
        return best
    
    def _related_beliefs(self, question: str) -> List[str]:
        """Find beliefs related to a question (by word overlap)"""
        q_words = set(question.lower().split())
        related = []
        for prop in self.beliefs:
            p_words = set(prop.lower().split())
            if q_words & p_words:  # Any overlap
                related.append(prop)
        return related
    
    def _expected_gain(self, question: str, related: List[str]) -> float:
        """Estimate information gain from asking a question"""
        if not related:
            return 0
        
        # Current entropy of related beliefs
        priors = [self.beliefs[r].probability for r in related]
        current_entropy = sum(entropy([p, 1-p]) for p in priors) / len(priors)
        
        # Expected posterior entropy (assume answer reduces uncertainty by half)
        expected_posterior = current_entropy * 0.5
        
        return current_entropy - expected_posterior
    
    def query(self, proposition: str) -> Tuple[float, float]:
        """Query belief probability and confidence"""
        if proposition in self.beliefs:
            b = self.beliefs[proposition]
            return b.probability, b.confidence()
        
        # Try to infer from conditionals
        inferred = self._infer(proposition)
        if inferred is not None:
            return inferred, 0.3  # Lower confidence for inferred beliefs
        
        return 0.5, 0.0  # Unknown
    
    def _infer(self, proposition: str) -> Optional[float]:
        """Infer probability from conditional relationships"""
        # Look for P(proposition|something)
        for (a, b), prob in self.conditionals.items():
            if a == proposition and b in self.beliefs:
                # P(A) ≈ P(A|B) * P(B) + P(A|¬B) * P(¬B)
                pb = self.beliefs[b].probability
                return prob * pb + (1 - prob) * (1 - pb) * 0.5
        
        return None
    
    def explain(self, proposition: str) -> str:
        """Explain the reasoning behind a belief"""
        if proposition not in self.beliefs:
            return f"No information about: {proposition}"
        
        b = self.beliefs[proposition]
        lines = [f"Belief: {proposition}"]
        lines.append(f"Probability: {b.probability:.2%}")
        lines.append(f"Confidence: {b.confidence():.2%}")
        
        if b.evidence:
            lines.append(f"Supporting evidence ({len(b.evidence)}):")
            for e in b.evidence[-3:]:  # Last 3
                lines.append(f"  + {e}")
        
        if b.contrary_evidence:
            lines.append(f"Contrary evidence ({len(b.contrary_evidence)}):")
            for e in b.contrary_evidence[-3:]:
                lines.append(f"  - {e}")
        
        return "\n".join(lines)


# =============================================================================
# CONSTRAINT PROPAGATOR
# =============================================================================

@dataclass
class Variable:
    """A variable with a domain of possible values"""
    name: str
    domain: Set[Any]
    value: Optional[Any] = None
    
    def is_assigned(self) -> bool:
        return self.value is not None
    
    def domain_size(self) -> int:
        return len(self.domain)


@dataclass  
class Constraint:
    """A constraint between variables"""
    variables: List[str]
    predicate: Callable[..., bool]
    description: str = ""


class ConstraintPropagator:
    """
    Constraint Satisfaction Problem (CSP) solver using:
    1. Arc Consistency (AC-3)
    2. Most Constrained Variable heuristic
    3. Least Constraining Value heuristic
    """
    
    def __init__(self):
        self.variables: Dict[str, Variable] = {}
        self.constraints: List[Constraint] = []
        self.solution_history: List[Dict[str, Any]] = []
    
    def add_variable(self, name: str, domain: List[Any]):
        """Add a variable with its domain"""
        self.variables[name] = Variable(name=name, domain=set(domain))
    
    def add_constraint(self, var_names: List[str], predicate: Callable[..., bool], 
                       description: str = ""):
        """Add a constraint between variables"""
        self.constraints.append(Constraint(
            variables=var_names,
            predicate=predicate,
            description=description
        ))
    
    def propagate(self) -> bool:
        """
        AC-3 algorithm: Reduce domains based on constraints.
        Returns False if any domain becomes empty (no solution).
        """
        # Build arcs: (var1, var2, constraint)
        queue = []
        for c in self.constraints:
            if len(c.variables) == 2:
                queue.append((c.variables[0], c.variables[1], c))
                queue.append((c.variables[1], c.variables[0], c))
        
        while queue:
            xi, xj, constraint = queue.pop(0)
            if self._revise(xi, xj, constraint):
                if self.variables[xi].domain_size() == 0:
                    return False  # Domain wiped out
                
                # Add neighbors back to queue
                for c in self.constraints:
                    if xi in c.variables:
                        for xk in c.variables:
                            if xk != xi and xk != xj:
                                queue.append((xk, xi, c))
        
        return True
    
    def _revise(self, xi: str, xj: str, constraint: Constraint) -> bool:
        """Remove values from xi's domain that have no support in xj"""
        revised = False
        to_remove = set()
        
        vi = self.variables[xi]
        vj = self.variables[xj]
        
        for val_i in vi.domain:
            # Check if any value in xj's domain satisfies constraint with val_i
            has_support = False
            for val_j in vj.domain:
                args = {xi: val_i, xj: val_j}
                ordered_args = [args[v] for v in constraint.variables]
                try:
                    if constraint.predicate(*ordered_args):
                        has_support = True
                        break
                except:
                    pass
            
            if not has_support:
                to_remove.add(val_i)
                revised = True
        
        vi.domain -= to_remove
        return revised
    
    def solve(self) -> Optional[Dict[str, Any]]:
        """
        Solve the CSP using backtracking with heuristics.
        Returns assignment dict or None if unsolvable.
        """
        # First, propagate constraints
        if not self.propagate():
            return None
        
        # Check if already solved
        if all(v.is_assigned() or v.domain_size() == 1 for v in self.variables.values()):
            return self._get_assignment()
        
        # Backtracking search
        return self._backtrack({})
    
    def _backtrack(self, assignment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Recursive backtracking with MCV and LCV heuristics"""
        # Check if complete
        if len(assignment) == len(self.variables):
            return assignment.copy()
        
        # Select unassigned variable (Most Constrained Variable)
        var = self._select_unassigned_variable(assignment)
        if var is None:
            return None
        
        # Try values in order (Least Constraining Value)
        for value in self._order_domain_values(var, assignment):
            if self._is_consistent(var.name, value, assignment):
                assignment[var.name] = value
                
                result = self._backtrack(assignment)
                if result is not None:
                    self.solution_history.append(result)
                    return result
                
                del assignment[var.name]
        
        return None
    
    def _select_unassigned_variable(self, assignment: Dict[str, Any]) -> Optional[Variable]:
        """MCV: Select variable with smallest remaining domain"""
        unassigned = [v for v in self.variables.values() 
                      if v.name not in assignment]
        if not unassigned:
            return None
        return min(unassigned, key=lambda v: v.domain_size())
    
    def _order_domain_values(self, var: Variable, assignment: Dict[str, Any]) -> List[Any]:
        """LCV: Order values by how few constraints they rule out"""
        def constraining_count(value):
            count = 0
            for c in self.constraints:
                if var.name in c.variables:
                    for other_name in c.variables:
                        if other_name != var.name and other_name not in assignment:
                            other = self.variables[other_name]
                            for other_val in other.domain:
                                args = {var.name: value, other_name: other_val}
                                ordered = [args[v] for v in c.variables]
                                try:
                                    if not c.predicate(*ordered):
                                        count += 1
                                except:
                                    pass
            return count
        
        return sorted(var.domain, key=constraining_count)
    
    def _is_consistent(self, var_name: str, value: Any, assignment: Dict[str, Any]) -> bool:
        """Check if assigning value to variable is consistent with constraints"""
        test_assignment = assignment.copy()
        test_assignment[var_name] = value
        
        for c in self.constraints:
            # Only check if all variables are assigned
            if all(v in test_assignment for v in c.variables):
                args = [test_assignment[v] for v in c.variables]
                try:
                    if not c.predicate(*args):
                        return False
                except:
                    return False
        
        return True
    
    def _get_assignment(self) -> Dict[str, Any]:
        """Get current assignment (for solved CSPs)"""
        result = {}
        for name, var in self.variables.items():
            if var.value is not None:
                result[name] = var.value
            elif var.domain_size() == 1:
                result[name] = next(iter(var.domain))
        return result


# =============================================================================
# MEMORY SYSTEM
# =============================================================================

@dataclass
class Memory:
    """A single memory with content and metadata"""
    id: str
    content: Any
    memory_type: str  # 'working', 'episodic', 'semantic'
    timestamp: float
    access_count: int = 0
    associations: Set[str] = field(default_factory=set)
    embedding: Optional[List[float]] = None


class MemorySystem:
    """
    Three-tier memory system:
    1. Working Memory - Current context (limited capacity)
    2. Episodic Memory - Past interactions (time-ordered)
    3. Semantic Memory - Learned facts (associative)
    """
    
    WORKING_CAPACITY = 7  # Miller's magic number
    
    def __init__(self):
        self.working: List[Memory] = []
        self.episodic: List[Memory] = []
        self.semantic: Dict[str, Memory] = {}
        self._access_counter = 0
    
    def _generate_id(self) -> str:
        self._access_counter += 1
        return hashlib.md5(str(self._access_counter).encode()).hexdigest()[:8]
    
    def store_working(self, content: Any) -> str:
        """Store in working memory (limited capacity, FIFO)"""
        import time
        
        mem_id = self._generate_id()
        memory = Memory(
            id=mem_id,
            content=content,
            memory_type='working',
            timestamp=time.time()
        )
        
        self.working.append(memory)
        
        # Enforce capacity limit
        while len(self.working) > self.WORKING_CAPACITY:
            evicted = self.working.pop(0)
            # Move to episodic if significant
            if evicted.access_count > 2:
                self.episodic.append(evicted)
        
        return mem_id
    
    def store_episodic(self, content: Any, associations: Set[str] = None) -> str:
        """Store in episodic memory (time-ordered, unlimited)"""
        import time
        
        mem_id = self._generate_id()
        memory = Memory(
            id=mem_id,
            content=content,
            memory_type='episodic',
            timestamp=time.time(),
            associations=associations or set()
        )
        
        self.episodic.append(memory)
        return mem_id
    
    def store_semantic(self, key: str, content: Any, associations: Set[str] = None) -> str:
        """Store in semantic memory (key-value, permanent)"""
        import time
        
        mem_id = key
        memory = Memory(
            id=mem_id,
            content=content,
            memory_type='semantic',
            timestamp=time.time(),
            associations=associations or set()
        )
        
        self.semantic[key] = memory
        return mem_id
    
    def recall_working(self) -> List[Any]:
        """Get current working memory contents"""
        return [m.content for m in self.working]
    
    def recall_recent(self, n: int = 5) -> List[Any]:
        """Get n most recent episodic memories"""
        for m in self.episodic[-n:]:
            m.access_count += 1
        return [m.content for m in self.episodic[-n:]]
    
    def recall_semantic(self, key: str) -> Optional[Any]:
        """Retrieve from semantic memory by key"""
        if key in self.semantic:
            self.semantic[key].access_count += 1
            return self.semantic[key].content
        return None
    
    def search(self, query: str, memory_types: List[str] = None) -> List[Tuple[str, Any, float]]:
        """
        Search memories using compression distance.
        Returns (id, content, similarity) tuples.
        """
        memory_types = memory_types or ['working', 'episodic', 'semantic']
        results = []
        
        all_memories = []
        if 'working' in memory_types:
            all_memories.extend(self.working)
        if 'episodic' in memory_types:
            all_memories.extend(self.episodic)
        if 'semantic' in memory_types:
            all_memories.extend(self.semantic.values())
        
        for m in all_memories:
            content_str = str(m.content)
            similarity = 1.0 - compression_distance(query, content_str)
            if similarity > 0.3:  # Threshold
                results.append((m.id, m.content, similarity))
        
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:10]
    
    def associate(self, mem_id: str, associations: Set[str]):
        """Add associations to a memory"""
        # Search in all stores
        for m in self.working + self.episodic:
            if m.id == mem_id:
                m.associations.update(associations)
                return
        
        if mem_id in self.semantic:
            self.semantic[mem_id].associations.update(associations)
    
    def spread_activation(self, start_id: str, depth: int = 2) -> List[Tuple[str, float]]:
        """
        Spreading activation from a memory.
        Returns related memories with activation strength.
        """
        activation = {start_id: 1.0}
        visited = set()
        
        for _ in range(depth):
            new_activation = {}
            for mem_id, strength in activation.items():
                if mem_id in visited:
                    continue
                visited.add(mem_id)
                
                # Find memory
                mem = self._find_memory(mem_id)
                if mem:
                    for assoc in mem.associations:
                        if assoc not in new_activation:
                            new_activation[assoc] = 0
                        new_activation[assoc] += strength * 0.5  # Decay factor
            
            activation.update(new_activation)
        
        # Remove start and sort
        del activation[start_id]
        return sorted(activation.items(), key=lambda x: x[1], reverse=True)
    
    def _find_memory(self, mem_id: str) -> Optional[Memory]:
        """Find memory by ID in any store"""
        for m in self.working + self.episodic:
            if m.id == mem_id:
                return m
        return self.semantic.get(mem_id)
    
    def consolidate(self):
        """
        Memory consolidation: Move important episodic memories to semantic.
        Based on access frequency and recency.
        """
        import time
        current = time.time()
        
        to_consolidate = []
        for m in self.episodic:
            age = current - m.timestamp
            importance = m.access_count * (1.0 / (1 + age/3600))  # Decay with hours
            if importance > 3:  # Threshold
                to_consolidate.append(m)
        
        for m in to_consolidate:
            # Generate semantic key from content
            key = hashlib.md5(str(m.content).encode()).hexdigest()[:12]
            if key not in self.semantic:
                m.memory_type = 'semantic'
                self.semantic[key] = m


# =============================================================================
# COMPOSITIONAL GENERATOR
# =============================================================================

@dataclass
class Template:
    """A generative template with slots and constraints"""
    id: str
    pattern: str  # e.g., "The {SUBJECT} {VERB} the {OBJECT}"
    slots: Dict[str, List[str]]  # Slot name -> possible fillers
    constraints: List[Callable[[Dict[str, str]], bool]] = field(default_factory=list)


class CompositionalGenerator:
    """
    Generates outputs by:
    1. Template instantiation
    2. Grammar-based expansion
    3. Constraint-guided search
    """
    
    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self.grammar: Dict[str, List[str]] = {}  # Non-terminal -> productions
        self.memory: MemorySystem = None  # Optional memory for personalization
    
    def add_template(self, template: Template):
        self.templates[template.id] = template
    
    def add_grammar_rule(self, non_terminal: str, productions: List[str]):
        """Add grammar rules: non_terminal -> [production1, production2, ...]"""
        self.grammar[non_terminal] = productions
    
    def generate_from_template(self, template_id: str, 
                               overrides: Dict[str, str] = None) -> Optional[str]:
        """Generate text from a template"""
        if template_id not in self.templates:
            return None
        
        template = self.templates[template_id]
        overrides = overrides or {}
        
        # Try to fill slots satisfying constraints
        for _ in range(100):  # Max attempts
            assignment = {}
            
            for slot, options in template.slots.items():
                if slot in overrides:
                    assignment[slot] = overrides[slot]
                else:
                    assignment[slot] = random.choice(options)
            
            # Check constraints
            if all(c(assignment) for c in template.constraints):
                # Fill template
                result = template.pattern
                for slot, value in assignment.items():
                    result = result.replace('{' + slot + '}', value)
                return result
        
        return None  # Could not satisfy constraints
    
    def generate_from_grammar(self, start: str, max_depth: int = 10) -> str:
        """Generate text using grammar expansion"""
        return self._expand(start, max_depth)
    
    def _expand(self, symbol: str, depth: int) -> str:
        """Recursively expand a symbol"""
        if depth <= 0:
            return symbol
        
        if symbol not in self.grammar:
            return symbol
        
        # Choose a production
        production = random.choice(self.grammar[symbol])
        
        # Find and expand non-terminals
        result = []
        for token in production.split():
            if token.startswith('<') and token.endswith('>'):
                expanded = self._expand(token[1:-1], depth - 1)
                result.append(expanded)
            else:
                result.append(token)
        
        return ' '.join(result)
    
    def generate_solution(self, problem: str, constraints: List[Callable[[str], bool]]) -> Optional[str]:
        """
        Generate a solution satisfying constraints.
        Uses hill-climbing with restarts.
        """
        best_solution = None
        best_score = 0
        
        for _ in range(50):  # Restarts
            # Generate candidate
            candidate = self._generate_candidate(problem)
            
            # Score by constraint satisfaction
            score = sum(1 for c in constraints if c(candidate))
            
            if score > best_score:
                best_score = score
                best_solution = candidate
            
            if score == len(constraints):
                return candidate  # All constraints satisfied
        
        return best_solution
    
    def _generate_candidate(self, problem: str) -> str:
        """Generate a candidate solution based on problem type"""
        # Extract key words
        words = re.findall(r'\b\w+\b', problem.lower())
        
        # Look for matching template
        for tid, template in self.templates.items():
            if any(w in tid.lower() for w in words):
                return self.generate_from_template(tid) or ""
        
        # Fallback to grammar
        if 'START' in self.grammar:
            return self.generate_from_grammar('START')
        
        return ""


# =============================================================================
# UNIVERSAL REASONING KERNEL
# =============================================================================

class UniversalKernel:
    """
    The Universal Reasoning Kernel - combines all components into
    a unified reasoning system.
    
    Key Principles:
    1. Compression = Understanding (Solomonoff)
    2. Minimize Surprise (Free Energy)
    3. Propagate Constraints (Logical Consistency)
    4. Update Beliefs (Bayesian Learning)
    5. Remember and Associate (Memory)
    6. Generate and Test (Problem Solving)
    """
    
    def __init__(self, name: str = "URK"):
        self.name = name
        
        # Components
        self.patterns = PatternRecognizer()
        self.beliefs = BayesianReasoner()
        self.constraints = ConstraintPropagator()
        self.memory = MemorySystem()
        self.generator = CompositionalGenerator()
        self.generator.memory = self.memory
        
        # State
        self.context: Dict[str, Any] = {}
        self.interaction_count = 0
        
        # Initialize with basic patterns
        self._init_basic_patterns()
    
    def _init_basic_patterns(self):
        """Initialize with fundamental patterns"""
        # Question patterns
        self.patterns.add_pattern(Pattern(
            id='question',
            regex=r'^(what|who|where|when|why|how|is|are|do|does|can|could|would|should)\b',
            semantic_tags={'inquiry', 'information_seeking'}
        ))
        
        # Command patterns
        self.patterns.add_pattern(Pattern(
            id='command',
            regex=r'^(make|create|build|generate|find|calculate|solve|explain|list)\b',
            semantic_tags={'action', 'imperative'}
        ))
        
        # Assertion patterns
        self.patterns.add_pattern(Pattern(
            id='assertion',
            regex=r'\bis\s+\w+|are\s+\w+|has\s+\w+|have\s+\w+',
            semantic_tags={'fact', 'statement'}
        ))
    
    def process(self, input_text: str) -> Dict[str, Any]:
        """
        Main processing pipeline:
        1. Recognize patterns
        2. Update beliefs
        3. Check constraints
        4. Store in memory
        5. Generate response
        """
        self.interaction_count += 1
        
        # Store in working memory
        self.memory.store_working(input_text)
        
        # Pattern recognition
        patterns = self.patterns.recognize(input_text)
        primary_pattern = patterns[0][0] if patterns else 'unknown'
        
        # Extract entities and facts
        entities = self._extract_entities(input_text)
        facts = self._extract_facts(input_text)
        
        # Update beliefs based on facts
        for fact in facts:
            if fact not in self.beliefs.beliefs:
                self.beliefs.add_belief(fact, prior=0.6)
            self.beliefs.observe(input_text, supports=[fact])
        
        # Search memory for related content
        related = self.memory.search(input_text)
        
        # Generate response based on pattern type
        response = self._generate_response(input_text, primary_pattern, entities, related)
        
        # Store interaction
        self.memory.store_episodic({
            'input': input_text,
            'pattern': primary_pattern,
            'entities': entities,
            'response': response
        })
        
        return {
            'input': input_text,
            'patterns': patterns,
            'entities': entities,
            'facts': facts,
            'related_memories': [(r[0], r[2]) for r in related[:3]],
            'response': response,
            'confidence': self._calculate_confidence(patterns, related)
        }
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities (simplified)"""
        # Capitalized words (not at sentence start)
        entities = re.findall(r'(?<!\. )[A-Z][a-z]+', text)
        # Quoted strings
        entities.extend(re.findall(r'"([^"]+)"', text))
        # Numbers with context
        entities.extend(re.findall(r'\d+(?:\.\d+)?(?:\s*(?:dollars?|percent|%|years?|days?))?', text))
        return list(set(entities))
    
    def _extract_facts(self, text: str) -> List[str]:
        """Extract factual statements"""
        facts = []
        
        # "X is Y" patterns
        is_patterns = re.findall(r'(\w+)\s+is\s+(\w+)', text, re.IGNORECASE)
        for subject, predicate in is_patterns:
            facts.append(f"{subject}_is_{predicate}")
        
        # "X has Y" patterns
        has_patterns = re.findall(r'(\w+)\s+has\s+(\w+)', text, re.IGNORECASE)
        for subject, obj in has_patterns:
            facts.append(f"{subject}_has_{obj}")
        
        return facts
    
    def _generate_response(self, input_text: str, pattern: str, 
                          entities: List[str], related: List) -> str:
        """Generate appropriate response based on input type"""
        
        if pattern == 'question':
            return self._answer_question(input_text, entities, related)
        elif pattern == 'command':
            return self._execute_command(input_text, entities)
        elif pattern == 'assertion':
            return self._acknowledge_assertion(input_text, entities)
        else:
            return self._default_response(input_text, related)
    
    def _answer_question(self, question: str, entities: List[str], 
                        related: List) -> str:
        """Answer a question using beliefs and memory"""
        
        # Check beliefs for relevant information
        relevant_beliefs = []
        for entity in entities:
            for prop, belief in self.beliefs.beliefs.items():
                if entity.lower() in prop.lower():
                    relevant_beliefs.append((prop, belief.probability))
        
        if relevant_beliefs:
            best = max(relevant_beliefs, key=lambda x: x[1])
            return f"Based on what I know: {best[0]} (confidence: {best[1]:.0%})"
        
        # Check memory
        if related:
            best_memory = related[0][1]
            return f"From my memory: {best_memory}"
        
        # Uncertain
        uncertain = self.beliefs.most_uncertain()
        if uncertain:
            return f"I'm uncertain. Could you tell me more about {uncertain}?"
        
        return "I don't have enough information to answer that."
    
    def _execute_command(self, command: str, entities: List[str]) -> str:
        """Execute a command"""
        
        if 'calculate' in command.lower() or 'solve' in command.lower():
            # Try to extract and evaluate math
            numbers = re.findall(r'\d+(?:\.\d+)?', command)
            if len(numbers) >= 2:
                try:
                    nums = [float(n) for n in numbers]
                    if 'add' in command or '+' in command or 'sum' in command:
                        result = sum(nums)
                        return f"Result: {result}"
                    elif 'multiply' in command or '*' in command or 'product' in command:
                        result = 1
                        for n in nums:
                            result *= n
                        return f"Result: {result}"
                    elif 'subtract' in command or '-' in command:
                        result = nums[0] - sum(nums[1:])
                        return f"Result: {result}"
                except:
                    pass
        
        if 'list' in command.lower() or 'show' in command.lower():
            # List something from memory
            memories = self.memory.recall_recent(5)
            if memories:
                return f"Recent items: {memories}"
        
        if 'remember' in command.lower() or 'store' in command.lower():
            # Store something
            content = command.split(':', 1)[-1].strip() if ':' in command else command
            key = entities[0] if entities else 'info'
            self.memory.store_semantic(key, content)
            return f"Stored '{content}' under '{key}'"
        
        return f"Command recognized. Working on: {entities if entities else 'task'}"
    
    def _acknowledge_assertion(self, assertion: str, entities: List[str]) -> str:
        """Acknowledge and store an assertion"""
        # Store as semantic memory
        if entities:
            self.memory.store_semantic(entities[0], assertion)
        
        # Create/update belief
        fact_key = '_'.join(entities[:2]) if len(entities) >= 2 else 'fact'
        self.beliefs.add_belief(fact_key, prior=0.7)
        self.beliefs.observe(assertion, supports=[fact_key])
        
        return f"Understood. I've noted that: {assertion}"
    
    def _default_response(self, input_text: str, related: List) -> str:
        """Default response when pattern is unclear"""
        if related:
            return f"That relates to: {related[0][1]}"
        return "I'm processing that. Could you elaborate?"
    
    def _calculate_confidence(self, patterns: List, related: List) -> float:
        """Calculate confidence in the response"""
        pattern_conf = patterns[0][1] if patterns else 0.3
        memory_conf = related[0][2] if related else 0.0
        return (pattern_conf + memory_conf) / 2
    
    def ask(self, question: str) -> str:
        """Simple interface for asking questions"""
        result = self.process(question)
        return result['response']
    
    def learn(self, fact: str, confidence: float = 0.8):
        """Learn a new fact"""
        self.beliefs.add_belief(fact, prior=confidence)
        self.memory.store_semantic(fact, fact)
        self.patterns.learn_pattern(f'fact_{len(self.patterns.patterns)}', [fact])
    
    def reason(self, premises: List[str], goal: str) -> Tuple[bool, str]:
        """
        Logical reasoning: Given premises, try to prove goal.
        Uses constraint propagation.
        """
        # Create CSP from premises
        csp = ConstraintPropagator()
        
        # Extract variables and constraints from premises
        variables = set()
        for premise in premises:
            vars_in_premise = re.findall(r'\b([A-Z])\b', premise)
            variables.update(vars_in_premise)
        
        for var in variables:
            csp.add_variable(var, [True, False])
        
        # Add constraints based on premises
        for premise in premises:
            if '->' in premise:  # Implication
                parts = premise.split('->')
                if len(parts) == 2:
                    a, b = parts[0].strip(), parts[1].strip()
                    if a in variables and b in variables:
                        csp.add_constraint([a, b], 
                            lambda x, y: not x or y,  # A -> B ≡ ¬A ∨ B
                            f"{a} implies {b}")
        
        # Try to solve
        solution = csp.solve()
        
        if solution:
            goal_var = re.search(r'\b([A-Z])\b', goal)
            if goal_var and goal_var.group(1) in solution:
                result = solution[goal_var.group(1)]
                return (result, f"Proved: {goal} is {result}")
            return (True, f"Reasoning complete: {solution}")
        
        return (False, "Could not prove goal with given premises")
    
    def analogy(self, a: str, b: str, c: str) -> str:
        """Complete analogy: A:B :: C:?"""
        candidates = self.patterns.analogical_match(a, b, c)
        if candidates:
            best = candidates[0]
            return f"{a} : {b} :: {c} : {best[0]} (similarity: {best[1]:.2f})"
        return f"Could not find analogical match for {a}:{b}::{c}:?"
    
    def explain(self, topic: str) -> str:
        """Explain what the kernel knows about a topic"""
        lines = [f"=== Knowledge about '{topic}' ==="]
        
        # Check beliefs
        relevant_beliefs = [(k, v) for k, v in self.beliefs.beliefs.items() 
                          if topic.lower() in k.lower()]
        if relevant_beliefs:
            lines.append("\nBeliefs:")
            for k, v in relevant_beliefs:
                lines.append(f"  - {k}: {v.probability:.0%} confident")
        
        # Check memory
        memories = self.memory.search(topic)
        if memories:
            lines.append("\nMemories:")
            for mid, content, sim in memories[:3]:
                lines.append(f"  - [{mid}] {content} (relevance: {sim:.2f})")
        
        # Check patterns
        matching_patterns = self.patterns.recognize(topic)
        if matching_patterns:
            lines.append("\nRecognized patterns:")
            for pid, score in matching_patterns[:3]:
                lines.append(f"  - {pid}: {score:.2f}")
        
        if len(lines) == 1:
            lines.append("\nNo significant knowledge found.")
        
        return '\n'.join(lines)
    
    def save_state(self, filepath: str):
        """Save kernel state to JSON"""
        state = {
            'name': self.name,
            'interaction_count': self.interaction_count,
            'beliefs': {k: {'prob': v.probability, 'evidence': v.evidence} 
                       for k, v in self.beliefs.beliefs.items()},
            'semantic_memory': {k: str(v.content) 
                               for k, v in self.memory.semantic.items()},
            'context': self.context
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filepath: str):
        """Load kernel state from JSON"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.name = state.get('name', 'URK')
        self.interaction_count = state.get('interaction_count', 0)
        
        for k, v in state.get('beliefs', {}).items():
            self.beliefs.add_belief(k, v.get('prob', 0.5))
            for e in v.get('evidence', []):
                self.beliefs.observe(e, supports=[k])
        
        for k, v in state.get('semantic_memory', {}).items():
            self.memory.store_semantic(k, v)
        
        self.context = state.get('context', {})


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_kernel(name: str = "URK") -> UniversalKernel:
    """Create a new Universal Reasoning Kernel"""
    return UniversalKernel(name)


def quick_reason(premises: List[str], conclusion: str) -> bool:
    """Quick logical reasoning check"""
    kernel = UniversalKernel()
    result, _ = kernel.reason(premises, conclusion)
    return result


def quick_analogy(a: str, b: str, c: str) -> str:
    """Quick analogy completion"""
    kernel = UniversalKernel()
    return kernel.analogy(a, b, c)


# =============================================================================
# MAIN / DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("UNIVERSAL REASONING KERNEL (URK)")
    print("Mathematical AI without LLMs")
    print("=" * 60)
    
    kernel = create_kernel("Demo")
    
    # Test pattern recognition
    print("\n--- Pattern Recognition ---")
    tests = [
        "What is the capital of France?",
        "Create a recipe for pasta",
        "The sky is blue"
    ]
    for test in tests:
        result = kernel.process(test)
        print(f"Input: {test}")
        print(f"  Pattern: {result['patterns'][0] if result['patterns'] else 'none'}")
        print(f"  Response: {result['response']}")
    
    # Test learning
    print("\n--- Learning ---")
    kernel.learn("Paris is the capital of France")
    kernel.learn("France is in Europe")
    print("Learned: Paris is capital of France, France is in Europe")
    
    # Query beliefs
    print("\n--- Belief Query ---")
    print(kernel.explain("France"))
    
    # Test analogy
    print("\n--- Analogical Reasoning ---")
    print(kernel.analogy("cat", "cats", "dog"))
    print(kernel.analogy("good", "better", "bad"))
    
    # Test constraint satisfaction
    print("\n--- Constraint Satisfaction ---")
    csp = ConstraintPropagator()
    csp.add_variable("A", [1, 2, 3])
    csp.add_variable("B", [1, 2, 3])
    csp.add_variable("C", [1, 2, 3])
    csp.add_constraint(["A", "B"], lambda a, b: a != b, "A ≠ B")
    csp.add_constraint(["B", "C"], lambda b, c: b != c, "B ≠ C")
    csp.add_constraint(["A", "C"], lambda a, c: a < c, "A < C")
    solution = csp.solve()
    print(f"CSP Solution: {solution}")
    
    # Test Bayesian reasoning
    print("\n--- Bayesian Reasoning ---")
    bayes = BayesianReasoner()
    bayes.add_belief("raining", prior=0.3)
    bayes.add_belief("cloudy", prior=0.5)
    bayes.add_conditional("raining", "cloudy", 0.8)
    bayes.observe("The sky is overcast", supports=["cloudy"])
    bayes.observe("I heard thunder", supports=["raining"])
    print(f"P(raining) = {bayes.query('raining')}")
    print(f"P(cloudy) = {bayes.query('cloudy')}")
    
    # Test compression-based similarity
    print("\n--- Compression Similarity ---")
    texts = ["Hello world", "Hello there", "Goodbye world", "Completely different"]
    base = "Hello world"
    for t in texts:
        dist = compression_distance(base, t)
        print(f"'{base}' vs '{t}': distance={dist:.3f}, similarity={1-dist:.3f}")
    
    print("\n--- Information Theory ---")
    # Maximum entropy (most uncertain) at p=0.5
    for p in [0.1, 0.3, 0.5, 0.7, 0.9]:
        H = entropy([p, 1-p])
        print(f"P={p}: Entropy={H:.3f} bits")
    
    print("\n" + "=" * 60)
    print("URK ready for use!")
