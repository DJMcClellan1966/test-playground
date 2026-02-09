# Learning App Blueprint

> A complete specification for building a learning application with book/content corpus.

---

## Core Purpose

Help users **learn and retain** information from a collection of documents, books, or educational content.

**Key insight:** Reading is not learning. The app must support the full cycle:
```
Import → Read → Mark → Review → Remember → Apply
```

---

## User Types

| User | Goal | Key Actions |
|------|------|-------------|
| Self-learner | Master topics independently | Import books, take notes, review |
| Student | Study for courses/exams | Highlight key points, create flashcards, quiz self |
| Professional | Stay current in field | Read technical content, extract insights |
| Researcher | Connect ideas across sources | Search, cross-reference, export citations |

---

## Feature Categories

### 📥 Content Import
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Upload PDF files | Most common book format | Must have |
| Upload EPUB files | Standard ebook format | Should have |
| Upload TXT/Markdown | Simple notes, articles | Must have |
| Drag-and-drop upload | Ease of use | Must have |
| Bulk import folder | Speed for large libraries | Nice to have |
| Import from URL | Web articles, docs | Nice to have |
| Auto-detect chapters | Structure navigation | Should have |
| Extract table of contents | Quick navigation | Should have |
| OCR for scanned PDFs | Some books are images | Nice to have |

### 📖 Reading Experience
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Clean reader view | Focus on content | Must have |
| Page/scroll navigation | Basic reading | Must have |
| Progress bar/percentage | Know where you are | Must have |
| Remember reading position | Resume later | Must have |
| Adjustable font size | Accessibility | Must have |
| Adjustable line spacing | Readability | Should have |
| Dark/light/sepia themes | Eye comfort | Must have |
| Full-screen mode | Distraction-free | Should have |
| Keyboard shortcuts | Power users | Should have |
| Two-column view (wide screens) | Better reading ergonomics | Nice to have |
| Table of contents sidebar | Navigation | Must have |

### ✏️ Annotation Tools
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Highlight text (multiple colors) | Mark important passages | Must have |
| Add note to highlight | Capture thoughts | Must have |
| View all highlights (per book) | Review marked content | Must have |
| View all highlights (global) | Cross-book review | Should have |
| Bookmark pages | Quick return points | Should have |
| Copy text with citation | Academic use | Nice to have |
| Export highlights/notes | External use, backup | Must have |
| Export to Markdown | Common format | Should have |
| Export to Anki format | Flashcard apps | Nice to have |

### 🔍 Search & Discovery
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Search within current book | Find specific content | Must have |
| Search across all books | "Where did I read X?" | Must have |
| Search within notes | Find your own thoughts | Should have |
| Filter by book/tag/date | Narrow results | Should have |
| Recent searches | Quick re-access | Nice to have |
| "Similar passages" | Connect ideas | Nice to have |

### 🧠 Learning & Retention
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Convert highlight to flashcard | Active recall | Should have |
| Manual flashcard creation | Custom learning | Should have |
| Spaced repetition scheduling | Optimal review timing | Should have |
| Daily review queue | "What to review today" | Should have |
| Quiz mode (from highlights) | Test yourself | Nice to have |
| Track review stats | Monitor retention | Nice to have |
| Forgetting curve visualization | Motivation | Nice to have |

### 📚 Library Management
| Feature | Why Needed | Priority |
|---------|------------|----------|
| List all books | Basic organization | Must have |
| Book cover thumbnails | Visual recognition | Should have |
| Sort by title/author/date | Find books | Must have |
| Tag/categorize books | Personal organization | Should have |
| Collections/shelves | Group related books | Should have |
| Reading status (to-read/reading/done) | Track progress | Should have |
| Delete books | Cleanup | Must have |
| Edit book metadata | Fix incorrect info | Should have |

### 📊 Progress & Stats
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Reading progress per book | Know where you are | Must have |
| Total books completed | Motivation | Should have |
| Reading streak | Habit building | Nice to have |
| Time spent reading | Awareness | Nice to have |
| Highlights count | Engagement metric | Nice to have |
| Weekly/monthly summary | Reflection | Nice to have |

### 💾 Data & Sync
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Offline access | Read anywhere | Must have |
| Local data storage | Privacy, speed | Must have |
| Export all data | User ownership | Must have |
| Import library backup | Recovery, migration | Should have |
| Cloud sync (optional) | Multi-device | Nice to have |

---

## User Flows

### Flow 1: First-Time Setup
```
Open app → Welcome screen → Import first book → Auto-detect structure → 
Show in library → Open to read → Tutorial overlay (optional)
```

### Flow 2: Daily Reading
```
Open app → See "Continue Reading" → Resume book → Read → Highlight passage → 
Add note (optional) → Continue → Close (auto-save position)
```

### Flow 3: Study Session
```
Open app → Go to Reviews → See today's cards → Flip card → Mark known/unknown → 
Complete session → See stats
```

