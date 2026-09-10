# Changelog

## 0.2.5 — 2026-08-21

**Fixes the one defect the 0.2.4 eval found.** That eval (13 runs, `evals/README.md`) came back
1 PASS / 12 FAIL, and all twelve failures were a single criterion: Working-depth orientation
memos ran **1963–3213 words against a stated "one to two pages" budget, and not one of the
twelve acknowledged the overrun** anywhere in the deliverable or in stdout.

**Why the existing instruction did not work.** The budget was not missing. `assets/orientation-
memo.md` has carried "Length: one to two pages" since 0.2.3, and even told the model to say so
out loud if the material outstripped it. It was prose: no number, no counting step, no point in
the workflow where the draft is measured against it. 12 of 13 runs read that line and sailed
past it. A stated goal the model never converts into a check is not an instruction, it is a
decoration.

**What changed.** STEP 6 gains a **length gate** — executed before the file is written, not held
in mind. Count the body with `wc -w`; at or under ~1200 words finalize as-is; meaningfully over,
take exactly one of three visible branches: **(a)** cut lowest-priority content (never §6, §7 or
the ledger — that trades the falsification record for page count), **(b)** escalate to Full depth
per STEP 0.5 and name it as the reason, or **(c)** declare the overrun in §0 Provenance with the
actual count and why it would not compress, at the same standing as a STEP -1 capability gap. An
over-budget memo with none of the three is a failed deliverable regardless of ledger quality.
`assets/orientation-memo.md` is updated to match on both ends: the length block now states the
number and points at the gate, and §0 Provenance carries a conditional `Length` bullet that is
where branch (c) lands.

**The ledger counts toward the budget and cannot be trimmed to buy room.** Stated explicitly,
because the tempting cheat is to shrink the falsification record to make page count. If post-fix
runs cluster in branch (c) — memos that genuinely cannot compress because a mandatory ledger eats
most of 1200 words — the honest reading is that the two-page budget is wrong for this template,
and the *budget* should move in a later version. The discipline of declaring should not.

**Spot-check only, and it does not prove the fix.** One fresh Working-depth run against a target
not used in the original 13 (`evals/smoke-length-fix.md`). A single run cannot establish that a
12-of-13 systematic defect is closed; the other twelve targets have not been re-run against
0.2.5. `status` and `evaluation_status` say so rather than claiming the defect is fixed.

