---
name: automation-triage
description: Decides which of a client's repeated tasks are worth automating, which to teach a person instead, and which to tell them not to touch — computed from ten stated fields per task and your own build economics, never from a feeling. Runs after the discovery call, on tasks the team said in their own words. Produces a ranked triage, a client-facing list of what is not worth automating, and a handoff to the next skill. Use on "what should we automate", "which tasks are worth automating", "build or train", "is it worth building an agent for this", or Serbian "šta da automatizujemo", "koje zadatke automatizovati", "da li vredi graditi agenta za ovo", "graditi ili obučiti", "šta ne treba automatizovati", "trijaža zadataka". Do NOT use for market sizing or idea validation (market-research-navigator), to write the training programme (team-enablement-program), to build the agent (safe-agent-builder), or to screen a pipeline input (pipeline-input-validator).
compatibility: No MCP dependency -- pure scoring logic from ten stated fields per task. Python 3 (stdlib only) runs scripts/screen_task.py, scripts/score_task.py and scripts/check_triage.py; scripts/selftest.py exercises all three plus mutation coverage.
---

# Automation Triage

## What this produces

| File | Who reads it |
|---|---|
| `<client>-automation-triage.md` | The client. Ranked table, then a block per task. |
| `<client>-not-worth-automating.md` | The client. Only the refusals, with the reason. |
| `<client>-triage-handoff.md` | You. Names and verdicts for the next skill. No hours. |
| `triage/*.json` | Nobody, until someone disputes a verdict. Then everybody. |

The gap this fills is the one between knowing what a company does and deciding what to build for them. Research tells you the first. Nothing in the chain decided the second, so it got decided in a proposal, from a feeling, by the person being paid for the answer.

## Two rules that govern everything below

**One. The verdict is computed, never chosen.** You supply stated fields and your own build economics; `scripts/score_task.py` applies the rules and records which one fired. You are paid more for BUILD than for TRAIN, and you supply every input — that is precisely why the arithmetic must not be yours.

**Two. Nothing you were not told may appear.** `team-enablement-program/references/engagement.md` §3: *"Never invent a fact about the client. Not their process, not their volumes, not their systems, not what their people find annoying."* Volumes come from the team. Friction comes from the person doing the task. If a field is missing it is `NOT MEASURED` and the task goes to `WATCH` — it does not get a plausible number.

---

## Step 0 — Where you must be standing

**After the discovery call, never before.** `prospect-discovery` produces *candidates* from public information and marks them `TO CONFIRM ON CALL`, because a website cannot tell you what a team does repeatedly. Scoring a candidate means scoring your own hypothesis.

If you have not had the call, you do not have tasks. You have questions.

## Step 1 — Set the economics once

Three numbers, and the first two are yours, not the client's:

- `--build-cost` — what you charge to build and hand over one agent
- `--hour-value` — what an hour of that team's time costs the client
- `--payback-months` — how long a payback you and they accept (default 6)

The threshold in hours is derived from these, never written in the code. A client whose hour costs 15 and one whose hour costs 60 do not have the same threshold, and a skill that pretends they do is wrong for both.

`--saved-fraction` (default 0.5) is the share of the task the agent actually removes. **It is an assumption, and it stays labelled as one everywhere it appears.** It becomes a measurement only after a Week 12 comparison, and then it should be replaced with that client's real figure.

## Step 2 — Pass one, the sieve

Four fields per task, a minute each, for **every** task the team named:

```
python3 scripts/screen_task.py --task-id T-01 \
  --task "ocenjivanje inbound lead-ova" --who sales --how-many 2 \
  --frequency-band weekly --who-notices "niko dok se klijent ne požali" \
  --out-dir triage
```

`--who-notices` is the cheapest signal in the whole skill. "Nobody, until the client complains a month later" tells you more about verifiability and error cost than three separate questions would.

**The sieve may only DROP or ADVANCE.** It may never reach a verdict. A client told "do not automate this" deserves the ten fields behind it, not four.

What is dropped is still written down. A task that vanishes with no record comes back at the next meeting and nobody remembers why it went.

## Step 3 — Pass two, the scoring

Ten fields, only for what advanced. Two of them decide almost everything.

**`--verifiability` is not a number on its own.** At 2 or 3 it requires `--check-rule`, written in the same small language `agent-delivery-pack` uses:

```
--verifiability 3 --check-rule "json_has_key:score"
--verifiability 3 --check-rule "json_key_in:fit=low,medium,high"
--verifiability 2 --check-rule "contains:<invoice number from the source>"
```

`safe-agent-builder`'s first non-negotiable rule is *"if a rule matters, it must be checkable in code."* That is the same test. If you cannot write the rule at the table, the score is not a 3 — and the dimension stops being your judgement and becomes something a client can argue with.

That one rule then travels: into the validator `safe-agent-builder` generates, and into `--rule` in `record_evidence.py` when `agent-delivery-pack` writes the acceptance test. Written once on the call, it ends up in a document the client can run themselves.

**`--friction` comes from the person who does the task.** Not the sponsor, not you. `team-enablement-program/references/baseline.md`: *"Predicts adoption better than hours do… A 6-hour task rated 1 for annoyance often stays manual all year, while a 40-minute task rated 5 gets automated in Week 5 and stays used."*

```
python3 scripts/score_task.py --task-id T-01 \
  --task "ocenjivanje inbound lead-ova" --who sales --how-many 2 \
  --per-month 240 --minutes-each 6 \
  --output structured --when-wrong "pogrešan prioritet, primeti se za nedelju" \
  --verifiability 3 --check-rule "json_has_key:score" --data-access 3 \
  --error-cost low --stability stable --friction 4 \
  --build-cost 4000 --hour-value 25 --out-dir triage
```

