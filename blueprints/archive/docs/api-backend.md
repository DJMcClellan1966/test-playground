# API / Backend Blueprint

> Complete specification for building a RESTful API backend.

---

## Core Purpose

Provide a **reliable, secure data layer** that applications can build upon.

**Key insight:** A good API is boring. It does what clients expect, fails gracefully, and stays out of the way.
```
Request → Validate → Process → Persist → Respond
```

---

## User Types

| User | Goal | Key Actions |
|------|------|-------------|
| Frontend dev | Integrate features | Call endpoints, handle errors |
| Mobile dev | Build client app | Auth flows, CRUD, pagination |
| Admin/ops | Monitor health | Check logs, metrics, uptime |

---

## Feature Categories

### 🔐 Authentication
| Feature | Why Needed | Priority |
|---------|------------|----------|
| User registration | Create accounts | Must have |
| Login (email/password) | Basic auth | Must have |
| Password hashing | Security | Must have |
| JWT tokens | Stateless auth | Must have |
| Token refresh | Long sessions | Should have |
| Logout (token invalidation) | Security | Should have |
| Password reset (email) | Recovery | Should have |
| OAuth (Google, GitHub) | Convenience | Nice to have |

### 🔒 Authorization
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Role-based access (admin/user) | Permission levels | Should have |
| Resource ownership | Users own their data | Must have |
| API keys | Machine-to-machine | Nice to have |

### 📦 CRUD Operations
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Create resource | Add data | Must have |
| Read single resource | Get by ID | Must have |
| Read list (paginated) | Browse data | Must have |
| Update resource | Modify data | Must have |
| Delete resource | Remove data | Must have |
| Bulk operations | Efficiency | Nice to have |

### 🔍 Querying
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Pagination | Handle large sets | Must have |
| Sorting | Order results | Should have |
| Filtering | Narrow results | Should have |
| Search | Find by text | Should have |
| Field selection | Reduce payload | Nice to have |

### ✅ Validation
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Input validation | Prevent bad data | Must have |
| Type checking | Data integrity | Must have |
| Required fields | Completeness | Must have |
| Format validation (email, etc) | Correctness | Should have |
| Custom validation rules | Business logic | Should have |

### 📝 Error Handling
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Consistent error format | Predictable API | Must have |
| HTTP status codes | Standard semantics | Must have |
| Validation error details | Fix input | Must have |
| Not found handling | 404s | Must have |
| Server error handling | 500s | Must have |

### 📊 Logging & Monitoring
| Feature | Why Needed | Priority |
|---------|------------|----------|
| Request logging | Debugging | Must have |
| Error logging | Track issues | Must have |
| Health check endpoint | Uptime monitoring | Should have |
| Metrics endpoint | Performance | Nice to have |

### 🧪 Developer Experience
| Feature | Why Needed | Priority |
|---------|------------|----------|
| API documentation | Onboarding | Must have |
| OpenAPI/Swagger spec | Standardized docs | Should have |
| Example requests | Easy testing | Should have |
| Consistent naming | Predictability | Must have |

---

## User Flows

### Flow 1: Auth + CRUD
```
Client login -> Receive JWT -> Create resource -> Read resource -> Update -> Delete
```

### Flow 2: Paginated List
```
Request list -> Server applies filters -> Return data + meta -> Client renders
```

---

## Screens/Pages

| Screen | Purpose | Key Components |
|--------|---------|----------------|
| API Docs | Developer onboarding | Swagger/OpenAPI, examples |
| Health Check | Ops monitoring | Status + uptime |
| Admin Console (optional) | Management | Logs, metrics, user tools |

---

## API Design Patterns

### URL Structure
```
GET    /api/v1/resources         # List all
GET    /api/v1/resources/:id     # Get one
POST   /api/v1/resources         # Create
PUT    /api/v1/resources/:id     # Update (full)
PATCH  /api/v1/resources/:id     # Update (partial)
DELETE /api/v1/resources/:id     # Delete
```

### Response Format
```json
// Success
{
  "data": { ... },
  "meta": { "timestamp": "...", "requestId": "..." }
}

// Success (list)
{
  "data": [ ... ],
  "meta": { 
    "total": 100,
    "page": 1,
    "perPage": 20,
    "totalPages": 5
  }
}

// Error
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  }
}
```

### HTTP Status Codes
| Code | When |
|------|------|
| 200 | Success (GET, PUT, PATCH) |
| 201 | Created (POST) |
| 204 | No content (DELETE) |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (no/invalid token) |
| 403 | Forbidden (no permission) |
| 404 | Not found |
| 409 | Conflict (duplicate, etc) |
| 500 | Server error |

---

## Data Model (Example: Task API)

### User
```
id: uuid
email: string (unique)
passwordHash: string
name: string
role: "user" | "admin"
createdAt: timestamp
updatedAt: timestamp
```

### Task
```
id: uuid
userId: uuid (owner)
title: string
description: string | null
status: "todo" | "in-progress" | "completed"
priority: "high" | "medium" | "low" | null
dueDate: timestamp | null
createdAt: timestamp
updatedAt: timestamp
```

---

## Technical Stack (Recommended)

### Node.js (JavaScript)
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Framework | Express or Fastify | Simple, widely used |
| Validation | Zod or Joi | Type-safe validation |
| ORM | Prisma or Drizzle | Type-safe DB access |
| Database | PostgreSQL or SQLite | Reliable, free |
| Auth | jsonwebtoken | JWT handling |
| Password | bcrypt | Secure hashing |
| Docs | swagger-jsdoc | Auto-generate OpenAPI |

