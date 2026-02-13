"""
Universal Agent Core
====================
Algorithmic foundations common to ALL intelligent agents.

These are mathematical invariants that appear across:
- Reinforcement Learning (Q-learning, Policy Gradient)
- Planning (A*, MCTS, HTN)
- Game Theory (Nash, Minimax)
- Cognitive Science (Working Memory, Attention)
- Neuroscience (Predictive Coding, Hebbian Learning)
- Control Theory (PID, Kalman)
- Evolution (Genetic Algorithms, Selection)

Each component is mathematically defined and can be composed
to create different agent architectures.
"""

from __future__ import annotations
import math
import random
import heapq
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Generic
from collections import defaultdict, deque
from abc import ABC, abstractmethod

# Type variables for generic state/action
S = TypeVar('S')  # State type
A = TypeVar('A')  # Action type


# =============================================================================
# 1. BELLMAN OPTIMALITY - The Foundation of Sequential Decisions
# =============================================================================
# V*(s) = max_a [R(s,a) + γ * Σ P(s'|s,a) * V*(s')]
# "Optimal value = immediate reward + discounted future value"

@dataclass
class MDP(Generic[S, A]):
    """
    Markov Decision Process - the mathematical model of sequential decision making.
    Every RL/planning problem can be expressed as an MDP.
    """
    states: Set[S]
    actions: Set[A]
    transition: Callable[[S, A], Dict[S, float]]  # P(s'|s,a) -> distribution
    reward: Callable[[S, A, S], float]            # R(s,a,s')
    gamma: float = 0.99                            # Discount factor
    
    def get_transitions(self, state: S, action: A) -> Dict[S, float]:
        """Get probability distribution over next states"""
        return self.transition(state, action)


def value_iteration(mdp: MDP, epsilon: float = 1e-6, max_iter: int = 1000) -> Dict[Any, float]:
    """
    Bellman backup until convergence.
    Finds optimal value function V*(s) for all states.
    
    V(s) ← max_a [Σ P(s'|s,a) * (R(s,a,s') + γ*V(s'))]
    """
    V = {s: 0.0 for s in mdp.states}
    
    for iteration in range(max_iter):
        delta = 0
        new_V = {}
        
        for s in mdp.states:
            old_v = V[s]
            
            # Bellman backup: find max over actions
            best_value = float('-inf')
            for a in mdp.actions:
                action_value = 0
                for s_next, prob in mdp.get_transitions(s, a).items():
                    r = mdp.reward(s, a, s_next)
                    action_value += prob * (r + mdp.gamma * V.get(s_next, 0))
                best_value = max(best_value, action_value)
            
            new_V[s] = best_value if best_value > float('-inf') else 0
            delta = max(delta, abs(old_v - new_V[s]))
        
        V = new_V
        if delta < epsilon:
            break
    
    return V


def q_learning_update(Q: Dict[Tuple, float], state, action, reward: float, 
                      next_state, alpha: float = 0.1, gamma: float = 0.99,
                      available_actions: List = None) -> float:
    """
    Q-learning: Model-free online RL
    Q(s,a) ← Q(s,a) + α[r + γ*max_a'(Q(s',a')) - Q(s,a)]
    """
    current_q = Q.get((state, action), 0.0)
    
    # Max Q-value for next state
    if available_actions is None:
        next_max = max((Q.get((next_state, a), 0.0) for a in Q.keys() 
                       if isinstance(a, tuple) and a[0] == next_state), default=0)
    else:
        next_max = max((Q.get((next_state, a), 0.0) for a in available_actions), default=0)
    
    # TD update
    td_target = reward + gamma * next_max
    td_error = td_target - current_q
    new_q = current_q + alpha * td_error
    
    Q[(state, action)] = new_q
    return td_error  # Useful for prioritized replay


def policy_gradient_loss(log_probs: List[float], rewards: List[float], 
                         gamma: float = 0.99) -> float:
    """
    REINFORCE: Policy gradient theorem
    ∇J(θ) = E[Σ ∇log π(a|s) * G_t]
    where G_t = Σ γ^k * r_{t+k} (discounted return)
    """
    # Compute discounted returns
    returns = []
    G = 0
    for r in reversed(rewards):
        G = r + gamma * G
        returns.insert(0, G)
    
    # Normalize returns (reduces variance)
    if len(returns) > 1:
        mean_r = sum(returns) / len(returns)
        std_r = (sum((r - mean_r)**2 for r in returns) / len(returns)) ** 0.5
        if std_r > 0:
            returns = [(r - mean_r) / std_r for r in returns]
    
    # Policy gradient: -log_prob * return (negative for gradient ascent)
    loss = sum(-lp * r for lp, r in zip(log_probs, returns))
    return loss


# =============================================================================
# 2. ATTENTION - Universal Selection Mechanism
# =============================================================================
# Attention(Q,K,V) = softmax(QK^T / √d) * V
# "Focus limited resources on what matters"

def softmax(values: List[float], temperature: float = 1.0) -> List[float]:
    """Temperature-controlled probability distribution"""
    if not values:
        return []
    max_v = max(values)
    exp_v = [math.exp((v - max_v) / temperature) for v in values]
    total = sum(exp_v)
    return [e / total for e in exp_v]


