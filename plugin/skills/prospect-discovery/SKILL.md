---
name: prospect-discovery
version: 1.1.0
description: Researches a company from a URL or name and produces a consultant-ready discovery pack — a sourced dossier where every claim carries a citation or is marked unverified, a discovery call agenda built from that company's actual business, a filled intake block that feeds straight into team-enablement-program, and a proposal skeleton with hypotheses marked as unconfirmed. Use whenever the user gives a company website, names a prospect or client to look into, or asks to prepare for a sales or discovery call, research a lead, build a client dossier, qualify a prospect, or find out what a business actually does before pitching them. Also use before any client-facing engagement skill, since researched facts are what separate a specific deliverable from a template. Do NOT use for market sizing or competitor landscapes (use market-research-navigator), for verifying a single claim (use skill-research), or for building the training programme itself (use team-enablement-program).
---

# Prospect Discovery

## What this produces and why it exists

Five files from one company URL:

| File | Purpose |
|---|---|
| `<company>-dossier.md` | What is known, each claim cited. What is not known, listed as such. |
| `<company>-call-agenda.md` | Discovery call questions built from their actual business, not a template. |
| `<company>-intake.md` | The intake block for `team-enablement-program`, pre-filled where research allows. |
| `<company>-proposal-skeleton.md` | A draft proposal whose every commercial claim is marked as a hypothesis to confirm. |
| `<company>-covering-note.md` | Your own briefing: what you are confident about, what the call must settle, which details to use. |

Researching before pitching changes what the downstream documents can say. In one internal comparison — a single pair of runs, not a study — the same programme-writing skill produced roughly three times the density of client-specific terms when given researched input rather than a one-line brief. Treat that as an illustration of the mechanism, not as evidence: n=1, self-run, and the metric was our own. The mechanism itself is not in doubt, because a generator can only name tools, markets and instruments that its input contains.

## The rule that governs everything

**Every factual claim about the company carries a source label, or a gap marker (`UNVERIFIED`, `NOT FOUND`, `TO CONFIRM`). There is no third option.**

Hedging is not a third option. "The company states it handles 50,000 MT" is a *grade* — it tells the reader whose claim it is — and it still needs the label saying where the statement was read. `references/research-method.md` sets out the three grades; this rule is about citation, which applies to all three.

The failure mode this prevents is specific and expensive. Research produces a pile of plausible statements — some read off the company's own site, some inferred, some half-remembered from an adjacent industry. Once they are in one document they all look equally solid, and a prospect who checks one and finds it wrong discounts everything else. A dossier is only useful if the reader can tell which lines they can rely on.

The same standard applies to this skill's own prose. Where a reference file states a working rule — a stopping point, a rule of thumb about where time goes, a prediction about how a call will run — it is a convention adopted because it is useful, not a finding. Those are written as conventions. Anything phrased as an empirical fact about the world, in a document you hand a client, needs a source or it does not go in.

Two consequences worth internalising:

- **A company's own website is a source for what they claim, not for what is true.** "Largest importer of oils and fats into Benin" is cited as *the company states*, not as fact.
- **Inference is not research.** "They trade agricultural commodities, so they probably use WhatsApp" belongs in the call agenda as a question, never in the dossier as a finding.

## Step 0 — Before the first fetch

Two questions, both cheap, both expensive to skip.

**Is this account already someone's?** A colleague may own it, or it may have been pitched recently. Asking afterwards wastes the research and can embarrass you internally.

**Does this prospect conflict with a current client?** If they compete, the engagement may be closed to you regardless of what the research finds.

If you can ask the user, ask now. **If you cannot** — running unattended, or the user is not reachable — do not let that block the work: proceed, and put both questions at the top of the covering note as items to settle **before the call is booked**, not before the dossier exists. A dossier is cheap to discard; a call under an undeclared conflict is not.

## Step 1 — Establish identity before researching anything else

Get the legal entity right first, because everything downstream inherits the error if you do not. A run that spent its whole effort on the wrong spelling of a company name produces four confident, useless documents.

Fetch the site, then find the registered entity: the legal name, registration number, jurisdiction, registered address and status. Company registries, business directories and trade-data aggregators are the usual places to find it — though availability varies sharply by jurisdiction, and see the degraded mode below. Note explicitly when the trading name and the registered name differ, and when the site's founding date and the registration date disagree — both are common in family businesses and group structures, and neither is your call to resolve. Record both and flag it as a question.

**Degraded mode.** Registry access is not universal. Some jurisdictions publish no officer data, some charge for it, some rate-limit or block automated access, and sole traders have no entry at all. In both of this skill's own trial runs the registry step degraded — one jurisdiction had no free public search, and in another both aggregators refused the request. So a missing registry record is the normal case, not a failure:

- Proceed on the **trading identity** — the name, site and address the company publishes about itself — and record the entity fields as `NOT FOUND`, naming what was tried and why it failed.
- Say in the dossier what that costs: without a registry record you cannot confirm legal name, status or officers, which matters before a contract and should be verified then.
- Stop only when you cannot tell **which company this is** — two plausible matches, a name that resolves to nothing, or a site that identifies no entity at all. Uncertain identity is fatal; an unavailable registry is a gap.

