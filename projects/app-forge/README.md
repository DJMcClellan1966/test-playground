# App Forge - AI-Free, Constraint-Driven App Builder

Build working Flask apps with natural language + smart questions. No AI hallucination, no visual block editors—just describe what you want and get a working preview.

## The Vision

**Your workflow:**
1. Type: "A recipe collection app where I can save recipes with ingredients"
2. Answer: 2-5 yes/no questions (only what can't be inferred)
3. Get: Working Flask app with tech stack automatically chosen
4. Test: Preview runs instantly
5. Export: Save to desktop or GitHub

**Why this beats AI code generation:**
- ✅ Every decision is explicit and explainable
- ✅ Constraint solver picks the right tech (no random choices)
- ✅ Code is always valid and runnable
- ✅ You understand every piece
- ✅ Learns from your feedback (Good/Bad stores)
- ✅ Improves with Naive Bayes classification
- ✅ Intent Graph for LLM-like understanding (without the LLM)
- ✅ **NEW** Multi-file architecture with models.py + db.py separation
- ✅ **NEW** 28 game templates (Tetris, Breakout, Minesweeper, Wordle, Sudoku, Connect Four, etc.)
- ✅ **NEW** Download as ZIP with deployment configs (Docker, Vercel, Railway, Render)
- ✅ **NEW** Dark mode UI with localStorage persistence
- ✅ **NEW** Learning loop with regex pattern generator
- ✅ **NEW** 3-Layer Universal Template Architecture (Template → Features → Traits)
- ✅ **NEW** Slot-based code injection for 5 frameworks (Flask, FastAPI, Click, HTML Canvas, scikit-learn)
- ✅ **NEW** Trait Store that learns from successful builds
- ✅ **NEW** Semantic Kernel for LLM-free understanding (4-layer pipeline replaces neural networks)

## Quick Start

```powershell
cd projects\app-forge

# Install
pip install -r requirements.txt

# Run
python backend\app.py
```

Open **http://127.0.0.1:5000**

## Architecture

```
backend/
├── app.py              # Flask API server (main entry point)
├── smartq.py           # Question engine with smart inference
├── solver.py           # Constraint solver (answers → tech stack)
├── codegen.py          # Code generator (Flask boilerplate + multi-file apps)
├── project_manager.py  # Save to disk, git init, push to GitHub
├── preview_server.py   # Live preview subprocess management
├── template_registry.py    # Feature extraction + template matching
├── tfidf_matcher.py        # TF-IDF + BM25 + Jaccard similarity
├── intent_graph.py         # Semantic network with spreading activation
├── component_assembler.py  # Composable UI components (24 types)
├── modular_kernel.py       # Kernel + Component architecture
├── build_memory.py         # Good/Bad stores with revision tracking
├── classifier.py           # Naive Bayes ML for learning
├── domain_parser.py        # Parse domain models from description
├── game_engine.py          # 28 game templates with component configs
├── regex_generator.py      # Learning system for prompt→template patterns
├── universal_template.py   # Slot-based templates for 5 frameworks
├── feature_store.py        # 12+ composable features with dependencies
├── trait_store.py          # App-specific patterns that learn
├── slot_generator.py       # Main generator: Template + Features + Traits
├── semantic_kernel.py      # LLM-free understanding (4-layer pipeline)
├── knowledge_base.py       # Entity/action/type mappings (500+ entries)
└── data/
    ├── build_memory.db     # SQLite: build history
    └── models/             # Trained classifier models (.pkl)

frontend/
├── index.html          # 3-step wizard with edit/history
├── js/app.js           # State machine + API calls
└── css/style.css       # Clean UI with dark mode support
```

## Semantic Kernel - What LLMs Do, Without LLMs

**The Problem:** LLMs are excellent at understanding natural language, but they:
- Require cloud APIs ($$$)
- Hallucinate code that doesn't work
- Can't be explained (black box)
- Change behavior unpredictably (model updates)

**The Solution:** Extract the **universal patterns** that LLMs learn and implement them algorithmically.

### The 4-Layer Architecture

App Forge uses a **Semantic Kernel** that replicates LLM understanding through compositional semantics:

```
Description: "inventory tracker for products with suppliers"
                    ↓
┌──────────────────────────────────────────────────────────┐
│ LAYER 1: PARSE (Syntax Analysis)                        │
│ ├─ Entity Extraction: "inventory", "products",          │
│ │                      "suppliers" (nouns → models)     │
│ ├─ Relationship Detection: products→suppliers           │
│ │                          (prepositions)               │
│ └─ Action Extraction: "track" (verbs → features)        │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ LAYER 2: UNDERSTAND (Semantic Similarity)               │
│ └─ GloVe Embeddings: "track" ≈ "manage" ≈ "organize"   │
│                      (word vectors, cosine similarity)   │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ LAYER 3: KNOWLEDGE (Domain Inference)                   │
│ ├─ Entity→Fields Dictionary (500+ mappings):            │
│ │  "product" → {name, price, sku, quantity}            │
│ │  "supplier" → {name, contact, email, phone}          │
│ ├─ Action→Feature Mapping (100+ verbs):                 │
│ │  "track" → {database, crud}                          │
│ └─ Type Inference Rules:                                │
│    "price" → float, "quantity" → int, "name" → str     │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ LAYER 4: COMPOSE (Feature Assembly)                     │
│ ├─ Framework Selection: Flask (has_data=true)           │
│ ├─ Feature Resolution: {database, crud, search}         │
│ └─ Model Generation:                                    │
│    - Product(name, price, sku, quantity)                │
│    - Supplier(name, contact, email)                     │
│    - Inventory(item_name, quantity, location)           │
└──────────────────────────────────────────────────────────┘
                    ↓
            Working Flask App
```

### Knowledge Base (No Training Required)

The kernel uses **curated dictionaries** instead of neural networks:

| What LLMs Learn | Our Implementation | Size |
|-----------------|-------------------|------|
| Common database schemas | `ENTITY_FIELDS` dict | ~50 entities, 500+ fields |
| REST API patterns | `ACTION_FEATURES` dict | ~100 action verbs |
| Type system conventions | `TYPE_HINTS` dict | ~60 field types |
| Word meanings | GloVe embeddings | 300MB (already in App Forge) |
| Composition rules | Dependency graph | ~20 constraint rules |

**Example Knowledge:**
```python
# What "product" typically has (learned from millions of schemas)
"product": [
    FieldDefinition("name", "str", required=True),
    FieldDefinition("price", "float", required=True),
    FieldDefinition("sku", "str", required=False),
    FieldDefinition("quantity", "int", required=True),
]

# What actions imply which features
"track": {"database", "crud"},
"search": {"search", "database"},
"export": {"export", "database"},
```

### Test Results

From `test_semantic_kernel.py`:

```
✓ Entity Extraction: 5/5 pass (100%)
✓ Action Extraction: 4/4 pass (100%)
✓ Feature Inference: 4/4 pass (100%)
✓ Model Inference: 4/4 pass (100%)
✓ Complete Understanding: 3/4 pass (75%)
✓ Novel Descriptions: 4/5 pass (80%)
```

**Novel descriptions** (no pre-defined trait):
- "pet grooming appointment scheduler" → `Appointment` model with scheduler features
- "plant watering reminder tracker" → `Reminder` model with tracking
- "car maintenance log with service records" → `Maintenance`, `Service` models

### Fallback Strategy

```python
# In slot_generator.py
trait = trait_store.match(description)  # Try exact match first

if not trait:
    # Fallback to Semantic Kernel
    understanding = semantic_kernel.understand(description)
    models = understanding.models      # Auto-generated
    features = understanding.features  # Auto-inferred
    framework = understanding.framework  # Auto-selected
```

### Why This Works

LLMs learn patterns from training data. Instead of:
1. ❌ Training a neural network on millions of examples
2. ❌ Paying for inference on each request
3. ❌ Debugging hallucinations

We:
1. ✅ Extract the patterns LLMs learn into dictionaries
2. ✅ Run pattern matching + composition locally
3. ✅ Get explainable, deterministic results

**No external APIs. No neural networks. Just smart algorithms.**

## Understanding Engine (AI-Free NLU)

App Forge uses a **5-layer understanding system** that achieves 100% accuracy on our test suite—matching LLM quality without any cloud AI:

| Layer | Technique | What it does | Accuracy Boost |
|-------|-----------|--------------|----------------|
| 1. Fuzzy Correction | Levenshtein + difflib | Fix typos ("calculater" → "calculator") | Baseline |
| 2. Feature Extraction | Regex + TF-IDF/BM25/Jaccard | Pattern matching + semantic similarity | +13% |
| 3. Intent Graph | Spreading activation | Multi-hop reasoning (3 hops, 60% decay) | +16% |
| 4. GloVe Embeddings | Word vectors | Synonym expansion ("quick" ≈ "fast") | +5% |
| 5. Position Attention | Weighted scoring | First words matter more (3.0x boost) | +3% |
| 6. User Preferences | Build history | Boost templates user frequently picks | Adaptive |

**Example:** "reaction time game with different colored tiles"
- **Regex only:** Matches `sliding_puzzle` (wrong) because it sees "tiles"
- **With semantic layer:** "colored" → visual → distractor → `reaction_game`
- **With Intent Graph:** "different" → distractor concept, spreading to `reaction_game` ✓

### Matching Functions

```python
from template_registry import (
    match_template,          # Regex only (fast, 84% accuracy)
    match_template_hybrid,   # + TF-IDF/BM25/Jaccard (100% accuracy)
    match_template_intent,   # + Intent Graph (100% accuracy, best for edge cases)
)

# Best option - combines all three
best_id, features, scores = match_template_intent("track my daily habits")
# → ('crud', {...}, [('crud', 12.5), ...])
```

## Core Components

### 1. Smart Inference (`template_registry.py`)
Extracts features from natural language descriptions:
```python
"a wordle clone" → {word_based: true, game: true, wordle: true}
"recipe manager with search" → {data_app: true, crud: true, search: true}
```

### 2. Semantic Matching (`tfidf_matcher.py`)
Three complementary algorithms working together:

| Algorithm | Best For | How It Works |
|-----------|----------|--------------|
| **TF-IDF** | Common terms | Term frequency × inverse document frequency |
| **BM25** | Varying doc lengths | Saturation function for repeated words |
| **Jaccard** | Partial matches | N-gram overlap ("colored" ≈ "multicolored") |

```python
from tfidf_matcher import combined_match, combined_explain

# Get best template matches
results = combined_match("quick reflex test", top_k=3)
# → [('reaction_game', 1.0), ('timer', 0.12), ...]

# Explain why
combined_explain("quick reflex test", "reaction_game")
# → {tfidf_score: 0.57, bm25_score: 11.3, jaccard_score: 0.18, ...}
```

### 3. Intent Graph (`intent_graph.py`)
A semantic network that mimics LLM attention:

```
Concept Nodes: game, puzzle, reaction, visual, distractor, recipe, crud...
Relationships: colored → visual → distractor → reaction_game

Spreading Activation (3 hops, 60% decay):
  "different" activates → distractor (0.7)
  distractor spreads to → reaction (0.8)
  reaction activates → reaction_game template
```

```python
from intent_graph import intent_match, intent_explain

# Get template scores from semantic understanding
intent_match("click the correct color quickly")
# → {'reaction_game': 2.8, 'memory_game': 0.4, ...}

# See what activated
intent_explain("click the correct color quickly")
# → {initial: [click, visual, correct], spread: [reaction, target, distractor]}
```

### 4. Template Matching (`template_registry.py`)
Scores templates against extracted features using attention-weighted matching:
```python
match_template("password generator")  # → ("generator", 0.95)
match_template("recipe collection")   # → ("crud_app", 0.87)
```

### 3. Game Engine (`game_engine.py`)
28 pre-configured game templates with modular components:
- **Classic Games**: wordle, hangman, tic-tac-toe, memory, sliding puzzle, quiz, connect four, blackjack
- **Arcade Games**: snake, tetris, 2048, breakout, minesweeper, cookie clicker
- **Mini Games**: dice roller, coin flip, rock-paper-scissors, reaction time test, typing test
- **Utilities**: calculator, timer, unit converter, guess the number
- **Experimental**: jigsaw puzzle, sudoku, algorithm visualizer

### 4. Component Assembly (`component_assembler.py`)
30+ composable UI components for apps not in the template store:
- **Generators**: password, color palette, dice, coin, quote, lorem, name
- **UI**: editor, canvas, kanban, chat, flashcard, typing test
- **Productivity**: pomodoro timer, habit tracker, expense tracker
- **Logic**: crud, search, export

### 5. Modular Kernel (`modular_kernel.py`)
The core algorithm: **Kernel + Components = App**

| Kernel | Description | Provides |
|--------|-------------|----------|
| `flask_minimal` | Bare Flask app | routing, templates |
| `flask_data` | Flask + SQLAlchemy | + database, models |
| `flask_auth` | Flask + Auth | + login, users, sessions |
| `flask_realtime` | Flask + SocketIO | + websockets, live updates |

```python
builder.compose("a realtime chat app")
# → kernel: flask_realtime, components: ['chat']

builder.compose("a todo list manager")  
# → kernel: flask_data, components: ['crud']
```

### 6. Universal Template Architecture (`slot_generator.py`)

A **3-layer composable system** that generates apps for any framework:

```
┌─────────────────────────────────────────────────────────┐
│                  UNIVERSAL TEMPLATE                      │
│  Slot-based code injection (IMPORTS, CONFIG, MODELS,    │
│  INIT, ROUTES, HELPERS, ERROR_HANDLING, CLEANUP, MAIN)  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   FEATURE STORE                          │
│  12+ composable features: database, crud, auth, search, │
│  export, realtime, responsive_ui, game_loop, scoring... │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              TRAIT STORE (Learning)                      │
│  8 seed traits (recipe_app, todo_app, game_generic...)  │
│  + learns new traits from successful builds             │
└─────────────────────────────────────────────────────────┘
```

**Frameworks supported:** Flask, FastAPI, Click CLI, HTML Canvas (games), scikit-learn (ML pipelines)

```python
from slot_generator import generate_app

# Generate from description
project = generate_app("a recipe collection app", {"search": True})
# → RecipeCollection: Flask + SQLAlchemy + CRUD + Search
# → Files: app.py, requirements.txt, templates/index.html

project = generate_app("a snake game")
# → SnakeGame: HTML Canvas + game_loop + input_handler + scoring
# → Files: index.html

project = generate_app("REST API for users", {"needs_auth": True})
# → RestApiUser: FastAPI + auth + JWT + SQLAlchemy
# → Files: main.py, requirements.txt
```

### 7. Build Memory (`build_memory.py`)
Persistent storage of all builds with accept/reject tracking:

| Store | Purpose |
|-------|---------|
| **Good Store** | Accepted builds with full revision history |
| **Bad Store** | Rejected/deleted builds with reasons |

```python
memory.accept_build(build_id)                    # → Good store
memory.reject_build(build_id, "Code incomplete") # → Bad store
memory.create_revision(build_id, edits)          # → New version
memory.get_revision_chain(build_id)              # → Full history
```

### 7. Naive Bayes Classifier (`classifier.py`)
Learns from your Good/Bad stores to improve predictions:

| Classifier | Learns |
|------------|--------|
| `TemplateClassifier` | Which kernel fits which description |
| `FeatureClassifier` | Multi-label: needs_auth, needs_data, etc. |
| `ComponentClassifier` | Which components work well together |

```bash
# Train on accepted builds
python classifier.py train

# Predict for new description
python classifier.py predict "a word guessing game"
```

## API Reference

### Build Flow
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/start` | POST | Start wizard with description |
| `/api/answer` | POST | Submit yes/no answer |
| `/api/generate` | POST | Generate code |
| `/api/save-and-preview` | POST | Save to disk |
| `/api/export-github` | POST | Push to GitHub |

### Build Memory
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/builds?status=good\|bad` | GET | List builds by status |
| `/api/builds/<id>` | GET | Get build details |
| `/api/builds/<id>/accept` | POST | Move to Good store |
| `/api/builds/<id>/reject` | POST | Move to Bad store |
| `/api/builds/<id>/delete` | DELETE | Soft delete with reason |
| `/api/builds/<id>/revisions` | GET | Get revision history |
| `/api/builds/stats` | GET | Get build statistics |

### Modular Kernel
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/compose` | POST | Compose app from description |
| `/api/recommendations` | POST | Get suggestions from history |
| `/api/kernels` | GET | List available kernels |
| `/api/components` | GET | List available components |

### ML Classifier
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ml/status` | GET | Check training status |
| `/api/ml/train` | POST | Train on Good store |
| `/api/ml/predict` | POST | Get ML predictions |

## How It Works

### Step 1: Description
User types what they're building.

### Step 2: Questions
Smart yes/no questions about:
- Multi-user access
- Authentication needs
- Real-time requirements
- Database complexity
- Mobile support
- Search/filter features
- Export capabilities

Questions adapt based on previous answers (no useless questions).

### Step 3: Review & Export
- Tech stack recommendation (Flask, SQLite, auth, etc.)
- Code preview
- App name
- Save to [`~/AppForge/<app-name>/`](~/AppForge/<app-name>/)
- Optional: Push to GitHub

## Tech Stack Selection (Smart)

The modular kernel automatically selects based on requirements:

| Description | Kernel | Components |
|-------------|--------|------------|
| "a wordle game" | flask_minimal | wordle |
| "a recipe manager" | flask_data | crud |
| "a login system" | flask_auth | — |
| "a chat app" | flask_realtime | chat |
| "a markdown editor" | flask_minimal | editor |
| "a kanban board" | flask_data | kanban, crud |
| "a snake game" | standalone | snake (canvas) |
| "a platformer" | standalone | Phaser.js platformer |
| "a space shooter" | standalone | Phaser.js shooter |

No LLM guessing—pure logic + learned patterns.

## Generated App Features

Each project includes:
- ✅ Flask server with routes
- ✅ HTML template with Tailwind CSS
- ✅ Database models (if needed) — **multi-file architecture** with separate `models.py` and `db.py`
- ✅ Authentication (if needed)
- ✅ UI components (editor, kanban, games, etc.)
- ✅ `.gitignore` and README
- ✅ **Deployment configs** (Docker, Vercel, Railway, Render) — optional
- ✅ Ready to run immediately
- ✅ **Download as ZIP** with all files bundled

Build tracked in memory for learning:
- Accept → Good store (used for future training)
- Reject → Bad store (with reason for analysis)
- Revise → New version linked to original

## Full Circle: Save & Export

### Save to Desktop
```
~/AppForge/my-app/
├── app.py
├── models.py         # (for data apps)
├── db.py             # (for data apps)
├── requirements.txt
├── templates/
│   └── index.html
├── static/
├── .gitignore
├── .appforge.json    # metadata
├── Dockerfile        # (optional)
├── docker-compose.yml # (optional)
├── vercel.json       # (optional)
├── railway.json      # (optional)
├── render.yaml       # (optional)
└── README.md
```

Then run:
```bash
cd ~/AppForge/my-app
pip install -r requirements.txt
python app.py
```

### Export to GitHub
1. Create empty repo on GitHub
2. In App Forge: "Export to GitHub"
3. Paste your repo URL
4. App Forge will git init, commit, and push

Done. Your app is live on GitHub.

## Next Steps (Roadmap)

- [x] Preview server (auto-start Flask in subprocess)
- [x] Smart inference from description (skip obvious questions)
- [x] Template registry with feature extraction
- [x] Component assembler for novel app types
- [x] Modular kernel architecture
- [x] Build memory with Good/Bad stores
- [x] Naive Bayes classifier for learning
- [x] 5-layer NLU: Fuzzy → Regex/TF-IDF → Intent Graph → GloVe → Position Attention
- [x] User preference learning from build history
- [x] Arcade games: Snake, Tetris, 2048 (vanilla JS)
- [x] Phaser.js games: Platformer, Space Shooter, Breakout
- [x] **Game engine expansion** (28 templates: Tetris, Breakout, Minesweeper, Wordle, Sudoku, Connect Four, etc.)
- [x] **Multi-file generation** (models.py + db.py separation for data apps)
- [x] **Download as ZIP** with build_id tracking
- [x] **Docker + deployment configs** (Dockerfile, docker-compose, Vercel, Railway, Render)
- [x] **Dark mode UI** with localStorage persistence
- [x] **Learning loop** with regex pattern generator
- [x] **Universal Template Architecture** (slot-based code injection for 5 frameworks)
- [x] **Feature Store** (12+ composable features with dependency resolution)
- [x] **Trait Store** (8 seed traits + learns from successful builds)
- [ ] K-means clustering for "similar apps" recommendations
- [ ] Ollama integration (smart Q generation from description)
- [ ] More kernels (FastAPI, Django)
- [ ] Custom components (user-defined patterns)
- [ ] Iterate mode (change answer, regenerate)
- [ ] Component marketplace (share custom generators)

## Philosophy

> "Constraint-driven development beats probabilistic generation."

This builder is **anti-AI** in the right way:
- No black boxes
- No hallucinations
- No "looks good but broken" code
- Only composition of proven patterns
- You own and understand every line
- **Learning without LLMs** — Naive Bayes on your own data
