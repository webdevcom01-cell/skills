# What goes in each client file

Write these after the runs, never before. Every behavioural sentence carries `[EV:AT-0n]` or a gap marker; the checker will find the ones that do not.

---

## 1. `<agent>-delivery-note.md`

**Write the second section first.** The limits section is the one that prevents an argument; the capability section is the one that sells. Writing limits first stops the selling voice from leaking into them.

### What it does

One paragraph in the client's vocabulary, not the flow's. Then the capabilities, each tagged:

> Given a lead description, it returns a score from 0 to 100, a fit band, and the reasons behind both `[EV:AT-01]` `[EV:AT-03]`. The fit band is always one of low, medium or high `[EV:AT-02]`.

### What it deliberately does not do

Not a disclaimer — a specification. This section needs no evidence tags, because stating a limit under-promises, and an under-promise costs nothing.

Cover, at minimum:

- **What it will not touch.** It does not send email, does not write to your CRM, does not change any record.
- **What it refuses.** Input with no lead in it is refused rather than guessed at `[EV:AT-04]`.
- **What it assumes, and where that assumption lives.** This is the one people skip and regret. If the agent scores against an ideal-customer profile held in its knowledge base, say so and say what that profile contains — otherwise the client's own largest account gets scored low in month two and the call is unpleasant.
- **What was not tested.** Non-Latin input, very long input, concurrent use — whatever you did not run. `NOT TESTED` is a complete and honest answer.
- **What it is not.** It is not a decision. A human decides; the agent sorts.

### What it costs to run

Only what you can state as fact: the model it runs on, and the typical round-trip time you observed, tagged. No monthly figure unless the client's billing is in front of you.

Two traps here, both of which caught the first live pack:

- **The model name is a configuration fact, not a behaviour.** It comes from `as_get_agent` and needs a `--kind config` record; `[EV:AT-01]` cannot support it, and the checker reports `CONFIG_CLAIM` if nothing does. The same is true of a node count, a flow id and an eval-suite name.
- **A round-trip range must be the range the cited records measured.** Writing "about 10 s to 21 s [EV:AT-01] [EV:AT-03]" when those two records hold 20.5 s and 9.7 s is a fabricated upper bound, and `FIGURE_OUTSIDE` will say so. Cite the record the number came from, and do not quote a scoring time from a refusal case — a refusal is faster and is not a lead.

### What this document does not cover

One short list: legal advice, data-protection assessment, security review, and the correctness of the agent on inputs nobody tested. Say who they should ask instead.

---

## 2. `<agent>-acceptance-test.md`

The centre of the pack, and the only document that changes the commercial conversation. Structure:

**How to run it yourself.** Numbered, exact, and written for someone who has not seen Agent Studio: open the agent, paste this input, compare against the expected line. If they cannot re-run it, the rest of the document is a claim like any other.

**The cases.** One block each — never a table, because the inputs are too long to read sideways:

> ### AT-04 — Input with no lead in it is refused
> **Intent:** the agent should refuse.
> **Paste this:** `hey, can you help me?`
> **You should see:** the agent refuses and names the missing field, instead of inventing a company.
> **Result on 2026-07-31:** PASS `[EV:AT-04]`
> **How that was decided:** the response contains `BLOCKED`.

Every field earns its place. `How that was decided` is what stops the result being an opinion — the client can see the rule, disagree with it, and propose a better one, which is a far better conversation than "trust me".

**What the result does and does not mean.** Two sentences, and do not soften them:

> These seven cases ran on the date shown and produced the results shown. They say nothing about inputs outside them, and they are not a measure of accuracy.

**Re-running after a change.** Whoever changes the agent re-runs the suite. Say it here and repeat it in the maintenance terms.

---

## 3. `<agent>-failure-plan.md`

Four facts. A plan with three of them is not a plan.

| | |
|---|---|
| **Owner** | A person's name, not a department. The one who is called. |
| **Alert** | How they find out — who notices, watching what. "Nobody is watching" is an honest and useful answer; write it if it is true. |
| **Fallback** | Exactly how the work gets done by hand while the agent is off, written so someone who has never done it can follow it. |
| **Kill switch** | The specific action that stops it, and who is allowed to take it. |

Then: **what "broken" looks like here.** Silence, an error, a plausible answer that is wrong — the third is the dangerous one and the hardest to notice, so name what to watch for. If the agent has no monitoring, that sentence belongs here, plainly, and it is often what sells a maintenance retainer without a single word of selling.

---

## 4. `<agent>-handover.md`

**The register.** One row per item, with a named person against each — the agent itself, its prompt, its knowledge base and every document in it, the credentials, the account it runs under, the evaluation suite, and this pack.

Every id, node count and suite name in that register is a configuration fact. Either it carries a `[EV:CFG-0n]` tag pointing at a recorded `as_get_agent` snapshot, or it is `[TO CONFIRM]`. A register full of confident ids nobody can check is the part of the pack a client's own engineer will test first.

**Who may change what.** Which changes are safe for the client, which require you, and which void the acceptance result. Editing the prompt or the knowledge base changes behaviour and invalidates the test — this is the single most common way a delivered agent quietly stops matching its documentation.

**What you keep.** Be explicit about your own copies, templates and notes, and about how long you hold the client's material. This paragraph costs nothing to write and answers a question clients often do not ask out loud.

**What is not transferred.** Third-party accounts, model provider terms, anything under someone else's licence.

---

## 5. `<agent>-maintenance-terms.md`

Marked `DRAFT` until fees are agreed — the checker enforces the pairing, so a file with `[TO AGREE]` in it and no `DRAFT` marker will not pass.

See `references/maintenance.md`. Included, chargeable, response expectations stated as intentions rather than commitments, who may change the agent, and what ends the arrangement.

---

## 6. `<agent>-internal-note.md`

Marked `INTERNAL` at the top. Not gated by the checker, because it is where you write what you actually think.

- What the runs really showed, including anything that made you uneasy
- Which claims you wanted to make and could not, and what it would take to make them
- Which cases are weak, and which rule would fail a bad answer
- What you would test next, with more time
- What the client is likely to discover on their own, and when
