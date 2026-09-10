# Maintenance, ownership and the claims that must never appear

## Before you write a word of this

This file describes a commercial document. It is not legal advice and neither are you. The structure below is a working shape a consultant can hand to a lawyer; it is not a contract, it does not say what any law requires, and nothing in it has been reviewed by anyone qualified to review it.

Put that in the document too, at the top, where it is read rather than at the bottom where it is not:

> This document sets out what we intend to do and what it costs. It is not legal advice, and it makes no statement about what any law or regulation requires. Have your own adviser review it before signing.

While fees are unagreed, the file is marked `DRAFT — NOT FOR SIGNATURE` and the amounts stay `[TO AGREE]`. `check_pack.py` fails a placeholder in a file that is not marked draft, which is deliberate: the expensive version of this mistake is a `[TO AGREE]` reaching a client's inbox looking like a finished number.

## What must never appear, in any wording

The checker refuses these outright, and softening them is not the fix — deleting them is.

| Never write | Why it is refused | Write instead |
|---|---|---|
| "compliant with GDPR" / "usklađeno sa zakonom" | A legal conclusion you are not qualified to reach | "Data protection has not been assessed. Your adviser should review this before go-live." |
| "secure" / "bug-free" | Unfalsifiable, and read as a warranty | "No security review has been carried out." |
| "guarantees" / "garantuje" | A warranty, whatever the surrounding sentence says | "We intend to respond within one working day." |
| "100% accurate" / "never fails" | No test supports a claim about all inputs | "Seven cases ran on the date shown `[EV:...]`. Inputs outside them were not tested." |
| "fully automated" | Invites the client to stop supervising | "A person reviews the output before it is used." |
| "saves N hours a week" | The runs measure round-trip time, not anyone's week | Either measure it properly and cite the measurement, or say nothing. |
| "production-ready" | Means whatever the reader wants it to mean | Describe what was tested and let them decide. |

The pattern behind the table: **say what was done and when; never what will happen or what is permitted.**

Note the shape of every replacement in the right-hand column: it describes work that was or was not done. "No security review has been carried out" passes the checker; "the agent is secure" does not. One is a fact about your week, the other is a warranty. The same holds in Serbian: `bezbednosni pregled nije rađen` is a description, `sistem je bezbedan` is refused.

What the checker refuses is the *predicative* use — the agent **is** secure, **is** production-ready. "Secure the client's sign-off before the workshop" and "keep the key in a secure password manager" are ordinary sentences about your own work and pass untouched. And an explicit refusal to claim — "we do not claim the agent is secure", "nothing here should be read as production-ready" — passes too, because a gate that deletes that sentence teaches the author to say nothing at all.

## The shape of the terms

### What is included

Enumerate, and keep it short enough to remember:

- Keeping the agent running as delivered
- Re-running the acceptance suite after any change we make
- A stated number of small changes per period, with "small" defined by example rather than by adjective

### What is chargeable

- New behaviour, new inputs, new outputs
- Changes to the knowledge base beyond agreed refreshes
- Work caused by a change someone else made to the agent
- Work caused by a third-party change — a model retired, an API altered, pricing moved

That fourth line matters more than it looks. A model being retired is nobody's fault and still costs a day.

### Response expectations

State them as intentions, never as commitments, and never with a percentage:

> We aim to acknowledge within one working day and to say what we have found within three. These are intentions, not guarantees, and no availability level is promised.

### Who may change the agent

The most valuable clause in the document, and the one clients push back on least once it is explained:

> The agent's prompt, its flow and its knowledge base determine what it does. Changing any of them changes its behaviour and makes the acceptance result in `<agent>-acceptance-test.md` no longer describe the agent you are running. If your team changes them, re-run the acceptance suite; we cannot stand behind a result for a version we did not test.

This is not a restriction on the client. It is the sentence that stops a dispute in month six about an agent that stopped matching its own documentation, and it is *why* the acceptance test being re-runnable by the client matters commercially.

### Ending it

Notice period, what happens to the agent, what happens to the material each side holds. Plain and short. A client reading a hard exit clause reads a supplier who expects to be worth keeping.

## The one thing worth saying out loud to the client

They can run the acceptance test themselves, today, and get the same answer. Nothing else in the pack changes the relationship as much — it converts every future disagreement about whether the agent works from an argument into a procedure.
