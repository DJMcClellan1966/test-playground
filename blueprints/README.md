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

### Option A: Scaffold a Project (Fastest Start)

Generate a working project skeleton with one command:

```powershell
cd blueprints
python scaffold.py learning-app --name MyBookTracker --stack flask
```

This creates:
- ✅ Directory structure from the blueprint
- ✅ Model files with fields from Data Model section
- ✅ Main app entry point with starter code
- ✅ Package/requirements file
- ✅ README with next steps

**Available stacks:** flask, fastapi, react, express

```powershell
# List all blueprints
python scaffold.py --list

# Preview without creating files
python scaffold.py task-manager --name QuickTodo --dry-run
```

### Option B: Socratic Blueprint Advisor

Not sure which blueprint to pick? Let the advisor guide you through dialogue:

```powershell
cd projects/socratic-learner
python blueprint_advisor.py
```

The advisor asks questions to help you discover:
- Which blueprint fits your actual needs
- Which features truly matter for your context
- How to scope your MVP appropriately

### Option C: Choose Manually

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

## When You Have AI Access Again

Use it to:
1. Generate new blueprints for app types not listed
2. Expand existing blueprints with more detail
3. Create actual code from these specs
4. Debug issues you hit during implementation

**The goal:** These blueprints let you make real progress without AI. Then use AI time strategically.