### Flow 4: Find Something
```
Open app → Press Cmd/Ctrl+F → Type query → See results across books → 
Click result → Jump to location in context
```

### Flow 5: Export Notes
```
Open book → View highlights → Select "Export" → Choose format → 
Download file / Copy to clipboard
```

---

## Screens/Pages

| Screen | Purpose | Key Components |
|--------|---------|----------------|
| **Library** | Browse/manage all books | Book grid/list, search, sort, filters, add book button |
| **Reader** | Read book content | Content area, TOC sidebar, highlight tools, progress bar |
| **Highlights** | View/manage annotations | List of highlights, filter by book/color, export button |
| **Flashcards** | Create/edit cards | Card list, add new, edit form |
| **Review** | Spaced repetition session | Card display, flip button, rating buttons, progress |
| **Search Results** | Find across library | Search input, filtered results, click to navigate |
| **Book Detail** | Metadata and stats | Cover, title, author, progress, highlights count, open/delete |
| **Settings** | App configuration | Theme, font size, export, account (if any) |
| **Stats** | Reading analytics | Charts, streaks, totals |

---

## Data Model

### Book
```
id: string (uuid)
title: string
author: string (optional)
filepath: string
filetype: "pdf" | "epub" | "txt" | "md"
cover: string (path or base64)
dateAdded: timestamp
lastOpened: timestamp
readingPosition: { page/percent/chapter }
status: "to-read" | "reading" | "completed"
tags: string[]
collectionId: string (optional)
metadata: { pageCount, wordCount, ... }
```

### Highlight
```
id: string
bookId: string
text: string
note: string (optional)
color: "yellow" | "green" | "blue" | "pink"
location: { page, startOffset, endOffset }
createdAt: timestamp
```

### Flashcard
```
id: string
bookId: string (optional - can be standalone)
highlightId: string (optional - if generated from highlight)
front: string
back: string
nextReviewDate: timestamp
interval: number (days)
easeFactor: number
reviewCount: number
```

### Collection
```
id: string
name: string
description: string
bookIds: string[]
createdAt: timestamp
```

### ReviewSession
```
id: string
date: timestamp
cardsReviewed: number
correctCount: number
duration: number (seconds)
```

---

## Technical Stack (Recommended)

### For Web App (Fastest to Build)
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Frontend | React or Svelte | Component-based, good ecosystem |
| Styling | Tailwind CSS | Fast, consistent, responsive |
| PDF Rendering | PDF.js | Mozilla's free library |
| EPUB Rendering | epub.js | Standard library |
| Local Storage | IndexedDB (via Dexie.js) | Large file support |
| State Management | Zustand or Context | Simple, sufficient |
| Search | FlexSearch | Fast client-side search |
| Spaced Repetition | Custom or SM-2 algorithm | Well-documented |
| Build Tool | Vite | Fast, modern |

### For Desktop App (If Needed)
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Framework | Tauri or Electron | Cross-platform |
| File System | Native fs access | Better file handling |
| Database | SQLite (via better-sqlite3) | Robust, local |

### For Mobile (Later)
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Framework | React Native or Capacitor | Share web code |

---

## MVP Scope (Build This First)

### What's In
- [ ] Upload PDF/TXT files
- [ ] Basic reader with navigation
- [ ] Progress tracking (% complete)
- [ ] Resume reading position
- [ ] Highlight text (single color)
- [ ] Add notes to highlights
- [ ] View highlights list
- [ ] Export highlights as Markdown
- [ ] Full-text search (current book)
- [ ] Library view with all books
- [ ] Dark/light theme

### What's Out (For Now)
- EPUB support
- Spaced repetition
- Flashcards
- Cloud sync
- Stats/analytics
- Collections
- Multi-device

### MVP Effort Estimate
**2-3 focused weeks** for a working prototype

---

## Full Vision (Eventually)

Everything in MVP plus:
- All file formats (EPUB, web articles)
- Spaced repetition with flashcards
- Cross-book search
- Collections and tags
- Reading statistics
- Cloud backup/sync
- Mobile companion app
- AI summarization (optional)
- Offline-first PWA

---

## File Structure