**One honesty cost, recorded.** The gate's 1200-word threshold is the same number `evals/
RUBRIC.md` used to grade the failures. The skill is now specified against its own test on this
criterion, so a future eval of P4 is no longer fully independent. The number is independently
defensible (two pages at 600 words/page, which is where the rubric got it too), but anyone
reading a future P4 pass should know the target was set by the grader.

No other content changed. References, the as-built spec and the rebuild plan are untouched.

## 0.2.4 — 2026-08-20

**The eval that 0.2.3 recorded as blocked is now done.** 13 headless `claude -p` runs, one per
target, across all four target types (3 codebase, 3 web, 3 AI system, 4 binary/protocol), model
`claude-opus-5[1m]`. Graded against a rubric written to disk 2026-08-19 21:48, before twelve of
the thirteen runs' outputs existed. Rubric, per-run grades, verbatim prompts, agent stdout and
full deliverables are all under `evals/`. No skill content changed in this release — only
`metadata.version`, `metadata.status` and `metadata.evaluation_status`, which now describe
measured behaviour of the 0.2.3 content instead of carrying 0.2.2 numbers forward.

**Result: 1 PASS / 12 FAIL.** The pass is `codebase-2`, the only run that escalated to full
depth, which it did while naming the cue that triggered it.

**What works.** 13 of 13 runs produced an enumerated falsification ledger whose
confirmed+downgraded+dropped arithmetic matches its actual row count. Several went further than
the rubric required: `binary-1` reported that a held-out capture disconfirmed one of its own
claims; `binary-3` dropped 5 claims including the eval prompt's own false premise; `binary-4`
dropped a claim after held-out disconfirmation; `ai-3` falsified its target's `content_hash`
field by substituting 64 zeroes and observing `passed: true`; `codebase-1` refused to execute
`install.sh` against the real `$HOME` and labelled its diff STATIC-ONLY per STEP -1;
`codebase-3` refused to verify quotes from training memory. This is the behaviour the skill
exists to force and it held across every target type.

**What does not work, and is now a known open defect.** All 12 failures are the same criterion.
Working-depth runs came in at 1963–3213 words against an `assets/orientation-memo.md` template
that asks for "one to two pages," and not one acknowledged the overrun in the deliverable or in
stdout. The template states a length; nothing in the skill instructs the model to check its
draft against that number or to say so when it exceeds it. Fix belongs in the skill, not in the
rubric — candidate for 0.3.0.

**Limits of the measurement, recorded rather than smoothed over.** n=1 per target, so no
run-to-run variance was measured. Runs and grading come from the same model family; P1/P2 are
mechanical enough to survive that, P3 and the capability-gap half of P4 are not. `raw-binary-2`
completed four minutes before the rubric file was written, so that one run's
rubric-independence rests on assertion rather than timestamps. `ai-1`'s first attempt died on a
429 usage limit and the re-run inherited its probe scaffolding, making it a continuation rather
than a clean-room repeat — the run disclosed this itself. As a partial check on all of it, every
one of the 13 grades was mechanically re-derived from the artifacts afterwards (word count,
ledger N, the three-way sum, distinct C-id count) and all 13 reproduced. Full write-up in
`evals/README.md`.

**Not re-tested here.** Triggering precision/recall, which 0.2.2 measured at 100% precision
across 10 near-miss negatives. Those figures are not carried forward as current.

## 0.2.3 — 2026-08-19

Both items this file has carried as "0.3.0 candidates" since 0.2.0 are closed. No eval yet —
that is still blocked in this environment (see below) — so `status` is downgraded from
"evaluated" to "evaluated at 0.2.2; 0.2.3 changes not yet evaluated" rather than carrying the
0.2.2 numbers forward onto content they never measured.

**Tooling availability column.** `references/codebase.md`'s tooling table listed Structure101,
Sourcegraph public code search, and Pyan without saying whether they were still around. Checked
2026-08-19 by web search: Sourcegraph public search is live and free; Structure101 is no longer
sold standalone (Sonar acquired it and folded it into their platform); Pyan (`pyan3`) is
actively maintained, revived February 2026, v2.6.0 shipped 2026-04-30. The other ~10 tools in
the table are marked "not checked" rather than left silently implying they were verified too.

**Orientation-memo template.** Working-teardown depth had a description ("a one-page memo:
findings table, ledger, what you could not determine") but no template, the only depth without
one. New `assets/orientation-memo.md`, deliberately not a shrunken as-built spec: written in an
explanation register rather than reference, one page to two, one diagram (C4 Level 1 only).
Design grounded in Diátaxis's explanation quadrant, C4's stated audience split between Level 1
and Level 2, arc42 §1 (which turns out not to address this — a useful negative result), README-
Driven Development's small-by-design discipline, and George Fairbanks's Architecture Haiku,
which is the closest existing precedent for this exact genre. Five places in SKILL.md now point
to it (Outputs list, STEP 0.5 table, STEP 6, Reference loading table) and the as-built spec's
old "at Working depth this collapses to..." note — which would have contradicted the new
template — is rewritten to say Working depth has its own file now.

**Still blocked, not done here.** Re-running the eval (this skill's own `evaluation_status`
pointed at `system-teardown-workspace/`, which could not be located or reproduced from this
session — see the project's punch-list and implementation-plan docs for the full trail) needs
an environment where `claude -p` opens an isolated session per call. This one does not: two
consecutive `claude -p` invocations returned the same `session_id`, tied to the container, not
to the invocation. That part of the work is still owed, from a different environment, before
this file's numbers can honestly cover 0.2.3.

## 0.2.2 — 2026-08-16

Evaluated. No behavioral or description change — the description scored at ceiling, so it was
kept verbatim. Only the frontmatter status and this record changed.

**Output quality** (with-skill vs no-skill baseline, one test case per target — a real 85-line
Flask codebase on disk, a live web fetch of example.com, a third-party chatbot from observed
behavior; 5–6 assertions each, graded on the four priorities): with-skill **100%** (16/16),
baseline **24%** (4/16), delta **+0.76**. Cost ~2x wall time and +40% tokens — the price of the
falsification work the baseline skips.

The decisive pattern: every baseline pass was a case where a capable model happened to find a
fact or hedge once; **no baseline produced a falsification ledger, a provenance tag, or a "what
we could not determine" section in any of the three runs.** The v0.2.1 enumerated-ledger fix
demonstrably fired — all three with-skill runs emitted a ledger with claims enumerated by ID, not
an empty shell. Honesty discriminators held: the with-skill web run left CDN/host UNCONFIRMED
with the exact `curl -sI`/`dig` to settle it while the baseline named a CDN vendor from memory;
the with-skill AI run flagged citation fabrication as "the single most important caveat."

**Triggering** (20 queries — 10 trigger, 10 near-miss — 3 runs each, 5 iterations, 60/40
train/held-out, run via `claude -p`): on completed runs, **100% precision in every iteration**
(no mis-fire on any of the ten near-misses — the boundaries against prospect-discovery,
market-research-navigator, prompt-engineer-pro, soma-agent-debugger, agent-dependency-mapper,
skill-research, and engineering:documentation all held), **90–100% held-out recall**. The one
recall miss was a single run of the competitor-chatbot Serbian query; it passed 2/2 in another
iteration. The optimization loop's proposed rewrites were discarded: it ran under heavy `claude
-p` 30s timeouts (~30% of runs lost to infrastructure, not triggering), so no candidate could be
shown to beat a description already at 100% on the clean signal. Description kept verbatim.

Still open for 0.3.0 (unchanged by the eval): no onboarding-document genre for the codebase
target; a few discontinued tools listed without an availability column.

## 0.2.1 — 2026-08-16

Focused regression pass over the v0.2.0 deltas by two independent reviewers who did not write
the skill. It found two real holes in the new mechanisms and six cheap regressions from the
15-place edit. All fixed here; no new features.

**The ledger was arithmetically circular (blocking).** N was defined as confirmed + downgraded +
dropped, but dropped claims leave the document — so a reviewer counting `[INFERRED]` tags sees
only confirmed + downgraded, never N, and the "check N against the claim count" the skill
advertised could not be performed. The model controlled both numbers. Fixed by making the
ledger's core an **enumerated list**: each inferred claim gets an ID, a disposition, and an
evidence pointer to the row that settled it; N is the length of that list; every CONFIRMED body
claim must appear by ID and vice versa. Coverage denominators are now tied to countable
artifacts (edges in the diff, INFERRED rows, captured messages) plus a "system scale examined"
line, so "2 of 2 divergences resolved" can no longer read as complete coverage of a thousand-file
system.

**Quick depth was a clean bypass (blocking).** A model could pick Quick to owe no ledger, and the
two most hallucination-prone questions — a third-party stack, a third-party chatbot — landed
there by the depth table's own examples. Over-claiming was guarded, under-claiming was not.
Fixed three ways: Quick is now stated to perform **no** falsification (it was mislabeled as
falsification-by-tagging); the depth statement must name the request cue that selected the depth,
making under-classification visible; and a Quick answer to a third-party stack/architecture
question must come from an observation or say what could not be seen, never from training memory.
Hard rule 2 now covers silent *downgrade*, not just silent skip.

**Regressions fixed:** SKILL.md cross-reference "§16" → "§16a" (the section was renamed in the
template and 0.2.0's CHANGELOG wrongly claimed this was reconciled); `ai-system.md` deliverable
"Confidence-tagged" → "Verdict-tagged" (a survivor of the eliminated third vocabulary);
`binary-protocol.md` protocol procedure given a `[USER]`/`[MODEL]` split (it was still flat
imperative for user-run capture and probing); `codebase.md` heading "Ten failure modes" →
"Eleven" (mode 11 was added in 0.2.0); `binwalk` removed from the B1 `[MODEL]` triage body
(it is not available here and was already listed as unavailable two lines up).

Measured: SKILL.md 305 lines, ~4.1k tokens; description 1,007 chars; still within all limits.

Still not done: no evals. The two deeper items 0.2.0 deferred (no onboarding-document genre for
the codebase target; discontinued tools without an availability column) remain open for 0.3.0.

## 0.2.0 — 2026-08-16

Revision after an adversarial review by four independent reviewers with no context of the
skill's authorship: a cold structural read, a test of eight author-stated hypotheses, a trace of
three realistic user requests, and a fact-check of every load-bearing claim against primary
sources. Verdict on 0.1.0 was **not ready for use**. This release addresses the blocking
findings.

### The finding that drove the redesign

Three reviewers independently reached the same diagnosis: the skill had **one gear** — a
multi-week engagement — and when a request did not fit that gear, the model abandoned the
process while keeping its vocabulary. It emitted a Reflexion-shaped table it had not computed,
tagged the first two tables and then stopped, filled an evidence column without ever naming an
alternative explanation. The reader saw a falsified teardown; there had been no falsification.

That is precisely the pathology the skill exists to prevent, manufactured by the skill's own
design. Two changes address it.

**STEP 0.5 — depth selector.** Quick read / working teardown / full engagement, chosen from the
request rather than asked about, with falsification defined at each depth. An unsatisfiable rule
does not get followed, it gets rationalised — and rationalising it is how a model learns to fake
the table. A rule scaled to what the situation permits is a rule that gets obeyed. A smaller
coverage number is now explicitly a weaker claim, not a failure.

**Falsification ledger.** STEP 5 now terminates in an artifact with an arithmetic check
(`confirmed + downgraded + dropped = inferred claims entering`), a per-target coverage number,
and an explicit "falsification NOT performed, and why" line. In 0.1.0 the mandate was three
sentences of prose with no mechanism; a mechanism existed for the codebase target only, by
accident of the arc42 template. Any claim in the output but not in the ledger's confirmed set is
now written UNCONFIRMED.

### Other blocking fixes

- **STEP -1 capability check**, per target, stating floor / full / what-to-do-with-only-the-floor.
  In 0.1.0 the most operationally decisive information sat in the frontmatter and the last twelve
  lines of the body, after the handoff table — the model started working before reaching it.
- **`[MODEL]` / `[USER]` labels** in `web-product.md` and `binary-protocol.md`. Both files were
  written in flat imperative for work the model cannot perform: DevTools, HAR export, proxy
  chains, account signup, disassembly. Only the binary file had admitted this.
- **Binary triage reclassified as executable.** `file`, `strings`, `objdump`, `readelf`, `nm`
  are available here; a blanket "reference-only" label was causing the skill to decline work it
  could do. B1 now returns a real GO/NO-GO; B2–B3 remain user-run.
- **Output contract in STEP 6** — file name, location, and an instruction not to paste the whole
  document into the conversation. 0.1.0 said "fill the template" and never said where it went.
- **Description no longer forbids the AI target's main use case.** It excluded "auditing or
  fixing an agent you own", which closed off the branch `ai-system.md` is mostly written for —
  reconstructing your own undocumented system. Now scoped to remediation only.
- **"What we could not determine" reconciled.** SKILL.md claimed both templates had a section
  the rebuild plan did not contain; it is now §16a in the spec and §6 + §10 in the plan, named
  in both.
- **Clean-room gate rewired to fire on contamination, not on ambition.** 0.1.0 triggered a
  two-team procedure whenever the user wanted to build something comparable, including for users
  who had contaminated nobody, and then refused to continue. Now: a contamination question
  first, and a small-team variant for teams that cannot staff two walls.

### Factual corrections

- **Ryanair v. Booking.com** — the August 2024 CFAA verdict was **vacated on JMOL, 22 January
  2025**, and the court rejected the exact proposition 0.1.0 taught as its lesson: generic
  investigation and response costs are not CFAA "loss" absent technological harm. On appeal to
  the Third Circuit. This was the only affirmatively false claim in the skill.
- **Van Buren** — footnote 8 expressly reserves whether contract or policy limits can define the
  "gates". 0.1.0 stated ToS-based theories were rejected outright; the Court declined to say so,
  and the whole US framework rested on that sentence.
- **hiQ v. LinkedIn** — 0.1.0's lesson ("the CFAA claim failed, the contract claim had teeth")
  was wrong. hiQ conceded CFAA *and* Cal. Penal Code §502 liability over **fake accounts**, paid
  $500,000, and destroyed derived algorithms. Since fake accounts are on this skill's refusal
  list, understating this weakened the skill's own rationale.
- **The 61% static call graph figure** — real (ISSTA 2024, arXiv 2407.07804) but measured on
  **1,000 Android apps**, driven by Android framework callbacks, against dynamic ground truth at
  ~8% coverage. 0.1.0 presented it three times as a universal law of static analysis, once in
  the headline Core principle section. Now scoped, sourced, and stated once.
- **The 12% symbol-level figure** — the paper reports 12% by a2a and **7% by MoJoFM**, against
  *include* dependencies on a mostly C/C++ corpus. 0.1.0 quoted the better metric only.
- **Chikofsky & Cross** — 0.1.0 gave the paper's purpose statement as its definition of reverse
  engineering. Corrected, along with the reengineering definition.
- **RPE (arXiv 2411.06729)** — the genetic algorithm's fitness is **ROUGE-1 based**; embedding
  cosine similarity is the paper's evaluation metric, not its inner loop. Also flagged as a
  preprint.

### Corrections to reasoning, not just facts

- **Ablation logic was invalid as written.** "If removal changes nothing, the instruction was
  never there" does not follow — it means the instruction is not load-bearing *on your battery*.
  Conditional guardrails ("never name a competitor", "if the user is in the EU…") are inert on
  most inputs by construction and are exactly what a teardown needs to find; naive ablation
  prunes them first. Now: design a triggering case before dropping anything, else downgrade to
  UNCONFIRMED.
- **TCP stream reassembly was missing entirely** from the protocol procedure, which went from
  "build a corpus" straight to "tokenize and align" as though each packet were a message. It is
  the most common practical failure in trace-based protocol RE. Added as step 3, with snaplen
  truncation called out.
- **"The spec is wrong, not the message"** replaced with a four-way triage: truncated capture,
  unreassembled framing, mixed protocol versions, then wrong specification.
- **The alternative-explanation requirement in `web-product.md` is now a table column**, not
  prose. Anything that is not a column does not get filled in.
- **Timing noise floor** added to the AI passive scan, which was drawing six architectural
  conclusions from latency shape while the same file — correctly — insisted that reporting
  agreement without a variance floor is the standard error in this work.
- **Failure mode 11: coupling through shared state.** Two components sharing a table, a topic, a
  cache namespace, or a path are coupled with no static edge and no import to find.

### Coherence

- **Hard rules cut from six to three.** Four of the six restated procedural steps stated
  unambiguously elsewhere; rule 3 appeared three times across two files. A rule restated is a
  rule readers learn to skim, and the skim generalises to its neighbours — which is how the one
  rule with no other enforcement was getting lost.
- **"Confidence" eliminated as a third vocabulary.** It appeared 14 times across five files,
  never defined, sometimes a synonym for verdict and sometimes a separate column. Verdict *is*
  the confidence scale; the `Confidence` columns are renamed.
- **MISLEADING restored to the verdict set.** `skill-research` has four verdicts, not three, and
  MISLEADING — *the documentation says X, the code does Y* — is the most common verdict in a
  codebase teardown. 0.1.0 dropped it while claiming to reuse the house vocabulary.
- **Router self-collision fixed** ("undocumented API" appeared under both web and binary), with
  tie-break rules and explicit signals for mobile apps and Electron.
- **Templates no longer leak editorial** into the deliverable — guidance is in a
  do-not-copy block or in italics, with an instruction in STEP 6.
- **arc42 numbering restored.** Sections 1–12 keep canonical numbers; RE additions are lettered.
- **~45 lines of dead table-of-contents blocks removed** from reference files, plus roughly 40
  lines of verbatim duplication between SKILL.md and reference files.

### Description

Dropped `"kako ovo radi"` (fires on anything; collides with `skill-research`) and
`"napravi isto ovo"` (a build request, which the skill body refuses). Added Serbian triggers for
the AI and binary targets, which were unreachable in Serbian. Added `engineering:documentation`
and `skill-research` to the negative list — the two nearest collisions, neither of which was in
the 0.1.0 overlap analysis. Reviewers refuted the worry about `prompt-engineer-pro` and
`agent-architect`: those barely overlap.

### Measured

- SKILL.md: 274 lines, ~3.5k tokens (limits: 500 lines / 5,000 tokens)
- description: 1,007 of 1,024 characters — 17 characters of headroom
- compatibility: 390 of 500 characters
- frontmatter: five of the six spec-allowed fields (`allowed-tools` unused)

### Still not done

No evals. Description triggering remains unoptimized. Reviewers noted two open items this
release does not address: `codebase.md` has no orientation/onboarding output genre — its two
templates are an architecture reference and a rebuild plan, and "help my team understand this
system" is neither — and several named tools are discontinued (Structure101, Sourcegraph public
code search, Pyan) without an availability column. Both are candidates for 0.3.0, after evals
say whether they matter.
