---
name: system-teardown
description: "Reconstruct how an existing system works when documentation is missing, then produce an as-built spec or a rebuild plan. Four targets: a codebase you did not write, a live web product, an AI prompt or agent inferred from behavior, a binary or network protocol. Use when the user says reverse engineer, teardown, reconstruct the architecture, recover the design, figure out how X is built, what stack does X use, or Serbian: reverse inzenjering, rekonstruisi arhitekturu, naslijedjeni kod koji niko ne razumije, koji stack koriste, koji prompt koriste, sta radi ovaj exe. Do NOT use for market or competitor landscapes (use market-research-navigator), a commercial dossier from a company URL (use prospect-discovery), fixing or hardening an agent you own (use soma-agent-debugger), agent call graphs (use agent-dependency-mapper), writing a new prompt (use prompt-engineer-pro), documenting a system you already understand (use engineering:documentation), or checking one external claim (use skill-research)."
license: Proprietary. LICENSE.txt has complete terms.
compatibility: Capability differs per target and per depth — STEP -1 in the body states the floor, the full requirement, and what to do when only the floor is available. Binary/protocol triage is executable here; disassembly is not, and is guided rather than performed. Never answer a stack or architecture question from training memory when the tool to observe it is missing; say what is missing instead.
metadata:
  version: "0.2.5"
  owner: "buky <webdevcom01@gmail.com>"
  status: "evaluated at 0.2.4 (1 PASS / 12 FAIL, 13 runs); 0.2.5 fixes the sole failing criterion, spot-checked on one run only"
  evaluation_status: "Behavioural eval of v0.2.3 content, 2026-08-19/20: 13 headless runs, one per target (3 codebase, 3 web, 3 AI system, 4 binary/protocol), n=1 each, model claude-opus-5[1m], graded against a rubric pre-registered on disk before the runs (evals/RUBRIC.md). Result 1 PASS / 12 FAIL. Falsification machinery held: 13 of 13 emitted an enumerated ledger whose confirmed+downgraded+dropped arithmetic matches its row count, several disconfirming or dropping their own claims. All 12 failures were one criterion — Working-depth memos ran 1963-3213 words against a 1200-word budget with the overrun never acknowledged. 0.2.5 addresses exactly that with an executed length gate in STEP 6 plus a numeric budget in the template. That fix is spot-checked on a single fresh run (evals/smoke-length-fix.md), NOT re-evaluated: one run cannot establish that a systematic 12-of-13 defect is fixed, and the other 12 runs have not been repeated against 0.2.5. The gate's 1200-word threshold is the same number the rubric used, so a future eval of this criterion is no longer fully independent of the rubric that motivated it. Other limits in evals/README.md: n=1 per target, self-graded by the same model family, binary-2 completed 4 minutes before the rubric file was written, ai-1 is a continuation of a usage-limit-aborted run. All 13 grades were mechanically re-derived from the artifacts and reproduced. Prior 0.2.2 output-quality and triggering figures are superseded and were not re-measured."
---

# System Teardown

Recover the design of a system that already exists, from evidence rather than from
assumption, and write it down in a form someone else can act on.

Outputs, depending on depth (STEP 0.5) and on what the user asked for:

- **A direct answer** — for a single question. No template.
- **An orientation memo** — one session's worth of teardown, aimed at understanding rather
  than reference. Template: `assets/orientation-memo.md`
- **As-built technical spec** — what the system *is*. Template: `assets/as-built-spec.md`
- **Rebuild plan** — how to build an equivalent. Template: `assets/rebuild-plan.md`

## Core principle: a teardown without falsification is a confident hallucination

Reconstruction is easy; reconstruction that survives contact with reality is hard; and the
two are indistinguishable when you read the report. Four independent professional traditions
converged on the same countermeasure:

