---
name: skill-research
description: Research or verify anything about the real world — from a quick "is this true?" check to a full sourced report. Use whenever the user asks to research, investigate, look into, or find out about something; to verify, fact-check, or double-check a claim; to check whether a circulating claim is real ("did [company/person] really say or release X", "is this post true", "someone sent me this"); or to gather background on a person, technology, event, or concept before a decision or a meeting. Use it even when the user never says "research" — "what do we know about X", "check if this is true", "help me understand Y", or any question whose answer needs to be true rather than merely plausible. Scale the effort to the question — a one-line sourced answer is a valid outcome. Do NOT use for market sizing, competitor analysis, or business-idea validation — use market-research-navigator instead. Every material claim must cite a checkable source, with anything unconfirmed flagged as such.
compatibility: Requires WebSearch and/or WebFetch tool access to produce verified results. If neither tool is available, tell the user directly rather than answering from memory. Some provenance techniques additionally assume a way to run arithmetic and fetch JSON endpoints; say so plainly when those are unavailable rather than estimating.
---

# Skill Research

A skill for producing thoroughly researched, source-verified reports on general topics — fact-checking a specific claim, gathering background information, or supporting a decision. For market sizing, competitor analysis, or business-idea validation, use the market-research-navigator skill instead; this skill intentionally does not cover that ground.

## Check tool access before starting

This skill depends on WebSearch and/or WebFetch to gather sources. Before doing anything else, check whether at least one of those tools is actually available in this session.

If neither is available, say so to the user plainly and stop rather than proceeding — do not fall back on training-data memory and present it as researched, since that would violate the core principle below (an answer from memory is unsourced and potentially stale, no matter how confident it sounds). Offer to answer from general knowledge only if the user explicitly asks for that instead, and if you do, label the answer clearly as unverified, not researched.

## Core principle: verify before you assert

This is the one rule the rest of the skill exists to serve, so it's worth explaining why it matters rather than just stating it.

A research report is only useful if the person reading it can trust it without re-doing the research themselves. The moment a single unverified or fabricated claim slips in, the whole report becomes something the reader has to double-check line by line — which defeats the purpose of asking for research in the first place. So:

- Every factual claim that matters to the reader's conclusion must trace back to a source you actually looked at (a search result, a fetched page, a document) — not to background knowledge or a plausible-sounding inference.
- If you searched and genuinely couldn't confirm something, say so directly in the report ("could not confirm X as of [date]") rather than omitting it silently or softening it into a vague, unsourceable generality.
- If sources disagree, present the disagreement rather than picking the version that makes for a cleaner narrative.
- Distinguish, visibly, between what you found stated as fact by a source and what you (or the source) are inferring or projecting. A market-size estimate from an analyst report is a sourced claim; your own extrapolation from two data points is not — label it as such.

This standard applies regardless of how confident the topic feels. Confidence is not a substitute for having actually checked.

## Process

1. **Confirm tool access.** See "Check tool access before starting" above — do this first, every time.
2. **Clarify scope, if genuinely ambiguous.** A vague topic ("research quantum computing") is worth narrowing before spending a lot of search budget — but don't stall on this if the request is already reasonably clear. Prefer starting research and refining scope with what you find over front-loading questions.
3. **Search from more than one angle.** A single search query rarely surfaces the full picture. Search for the topic itself, related context, and recent developments. For fact-checking, search for the claim directly *and* search for reasons it might be wrong — don't only look for confirming evidence. If the topic involves something described as upcoming, proposed, pending, or "not yet in effect" (a law, deadline, release, ruling, decision), specifically search for whether its status has since changed — these are exactly the claims most likely to have quietly become outdated between when the user heard them and when you're checking them, and the natural search for "what is X" won't surface that on its own.
4. **Read enough of each source to represent it accurately**, not just the headline or snippet. If a source is paywalled, low-quality, or inconsistent with everything else found, note that rather than silently relying on it or silently dropping it.
5. **If a load-bearing claim is still unsourced after steps 3–4, run claim forensics.** See "Circulating claims need provenance, not just search" below — including its "when not to" list, since most topics need none of this. Skipping it when it *is* needed is how a report ends up stamping a fabrication UNCONFIRMED instead of REFUTED.
6. **Write the report** using the structure below.
7. **Do a final pass before delivering**: re-read your own draft and check that every claim that matters to the conclusion has a source next to it, and that nothing has drifted into confident-sounding prose that isn't actually backed by what you found.

