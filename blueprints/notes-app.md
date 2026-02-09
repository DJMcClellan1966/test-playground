# Note-Taking App Blueprint

> Complete specification for building a personal notes application.

---

## Core Purpose

Help users **capture, organize, and retrieve** thoughts, ideas, and information quickly.

**Key insight:** Notes are useless if you can't find them. Search and structure are as important as capture.
```
Capture → Organize → Find → Use
```

---

## User Types

| User | Goal | Key Actions |
|------|------|-------------|
| Student | Capture class notes | Write, organize, search |
| Knowledge worker | Track ideas | Tag, link, review |
| Writer | Draft content | Organize by project |
| Personal user | Daily notes | Quick capture, search |

---

## Feature Categories

### ✏️ Note Creation
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Create new note (instant) | Zero friction | Must have |
| Rich text editor | Formatting | Must have |
| Markdown support | Power users | Should have |
| Auto-save | Never lose work | Must have |
| Undo/redo | Mistake recovery | Must have |
| Keyboard shortcuts | Speed | Should have |
| Note templates | Common patterns | Nice to have |

### 📝 Content Features
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Headings | Structure | Must have |
| Bold/italic/underline | Emphasis | Must have |
| Bullet lists | Enumeration | Must have |
| Numbered lists | Sequences | Must have |
| Checkboxes | Todo items | Should have |
| Links (internal) | Connect notes | Should have |
| Links (external) | Reference URLs | Must have |
| Code blocks | Technical notes | Should have |
| Images | Visual notes | Should have |
| Tables | Structured data | Nice to have |
| Embeds (video, etc) | Rich content | Nice to have |

### 📁 Organization
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Folders/notebooks | Hierarchy | Should have |
| Tags | Cross-cutting categories | Should have |
| Favorites/starred | Quick access | Should have |
| Recent notes | Continue work | Must have |
| Drag-drop organization | Easy sorting | Should have |
| Archive notes | Clean up without delete | Should have |
| Trash/restore | Recovery | Should have |

### 🔍 Search & Find
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Full-text search | Find anything | Must have |
| Search in titles | Quick filter | Must have |
| Filter by tag/folder | Narrow scope | Should have |
| Sort by date/title | Order results | Should have |
| Search highlights | See matches | Should have |

### 💾 Data & Sync
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Offline support | Works anywhere | Must have |
| Local storage | Privacy, speed | Must have |
| Export notes (MD, PDF) | Data portability | Should have |
| Import from other apps | Migration | Nice to have |
| Cloud sync | Multi-device | Nice to have |
| Backup/restore | Peace of mind | Should have |

### 🎨 Experience
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Dark/light theme | Comfort | Should have |
| Distraction-free mode | Focus | Nice to have |
| Custom fonts | Preference | Nice to have |
| Split view (list + editor) | Navigation | Should have |

---

## User Flows

### Flow 1: Quick Capture
```
Press Cmd+N (or click +) → Cursor in title → Type title → 
Tab to body → Write → Auto-saves
```

### Flow 2: Find a Note
```
Press Cmd+K (or click search) → Type query → See results → 
Click to open → Edit if needed
```

### Flow 3: Organize Notes
```
Select note → Drag to folder OR Add tag → Note organized → 
Visible in folder/tag view
```

### Flow 4: Export
```
Open note → Click menu → Export as Markdown → Save file
```

---

## Screens/Pages

| Screen | Purpose | Key Components |
|--------|---------|----------------|
| **Main View** | Primary interface | Sidebar + Note list + Editor |
| **Sidebar** | Navigation | Folders, tags, favorites, trash |
| **Note List** | Browse notes | Note previews, sort, filter |
| **Editor** | Write/edit | Toolbar, content area |
| **Search** | Find notes | Search bar, results list |
| **Settings** | Configuration | Theme, export, account |

---

## Data Model

### Note
```
id: string (uuid)
title: string
content: string (markdown or HTML)
createdAt: timestamp
updatedAt: timestamp
folderId: string | null
tags: string[]
favorite: boolean
archived: boolean
trashed: boolean
trashedAt: timestamp | null
```

### Folder
```
id: string
name: string
parentId: string | null  # for nested folders
order: number
color: string | null
```

### Tag
```
id: string
name: string
color: string
```

---

## Technical Stack (Recommended)

### Web App
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Frontend | React or Svelte | Component-based |
| Editor | TipTap or Lexical | Modern rich text |
| Markdown | remark/rehype | Parsing/rendering |
| Storage | IndexedDB (Dexie) | Large local storage |
| Search | FlexSearch or MiniSearch | Fast client-side |
| Styling | Tailwind | Quick development |

### Desktop
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Framework | Tauri | Lightweight, file access |
| Storage | SQLite | Robust local DB |

---

## MVP Scope

### What's In
- [ ] Create/edit/delete notes
- [ ] Rich text editor (basic formatting)
- [ ] Auto-save
- [ ] Note list sidebar
- [ ] Full-text search
- [ ] Folders (one level)
- [ ] Tags
- [ ] Favorites
- [ ] Dark/light theme
- [ ] Local storage (persists)

