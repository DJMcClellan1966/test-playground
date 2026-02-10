# Test Playground

A workspace for building and experimenting with local-first tools and apps.

---

## Quick Reference

| What | Command |
|------|---------|
| Create new app | `cd blueprints && python forge.py new "my app"` |
| Run existing app | `cd blueprints && python forge.py run <name>` |
| List all apps | `cd blueprints && python forge.py list` |

---

## Working Apps

### 1. Forge - Template App Builder

**Location:** `blueprints/forge.py`

Build Flask apps without AI. Deterministic template assembly.

```powershell
cd blueprints

# Create a new app
python forge.py new "book tracker"

# Run it
python forge.py run book-tracker

# Opens at http://localhost:5000
```

**Available Features:**
- `auth` - Login/logout
- `search` - Find by keyword
- `export` - Download as JSON

```powershell
python forge.py new "private notes" --with auth
python forge.py new "inventory" --with search export
```

---

### 2. Generated Apps (Ready to Run)

**Location:** `blueprints/forge_projects/`

| App | Features | Run Command |
|-----|----------|-------------|
| grocery-planner | search | `cd blueprints && python forge.py run grocery-planner` |
| meal-planner | search | `cd blueprints && python forge.py run meal-planner` |
| movie-collection | search | `cd blueprints && python forge.py run movie-collection` |
| workout-log | auth | `cd blueprints && python forge.py run workout-log` |

Or run directly:
```powershell
cd blueprints/forge_projects/movie-collection
python app.py
# Opens at http://localhost:5000
```

---

### 3. Socratic Learner

**Location:** `projects/socratic-learner/`

AI-powered learning system that extracts knowledge from authoritative texts.

```powershell
cd projects/socratic-learner

# Check setup (requires Ollama)
python setup_check.py

# Extract knowledge from a text
python extractor.py sources/algorithms_intro.md

# Interactive learning (CLI)
python socrates.py

# GUI version
python gui.py
```

**Requires:** Ollama running locally (`ollama serve`)

---

### 4. Prompt Twin - AI Context Profiler

**Location:** `blueprints/prompt_twin.py`

Builds a local profile of your coding patterns for AI agents. Now with watch mode and Ollama integration.

```powershell
cd blueprints

# Scan local projects
python prompt_twin.py scan

# Fetch GitHub data
python prompt_twin.py github <your-username>

# Inject context into AI tools (Cursor, VS Code, Ollama)
python prompt_twin.py inject

# Watch for changes and auto-update (Ctrl+C to stop)
python prompt_twin.py watch

# Install git post-commit hook for auto-updates
python prompt_twin.py hook

# Export structured profile (JSON + YAML)
python prompt_twin.py structured

# Test Ollama completions with/without context
python prompt_twin.py ollama "write a flask api"
```

**Feedback Commands:**
```powershell
# View feedback summary
python prompt_twin.py feedback

# Log results for AI learning
python prompt_twin.py outcome "ran app.py" success
python prompt_twin.py error "ImportError" "No module flask"
python prompt_twin.py correction "AI suggested" "I preferred"

# Nuanced feedback (naming/style/deprecated/complexity)
python prompt_twin.py nuanced naming "Used camelCase instead of snake_case"
python prompt_twin.py nuanced-summary
```

**High-Value Commands:**
```powershell
# Start MCP server (for AI agent queries)
python prompt_twin.py mcp [port]        # Default: 8765

# Configuration
python prompt_twin.py config            # Show config
python prompt_twin.py config set KEY VAL
python prompt_twin.py health            # Check all integrations

# LLM Analysis
python prompt_twin.py analyze           # AI pattern analysis
python prompt_twin.py suggest "api with auth"  # Template suggestions

# Profile Tracking
python prompt_twin.py snapshot          # Save profile snapshot
python prompt_twin.py snapshots         # List snapshots
python prompt_twin.py diff              # Compare with last snapshot
```

Creates: `.cursorrules`, `.github/copilot-instructions.md`, `profile.yaml`

---

## Folder Structure

```
Test_playground/
├── blueprints/
│   ├── forge.py              # App builder (main tool)
│   ├── prompt_twin.py        # AI context profiler
│   ├── forge_projects/       # Generated apps (run these!)
│   ├── patterns/             # Code pattern library
│   ├── archive/              # Legacy experimental code
│   └── examples/             # Example apps
├── projects/
│   └── socratic-learner/     # Learning system
├── ideas/                    # Planning docs
├── docs/                     # Notes
└── .venv/                    # Python environment
```

---

## Setup

```powershell
# Activate virtual environment (if not already)
.\.venv\Scripts\Activate

# For Socratic Learner (optional)
ollama serve  # In separate terminal
```

---

## Philosophy

- **Local-first** - Everything runs on your machine
- **No AI required** - Forge templates are deterministic
- **AI optional** - Use when helpful, not dependent
- **Working code** - Build incrementally, verify often