## Step 1b — Fix the language of the pack

Decide once, at the start, and state it on the dossier. Two languages are in play and conflating them produces a pack nobody can use: the **prospect's language**, which governs anything that will be read by or quoted to them, and **your working language**, which governs the internal analysis.

At Step 1b you have not spoken to anyone, so the call language is an assumption — mark it `TO CONFIRM` on the dossier rather than stating it as settled. The working language is yours; take it from the language the request came in.

The default that works: write the pack in the language the call will be held in, keep the covering note in your own, and never translate a quotation without marking it as translated. A machine-translated registry status or legal form is a claim you cannot stand behind, so leave `d.o.o.`, `SARL`, `GmbH` and the like in the original with a gloss.

One file is exempt and it is easy to miss. **The intake block's field names stay in English**, whatever language the rest of the pack is in, because `team-enablement-program` matches on them mechanically — translate `Repeated tasks` and the receiving skill finds an empty required field. The content of those fields follows the pack's language as usual. `references/handoff.md` says so inside the template itself; this is the reminder that Step 1b does not override it.

## Step 2 — Research

Read `references/research-method.md` for what to search, in what order, and how to grade a source. In short: the company's own site and its subpages first, then the registry, then trade or industry data, then news and social. Prefer primary sources; treat aggregators as indicative.

Collect against the dossier structure in `references/dossier.md` so you are not reorganising later. Where a section has nothing, write `NOT FOUND` — an empty heading is information, a missing heading looks like an oversight.

Stop when new searches stop returning new facts. Depth beyond that buys nothing a discovery call would not answer faster.

## Step 3 — Write the dossier

Follow `references/dossier.md`. Cite inline. Then run the source check, using the full path to the script since the dossier will not be in the skill directory:

```bash
python3 /path/to/prospect-discovery/scripts/check_sources.py <company>-dossier.md --strict
```

It flags claims with no citation and no gap marker, and separately flags citation labels that are not defined in the Sources block — because a bracketed note is not a source. Run it with `--strict` and fix until it exits 0, then run it on the proposal skeleton and the intake block too.

Widening it past the dossier looks backwards and is not: the dossier is internal, and an error in it gets corrected in conversation. The proposal is the one file that becomes client-facing, so an uncited figure there is the expensive one — and on the run this guidance comes from, the proposal was the file that lost every citation it should have carried, precisely because the gate had never been pointed at it. When a line moves from dossier to proposal, its label and its grade move with it; "the company states" dropped in transit turns their claim into your assertion about them.

### Then the read-back pass, which is the one that finds things

**The checker is a floor, not a ceiling.** Exit 0 means every claim has the *shape* of a sourced claim. Nothing about its content has been checked, and nothing automated can check it — a regex cannot tell whether the page you cited says what you say it says.

That distinction is not theoretical. On the run this section comes from, `--strict` exited 0 while ten factual errors were still in the file. It caught none of them. All ten were found by reopening the sources.

So make that a step rather than an intention. Go back over the cited lines with each source open, and **read the source first and your claim second**. The order is the whole technique: a reader who already knows what the sentence was meant to say supplies the missing support without noticing, so reading your own sentence first is how a strengthened word survives three passes. Reading the source first makes the gap between the two visible.

Watch particularly for the failure modes in `references/research-method.md` under *Fidelity* — upgraded words, shortened lists, derived figures, platform furniture — and for a label that points at the right site but the wrong page, which the checker cannot see at all because the label resolves.

Reopening a dozen sources costs perhaps twenty minutes. It is the highest-yield twenty minutes in the whole method, and there is no substitute for it.

Two things it will tell you that are worth understanding rather than working around:

- **Hedging does not replace a label.** "The company states it handles 50,000 MT" still needs the label saying where that statement was read. The hedge sets the grade, the label lets the reader check it.
- **A `MIXED` finding means a gap marker and a figure share one sentence**, so the figure inherits an exemption it was never given. Split the sentence rather than rewording around the check.

**The gate is not equally strong in every language.** Figure, registration, field and table checks are language-neutral. Assertion detection covers English and Serbian; in any other language an uncited assertion will pass. The script says so when it sees a non-English file — treat that pack as partially checked and read the prose yourself.

If you find yourself rewording a true, well-sourced sentence to satisfy the regex, stop and report it — that is a defect in the checker, and `scripts/selftest.py` is where the fix gets locked in.

## Step 4 — Write the call agenda

Follow `references/call-agenda.md`. The agenda's value is entirely in question quality. A question anyone could ask any company wastes the slot; a question that could only be asked of this company proves you did the work and gets a real answer.

The agenda is built around what research **could not** establish — team size, tools, processes, ownership, what actually hurts. Those gaps are the agenda. If the dossier is honest about them, the agenda writes itself.

## Step 5 — Write the intake block

Follow `references/handoff.md`. This is the block that feeds `team-enablement-program`, pre-filled only where research supports it and marked `TO CONFIRM ON CALL` everywhere else.

