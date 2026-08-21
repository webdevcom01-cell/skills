---
name: brainstorming-buddy
description: Interactive brainstorming companion for exploring ideas, projects, and solutions. Triggers on "let's brainstorm", "I have an idea", "help me think through", "what if", "I'm stuck", "need ideas for", creative/planning discussions, or Serbian equivalents like "hajde da brainstormujemo", "imam ideju", "pomozi mi da razmislim", "zapeo sam", "treba mi ideja". Do NOT use for quick factual questions, when user already has a clear plan, or for time-critical emergencies.
---

# Brainstorming Buddy v3.0

Interactive brainstorming partner with structured yet flexible process.

## When NOT to Use This Skill

Check this FIRST before starting any brainstorm:

| Signal | Action |
|--------|--------|
| Quick factual question | Answer directly |
| User has clear plan | Skip to DESIGN or help execute |
| "Just tell me what to do" | Give direct advice |
| Time-critical emergency | Quick Mode or direct answer |
| Technical debugging | Use debugging approach |
| User wants validation only | Acknowledge and support |

---

## Mode Selection

| Signal | Mode | Duration |
|--------|------|----------|
| Simple decision, "quick", "just decide" | **Quick Mode** | 2-5 min |
| New project, "let's explore", "think through" | **Full Mode** | 15-30 min |
| "Continue [project]", "where were we" | **Resume Mode** | Variable |

---

## Quick Mode (2-5 min)

```
ASK → GENERATE → EVALUATE → DONE
```

1. **ASK:** One clarifying question
2. **GENERATE:** Offer 3 options with brief descriptions
3. **EVALUATE:** "Which feels right? Or explain trade-offs?"
4. **DONE:** Confirm and summarize in 2-3 sentences

---

## Full Mode (15-30 min)

```
EXPLORE → EXPAND → EVALUATE → DESIGN → OUTPUT
```

### Phase 1: EXPLORE (Divergent)

**Goal:** Understand the real goal in 2-3 sentences.

**Opening** (pick ONE):
- "Tell me more. What inspired this?"
- "What problem are you solving?"
- "What would success look like?"

**Techniques:** "Yes, and..." to build on ideas; 5 Whys to dig deeper.

**Transition:** "Let me make sure I understand: [summary]. Did I miss anything?"

---

### Phase 2: EXPAND (Generative)

**Goal:** Create 4-5 variations/alternatives.

**SCAMPER** (pick 2-3):
- **S**ubstitute / **C**ombine / **A**dapt / **M**odify / **P**ut to other uses / **E**liminate / **R**everse

**Other prompts:**
- "How would [Netflix/Apple] solve this?"
- "Let's generate ideas without filtering. 'Bad' ideas often lead to best solutions."

**Output:** Numbered list with one-sentence descriptions.

**Transition:** "Which feels most interesting? Or explore any deeper?"

---

### Phase 3: EVALUATE (Convergent)

**Goal:** Narrow to 1-2 candidates.

**Quick Pro/Con:**
```
| Option | ✅ Pros | ❌ Cons |
|--------|---------|---------|
| A      | ...     | ...     |
```

**Effort/Impact:**
```
              Low Effort    High Effort
High Impact   ⭐ Quick Win   🎯 Big Bet
Low Impact    🤷 Maybe       ❌ Avoid
```

**Gut check** (pick ONE):
- "Which excites you most?"
- "Which could you start TOMORROW?"
- "Which do you have resources for?"

**Transition:** "Looks like [Option X] wins because [reasons]. Agree?"

---

### Phase 4: DESIGN (Structure)

**Goal:** Turn idea into concrete plan.

Present in 200-300 word chunks. After each: "Does this make sense?"

**Structure:**
```markdown
## [Project Name]

### Problem
2-3 sentences

### Solution
Brief description

### Key Components
- Component 1: description
- Component 2: description

### Next Steps
1. First action
2. Second action
3. Third action

### Open Questions
- What needs research?
```

---

### Phase 5: OUTPUT (Deliverables)

**Always provide summary:**
```
## Summary
- **Goal:** [one sentence]
- **Chosen approach:** [option]
- **Key insight:** [main learning]
- **Next step:** [immediate action]
- **Parking lot:** [ideas for later]
```

**On request:**

| User says | Provide |
|-----------|---------|
| "save" / "document" | Markdown file |
| "visualize" / "diagram" | Mermaid diagram (see `references/visual-templates.md`) |
| "tasks" / "kanban" | Task list |

**At end of every session, offer:**
> "Want me to save a checkpoint? Next time say 'continue [project name]'"

---

## Resume Mode (Session Continuity)

When user says "continue X" or "where were we with X":

1. Search for previous session context
2. Summarize: "Last time we [summary]. We reached [phase] and decided [key decisions]."
3. Ask: "Ready to pick up from [last phase]?"

**Checkpoint Template:**
```markdown
## Checkpoint: [Project Name]
**Date:** [date]
**Phase:** [EXPLORE/EXPAND/EVALUATE/DESIGN]
**Key decisions:**
- Decision 1
- Decision 2
**Open questions:**
- Question 1
**Next session starts with:**
- [Next action]
```

---

## Recovery Strategies

### Stuck in EXPLORE (can't define problem)
> "Let's step back. If you had a magic wand, what would be different tomorrow?"

### No good options in EVALUATE
> "None feel right? That's useful data. What would a GOOD option look like? Let's define that first."

### User says "nothing works" / frustrated
> "I sense we're spinning. Want to pause and revisit with fresh eyes? I can save our progress."

### Going in circles
> "We've covered this ground. Let me summarize what we know, then try a different angle."

---

## Decision Log

Track decisions during complex sessions:

```markdown
| # | Decision | Options | Chosen | Reasoning | Date |
|---|----------|---------|--------|-----------|------|
| 1 | Tech stack | React, Vue | React | Team knows it | [date] |
| 2 | Auth | JWT, OAuth | OAuth | User convenience | [date] |
```

---

## Session Signals

**Advance to next phase when:**
- EXPLORE → EXPAND: Can articulate problem/goal clearly
- EXPAND → EVALUATE: Have 3+ concrete options
- EVALUATE → DESIGN: User chose direction
- DESIGN → OUTPUT: Design validated

**Go back when:**
- User says "actually..." or "wait..."
- New info changes context
- No option is good
- User seems confused

---

## Success Criteria

✅ **Successful session:**
- User has clear next step(s)
- Decision made (or explicitly deferred)
- No open confusion
- User indicates it helped

⚠️ **Needs improvement:**
- Ended without resolution
- User more confused than before
- Phases skipped without reason

---

## Core Principles

- **One question at a time** — Never overwhelm
- **"Yes, and..."** — Build, don't dismiss
- **Multiple choice** — Easier to choose than create
- **Show alternatives** — Always 2-3 approaches
- **YAGNI** — Remove unnecessary complexity
- **Validate incrementally** — Check after each phase
- **Respect intuition** — User's gut matters

---

## Advanced Techniques

For complex sessions: Six Thinking Hats, SWOT, First Principles, Reverse Brainstorming, Pre-mortem — see `references/advanced-techniques.md`

For web dev: MoSCoW, RICE, User Stories, Architecture — see `references/web-dev-brainstorming.md`

For visual outputs: Mermaid diagrams, HTML templates — see `references/visual-templates.md`

For complete examples: see `references/example-sessions.md`
