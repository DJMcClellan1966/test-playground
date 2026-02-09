# App Blueprint Library

**Purpose:** Pre-built specifications for common app types so you can build complete applications without needing AI assistance.

Each blueprint includes:
- ✅ All "obvious" features (the stuff you shouldn't have to ask for)
- 📋 User flows and screens
- ⚙️ Technical decisions and recommendations
- 🎯 MVP scope vs full vision
- ⚠️ Common pitfalls to avoid
- 📁 Suggested file structure

---

## 🚀 NEW: Intelligent Scaffolding System

A breakthrough system that achieves **LLM-like intelligence without AI** by combining three approaches:

### 1. Constraint Solver (`constraint_solver.py`)
Logical deduction engine with 15+ architectural rules. Your requirements → derived architecture.

```powershell
python constraint_solver.py --offline --multi-user --explain
```

**Example**: "needs offline" + "multi-user" → automatically deduces CRDT sync, conflict resolution, auth backend

### 2. Compositional Blocks (`blocks.py`)
Code LEGOs that declare what they `require` and `provide`. Blocks auto-assemble based on constraints.

```powershell
python blocks.py --list              # See all blocks
python blocks.py --auth --offline    # Assemble matching blocks
```

**Blocks**: Auth, CRDT Sync, JSON Storage, SQLite Storage, CRUD Routes

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
├── constraint_solver.py   # Logical deduction engine
├── blocks.py              # Compositional code blocks
├── contracts.py           # Bidirectional spec/code contracts
├── intelligent_scaffold.py # Unified pipeline
├── test_system.py         # Comprehensive test suite (41 tests)
│
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
