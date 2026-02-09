# Task Manager / Todo App Blueprint

> Complete specification for building a task management application.

---

## Core Purpose

Help users **capture, organize, and complete** work — from simple todos to complex projects.

**Key insight:** Task apps fail when they add friction. Every interaction should be fast.
```
Capture → Organize → Work → Complete → Review
```

---

## User Types

| User | Goal | Key Actions |
|------|------|-------------|
| Individual | Manage personal tasks | Quick add, check off, daily planning |
| Knowledge worker | Handle projects with multiple tasks | Organize by project, set deadlines |
| Team member | Coordinate with others | Assign, comment, track progress |
| GTD practitioner | Implement Getting Things Done | Inbox, contexts, weekly review |

---

## Feature Categories

### ✏️ Task Capture
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Quick add (keyboard shortcut) | Zero friction capture | Must have |
| Add task with one click | Basic functionality | Must have |
| Add from anywhere (global hotkey) | Capture without context switch | Nice to have |
| Voice input | Hands-free capture | Nice to have |
| Email to inbox | Capture from email | Nice to have |
| Parse natural language dates | "tomorrow", "next friday" | Should have |
| Templates for recurring tasks | Common patterns | Should have |

### 📋 Task Properties
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Title | What's the task | Must have |
| Description/notes | Details and context | Should have |
| Due date | When it's needed | Must have |
| Priority (high/medium/low) | What matters most | Should have |
| Tags/labels | Cross-project categorization | Should have |
| Project/list assignment | Grouping | Must have |
| Subtasks/checklist | Break down complex tasks | Should have |
| Attachments | Reference files | Nice to have |
| Time estimate | Planning | Nice to have |
| Recurrence | Repeating tasks | Should have |

### 📁 Organization
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Projects/lists | Group related tasks | Must have |
| Folders for projects | Hierarchy | Should have |
| Drag-drop reordering | Manual priority | Must have |
| Filter by status/date/tag | Find tasks | Must have |
| Sort options | Different views | Should have |
| Search tasks | Quick find | Must have |
| Archive completed | Clean workspace | Should have |

### 👁️ Views
| Feature | Why Needed | Priority |
|---------|------------|----------|
| List view | Default, simple | Must have |
| Today view | Focus on now | Must have |
| Upcoming view | See what's coming | Should have |
| Calendar view | Time-based planning | Nice to have |
| Kanban board | Status-based workflow | Should have |
| Project view | All tasks in one project | Must have |

### ⚡ Productivity Features
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Keyboard shortcuts | Speed | Must have |
| Inbox (uncategorized tasks) | Quick capture, organize later | Should have |
| Daily planning | Pick today's tasks | Should have |
| Focus mode | One task at a time | Nice to have |
| Pomodoro timer | Time boxing | Nice to have |
| Habit tracking | Recurring behaviors | Nice to have |

### 🔔 Reminders & Notifications
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Due date reminders | Don't miss deadlines | Should have |
| Custom reminder times | Flexibility | Nice to have |
| Overdue indicators | Visual urgency | Must have |
| Daily digest email | Summary | Nice to have |

### 💾 Data
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Offline support | Works anywhere | Must have |
| Cloud sync | Multi-device | Nice to have |
| Export to JSON/CSV | Data ownership | Should have |
| Undo/redo | Mistake recovery | Should have |

---

## User Flows

### Flow 1: Quick Capture
```
Press "n" or click + → Type task → Press Enter → Task saved to Inbox
```

### Flow 2: Daily Planning
```
Open app → Go to Inbox → Drag tasks to Today → Set priorities → Start working
```

### Flow 3: Complete Task
```
Click checkbox → Task strikes through → Moves to completed → Undo available (5 sec)
```

### Flow 4: Weekly Review
```
Open "All Tasks" → Review each project → Update/delete stale tasks → 
Check completed → Archive old items → Plan next week
```

### Flow 5: Create Project
```
Click "New Project" → Name it → Add tasks → Set deadline (optional) → Track progress
```

---

## Screens/Pages

| Screen | Purpose | Key Components |
|--------|---------|----------------|
| **Inbox** | Unsorted tasks | Task list, quick add, bulk organize |
| **Today** | Focus view | Today's tasks, add to today button |
| **Upcoming** | Future planning | Tasks grouped by date |
| **Project View** | Single project | Tasks, progress bar, description |
| **All Tasks** | Everything | Filters, search, bulk actions |
| **Calendar** | Time-based view | Month/week view, drag to reschedule |
| **Kanban** | Status board | Columns (todo/doing/done), drag cards |
| **Search Results** | Find tasks | Search bar, filtered results |
| **Settings** | Configuration | Theme, notifications, shortcuts |

---

## Data Model

### Task
```
id: string (uuid)
title: string
description: string
status: "todo" | "in-progress" | "completed"
priority: "high" | "medium" | "low" | null
dueDate: timestamp | null
dueTime: string | null
completedAt: timestamp | null
createdAt: timestamp
updatedAt: timestamp
projectId: string | null
tags: string[]
subtasks: Subtask[]
recurrence: RecurrenceRule | null
estimatedMinutes: number | null
order: number  // for manual sorting
```

### Subtask
```
id: string
title: string
completed: boolean
order: number
```

### Project
```
id: string
name: string
description: string
color: string
icon: string | null
folderId: string | null
order: number
archived: boolean
createdAt: timestamp
```

### Folder
```
id: string
name: string
order: number
```

### Tag
```
id: string
name: string
color: string
```

