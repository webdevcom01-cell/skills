---
name: agent-delivery-pack
description: Turns an agent you have already built into something a client can accept, own and be handed — five client-facing documents plus the receipts behind them. Runs an acceptance test against the live agent through the Agent Studio MCP, records each run with the server's own execution record, and writes the real dated result into the document instead of the words "it has been tested". Use when handing an agent to a client, or on "delivery pack", "handover", "acceptance test", "sign-off", "what do I send the client", "how do I charge for maintenance", or Serbian "primopredaja", "prijemni test", "predaja agenta klijentu", "dokumentacija za klijenta", "šta šaljem klijentu", "održavanje i cena". Also use before invoicing an agent build. Do NOT use to build or fix an agent (agent-scaffolder, safe-agent-builder, soma-agent-debugger), or to audit it against an enterprise bar (enterprise-agent-readiness).
compatibility: Requires Agent Studio MCP (as_chat_with_agent, as_get_agent, as_get_recent_executions, as_inspect_flow, as_list_agents, as_list_eval_cases, as_list_evals) to gather the live evidence a delivery pack cites, plus Python 3 (stdlib only) to run scripts/record_evidence.py, scripts/check_pack.py and scripts/selftest.py. Every claim in a delivered pack must resolve to a recorded as_chat_with_agent or as_get_recent_executions payload -- without Agent Studio access there is nothing to cite and the pack cannot be produced.
allowed-tools:
  - Read
  - Write
  - Bash
  - mcp__agent-studio__as_chat_with_agent
  - mcp__agent-studio-db__as_chat_with_agent
  - mcp__agent-studio__as_get_agent
  - mcp__agent-studio-db__as_get_agent
  - mcp__agent-studio__as_get_recent_executions
  - mcp__agent-studio-db__as_get_recent_executions
  - mcp__agent-studio__as_inspect_flow
  - mcp__agent-studio-db__as_inspect_flow
  - mcp__agent-studio__as_list_agents
  - mcp__agent-studio-db__as_list_agents
  - mcp__agent-studio__as_list_eval_cases
  - mcp__agent-studio-db__as_list_eval_cases
  - mcp__agent-studio__as_list_evals
  - mcp__agent-studio-db__as_list_evals
---

# Agent Delivery Pack

## What this produces

Seven things from one agent that already exists and runs:

| File | Who reads it |
|---|---|
| `<agent>-delivery-note.md` | The client. What it does, what it deliberately does not do. |
| `<agent>-acceptance-test.md` | The client. The test, the real result, and how to run it again themselves. |
| `<agent>-failure-plan.md` | The client. Owner, alert, manual fallback, kill switch. |
| `<agent>-handover.md` | The client. What they own, what they hold, what a change costs. |
| `<agent>-maintenance-terms.md` | The client. Included, chargeable, and who is allowed to change it. |
| `evidence/*.json` | Nobody, until someone disputes something. Then everybody. |
| `<agent>-internal-note.md` | You. What the runs actually showed, and what you must not claim. |

The pack exists because the gap between a working agent and a delivered agent is not code. A client who cannot test the thing themselves has bought a promise; a client who can test it has bought an asset. And an agent handed over without a named owner and a kill switch becomes the consultant's problem permanently, unpaid.

## Two rules that govern everything below

**One. Nothing about the agent's behaviour goes into a client file unless a recorded run supports it, or the file says plainly that it was not tested.** Not "should", not "is designed to". The client will hold the document, not the intent behind it. Claims carry `[EV:CASE-ID]`; everything else carries a gap marker.

**Two. No legal, compliance, security or outcome claim, in any file, under any circumstances.** Not "GDPR-compliant", not "secure", not "production-ready", not "saves 12 hours a week". You are not a lawyer, the runs do not measure hours, and a document that says these things is a document a client can point at later. `scripts/check_pack.py` refuses each of those outright — a tag does not buy them — and the correct response to that refusal is to delete the sentence, never to soften the checker. Describing the *absence* of such work stays legal and is what you write instead: "no security review has been carried out."

**And a corollary that cost us a live pack.** A tag is not a fact. Where the record can settle the question the checker now compares the two, so a `PASS` beside a case the record failed, or a duration outside the range the cited runs measured, is a finding rather than a citation.

---

## Step 0 — Before you run anything

Two questions, and the second one is not optional.

1. **Which agent.** `as_list_agents` if the name is not exact.
2. **Is it safe to run.** The acceptance test calls the live agent. If that agent sends messages, writes to a knowledge base, calls another agent, posts to an external system or spends money, then running it seven times has real effects. Read its flow first (`as_get_agent` shows the node summary; `as_inspect_flow` shows the wiring) and **ask the user before running an agent that writes anywhere.** If the answer is no, say so and stop — a delivery pack without runs is not a delivery pack.

