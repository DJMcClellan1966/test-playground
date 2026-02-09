# Personal Website / Portfolio Blueprint

> Complete specification for building a personal website or portfolio.

---

## Core Purpose

Present yourself, your work, and make it easy for people to **contact you or take action**.

**Key insight:** Personal sites fail when they're about you, not for visitors. Answer: "Why should I care?"
```
Who are you → What do you do → Prove it → How to engage
```

---

## User Types (Visitors)

| Visitor | Goal | Key Actions |
|---------|------|-------------|
| Recruiter | Assess fit for role | Skim bio, view projects, check resume |
| Potential client | Evaluate for hire | See portfolio, read case studies |
| Peer/colleague | Learn about you | Browse work, find contact |
| Random visitor | Quick understanding | Get gist in 10 seconds |

---

## Feature Categories

### 🏠 Homepage
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Clear headline | Who you are, what you do | Must have |
| Professional photo | Personal connection | Should have |
| Brief tagline | Quick summary | Must have |
| CTA button | What to do next | Must have |
| Navigation | Reach other pages | Must have |

### 👤 About Page
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Bio paragraph | Story, background | Must have |
| Skills list | Capabilities | Should have |
| Experience timeline | Career history | Should have |
| Education | Credentials | Nice to have |
| Personal interests | Humanization | Nice to have |

### 💼 Portfolio/Work
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Project grid/list | Browse work | Must have |
| Project thumbnails | Visual appeal | Should have |
| Project detail pages | Deep dive | Should have |
| Tags/categories | Filter by type | Nice to have |
| Live demo links | See it work | Should have |
| Source code links | Credibility | Should have |

### 📝 Blog (Optional)
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Post list | Browse articles | Should have |
| Single post page | Read content | Should have |
| Markdown support | Easy writing | Should have |
| Syntax highlighting | Code blocks | Should have |
| Date/category | Organization | Should have |
| RSS feed | Syndication | Nice to have |

### 📄 Resume
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Online resume page | Always accessible | Should have |
| PDF download | Offline use | Should have |
| Work experience | Standard info | Must have |
| Skills section | Technical abilities | Should have |

### 📬 Contact
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Contact form | Easy reach out | Must have |
| Email link | Direct contact | Must have |
| Social links | Other platforms | Should have |
| Location (city) | Context | Nice to have |
| Spam protection | Prevent bots | Should have |

### 🎨 Design & Polish
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Mobile responsive | Phone visitors | Must have |
| Fast loading | User experience | Must have |
| Dark mode toggle | Preference | Nice to have |
| Consistent style | Professional | Must have |
| Favicon | Browser tab | Should have |
| Open Graph meta | Social sharing | Should have |

---

## User Flows

### Flow 1: First Impression
```
Visit site -> Read headline -> See featured work -> Click project
```

### Flow 2: Contact
```
Browse portfolio -> Open contact -> Send message -> Follow up
```

---

## Screens/Pages

| Page | Purpose | Key Components |
|------|---------|----------------|
| **Home** | First impression | Hero, headline, CTA, featured work |
| **About** | Background story | Bio, photo, skills, timeline |
| **Work/Portfolio** | Showcase projects | Grid, thumbnails, filters |
| **Project Detail** | Case study | Screenshots, description, links |
| **Blog** | Thought leadership | Post list, tags |
| **Post** | Single article | Content, date, share |
| **Resume** | Professional history | Sections, download |
| **Contact** | Reach you | Form, email, socials |

---

## Data Model

### Project
```
id: string
title: string
slug: string  # URL-friendly name
description: string
longDescription: string (markdown)
thumbnail: string (image path)
images: string[]
technologies: string[]
liveUrl: string | null
sourceUrl: string | null
featured: boolean
date: date
category: "web" | "mobile" | "design" | "other"
```

### Blog Post
```
id: string
title: string
slug: string
content: string (markdown)
excerpt: string
date: date
tags: string[]
published: boolean
```

---

## Technical Stack (Recommended)

### Static Site (Recommended for Portfolio)
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Framework | Astro or Next.js (static) | Fast, SEO-friendly |
| Styling | Tailwind CSS | Quick, consistent |
| Markdown | MDX | Blog posts, project descriptions |
| Hosting | Vercel, Netlify, GitHub Pages | Free, fast, easy |
| Forms | Formspree, Netlify Forms | No backend needed |
| Analytics | Plausible, Umami | Privacy-friendly |

### Simple HTML/CSS
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Build | None needed | Simplicity |
| Styling | Plain CSS or Tailwind | Works everywhere |
| Hosting | GitHub Pages | Free |
| Forms | Formspree | External service |