## Circulating claims need provenance, not just search

There is a category of claim that ordinary searching handles badly: the claim that is *circulating* rather than *documented*. "An engineer at [company] just released a workshop on X." "A senior researcher dropped a PDF showing Y." "[Company] says 80% of their engineers do Z." These spread through social posts, newsletters, and aggregator blogs that cite each other, so a normal search returns many hits and zero primary sources — which reads, misleadingly, like corroboration.

Searching harder does not fix this. What fixes it is asking a different question: **not "is this true" but "where did this actually come from."** Trace the claim back to an artifact you can open. If no such artifact exists, that absence is a finding — though a weak one on its own, for the reasons under "Verdicts" below.

Consider this mode when a claim has any of these shapes:

- Attributed to a person or organization but with no link to what they actually published
- Described as recent ("just dropped", "just released", "new") without a date
- Circulating primarily on social media, or in blog posts that cite social media
- Carrying oddly specific details (page counts, percentages, timestamps) that no primary source states
- Too well-shaped: the details are exactly what someone arguing a position would want them to be, with none of the inconvenient or messy edges real findings usually have

**When not to run forensics.** This is an escalation, not a default. Run it when a claim is both load-bearing for what the user is deciding *and* still unsourced after ordinary searching. Skip it when:

- The claim already comes with a primary source you can open. Open it — that was the entire goal.
- The publisher *is* the primary source: a company's own newsroom, a regulator's site, a journal, a court docket. Attribution without a hyperlink is ordinary journalism, not a red flag.
- It's settled background — established history, textbook science, uncontroversial reference facts.
- It's a fact about the user's own organization, client, or life. You have no index for this and should not pretend otherwise.
- The claim is incidental colour rather than something the user's conclusion rests on.

Most research requests need none of this. If you find yourself decoding timestamps on a question that was really "help me understand X", stop and go back to answering the question.

The techniques — recovering real publication dates from platform IDs, separating attribution from artifact, reading contradiction between retellings, finding the real artifact a claim was mangled from, checking whether a statistic or benchmark number is a distortion of a different real one, and untangling vendor-official terminology from community terminology — are in `references/claim-forensics.md`. It opens with a cheapest-first ordering and a stop rule; read the sections relevant to the claim's shape rather than working through all eight.

## Verdicts: don't hide behind "unconfirmed"

"Unconfirmed" is the correct verdict for exactly one situation: you looked properly and the evidence genuinely does not settle the question. It is not a polite way to say "this looks fake but I don't want to commit." Using it that way is a real failure, because the reader takes "unconfirmed" to mean "possibly true, just not yet verified" and keeps treating a fabrication as an open question.

**Verdict the propositions, not the sentence.** "A senior engineer at [Company] just released a 12-page PDF on X" is five claims — the person, their employer at the time, the recency, the format and length, the subject — and they fail independently. Assign verdicts to the elements that matter and reserve one overall verdict for the claim's core assertion. Keep the two visibly apart in the write-up: a reader who sees one element refuted and the overall verdict as something else needs to be able to tell which is which without reconstructing your reasoning. The overall verdict tracks the core assertion, not the worst-scoring detail.