def attention_weights(query: List[float], keys: List[List[float]], 
                      temperature: float = 1.0) -> List[float]:
    """
    Scaled dot-product attention weights.
    Given a query, compute attention over all keys.
    
    α_i = softmax(q · k_i / √d)
    """
    d = len(query) ** 0.5  # Scale factor
    
    # Compute similarities
    similarities = []
    for k in keys:
        dot = sum(qi * ki for qi, ki in zip(query, k))
        similarities.append(dot / d if d > 0 else dot)
    
    return softmax(similarities, temperature)


def attend(query: List[float], keys: List[List[float]], values: List[Any],
           temperature: float = 1.0) -> Tuple[Any, List[float]]:
    """
    Full attention: select from values based on query-key similarity.
    Returns weighted combination (or best match for non-numeric values).
    """
    weights = attention_weights(query, keys, temperature)
    
    # If values are numeric, return weighted sum
    if all(isinstance(v, (int, float)) for v in values):
        weighted_value = sum(w * v for w, v in zip(weights, values))
        return weighted_value, weights
    
    # For non-numeric, return highest-weight value
    best_idx = weights.index(max(weights))
    return values[best_idx], weights


class AttentionHead:
    """
    A single attention head with learnable projections.
    Used for multi-head attention.
    """
    def __init__(self, d_model: int, d_head: int):
        self.d_model = d_model
        self.d_head = d_head
        # Random initialization (would be learned in real system)
        self.W_q = [[random.gauss(0, 0.1) for _ in range(d_head)] for _ in range(d_model)]
        self.W_k = [[random.gauss(0, 0.1) for _ in range(d_head)] for _ in range(d_model)]
        self.W_v = [[random.gauss(0, 0.1) for _ in range(d_head)] for _ in range(d_model)]
    
    def project(self, x: List[float], W: List[List[float]]) -> List[float]:
        """Project vector through weight matrix"""
        return [sum(xi * w for xi, w in zip(x, col)) for col in zip(*W)]
    
    def forward(self, query: List[float], keys: List[List[float]], 
                values: List[List[float]]) -> Tuple[List[float], List[float]]:
        """Forward pass through attention head"""
        q = self.project(query, self.W_q)
        ks = [self.project(k, self.W_k) for k in keys]
        vs = [self.project(v, self.W_v) for v in values]
        
        weights = attention_weights(q, ks)
        
        # Weighted sum of value projections
        output = [sum(w * v[i] for w, v in zip(weights, vs)) 
                  for i in range(self.d_head)]
        
        return output, weights


# =============================================================================
# 3. EXPLORATION vs EXPLOITATION - The Fundamental Tradeoff
# =============================================================================
# "When to try new things vs. stick with what works"

def epsilon_greedy(q_values: Dict[Any, float], epsilon: float = 0.1) -> Any:
    """
    ε-greedy: Explore with probability ε, exploit otherwise.
    Simple but effective.
    """
    if random.random() < epsilon:
        return random.choice(list(q_values.keys()))
    return max(q_values.keys(), key=lambda a: q_values[a])


def ucb_select(values: Dict[Any, float], counts: Dict[Any, int], 
               total_count: int, c: float = 2.0) -> Any:
    """
    Upper Confidence Bound (UCB1): Optimism in the face of uncertainty.
    UCB(a) = Q(a) + c * √(ln(N) / n(a))
    
    Balances exploitation (Q value) with exploration (uncertainty bonus)
    """
    if not values:
        return None
    
    ucb_values = {}
    for action, value in values.items():
        count = counts.get(action, 1)
        exploration_bonus = c * math.sqrt(math.log(total_count + 1) / count)
        ucb_values[action] = value + exploration_bonus
    
    return max(ucb_values.keys(), key=lambda a: ucb_values[a])


def thompson_sample(successes: Dict[Any, int], failures: Dict[Any, int]) -> Any:
    """
    Thompson Sampling: Bayesian approach to exploration.
    Sample from posterior Beta(α=successes+1, β=failures+1) for each arm.
    
    Naturally balances exploration/exploitation through uncertainty.
    """
    samples = {}
    for action in successes.keys():
        alpha = successes.get(action, 0) + 1
        beta = failures.get(action, 0) + 1
        # Sample from Beta distribution (approximation using numpy-free method)
        samples[action] = _beta_sample(alpha, beta)
    
    return max(samples.keys(), key=lambda a: samples[a])


def _beta_sample(alpha: float, beta: float) -> float:
    """Sample from Beta distribution using gamma ratio"""
    # Using the fact that Beta(α,β) = Gamma(α) / (Gamma(α) + Gamma(β))
    x = sum(-math.log(random.random() + 1e-10) for _ in range(int(alpha)))
    y = sum(-math.log(random.random() + 1e-10) for _ in range(int(beta)))
    return x / (x + y) if (x + y) > 0 else 0.5