### MVP Effort: 1-2 weeks

---

## Full Vision

Everything in MVP plus:
- Nested folders
- Cloud sync
- Images
- Tables
- Export
- Trash

---

## File Structure

```
notes-app/
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Sidebar.jsx
│   │   │   └── MainContent.jsx
│   │   ├── Notes/
│   │   │   ├── NoteList.jsx
│   │   │   ├── NoteListItem.jsx
│   │   │   └── NoteEditor.jsx
│   │   ├── Editor/
│   │   │   ├── RichTextEditor.jsx
│   │   │   └── Toolbar.jsx
│   │   ├── Organization/
│   │   │   ├── FolderTree.jsx
│   │   │   └── TagList.jsx
│   │   └── common/
│   │       ├── SearchBar.jsx
│   │       └── Modal.jsx
│   ├── stores/
│   │   ├── noteStore.js
│   │   └── uiStore.js
│   ├── services/
│   │   ├── database.js
│   │   └── search.js
│   └── utils/
│       └── markdown.js
├── package.json
└── README.md
```

---

## Common Pitfalls

### 1. Slow with Many Notes
**Solution:** Virtualize note list. Index for search on save, not on search.

### 2. Editor Losing Focus
**Solution:** Manage focus state carefully. Don't re-render editor unnecessarily.

### 3. Content Not Saving
**Solution:** Debounce auto-save (500ms). Save to IndexedDB immediately.

### 4. Search Too Slow  
**Solution:** Build search index incrementally. Use dedicated search library.

### 5. Folder/Tag UI Confusing
**Solution:** Keep it simple. One level of folders is enough for MVP.

---

## Implementation Order

```
Week 1:
1. Project setup
2. Basic layout (sidebar + content)
3. Note CRUD (create, read, update, delete)
4. Simple text editor (no formatting first)
5. Note list with selection
6. Local storage persistence
7. Full-text search

Week 2:
8. Rich text editor (TipTap)
9. Formatting toolbar
10. Folders
11. Tags
12. Favorites
13. Theme toggle
14. Polish
```

---

## Appendix: Code Patterns

### TipTap Editor Setup
```jsx
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';

function NoteEditor({ note, onChange }) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: 'Start writing...'
      })
    ],
    content: note.content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    }
  });

  return (
    <div className="prose max-w-none">
      <input 
        type="text"
        value={note.title}
        onChange={(e) => onChange({ title: e.target.value })}
        className="text-2xl font-bold w-full border-none outline-none mb-4"
        placeholder="Untitled"
      />
      <EditorContent editor={editor} />
    </div>
  );
}
```

### Debounced Auto-Save
```javascript
import { useMemo, useEffect } from 'react';
import { debounce } from 'lodash-es';

function useAutoSave(note, saveNote) {
  const debouncedSave = useMemo(
    () => debounce((note) => {
      saveNote({ ...note, updatedAt: new Date() });
    }, 500),
    [saveNote]
  );
  
  useEffect(() => {
    if (note) {
      debouncedSave(note);
    }
    return () => debouncedSave.cancel();
  }, [note, debouncedSave]);
}
```

### Search Index (FlexSearch)
```javascript
import FlexSearch from 'flexsearch';

const index = new FlexSearch.Document({
  document: {
    id: 'id',
    index: ['title', 'content'],
    store: ['title', 'updatedAt']
  }
});

// Add notes to index
function indexNote(note) {
  index.add(note);
}

// Search
function searchNotes(query) {
  const results = index.search(query, { enrich: true });
  return results.flatMap(r => r.result);
}

// Remove from index
function removeFromIndex(noteId) {
  index.remove(noteId);
}
```

### Note Store (Zustand + Dexie)
```javascript
import { create } from 'zustand';
import { db } from './database';

const useNoteStore = create((set, get) => ({
  notes: [],
  currentNoteId: null,
  
  loadNotes: async () => {
    const notes = await db.notes.toArray();
    set({ notes });
  },
  
  createNote: async () => {
    const note = {
      id: crypto.randomUUID(),
      title: 'Untitled',
      content: '',
      createdAt: new Date(),
      updatedAt: new Date(),
      folderId: null,
      tags: [],
      favorite: false,
      archived: false
    };
    await db.notes.add(note);
    set(state => ({ 
      notes: [note, ...state.notes],
      currentNoteId: note.id 
    }));
    return note;
  },
  
  updateNote: async (id, updates) => {
    const updated = { ...updates, updatedAt: new Date() };
    await db.notes.update(id, updated);
    set(state => ({
      notes: state.notes.map(n => 
        n.id === id ? { ...n, ...updated } : n
      )
    }));
  },
  
  deleteNote: async (id) => {
    await db.notes.delete(id);
    set(state => ({
      notes: state.notes.filter(n => n.id !== id),
      currentNoteId: state.currentNoteId === id ? null : state.currentNoteId
    }));
  },
  
  getCurrentNote: () => {
    return get().notes.find(n => n.id === get().currentNoteId);
  }
}));
```