Resist the temptation to fill it in. A plausible guess at a tool stack is the exact failure the receiving skill is built to refuse, and it arrives pre-laundered by having been written down in a document.

## Step 6 — Write the proposal skeleton

Follow `references/proposal.md`. It is a skeleton because a proposal written before the call is a guess with a price on it.

Every hypothesis about where their time goes, what an engagement is worth, or what they should do first is labelled as a hypothesis to test on the call. No fee appears — fees follow scope, and scope follows the conversation.

## Step 7 — Deliver, and to whom

**Two of the four files are internal and two are client-facing. They are not sent to the same person.**

| File | Audience | Header it must carry | Retention line |
|---|---|---|---|
| Dossier | You and your team only | `INTERNAL — NOT FOR THE PROSPECT` | yes |
| Call agenda | You only | `INTERNAL — NOT FOR THE PROSPECT` | yes |
| Intake block | You, and the engagement skill | `INTERNAL` | yes |
| Proposal skeleton | Becomes client-facing after the call | `DRAFT — NOT YET SENT` | yes |
| Covering note | You only | `INTERNAL — NOT FOR THE PROSPECT` | yes |

Put those headers on the first line of each file. **All five carry the retention line**, not just the dossier — every one of them names living people, and the two that get forgotten are the two nobody re-opens.

The retention rule and the moment you write it do not line up, and pretending otherwise is why the line goes missing. The clock runs 90 days from the call; at creation time no call is booked. So write both — the rule, and a fallback computed from the research date — and a pack for a call that never happens still expires:

> `Obrisati 90 dana posle discovery poziva. Ako poziva ne bude do 2026-10-30, obrisati tada.` The dossier contains a section on contradictions between what a company says publicly and what its registry shows, and a section of open questions about named officers. Forwarded to the prospect by accident, it ends the relationship — and a file with no marking on it gets forwarded eventually.

The covering note is the fifth file, `<company>-covering-note.md`, carrying `INTERNAL — NOT FOR THE PROSPECT.` on its first line. It goes to **your own side**, and states:

- The one thing you are most confident about, and why — and note that this prompt asks for exactly the unsourced synthesis the rest of the skill forbids. That is fine here, because the covering note goes only to you. It is fine **only** if the line says what it rests on, and says plainly when that is an inference rather than something you read. On the run this guidance comes from, the covering note's headline confidence was an inference presented as the surest thing in the pack.
- The one thing you most need the call to answer
- Which one or two researched details you intend to use on the call
- The two Step 0 questions, if they could not be answered before the research began

That last point is deliberately narrow. Two or three well-chosen details prove you did the work; reciting everything reads as surveillance, and `references/call-agenda.md` sets out what to hold back and why.

Before anything leaves, re-run `check_sources.py --strict` on the dossier. A dossier that was clean three edits ago is not clean now.

## Scope boundaries and adverse findings

**Read `references/scope-and-compliance.md` before Step 7** if research turned up litigation, insolvency, enforcement action, sanctions, or press alleging wrongdoing — it covers when to stop and escalate instead of writing, what never to research about named individuals, and how to handle the personal data a dossier necessarily collects (retention date, minimisation, deletion on close). Read it before starting research too if the individuals/addresses/paywall boundaries aren't already clear.

## Reference files

- `references/research-method.md` — search order, source grading, what each source type can and cannot establish
- `references/dossier.md` — dossier structure and citation format
- `references/call-agenda.md` — how to turn gaps into questions worth an hour of a director's time
- `references/handoff.md` — the intake block for `team-enablement-program`
- `references/proposal.md` — proposal skeleton and the rules on hypotheses
- `scripts/check_sources.py` — flags uncited claims and citations that resolve to nothing; run with `--strict` before delivering
- `scripts/selftest.py` — regression suite for the checker. Run `python3 scripts/selftest.py --mutate` once before your first client dossier: the plain pass checks the cases, the mutation pass verifies the suite would notice if the checker were weakened. An earlier version of this suite stayed green after an entire branch of the checker was deleted.

## Honest limits

- **Research establishes context, never operations.** No website says which CRM a team uses, how long a task takes, or who is difficult in a meeting. The gap between a well-researched dossier and a usable engagement brief is one conversation, and pretending otherwise produces confident nonsense.
- **Registry data lags.** Directors change, addresses change, status changes. Treat a registry record as of its date, and say the date.
- **Trade and shipment aggregators cover partially.** A count of four shipments may mean four shipments or may mean four that this provider saw. Never present an aggregator's absence of data as evidence of absence.
- **A dossier ages.** Put the research date and the deletion date on it. After a few weeks it is a starting point, not a briefing.
- **The checker is a floor, not a ceiling.** It catches uncited figures and dead labels. It cannot tell whether a cited source actually says what you claim it says, and nothing automated can. That check is yours.
- **Large groups break the intake block.** For a company of one team the required fields are unknown; for a group of fourteen entities they are not single-valued, and the honest move is to say the scope must be decided before the fields can have values rather than picking one.
