---
name: saas-growth-and-validation
description: >-
  Applies SaaS growth-engineering UX patterns (onboarding, paywalls,
  churn/cancellation flows) and a validate-before-you-build gate checking
  for real demand signals before development starts. Use when adding or
  reviewing onboarding steps, paywall/upgrade prompts, or cancellation
  flows, or when someone proposes building a new product/feature before
  checking whether anyone actually asked for it. Trigger phrases (en/sr) -
  "add a paywall", "reduce churn", "improve onboarding", "should I build
  this", "do we have validated demand", "dodaj paywall", "smanji churn",
  "popravi onboarding", "da li da gradim ovo", "da li imamo potvrđenu
  potražnju". Do NOT use for marketing copy/campaigns/SEO (use marketing:*
  skills), throwaway UI-variant prototypes (use `prototype` - covers
  component-level A/B variant switching), session-level pattern learning
  (use `continuous-learning`), or general coding/test discipline (already
  enforced by `tdd-workflow` and this environment's CLAUDE.md rules).
metadata:
  version: "1.0.0"
  distilled_from: "executive-summary source document, 2026-09-09"
---

# SaaS growth and validation

Two related disciplines for making agent-built products commercially sound,
not just functionally correct:

1. **Growth-engineering UX patterns** — onboarding, paywalls, and churn flows
   encode business outcomes (activation, conversion, retention) directly into
   the product, instead of leaving them as an afterthought.
2. **A validate-before-you-build gate** — don't start development on a new
   product or feature until real people have confirmed the problem and some
   willingness to pay for a fix.

The shared premise: code that is functionally perfect but ignores these
constraints is often commercially unviable. These patterns exist to make that
gap visible before, not after, the work is done.

## Index

| Topic | Load when |
|---|---|
| [references/growth-engineering-patterns.md](references/growth-engineering-patterns.md) | Implementing or reviewing onboarding, paywall, or cancellation/churn UX |
| [references/validation-before-build.md](references/validation-before-build.md) | Someone proposes building a new product or a substantial new feature |

## Related capabilities already covered elsewhere

The source this skill was distilled from described four other patterns that,
on inspection, are already covered by skills or capabilities present in this
environment. Rather than duplicating them, use the existing coverage:

- **Observing a session and turning a repeated mistake into a standing rule**
  (the source calls this "Task Observer") — already implemented by the
  `continuous-learning` skill (session-end pattern extraction into
  `~/.claude/learned/`).
- **Four cognitive-discipline rules** (don't guess — ask; keep the simplest
  architecture that satisfies the requirement; don't touch anything outside
  the defined scope; define the tests before writing code) — already
  enforced by this environment's own global CLAUDE.md ("ask ONE short
  question", "Don't refactor things I didn't ask you to refactor / Don't
  change unrelated files", "Don't over-engineer simple things") and, for the
  test-first rule specifically, by the `tdd-workflow` skill. Restating these
  here would just be a second copy of a rule already loaded every session.
- **Isolating one UI section/component to switch between variants without
  touching the rest of the page** (the source calls this "Very8") — already
  covered by the `prototype` skill's UI branch (`UI.md`, sub-shape A):
  variant switching via a `?variant=` param on the existing route, isolated
  to the relevant subtree.
- **Automating a web action by reusing an existing logged-in session instead
  of sharing credentials or paying for an API** (the source calls this "Open
  CLI") — the same underlying approach (drive the web through an existing
  authenticated session rather than credentials or a paid API) is already
  available in this environment via the Chrome browser automation tooling.

## Sourcing note

This skill was distilled from a single secondary source document, not from
the original methodologies it describes. Two specific numeric claims in that
source could not be corroborated independently: the exact size of the
marketing-skill library it references, and the "10 named people / 3 paying"
validation threshold. Both are flagged inline in the relevant reference file
rather than stated as verified fact — treat them as this-source-only unless
corroborated elsewhere.