**If the Agent Studio MCP is unavailable**, do not produce the pack. Produce the acceptance-test plan alone, mark it `NOT RUN`, and say what is missing. A pack whose evidence directory is empty is worse than no pack, because it looks finished.

## Step 1 — Read the agent as a stranger would

Collect, and keep the raw output:

- `as_get_agent` — model, description, node summary, when it last changed
- `as_list_evals` and `as_list_eval_cases` — an existing golden set is the best possible starting point for the acceptance cases
- `as_get_recent_executions` — has it run at all, and did those runs succeed

**Record the configuration before you touch anything else.** The model, the node count, the flow id, when it last changed — these end up in the delivery note and the handover register, and no acceptance case can ever evidence them, because they are not behaviour. Save the `as_get_agent` reply verbatim and record it:

```
python3 scripts/record_evidence.py --case-id CFG-01 --kind config \
  --label "agent configuration as read on the day" --payload agent.json --out-dir evidence
```

Then write `Model: gpt-4.1-mini [EV:CFG-01]`. Without that record the sentence is your memory of a tool call, and the checker will say so — `CONFIG_CLAIM` is the category, and it fires on model names, node counts and ids.

Two things you are looking for specifically, because they end up in the delivery note:

- **What the agent silently assumes.** A scorer with an ideal-customer profile in its knowledge base will rate the client's own best leads low if their business does not match that profile. That is not a defect, but a client who discovers it after signing will call it one.
- **What it refuses.** An agent with a gate has a refusal behaviour, and that refusal is the most valuable thing in the pack — it is the part that makes the agent trustworthy rather than merely fluent.

## Step 2 — Agree the acceptance cases

Between four and seven cases. **At least two must be cases the agent is supposed to refuse.** A suite of happy paths proves the agent talks; only a refusal proves it has a floor.

Each case needs, before anything runs:

- a plain-language label the client will understand
- an intent: `pass` or `block`
- a rule that decides it, in the small language `record_evidence.py` accepts: `contains:` `not_contains:` `regex:` `json_has_key:` `json_key_in:key=a,b`
- what the client should see, in the client's words

Write the rule **before** the run. A rule written after seeing the output is not a test, it is a description.

See `references/acceptance.md` for how to choose cases that a client will accept as fair.

## Step 3 — Run them and record the receipts

For each case, in this order:

1. `as_chat_with_agent` — save the entire JSON reply verbatim to a file. Do not retype it.
2. `as_get_recent_executions` for that agent, `limit` 3 — save that verbatim too.
3. `python3 scripts/record_evidence.py --case-id AT-01 --label "..." --intent pass --rule json_has_key:score --expected "..." --chat chat.json --exec exec.json --out-dir evidence`

The second call is the point. `as_chat_with_agent` tells you what the agent said; `as_get_recent_executions` is the server's own record that the run happened, with a server-side timestamp and an execution id **anyone with access can look up afterwards**. The script cross-checks the two and records how strong the corroboration is. It will not report `CONFIRMED` on a run it cannot corroborate, and it computes `PASS` or `FAIL` from your rule rather than from your opinion.

Two things about attribution, because both bit the first live pack:

- **`--exec-id` chooses which execution is written down. It does not prove which one ran.** If two runs emitted the same output — routine for a gated agent, whose refusals are identical — the record stays `ambiguous` and names both ids even when you pin one. That is the honest state, and pinning cannot improve it.
- **If nothing in the execution list matches the response**, the record says `unmatched`, carries a note saying the stored id may belong to another case, and the gate reports `UNATTRIBUTED`. Fetch the executions again, closer to the run, rather than shipping it.

A `FAIL` is recorded, not deleted. If a case fails, you have three honest options and no fourth: fix the agent and re-run, change the claim, or tell the client. `check_pack.py` will find a recorded failure that no document mentions.

## Step 4 — Write the five client files

Follow `references/pack-contents.md` for what goes in each. Three things matter more than the rest:

- **The "what it does not do" section is the most important paragraph in the pack.** Write it before the capability section. It is the section that stops an argument in month four.
- **Every behavioural sentence carries `[EV:AT-0n]`.** If no case covers it, either add a case and run it, or write `NOT TESTED`.
- **Fees stay `[TO AGREE]` and the file stays marked `DRAFT` until they are agreed.** The checker enforces this pairing.

## Step 5 — The gate

```
python3 scripts/check_pack.py <agent>-*.md --evidence evidence --strict
```

Clean, or the pack is not finished. The glob is safe: a file whose first 400 characters carry `INTERNAL` is skipped and said to be skipped, so the internal note stays out of the gate without you having to remember to exclude it.

