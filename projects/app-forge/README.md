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
- ✅ **NEW** Intent Graph for LLM-like understanding (without the LLM)

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
├── codegen.py          # Code generator (Flask boilerplate)
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
└── data/
    ├── build_memory.db     # SQLite: build history
    └── models/             # Trained classifier models (.pkl)

frontend/
├── index.html          # 3-step wizard with edit/history
├── js/app.js           # State machine + API calls
└── css/style.css       # Clean UI
```

## Understanding Engine (AI-Free NLU)

App Forge uses a **3-layer understanding system** that mimics LLM behavior without any ML models:

| Layer | Technique | What it does | Accuracy Boost |
|-------|-----------|--------------|----------------|
| 1. Regex | Feature extraction | Precise keyword/pattern matching | Baseline |
| 2. TF-IDF + BM25 + Jaccard | Semantic similarity | Fuzzy matching, synonyms | +13% |
| 3. Intent Graph | Spreading activation | Multi-hop reasoning | +16% |

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

### 3. Component Assembly (`component_assembler.py`)
24 composable UI components for apps not in the template store:
- **Generators**: password, color palette, dice, coin, quote, lorem, name
- **Games**: wordle, hangman, tictactoe, memory, sliding puzzle, quiz
- **UI**: editor, canvas, kanban, chat, flashcard, typing test
- **Logic**: crud, search, export

### 4. Modular Kernel (`modular_kernel.py`)
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

### 5. Build Memory (`build_memory.py`)
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

### 6. Naive Bayes Classifier (`classifier.py`)
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

No LLM guessing—pure logic + learned patterns.

## Generated App Features

Each project includes:
- ✅ Flask server with routes
- ✅ HTML template with Tailwind CSS
- ✅ Database models (if needed)
- ✅ Authentication (if needed)
- ✅ UI components (editor, kanban, games, etc.)
- ✅ `.gitignore` and README
- ✅ Ready to run immediately

Build tracked in memory for learning:
- Accept → Good store (used for future training)
- Reject → Bad store (with reason for analysis)
- Revise → New version linked to original

## Full Circle: Save & Export

### Save to Desktop
```
~/AppForge/my-app/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
├── static/
├── .gitignore
├── .appforge.json  (metadata)
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
