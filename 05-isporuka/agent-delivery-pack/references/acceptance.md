# Choosing acceptance cases

## What makes a test the client accepts as fair

A client who suspects the test was chosen to pass will not trust the result, and they are right not to. Three properties make a suite fair, and all three are visible to a non-technical reader:

1. **It contains cases the agent is supposed to refuse.** If every case succeeds, the suite has demonstrated fluency and nothing else. Refusals are what prove there is a floor under the agent.
2. **The rules were written before the runs.** A rule fitted to an output already seen is a description wearing the costume of a test. Write the rule in Step 2, run in Step 3, in that order, and do not revise a rule after seeing its output — record the failure instead.
3. **The inputs look like the client's real work.** A case built from the client's own domain is checkable by them; a case built from `foo` and `bar` is not.

## Where to get the cases

In order of preference:

- **An existing eval suite.** `as_list_eval_cases` returns each case's input and its assertion. If the agent already has a golden set, it was written by whoever built the agent, at a time when they knew what mattered. Start there.
- **The agent's own gate.** If the flow has a validator and a condition node, the validator encodes what the builder decided was unacceptable. Every rejection branch is a refusal case waiting to be written.
- **The client's stated worry.** What they asked about in the discovery call — "what if someone pastes in the wrong thing" — is the case they will actually run themselves.

## The five rules and when each fits

| Rule | Fits when |
|---|---|
| `json_has_key:score` | The agent returns structured output and the key's presence is the contract. Strongest available: it fails if the output is not parseable at all. |
| `json_key_in:fit=low,medium,high` | A field must hold one of a known set. Catches an agent that invents a new category. |
| `contains:BLOCKED` | The refusal is signalled by a token the flow emits. Check the exact token in the flow, not the token you expect. |
| `not_contains:BLOCKED` | A pass case, asserting the gate did not fire. Weak on its own — pair it with a `json_has_key` case. |
| `regex:` | Last resort. A regex that is clever is a regex nobody will re-check. |

`contains:` is case-sensitive and literal, on purpose. `regex:` is the only rule with wildcards.

## Writing the expected line

`--expected` is the sentence the client reads in the acceptance-test document. It is not the rule. Write it as an outcome a person could confirm by looking:

- Bad: `json_has_key:score returns true`
- Good: `A score, a fit band and a list of reasons come back as structured data.`
- Bad: `assertion holds`
- Good: `The agent refuses the input and says which field was missing, instead of guessing.`

## A worked shape

Seven cases for a scoring agent with a gate:

| Case | Intent | Rule | Why it is there |
|---|---|---|---|
| AT-01 | pass | `json_has_key:score` | The ordinary job, done on a realistic input |
| AT-02 | pass | `json_key_in:fit=low,medium,high` | The output stays inside the agreed vocabulary |
| AT-03 | pass | `json_has_key:reasons` | The client can see why, not only what |
| AT-04 | block | `contains:BLOCKED` | Empty or off-topic input is refused |
| AT-05 | block | `contains:BLOCKED` | Input that looks plausible but is missing the required field |
| AT-06 | pass | `json_has_key:score` | An edge of the client's real range — the largest or smallest case they handle |
| AT-07 | pass | `json_has_key:score` | A case near the gate that must *not* be refused, so the gate is not simply always on |

AT-07 is the one people leave out, and it is the one that catches a gate that has been tightened until nothing gets through.

Note what AT-07 does **not** use. `not_contains:BLOCKED` is the obvious rule for it and it is the wrong one — it passes on any output that is not a refusal, including a malformed one, so a gate that has broken into gibberish still scores a pass. This is not hypothetical: it is the mistake made on the first live pack built with this skill, caught only when the pack was read back critically afterwards. On a case whose whole job is to prove the agent still works, assert what the output must *contain*, never merely what it must lack.

## Two executions, one output

A gated agent emits the same refusal for every kind of bad input, so two refusal cases produce byte-identical replies and their execution records become indistinguishable by content. `record_evidence.py` says `ambiguous` and names both ids.

`--exec-id` picks which one is written into the record. It does not turn a guess about run order into evidence, so the record stays `ambiguous` and still names the other id. Resist the urge to read that as a defect in the tooling: it is the tooling declining to launder your reasonable assumption into a fact. If it matters, fetch `as_get_recent_executions` immediately after each run instead of once at the end, and the ambiguity disappears at source.

If the record says `unmatched`, nothing in the list corresponded to the reply at all — the id stored beside it may belong to a different case. That is a re-run, not a rewrite.

## When a case fails

Record it. `record_evidence.py` writes the `FAIL` and exits 1; it does not refuse to write.

Then choose one of three, and there is no fourth:

- **Fix the agent and re-run.** Re-run every case afterwards, not only the one that failed — a change to a prompt or a gate can move a case that used to pass.
- **Change the claim.** Sometimes the agent is right and the case was wrong. Say so in the internal note, rewrite the case, and keep both records.
- **Tell the client.** A pack that says "AT-05 fails today, here is the fallback" is a stronger document than one that quietly holds six cases. It is also the only version that survives the client finding out on their own.

Deleting the evidence file is not on the list. `check_pack.py` reports a recorded failure that no document mentions, which is the whole reason that check exists.
