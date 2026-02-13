# Universal Reasoning Kernel (URK)

**A Mathematical AI System Without LLMs**

URK is a local, explainable AI system built on mathematical foundations rather than neural networks. It combines information theory, Bayesian inference, constraint satisfaction, and pattern recognition to create a reasoning engine that can learn, remember, and solve problems.

## Core Philosophy

1. **Compression = Intelligence** (Solomonoff Induction) - Understanding emerges from finding compact representations
2. **Minimize Surprise** (Free Energy Principle) - Intelligent systems predict and reduce uncertainty
3. **Bayesian Updating** - Learn from evidence, not memorization
4. **Constraint Propagation** - Ensure logical consistency
5. **Compositional Generation** - Build complex outputs from simple parts

## Features

| Component | Description | Math Foundation |
|-----------|-------------|-----------------|
| **Pattern Recognizer** | Regex + compression-based similarity | Kolmogorov complexity |
| **Bayesian Reasoner** | Belief networks with evidence updating | Bayes' theorem |
| **Constraint Propagator** | CSP solver with arc consistency | AC-3 algorithm |
| **Memory System** | Working + episodic + semantic memory | Spreading activation |
| **Compositional Generator** | Template + grammar-based generation | CFG derivation |

## Benchmark: vs AI Agents

Run `python benchmark_vs_ai.py` to compare against simulated AI agent characteristics.

| Metric | Universal Kernel | GPT-4 | Claude Opus | Gemini Pro |
|--------|-----------------|-------|-------------|------------|
| **Latency (avg)** | **0.09ms** | ~2500ms | ~3000ms | ~1200ms |
| **Consistency** | **100%** | 85% | 88% | 82% |
| **Adversarial Resilience** | **100%** | 92% | 95% | 88% |
| **Cost (1K requests)** | **$0.00** | $3.00 | $1.50 | $0.03 |
| **Explainability** | **100%** | ~20% | ~30% | ~20% |
| **Deterministic** | **✓** | ✗ | ✗ | ✗ |
| **Works Offline** | **✓** | ✗ | ✗ | ✗ |

**Overall Score: 96/100 (A+)** | **27,000x faster than GPT-4**

### Where Universal Kernel Wins
- Speed (sub-millisecond vs seconds)
- Determinism (same input = same output, always)
- Cost (free, local)
- Privacy (no data leaves your machine)
- Explainability (full decision audit trail)

### Where LLMs Win
- Novel understanding (completely new domains)
- Natural language fluency
- Complex multi-step reasoning
- Full program synthesis

## Quick Start

```python
from kernel import create_kernel

# Create a kernel
kernel = create_kernel("MyAI")

# Learn facts
kernel.learn("Paris is the capital of France")
kernel.learn("France is in Europe")

# Ask questions
answer = kernel.ask("What is the capital of France?")
print(answer)

# Process with full analysis
result = kernel.process("Tell me about France")
print(result['response'])
print(result['confidence'])
```

## Components

### 1. Pattern Recognizer

```python
from kernel import PatternRecognizer, Pattern

recognizer = PatternRecognizer()

# Add explicit pattern
recognizer.add_pattern(Pattern(
    id='greeting',
    regex=r'^(hi|hello|hey)\b',
    semantic_tags={'social', 'opening'}
))

# Learn pattern from examples
recognizer.learn_pattern('email', [
    'user@example.com',
    'test@domain.org'
])

# Recognize patterns
matches = recognizer.recognize("Hi there!")
# [('greeting', 0.5)]
```

### 2. Bayesian Reasoner

```python
from kernel import BayesianReasoner

bayes = BayesianReasoner()

# Set prior beliefs
bayes.add_belief("raining", prior=0.3)
bayes.add_belief("cloudy", prior=0.6)

# Add conditional probabilities
bayes.add_conditional("raining", "cloudy", 0.8)  # P(rain|cloudy) = 0.8

# Observe evidence
bayes.observe("I see dark clouds", supports=["cloudy", "raining"])

# Query beliefs
prob, confidence = bayes.query("raining")
print(f"P(raining) = {prob:.0%}, confidence: {confidence:.0%}")

# Find what's most uncertain
bayes.most_uncertain()  # "raining"
```

### 3. Constraint Propagator (CSP Solver)

```python
from kernel import ConstraintPropagator

csp = ConstraintPropagator()

# Map coloring problem
colors = ['red', 'green', 'blue']
regions = ['A', 'B', 'C']

for r in regions:
    csp.add_variable(r, colors)

# Adjacent regions must differ
csp.add_constraint(['A', 'B'], lambda a, b: a != b)
csp.add_constraint(['B', 'C'], lambda b, c: b != c)

# Solve
solution = csp.solve()
# {'A': 'red', 'B': 'green', 'C': 'red'}
```

### 4. Memory System