def boltzmann_select(q_values: Dict[Any, float], temperature: float = 1.0) -> Any:
    """
    Boltzmann (softmax) exploration: Higher temperature = more exploration.
    P(a) ∝ exp(Q(a) / τ)
    """
    actions = list(q_values.keys())
    values = [q_values[a] for a in actions]
    probs = softmax(values, temperature)
    
    # Weighted random selection
    r = random.random()
    cumsum = 0
    for action, prob in zip(actions, probs):
        cumsum += prob
        if r < cumsum:
            return action
    return actions[-1]


# =============================================================================
# 4. TEMPORAL CREDIT ASSIGNMENT - What Caused What
# =============================================================================
# "Which past decisions led to current outcomes"

def temporal_difference(values: List[float], rewards: List[float], 
                        gamma: float = 0.99, lambda_: float = 0.9) -> List[float]:
    """
    TD(λ): Eligibility traces for credit assignment.
    Blends TD(0) with Monte Carlo through λ parameter.
    
    δ_t = r_t + γV(s_{t+1}) - V(s_t)
    V(s) ← V(s) + α * δ_t * e_t
    
    where e_t is the eligibility trace.
    """
    n = len(values)
    td_errors = []
    
    for t in range(n - 1):
        # TD error: actual return vs predicted
        td_error = rewards[t] + gamma * values[t + 1] - values[t]
        td_errors.append(td_error)
    
    # Last step (terminal)
    td_errors.append(rewards[-1] if rewards else 0)
    
    # Apply eligibility traces (backward view)
    traces = [0.0] * n
    for t in range(n - 1, -1, -1):
        traces[t] = td_errors[t]
        if t < n - 1:
            traces[t] += gamma * lambda_ * traces[t + 1]
    
    return traces


def advantage_estimation(values: List[float], rewards: List[float],
                         gamma: float = 0.99, lambda_: float = 0.95) -> List[float]:
    """
    Generalized Advantage Estimation (GAE).
    Used in PPO, A3C, and other policy gradient methods.
    
    A_t = Σ (γλ)^l * δ_{t+l}
    where δ_t = r_t + γV(s_{t+1}) - V(s_t)
    """
    n = len(values)
    advantages = [0.0] * n
    gae = 0
    
    for t in range(n - 1, -1, -1):
        if t == n - 1:
            delta = rewards[t] - values[t]  # Terminal state
        else:
            delta = rewards[t] + gamma * values[t + 1] - values[t]
        
        gae = delta + gamma * lambda_ * gae
        advantages[t] = gae
    
    return advantages


class ExperienceReplay:
    """
    Experience Replay Buffer - breaks temporal correlation.
    Stores (s, a, r, s', done) transitions for batch learning.
    """
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)
    
    def store(self, state, action, reward: float, next_state, done: bool):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int) -> List[Tuple]:
        return random.sample(list(self.buffer), min(batch_size, len(self.buffer)))
    
    def __len__(self):
        return len(self.buffer)


class PrioritizedReplay(ExperienceReplay):
    """
    Prioritized Experience Replay - sample by TD error magnitude.
    Important transitions are replayed more often.
    """
    def __init__(self, capacity: int = 10000, alpha: float = 0.6):
        super().__init__(capacity)
        self.priorities = deque(maxlen=capacity)
        self.alpha = alpha  # Priority exponent
    
    def store(self, state, action, reward: float, next_state, done: bool, 
              priority: float = 1.0):
        self.buffer.append((state, action, reward, next_state, done))
        self.priorities.append(priority ** self.alpha)
    
    def sample(self, batch_size: int) -> Tuple[List[Tuple], List[int]]:
        total_priority = sum(self.priorities)
        probs = [p / total_priority for p in self.priorities]
        
        indices = random.choices(range(len(self.buffer)), weights=probs, k=batch_size)
        samples = [self.buffer[i] for i in indices]
        
        return samples, indices
    
    def update_priority(self, index: int, priority: float):
        if 0 <= index < len(self.priorities):
            self.priorities[index] = priority ** self.alpha


# =============================================================================
# 5. PREDICTIVE CODING - The Brain's Algorithm
# =============================================================================
# "Minimize prediction error at every level"

@dataclass
class Prediction:
    """A prediction with confidence"""
    value: Any
    confidence: float
    timestamp: float = 0.0


