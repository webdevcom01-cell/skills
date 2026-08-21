# Orientation memo — template

## How to use this template — do not copy this block into the deliverable

This is the Working-teardown output — what "help my team understand this system" produces.
It is not a compressed as-built spec. It is a different genre, written in a different
register, and the two most common ways to fail it are the same mistake: reaching for the
as-built spec's tables out of habit, and letting it grow past the point where a newcomer
would actually read it in one sitting.

**Register: explanation, not reference.** The as-built spec answers *what is* — precise,
tabular, exhaustive within its scope. This memo answers *why it's built this way* and
*what a newcomer needs to not get burned* — discursive, selective, readable away from the
code. Write prose paragraphs, not tables, except where a table is explicitly called for
below. A memo that reads like a shrunken spec has missed the point of writing a second
template at all.

**Length: one to two pages — hard number, 1200 words of body, §0 through §8 including
the ledger.** Architecture Haiku's discipline applies: the limit is not a compromise, it is
what forces you to name only what actually matters. Treat it as a number you check, not a
feeling you have — measured runs show the feeling does not work. **Before finalizing, run
STEP 6's length gate:** count the words, and if you are meaningfully over, either cut to
fit, escalate to Full depth per STEP 0.5 and name that as the reason, or declare the overrun
in §0 below. Silently shipping 2000+ words against this budget is the single most common way
this template has been failed.

**One diagram only, and it is C4 Level 1.** System context — this system, its neighbors,
who talks to it and why. Not the container or component breakdown; that level of detail
belongs to the as-built spec's §5, for the reader who needs it. If you find yourself
drawing containers, you have drifted into Full-depth work.

**Copy only the headings and tables below the line.** Italic guidance is for you, not the
reader.

§0, §7, and §8 are never dropped: §0 is what makes the memo an artifact rather than an
opinion, §7 is the falsification ledger — required at Working depth exactly as it is at
Full, just smaller — and §8 is this template's "what we could not determine," the same
non-negotiable as the as-built spec's §16a.

---

# Orientation: [system name]

## 0. Provenance

*Shorter than the as-built spec's §0 — this is a memo, not an engagement record — but not
absent. A reader deciding whether to trust this needs to know what it's pinned to and what
was not looked at.*

- **Pin** — commit SHA / URL + capture timestamp / endpoint + date, whichever applies
- **Depth** — working
- **What was NOT examined** — one line is enough if the scope was genuinely small
- **Length** — *include this bullet only when STEP 6's gate put you over the 1200-word budget
  and you chose branch (c): give the actual count, the budget, and why the material would not
  compress. Omit the bullet entirely when you are within budget — do not write "within budget"
  as a line of content.*

## 1. What this system is

*One paragraph. Plain language. If someone who has never seen this system reads only this
paragraph, they should know what it's for and why it exists — not the tech stack, the
purpose.*

## 2. System context

*C4 Level 1 — this system in the middle, the people and other systems around it, and why
each connection exists. This is the "everybody, technical and non-technical" diagram; keep
it that plain. One diagram, nothing more granular.*

## 3. How it's put together

*3 to 7 items, not a full building-block decomposition. Name the major pieces and the one
thing worth knowing about each — the thing that would otherwise take a newcomer a day of
grepping to figure out. Skip anything that doesn't clear that bar; a haiku is measured by
what it leaves out as much as by what it includes.*

## 4. Decisions that shape it

*2 to 5 entries, one or two sentences each: the decision, why it was probably made, and
where the evidence lives. Lighter than the as-built spec's §9 Nygard-template ADRs — this
is "the thing to know," not the full retroactive record.*

| Decision | Probable reason | Evidence | Verdict |
|---|---|---|---|

## 5. Where the bodies are buried

*The MISLEADING or surprising findings a newcomer would trip on without this memo —
documentation that lies, a name that means the opposite of what it suggests, a dependency
that isn't where anyone expects it. The as-built spec's §4a calls this "usually the
highest-value page in the whole document," and at Working depth it is often the entire
reason someone asked for this memo rather than reading the README themselves.*

## 6. Falsification ledger

*Required — STEP 5 applies at Working depth exactly as it does at Full. A small N is
expected and honest; skipping the ledger is not. Use the same format as the as-built
spec's §0.1, scaled down: it is fine for this to be three or four rows, as long as every
CONFIRMED claim above appears here by ID and vice versa.*

```
FALSIFICATION LEDGER
Target: <codebase|web|ai|binary>   Depth: working
Method: <Reflexion diff | evidence-column attack | ablation + differential | independent parser>

Inferred claims (one row each — this list IS N):
  C1  <claim>  → CONFIRMED    evidence: <the row/case that settled it>
  C2  <claim>  → UNCONFIRMED  evidence: <attempted, why unsettled>
  ...
  N = <row count>   confirmed a / downgraded b / dropped c   (a+b+c=N)

System scale examined: <e.g. 8 of ~340 files read · reduced scale is expected here>
Falsification NOT performed, and why: <or "none">
```

## 7. What we could not determine

**Required. Never omitted. Never empty.**

| Unknown | Why unresolved | What would resolve it |
|---|---|---|

*Shorter than the as-built spec's §16a is fine. Absent is not — the same reasoning applies:
a memo without this section presents the boundary of a one-session look as the boundary of
the system, and a newcomer has no way to tell the difference.*

## 8. Where to go deeper

*One or two lines: which existing documentation turned out to be trustworthy, which did
not, and — only if it's true — what a Full teardown would add if someone commissioned one.
This is a pointer, not a sales pitch for escalating; most orientation requests end here and
should be allowed to.*
