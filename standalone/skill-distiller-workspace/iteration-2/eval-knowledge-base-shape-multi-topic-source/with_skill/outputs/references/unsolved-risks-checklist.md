# Unsolved distribution risks — checklist

Load this before assuming a distribution mechanism (one of these five, or a
new one you're reviewing) has already solved a trust, lifecycle, or privacy
problem. None of the five ecosystems compared here have solved every item
below; most only handle a subset. Grouped by concern, not by which
ecosystem — the point is to check a new system against the whole list, not
to rank the five against each other.

## Trust & identity

- **Two publishers, one look-alike name.** Nothing outside a single registry
  confirms that a handle on one platform and a differently-formatted
  identifier on another actually trace back to the same person or
  organization. Any registry that hands out names without checking domain
  or account ownership first is, by construction, open to squatting on a
  name that looks like it belongs to someone it doesn't.
- **Signing is the exception, not the rule.** Out of the five, cryptographic
  signing tied back to a registry-verified key happens in exactly one.
  Everywhere else, "who published this" reduces entirely to "who was logged
  into that account" — which means the moment an account's login is
  compromised, an attacker's publish is indistinguishable from a real one.
- **Local names can get hijacked by a later public registration.** A couple
  of these ecosystems let a developer use an unpublished local name during
  development that happens to match something not yet registered. Nothing
  stops a different party from registering that same name publicly
  afterward — at which point tooling that was quietly resolving to the
  local copy can start resolving to the newly-registered remote one
  instead, without any warning that the target changed.
- **Passing validation isn't the same claim as passing review.** A manifest
  that parses correctly, matches its schema, and even carries a valid
  signature has told you nothing about whether anyone actually looked at
  what the package does. None of the five distinguish, in a way a consumer
  can see, between "structurally fine" and "someone checked the behavior."

## Lifecycle & revocation

- **Pulling a listing doesn't reach what's already out there.** Removing a
  bad version from a registry's own index has no defined effect on mirrors,
  forks, or anything already downloaded onto someone's machine. Even the
  one ecosystem in this set with an explicit "deprecate" call only stops
  *future* installs from picking up that version — it does nothing to a
  copy that's already running.
- **A leaked secret has no broadcast channel.** When a credential a package
  depends on turns out to be compromised, there is no mechanism in any of
  these five that pushes a "rotate this" notice out to everyone who
  installed it. Getting the word out is left entirely to whatever
  out-of-band channel (a blog post, a mailing list, word of mouth) the
  maintainer happens to use, if they use one at all.
- **Deprecation rarely comes with directions.** Marking something outdated
  typically means nothing more than a sentence in a README pointing at a
  replacement, if even that. There's no field, in any of the five schemas
  studied, a tool could read to automatically figure out "this is retired,
  install that instead."

## Versioning & comparability

- **The word "version" doesn't mean one thing across all five.** Two of the
  ecosystems tie version numbers to a real, registry-checked semver format;
  a third uses a shorthand two-part number nothing actually validates; a
  fourth treats the version field as an arbitrary string an author could
  set to anything at all. Comparing two version numbers across ecosystem
  boundaries and expecting the comparison to mean something is a mistake —
  first confirm which of these four regimes you're actually working under.

## Data, privacy & licensing

- **Forking doesn't carry the license along automatically.** Whether a
  redistributed copy of a package still declares — or even keeps — its
  original license is left entirely to whoever forked it. No tooling among
  the five checks for this; it survives or doesn't purely by habit.
- **Almost nobody draws the distributor/user data line on paper.** Section
  `data-ownership-separation.md` covers the one exception. For the other
  four, answering "what do we actually store about this specific user, and
  where" for a deletion or export request means tracing it by hand, system
  by system — there's no schema to consult instead.
- **A registry entry can point somewhere it never actually checked.** Some
  of these systems let a listing reference a live, remotely hosted service
  rather than shipping code directly. The registry validates that the
  *reference* is well-formed; it has no visibility into, and makes no claim
  about, what that remote endpoint actually does once traffic reaches it.

## How to use this list

When reviewing a new or unfamiliar distribution mechanism, go through each
cluster and ask specifically which of these it has actually solved versus
merely hasn't run into yet. "We haven't had an incident" is not evidence a
risk is handled — every item above is a structural gap, not a rare event,
and a system can go a long time without a public incident in a given
category while still having no real mechanism in place to prevent one.