class PredictiveCoder:
    """
    Predictive Coding: Hierarchical prediction error minimization.
    
    Each level predicts the level below, passing up only prediction errors.
    This is the computational principle behind the Free Energy Principle.
    """
    def __init__(self, levels: int = 3):
        self.levels = levels
        self.predictions: List[Optional[Prediction]] = [None] * levels
        self.observations: List[Optional[Any]] = [None] * levels
        self.errors: List[float] = [0.0] * levels
        self.learning_rate = 0.1
    
    def predict(self, level: int, value: Any, confidence: float = 0.5):
        """Make a prediction at a given level"""
        import time
        self.predictions[level] = Prediction(value, confidence, time.time())
    
    def observe(self, level: int, value: Any) -> float:
        """
        Observe actual value, compute prediction error.
        Returns prediction error magnitude.
        """
        self.observations[level] = value
        
        if self.predictions[level] is not None:
            # Compute prediction error
            pred = self.predictions[level]
            error = self._compute_error(pred.value, value)
            
            # Weight error by (inverse) confidence
            weighted_error = error * (1 - pred.confidence)
            self.errors[level] = weighted_error
            
            # Update prediction (simple gradient descent on error)
            self._update_prediction(level, value, error)
            
            return weighted_error
        
        return 0.0
    
    def _compute_error(self, predicted: Any, observed: Any) -> float:
        """Compute error between prediction and observation"""
        if isinstance(predicted, (int, float)) and isinstance(observed, (int, float)):
            return abs(predicted - observed)
        elif isinstance(predicted, str) and isinstance(observed, str):
            # Character-level difference
            return sum(1 for a, b in zip(predicted, observed) if a != b) / max(len(predicted), len(observed), 1)
        else:
            return 0.0 if predicted == observed else 1.0
    
    def _update_prediction(self, level: int, observed: Any, error: float):
        """Update prediction to reduce future errors"""
        if self.predictions[level] is None:
            return
        
        pred = self.predictions[level]
        
        # Increase confidence if prediction was accurate
        if error < 0.1:
            pred.confidence = min(1.0, pred.confidence + self.learning_rate)
        else:
            pred.confidence = max(0.0, pred.confidence - self.learning_rate)
        
        # For numeric predictions, adjust value
        if isinstance(pred.value, (int, float)) and isinstance(observed, (int, float)):
            pred.value = pred.value + self.learning_rate * (observed - pred.value)
    
    def total_surprise(self) -> float:
        """Total prediction error across all levels (Free Energy proxy)"""
        return sum(self.errors)
    
    def predict_next(self, level: int, history: List[Any]) -> Prediction:
        """Predict next value based on history"""
        if not history:
            return Prediction(None, 0.0)
        
        if all(isinstance(h, (int, float)) for h in history):
            # Simple autoregressive prediction
            if len(history) >= 2:
                trend = history[-1] - history[-2]
                predicted = history[-1] + trend
            else:
                predicted = history[-1]
            
            # Confidence based on trend stability
            if len(history) >= 3:
                trends = [history[i+1] - history[i] for i in range(len(history)-1)]
                variance = sum((t - sum(trends)/len(trends))**2 for t in trends) / len(trends)
                confidence = 1.0 / (1.0 + variance)
            else:
                confidence = 0.3
            
            return Prediction(predicted, confidence)
        
        # For non-numeric, predict most recent
        return Prediction(history[-1], 0.5)


# =============================================================================
# 6. HIERARCHICAL ABSTRACTION - Chunking for Capacity
# =============================================================================
# "Group detailed states into abstract chunks"

@dataclass
class AbstractState:
    """A high-level state abstracting over low-level details"""
    id: str
    members: Set[Any]
    features: Dict[str, float] = field(default_factory=dict)


class StateAbstractor:
    """
    Hierarhical State Abstraction.
    Groups similar states to reduce effective state space.
    
    Key insight: Human working memory holds 7±2 "chunks", not items.
    """
    def __init__(self, similarity_threshold: float = 0.8):
        self.abstractions: Dict[str, AbstractState] = {}
        self.state_to_abstract: Dict[Any, str] = {}
        self.threshold = similarity_threshold
    
    def abstract(self, state: Any, features: Dict[str, float] = None) -> str:
        """
        Map a concrete state to its abstraction.
        Creates new abstraction if none is similar enough.
        """
        features = features or {}
        
        # Check existing abstractions
        for abs_id, abstract in self.abstractions.items():
            if self._similarity(features, abstract.features) >= self.threshold:
                abstract.members.add(state)
                self.state_to_abstract[state] = abs_id
                return abs_id
        
        # Create new abstraction
        new_id = f"abs_{len(self.abstractions)}"
        self.abstractions[new_id] = AbstractState(
            id=new_id,
            members={state},
            features=features.copy()
        )
        self.state_to_abstract[state] = new_id
        return new_id
    
    def _similarity(self, f1: Dict[str, float], f2: Dict[str, float]) -> float:
        """Cosine similarity between feature vectors"""
        if not f1 or not f2:
            return 0.0
        
        common_keys = set(f1.keys()) & set(f2.keys())
        if not common_keys:
            return 0.0
        
        dot = sum(f1[k] * f2[k] for k in common_keys)
        norm1 = sum(f1[k]**2 for k in common_keys) ** 0.5
        norm2 = sum(f2[k]**2 for k in common_keys) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def get_abstract(self, state: Any) -> Optional[str]:
        """Get abstraction for a state"""
        return self.state_to_abstract.get(state)
    
    def merge(self, abs_id1: str, abs_id2: str) -> str:
        """Merge two abstractions"""
        if abs_id1 not in self.abstractions or abs_id2 not in self.abstractions:
            return abs_id1
        
        a1 = self.abstractions[abs_id1]
        a2 = self.abstractions[abs_id2]
        
        # Merge members
        a1.members.update(a2.members)
        
        # Average features
        all_keys = set(a1.features.keys()) | set(a2.features.keys())
        for k in all_keys:
            v1 = a1.features.get(k, 0)
            v2 = a2.features.get(k, 0)
            a1.features[k] = (v1 + v2) / 2
        
        # Update mappings
        for state in a2.members:
            self.state_to_abstract[state] = abs_id1
        
        del self.abstractions[abs_id2]
        return abs_id1


