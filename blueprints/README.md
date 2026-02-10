# Forge - Template-Based App Builder

> **No AI required. Same input = same output, every time.**

---

## Quick Start

```powershell
cd blueprints
python forge.py new "recipe tracker"
python forge.py run recipe-tracker
```

That's it. You have a working Flask app with CRUD, SQLite, and a web interface.

---

## Commands

```powershell
python forge.py new "name"              # Create a new project
python forge.py new "name" --with auth  # Create with specific features
python forge.py run <name>              # Run a project
python forge.py list                    # Show your projects
python forge.py templates               # Show available features
```

---

## Available Features

| Feature | Description | Trigger Keywords |
|---------|-------------|------------------|
| **Base** | Flask + SQLite + CRUD + Web UI | (always included) |
| `auth` | Login/logout with username/password | login, auth, user, password |
| `search` | Find items by keyword | search, find, filter, query |
| `export` | Download data as JSON | export, download, backup |

---

## Examples

```powershell
# Simple tracker
python forge.py new "book collection"

# With authentication
python forge.py new "private notes" --with auth

# With search and export
python forge.py new "inventory" --with search export

# Keywords auto-detect features
python forge.py new "secure password manager"  # auto-adds auth
```

---

## How It Works

1. You describe what you want
2. Forge assembles **pre-written templates** (visible in `forge.py`)
3. You get working code you can read and edit
4. **No AI involved** - deterministic output

---

## Your Workflow

1. **Create**: `python forge.py new "my app"`
2. **Run**: `python forge.py run my-app` (or `cd forge_projects/my-app && python app.py`)
3. **Edit**: Open files in VS Code, changes auto-reload
4. **Evolve**: Modify the code directly - it's just Python and HTML

---

## Generated Files

Each project contains:

```
forge_projects/my-app/
├── app.py              # Flask application (edit this!)
├── templates/
│   ├── index.html      # Web interface (edit this!)
│   └── login.html      # Login page (if auth enabled)
├── data.db             # SQLite database (created on run)
├── forge.json          # Project metadata
└── README.md           # How to run and edit
```

---

## Philosophy

| AI Code Generation | Forge Templates |
|-------------------|-----------------|
| Probabilistic output | **Deterministic output** |
| Opaque reasoning | **Visible templates** |
| Variable results | **Same input = same result** |
| May hallucinate code | **Code is pre-tested** |
| Requires trust | **Read the source** |

The AI assistant is **optional** - ask it for help if stuck, but the code generation itself is just template assembly. No magic.

---

## Other Tools

### prompt_twin.py - Local Context Profiling

Build a local profile from your coding patterns for AI agents to consult:

```powershell
python prompt_twin.py scan                    # Scan projects for patterns
python prompt_twin.py github <username>       # Fetch GitHub data
python prompt_twin.py inject                  # Inject context into AI tools
python prompt_twin.py feedback                # Show reality feedback
python prompt_twin.py outcome "action" "success|failure"  # Log outcomes
```

Creates `.cursorrules`, `.github/copilot-instructions.md`, and Ollama wrapper. Includes reality feedback loop to track what actually works.

---

## Legacy Tools

Other files in this directory are experimental:
- `nexus.py`, `builder_server.py`, `visual_builder.py` - Complex visual builders
- `constraint_solver.py`, `csp_constraint_solver.py` - Formal constraint systems
- `idea.py`, `dev.py` - Earlier iterations of forge.py