### Python
| Concern | Recommendation | Why |
|---------|----------------|-----|
| Framework | FastAPI | Modern, typed, auto-docs |
| Validation | Pydantic (built-in) | Excellent |
| ORM | SQLAlchemy | Mature, flexible |
| Database | PostgreSQL or SQLite | Reliable |
| Auth | python-jose | JWT handling |
| Password | passlib | Secure hashing |

---

## MVP Scope

### What's In
- [ ] User registration & login
- [ ] JWT authentication
- [ ] One resource CRUD (e.g., tasks)
- [ ] Input validation
- [ ] Error handling
- [ ] Pagination
- [ ] Database (SQLite for simplicity)
- [ ] Basic logging

### MVP Effort: 1-2 weeks

---

## Full Vision

Everything in MVP plus:
- OAuth providers
- Roles/permissions
- Rate limiting
- File uploads
- Email sending
- Background jobs

---

## File Structure (Node + Express)

```
api/
├── src/
│   ├── index.js              # Entry point
│   ├── app.js                # Express app setup
│   ├── config/
│   │   └── index.js          # Environment config
│   ├── routes/
│   │   ├── index.js          # Route aggregator
│   │   ├── auth.routes.js    # /auth endpoints
│   │   └── tasks.routes.js   # /tasks endpoints
│   ├── controllers/
│   │   ├── auth.controller.js
│   │   └── tasks.controller.js
│   ├── services/
│   │   ├── auth.service.js
│   │   └── tasks.service.js
│   ├── models/
│   │   └── index.js          # Prisma client
│   ├── middleware/
│   │   ├── auth.js           # JWT verification
│   │   ├── validate.js       # Request validation
│   │   └── errorHandler.js   # Global error handler
│   ├── validators/
│   │   ├── auth.validator.js
│   │   └── tasks.validator.js
│   └── utils/
│       ├── jwt.js
│       ├── password.js
│       └── ApiError.js
├── prisma/
│   └── schema.prisma
├── package.json
└── README.md
```

---

## Common Pitfalls

### 1. Not Hashing Passwords
**Solution:** ALWAYS use bcrypt. Never store plain text.

### 2. Leaking Sensitive Data
**Solution:** Never return passwordHash, tokens in responses. Select specific fields.

### 3. SQL Injection
**Solution:** Use ORM with parameterized queries. Never string-concatenate SQL.

### 4. No Rate Limiting
**Solution:** Add rate limiting before production (express-rate-limit).

### 5. Poor Error Messages
**Solution:** Return specific, actionable error messages. Include field names.

### 6. Not Validating Input
**Solution:** Validate EVERY input. Use Zod/Joi schemas.

### 7. Inconsistent Naming
**Solution:** Pick a convention (camelCase vs snake_case) and stick to it.

---

## Implementation Order

```
Week 1:
1. Project setup (Express, TypeScript optional)
2. Database setup (Prisma + SQLite)
3. Basic CRUD for one resource
4. Input validation
5. Error handling middleware
6. Request logging

Week 2:
7. User model
8. Registration endpoint
9. Login endpoint (JWT)
10. Auth middleware
11. Protect routes
12. Pagination & filtering
```

---

## Appendix: Code Patterns

### Auth Middleware
```javascript
import jwt from 'jsonwebtoken';
import { ApiError } from '../utils/ApiError.js';

export function authenticate(req, res, next) {
  const header = req.headers.authorization;
  
  if (!header?.startsWith('Bearer ')) {
    throw new ApiError(401, 'Missing authorization token');
  }
  
  const token = header.slice(7);
  
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    req.user = payload;
    next();
  } catch (err) {
    throw new ApiError(401, 'Invalid or expired token');
  }
}
```

### Validation Middleware (Zod)
```javascript
export function validate(schema) {
  return (req, res, next) => {
    const result = schema.safeParse(req.body);
    
    if (!result.success) {
      return res.status(400).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid input',
          details: result.error.errors.map(e => ({
            field: e.path.join('.'),
            message: e.message
          }))
        }
      });
    }
    
    req.validated = result.data;
    next();
  };
}

// Usage
const createTaskSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().optional(),
  dueDate: z.string().datetime().optional()
});

router.post('/tasks', validate(createTaskSchema), createTask);
```

### Error Handler
```javascript
export function errorHandler(err, req, res, next) {
  console.error(err);
  
  if (err instanceof ApiError) {
    return res.status(err.status).json({
      error: {
        code: err.code,
        message: err.message,
        details: err.details
      }
    });
  }
  
  // Unknown error
  res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred'
    }
  });
}
```

### Pagination
```javascript
async function listTasks(req, res) {
  const page = parseInt(req.query.page) || 1;
  const perPage = Math.min(parseInt(req.query.perPage) || 20, 100);
  const skip = (page - 1) * perPage;
  
  const [tasks, total] = await Promise.all([
    prisma.task.findMany({
      where: { userId: req.user.id },
      skip,
      take: perPage,
      orderBy: { createdAt: 'desc' }
    }),
    prisma.task.count({ where: { userId: req.user.id } })
  ]);
  
  res.json({
    data: tasks,
    meta: {
      total,
      page,
      perPage,
      totalPages: Math.ceil(total / perPage)
    }
  });
}
```