class HierarchicalRL:
    """
    Hierarchical Reinforcement Learning (Options Framework).
    Actions at higher levels are "options" - temporally extended actions.
    """
    def __init__(self):
        self.options: Dict[str, 'Option'] = {}
        self.primitive_actions: Set[Any] = set()
    
    def add_option(self, option: 'Option'):
        self.options[option.name] = option
    
    def add_primitive(self, action: Any):
        self.primitive_actions.add(action)
    
    def available_actions(self, state: Any) -> List[Any]:
        """Get all available actions (options + primitives) in a state"""
        available = list(self.primitive_actions)
        for opt in self.options.values():
            if opt.initiation_set(state):
                available.append(opt)
        return available
    
    def execute(self, action: Any, state: Any, 
                step_fn: Callable[[Any, Any], Tuple[Any, float, bool]]) -> Tuple[Any, float]:
        """
        Execute an action (option or primitive).
        Returns (final_state, total_reward).
        """
        if isinstance(action, Option):
            return action.execute(state, step_fn)
        else:
            next_state, reward, done = step_fn(state, action)
            return next_state, reward


@dataclass
class Option:
    """
    An option in the Options Framework.
    Consists of: initiation set, policy, termination condition.
    """
    name: str
    initiation_set: Callable[[Any], bool]  # Where can this option start?
    policy: Callable[[Any], Any]            # What action to take?
    termination: Callable[[Any], float]     # Probability of terminating
    
    def execute(self, state: Any, 
                step_fn: Callable[[Any, Any], Tuple[Any, float, bool]]) -> Tuple[Any, float]:
        """Execute option until termination"""
        total_reward = 0
        current_state = state
        
        for _ in range(100):  # Safety limit
            action = self.policy(current_state)
            next_state, reward, done = step_fn(current_state, action)
            total_reward += reward
            current_state = next_state
            
            if done or random.random() < self.termination(current_state):
                break
        
        return current_state, total_reward


# =============================================================================
# 7. HEBBIAN LEARNING - Associative Memory
# =============================================================================
# "Neurons that fire together, wire together"

class HebbianNetwork:
    """
    Hebbian Learning Network: Unsupervised associative learning.
    
    w_ij ← w_ij + η * x_i * x_j
    
    Forms associations between co-occurring patterns.
    """
    def __init__(self, size: int, learning_rate: float = 0.1):
        self.size = size
        self.learning_rate = learning_rate
        # Weight matrix (symmetric)
        self.weights = [[0.0] * size for _ in range(size)]
    
    def activate(self, pattern: List[float]) -> List[float]:
        """
        Activate network with a pattern.
        Returns pattern completion based on associations.
        """
        if len(pattern) != self.size:
            raise ValueError(f"Pattern size {len(pattern)} != network size {self.size}")
        
        output = []
        for i in range(self.size):
            activation = sum(self.weights[i][j] * pattern[j] for j in range(self.size))
            output.append(self._sigmoid(activation))
        
        return output
    
    def learn(self, pattern: List[float]):
        """
        Learn associations in a pattern.
        Strengthens connections between co-active units.
        """
        for i in range(self.size):
            for j in range(self.size):
                if i != j:
                    # Hebbian update
                    delta = self.learning_rate * pattern[i] * pattern[j]
                    self.weights[i][j] += delta
                    
                    # Weight decay (prevents runaway)
                    self.weights[i][j] *= 0.99
    
    def recall(self, partial: List[float], iterations: int = 10) -> List[float]:
        """
        Pattern completion: Fill in missing parts of a pattern.
        Uses iterative settling.
        """
        current = partial.copy()
        
        for _ in range(iterations):
            new_pattern = self.activate(current)
            
            # Keep known values, update unknowns
            for i in range(self.size):
                if partial[i] > 0.9:  # Known value
                    new_pattern[i] = partial[i]
            
            # Check for convergence
            if all(abs(a - b) < 0.01 for a, b in zip(current, new_pattern)):
                break
            
            current = new_pattern
        
        return current
    
    def _sigmoid(self, x: float) -> float:
        """Sigmoid activation"""
        return 1.0 / (1.0 + math.exp(-x))


# =============================================================================
# 8. GAME THEORY - Multi-Agent Reasoning
# =============================================================================
# "Optimal behavior when others are also optimizing"

def minimax(game_tree: Callable[[Any, bool], Tuple[List[Any], List[float]]],
            state: Any, depth: int, maximizing: bool) -> Tuple[float, Any]:
    """
    Minimax with depth limit.
    Finds optimal play assuming adversarial opponent.
    
    Used in: Chess, Go, adversarial planning
    """
    children, utilities = game_tree(state, maximizing)
    
    if depth == 0 or not children:
        # Terminal or depth limit
        return (utilities[0] if utilities else 0, None)
    
    if maximizing:
        best_value = float('-inf')
        best_action = None
        for child, util in zip(children, utilities):
            value, _ = minimax(game_tree, child, depth - 1, False)
            if value > best_value:
                best_value = value
                best_action = child
        return best_value, best_action
    else:
        best_value = float('inf')
        best_action = None
        for child, util in zip(children, utilities):
            value, _ = minimax(game_tree, child, depth - 1, True)
            if value < best_value:
                best_value = value
                best_action = child
        return best_value, best_action


