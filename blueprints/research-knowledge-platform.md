# Research & Knowledge Platform Blueprint

> A complete specification for a research assistant that combines semantic search, knowledge graphs, multi-agent guidance, and Socratic refinement.

---

## Core Purpose

Help users **find, understand, and connect** knowledge across large document collections, while refining their questions through Socratic dialogue.

**Key insight:** Research is not just retrieval. It is iterative question refinement.

```
Ingest -> Index -> Ask -> Refine -> Connect -> Conclude
```

---

## Target Users

| User | Goal | Key Actions |
|------|------|-------------|
| Researcher | Discover related work quickly | Ask questions, refine, build maps |
| Student | Learn a domain efficiently | Guided questions, summaries, evidence |
| Analyst | Synthesize insights | Cross-source links, exports |
| Professional | Stay current | Trend discovery, alerts |

---

## Feature Categories

### Ingestion & Sources
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Upload PDF/TXT/MD | Core corpus input | Must have |
| Batch import folder | Large libraries | Should have |
| Source metadata extraction | Titles/authors/dates | Should have |
| Versioned source updates | Track changes | Nice to have |
| URL import (optional) | Web docs | Nice to have |

### Search & Retrieval
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Semantic search | Meaning > keywords | Must have |
| Keyword search | Precise targeting | Must have |
| Filters (date/type/tag) | Narrow results | Should have |
| Result previews | Fast triage | Must have |
| Saved queries | Repeat research | Nice to have |

### Socratic Refinement
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Clarifying questions | Improve query quality | Must have |
| Assumption detection | Catch flawed premises | Should have |
| Question history | Track refinement | Should have |
| Guided next questions | Keep momentum | Should have |

### Knowledge Graph
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Concept extraction | Build nodes | Must have |
| Relationship linking | Show structure | Should have |
| Graph view | Visual connections | Should have |
| Evidence links | Trace to sources | Must have |
| Export graph data | Reuse outside | Nice to have |

### Summaries & Evidence
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Section summaries | Fast comprehension | Must have |
| Evidence citations | Trustworthy output | Must have |
| Claim verification | Reduce hallucination | Should have |
| Multi-level summaries | Overview vs detail | Should have |

### Multi-Agent Roles
| Agent | Purpose | Priority |
|-------|---------|----------|
| Question Refiner | Socratic probing | Must have |
| Source Scout | Finds related docs | Should have |
| Synthesis Agent | Drafts summaries | Should have |
| Ethics/Scope Checker | Avoid overreach | Nice to have |

### Output & Export
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Export to Markdown | Notes and reports | Must have |
| Export citations | Academic use | Should have |
| Clipboard copy | Quick reuse | Should have |
| Project folders | Organize research | Should have |

---

## User Flows

### Flow 1: New Research Question
```
Import sources -> Ask question -> Socratic refinement -> Search results ->
Open sources -> Summaries + evidence -> Save notes
```

### Flow 2: Explore Connections
```
Search topic -> Build concept graph -> Click node -> View sources ->
Add note -> Export graph
```

### Flow 3: Draft a Report
```
Select sources -> Generate summary -> Verify claims -> Export Markdown
```

---

## Screens/Pages

| Screen | Purpose | Key Components |
|--------|---------|----------------|
| Library | Manage sources | Upload, tags, metadata |
| Search | Query & refine | Query box, filters, results, previews |
| Socratic Dialogue | Question refinement | Chat, assumptions, next prompts |
| Knowledge Graph | Concept map | Graph view, nodes, evidence links |
| Source Viewer | Read sources | Highlighted passages, citations |
| Notes/Export | Final outputs | Outline, citations, export buttons |
| Settings | Configure system | Models, storage, privacy |

---

## Data Model (MVP)

### Source
```
id: string
path: string
title: string
author: string (optional)
created_at: timestamp
tags: string[]
summary: string (optional)
```

### Passage
```
id: string
source_id: string
text: string
embedding: vector (optional)
metadata: {page, section}
```

### Question
```
id: string
text: string
timestamp: timestamp
refinements: string[]
```

### ConceptNode
```
id: string
label: string
description: string
sources: string[]
```

### ConceptEdge
```
from: string
to: string
relation: string
evidence: string[]
```

---

## Technical Stack (Recommended)

**Local-first (recommended):**
- Python backend + local embeddings
- Lightweight UI (Tkinter, Electron, or web)
- Local storage (SQLite + JSON)

**Web:**
- FastAPI + React
- Postgres + vector store

**Local-first implementation (details):**
- Storage: SQLite for sources, passages, questions, notes
- Indexing: chunk passages (200-500 words), store embeddings locally
- Search: BM25 + vector similarity with small-model rerank
- UI: split view for results + source viewer

---

## MVP Scope

**Must ship in v1:**
- Source ingestion (PDF/TXT/MD)
- Semantic + keyword search
- Socratic refinement chat
- Summaries with evidence links
- Export to Markdown

---

## Full Vision

- Full graph visualization
- Multi-agent roles beyond Socratic refiner
- Trend forecasting
- Out of scope: web scraping, visual UI/UX analysis, full web RAG deployment

**Success Criteria:**
- Users can refine questions into a clear research query
- Top 3 results include relevant sources with evidence
- Exported Markdown includes citations
- Average time from question to summary under 2 minutes

**Inspiration Sources:**
- ResearchAI concept (semantic search + Socratic refinement)
- ML Toolbox capability constraints (text analysis focus)
- Intelligent tutoring system principles

---

## File Structure

```
research-platform/
├── app/
│   ├── ui/                # Screens (library, search, dialogue, viewer)
│   ├── services/          # Search, embeddings, summarizer
│   ├── storage/           # SQLite access + migrations
│   └── models/            # Data models
├── data/
│   ├── sources/           # Imported files
│   └── index/             # Embeddings + search index
├── scripts/               # Ingest/index tasks
├── tests/
└── README.md
```

---

## Common Pitfalls

- No citations: users stop trusting the system
- Over-indexing: slow ingest and bloated storage
- Too much context: slow LLM responses
- No question refinement: poor search results
- Slow search: precompute embeddings
- Scope creep: avoid web scraping and visual UI/UX analysis

---

## Implementation Order

1. Ingestion: import files and store metadata
2. Indexing: chunk, embed, and persist search index
3. Search UI: keyword + semantic search with previews
4. Socratic refinement: clarify questions before search
5. Summaries: generate evidence-linked output
6. Export: Markdown + citations
