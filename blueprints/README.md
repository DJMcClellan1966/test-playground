# Blueprint: Constraint-First Development

> **"What AI guesses, we prove."**

---

## The Paradigm

**Constraint-First Development** is a fundamentally different approach to software scaffolding:

| AI Paradigm | Constraint-First Paradigm |
|-------------|---------------------------|
| Probabilistic output | **Deterministic output** |
| Opaque reasoning | **Explainable derivation** |
| Requires external services | **100% offline** |
| Can generate invalid configs | **Invalid states are impossible** |
| Variable results | **Same input → same result, always** |

This is not an incremental improvement. It's a different answer to "How should software be scaffolded?"

**Mathematically proven**: See [PROOF_CONFLUENCE.md](PROOF_CONFLUENCE.md) for the formal proof that rule order doesn't affect output (confluence property).

---

## 🔬 THE DEMO: 30 Seconds to Proof

Run this now:

```powershell
python blueprint.py prove
```

You will see 4 guarantees that **no AI scaffolder can provide**:

1. **Deterministic Output** - Same requirements, same result, 3 times in a row
2. **Provable Correctness** - Invalid configurations are blocked, not generated
3. **Explainable Reasoning** - Full derivation trace for every decision
4. **Zero AI Dependency** - No API, no model, no internet required

**This single demo is the paradigm.** Everything else follows from these guarantees.

---

## Quick Start

```powershell
# Interactive mode
python blueprint.py

# Natural language → verified project
python blueprint.py create "todo app with offline sync"

# Run the proof demo
python blueprint.py prove

# Start learning journey
python blueprint.py learn
```

---

## 🧠 The Core System

Three components achieve LLM-like results through formal methods:

### 1. Constraint Solver (`constraint_solver.py`)
Logical deduction engine with 15+ architectural rules. Your requirements → derived architecture.

```powershell
python constraint_solver.py --offline --multi-user --explain
```

**Example**: "needs offline" + "multi-user" → automatically deduces CRDT sync, conflict resolution, auth backend

### 1b. CSP Constraint Solver (`csp_constraint_solver.py`) ⚡ NEW

**Formal constraint satisfaction** that goes from "clever advisor" to "essential validator" — inspired by Rust's borrow checker:

```powershell
python csp_constraint_solver.py --demo  # See constraint validation in action
python csp_constraint_solver.py --offline --multi-user --blocks crdt_sync
```

**Key Differences from Rule-Based Solver:**

| Aspect | Old Solver | CSP Solver |
|--------|------------|------------|
| **Mode** | Advisory (suggests) | Essential (blocks invalid states) |
| **Conflicts** | Ignores | Detects & explains |
| **Missing deps** | Hints | Proves what's required |
| **Foundation** | Hand-coded rules | Formal CSP with backtracking |

**Example: Invalid Configuration Detection**
```python
from csp_constraint_solver import ArchitectureCSP

solver = ArchitectureCSP()
solver.add_block("crdt_sync")  # Requires backend + storage
result = solver.validate()
# result.valid = False
# result.conflict.explanation = "Block 'crdt_sync' requires: storage, backend"
# result.conflict.suggestions = ["Add backend_flask or backend_fastapi"]
```

**Example: Auto-Solve Dependencies**
```python
solver = ArchitectureCSP()
solver.set_requirement("offline", True)
solver.set_requirement("multi_user", True)
result = solver.solve()
# Automatically adds: auth_basic, backend_fastapi, storage_sqlite, crdt_sync
# With full derivation trace explaining WHY each was added
```

### 2. Compositional Blocks (`blocks.py`)
Code LEGOs that declare what they `require` and `provide`. Blocks auto-assemble based on constraints.

```powershell
python blocks.py --list              # See all blocks
python blocks.py --auth --offline    # Assemble matching blocks
```

**14 Blocks Available**:
| Category | Blocks |
|----------|--------|
| Storage | JSON, SQLite, PostgreSQL, **S3 Files** |
| Backend | Flask, FastAPI |
| Auth | Basic Auth, **OAuth (Google/GitHub)** |
| Sync | CRDT Sync |
| Real-time | WebSocket |
| Deployment | Docker |
| API | CRUD Routes |
| Email | **SendGrid** |
| Cache | **Redis** |