| Target | The falsification step practitioners use |
|---|---|
| Codebase | **Reflexion Model diff** — hypothesized architecture vs extracted facts, iterated until every divergence and absence is explained |
| Web product | **Evidence column, then attack it** — each `[INFERRED]` row must survive a named alternative explanation |
| AI system | **Ablation + differential test** against a probe battery with a measured variance floor |
| Binary/protocol | **An independent parser consumes 100% of the corpus**, plus a held-out capture |

STEP 5 is where this happens and it terminates in a **ledger** — an artifact you cannot
produce by narrating. Falsification you cannot show in the ledger did not happen.

## STEP -1 — Can you actually do this?

Check before anything else and say the answer out loud. Capability differs per target, and
the honest floor is more useful than a confident guess.

| Target | Floor | Full | With only the floor |
|---|---|---|---|
| Codebase | Read/Glob/Grep/Bash over a checkout on disk | plus a build that runs, a test suite, a live DB | Phases 0–3 and 5 only. Every behavioral claim ships UNCONFIRMED. Label the Reflexion diff *static-only*. Never analyze a repo from a description of it. |
| Web product | WebFetch or a browser MCP — HTML, JS, public spec files | headers, HAR, DevTools, accounts: **the user runs these** | Fingerprint from HTML/JS only. Say which signals you could not obtain. Never answer a stack question from memory. |
| AI system | live query access to the target | a programmatic harness for a repeatable battery | Passive surface scan only. State that no ablation was run. |
| Binary/protocol | `file`, `strings`, `objdump`, `readelf`, `nm`, `sha256sum`, `python3` — B1 triage **is** executable | a disassembler, debugger, VM, packet capture — **user-run** | Do the triage and hand back a real GO/NO-GO plus a string and import inventory. Guide B2–B3; never narrate an analysis you did not perform. |

## STEP 0 — Authorization gate

Ask directly unless the conversation already answers it:

1. **Whose system is it?** Yours, your employer's, a client's under contract, public or
   open-source, or a third party's.
2. **What is the access path?** Owned copy, written authorization, ordinary permitted use,
   or public unauthenticated observation.
3. **What is the goal?** Understanding, interoperability, migration, security review, or
   building something comparable.

When the answers are obvious from the request, do not interrogate — state the conclusion in
one line and move on. A gate that produces a visible sentence can be checked; a silent one
cannot.

Third party plus no written authorization means: **observation from ordinary permitted use
and public artifacts only**, said out loud in the output, and no extraction techniques.

Read `references/legal-boundaries.md` whenever the target is not the user's own, whenever a
competitor is mentioned, or whenever the plan involves automated collection, authentication,
or anything compiled.

## STEP 0.5 — Depth

Pick from the request; do not ask. Most requests are not engagements, and escalating a
question into a document is how a teardown becomes ceremony the user abandons.

| The user asked for | Depth | What stands in for falsification | Output |
|---|---|---|---|
| A single fact — "what stack does X use", "how is this bot built" | **Quick read** | none — Quick performs **no falsification**. It relies on honest provenance: every claim not directly observed is UNCONFIRMED, with one line on what would confirm it | a direct answer, a few sentences |
| Orientation — "how does this work", "help my team understand this" | **Working teardown** | the target's method at reduced scale, ledger included, coverage stated as the small numbers it is | orientation memo, explanation register, 1-2 pages. Template: `assets/orientation-memo.md` |
| A document someone will act on — spec, handover, rebuild | **Full** | the target's method at full scale | the template |

State the depth you chose in one line **and name the cue in the request that selected it** — so
an under-classification (picking Quick to avoid the ledger) is visible and accountable, not
silent. The deadline guard runs both ways: never claim Full and under-deliver, and never drop to
Quick to escape STEP 5 on a question that deserves a teardown.

**Quick read is not a licence to guess.** It performs no falsification, so it may only report
what was observed. When the target is a third party's and the question is about its stack or
architecture, a Quick answer must come from an actual observation (a header, a bundle, a visible
behavior) or say plainly what could not be seen — **never from training memory**. "Probably
GPT-4 with RAG" tagged UNCONFIRMED is exactly the confident hallucination this skill exists to
stop. If you cannot observe and the user needs an answer, that is a Working teardown, not a Quick
one.

