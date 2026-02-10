# The Constraint-First Manifesto

## Incommensurability: Why These Paradigms Cannot Be Compared

---

### The AI Paradigm Says:

> "Give me a prompt, I'll generate code."

This is **probabilistic scaffolding**:
- Statistical inference over training data
- Token prediction until EOS
- Confidence scores, not guarantees
- Works most of the time

### The Constraint-First Paradigm Says:

> "Give me requirements, I'll prove a solution."

This is **verified composition**:
- Logical deduction from constraints
- Block assembly with satisfied dependencies
- Full derivation trace
- Works all of the time, or fails to compile

---

## What AI Scaffolders Cannot Do

The following are **structurally impossible** in the AI paradigm, not merely difficult:

### 1. Deterministic Output

**AI**: Uses temperature, sampling, context windows. Same prompt → different outputs.

**CFD**: Pure mathematical function. Same constraints → identical output, forever.

```python
# Run this 1000 times with AI - you'll get variations
# Run this 1000 times with CFD - identical output every time

from constraint_solver import ConstraintSolver
solver = ConstraintSolver()
solver.add_constraint('offline', True)
result = solver.solve()  # Same. Every. Time.
```

**Why AI can't do this**: Transformers are inherently stochastic. Even with temperature=0, floating point and attention mechanisms introduce variation.

---

### 2. Provable Correctness

**AI**: Can generate "seems right" code. Cannot prove it satisfies constraints.

**CFD**: CSP solver proves constraint satisfaction before generating anything.

```python
from csp_constraint_solver import ArchitectureCSP

csp = ArchitectureCSP()
csp.add_block("crdt_sync")

# AI would generate code for this
# CFD blocks it: "crdt_sync requires backend"

result = csp.validate()
assert result['valid'] == False  # Invalid state blocked
```

**Why AI can't do this**: LLMs don't have formal verification. They approximate. A correct-looking config can still be broken.

---

### 3. Complete Explainability

**AI**: 175 billion parameters. Cannot explain why it chose X over Y.

**CFD**: Full derivation trace. Every decision has a documented reason.

```
Derivation trace:
  1. offline=True [user input]
  2. needs_local_storage=True [rule: offline → local_storage]
  3. multi_user=True [user input]
  4. needs_sync=True [rule: offline ∧ multi_user → sync]
  5. crdt_sync=True [rule: offline ∧ sync → crdt]
  ...
```

**Why AI can't do this**: Neural networks are inherently opaque. "Attention maps" and "feature attribution" are approximations, not true explanations.

---

### 4. Offline Independence

**AI**: Requires API calls, model weights, internet connection, subscriptions.

**CFD**: Pure Python. Works on an air-gapped machine forever.

```powershell
# Disconnect from internet
# AI scaffolders: ❌ Connection refused

# CFD:
python blueprint.py prove  # ✅ Works perfectly
```

**Why AI can't do this**: The model is the product. It lives on servers. Local models require GB of downloads and GPU.

---

### 5. Guaranteed Spec-Code Consistency

**AI**: Generates spec (docs) and code (impl) separately. They can disagree.

**CFD**: Contracts are both spec and code. Disagreement is structurally impossible.

```python
# This Contract generates Python, TypeScript, Markdown, Routes
# They cannot disagree because they ARE the same thing

Contract(
    name='Task',
    fields=[Field('title', 'string'), Field('done', 'boolean')]
)
# → Python validates title is string
# → TypeScript types title as string  
# → Markdown documents title as string
# → Routes enforce title is string
```

**Why AI can't do this**: AI generates text sequentially. The second generation doesn't "know" the first. Bidirectionality requires formal structure.

---

### 6. Proven Security Properties

**AI**: Can add auth, might forget edge cases, can hallucinate security patterns.

**CFD**: Security blocks have declared requirements. Missing requirements = compile failure.

```python
# If you want auth, you MUST have storage
# This is not a suggestion, it's a requirement

Block(
    id='auth_basic',
    requires=['storage'],  # Enforced
    provides=['auth']
)

# Try to add auth without storage → blocked
```

**Why AI can't do this**: LLMs don't have formal security analysis. They pattern-match from training data, which included insecure code.

---

## The Incommensurability

These paradigms are **not competing for the same use cases**.

| Question | AI Answer | CFD Answer |
|----------|-----------|------------|
| "How do I scaffold?" | Generate probabilistically | Derive logically |
| "Is this valid?" | Probably | Provably |
| "Why this choice?" | ¯\_(ツ)_/¯ | See derivation |
| "Will it work offline?" | Need API | Always |
| "Same output twice?" | Unlikely | Guaranteed |

You cannot ask "which is better?" because they optimize for different things:
- AI optimizes for **flexibility** (generate anything)
- CFD optimizes for **guarantees** (generate only valid things)

---

## When to Choose Each

### Use AI When:
- Exploring possibilities
- Generating natural language
- One-off creative tasks
- Flexibility > Correctness

### Use Constraint-First When:
- Determinism required
- Audit trail needed
- Working offline
- Correctness > Flexibility
- Configuration must be valid by construction

---

## The Paradigm Shift

Thomas Kuhn described paradigm shifts as:

1. **Normal science** operates within accepted framework
2. **Anomalies** accumulate that the framework can't explain
3. **Crisis** emerges when anomalies become severe
4. **New paradigm** offers different fundamental approach
5. **Incommensurability** - new and old can't be compared

We are at stage 4-5 for scaffolding:

- **Old paradigm**: AI generates code probabilistically
- **Anomalies**: Non-determinism, unexplainability, dependency, invalidity
- **New paradigm**: Constraints derive code deterministically
- **Incommensurability**: They solve different problems differently

---

## The Choice

You can continue with probabilistic scaffolding. It works most of the time.

Or you can switch to verified scaffolding. It works all of the time, or tells you exactly why not.

**The paradigm that proves, rather than guesses.**

```powershell
python blueprint.py prove
```