def alpha_beta(game_tree: Callable[[Any, bool], Tuple[List[Any], List[float]]],
               state: Any, depth: int, alpha: float, beta: float, 
               maximizing: bool) -> Tuple[float, Any]:
    """
    Alpha-Beta pruning: Minimax with pruning.
    Prunes branches that can't affect the final decision.
    """
    children, utilities = game_tree(state, maximizing)
    
    if depth == 0 or not children:
        return (utilities[0] if utilities else 0, None)
    
    best_action = children[0] if children else None
    
    if maximizing:
        value = float('-inf')
        for child, util in zip(children, utilities):
            child_value, _ = alpha_beta(game_tree, child, depth - 1, alpha, beta, False)
            if child_value > value:
                value = child_value
                best_action = child
            alpha = max(alpha, value)
            if beta <= alpha:
                break  # Prune
        return value, best_action
    else:
        value = float('inf')
        for child, util in zip(children, utilities):
            child_value, _ = alpha_beta(game_tree, child, depth - 1, alpha, beta, True)
            if child_value < value:
                value = child_value
                best_action = child
            beta = min(beta, value)
            if beta <= alpha:
                break  # Prune
        return value, best_action


def nash_equilibrium_2x2(payoff_matrix: List[List[Tuple[float, float]]]) -> Tuple[List[float], List[float]]:
    """
    Find mixed Nash equilibrium for 2x2 games.
    Returns (row_strategy, col_strategy).
    
    Example: Prisoner's Dilemma, Matching Pennies
    """
    # Extract payoffs for player 1 (row player)
    a, b = payoff_matrix[0][0][0], payoff_matrix[0][1][0]
    c, d = payoff_matrix[1][0][0], payoff_matrix[1][1][0]
    
    # Extract payoffs for player 2 (column player)
    A, B = payoff_matrix[0][0][1], payoff_matrix[0][1][1]
    C, D = payoff_matrix[1][0][1], payoff_matrix[1][1][1]
    
    # Check for dominant strategies first
    # ... (simplified: assume mixed equilibrium exists)
    
    # Mixed strategy probabilities
    # Row player: makes column player indifferent
    # q = (D - B) / (A - B - C + D)
    denom_row = A - B - C + D
    if abs(denom_row) > 1e-10:
        q = (D - B) / denom_row
        q = max(0, min(1, q))
    else:
        q = 0.5
    
    # Column player: makes row player indifferent
    # p = (d - b) / (a - b - c + d)
    denom_col = a - b - c + d
    if abs(denom_col) > 1e-10:
        p = (d - b) / denom_col
        p = max(0, min(1, p))
    else:
        p = 0.5
    
    return [p, 1-p], [q, 1-q]


class SelfPlay:
    """
    Self-play training: Agent improves by playing against itself.
    Used in: AlphaGo, AlphaZero
    """
    def __init__(self, policy: Callable[[Any], Any]):
        self.policy = policy
        self.history: List[Tuple[Any, Any, float]] = []  # (state, action, outcome)
    
    def play_game(self, initial_state: Any,
                  transition: Callable[[Any, Any], Any],
                  terminal: Callable[[Any], Tuple[bool, float]]) -> float:
        """
        Play a game against self.
        Returns final outcome.
        """
        state = initial_state
        game_history = []
        
        while True:
            is_done, outcome = terminal(state)
            if is_done:
                # Record all positions with outcome
                for s, a in game_history:
                    self.history.append((s, a, outcome))
                return outcome
            
            action = self.policy(state)
            game_history.append((state, action))
            state = transition(state, action)
    
    def get_training_data(self, n: int = 100) -> List[Tuple[Any, Any, float]]:
        """Get recent training data from self-play"""
        return self.history[-n:]


# =============================================================================
# 9. PLANNING - Search for Solutions
# =============================================================================

def a_star(start: Any, goal_test: Callable[[Any], bool],
           successors: Callable[[Any], List[Tuple[Any, float]]],
           heuristic: Callable[[Any], float]) -> Optional[List[Any]]:
    """
    A* Search: Optimal admissible heuristic search.
    f(n) = g(n) + h(n)
    """
    frontier = [(heuristic(start), 0, start, [start])]
    explored = set()
    
    while frontier:
        f, g, state, path = heapq.heappop(frontier)
        
        if goal_test(state):
            return path
        
        if state in explored:
            continue
        explored.add(state)
        
        for next_state, cost in successors(state):
            if next_state not in explored:
                new_g = g + cost
                new_f = new_g + heuristic(next_state)
                heapq.heappush(frontier, (new_f, new_g, next_state, path + [next_state]))
    
    return None