A smaller coverage number is a weaker claim, not a failure. **12 probe cases honestly labelled
beats 200 claimed.**

## STEP 1 — Route

Resolve the target from the signals, state which signal decided it in one line, then proceed.
Ask only when two rows genuinely tie.

| Target | Signals | Load |
|---|---|---|
| Codebase | repo, checkout, "inherited this codebase", "nobody knows how this works", legacy, migration, Electron/Tauri app (readable JS) | `references/codebase.md` |
| Web product | URL, competitor's app, "what stack", SaaS teardown, HTTP/JSON API seen in a browser, mobile app you can proxy | `references/web-product.md` |
| AI system | chatbot, LLM app, agent, prompt inference, tool inference, "how is this agent wired" | `references/ai-system.md` |
| Binary/protocol | .exe/.so/.bin/firmware, pcap, custom wire framing, "what does this binary do" | `references/binary-protocol.md` |

**Tie-breaks.** Source on disk → codebase, whatever the artifact is; if it is also an LLM app,
do codebase for structure then a second ai-system pass. An API over HTTP/JSON in a browser
session → web. An API with custom binary framing, or only a pcap → protocol. A question about
an LLM's behavior rather than its transport → AI. Mobile app (.apk/.ipa) → web, via proxy
capture; only the compiled internals are the binary target.

Two targets in one request run as sequential passes, never blended. Each gets its own freeze,
facts, and ledger.

## STEP 2 — Freeze

Pin what is being examined. An artifact without a pin is unfalsifiable — nobody can later tell
whether a finding was wrong or the system simply changed.

Codebase → commit SHA, branch, build and test state. Web → URL, capture timestamp, account
tier, geography. AI → endpoint, model version if visible, date, sampling settings. Binary →
SHA-256, version string, acquisition source.

At Quick read depth this collapses to a date and an identifier. Do not skip it entirely.

## STEP 3 — Gather facts

Follow the loaded reference file. Tag every fact as you record it:

- `[OBSERVED]` — you saw it happen or read it directly
- `[TOOL]` — a tool reported it; name the tool and the command
- `[INFERRED]` — you concluded it; state from what

Tag at the level of a table row or a discrete finding, not every clause of prose. Prefer
sources that produce queryable facts over sources that produce pictures — a picture cannot be
tested against a hypothesis.

## STEP 4 — Hypothesis

Draw the model and mark which parts are inferred rather than observed. Those are what STEP 5
attacks. A hypothesis with no inferences is not a hypothesis, it is an inventory.

Draft from structure, ownership, deployment units, and domain vocabulary. Automated clustering
or detection tools give a second opinion, never the primary answer.

## STEP 5 — Falsify, and emit the ledger

Applies at Working and Full depth. Quick read does not run STEP 5 — see the note at the end.

Use the target's method from the reference file. Then produce this ledger. It goes in the output
as its own block, and its core is an **enumerated list**, not a set of free integers — that is
what makes it hard to fake:

```
FALSIFICATION LEDGER
Target: <codebase|web|ai|binary>   Depth: <working|full>
Method: <Reflexion diff | evidence-column attack | ablation + differential | independent parser>

Inferred claims (one row each — this list IS N):
  C1  <claim>   → CONFIRMED   evidence: <the §5 row / evidence-table row / battery case that settled it>
  C2  <claim>   → UNCONFIRMED evidence: <what was attempted, why it did not settle>
  C3  <claim>   → DROPPED     evidence: <the disconfirming result>
  ...
  N = <count of rows above>   confirmed a / downgraded b / dropped c   (a+b+c=N)

Coverage denominator (a number you did NOT choose freely):
  codebase → divergences+absences resolved: x of y, where y = all edges in the Reflexion diff
  web      → INFERRED rows with a ruled-out alternative: x of y, where y = all INFERRED rows in the doc
  ai       → battery cases run: x   variance floor: z%   ablated instructions: p of q reconstructed
  binary   → messages parsed: x of x captured   held-out: y of y

System scale examined (so a small y cannot masquerade as complete):
  <e.g. 12 of ~340 source files read · 3 of 18 API endpoints traced · 1 of 6 plan tiers observed>

Unresolved, filed to §16a "What we could not determine": k
Falsification NOT performed, and why: <or "none">
```