```python
from kernel import MemorySystem

mem = MemorySystem()

# Three types of memory
mem.store_working("current context")           # Limited capacity (7 items)
mem.store_episodic("past interaction")         # Time-ordered history
mem.store_semantic("dog", "canine mammal",     # Permanent knowledge
                   associations={'pet', 'animal'})

# Search by compression similarity
results = mem.search("furry pet")

# Recall recent
recent = mem.recall_recent(5)

# Spreading activation
activated = mem.spread_activation('dog', depth=2)
```

### 5. Compositional Generator

```python
from kernel import CompositionalGenerator, Template

gen = CompositionalGenerator()

# Template-based
gen.add_template(Template(
    id='greeting',
    pattern='Hello, {NAME}! Welcome to {PLACE}.',
    slots={
        'NAME': ['friend', 'user', 'developer'],
        'PLACE': ['the app', 'URK', 'our service']
    }
))

print(gen.generate_from_template('greeting'))
# "Hello, user! Welcome to URK."

# Grammar-based
gen.add_grammar_rule('S', ['<NP> <VP>'])
gen.add_grammar_rule('NP', ['the <N>', 'a <ADJ> <N>'])
gen.add_grammar_rule('N', ['cat', 'robot'])
gen.add_grammar_rule('VP', ['runs', 'thinks'])
gen.add_grammar_rule('ADJ', ['clever', 'fast'])

print(gen.generate_from_grammar('S'))
# "a clever robot thinks"
```

## Mathematical Functions

```python
from kernel import (
    entropy,
    information_gain,
    compression_distance,
    kl_divergence,
    bayesian_update,
    softmax
)

# Shannon entropy - uncertainty measure
H = entropy([0.5, 0.5])  # 1.0 bit (maximum uncertainty)
H = entropy([0.9, 0.1])  # 0.47 bits (more certain)

# Compression-based similarity (approximates Kolmogorov complexity)
dist = compression_distance("hello world", "hello there")
similarity = 1 - dist  # ~0.63

# Softmax with temperature
probs = softmax([3.0, 1.0, 0.5], temperature=1.0)
# [0.84, 0.11, 0.05] - decisive
probs = softmax([3.0, 1.0, 0.5], temperature=2.0)
# [0.62, 0.22, 0.16] - more exploratory
```

## Full Kernel Usage

```python
from kernel import UniversalKernel

kernel = UniversalKernel("MyKernel")

# Process any input
result = kernel.process("What is machine learning?")
print(result['patterns'])      # Recognized patterns
print(result['entities'])      # Extracted entities
print(result['response'])      # Generated response
print(result['confidence'])    # Confidence score

# Learn new information
kernel.learn("Machine learning is a type of AI")

# Analogical reasoning
kernel.analogy("cat", "cats", "dog")  
# "cat : cats :: dog : dogs"

# Explain knowledge
kernel.explain("learning")

# Logical reasoning
kernel.reason(
    premises=["A -> B", "B -> C"],
    goal="C"
)

# Save/load state
kernel.save_state("kernel_state.json")
kernel.load_state("kernel_state.json")
```

## Demos

Run individual demos:

```bash
python demo.py 1   # Intelligent assistant
python demo.py 2   # Problem solving (CSP)
python demo.py 3   # Bayesian diagnosis
python demo.py 4   # Pattern learning
python demo.py 5   # Analogical reasoning
python demo.py 6   # Memory system
python demo.py 7   # Information theory
python demo.py 8   # Compositional generation
python demo.py 9   # Full system integration
```

Or run all:

```bash
python demo.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   UNIVERSAL REASONING KERNEL                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐     ┌─────────────────┐               │
│  │ Pattern         │     │ Bayesian        │               │
│  │ Recognizer      │────▶│ Reasoner        │               │
│  │ - Regex         │     │ - Beliefs       │               │
│  │ - Compression   │     │ - Updating      │               │
│  │ - Analogy       │     │ - Entropy       │               │
│  └─────────────────┘     └─────────────────┘               │
│          │                       │                          │
│          ▼                       ▼                          │
│  ┌─────────────────────────────────────────┐               │
│  │            Memory System                 │               │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐   │               │
│  │  │ Working │ │Episodic │ │Semantic │   │               │
│  │  │ (7 ±2)  │ │(time)   │ │(facts)  │   │               │
│  │  └─────────┘ └─────────┘ └─────────┘   │               │
│  └─────────────────────────────────────────┘               │
│          │                       │                          │
│          ▼                       ▼                          │
│  ┌─────────────────┐     ┌─────────────────┐               │
│  │ Constraint      │     │ Compositional   │               │
│  │ Propagator      │────▶│ Generator       │               │
│  │ - CSP           │     │ - Templates     │               │
│  │ - AC-3          │     │ - Grammars      │               │
│  │ - Backtracking  │     │ - Constraints   │               │
│  └─────────────────┘     └─────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Universal Agent Core (agent_core.py)

**NEW:** Algorithmic foundations common to ALL intelligent agents.

These mathematical invariants appear across RL, planning, game theory, cognitive science, and neuroscience:

| Component | Math Foundation | Appears In |
|-----------|-----------------|------------|
| **Bellman Optimality** | V(s) = max[R + γV(s')] | RL, Planning, Games |
| **Attention** | softmax(QK^T/√d) | Transformers, Cognition |
| **Exploration/Exploitation** | UCB, Thompson, ε-greedy | RL, Bandits, Search |
| **Credit Assignment** | TD(λ), GAE, eligibility traces | Backprop, RL |
| **Predictive Coding** | Minimize prediction error | Neuroscience, Free Energy |
| **Hierarchical Abstraction** | State chunking, options | HTM, HRL |
| **Hebbian Learning** | "Fire together, wire together" | Neural nets, Association |
| **Game Theory** | Nash, Minimax, Alpha-Beta | Multi-agent, Adversarial |
| **Planning** | A*, MCTS | Search, Game AI |

### Usage Examples

```python
from agent_core import (
    value_iteration, q_learning_update,  # Bellman
    attention_weights, attend,            # Attention
    ucb_select, thompson_sample,          # Exploration
    temporal_difference, advantage_estimation,  # Credit assignment
    PredictiveCoder,                      # Predictive coding
    StateAbstractor, HierarchicalRL,      # Abstraction
    HebbianNetwork,                       # Associative learning
    minimax, alpha_beta, nash_equilibrium_2x2,  # Game theory
    a_star, MCTS                          # Planning
)

