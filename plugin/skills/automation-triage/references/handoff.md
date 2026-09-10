# What crosses the boundary, and what must not

## To `team-enablement-program`

**Carries:** task names, byte for byte. Verdicts.

**Never carries:** hours, minutes, volumes, or anything derived from them.

`team-enablement-program/SKILL.md`: *"if the client has not measured how long a task takes today, the program says `TO BE MEASURED IN WEEK 0`, never a plausible-sounding estimate. Invented baselines are the single fastest way to destroy a consultant's credibility at the Week 12 review, because the client will check."*

Triage runs on estimates by design. If those estimates cross this line they become a baseline, and the Week 12 comparison is measuring the estimate rather than the work. The whole commercial argument rests on that one comparison.

### The name is a key, not a label

Task names become **literal match keys** in the baseline workbook, matched including capitalisation. Rename one after Week 0 and every hour logged against it moves to the `UNMATCHED` row.

So: no translation, no tidying, no shortening, no consultant-voice rewrite. `T-01` is an internal key for the record, and it is not the name.

`score_task.py` refuses a name containing `*` or `?` for the same reason — those are wildcards in the workbook's matching, and `unos *svih* podataka` would silently absorb every other row starting with `unos` and inflate the baseline.

### The counts

Three to seven tasks, five per person at the measurement. Fewer than three and the programme has nothing to run on; more than seven and the Week 0 session produces worse data.

## To `safe-agent-builder`

**Carries:** the task, the output shape, the `when_wrong` answer, and the `check_rule`.

That is exactly what it asks for. Its four non-negotiable rules require a validator that decides in code, an input guard that rejects an empty or missing core input, and a block that fails closed — and the four triage fields above supply each of them without a second round of questions.

`check_rule` then continues past the build. `agent-delivery-pack` takes it as `--rule` in `record_evidence.py`, where it decides PASS or FAIL on the acceptance test the client can re-run.

One rule, written at a table during a discovery call, ends up in a document the client runs themselves. That is the whole chain working.

## Back from `team-enablement-program`

The return path matters as much as the outward one.

`WATCH` tasks go into the programme with no verdict. Week 0 measures them. After that:

1. Re-run `score_task.py` with the measured `per_month` and `minutes_each`
2. Replace `--saved-fraction` with the client's real figure from the Week 12 comparison, if there has been one
3. The verdict is no longer fragile, because it no longer rests on an estimate

This is the only route by which a `BUILD` becomes safe rather than merely computed. Until a task has been through it, the sensitivity check is all that stands between a verdict and a sponsor's optimism.