Two rules make the numbers mean something:

- **Every CONFIRMED claim in the body must appear by ID in this list, and vice versa.** N is the
  length of the enumerated list, not a number you assert. A reviewer counts the rows. A model that
  skipped falsification cannot produce n distinct evidence pointers that also resolve to rows
  elsewhere in the document.
- **The coverage denominator is a countable artifact, not a figure you pick** — total edges in the
  diff, total INFERRED rows in the document, total captured messages. Pair it with the *system
  scale* line so that "2 of 2 divergences resolved" cannot read as complete coverage of a
  thousand-file system.

Any claim in the output whose ID is not in this list, or is listed as anything but CONFIRMED, is
written UNCONFIRMED (or dropped) in the body too. The ledger and the body agree by ID or the run
is not finished.

Where the method could not run — no runtime access, no capture, no authorization — say which
falsification was not performed, why, and what it would take. That is a useful result. Omitting
the step and reading complete is not.

Confirmation bias is the live risk. When evidence fits the hypothesis, ask what else would
produce the same evidence before accepting it.

## STEP 6 — Output

At Quick read depth: answer directly, tagged, with one line on what would confirm it. No file,
no template, no ceremony.

At Working depth: fill `assets/orientation-memo.md`, write it to `<target>-orientation.md` in
the working directory, and tell the user the path. Do not paste the whole document into the
conversation. This is a different template from Full depth's, not a shrunken copy of it — see
the template's own header for the register and length it requires.

**Length gate — Working depth, run this before you write the file.** The budget is **1200
words of deliverable body** (two pages at 600 words per page), counted across §0–§8 including
the ledger block. The ledger counts and cannot be trimmed to buy room; if it is large, the
prose around it has to be correspondingly tighter or you take branch (c) below.

This is a gate you execute, not a goal you hold in mind. The budget existed as prose from
0.2.3 and 12 of 13 evaluated runs sailed past it — 1963 to 3213 words — without one of them
noticing (`evals/README.md`). Reading the instruction is demonstrably not enough.

1. **Count it.** `wc -w` the draft, or count it. Do not estimate from feel — estimating is the
   thing that failed.
2. **At or under ~1200 — finalize as-is.** No note, no ceremony.
3. **Meaningfully over — do exactly one of these three, and the choice must be visible in the
   deliverable itself, not in your reply to the user:**
   - **(a) Cut to fit.** The default. Trim lowest-priority content first: §8 pointers, §4
     decisions the reader can infer from §3, and any prose restating a ledger row. Never buy
     room by dropping §6 or §7, or by thinning the ledger — that trades the falsification
     record for page count, which is the one trade this skill exists to refuse.
   - **(b) Escalate to Full depth** per STEP 0.5, if the target genuinely warrants the space.
     Name it as the reason and name the cue, exactly as STEP 0.5 requires: an escalation you
     do not announce is an under-classification wearing better clothes. Then use the Full
     template — do not ship an oversized memo and call it Full.
   - **(c) Declare the overrun.** If neither cutting nor escalating is honest, state the
     deviation in **§0 Provenance** — the actual word count, the budget, and why the material
     would not compress. Same standing as a STEP -1 capability gap: visible at the top of the
     document, in the document.

An orientation memo over budget with no (a), (b) or (c) is a failed deliverable, however good
its ledger is.

At Full depth: fill `assets/as-built-spec.md` or `assets/rebuild-plan.md`, write it to
`<target>-as-built.md` or `<target>-rebuild-plan.md` in the working directory, and tell the
user the path. Same rule: do not paste the whole document into the conversation.

Copy only headings and tables from the templates. Lines explaining *why* a section exists are
instructions to you, not content for the reader.