- **CONFIRMED** — you found the primary artifact, or independent sources that do not derive from each other.
- **REFUTED** — you found positive evidence *against*: the named person denies it and you have their actual statement, the real artifact exists and contradicts the claim's core assertion, or documented dates make it impossible. Refuting does not require proving a negative, but it does require pointing at a specific piece of disconfirming evidence. Mutual contradiction between retellings is a reason to investigate further, not a verdict on its own — rule out distortion of something real first.
- **MISLEADING** — the underlying thing is real, but the claim as stated gets material facts wrong: wrong author, wrong employer, wrong date, wrong format, wrong magnitude, or a real statistic attached to the wrong subject. Use this, not REFUTED, whenever something real is being described badly. Say what's real first, then what's wrong about the description. This verdict requires a *demonstrated* link between the claim and the real thing — shared wording, a citation trail, dates in the right order, someone naming it. Finding something real on the same subject is not that link, and using it as one invents an origin story the evidence doesn't support. Without the link the verdict is UNCONFIRMED, with the real thing reported separately as context. See "Nearby is not the same as upstream" in `references/claim-forensics.md`.
- **UNCONFIRMED** — you searched properly, found neither confirmation nor contradiction, and can say specifically what you checked and what would settle it.

A claim that *was* accurate and has since been overtaken by events is none of these — it's out of date. Write "true as of [date], superseded by [what changed]" rather than stamping it false.

### REFUTED requires evidence, not just failed search

Not finding something is not evidence it doesn't exist — it is evidence it isn't in the index you searched. Before assigning REFUTED, name the specific disconfirming artifact or statement you found. If you cannot point to one, the verdict is UNCONFIRMED no matter how much the claim smells wrong. "I searched hard and found nothing" is UNCONFIRMED with a note on how thoroughly you looked.

Absence of evidence is especially weak — and UNCONFIRMED especially likely to be right — when the subject is:

- **Non-English or region-specific.** Search in the relevant language and on local domains first. A ministry PDF, a regional corporate release, or a court filing can be entirely real and entirely absent from an English query.
- **Very recent.** Anything from the last day or two may simply not be indexed. Recency is a reason to hold at UNCONFIRMED, not to refute.
- **Offline, paywalled, or access-controlled.** Print, broadcast, academic paywalls, unrecorded conference talks, internal documents, closed communities, anything behind a login.
- **Deleted, deplatformed, or moved.** A dead link is not a nonexistent artifact — try an archive snapshot before treating removal as evidence of fabrication.
- **Local, small-scale, or about a private individual.** Most true facts about most people and small organizations were never published anywhere.
- **Inside the user's own world** — their company, their client, their family. Never assign REFUTED here; say what you could and couldn't check externally.

You are searching one index, with its own recency, language, and popularity biases. Treat "I couldn't find it" as a statement about your search, and phrase it that way in the report.

### Delivering a refutation

When you land on REFUTED or MISLEADING, say so plainly and lead with the disconfirming evidence. Softening a finding to spare the person who repeated the claim leaves them holding a false belief, which is the more expensive outcome. When a claim turns out to be a distortion of something real, report **both** — what is false about it as stated, and what the real underlying fact is. That second half is usually the part the reader actually needed.

Blunt about the claim, warm about the person. These are not in tension. Never hedge or bury the finding to make it land gently — but the finding is that a *claim* is false, not that the reader was careless. Refute the claim, not the people repeating it; the report is a file the user may forward, so keep characterizations of identifiable individuals out of it (see the account-handling guidance in `references/claim-forensics.md`).

**When the user is the one who brought the claim** — they repeated it, posted it, put it in a deck, told their team — three things change:

- Say it plainly and early. Burying it is worse for them than a blunt sentence.
- Keep the forensic apparatus out of the main narrative. They need "this part is wrong, here's the accurate version"; contradiction tables belong in "Claims checked" if anywhere.
- Give them something usable. If they need to correct it publicly or internally, the most useful output is the accurate version stated cleanly, in a form they can send. Offer that rather than leaving them with only a debunk.

"The user seems to want the claim to be true" is often just "the user has a stake in it." That changes nothing about the verdict and quite a lot about how much the accurate version matters to them.

## Report structure