---

## MVP Scope

### What's In
- [ ] Homepage with headline + about blurb
- [ ] About section/page
- [ ] 3-5 project cards
- [ ] Contact form (Formspree)
- [ ] Mobile responsive
- [ ] Basic SEO (title, description, OG tags)

### MVP Effort: 3-5 days

---

## Full Vision

Everything in MVP plus:
- Blog
- Dark mode
- Animations
- CMS for content
- Comments

---

## File Structure (Astro)

```
portfolio/
├── public/
│   ├── favicon.ico
│   └── images/
│       ├── profile.jpg
│       └── projects/
├── src/
│   ├── layouts/
│   │   └── BaseLayout.astro
│   ├── pages/
│   │   ├── index.astro       # Home
│   │   ├── about.astro
│   │   ├── work.astro
│   │   ├── contact.astro
│   │   └── projects/
│   │       └── [slug].astro  # Dynamic project pages
│   ├── components/
│   │   ├── Header.astro
│   │   ├── Footer.astro
│   │   ├── ProjectCard.astro
│   │   ├── SkillBadge.astro
│   │   └── ContactForm.astro
│   ├── content/
│   │   └── projects/
│   │       ├── project-1.md
│   │       └── project-2.md
│   └── styles/
│       └── global.css
├── astro.config.mjs
├── tailwind.config.js
└── package.json
```

---

## Common Pitfalls

### 1. No Clear CTA
**Solution:** Every page should have a next action (view work, contact, download resume).

### 2. Projects Without Context
**Solution:** Don't just show screenshots. Explain problem, process, outcome.

### 3. Long Load Times
**Solution:** Optimize images, use lazy loading, minimize JS.

### 4. Not Mobile-Friendly
**Solution:** Design mobile-first. Test on actual phones.

### 5. Outdated Content
**Solution:** Remove old projects. Quality over quantity.

### 6. Broken Links
**Solution:** Check links before deploying. Use relative paths.

---

## Implementation Order

```
Day 1-2:
1. Project setup
2. Layout component (header, footer)
3. Homepage design
4. About section

Day 3:
5. Project data structure
6. Project grid component
7. Project cards

Day 4:
8. Individual project pages
9. Contact form
10. Mobile responsiveness

Day 5:
11. SEO/meta tags
12. Deploy
13. Test on devices
```

---

## Content Checklist

Before launching, have:

- [ ] Professional photo
- [ ] 2-sentence bio
- [ ] 3-5 strong projects with descriptions
- [ ] Each project: what, why, how, outcome
- [ ] Contact email
- [ ] At least 2 social links
- [ ] Resume PDF (if applicable)
- [ ] Favicon
- [ ] Meta description
- [ ] OG image for social sharing

---

## Appendix: Code Patterns

### Responsive Project Grid (Tailwind)
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {projects.map(project => (
    <ProjectCard project={project} />
  ))}
</div>
```

### Project Card Component
```astro
---
const { project } = Astro.props;
---

<a href={`/projects/${project.slug}`} class="group">
  <div class="relative overflow-hidden rounded-lg">
    <img 
      src={project.thumbnail} 
      alt={project.title}
      class="w-full h-48 object-cover transition group-hover:scale-105"
    />
  </div>
  <h3 class="mt-3 font-semibold group-hover:text-blue-600">
    {project.title}
  </h3>
  <p class="text-gray-600 text-sm mt-1">
    {project.description}
  </p>
  <div class="flex gap-2 mt-2">
    {project.technologies.slice(0, 3).map(tech => (
      <span class="text-xs px-2 py-1 bg-gray-100 rounded">{tech}</span>
    ))}
  </div>
</a>
```

### Contact Form (Formspree)
```html
<form action="https://formspree.io/f/YOUR_FORM_ID" method="POST" class="space-y-4">
  <div>
    <label for="name" class="block text-sm font-medium">Name</label>
    <input type="text" name="name" id="name" required 
           class="mt-1 w-full px-3 py-2 border rounded-md" />
  </div>
  <div>
    <label for="email" class="block text-sm font-medium">Email</label>
    <input type="email" name="email" id="email" required 
           class="mt-1 w-full px-3 py-2 border rounded-md" />
  </div>
  <div>
    <label for="message" class="block text-sm font-medium">Message</label>
    <textarea name="message" id="message" rows="4" required
              class="mt-1 w-full px-3 py-2 border rounded-md"></textarea>
  </div>
  <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
    Send Message
  </button>
</form>
```
