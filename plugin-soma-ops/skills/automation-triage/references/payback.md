# The parameters, and why the sum often says do not build

## What the script computes

```
volume_hours     = per_month × minutes_each × how_many / 60
saved_per_month  = volume_hours × saved_fraction
value_per_month  = saved_per_month × hour_value
cost_over_window = build_cost + maintain_year × payback_months / 12
payback_actual   = cost_over_window / value_per_month
```

A BUILD requires `payback_actual ≤ payback_months`, on top of verifiability ≥ 2 and data access ≥ 2.

## The parameters

| | What it is | Default |
|---|---|---|
| `--build-cost` | what you charge to build and hand over one agent | asked |
| `--maintain-year` | annual maintenance | 20% of build cost |
| `--hour-value` | what an hour of that team's time costs the client | asked |
| `--payback-months` | acceptable payback | 6 |
| `--saved-fraction` | the share of the task the agent actually removes | 0.5 |
| `--train-floor-hours` | below this even a written skill does not repay | 2 |

`hour_value` is the client's cost, not their billing rate and not your rate. Loaded salary divided by working hours is close enough; ask the sponsor rather than guessing, because guessing it is inventing a fact about the client.

## Why the answer is usually no

At `build_cost` 4000 and `hour_value` 25, with the default saved fraction and a six-month window, a single task needs roughly **50 hours a month** before a build repays itself. Most tasks a team complains about are three to ten.

This is not the calculation being harsh. It is the reason the enablement business exists: twelve people each writing four skills covers ground no sequence of individual builds could pay for.

Two honest ways the answer turns to yes:

- **The task is genuinely large** — several people, every day, and the hours are real rather than hoped for. The sensitivity check is what tells you which.
- **The window is longer.** A client who thinks in years rather than quarters may accept twelve or eighteen months, and that is their call to make with the number in front of them, not yours to assume.

## saved_fraction is the weakest number here

0.5 is a deliberately conservative guess. It is not measured, and the record and every document say so.

It becomes real exactly once: after a Week 12 comparison, where the workbook shows what the hours on that task actually did. Replace the default with that client's figure and re-run the triage. That is the loop closing, and it is the only path by which a BUILD verdict stops resting on an assumption.

## What the calculation cannot see

Strategic value, a client relationship, a task that blocks something larger, a build you would do at a loss because it opens a door. All real, none of them in the arithmetic.

Override deliberately and in writing. A verdict overridden with a stated reason is a decision; a verdict quietly ignored is the start of the argument in month six.
