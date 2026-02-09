# Building Apps Without AI: A Practical Guide

> How to use these blueprints and develop apps independently when AI help isn't available.

---

## The Mindset Shift

When AI isn't available, you become the architect. That's okay — developers built amazing things for decades before AI. The key is:

1. **Plan before coding** — The blueprints give you the plan
2. **Search for solutions** — Most problems are already solved
3. **Build incrementally** — Small working pieces, not big broken ones
4. **Learn patterns** — Same problems recur; learn the solutions

---

## Your Development Workflow

### Phase 1: Understand What You're Building

1. **Pick the closest blueprint** for your app idea
2. **Read the Core Purpose** — Make sure it matches your goal
3. **Customize the feature list:**
   - ✅ Check features you need
   - ❌ Cross out features you don't
   - ➕ Add any specific to your use case
4. **Identify MVP scope** — What's the minimum to make it useful?

### Phase 2: Set Up Your Project

1. **Choose your stack** (see blueprint recommendations)
2. **Create project structure** (follow the file structure template)
3. **Install dependencies** (README should list them)
4. **Get "Hello World" running** — Verify setup works before building features

### Phase 3: Build Feature by Feature

Follow the **Implementation Order** in each blueprint. For each feature:

```
1. Create the component/file
2. Get it rendering (even with dummy data)
3. Add the logic (handlers, state)
4. Connect to data layer
5. Test it works
6. Move to next feature
```

**Rule:** Don't start feature 2 until feature 1 works.

### Phase 4: Handle Problems

When stuck:
1. Read the error message carefully
2. Search: `[error message] [technology]`
3. Check Stack Overflow
4. Check official docs
5. Reduce scope if needed

---

## How to Google Effectively

| What You Want | Search Query Pattern |
|---------------|---------------------|
| How to do X | "how to [action] in [technology]" |
| Error fix | "[exact error message] [technology]" |
| Best practice | "[thing] best practices [technology]" |
| Library docs | "[library name] documentation" |
| Code example | "[what you want] example [technology]" |
| Comparison | "[option A] vs [option B]" |

### Examples
- `how to highlight text in PDF.js`
- `"cannot read property of undefined" React`
- `React state management best practices 2024`
- `Zustand persist middleware example`
- `IndexedDB vs localStorage`

---

## Essential Resources (Bookmark These)

### General
| Resource | What It's For |
|----------|---------------|
| [MDN Web Docs](https://developer.mozilla.org) | HTML, CSS, JavaScript reference |
| [Stack Overflow](https://stackoverflow.com) | Q&A for specific problems |
| [Dev.to](https://dev.to) | Tutorials and articles |

### React
| Resource | What It's For |
|----------|---------------|
| [React Docs](https://react.dev) | Official documentation |
| [React Patterns](https://reactpatterns.com) | Common patterns |

### Styling
| Resource | What It's For |
|----------|---------------|
| [Tailwind Docs](https://tailwindcss.com/docs) | Class reference |
| [Tailwind UI](https://tailwindui.com) | Component examples |
| [CSS Tricks](https://css-tricks.com) | CSS help |

### Node/Backend
| Resource | What It's For |
|----------|---------------|
| [Express Docs](https://expressjs.com) | Express reference |
| [Prisma Docs](https://www.prisma.io/docs) | Database ORM |

### Tools
| Resource | What It's For |
|----------|---------------|
| [npm](https://www.npmjs.com) | Find packages |
| [Bundlephobia](https://bundlephobia.com) | Check package size |
| [Can I Use](https://caniuse.com) | Browser compatibility |

---

## Problem-Solving Patterns

### "It's not rendering"
1. Check console for errors
2. Verify component is imported
3. Check if data exists (console.log it)
4. Check conditional rendering logic
5. Verify parent is rendering

### "State isn't updating"
1. Are you mutating state directly? (Don't)
2. Is the update async? (Use useEffect)
3. Are you spreading the old state?
4. Check if component is re-rendering (console.log in component)

### "Style isn't applying"
1. Check class name spelling
2. Check CSS specificity
3. Inspect element in dev tools
4. Check if Tailwind class exists

### "Data isn't persisting"
1. Check if save function is called (console.log)
2. Check localStorage/IndexedDB in dev tools
3. Verify the key matches on read/write
4. Check for async timing issues

### "API isn't working"
1. Check network tab in dev tools
2. Is the URL correct?
3. Check request/response in network tab
4. Is CORS blocking you?
5. Check error response body

---

## Learning Strategy

### When You Have Time
1. **Build small things** — Todo app, counter, timer
2. **Read framework docs** — Focus on concepts, not API details
3. **Study working code** — GitHub examples, open source
4. **Watch updated tutorials** — Make sure they're recent (last 1-2 years)

### While Building
1. **Understand before copying** — Why does this code work?
2. **Modify examples** — Change things, see what breaks
3. **Read error messages** — They usually tell you what's wrong
4. **Keep notes** — Save solutions to problems you solve

### Concepts Worth Mastering

| Frontend | Backend |
|----------|---------|
| Component lifecycle | Request/response cycle |
| State management | Authentication/authorization |
| Event handling | Database operations |
| Async/await | Error handling |
| Array methods (map, filter, etc) | Validation |
| CSS layout (flexbox, grid) | REST API design |

---

## When to Simplify

Signs you should reduce scope:
- Feature is taking way longer than expected
- You don't understand what you're building
- The problem requires technology you don't know
- You're adding "nice to haves" before "must haves"

**Simplification tactics:**
- Use a simpler library (or none)
- Skip the edge cases for now
- Hardcode what could be dynamic
- Use local storage instead of a database
- Skip the backend (use local-first)
- Remove the feature entirely

---

## Local Development Survival Kit

### Packages You'll Reuse

```json
{
  "dependencies": {
    "react": "^18.x",
    "react-dom": "^18.x",
    "zustand": "^4.x",
    "dexie": "^4.x",
    "date-fns": "^3.x"
  },
  "devDependencies": {
    "vite": "^5.x",
    "tailwindcss": "^3.x"
  }
}
```

### Project Starter Command
```bash
npm create vite@latest my-app -- --template react
cd my-app
npm install
npm install zustand dexie date-fns
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### File Templates

**Basic React Component:**
```jsx
export function MyComponent({ prop1, prop2 }) {
  return (
    <div>
      {/* content */}
    </div>
  );
}
```

**Zustand Store:**
```javascript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useStore = create(
  persist(
    (set, get) => ({
      items: [],
      addItem: (item) => set((state) => ({
        items: [...state.items, item]
      })),
      // more actions
    }),
    { name: 'my-store' }
  )
);

export default useStore;
```

**Dexie Database:**
```javascript
import Dexie from 'dexie';

export const db = new Dexie('MyDatabase');

db.version(1).stores({
  items: '++id, name, createdAt',
  // more tables
});
```

---

## Checklist Before Building

- [ ] I know what problem this solves
- [ ] I have a feature list (prioritized)
- [ ] I know my MVP scope
- [ ] I've picked my tech stack
- [ ] I have the file structure planned
- [ ] I know what to build first

## Checklist Before Shipping

- [ ] Core features work
- [ ] No console errors
- [ ] Works on mobile
- [ ] Data persists on refresh
- [ ] Error states handled
- [ ] Loading states shown
- [ ] Tested in another browser

---

## Remember

- **The blueprints are your AI substitute** — They contain the thinking you'd ask for
- **One feature at a time** — Don't parallelize until each piece works
- **Shipping beats perfect** — A working app is better than an imagined perfect one
- **Save your solutions** — When you solve a hard problem, write it down

You've got this.
