# The one-page AI governance card

## Before you write it

Read `references/engagement.md` §3 and §4. The card is the deliverable most likely to make a legal or regulatory claim, and the one most likely to end up printed on a wall where nobody re-reads the covering email. Three rules apply without exception:

- The mandatory legal notice goes at the **top** of the card, not the last page.
- Name no statute or regulator you cannot cite. Write `[REGULATOR / RULE — CONFIRM WITH THE CLIENT'S ADVISER]`.
- A card holding any unfilled `[TO CONFIRM]` field is watermarked **DRAFT — DO NOT PRINT**, and the "print this and pin it up" instruction is removed until the escalation names are filled in. A wall card with a blank emergency contact is worse than no card.

## Design constraint: it fits on one page or it does not work

The purpose of this card is to be remembered at the moment someone is about to paste something into a chat window. That moment lasts about three seconds. A twelve-page policy loses to three seconds every time, and worse, it creates false assurance — leadership believes the risk is handled because a document exists.

So: one page, three colours, plain language, and the client's own system names.

## The three tiers

Adapt the examples to the client's actual data. The tier logic is stable; the contents are not.

### 🟢 Green — just go

No approval needed. Work that is already public, internal-only, or purely generative.

Typical: drafts and outlines, summaries of public material, brainstorming, rewriting the team's own internal notes, code that touches no production data, research on public sources.

### 🟡 Yellow — ask first

Real, but needs a named human to approve before it goes anywhere. This tier is where most day-to-day work actually falls, and pretending otherwise is why policies get ignored.

Typical: anything naming a customer or client, work product delivered to a client, contract or pricing terms, competitive or unreleased internal information, anything that will be sent externally under the company's name.

State **who** approves. "Ask first" without a named approver becomes "go ahead" within a fortnight.

### 🔴 Red — never

No approval available. If the work seems to require it, that is an escalation, not a judgement call.

Typical: personal data of customers or employees, financial or health records, credentials, API keys, access tokens, anything covered by an NDA or a regulator's rules, source code under a licence that forbids it.

Name the client's specific regulated categories here. A card that says "regulated data" to a clinic means nothing; a card that says "patient records, including anything from [system name]" gets obeyed.

## The rule above the tiers

**A human name goes on everything that leaves the building.** No exceptions.

Not "reviewed by the team" — a person, identifiable afterwards. This single rule does more work than the three tiers combined, because it converts a diffuse risk into a specific accountability that people can feel before they hit send.

## Escalation path

The tiers only function if the yellow and red cases have somewhere to go. Fill these in with real names, not roles:

| Situation | Who to ask | How fast |
|---|---|---|
| Yellow item needs approval | [name] | Same day |
| Unsure which tier something is | [name] | Before proceeding — the default when unsure is to stop |
| Suspected red-tier data already entered | [name] + [name] | Immediately, same hour |
| Tool or connection behaving unexpectedly | [name] | Same day |

Make the "unsure" row explicit. Most real incidents are not people knowingly breaking a red rule; they are people who did not recognise the situation as red, and had nowhere quick to check.

## Break/fix protocol

Absent from most AI policies, and the reason unattended automations quietly rot. Every scheduled or shared workflow carries four facts, recorded in the Week 13 ownership register:

1. **Owner** — a named person, who knows they are the owner
2. **Alert** — how that person finds out it broke, without a customer telling them
3. **Fallback** — how the work gets done manually while it is broken
4. **Kill switch** — how to stop it, and who is allowed to

An automation missing any of the four should not be scheduled. This is not bureaucracy; it is the difference between a bad morning and a bad quarter.

## When output turns out to be wrong

Wrong output will reach a customer eventually. Deciding the response in advance keeps it from becoming a crisis:

- The named human on the output owns the correction — not the person who wrote the skill, not the consultant
- Correct it through the same channel it went out on, promptly, without theorising about AI in the correction itself
- Record what happened in the skill's acceptance check (Week 6) so the same failure is caught next time
- Update the check even when the cause was human error. A check that only catches machine errors misses most errors.

Treating each wrong output as a test-case contribution rather than an incident is what makes a team's checks improve over a year instead of decaying.
