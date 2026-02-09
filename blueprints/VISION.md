# Blueprint Evolution System

> From conversation to working app, with continuous improvement.

## The Vision

Traditional development:
```
Idea → Research → Design → Code → Test → Deploy → Hope it works
```

Blueprint Evolution:
```
Conversation → Custom Blueprint → Generated Code → Running App → Usage Feedback → Better Blueprints
      ↑                                                                                    │
      └────────────────────────────────────────────────────────────────────────────────────┘
```

**The key insight:** Software requirements aren't static. What users actually do reveals what they actually need.

---

## System Components

### 1. Custom Blueprint Generator
**File:** `blueprint_generator.py`

Instead of choosing from templates, describe what you want:

```powershell
python blueprint_generator.py
```

```
📝 What do you want to build?
You: An app to track recipes I've tried and what modifications I made

📝 Who will use this?
You: Just me, but I want to share specific recipes with friends...

🧠 Synthesizing your custom blueprint...
✅ Blueprint saved to: blueprints/custom/recipe-tracker.md
```

**How it works:**
- Socratic dialogue discovers your actual requirements
- LLM synthesizes a complete blueprint from:
  - Your stated needs
  - Patterns from existing blueprints (few-shot learning)
  - Standard best practices

### 2. LLM Code Generation
**File:** `scaffold.py` with `--generate` flag

Turn blueprints into working code:

```powershell
# Stub generation (original)
python scaffold.py learning-app --name MyApp

# LLM-powered implementation
python scaffold.py learning-app --name MyApp --generate
```

**Without --generate:**
```python
def list_books():
    # TODO: Implement - see blueprint
    return jsonify([])
```

**With --generate:**
```python
def list_books():
    """List all books in library."""
    books = Book.query.order_by(Book.last_opened.desc()).all()
    return jsonify([{
        "id": b.id,
        "title": b.title,
        "author": b.author,
        "status": b.status,
    } for b in books])
```

### 3. Usage Telemetry
**File:** `telemetry.py`

Track what features actually get used:

```python
from telemetry import tracker

@tracker.track("library.add_book")
def add_book(data):
    ...
```

View usage patterns:
```powershell
python telemetry.py myapp

📊 Usage Summary: myapp
   Total events: 1,247
   Top features:
      library.view_book: 523
      search.execute: 312
      highlights.create: 201
      flashcards.create: 12   # Rarely used!
```

### 4. Blueprint Analyzer
**File:** `telemetry.py` (analyzer functions)

Turn usage data into blueprint improvements:

```powershell
python telemetry.py --analyze learning-app

📊 Blueprint Analysis: learning-app
   Apps analyzed: 15
   
   ⬆️ Promote to MVP (widely used):
      • highlights.export (used by 93% of apps)
      • search.cross_book (used by 87% of apps)
   
   ⬇️ Consider removing (rarely used):
      • flashcards.spaced_repetition (only 13% of apps)
      • ocr.scanned_pdf (only 7% of apps)
```

---

## The Complete Workflow

### Phase 1: Create Your App

```
Step 1: Describe what you want
$ python blueprint_generator.py
→ Answers questions
→ Gets custom blueprint

Step 2: Generate working code
$ python scaffold.py custom/my-app --name MyApp --generate
→ LLM writes actual implementation
→ App is immediately runnable

Step 3: Customize and extend
→ Review generated code
→ Adjust as needed
→ The blueprint remains your reference
```

### Phase 2: Use Your App

```
Step 4: Run your app
$ cd projects/myapp
$ pip install -r requirements.txt
$ python src/app.py

Step 5: Usage is tracked (locally)
→ Which features you use
→ How often
→ What you ignore
```

### Phase 3: Improve Blueprints

```
Step 6: Analyze patterns
$ python telemetry.py --analyze learning-app

Step 7: Update blueprints
→ Promote popular features
→ Demote unused features
→ Add patterns from real usage

Step 8: Future apps benefit
→ Next person gets better defaults
→ The system learns
```

---

## Privacy & Data

**All telemetry is local by default:**
- Data stored in `projects/.telemetry/`
- No network calls
- You control what to share

**What's tracked:**
- Feature name (e.g., "library.add_book")
- Timestamp
- Session ID
- Optional metadata you add

**What's NOT tracked:**
- File contents
- Personal data
- Anything outside your explicit instrumentation

---

## Future Directions

### Near-term
- [ ] Auto-generate telemetry integration in scaffolded apps
- [ ] Blueprint diff tool (compare your code vs blueprint)
- [ ] Incremental feature addition (`scaffold.py --add-feature search`)

### Medium-term
- [ ] Cross-user pattern sharing (opt-in, anonymized)
- [ ] Blueprint versioning (track how blueprints evolve)
- [ ] AI-suggested blueprint updates from usage patterns

### Long-term Vision
- [ ] Blueprint as runtime constraint engine
- [ ] Live blueprint synchronization (code ↔ spec)
- [ ] Community blueprint evolution

---

## File Overview

```
blueprints/
├── README.md                    # Main docs
├── scaffold.py                  # Generate projects (with --generate for LLM)
├── blueprint_generator.py       # Create custom blueprints via dialogue
├── telemetry.py                 # Track and analyze usage
├── VISION.md                    # This file
├── custom/                      # Your generated custom blueprints
└── [blueprint].md               # Library blueprints
```

---

## Getting Started

```powershell
# 1. Create a custom blueprint (optional - can use library blueprints)
cd blueprints
python blueprint_generator.py

# 2. Generate your app with LLM (requires Ollama running)
python scaffold.py learning-app --name MyApp --generate

# 3. Run it
cd ../projects/myapp
pip install -r requirements.txt
python src/app.py

# 4. Later: View your usage patterns
cd ../../blueprints
python telemetry.py myapp
```

---

*"The best software evolves from real use, not imagined requirements."*