### 3. Bidirectional Contracts (`contracts.py`)
**The life-changing part**: Spec and code are THE SAME THING. Define once, generate:
- Python dataclasses with validation
- Flask routes with contract enforcement
- TypeScript interfaces with schemas
- Human-readable Markdown specs

```powershell
python contracts.py --demo      # See all 4 views from one contract
python contracts.py --generate  # Generate all files
```

### Unified Pipeline (`intelligent_scaffold.py`)

```powershell
python intelligent_scaffold.py --demo
```

Takes natural requirements → constraint solving → block selection → contract generation → working code.

**Demo output**: From 4 requirements ("needs multiple users", "offline", "auth", "sync") → generates 19 files including models, routes, types, and specs.

---

## 📚 Learning System - Beginner-Friendly Progression

A **level-based learning system** (`learning_integration.py`) that helps beginners grow with the platform:

```powershell
python learning_integration.py  # Run demo
```

### Why a Learning System?

| Problem | Solution |
|---------|----------|
| Beginners overwhelmed by all options | Level-gated blocks - start simple |
| No clear path forward | XP progression + unlock previews |
| Generic scaffolding vs learning | Real working code patterns |
| No reward for progress | XP, level ups, concept tracking |

### Features

1. **Level-Gated Blocks**
   - **Beginner**: JSON Storage, CRUD Routes
   - **Intermediate**: SQLite, Flask Backend, Auth, FastAPI
   - **Advanced**: PostgreSQL ✅, CRDT Sync, WebSocket ✅, Docker ✅, OAuth ✅, Redis ✅, S3 ✅, SendGrid ✅
   - **Expert**: Kubernetes (planned), GraphQL (planned)

2. **Working Code Projects** (18 total - not scaffolds, real apps!)
   
   **Beginner:**
   - Guess the Number (+20 XP) - loops, conditionals
   - Calculator (+15 XP) - functions, operators
   - Todo List (+30 XP) - classes, persistence
   - Tic-Tac-Toe (+35 XP) - 2D arrays, game logic
   - Binary Search (+30 XP) - divide & conquer
   
   **Intermediate:**
   - Flask Todo API (+50 XP) - REST, HTTP
   - Cross-Validation (+40 XP) - ML evaluation
   - LCG Random Generator (+40 XP) - number theory
   - Fisher-Yates Shuffle (+35 XP) - randomization
   - Kadane's Algorithm (+40 XP) - dynamic programming
   - Sliding Puzzle Game (+65 XP) - HTML/CSS/JS, game logic
   - Greedy Algorithms (+35 XP) - optimization patterns
   
   **Advanced:**
   - SQLite CRUD (+45 XP) - SQL, databases
   - Heapsort (+50 XP) - sorting, data structures
   - Backtracking Template (+55 XP) - constraint satisfaction
   - DP Templates (+60 XP) - memoization, tabulation
   - Information Entropy (+45 XP) - Shannon theory
   - Bias-Variance Tradeoff (+50 XP) - ML fundamentals