### RecurrenceRule
```
frequency: "daily" | "weekly" | "monthly" | "yearly"
interval: number  // every N days/weeks/etc
daysOfWeek: number[]  // 0-6 for weekly
dayOfMonth: number  // for monthly
endDate: timestamp | null
```

---

## Technical Stack (Recommended)

### Web App
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Frontend | React or Vue | Well-suited for list manipulation |
| Styling | Tailwind CSS | Fast development |
| State | Zustand or Jotai | Simple, handles complex state |
| Drag-Drop | dnd-kit or react-beautiful-dnd | Polished UX |
| Dates | date-fns or dayjs | Lightweight date handling |
| Local Storage | IndexedDB (Dexie) | Offline support |
| Search | Fuse.js | Fuzzy client-side search |

### Desktop
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Framework | Tauri | Lightweight, cross-platform |
| Global Hotkey | Native API | Quick capture from anywhere |

---

## MVP Scope

### What's In
- [ ] Add/edit/delete tasks
- [ ] Mark complete
- [ ] List view with projects
- [ ] Due dates with indicators
- [ ] Priority levels
- [ ] Quick add (keyboard)
- [ ] Inbox / project organization
- [ ] Today view
- [ ] Filter: all, active, completed
- [ ] Search
- [ ] Drag-drop reordering
- [ ] Local storage (persists reload)

### MVP Effort: 1-2 weeks

---

## Full Vision

Everything in MVP plus:
- Subtasks
- Recurrence
- Calendar view
- Kanban board
- Notifications
- Cloud sync
- Collaboration

---

## File Structure

```
task-app/
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── components/
│   │   ├── TaskList/
│   │   │   ├── TaskList.jsx
│   │   │   ├── TaskItem.jsx
│   │   │   └── TaskInput.jsx
│   │   ├── Sidebar/
│   │   │   ├── Sidebar.jsx
│   │   │   ├── ProjectList.jsx
│   │   │   └── ViewLinks.jsx
│   │   ├── Views/
│   │   │   ├── InboxView.jsx
│   │   │   ├── TodayView.jsx
│   │   │   ├── ProjectView.jsx
│   │   │   └── AllTasksView.jsx
│   │   └── common/
│   │       ├── Checkbox.jsx
│   │       ├── DatePicker.jsx
│   │       ├── PriorityBadge.jsx
│   │       └── Modal.jsx
│   ├── stores/
│   │   ├── taskStore.js
│   │   └── projectStore.js
│   ├── hooks/
│   │   ├── useTasks.js
│   │   └── useKeyboard.js
│   └── utils/
│       ├── dateHelpers.js
│       └── parseNaturalDate.js
├── package.json
└── README.md
```

---

## Common Pitfalls

### 1. Slow Rendering with Many Tasks
**Solution:** Virtualize lists. Only render visible items.

### 2. Drag-Drop Bugs
**Solution:** Use a battle-tested library. Don't build custom.

### 3. Date Timezone Issues
**Solution:** Store as UTC, display in local time. Use date-fns.

### 4. Lost Data on Refresh
**Solution:** Persist to IndexedDB on every change, not just on close.

### 5. Keyboard Shortcut Conflicts
**Solution:** Use common conventions (n=new, e=edit, d=done).

### 6. Overcomplicating Early
**Solution:** Ship list + checkbox + projects first. Add features based on actual use.

---

## Implementation Order

```
Week 1:
1. Basic task CRUD (add/edit/delete)
2. Task list rendering
3. Checkbox to complete
4. Projects (can assign task to project)
5. Sidebar with project list
6. Persist to localStorage/IndexedDB

Week 2:
7. Due dates (date picker)
8. Priority levels
9. Today view (filter by due = today)
10. Quick add with keyboard
11. Drag-drop reordering
12. Search
```

---

## Appendix: Code Patterns

### Natural Date Parsing
```javascript
function parseNaturalDate(text) {
  const today = new Date();
  const lower = text.toLowerCase();
  
  if (lower === 'today') return today;
  if (lower === 'tomorrow') {
    return new Date(today.setDate(today.getDate() + 1));
  }
  if (lower.startsWith('next ')) {
    const day = lower.replace('next ', '');
    const days = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday'];
    const targetDay = days.indexOf(day);
    if (targetDay >= 0) {
      const diff = (targetDay - today.getDay() + 7) % 7 || 7;
      return new Date(today.setDate(today.getDate() + diff));
    }
  }
  // Fall back to Date.parse
  return new Date(text);
}
```

### Task Store (Zustand)
```javascript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useTaskStore = create(
  persist(
    (set, get) => ({
      tasks: [],
      
      addTask: (task) => set((state) => ({
        tasks: [...state.tasks, { 
          id: crypto.randomUUID(),
          createdAt: new Date(),
          status: 'todo',
          ...task 
        }]
      })),
      
      toggleComplete: (id) => set((state) => ({
        tasks: state.tasks.map(t => 
          t.id === id 
            ? { ...t, status: t.status === 'completed' ? 'todo' : 'completed', completedAt: new Date() }
            : t
        )
      })),
      
      deleteTask: (id) => set((state) => ({
        tasks: state.tasks.filter(t => t.id !== id)
      })),
      
      getTasksByProject: (projectId) => 
        get().tasks.filter(t => t.projectId === projectId),
      
      getTodayTasks: () => {
        const today = new Date().toDateString();
        return get().tasks.filter(t => 
          t.dueDate && new Date(t.dueDate).toDateString() === today
        );
      }
    }),
    { name: 'tasks' }
  )
);
```
