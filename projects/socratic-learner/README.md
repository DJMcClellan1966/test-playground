# Socratic Learner

A prototype learning system that uses AI to extract baseline knowledge from authoritative texts, allowing novices to understand complex material without prior expertise.

## The Philosophy

**Plato's Forms meet LLMs:**
- The **corpus** (authoritative texts like TAOCP) = **perfect forms** (source of truth)
- The **local LLM** = **imperfect copy** that can access those forms
- The **user** = questioner seeking truth through dialogue

The LLM doesn't need to be perfect. It just needs to faithfully retrieve and present from the perfect source.

## How It Works

```
Authoritative Text (source of truth)
         ↓
Artificial Questioner (extracts structure)
         ↓
Knowledge Layer (accessible summaries)
         ↓
Human Learner (explores, goes deeper)
```

1. **Source texts** are loaded and chunked by section
2. **Standard Interrogation** extracts key information:
   - Overview (what is this about?)
   - Prerequisites (what must I know?)
   - Key terms (vocabulary)
   - Main claims (central ideas)
   - Examples (concrete illustrations)
   - Pitfalls (common mistakes)
   - Connections (related concepts)
3. **User explores** the pre-digested knowledge
4. **User goes deeper** by asking questions, AI retrieves from source

## Quick Start (Local LLM - FREE)

### Step 1: Install Ollama
```powershell
winget install Ollama.Ollama
```

### Step 2: Start Ollama (in a separate terminal)
```powershell
ollama serve
```

### Step 3: Download a small model
```powershell
# Pick one based on your RAM:
ollama pull phi3:mini      # 8GB RAM (recommended)
ollama pull gemma2:2b      # 4GB RAM (lightweight)
ollama pull qwen2.5:3b     # 8GB RAM (good balance)
ollama pull qwen2.5:7b     # 16GB RAM (better quality)
```

### Step 4: Check setup
```powershell
python setup_check.py
```

### Step 5: Extract knowledge from a source
```powershell
python extractor.py sources/algorithms_intro.md
```

### Step 6: Explore interactively
```powershell
python explorer.py
```

### Step 7: Socratic GUI (optional)
```powershell
python gui.py
```

## Model Recommendations

| Your RAM | Model | Command | Quality |
|----------|-------|---------|---------|
| 4GB | Gemma 2B | `ollama pull gemma2:2b` | Basic |
| 8GB | Phi-3 Mini | `ollama pull phi3:mini` | Good |
| 8GB | Qwen 2.5 3B | `ollama pull qwen2.5:3b` | Good |
| 16GB | Qwen 2.5 7B | `ollama pull qwen2.5:7b` | Very Good |
| 16GB | Llama 3.2 8B | `ollama pull llama3.1:8b` | Very Good |
| 32GB+ | Llama 3.1 70B | `ollama pull llama3.1:70b` | Excellent |

**For this use case**, even small models work well because the **knowledge is in the corpus**, not the model. The model just needs to follow instructions and cite text.

## Project Structure

```
socratic-learner/
├── sources/              # Authoritative texts (the "perfect forms")
│   └── algorithms_intro.md
├── knowledge/            # Generated knowledge layers
├── prompts/              # Interrogation prompts
│   └── standard_interrogation.py
├── config.py             # LLM provider settings
├── llm_client.py         # Ollama/API connections
├── extractor.py          # Extracts knowledge from sources
├── explorer.py           # Interactive CLI for learning
├── socrates.py           # Socratic dialogue engine
├── blueprint_advisor.py  # Socratic app planning advisor
├── gui.py                # Tkinter GUI for Socratic dialogue
├── setup_check.py        # Verify your setup
└── README.md
```

## Usage

### Extract Knowledge
```bash
python extractor.py sources/your_book.md
```

### Use a smaller model for extraction (faster)
```powershell
$env:OLLAMA_MODEL = "qwen2.5:7b"          # for dialogue
$env:OLLAMA_EXTRACT_MODEL = "qwen2.5:3b"  # for extraction
python extractor.py sources/your_book.md
```

