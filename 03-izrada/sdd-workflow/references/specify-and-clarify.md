# Specify + Clarify

Write `specs/<feature-slug>/spec.md`. This is the "what and why" — no implementation detail,
no technology choices, no file paths. If a sentence names a specific library, framework, or
file, it belongs in Plan instead, not here.

## spec.md template

```markdown
# Spec: <Feature Name>

**Status:** Draft → Approved
**Rigor level:** Trivial | Feature-sized | Regulated  (from rigor-scaling.md)

## 1. Problem / Motivation
What's broken, missing, or newly needed, in plain language.

## 2. Goals
What this must accomplish. One or two sentences per goal.

## 3. Non-goals
Explicitly named things this change does NOT do — this is what keeps scope from creeping
during Implement. As important as Section 2.

## 4. Requirements
Numbered, testable statements. Use plain language for Trivial/Feature-sized work; use EARS
(below) when the rigor level is Regulated, or whenever a requirement is genuinely
safety- or correctness-critical.

## 5. Acceptance Criteria
Concrete, checkable — things that can actually be verified in Converge, not "looks right."
Each criterion should trace to at least one requirement in Section 4.

## 6. Out of scope for this change
What's being deferred, and why — distinct from Non-goals (which are permanent; this is
"not yet").
```

## EARS notation (mandatory for Regulated, optional elsewhere)

EARS (Easy Approach to Requirements Syntax) forces a testable, unambiguous shape instead of
a sentence that reads fine but leaves room for interpretation:

```
WHEN <trigger condition or event>
THE SYSTEM SHALL <required behavior>
```

Example: `WHEN a user submits a payment form with an invalid card number, THE SYSTEM SHALL
reject the submission and display a field-level error without charging the card.`

Use it for anything where the cost of an agent misreading intent is high — payment flows,
fiscal/ESIR logic, anything a regulator or an angry customer would care about getting wrong.
Don't force it onto every requirement of a small internal tool; the overhead isn't worth it
there, and freeform acceptance criteria in Section 5 are enough.

## UC-1 / UC-2 / UC-3 pattern (recommended for anything with real logic)

For each requirement that has meaningful logic (not pure CRUD), write three concrete
input/output pairs instead of describing behavior abstractly. This catches ambiguity before
Plan, and doubles as the first draft of a test case:

```markdown
### UC-1: Standard case — expected input
**Input:** <realistic example>
**Expected output:** <realistic expected result>

### UC-2: Error case — invalid or missing input
**Input:** <malformed or missing example>
**Expected output:** <the specific error behavior, not "handles gracefully">

### UC-3: Edge case — valid but borderline input
**Input:** <boundary example — empty, maximum, ambiguous>
**Expected output:** <what should actually happen, spelled out>
```

## Clarify — before moving to Plan

Generate specific clarifying questions from gaps in the spec, not generic ones. Signs a spec
needs clarification before Plan:
- A requirement could be satisfied two structurally different ways, and it matters which.
- Section 3 (Non-goals) is empty or vague — that's usually a sign scope hasn't actually been
  bounded yet, just described.
- An acceptance criterion in Section 5 can't be checked without more information than the
  spec currently states.

Get explicit approval on the spec (with clarifications folded in) before Step 4 (Plan). This
is the single highest-leverage checkpoint in the whole workflow — underspecification here is
the most common reason an agent goes off the rails later, and it's far cheaper to fix in a
document than in a diff.