The categories, in the order it reports them:

| | |
|---|---|
| `FORBIDDEN` | a refused phrase — guarantee, compliant, *is* secure, production-ready, 100% |
| `VERDICT_MISMATCH` | the document says PASS where the record nearest it says FAIL |
| `WRONG_RECORD_KIND` | a verdict or a duration cited to a `--kind config` snapshot |
| `UNSOURCED_VERDICT` | a verdict word with no `[EV:...]` within 200 characters |
| `UNCLOSED_FENCE` | a code fence opened and never closed, so the file is read as prose |
| `DANGLING` | an evidence tag that resolves to nothing |
| `BURIED_FAIL` | a recorded failure that no document mentions |
| `UNATTRIBUTED` | a record whose execution could not be tied to its response |
| `FIGURE_OUTSIDE` | a duration outside the range the records it cites measured |
| `FIGURE` / `MIXED` | an untagged figure, or one sharing a sentence with a gap marker |
| `CONFIG_CLAIM` | a model, node count or id with no `--kind config` record behind it |
| `CLAIM` | an untagged capability claim |
| `DUPLICATE` | two evidence files claiming one case id — one of them is hiding the other |
| `PLACEHOLDER` | `[TO AGREE]` in a file whose first 1000 characters carry no `DRAFT` marker |

`--strict` additionally fails on weak corroboration and on evidence recorded but never cited. Run strict before delivery; lenient is for drafting.

What the gate reads, because each of these was once a way past it: zero-width characters are removed first, so a phrase split by an invisible character is still that phrase; a verdict is compared with the record cited in its own row *item*, so a table row holding two results attributes each to the right case; a negation governs only what follows it inside its own clause, so "it blocks every domain and never lets one through" is an assertion followed by a hedge, not a denial; and a duration is judged against the runs unless a configured limit or a conditional stands beside it.

Headings are read too, but only for the refused vocabulary — "## Fully automated scoring, guaranteed" is caught, while "## How the agent scores a lead" is a section title and is left alone.

The file the gate skips must carry `INTERNAL` (or `NOT FOR THE CLIENT`) **alone on a line**, optionally as a heading. `INTERNAL REF: LS-2026-014` is a reference, not a marker, and does not switch the gate off.

**Never edit the checker to make a pack pass.** If you believe a finding is wrong, add the case to `scripts/selftest.py` first, watch it fail, then fix the checker and confirm the mutation pass still catches a deliberately weakened version. `python3 scripts/selftest.py` must end at zero failures before the pack ships.

## Step 6 — Deliver

Send the five client files. `evidence/` and the internal note stay with you — the evidence directory is not secret, but it is raw, and raw material invites arguments about the material rather than the result. Offer it if asked; it is the whole reason the pack can be trusted.

Tell the client one sentence they will remember: **they can run the acceptance test themselves, today, and get the same answer.** That sentence is what the deterministic part of this skill buys.

---

## What this skill cannot do, stated plainly

- It cannot prove the agent behaves correctly on inputs nobody tested. Seven cases are seven cases.
- It cannot detect that a run's output is *wrong* — only that it matched or did not match a stated rule. A rule that is too loose passes a bad answer.
- It cannot stop a determined author from hand-writing an evidence file. The corroboration check and the server execution id make a fabricated record awkward and checkable by a third party; they do not make it impossible.
- It checks a tag against its record only where the record can settle it: verdicts, and figures carrying a time unit. A percentage, a count or a score beside a valid tag is still checked by you and nobody else.
- A `--kind config` record proves what `as_get_agent` returned on the day, not that the agent still matches it. Re-record it if the handover is weeks after the run.
- Half its categories are deterministic and half are not, and the difference matters when you read a finding. `VERDICT_MISMATCH`, `FIGURE_OUTSIDE`, `WRONG_RECORD_KIND`, `DANGLING`, `DUPLICATE`, `BURIED_FAIL` and `UNATTRIBUTED` compare a document against a record and are exact. `FORBIDDEN`, `CLAIM`, `CONFIG_CLAIM` and `FIGURE` read English and Serbian prose with regular expressions, and prose does not submit to those. Three rounds of adversarial testing closed thirty-odd holes in them and the thirty-first exists. Treat the first group as findings and the second as a reviewer who is right most of the time — and when it is wrong, add the sentence to `scripts/selftest.py` before touching the pattern.
- It says nothing about law, data protection or security, by design. If the client needs those, they need a lawyer and a security review, and the pack should say so.

## Reference files

- `references/acceptance.md` — choosing cases, writing rules, what a fair test looks like
- `references/pack-contents.md` — section-by-section content for the five client files
- `references/maintenance.md` — the maintenance and ownership terms, and the claims that must never appear in them