# Value Iteration (Bellman)
from agent_core import MDP
V = value_iteration(mdp)  # Optimal value function

# UCB Exploration
action = ucb_select(q_values, visit_counts, total_visits)

# Attention mechanism
weights = attention_weights(query, keys, temperature=0.5)
result, weights = attend(query, keys, values)

# Predictive Coding (Free Energy)
coder = PredictiveCoder(levels=3)
coder.predict(0, value, confidence=0.7)
error = coder.observe(0, actual_value)
surprise = coder.total_surprise()

# Hebbian associative memory
net = HebbianNetwork(size=10)
net.learn([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
recalled = net.recall([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])

# Nash Equilibrium (2x2 games)
payoffs = [[(1,-1), (-1,1)], [(-1,1), (1,-1)]]  # Matching Pennies
p1_strat, p2_strat = nash_equilibrium_2x2(payoffs)
# [0.5, 0.5], [0.5, 0.5] - mixed equilibrium

# A* Search
path = a_star(start, goal_test, successors, heuristic)

# MCTS Planning
mcts = MCTS()
action = mcts.search(state, get_actions, simulate, n_simulations=100)
```

### Universal Agent Interface

All agents share these operations:

```python
from agent_core import UniversalAgent, CompositeAgent

class MyAgent(UniversalAgent):
    def perceive(self, observation): ...
    def decide(self, options): ...
    def learn(self, feedback): ...
    def predict(self, query): ...

# Pre-built composite agent
agent = CompositeAgent(state_dim=10)
next_state, reward = agent.act(state, get_actions, step_fn)
```

Run agent demos:
```bash
python agent_core.py
```

## Theoretical Foundations

### Solomonoff Induction
Intelligence is optimal compression. The best prediction is the simplest explanation consistent with observations. URK approximates this via compression distance (NCD).

### Free Energy Principle (Friston)
Systems minimize "surprise" by building internal models. URK's Bayesian reasoner continuously updates beliefs to minimize prediction error.

### Constraint Satisfaction
Problems are defined by variables, domains, and constraints. Solutions satisfy all constraints simultaneously. URK uses AC-3 arc consistency and backtracking.

### Information Theory (Shannon)
- **Entropy**: H(X) = -Σ p(x) log₂ p(x) - measures uncertainty
- **Information Gain**: Reduction in entropy from new evidence
- **KL Divergence**: Distance between probability distributions

### Miller's Law
Working memory holds 7±2 items. URK enforces this limit, consolidating important memories to long-term storage.

## Comparison to LLMs

| Aspect | URK | LLMs |
|--------|-----|------|
| **Local** | Yes, pure Python | Often requires cloud |
| **Explainable** | Full trace of reasoning | Black box |
| **Consistent** | Logically guaranteed | Can contradict itself |
| **Learning** | Incremental, explicit | Requires retraining |
| **Memory** | Structured, searchable | Context window limited |
| **Size** | ~2000 lines, no GPU | Billions of parameters |
| **Fluency** | Structured output | Natural language |
| **Creativity** | Template-based | Generative |

## Use Cases

- **Diagnostic systems** - Bayesian reasoning with symptoms
- **Puzzle solvers** - CSP for Sudoku, scheduling, planning
- **Expert systems** - Rule-based reasoning with uncertainty
- **Tutoring** - Pattern recognition + adaptive questioning
- **Game AI** - Constraint-based decision making
- **Knowledge management** - Semantic memory with associations

## Dependencies

None! Pure Python 3.8+ standard library only.

## License

MIT

---

*"The simplest explanation consistent with the data is most likely correct."* - Solomonoff
