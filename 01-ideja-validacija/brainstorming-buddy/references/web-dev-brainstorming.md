# Web Development Brainstorming

Specialized techniques for web dev projects, features, and architecture.

---

## Feature Prioritization

### MoSCoW Method

| Category | Meaning | Question |
|----------|---------|----------|
| **Must** | Can't launch without | "Does it work without this?" |
| **Should** | Important, v1.1 | "Users expect this" |
| **Could** | Nice to have | "Delighter feature" |
| **Won't** | Deferred | "Not this release" |

**Template:**
```markdown
## Feature Prioritization

### Must Have (MVP)
- [ ] Feature 1
- [ ] Feature 2

### Should Have (v1.1)
- [ ] Feature 3

### Could Have (v1.2+)
- [ ] Feature 4

### Won't Have (Parking Lot)
- [ ] Feature 5 — Reason: too complex
```

---

### RICE Scoring

Quantitative prioritization for larger feature lists.

```
Score = (Reach × Impact × Confidence) / Effort
```

| Factor | Scale | Description |
|--------|-------|-------------|
| **Reach** | # users | How many affected? |
| **Impact** | 0.25-3 | How much does it help? |
| **Confidence** | 0-100% | How sure are we? |
| **Effort** | Person-weeks | How long? |

**Impact scale:**
- 3 = Massive (game-changer)
- 2 = High (significant improvement)
- 1 = Medium (nice improvement)
- 0.5 = Low (minor improvement)
- 0.25 = Minimal

#### RICE Calculator Template

```markdown
## RICE Score: [Feature Name]

| Factor | Value | Notes |
|--------|-------|-------|
| Reach (users/month) | _____ | |
| Impact (0.25-3) | _____ | |
| Confidence (0-100%) | _____ | |
| Effort (person-weeks) | _____ | |

**Score = ( ___ × ___ × ___ ) / ___ = _____**

### Comparison

| Feature | R | I | C | E | Score |
|---------|---|---|---|---|-------|
| Dark mode | 1000 | 1 | 80% | 2 | 400 |
| Export PDF | 500 | 2 | 90% | 3 | 300 |
| AI suggest | 200 | 3 | 50% | 8 | 37.5 |
```

---

## User Story Framework

### Basic Format
```
As a [user type]
I want [action]
So that [benefit]
```

### With Acceptance Criteria
```
As a [user type]
I want [action]
So that [benefit]

Acceptance Criteria:
- [ ] Given [context], when [action], then [result]
- [ ] Given [context], when [action], then [result]
```

### Mini Example
```
As a busy professional
I want to save articles for later
So that I can read them during commute

Acceptance Criteria:
- [ ] Given any article, when I click "Save", then it appears in my list
- [ ] Given saved articles, when offline, then I can still read them
- [ ] Given I've read an article, when I return, then it's marked read
```

---

## Technical Architecture

### Key Questions

**Data Flow:**
1. Where does data come from?
2. Where does it go?
3. What transformations happen?
4. Who needs access?

**Scalability:**
1. What if this scales 10x?
2. What's most expensive operation?
3. What can be cached?
4. What can be async?

**Resilience:**
1. What if [service] goes down?
2. What's the fallback?
3. How do we recover?

**Security:**
1. What's the attack surface?
2. What data is sensitive?
3. Who should access what?

### Architecture Decision Record (ADR)

```markdown
# ADR-001: [Decision Title]

## Status
Proposed / Accepted / Deprecated

## Context
What issue motivates this decision?

## Decision
What are we doing?

## Consequences
What becomes easier? Harder?

## Alternatives Considered
1. Alt A — rejected because...
2. Alt B — rejected because...
```

---

## API Design

### REST Resource Mapping

```
Noun (Resource)     Verbs (Actions)
───────────────     ───────────────
/users              GET (list), POST (create)
/users/:id          GET, PUT, PATCH, DELETE
/users/:id/posts    GET (user's posts)
/posts              GET, POST
/posts/:id          GET, PUT, DELETE
```

### API Checklist

- [ ] Resources are nouns
- [ ] Consistent naming
- [ ] Proper HTTP methods
- [ ] Meaningful status codes
- [ ] Pagination for lists
- [ ] Filtering/sorting
- [ ] Error format defined
- [ ] Auth documented
- [ ] Rate limiting
- [ ] Versioning strategy

---

## Database Schema

### Entity Questions

1. What entities exist?
2. How do they relate? (1:1, 1:N, N:N)
3. What attributes each?
4. Required vs optional?
5. What's unique?
6. What queries most often?

### Schema Template

```markdown
## Entity: [Name]

### Attributes
| Field | Type | Required | Unique | Notes |
|-------|------|----------|--------|-------|
| id | UUID | Yes | Yes | PK |
| name | String | Yes | No | Max 255 |
| email | String | Yes | Yes | Validated |

### Relationships
- Has many: [Entity]
- Belongs to: [Entity]

### Indexes
- email (login lookup)
- created_at (sorting)
```

---

## Performance Analysis

### Bottleneck Checklist

```
User Request
     │
     ▼
┌─────────┐
│   CDN   │ ← Cache static assets?
└────┬────┘
     │
     ▼
┌─────────┐
│  Load   │ ← Enough instances?
│Balancer │
└────┬────┘
     │
     ▼
┌─────────┐
│   App   │ ← Code optimized?
│ Server  │
└────┬────┘
     │
     ▼
┌─────────┐
│  Cache  │ ← Redis/Memcached?
└────┬────┘
     │
     ▼
┌─────────┐
│Database │ ← Queries optimized? Indexes?
└─────────┘
```

---

## Quick Prompts by Stage

### Ideation
- "What if we built this for [different audience]?"
- "What would competitor do?"
- "What's the 10x version?"
- "What's the MVP version?"

### Technical Design
- "Simplest thing that could work?"
- "Where will this break first?"
- "What don't we know yet?"
- "What would we change in 2 years?"

### UX Design
- "What would frustrate user here?"
- "What's the happy path?"
- "What are edge cases?"
- "How do we handle errors?"

### Launch
- "What metrics define success?"
- "What's rollback plan?"
- "Who needs to know before launch?"
- "Monitoring strategy?"
