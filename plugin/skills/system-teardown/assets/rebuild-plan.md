# Rebuild plan — template

## How to use this template — do not copy this block into the deliverable

Turning a completed teardown into a plan to build something equivalent.

**Do not start this document until the falsification ledger is closed.** A rebuild plan derived
from an unfalsified teardown propagates every wrong inference into a build schedule, where it is
far more expensive to discover.

**Copy only the headings and tables below the line.** Italic guidance is for you, not the reader.

§0 and §10 are never dropped: §0 decides whether this plan may legally exist in its current
form, and §10 is this template's version of "what we could not determine" — the assumptions
inherited from UNCONFIRMED findings, gathered in one place so that when one turns out wrong the
blast radius is visible immediately rather than discovered in integration. §6 carries the other
half: the unknowns that block the build.

---

# Rebuild plan: [name]

## 0. Contamination status

**Answer this before writing anything else. The question is contamination, not ambition.**

> Has anyone who will write the new system read the target's source code, decompiled output,
> recovered sourcemaps, or an extracted system prompt?

**If no** — no clean room is needed. Record that here, with what *was* used (public pages,
ordinary product use, published docs), and proceed normally. *Wanting to build something
comparable does not by itself require a clean room; reading the target's source does.*

**If yes** — name who is contaminated, and pick the separation that fits the team:

- **Full clean room** — analysis team, functional spec only, third-party review, separate
  implementation team, wall documented as it happens.
- **Small-team version** — the person who read the target writes the functional specification
  and then does **not** implement the parts they read. If that is impossible given the team
  size, the correct decision is not to read the source in the first place.

*Do not hand a two-person startup a two-team procedure. An unusable safeguard is one they
ignore entirely, which is worse than a smaller one they follow.* See
`references/legal-boundaries.md`.

Under EU Article 6, information obtained by decompilation may not be used to develop a
substantially similar program at all — a stricter bar than US clean-room practice.

## 1. What we are actually rebuilding

Not "a clone of X". State the specific capability, for whom, and why the existing option
does not serve. The teardown told you what exists; this section decides what *should*.

Explicitly list what the original does that we are **not** rebuilding, and why. This list
is usually where most of the schedule is saved.

## 2. Functional specification

Behavior only — what the system does, its interfaces, its formats, its guarantees. No
implementation detail carried over from the target, no distinctive naming, no structural
choices that were not functionally forced.

This is the artifact that crosses the clean-room wall. It is also the artifact that keeps
the rebuild honest: anything that cannot be expressed functionally was probably copied
rather than understood.

| Capability | Required behavior | Source finding | Provenance | Verdict |
|---|---|---|---|---|

*Rows whose source finding is UNCONFIRMED are hypotheses, not requirements. Mark them and
schedule a spike in §6, not an implementation task. Rows whose finding is MISLEADING deserve a
note on what the original's documentation claimed, so nobody re-imports the error.*

## 3. Architecture decision points

For each place the original made a choice, state the choice, the evidence it was made,
and whether we adopt or diverge.

| Decision | Original's choice (evidence) | Our choice | Rationale |
|---|---|---|---|

*Diverging deliberately is the point of a rebuild. Copying an architecture without knowing why
it was chosen inherits constraints that no longer apply — and a teardown usually recovers* what
*and not* why. *Mark those cases explicitly.*

## 4. Stack and dependencies

| Layer | Choice | Why | What it costs | Lock-in risk |
|---|---|---|---|---|

Where the original's choice is known, note whether we match it, and whether matching is for
interoperability, for team familiarity, or by default. *"By default" is not a reason — if that
is the honest answer, write it down as a decision nobody made.*

## 5. Phased build

Order by risk retired per unit of effort, not by architectural layer. *The first phase exists to
kill the largest uncertainty, not to build the foundation layer.*

| Phase | Delivers | Retires which risk | Depends on | Rough effort |
|---|---|---|---|---|

## 6. Spikes for unresolved unknowns

Every entry from the as-built spec's §16a "What we could not determine" that affects the build
gets a spike here — a timeboxed investigation with a decision at the end. **This section and §10
together are this document's required unknowns record; neither may be empty.**

| Unknown | Why it blocks | Spike | Timebox | Decision it produces |
|---|---|---|---|---|

Unknowns that do **not** affect the build are listed as explicitly out of scope, so nobody
re-investigates them later.

## 7. Verification against the original

How we will know the rebuild actually matches. Adapt to the target:

- Codebase → contract tests against the same interfaces; parity fixtures
- Web product → the same user flows completed end to end
- AI system → the frozen probe battery, scored on the four axes, with the variance floor
- Protocol → the independent parser against the full corpus plus a held-out capture

State the acceptance threshold **before** building, not after measuring. *For the AI target,
state it against the original's own variance floor — if the original disagrees with itself 12%
of the time, 88% agreement is a perfect match, not a mediocre one.*

## 8. What we are deliberately doing differently

The improvements. Each with the reason the original's approach was inadequate, and the new risk
the change introduces. *A rebuild with no entries here is a copy, and should be questioned on
whether it needed to exist at all.*

## 9. Risks

| Risk | Likelihood | Impact | Early warning signal | Mitigation |
|---|---|---|---|---|

Include the legal risks from section 0 if a clean room is in play.

## 10. What this plan assumes

Every assumption inherited from an UNCONFIRMED or MISLEADING teardown finding, in one place,
each with the section of the plan that depends on it.

| Assumption | Source finding | Verdict | What breaks if it is wrong |
|---|---|---|---|