All three deliverables require the ledger and a section recording what could not be
determined — §6 and §7 in the orientation memo, §16a in the as-built spec, §6 plus §10 in the
rebuild plan. None may be empty. A document without it presents the boundary of your
investigation as the boundary of the system, and the reader has no way to see the difference.

---

## Hard rules

1. **Never assert behavior you did not observe executing.** Static structure is a hypothesis;
   observed execution is evidence. Static call graphs are measurably unsound wherever there is
   reflection, dependency injection, or dynamic dispatch — see `references/codebase.md` for the
   measured recall figures and their scope.
2. **Falsification is never silently skipped, and never silently downgraded.** At Working and
   Full depth, emit the ledger; where the method could not run, name it, say why, and say what
   it would take. At Quick depth there is no ledger — but Quick may only report observations, and
   choosing Quick to escape a teardown the request deserved is the skipped-falsification failure
   wearing a different label.
3. **Recovered proprietary source contaminates a rebuild.** Anyone who read the target's
   source, decompiled output, or extracted prompt is contaminated. Before writing a rebuild
   plan, read `references/legal-boundaries.md` on clean-room separation.

## Verdict vocabulary

One axis, not two. `skill-research` semantics, all four verdicts:

- **CONFIRMED** — evidence supports it, and you name the evidence.
- **REFUTED** — you have positive disconfirming evidence. A failed search is not one.
- **MISLEADING** — surviving documentation, a README, a comment, or an ADR describes something
  real but materially wrong. Say what is real first, then what the description gets wrong.
  This is the most common verdict in a codebase teardown; do not collapse it into REFUTED.
- **UNCONFIRMED** — you looked properly and could not settle it. Say what would.

**Confidence and verdict are the same axis.** These four words *are* the confidence scale — no
percentages, no High/Medium/Low, no second column. Every claim carries exactly one provenance
tag from STEP 3 and exactly one verdict.

## What this skill refuses

Declined regardless of framing, and the refusal is stated plainly rather than worked around:

- Malware analysis and exploit development
- Circumventing protections: DRM, license checks, authentication, rate limits, WAF, bot defenses
- Access behind a login or paywall that is not the user's own; probing other users' data;
  fuzzing or enumeration without written authorization
- Fake or pretextual accounts created to gain access
- Extracting a third party's proprietary system prompt in order to copy it

Name the specific boundary and offer the legitimate adjacent path — usually architecture
inference from ordinary permitted use, or the same work against a system the user owns.

## Handoffs

This skill recovers design. It does not fix, sell, or rebuild.

| The user now wants | Use |
|---|---|
| The report tested on a real reader | `doc-coauthoring` |
| The findings as an interactive artifact | `web-artifacts-builder` |
| To fix an agent the teardown found problems in | `soma-agent-debugger`, or `safe-agent-builder` |
| A compliance verdict rather than a description | `enterprise-agent-readiness` |
| Market sizing or a competitor landscape | `market-research-navigator` |
| A commercial dossier and call agenda | `prospect-discovery` |
| One external claim verified | `skill-research` |
| Docs for a system they already understand | `engineering:documentation` |

## Reference loading

One level deep, on demand. Three of the four target files never enter context.

| Situation | Load |
|---|---|
| Target resolved in STEP 1 | the matching `references/*.md` |
| Target is not the user's own, or is a competitor | `references/legal-boundaries.md` |
| User wants to build something comparable | `references/legal-boundaries.md`, clean-room section |
| Writing at Working depth | `assets/orientation-memo.md` |
| Writing at Full depth | `assets/as-built-spec.md` or `assets/rebuild-plan.md` |

## Honest limits

Third-party traffic and revenue estimates are useful for rank order and trend direction only;
report the spread between vendors, never a point estimate as fact.

Legal notes in `references/legal-boundaries.md` are orientation, not legal advice. Several
cited decisions are district-level or on appeal. For anything commercially consequential the
answer is a lawyer, not this skill.