class MCTS:
    """
    Monte Carlo Tree Search: Planning through simulation.
    Used in: AlphaGo, game AI, complex planning
    """
    def __init__(self, exploration: float = 1.414):
        self.Q: Dict[Tuple, float] = {}  # Total value
        self.N: Dict[Tuple, int] = {}    # Visit counts
        self.children: Dict[Any, List] = {}
        self.exploration = exploration
    
    def search(self, state: Any, 
               get_actions: Callable[[Any], List],
               simulate: Callable[[Any, Any], Tuple[Any, float, bool]],
               n_simulations: int = 100) -> Any:
        """
        Run MCTS and return best action.
        """
        for _ in range(n_simulations):
            self._simulate(state, get_actions, simulate)
        
        # Return most visited action
        actions = get_actions(state)
        return max(actions, key=lambda a: self.N.get((state, a), 0))
    
    def _simulate(self, state: Any,
                  get_actions: Callable[[Any], List],
                  step: Callable[[Any, Any], Tuple[Any, float, bool]]) -> float:
        """Single MCTS simulation (selection, expansion, rollout, backup)"""
        
        # Selection: UCB until unexplored
        path = []
        current = state
        total_reward = 0
        
        while True:
            actions = get_actions(current)
            if not actions:
                break
            
            # Check for unexplored
            unexplored = [a for a in actions if (current, a) not in self.N]
            
            if unexplored:
                # Expansion
                action = random.choice(unexplored)
                path.append((current, action))
                next_state, reward, done = step(current, action)
                total_reward += reward
                
                # Initialize
                self.Q[(current, action)] = 0
                self.N[(current, action)] = 0
                
                # Rollout (random play)
                rollout_reward = self._rollout(next_state, get_actions, step)
                total_reward += rollout_reward
                break
            else:
                # UCB selection
                action = self._ucb_select(current, actions)
                path.append((current, action))
                next_state, reward, done = step(current, action)
                total_reward += reward
                current = next_state
                
                if done:
                    break
        
        # Backup
        for s, a in path:
            self.N[(s, a)] = self.N.get((s, a), 0) + 1
            self.Q[(s, a)] = self.Q.get((s, a), 0) + total_reward
        
        return total_reward
    
    def _ucb_select(self, state: Any, actions: List) -> Any:
        """Select action by UCB"""
        total_n = sum(self.N.get((state, a), 1) for a in actions)
        
        def ucb(action):
            n = self.N.get((state, action), 1)
            q = self.Q.get((state, action), 0) / n
            return q + self.exploration * math.sqrt(math.log(total_n) / n)
        
        return max(actions, key=ucb)
    
    def _rollout(self, state: Any,
                 get_actions: Callable[[Any], List],
                 step: Callable[[Any, Any], Tuple[Any, float, bool]],
                 max_steps: int = 50) -> float:
        """Random rollout from state"""
        total = 0
        current = state
        
        for _ in range(max_steps):
            actions = get_actions(current)
            if not actions:
                break
            
            action = random.choice(actions)
            next_state, reward, done = step(current, action)
            total += reward
            current = next_state
            
            if done:
                break
        
        return total


# =============================================================================
# 10. UNIVERSAL AGENT INTERFACE
# =============================================================================

class UniversalAgent(ABC):
    """
    Abstract base class defining the universal agent interface.
    All intelligent agents share these fundamental operations.
    """
    
    @abstractmethod
    def perceive(self, observation: Any) -> None:
        """Process incoming observation"""
        pass
    
    @abstractmethod
    def decide(self, options: List[Any]) -> Any:
        """Select action from options"""
        pass
    
    @abstractmethod
    def learn(self, feedback: float) -> None:
        """Update from feedback/reward"""
        pass
    
    @abstractmethod
    def predict(self, query: Any) -> Any:
        """Make prediction"""
        pass
    
    def act(self, state: Any, get_actions: Callable[[Any], List[Any]],
            step: Callable[[Any, Any], Tuple[Any, float, bool]]) -> Tuple[Any, float]:
        """
        Full agent cycle: perceive -> decide -> act -> learn
        """
        self.perceive(state)
        actions = get_actions(state)
        action = self.decide(actions)
        next_state, reward, done = step(state, action)
        self.learn(reward)
        return next_state, reward


