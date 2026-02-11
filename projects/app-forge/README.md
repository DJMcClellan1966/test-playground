# App Forge - AI-Free, Constraint-Driven App Builder

Build working Flask apps with natural language + smart questions. No AI hallucination, no visual block editors—just ask what features you need and get a working preview.

## The Vision

**Your workflow:**
1. Type: "A todo app where teams collaborate in real-time"
2. Answer: 5-7 yes/no questions (auth? real-time? mobile?)
3. Get: Working Flask app with tech stack automatically chosen
4. Test: Preview runs instantly
5. Export: Save to desktop or GitHub

**Why this beats AI code generation:**
- ✅ Every decision is explicit and explainable
- ✅ Constraint solver picks the right tech (no random choices)
- ✅ Code is always valid and runnable
- ✅ You understand every piece
- ✅ Iterate and rebuild instantly

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

### Backend (`backend/`)
- **smartq.py** - Question engine (yes/no questionnaire)
- **solver.py** - Constraint solver (maps answers → tech stack)
- **codegen.py** - Code generator (Flask boilerplate)
- **project_manager.py** - Save to disk, git init, push to GitHub
- **app.py** - Flask API server

### Frontend (`frontend/`)
- **index.html** - 3-step wizard
- **js/app.js** - State machine + API calls
- **css/style.css** - Clean UI

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

The constraint solver automatically picks:

| Need | Choice | Reason |
|------|--------|--------|
| No DB needed | — | None |
| Simple data | SQLite | Local-first, no server |
| Complex queries | PostgreSQL | Indexes, better performance |
| Real-time | FastAPI + WebSockets | Async + live updates |
| Mobile | React + React Native | Code sharing |
| Auth needed | Session-based | Secure, simple |

No LLM guessing—pure logic.

## Generated App Features

Each project includes:
- ✅ Flask server with basic CRUD
- ✅ HTML template (editable)
- ✅ Database models (if needed)
- ✅ Authentication routes (if needed)
- ✅ `.gitignore` and README
- ✅ Ready to run immediately

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

- [ ] Preview server (auto-start Flask in subprocess)
- [ ] Ollama integration (smart Q generation from description)
- [ ] More block library (Django, FastAPI templates)
- [ ] Custom blocks (user-defined patterns)
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