### Limit extraction output length (faster)
```powershell
$env:OLLAMA_NUM_PREDICT = "700"  # lower = faster, less verbose
python extractor.py sources/your_book.md
```

### Speed tuning presets
```powershell
# Fast extraction (small model + short output)
$env:OLLAMA_EXTRACT_MODEL = "qwen2.5:3b"
$env:OLLAMA_NUM_PREDICT = "600"

# Balanced extraction
$env:OLLAMA_EXTRACT_MODEL = "qwen2.5:3b"
$env:OLLAMA_NUM_PREDICT = "900"

# Higher quality extraction (slower)
$env:OLLAMA_EXTRACT_MODEL = "qwen2.5:7b"
$env:OLLAMA_NUM_PREDICT = "1200"
```

### Dialogue tuning presets
```powershell
# Fast dialogue (snappier responses)
$env:OLLAMA_MODEL = "qwen2.5:3b"
$env:OLLAMA_NUM_PREDICT = "500"

# Balanced dialogue
$env:OLLAMA_MODEL = "qwen2.5:7b"
$env:OLLAMA_NUM_PREDICT = "900"

# Higher quality dialogue (slower)
$env:OLLAMA_MODEL = "qwen2.5:7b"
$env:OLLAMA_NUM_PREDICT = "1400"
```

Note: `OLLAMA_NUM_PREDICT` applies to both extraction and dialogue unless you
set different values before each run.

### Explore Interactively
```bash
python explorer.py
```

### Socratic GUI
```bash
python gui.py
```

Commands in explorer:
- `1`, `2`, etc. - View a section's extracted knowledge
- `what is X` - Explain a term
- `explain X` - Deep explanation of a concept
- `example X` - Walk through an example
- `prereqs` - What should I know first?
- `summary` - Get summaries at different levels
- `source` - See original text for current section
- `challenge` - Challenge the last answer
- `help` - Show all commands
- `quit` - Exit

## Adding Your Own Sources

1. Add a Markdown file to `sources/`
2. Use `##` headers to mark sections
3. Run `python extractor.py sources/your_file.md`
4. Explore with `python explorer.py`

The system works best with:
- Authoritative, well-structured texts
- Clear section headers
- Formal domains (math, algorithms, law, specifications)

## Using Cloud LLMs (Optional)

If you have API credits:

```python
# In config.py:
LLM_PROVIDER = "openai"   # or "anthropic"
```

Set your API key:
```powershell
$env:OPENAI_API_KEY = "your-key-here"
python extractor.py sources/algorithms_intro.md
```

## The Socratic Method

When exploring, you can challenge any answer:
1. AI gives an explanation
2. You say "challenge: but what about X?"
3. AI re-examines the source text
4. Either corrects itself or provides evidence

This creates a dialogue where truth emerges from the source, not from the model's training data.

## Blueprint Advisor (Socratic App Planning)

The Socratic method also works for deciding **what to build**. The Blueprint Advisor helps you:
- Discover which app blueprint fits your needs
- Identify which features actually matter for your context
- Scope your MVP appropriately

### Run the Blueprint Advisor
```powershell
python blueprint_advisor.py
```

### How It Works
Instead of telling you what to build, the advisor asks questions:

```
You: I want to build an app for tracking what I learn

🎯 Advisor: Interesting! When you say "track what you learn," are you
   thinking about recording notes AS you learn, or reviewing what
   you've learned over time to reinforce it?
```

Through dialogue, you discover:
- Hidden requirements you hadn't considered
- Features you dismissed that are actually essential
- Whether you're over-engineering

### Commands
- `/blueprints` - List all available blueprints
- `/select learning-app` - Jump to a specific blueprint
- `/features` - Focus on feature customization
- `/mvp` - Focus on MVP scoping
- `/stack` - Focus on technical stack selection
- `/quit` - Exit

---

## Why This Works

Traditional chatbots:
```
Question → Model's memory → Answer (may hallucinate)
```

Socratic Learner:
```
Question → Model reads corpus → Answer with citations
```

The corpus IS the knowledge. The model is just a lens.