class CompositeAgent(UniversalAgent):
    """
    An agent composed of multiple universal components.
    Demonstrates how the primitives compose into full agents.
    """
    
    def __init__(self, 
                 state_dim: int = 10,
                 memory_size: int = 1000,
                 exploration: float = 0.1):
        
        # Core components
        self.memory = ExperienceReplay(memory_size)
        self.predictor = PredictiveCoder(levels=3)
        self.abstractor = StateAbstractor()
        self.hebbian = HebbianNetwork(state_dim)
        self.mcts = MCTS()
        
        # Learning state
        self.Q: Dict[Tuple, float] = {}
        self.exploration = exploration
        self.last_state = None
        self.last_action = None
        self.observation_history: List[Any] = []
    
    def perceive(self, observation: Any) -> None:
        """Process observation through multiple pathways"""
        self.observation_history.append(observation)
        
        # Predictive coding: compute surprise
        self.predictor.observe(0, observation)
        
        # State abstraction
        if isinstance(observation, dict):
            features = {k: float(v) for k, v in observation.items() 
                       if isinstance(v, (int, float))}
            self.abstractor.abstract(observation, features)
    
    def decide(self, options: List[Any]) -> Any:
        """Select action using exploration strategy"""
        if not options:
            return None
        
        # Get Q-values for options
        q_values = {a: self.Q.get((self.last_state, a), 0) for a in options}
        
        # Epsilon-greedy with Boltzmann tiebreaking
        if random.random() < self.exploration:
            return random.choice(options)
        
        return boltzmann_select(q_values, temperature=0.5)
    
    def learn(self, feedback: float) -> None:
        """Update from feedback"""
        if self.last_state is not None and self.last_action is not None:
            # Q-learning update
            current_obs = self.observation_history[-1] if self.observation_history else None
            q_learning_update(
                self.Q, 
                self.last_state, 
                self.last_action, 
                feedback,
                current_obs,
                alpha=0.1
            )
            
            # Store experience
            self.memory.store(
                self.last_state, 
                self.last_action, 
                feedback, 
                current_obs, 
                done=False
            )
    
    def predict(self, query: Any) -> Any:
        """Predict using predictive coding + associations"""
        # Use predictive coder
        prediction = self.predictor.predict_next(0, self.observation_history[-5:])
        return prediction.value


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("UNIVERSAL AGENT CORE - Algorithmic Foundations")
    print("=" * 60)
    
    # Demo 1: Value Iteration
    print("\n--- Value Iteration ---")
    # Simple grid world
    states = {(i, j) for i in range(3) for j in range(3)}
    actions = {'up', 'down', 'left', 'right'}
    
    def transition(s, a):
        i, j = s
        if a == 'up': new_s = (max(0, i-1), j)
        elif a == 'down': new_s = (min(2, i+1), j)
        elif a == 'left': new_s = (i, max(0, j-1))
        elif a == 'right': new_s = (i, min(2, j+1))
        else: new_s = s
        return {new_s: 1.0}
    
    def reward(s, a, s_next):
        return 10 if s_next == (2, 2) else -0.1
    
    mdp = MDP(states, actions, transition, reward, gamma=0.9)
    V = value_iteration(mdp)
    
    print("Grid world values (goal at (2,2)):")
    for i in range(3):
        row = [f"{V.get((i,j), 0):.1f}" for j in range(3)]
        print(f"  {row}")
    
    # Demo 2: UCB Selection
    print("\n--- UCB Exploration/Exploitation ---")
    values = {'A': 0.5, 'B': 0.7, 'C': 0.3}
    counts = {'A': 10, 'B': 5, 'C': 1}
    for _ in range(5):
        selected = ucb_select(values, counts, sum(counts.values()))
        print(f"  Selected: {selected}")
        counts[selected] = counts.get(selected, 0) + 1
    
    # Demo 3: Attention
    print("\n--- Attention Mechanism ---")
    query = [1.0, 0.5, 0.0]
    keys = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    values_list = ["red", "green", "blue"]
    result, weights = attend(query, keys, values_list)
    print(f"  Query: {query}")
    print(f"  Weights: {[f'{w:.2f}' for w in weights]}")
    print(f"  Attended: {result}")
    
    # Demo 4: Predictive Coding
    print("\n--- Predictive Coding ---")
    coder = PredictiveCoder()
    sequence = [1, 2, 3, 4, 5]
    for val in sequence:
        coder.predict(0, val, confidence=0.7)
        error = coder.observe(0, val)
        print(f"  Observed {val}, Error: {error:.3f}")
    
    prediction = coder.predict_next(0, sequence)
    print(f"  Next prediction: {prediction.value:.1f} (confidence: {prediction.confidence:.2f})")
    
    # Demo 5: Hebbian Learning
    print("\n--- Hebbian Associative Learning ---")
    net = HebbianNetwork(5)
    # Learn pattern
    pattern = [1.0, 0.0, 1.0, 0.0, 1.0]
    for _ in range(10):
        net.learn(pattern)
    
    # Recall from partial
    partial = [1.0, 0.0, 0.0, 0.0, 0.0]
    recalled = net.recall(partial)
    print(f"  Original:  {pattern}")
    print(f"  Partial:   {partial}")
    print(f"  Recalled:  {[f'{r:.2f}' for r in recalled]}")
    
    # Demo 6: Nash Equilibrium
    print("\n--- Nash Equilibrium (Matching Pennies) ---")
    # Matching pennies: zero-sum game
    payoffs = [
        [( 1, -1), (-1,  1)],  # H vs H, H vs T
        [(-1,  1), ( 1, -1)]   # T vs H, T vs T
    ]
    p1_strategy, p2_strategy = nash_equilibrium_2x2(payoffs)
    print(f"  Player 1 (row): {[f'{p:.2f}' for p in p1_strategy]}")
    print(f"  Player 2 (col): {[f'{p:.2f}' for p in p2_strategy]}")
    
    # Demo 7: A* Search
    print("\n--- A* Search ---")
    goal = (2, 2)
    
    def successors(s):
        i, j = s
        moves = []
        for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < 3 and 0 <= nj < 3:
                moves.append(((ni, nj), 1.0))
        return moves
    
    def heuristic(s):
        return abs(s[0] - goal[0]) + abs(s[1] - goal[1])
    
    path = a_star((0, 0), lambda s: s == goal, successors, heuristic)
    print(f"  Path from (0,0) to (2,2): {path}")
    
    print("\n" + "=" * 60)
    print("All universal agent components demonstrated!")
    print("=" * 60)
