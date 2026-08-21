# Advanced Brainstorming Techniques

Use when basic SCAMPER/Pro-Con techniques aren't sufficient.

## Quick Reference

| Situation | Technique |
|-----------|-----------|
| Need multiple perspectives | Six Thinking Hats |
| User completely stuck | Reverse Brainstorming |
| Business viability | SWOT Analysis |
| Disruptive/innovative ideas | First Principles |
| Analysis paralysis | Time-Boxing |
| Risk assessment | Pre-mortem |

---

## Six Thinking Hats

Examine idea from 6 perspectives. Pick 3-4 relevant hats, 2-3 min each.

| Hat | Focus | Question |
|-----|-------|----------|
| ⚪ White | Facts | "What data do we have? What's missing?" |
| ❤️ Red | Emotions | "How do you feel? What does your gut say?" |
| ⚫ Black | Risks | "What could go wrong?" |
| 💛 Yellow | Benefits | "What's the best case? Advantages?" |
| 💚 Green | Creativity | "What new ideas can we add?" |
| 💙 Blue | Process | "What's next? How do we organize?" |

### Mini Example: B2C to B2B Pivot

**Topic:** Should we pivot from B2C to B2B?

⚪ **White:** "Current MRR: $2k, CAC: $50, B2B avg ticket 10x higher"
❤️ **Red:** "Excited about B2B but scared of longer sales cycles"
⚫ **Black:** "Need new sales skills, existing users might churn"
💛 **Yellow:** "Higher revenue per customer, less support volume"
💚 **Green:** "Hybrid model? Keep B2C self-serve, add B2B tier"
💙 **Blue:** "Validate with 5 B2B interviews before deciding"

---

## Reverse Brainstorming

Use when user is stuck and can't generate ideas.

**Process:**
1. Ask: "How would we GUARANTEE this fails?"
2. Generate anti-solutions
3. Flip each into real solution

### Mini Example: Portfolio Website

**User:** "I need my portfolio to stand out but have no ideas"

**Anti-solutions → Solutions:**
```
❌ Boring template      → ✅ Custom design with personality
❌ No personality       → ✅ Inject hobbies/quirks
❌ Skills without work  → ✅ Case studies with process
❌ Slow loading         → ✅ Performance-first, <2s load
❌ Looks like everyone  → ✅ Unique visual style
```

**Follow-up:** "What makes YOU different? Hobbies, background?"

---

## SWOT Analysis

Strategic framework for evaluating projects.

```
┌───────────────────────┬───────────────────────┐
│      STRENGTHS        │      WEAKNESSES       │
│    (Internal +)       │     (Internal -)      │
│                       │                       │
│ Skills you have       │ Gaps in knowledge     │
│ Resources available   │ Limited time/budget   │
│ Unique advantages     │ Dependencies          │
├───────────────────────┼───────────────────────┤
│    OPPORTUNITIES      │       THREATS         │
│    (External +)       │     (External -)      │
│                       │                       │
│ Market trends         │ Competition           │
│ Timing advantages     │ Economic factors      │
│ Partnership options   │ Technology changes    │
└───────────────────────┴───────────────────────┘
```

### Mini Example: SaaS Launch

**Project:** Launching project management tool

| S | W | O | T |
|---|---|---|---|
| Strong dev team | No marketing budget | Remote work trend growing | Notion, Asana dominate |
| Unique AI feature | First product launch | AI hype | Economic downturn |
| Fast iteration | No brand recognition | Enterprise demand | Copycats if successful |

**Insight:** Focus on AI differentiator, target niche (agencies?) to avoid direct competition.

---

## First Principles Thinking

Strip away assumptions. Use for innovative/disruptive ideas.

**Process:**
1. "What is fundamentally true about this problem?"
2. "What assumptions does everyone accept?"
3. "What if those assumptions are wrong?"
4. "How would we solve this from scratch?"

### Mini Example: User Authentication

**Assumption:** "A website needs user login with passwords"

**Challenge:** "Why? What's the actual goal?"

**Insight:** "We need identity, not necessarily passwords"

**New ideas:**
- Magic link (email-based)
- OAuth only (Google/GitHub)
- Anonymous with local storage
- Passkeys

---

## Time-Boxing

For analysis paralysis or perfectionism.

### 2-Minute Drill
> "Pitch this idea in 2 minutes like an elevator pitch. GO!"

### 10-10-10 Rule
> "How will you feel about this decision in 10 minutes? 10 months? 10 years?"

### Fake Deadline
> "You MUST launch tomorrow. What absolutely MUST work?"

### Pomodoro Brainstorm
> "25 minutes: 20 to generate, 5 to evaluate. Timer starts now."

---

## Pre-mortem Analysis

Imagine project failed. Work backwards to prevent it.

**Process:**
1. "It's 6 months from now. Project failed. What happened?"
2. List failure reasons
3. Create prevention strategies
4. Prioritize which risks to address

### Mini Example: App Launch

| Failure Mode | Likelihood | Prevention |
|--------------|------------|------------|
| Ran out of money | High | Strict budget, milestone reviews |
| Users didn't want it | Medium | 10 user interviews before building |
| Technical debt buried us | Medium | TDD, code reviews, refactor sprints |
| Team burned out | Medium | Realistic deadlines, no crunch |

---

## Constraint Removal

Systematically remove constraints to unlock creativity.

**Questions:**
1. "What if money wasn't an issue?"
2. "What if time wasn't an issue?"
3. "What if you had a team of 10?"
4. "What if failure was impossible?"
5. "What if you had to do it in 1/10th the time?"

**Process:**
1. Generate ideas without constraint
2. Ask: "What's the essence of this idea?"
3. Find ways to achieve essence within real constraints

---

## Combining Techniques

| Combination | When to use |
|-------------|-------------|
| First Principles → SCAMPER | Innovative product ideas |
| SWOT → Pre-mortem | Project planning |
| Six Hats → Pro/Con | Complex decisions |
| Reverse Brainstorm → Constraint Removal | Breaking through blocks |
| Time-Boxing → Any technique | When user is overthinking |

---

## Decision Tree: Which Technique?

```
Is user stuck/blocked?
├─ Yes → Reverse Brainstorming or Constraint Removal
└─ No
   ├─ Need multiple perspectives?
   │  └─ Yes → Six Thinking Hats
   └─ No
      ├─ Evaluating business viability?
      │  └─ Yes → SWOT
      └─ No
         ├─ Industry "best practices" feel wrong?
         │  └─ Yes → First Principles
         └─ No
            └─ Analysis paralysis?
               └─ Yes → Time-Boxing
```
