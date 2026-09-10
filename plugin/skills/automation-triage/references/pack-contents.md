# What goes in each of the three documents

Write these after scoring, never before. Every number carries a `[T-0n]` tag or a `NOT MEASURED` marker.

---

## 1. `<client>-not-worth-automating.md`

**Written first.** See `references/refusal.md` for the wording rule — observation, never advice.

One block per refused task: the task in their words, the field that decided it, the tag, and where it exists, what would change the answer.

A short closing line stating what the document is not: not a legal or data-protection assessment, not a statement about what anyone is permitted to do.

---

## 2. `<client>-automation-triage.md`

**The ranked table.** One row per scored task: the task, the verdict, the rule number, and the tag. Sort by verdict, then by friction descending inside each group — because the order people will act in is the order of annoyance, not the order of hours.

**A block per task**, in that order:

> ### T-01 — ocenjivanje inbound lead-ova
> **Verdict:** BUILD (rule 7) `[T-01]`
> **Why:** the output is structured and a rule can check it — `json_has_key:score`. Every input is already in the CRM.
> **Supervision:** a person signs off a sample.
> **What we were told:** roughly 240 a month, about 6 minutes each, two people. These are the team's estimates and have not been measured.
> **Worth noticing:** two people do this, so adoption is the risk rather than the technology.

The `What we were told` line is not padding. It is the sentence that stops the Week 12 conversation from being about whose number was wrong.

**A fragile verdict says so in its own block**, next to the verdict, not in a footnote. `check_triage.py` reports `FRAGILE_UNMARKED` otherwise.

**What this ranking does and does not mean.** Two sentences, unsoftened:

> These verdicts were computed from what the team told us on <date> and from the build economics on the cover. They are not measurements, and the tasks marked WATCH are marked so precisely because a measurement would change them.

---

## 3. `<client>-triage-handoff.md`

Yours, not the client's. Three columns and nothing else: task name byte for byte, verdict, and `check_rule` where there is one.

**No hours.** `team-enablement-program` writes `TO BE MEASURED IN WEEK 0` deliberately; a triage estimate arriving as a baseline is the failure that skill exists to prevent.

Group by destination so the next step is obvious:

```
→ safe-agent-builder      BUILD tasks, with their check rules
→ team-enablement-program TRAIN and WATCH tasks, names only
→ nowhere                 REFUSE tasks, already in the client document
```

If TRAIN + WATCH is fewer than three, say so at the top of this file. The next skill will not run well on two.