```
learning-app/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── main.jsx                 # App entry point
│   ├── App.jsx                  # Root component, routing
│   ├── components/
│   │   ├── Library/
│   │   │   ├── LibraryView.jsx  # Book grid/list
│   │   │   ├── BookCard.jsx     # Single book preview
│   │   │   └── ImportButton.jsx # Upload handler
│   │   ├── Reader/
│   │   │   ├── ReaderView.jsx   # Main reader
│   │   │   ├── PDFRenderer.jsx  # PDF display
│   │   │   ├── TextRenderer.jsx # TXT/MD display
│   │   │   ├── HighlightLayer.jsx
│   │   │   ├── TOCSidebar.jsx
│   │   │   └── ProgressBar.jsx
│   │   ├── Highlights/
│   │   │   ├── HighlightList.jsx
│   │   │   ├── HighlightCard.jsx
│   │   │   └── ExportButton.jsx
│   │   ├── Search/
│   │   │   ├── SearchBar.jsx
│   │   │   └── SearchResults.jsx
│   │   └── common/
│   │       ├── Button.jsx
│   │       ├── Modal.jsx
│   │       └── ThemeToggle.jsx
│   ├── hooks/
│   │   ├── useBooks.js          # Book CRUD operations
│   │   ├── useHighlights.js     # Highlight management
│   │   ├── useReader.js         # Reading state
│   │   └── useSearch.js         # Search functionality
│   ├── stores/
│   │   ├── bookStore.js         # Library state
│   │   ├── readerStore.js       # Current reading state
│   │   └── settingsStore.js     # User preferences
│   ├── services/
│   │   ├── fileParser.js        # PDF/TXT parsing
│   │   ├── database.js          # IndexedDB operations
│   │   ├── search.js            # Search indexing
│   │   └── export.js            # Export functionality
│   ├── utils/
│   │   ├── formatters.js
│   │   └── constants.js
│   └── styles/
│       └── globals.css
├── package.json
├── vite.config.js
├── tailwind.config.js
└── README.md
```

---

## Common Pitfalls

### 1. PDF Rendering Complexity
**Problem:** PDFs are hard. Text selection, page rendering, different PDF versions.
**Solution:** Use PDF.js and accept some limitations. Don't try to build from scratch.

### 2. Large Files Crashing Browser
**Problem:** 500+ page PDFs can freeze the app.
**Solution:** Lazy load pages. Only render visible content. Use virtualization.

### 3. Losing User Data
**Problem:** User highlights disappear on reload.
**Solution:** Save to IndexedDB immediately on change. Test persistence early.

### 4. Highlight Position Breaking
**Problem:** Highlight coordinates don't match after resize or format change.
**Solution:** Store character offsets, not pixel positions. Recalculate on render.

### 5. Search Being Slow
**Problem:** Searching 50 books takes forever.
**Solution:** Build search index on import, not on search. Use FlexSearch or similar.

### 6. Scope Creep
**Problem:** Adding features before basics work.
**Solution:** Build MVP first. Each feature should ship working before starting next.

### 7. No Offline Support
**Problem:** App breaks without internet.
**Solution:** Make it local-first from day one. Network is optimization, not requirement.

---

## Implementation Order

Build in this sequence for fastest working app:

```
Week 1:
1. Project setup (Vite + React + Tailwind)
2. File upload (PDF only first)
3. Basic PDF reader (navigate pages)
4. Library view (list uploaded books)

Week 2:
5. Reading progress & resume position
6. Text selection + highlighting
7. Save highlights to IndexedDB
8. Highlight list view

Week 3:
9. Notes on highlights
10. Export highlights to Markdown
11. Search within book
12. Dark mode / theme switching
13. Polish & bug fixes
```

---

## You Can Build This Without AI

This blueprint gives you:
- Every feature to consider
- What to build first
- File structure to follow
- Code patterns to use
- Pitfalls to avoid
- Step-by-step order

Work through it methodically. When stuck, search for "[specific problem] [your framework]" — most issues have Stack Overflow answers.

---

## Appendix: Code Patterns

### Basic PDF.js Setup
```javascript
import * as pdfjsLib from 'pdfjs-dist';

pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';

async function loadPDF(file) {
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  return pdf;
}

async function renderPage(pdf, pageNum, canvas) {
  const page = await pdf.getPage(pageNum);
  const viewport = page.getViewport({ scale: 1.5 });
  canvas.height = viewport.height;
  canvas.width = viewport.width;
  
  await page.render({
    canvasContext: canvas.getContext('2d'),
    viewport: viewport
  }).promise;
}
```

### IndexedDB with Dexie
```javascript
import Dexie from 'dexie';

const db = new Dexie('LearningApp');

db.version(1).stores({
  books: '++id, title, author, dateAdded',
  highlights: '++id, bookId, createdAt',
  flashcards: '++id, bookId, nextReviewDate'
});

// Add a book
await db.books.add({ title: 'My Book', author: 'Someone', dateAdded: new Date() });

// Get all highlights for a book
const highlights = await db.highlights.where('bookId').equals(bookId).toArray();
```

### Simple SM-2 Spaced Repetition
```javascript
function calculateNextReview(card, quality) {
  // quality: 0-5 (0=complete fail, 5=perfect)
  let { interval, easeFactor, reviewCount } = card;
  
  if (quality < 3) {
    // Failed - reset
    interval = 1;
    reviewCount = 0;
  } else {
    // Passed
    if (reviewCount === 0) interval = 1;
    else if (reviewCount === 1) interval = 6;
    else interval = Math.round(interval * easeFactor);
    
    reviewCount++;
  }
  
  // Adjust ease factor
  easeFactor = Math.max(1.3, easeFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)));
  
  const nextReviewDate = new Date();
  nextReviewDate.setDate(nextReviewDate.getDate() + interval);
  
  return { interval, easeFactor, reviewCount, nextReviewDate };
}
```

