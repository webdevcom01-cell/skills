# Rigor scaling

The most common way an SDD process fails in practice isn't too little discipline — it's
using the full gated flow on a one-line button-color change and teaching everyone to route
around the skill entirely. Size the change honestly before picking a level.

## Decision table

| Signal | Level | What runs |
|---|---|---|
| 1–2 files touched, no new dependency, no new user-visible behavior, easily reverted | **Trivial** | Skip Constitution/Specify/Plan. Write one line in `tasks.md` describing the change, implement it, still run Converge (Step 7). |
| New module, new endpoint, new user-facing behavior, or touches more than a couple of files/subsystems | **Feature-sized** | Full flow: Constitution (if not already current) → Specify → Clarify → Plan → Tasks → Implement → Converge. |
| Touches money, fiscalization/ESIR, personal data, a legal/compliance obligation, or anything where a wrong answer has real-world consequences beyond this codebase | **Regulated** | Full flow, and EARS notation becomes mandatory for every requirement in `spec.md` (see `specify-and-clarify.md`) — freeform prose acceptance criteria are not precise enough here. |

## Judgment calls

- **When in doubt, one level up, not down.** The cost of an unnecessary Plan phase is a few
  minutes of review; the cost of a skipped Plan phase on something that turns out to be
  feature-sized is a rewrite.
- **A "small ask" that actually hides a fork in approach is feature-sized, not trivial.**
  If answering it requires picking between two real architectures, that's a Plan-phase
  question even if the resulting diff is small.
- **State the chosen level out loud, in one sentence, before doing anything else.** This is
  the person's cheapest opportunity to say "no, that's actually bigger than it looks" or
  "that's fine, don't bother with the full flow."
- **Never let rigor scale down to zero.** Converge (Step 7) always runs, even for a Trivial
  change — it's the cheapest phase to run and the one most likely to catch a change that
  looked smaller than it was.
- **Feature-sized work that touches security or integrity guarantees (audit trails, access
  control, tenant isolation) can warrant EARS notation even when it doesn't meet the
  Regulated row's letter.** The Regulated row names specific triggers (money, fiscalization,
  personal data, legal obligations); it doesn't claim to be the only case where precise,
  per-requirement acceptance criteria earn their cost. If ambiguity in a requirement here
  would be expensive to discover after Implement, that's the same argument the Regulated row
  makes — state the choice out loud (per the bullet above) rather than silently deciding
  either way.
