# Scoring verifiability and data access without flattering yourself

These are the only two fields the consultant supplies. Everything else comes from the team. That makes these the two a client can reasonably challenge, so score them as if they will.

## Verifiability

The question is not "is the output good?" It is **"can something other than a human opinion tell that it is wrong?"**

| | Meaning | What makes the score valid |
|---|---|---|
| 3 | Structured output with a checkable rule — a required key, a value from a known set, arithmetic that must reconcile | a written rule |
| 2 | The output can be compared against a source — extraction, transcription, classification where the source exists | a written rule |
| 1 | A person judges it against a rubric | the rubric, in one sentence |
| 0 | Nobody knows it is wrong until it is too late | nothing |

**A 2 or a 3 does not exist without the rule.** `score_task.py` refuses it. The rule language is the one `record_evidence.py` accepts:

| Rule | Fits when |
|---|---|
| `json_has_key:score` | the key's presence is the contract; fails if the output does not parse at all |
| `json_key_in:fit=low,medium,high` | a field must hold one of a known set; catches an invented category |
| `contains:BLOCKED` | a refusal is signalled by a literal token the flow emits |
| `not_contains:BLOCKED` | asserting the gate did not fire; weak alone, pair it with a `json_has_key` |
| `regex:` | last resort; a clever regex is one nobody re-checks |

If you find yourself writing "the output looks right" — that is a 1, and 1 means TRAIN, and TRAIN is a perfectly good outcome that closes faster than a build.

### The trap

The temptation is to score a 3 because the output *could* be structured if someone built it that way. That is a statement about a system that does not exist. Score what the task produces today.

## Data access

| | Meaning |
|---|---|
| 3 | Every input already sits in a system with an API or an MCP |
| 2 | Inputs exist as files or email a person hands over |
| 1 | Inputs are tacit — in somebody's head, or in a conversation |
| 0 | Inputs do not exist |

A 1 is where most enthusiasm dies. "The team just knows which customers are strategic" is a 1, and it is the reason a plausible-looking build stalls three weeks in.

Score 0 honestly. It is a REFUSE, and a REFUSE delivered in week one is a service; delivered in week nine it is an invoice nobody wants to pay.

## Error cost

Not a score. A gate.

- `low` — somebody notices and redoes it
- `medium` — rework, embarrassment, a delayed deal
- `high` — money moves, a legal commitment, or a customer-facing mistake that cannot be recalled

`high` with verifiability 0 is a REFUSE regardless of volume. `high` with a checkable rule is a build that a person signs off, every time.

## Friction

One to five, and **only from the person who does the task.** Not the sponsor, who is usually wrong about it, and not you, who are forbidden from inventing it.

It changes nothing about the threshold and everything about what actually gets used.