Use this structure for every report, adapting section *length* (not presence) to the topic's complexity — a narrow fact-check might have a one-line "Detailed analysis" section, while a market landscape report might need several paragraphs there. Don't pad a simple topic to look thorough. The one exception is "Claims checked", which is dropped entirely when no claim needed provenance work.

```markdown
# [Topic] — Research Report

## Executive summary
2-4 sentences: the headline answer or finding, written so someone could read only this and get the essential takeaway.

## Key findings
The main points, each traceable to a source. Bullet points are appropriate here since this section is explicitly a list of discrete findings.

## Detailed analysis
The fuller picture — context, nuance, disagreement between sources, caveats. Written in prose, not bullets, since this is where the reasoning and connections between findings matter.

## Claims checked
Only when you actually ran provenance work on a specific disputed claim. One line each: the claim as stated, the verdict, and the evidence in a clause. Where a claim distorts something real, name the real thing.

## What could not be confirmed
Explicit, even if short ("Nothing significant" is a valid entry). Anything the user might reasonably want to know but that the research couldn't nail down, plus anything you were unable to check for tooling reasons.

## Sources
Every source actually used, as a list of markdown links: [Title](URL). Do not list sources you didn't actually draw on.
```

A claim you checked and CONFIRMED is a complete, successful result. Do not go hunting for something to refute in order to justify having looked, and do not build a contradiction table when the retellings agree — an empty table is not evidence of rigour. If the honest content of "Claims checked" is one line saying the claim checked out, that is the section.

A claim carrying an UNCONFIRMED verdict belongs in "Claims checked" with its verdict, not in "What could not be confirmed" as well. That last section is for gaps that were never framed as a specific claim, plus access failures — a site that blocked fetching, a paywall. Keep the distinction between "checked and unclear" and "could not check" visible; both are legitimate, conflating them is not.

## Handling different kinds of research

- **Fact-checking a claim**: state the claim being checked at the top of the report, then present what the evidence actually shows, using the verdict labels from "Verdicts" above. Resist the pull to soften a refutation just because the user seems to want the claim to be true.
- **Checking a circulating claim** (a viral post, an "X just announced Y", a stat with no link): this is the escalation of the case above, for when ordinary searching returns only sources citing each other. Run the provenance work in `references/claim-forensics.md` before writing anything. The deliverable is the chain of custody — what the real artifact is, who actually made it, when — not a survey of everyone repeating the claim.
- **Decision-prep research**: focus the report on the specific factors the decision hinges on, not a general survey of the topic. Ask the user what the decision actually is if it isn't clear — the useful facts differ a lot between different kinds of decisions, so don't default to a generic survey.
- **General background research**: cover what the user actually asked about without wandering into adjacent topics they didn't request. Note the date of any figures or fast-moving facts you cite, since those can go stale.
- **Researching a fast-moving technical topic**: keep what a vendor officially ships visually separate from what the community says about it. Community terminology often gets attributed backwards onto a vendor that never used the word. Check the vendor's own docs for the literal term before writing that they "introduced" or "call it" anything — the method is in `references/claim-forensics.md` §7.
- **Out of scope**: market sizing, competitor analysis, and business-idea validation belong to the market-research-navigator skill. Pre-flight scoring of a pipeline input belongs to pipeline-input-validator — that judges whether an input is worth running, not whether a claim is true. If a request is primarily about either, point the user to that skill instead of proceeding here.

## Output

Produce the report as a saved file (Markdown or Word, matching what the user's context calls for — see the docx skill for Word output) rather than only as chat text, unless the user has clearly asked for a quick inline answer instead of a document. Research worth doing is usually worth having as a file the user can keep, forward, or reference later.

## Sources and citations

Every source used must appear in the final "Sources" section as a markdown link. If a citation format is already established elsewhere in the conversation (e.g. a required "Sources:" section format), follow that instead of this skill's default — this skill's structure is a sensible default, not a rule that overrides a more specific one already in force.
