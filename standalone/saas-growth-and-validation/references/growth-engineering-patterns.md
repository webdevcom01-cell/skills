# Growth-engineering UX patterns

Distilled from a source that attributes this pattern set to a marketing-skill
library associated with **Corey Haines** (public repo:
`github.com/coreyhaines31/marketingskills`). The source document itself
spelled the name "Corey Haynes" — that is a misspelling; the name is
corrected here. The source also describes this as a library of "48 marketing
skills"; that count is higher than the public repo's currently observable
size (40+ skills). Treat the exact number as unverified — describe this as
"a broad library of SaaS marketing skills" rather than citing "48" as fact.

Three sub-patterns, each pairing a mechanism with the business outcome it's
meant to produce.

## Onboarding — reduce time-to-value

- Cut the number of steps between signup and the user reaching real value.
- Autofill anything already inferable (prior profile data, detected
  settings) instead of asking again.
- Show a visible progress indicator across any multi-step flow.

Outcome this targets: faster activation and a higher signup-to-activation
completion rate.

## Paywalls — lock-and-unlock, not a wall upfront

- Let the user see and start interacting with a gated feature; intercept
  with a direct route to the pricing/upgrade page only at the point of
  actual use, rather than blocking the feature entirely before they've
  engaged with it.

Outcome this targets: maximizing conversion from free to paid, on the theory
that conversion happens best at the moment of demonstrated intent, not
before it.

## Churn prevention — change the default exit, not just the exit friction

- Make "pause" (not full cancellation) the default, most prominent action on
  the cancellation flow.
- Offer a personalized counter-offer at the moment cancellation intent is
  detected, instead of a generic retention message.

Outcome this targets: reducing revenue loss from the cancellation flow
itself — the mechanism is redirecting the user's path at the moment of
intent, not adding friction to make cancellation harder to complete.

## Applying this

When implementing or reviewing an onboarding, paywall, or cancellation flow,
check it against the relevant rule above before calling it done. These are
the specific techniques this source names, not universal laws — where one of
them conflicts with a concrete product constraint, the constraint wins.