3. **Adaptive Progression**
   - Track concepts learned
   - Prerequisites before advanced blocks
   - XP thresholds: Beginner(0) → Intermediate(100) → Advanced(300) → Expert(600)

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/learning/status` | POST | Get level, XP, concepts learned |
| `/api/learning/blocks` | POST | Get blocks available at current level |
| `/api/learning/projects` | POST | Get code projects available |
| `/api/learning/get-code` | POST | Get working code for a project (+XP) |
| `/api/learning/use-block` | POST | Record block usage (+XP) |
| `/api/learning/complete` | POST | Mark project complete (+50 XP) |
| `/api/learning/oracle` | POST | Query algorithm oracle for pattern advice |
| `/api/learning/oracle-rules` | POST | Get all available oracle rules |

### Algorithm Oracle (Pattern Advisor)

The learning system includes an **Algorithm Oracle** with 10 rules from classic sources:

| Profile | Pattern | Source |
|---------|---------|--------|
| `text + safety_critical` | Rule-Based + Ensemble | Content moderation |
| `high_dim + few_samples` | Regularized Linear + PCA | Curse of dimensionality |
| `imbalanced` | SMOTE + Class Weights | Classification |
| `streaming` | Online Learning + Sliding Window | Real-time data |
| `nonlinear` | Gradient Boosting → Neural Net | Complex patterns |
| `need_interpretability` | Decision Tree → SHAP | Explainable AI |

```python
# Query the oracle
from learning_integration import get_oracle_advice
advice = get_oracle_advice(['imbalanced', 'binary_classification'])
print(advice['top_recommendation']['pattern'])  # "SMOTE + Class Weights + Threshold Tuning"
```

### Usage in Builder

Open the **Learn** tab in the builder sidebar:
- See your current level and XP progress
- Browse available working code projects (18 total)
- Click a project to view full, runnable code
- Copy or save code to workspace
- Watch concepts unlock and level up!
- Query the Algorithm Oracle for ML/algorithm pattern guidance

---

## 🧠 Logic Advisor - Deterministic Guidance

A **rule-based advisor** that provides instant, explainable recommendations without AI (`logic_advisor.py`):

```powershell
python logic_advisor.py  # Run interactive demo
```

### Why Logic Instead of AI?

| Aspect | AI Advisor | Logic Advisor |
|--------|------------|---------------|
| Speed | Seconds (API call) | Instant |
| Availability | Needs Ollama | Always works |
| Consistency | Variable | Deterministic |
| Explainability | Opaque | Shows reasoning |
| Offline | Requires model | Just Python |

### What It Does

1. **State Analysis**: Examines your blocks and entities → suggests what's missing
2. **Question Answering**: Pattern-matched responses about blocks, patterns, CRDT, etc.
3. **Completeness Score**: 0-100% based on storage, API, auth, entities
4. **Next Steps**: Ordered list of what to do next

### Usage in Builder

Open the **Logic** tab in the builder sidebar:
- See real-time completeness score
- Click suggestions to auto-add blocks
- Ask questions like "What is CRDT?" or "Why do I need storage?"
- No timeouts, no AI dependencies

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/logic/analyze` | POST | Analyze blocks/entities, get suggestions |
| `/api/logic/ask` | POST | Answer questions via pattern matching |
| `/api/csp/validate` | POST | Validate block config against CSP constraints |
| `/api/csp/solve` | POST | Auto-add required blocks to satisfy constraints |

---

## 🌟 Beyond Belief: Revolutionary Features

Push the boundaries of what's possible without AI (`beyond_belief.py`):

### 1. Cross-Language Synthesis
One contract → Python, TypeScript, Go, Rust, Java. Write once, generate everywhere.

```powershell
python beyond_belief.py --cross-lang
```

Same `Task` contract generates:
- Python dataclass with validation
- TypeScript interface with branded types
- Go struct with JSON tags
- Rust struct with serde derives
- Java class with getters/setters

### 2. Refinement Types
Types that encode their own invariants. Invalid values are **impossible to construct**.

```python
# "age: int where >= 0 and <= 150"
age = Age(-5)  # Raises ValueError - can't create invalid age
```

### 3. Program Synthesis from Tests
Give input→output examples, get working code:

```python
# Examples: (1→2), (5→10), (0→0)
# Synthesized: def double(x): return x * 2
```

### 4. Inverse Scaffolding
Point at existing code → extract implicit contracts → regenerate cleanly:

```powershell
python beyond_belief.py --inverse
```

Analyzes Python classes to extract fields, types, and validation invariants.

### 5. Executable Specifications
The spec **IS** the program. Define constraints, execute them directly:

```python
task_spec = (
    ExecutableSpec("Task")
    .field("title", "str where not empty")
    .field("priority", "int where >= 1 and <= 5")
)
task_spec.create(title="Buy groceries", priority=2)  # Works
task_spec.create(title="", priority=6)  # Rejected!
```

### 6. Visual Block Editor
Drag-and-drop architecture builder (`visual_editor.html`):