See `references/dimensions.md` for how to score verifiability and data access without flattering yourself.

## Step 4 — Read what came back

Four verdicts, and a second axis that only applies to one of them.

| Verdict | Means |
|---|---|
| `BUILD` | Worth an agent. Goes to `safe-agent-builder`, then `agent-delivery-pack`. |
| `TRAIN` | Worth a person with a good prompt. Goes to `team-enablement-program`. |
| `WATCH` | Not decidable today. Also goes to the programme, where Week 0 measures it. |
| `REFUSE` | Do not put AI on this. Goes in the client document, and that is the point. |

Supervision is separate and applies only to `BUILD`: high error cost means a person signs off every output, medium means a sample, low means unattended is acceptable. A `BUILD` with high error cost is still a build — it is just not an unattended one.

**Expect the arithmetic to say "do not build" more often than you like.** At a 4000 build and a 25 hour, the payback window needs roughly 50 hours a month on a single task. That is not a bug in the calculation. It is the reason your business is shaped as training rather than as one build per task, stated in numbers instead of in conviction.

## Step 5 — The fragile verdicts

Any verdict that a 2× error in the client's estimate would overturn is downgraded to `WATCH` and marked `fragile`.

This exists because `team-enablement-program/references/baseline.md` says plainly: *"sponsors are routinely wrong about where their team's hours actually go."* A `BUILD` that rests on one optimistic number from a sponsor is a guess wearing a verdict.

A fragile task is not a failure. It is a task whose decision belongs after Week 0, when the estimate has become a measurement.

## Step 6 — Write the three documents

**The refusal list first.** Before the ranked table, before anything. `references/refusal.md` is short and worth reading, but the rule fits in a line: **write what the task is, never what the client should do.** "This task has no output a machine can check" is an observation from a field they gave you. "We do not recommend automating this" is a recommendation they can quote back.

Roles, never names. A table saying *Marko, 30 hours a month, BUILD* is a document that can end up in a conversation about Marko's job, with nobody intending it. `baseline.md` already warns that a measurement which smells like a productivity audit produces useless numbers; this inherits that risk and adds a personal one.

Follow `references/pack-contents.md` for what goes in each file.

## Step 7 — The gate

```
python3 scripts/check_triage.py <client>-*.md --records triage --names Marko Ana --strict
```

Clean, or the pack is not finished. Pass `--names` every name you heard on the call; the checker cannot guess which capitalised word is a person, and a wrong guess would be worse than none.

The categories, in the order it reports them:

| | |
|---|---|
| `FORBIDDEN` | a guarantee, a compliance or legal conclusion, a named regulation you cannot cite, research with no study named, a promised outcome |
| `VERDICT_MISMATCH` | the document says BUILD where the record says REFUSE |
| `NAMED_PERSON` | a name from `--names` in a client-facing file |
| `BURIED_REFUSAL` | a task scored REFUSE that no document mentions |
| `ESTIMATE_AS_FACT` | "saves", "reduces", "measured" over a number that is an estimate |
| `FRAGILE_UNMARKED` | a fragile verdict presented as firm |
| `ADVICE_NOT_OBSERVATION` | "we recommend" in the refusal document |
| `DANGLING` · `UNSOURCED_NUMBER` · `RULE_UNSTATED` · `UNCLOSED_FENCE` · `DUPLICATE` | |

**Never edit the checker to make a pack pass.** Add the case to `scripts/selftest.py`, watch it fail, then fix the checker and confirm the mutation layer still catches a deliberately weakened version. `python3 scripts/selftest.py` must end at zero before anything ships.

## Step 8 — Hand off

`references/handoff.md` has the detail. Three things carry across and one does not:

- **Task names, byte for byte.** They become literal match keys in the baseline workbook; rename one after Week 0 and every hour logged against it lands in the `UNMATCHED` row. A name containing `*` or `?` is refused at scoring time, because those become wildcards there and quietly absorb other rows.
- **Verdicts**, so the programme knows which tasks it is training on.
- **`check_rule`** for every `BUILD`, straight into `safe-agent-builder`.
- **Never the hours.** `team-enablement-program` writes `TO BE MEASURED IN WEEK 0` on purpose. Letting a triage estimate in as a baseline breaks the one thing that skill exists to protect.

One count to respect: the programme takes **three to seven** tasks. If `TRAIN + WATCH` is under three, the gate says so — go back for more tasks rather than discovering it downstream.

---

## What this skill cannot do, stated plainly

- It runs on estimates. Every number in it is what somebody said, not what anybody measured, and the documents say so on every line where a number appears.
- `--saved-fraction` is an assumption with a default of 0.5. Nothing in the skill measures it. After a first Week 12 comparison, replace it with that client's real figure and re-run.
- It cannot tell whether a task *should* exist. A task that is pure waste scores the same as one that matters; automating it faster is the second-best answer to a question nobody asked.
- It says nothing about law, data protection or employment. A verdict is a statement about a task, not about what the client is permitted to do with their people.
- The refusal list is the most valuable thing it produces and the most exposed. It is written as observation for that reason.

## Reference files

- `references/intake.md` — running the two passes, and spotting a wish stated as a fact
- `references/dimensions.md` — scoring verifiability and data access honestly, with examples
- `references/payback.md` — the parameters, and why the sum often says do not build
- `references/refusal.md` — writing a refusal a client experiences as service
- `references/pack-contents.md` — what goes in each of the three documents
- `references/handoff.md` — what crosses the boundary to the next skill, and what must not
