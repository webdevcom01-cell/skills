# Writing a refusal a client experiences as service

## The one rule

**Write what the task is. Never what the client should do.**

| Do not write | Write |
|---|---|
| We do not recommend automating this. | This task has no output a machine can check `[T-04]`. |
| This is not suitable for AI. | The inputs live in a conversation, not in a system `[T-06]`. |
| You should keep doing this manually. | A wrong answer here moves money, and nothing here can catch a wrong answer before it does `[T-02]`. |

The left column is advice. Advice is quoted back when the client automates anyway and it goes wrong. The right column is a statement about a field they gave you, and it survives the same conversation intact.

`check_triage.py` reports `ADVICE_NOT_OBSERVATION` on the left column, in the refusal file only.

## Why this section sells

A consultant who arrives saying everything can be automated is selling. A consultant who arrives with three tasks and a reason each is not, and the client can feel the difference before they can articulate it.

The refusal list is also the cheapest insurance you will ever write. Month six arrives, something has not been automated, and the question is whether that was an oversight or a decision. A document with the reason in it makes it a decision.

## Write it first

Before the ranked table, before the build list. The order matters for the same reason it matters in a delivery note: the selling voice leaks into whatever is written second.

## What belongs in each entry

- The task, in the team's own words
- The field that decided it — no output a machine can check, inputs that do not exist, a rule requiring a person, an expensive mistake nobody can catch
- The tag, so it resolves to a record
- Where relevant, what would change the answer. "If the ICP moved into the CRM, the inputs would be reachable" is worth more than the refusal itself, because it is the next engagement.

## What does not belong

- A recommendation
- A number that is not tagged
- A person's name
- Any sentence about what the law requires