- Drag blocks from palette to canvas
- Auto-connect based on provides/requires
- Real-time constraint checking
- One-click code generation

Open `visual_editor.html` in a browser to try it!

```powershell
python beyond_belief.py --all  # Run all demos
```

---

## 🔧 Builder Dev Server

A **working development server** that makes the visual editor actually write files (`builder_server.py`):

```powershell
python builder_server.py
# Opens http://localhost:8088 automatically
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/blocks` | GET | List all available compositional blocks |
| `/api/scaffold` | POST | Generate complete project from blocks + entities |
| `/api/create-contract` | POST | Create type-safe contract with multi-language output |
| `/api/save` | POST | Save individual files to workspace |
| `/api/project` | GET | Get current project structure |

### Example: Generate a Project

```python
import requests

response = requests.post('http://localhost:8088/api/scaffold', json={
    'name': 'my_todo_app',
    'blocks': [{'type': 'storage_sqlite'}, {'type': 'crud_routes'}],
    'entities': [{'name': 'Task', 'fields': [
        {'name': 'title', 'type': 'string'},
        {'name': 'done', 'type': 'boolean'}
    ]}]
})
# Creates: app.py, models/task.py, routes/task_routes.py, types/task.ts, etc.
```

### Visual Builder UI

Open `http://localhost:8088` to access the enhanced visual editor with:
- **Blocks tab**: Drag compositional blocks onto canvas
- **Entities tab**: Define data models with fields
- **Files tab**: Browse generated project files
- **Live preview**: See generated code in real-time
- **Generate button**: Write actual files to `workspace/` directory

---

## Available Blueprints

| Blueprint | Description | Complexity |
|-----------|-------------|------------|
| [Learning App](./learning-app.md) | Book/course reader with notes, highlights, spaced repetition | Medium-High |
| [Research & Knowledge Platform](./research-knowledge-platform.md) | Research assistant with semantic search and Socratic refinement | High |
| [Intelligent Tutoring System](./intelligent-tutoring-system.md) | Socratic tutoring with adaptive learning | High |
| [Task Manager](./task-manager.md) | Todo/project management with tags, deadlines, priorities | Medium |
| [Dashboard](./dashboard.md) | Data visualization, metrics, charts, reports | Medium |
| [API Backend](./api-backend.md) | RESTful service with auth, database, CRUD operations | Medium |
| [Personal Website](./personal-website.md) | Portfolio, blog, about page, contact | Low-Medium |
| [Note-Taking App](./notes-app.md) | Rich text notes, folders, search, sync | Medium |

---

## How to Use These Blueprints

### Option A: Intelligent Scaffold (Recommended)

Generate a complete project with logical deduction:

```powershell
cd blueprints
python intelligent_scaffold.py --demo
```

Or specify your own requirements:

```powershell
python intelligent_scaffold.py \
  --requirement "needs offline support" \
  --requirement "multiple users" \
  --entity "Task:title,description,priority" \
  --output my_project
```

### Option B: Template-Based Generation (No AI Required)

Generate working code from pre-built templates:

```powershell
python scaffold.py learning-app --name MyBookTracker --stack flask --generate
```

This creates:
- ✅ Directory structure from the blueprint
- ✅ Model files with actual code (not just stubs)
- ✅ Route handlers with CRUD operations
- ✅ Frontend components (React)
- ✅ Package/requirements file

**Available stacks:** flask, fastapi, react, express

### Option C: Blueprint Advisor (Interactive)

Not sure where to start? Use the keyword-based advisor:

```powershell
python advisor.py
```

Describe your app idea and get recommendations for:
- Which blueprint to start from
- Which features to include
- Suggested tech stack

### Option D: Menu-Driven Builder

Build a blueprint interactively with pre-curated options:

```powershell
python builder.py
```

Choose from:
- **Feature Library**: 50+ common features organized by category
- **Model Library**: Pre-built data models (User, Task, Note, etc.)
- **Screen Library**: Common UI patterns
- **Flow Library**: User journey templates

### Option E: Scaffold Structure Only

Generate project structure without implementation code:

```powershell
python scaffold.py learning-app --name MyBookTracker --stack flask
```

This creates:
- ✅ Directory structure from the blueprint
- ✅ Model files with fields from Data Model section
- ✅ Main app entry point with starter code
- ✅ Package/requirements file
- ✅ README with next steps

```powershell
# List all blueprints
python scaffold.py --list

# Preview without creating files
python scaffold.py task-manager --name QuickTodo --dry-run
```

### Option F: Choose Manually

### Step 1: Pick Your Blueprint
Choose the one closest to what you want to build.

### Step 2: Customize the Feature List
- Cross off features you don't need
- Add any specific to your use case
- Prioritize for MVP

### Step 3: Follow the File Structure
Copy the suggested structure as your starting point.

### Step 4: Build Screen by Screen
Each blueprint lists screens/pages — build one at a time.

### Step 5: Use the Pitfalls Section
Check what typically goes wrong and avoid it.

---

## Creating Your Own Blueprints

Use this template for new app types:

```markdown
# [App Type] Blueprint

## Core Purpose
What problem does this solve?

## User Types
Who uses this and why?

## Feature Categories
### Category 1
- Feature (why it's needed)

## User Flows
1. Flow name: step → step → step

## Screens/Pages
| Screen | Purpose | Key Components |

## Data Model
| Entity | Fields | Relationships |

## Technical Stack (Recommended)
| Concern | Recommendation | Why |

## MVP Scope
Must have for v1...

## Full Vision
Everything eventually...

## File Structure
```
project/
├── ...
```

## Common Pitfalls
- What goes wrong and how to avoid it

## Implementation Order
Build in this sequence...

## Appendix: Code Patterns
Optional starter snippets and patterns to reduce setup time.
```

---

## Architecture

```
blueprints/
├── README.md              # This file
├── *.md                   # Blueprint specifications
├── templates/             # Code templates for generation
│   ├── flask/
│   ├── fastapi/
│   ├── react/
│   └── express/
│
├── # Core Tools
├── scaffold.py            # Project scaffolder
├── template_engine.py     # Template-based code generator
├── advisor.py             # Keyword-based blueprint advisor
├── builder.py             # Menu-driven blueprint builder
│
├── # Intelligent Scaffolding System
├── constraint_solver.py   # Logical deduction engine (rule-based)
├── csp_constraint_solver.py # Formal CSP with conflict detection
├── blocks.py              # Compositional code blocks
├── contracts.py           # Bidirectional spec/code contracts
├── intelligent_scaffold.py # Unified pipeline
├── beyond_belief.py       # Advanced features (cross-lang, synthesis)
├── logic_advisor.py       # Deterministic advisor (no AI, instant)
├── learning_integration.py # Level-gated learning system
├── test_system.py         # Comprehensive test suite (44 tests)
│
├── # Builder Dev Server
├── builder_server.py      # HTTP API server for visual editor
├── builder.html           # Enhanced visual editor with API integration
├── visual_editor.html     # Standalone visual block editor
├── test_server.py         # API endpoint tests
│
├── workspace/             # Generated projects output
└── output/                # Demo generated project
```

---

## How It Works (No AI Required)

The intelligent scaffolding system achieves LLM-like results through:

| Approach | What LLMs Do | What We Do Instead |
|----------|--------------|-------------------|
| **Understanding** | Statistical inference | Logical constraint propagation |
| **Generation** | Token prediction | Compositional block assembly |
| **Correctness** | Probabilistic | Verified contracts |

### The Three Breakthroughs

1. **Constraint Solving**: Rules like "if offline + multi_user → CRDT sync" let us deduce architecture without guessing

2. **Compositional Blocks**: Code pieces that declare `requires: [storage]` and `provides: [auth]` auto-assemble correctly

3. **Bidirectional Contracts**: Spec and code are projections of the same entity — they literally cannot disagree

---

## When You Have AI Access

Use it to:
1. Generate new blueprints for app types not listed
2. Expand existing blueprints with more detail
3. Create custom blocks for domain-specific needs
4. Debug complex issues

**The goal:** These tools let you make real progress without AI. Then use AI time strategically.
