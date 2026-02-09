# Intent Amplification: Learning App with Book Corpus

**Original Request:** "A learning app with a corpus of books"

**Amplified Specification v1.0**

---

## What This App Actually Needs To Do

### Core Purpose
A person has books they want to learn from. They need to:
- Access the content easily
- Remember what they've read
- Find specific information later
- Track their learning progress
- Actually retain knowledge (not just read)

---

## Inferred Features (The "Obvious" Stuff)

### 📚 Content Management
| Feature | Why It's Obvious |
|---------|------------------|
| Import books (PDF, EPUB, TXT, MD) | You said "corpus of books" — need to get them in |
| Automatic chapter/section detection | Nobody wants one giant wall of text |
| Table of contents generation | Users need to navigate |
| Full-text search across all books | "Where did I read that thing about X?" |
| Book metadata (title, author, tags) | Organization becomes necessary at scale |

### 📖 Reading Experience
| Feature | Why It's Obvious |
|---------|------------------|
| Clean, distraction-free reader | Primary way to interact with content |
| Adjustable font size/theme | Accessibility and preference |
| Dark mode | Eye strain is real |
| Progress indicator (% complete) | "Where am I in this?" |
| Resume where you left off | No one finishes books in one sitting |
| Keyboard navigation | Power users expect this |

### ✏️ Active Learning Tools
| Feature | Why It's Obvious |
|---------|------------------|
| Highlight text | Mark important passages |
| Add notes to highlights | Capture thoughts in context |
| Export highlights + notes | Studying, reference, sharing |
| Bookmark pages/sections | Quick return to key spots |
| Look up word definitions | Unknown vocabulary happens |

### 🧠 Retention & Review
| Feature | Why It's Obvious |
|---------|------------------|
| Spaced repetition for highlights | "Learning" means remembering |
| Auto-generate flashcards from highlights | Low-effort review creation |
| Quiz mode from content | Active recall beats passive reading |
| Review dashboard | "What should I review today?" |
| Forgetting curve visualization | Motivation to review |

### 📊 Progress & Analytics
| Feature | Why It's Obvious |
|---------|------------------|
| Reading time tracking | Know your habits |
| Books completed / in progress | Sense of accomplishment |
| Streak tracking | Habit building |
| Highlights per book | Engagement metric |
| Words read / pages per session | Quantified progress |

### 🔍 Discovery & Organization
| Feature | Why It's Obvious |
|---------|------------------|
| Tag/categorize books | Personal taxonomy |
| Collections/shelves | Group related books |
| "Related passages" across books | Connect ideas |
| Search within notes | Find your own thoughts |

### 💾 Data & Sync
| Feature | Why It's Obvious |
|---------|------------------|
| Offline access | Read anywhere |
| Cloud backup | Don't lose progress |
| Export all data | User owns their data |
| Import/export library | Move between devices |

---

## What's NOT Obvious (Need Your Input)

### A. Social Features?
- [ ] Share highlights publicly?
- [ ] Discussion forums per book?
- [ ] See what others highlighted?
- [ ] Reading groups?

### B. AI Enhancements?
- [ ] Summarize chapters automatically?
- [ ] Generate questions from content?
- [ ] "Explain this passage" feature?
- [ ] Find similar books/passages?

### C. Platform?
- [ ] Web app (works everywhere)
- [ ] Desktop app (Windows/Mac)
- [ ] Mobile app (iOS/Android)
- [ ] All of the above?

### D. Content Source?
- [ ] Only your own books (upload)?
- [ ] Connect to public domain libraries?
- [ ] Integration with Kindle/Kobo highlights?

### E. Primary Use Case?
- [ ] Academic study (textbooks, papers)
- [ ] Professional development (technical books)
- [ ] Personal growth (self-help, philosophy)
- [ ] Mixed / General purpose

---

## Technical Decisions (Need Input)

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Where does data live? | Local only / Cloud / Hybrid | Hybrid (local-first + optional sync) |
| User accounts? | Required / Optional / None | Optional (works offline, sync if wanted) |
| Book storage | In-app DB / File system / Cloud | File system + indexed metadata |
| Tech stack | Electron / Tauri / Web / Native | Web (fastest to prototype) |

---

## MVP vs Full Vision

### Phase 1: Minimum Lovable Product (2-3 weeks)
1. Import PDF/TXT/MD files
2. Clean reader with progress tracking
3. Highlighting + notes
4. Full-text search
5. Resume reading position
6. Export highlights

### Phase 2: Learning Layer (2-3 weeks)
1. Spaced repetition system
2. Flashcard generation
3. Review dashboard
4. Basic quiz mode

### Phase 3: Polish (2-3 weeks)
1. Better import (EPUB, more formats)
2. Cloud sync
3. Collections/tags
4. Analytics dashboard
5. Mobile-friendly

---

## What Would a Basic AI Generate?

```
- Homepage with book list
- Upload button
- Basic text display
- Maybe a search bar
```

That's it. No progress, no notes, no search, no learning features, no retention, no export. You'd have to ask for each piece individually.

---

## Your Turn

1. **What did I get wrong?** (Features you don't want)
2. **What did I miss?** (Features you expected)
3. **What's most important to you?** (Prioritization)
4. **Answer the "Not Obvious" questions above**

Then we build.
