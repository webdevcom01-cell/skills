# The intake block — handing off to team-enablement-program

## What this is

`team-enablement-program` refuses to write anything until it has five required inputs, and refuses to invent them. This block is that intake, pre-filled from research where research supports it and marked as a gap everywhere else.

The two skills chain: this one prepares the call, the call fills the gaps, the engagement skill runs on the completed block.

## Format

Reproduce exactly this, so it can be pasted straight into the next skill.

**Field names stay in English even when the rest of the pack is not**, because the receiving skill matches on them mechanically. Field *content* follows the pack's language. A translated `Repeated tasks` heading reads perfectly well to a human and arrives at `team-enablement-program` as an empty required field — which is how one real run silently emptied all five.

```markdown
## Intake — <Company legal name>
Researched <date>. Fields marked TO CONFIRM ON CALL are not guesses; they are gaps.
Field names are English on purpose — the receiving skill matches on them. Content follows the pack's language.

**Client and team**
- Company: <legal name, trading name if different> [source]
- Team the programme is for: TO CONFIRM ON CALL
- Number of participants: TO CONFIRM ON CALL
- Current AI comfort level: TO CONFIRM ON CALL

**Tool stack**
- Tools in daily use: TO CONFIRM ON CALL
- System of record for email / documents: TO CONFIRM ON CALL
- AI assistant and plan: TO CONFIRM ON CALL

**Repeated tasks** — must be in the team's own words
- TO CONFIRM ON CALL
- Candidates suggested by their published services, to test rather than assume:
  - UNCONFIRMED: <question you would actually ask on the call>? <the published thing that suggests it> [source]
  - UNCONFIRMED: <question>? <what suggests it> [source]

**Sponsor**
- Named officers: <name, role> [source]
- Confirmed sponsor: TO CONFIRM ON CALL

**Context established by research** — usable in the programme without confirmation
- Sector and business model: <...> [source]
- Markets and geography: <...> [source]
- Commercial instruments, certifications, documentation types: <...> [source]
- Facilities and operations: <...> [source]

**Constraints and open questions**
- Data sensitivity: TO CONFIRM ON CALL
- Regulatory or contractual constraints: TO CONFIRM ON CALL
- Entity structure question, if any: <...> [sources]
- Language for deliverables: <inferred from site language, confirm>
```

## The line that matters

**Research fills the context block. It never fills the required fields.**

Every field marked `TO CONFIRM ON CALL` is one a website cannot answer — team size, tools, tasks in their own words, the sponsor. Filling one from inference produces exactly the failure both skills exist to prevent, made worse by having been written into a document, where it stops looking like a guess.

The context block is different, and it is where the value of research shows up. Sector, markets, payment instruments, documentation types, facilities — all cited, all usable immediately, and all things that turn a generic programme into one about their business.

## Candidate tasks

Publishing a service list tells you a lot about what a team does repeatedly. A trading company listing "FX sourcing and documentation" plausibly has somebody doing FX paperwork often — plausibly, not certainly, and the difference is the whole point of this section.

Offer those as **candidates to test**, never as findings. Two rules:

- Each candidate carries the source it came from
- Each is phrased as a question for the call, not a statement in the plan

Getting this right is the difference between arriving with an informed hypothesis and arriving with a document that tells the client what their job is.

## Candidates must not reach the next skill as if they were confirmed

`team-enablement-program` feeds the repeated-task list straight into the baseline workbook, where the names become **literal match keys**. Rename a task later and every hour logged against it lands in the workbook's UNMATCHED row.

So a candidate that has not been confirmed on the call must not be passed to that skill as a task. The chain test made this concrete: candidates passed through prefixed `UNCONFIRMED:` produced a workbook whose row labels all had to be renamed after Week 0, turning a marker into a maintenance trap.

The rule is simple: **the repeated-task field stays `TO CONFIRM ON CALL` until the team has said the words themselves.** Candidates live in their own list, clearly separated, for use as call questions only. Running the engagement skill without confirmed tasks is legitimate — it will say the tasks are unconfirmed — but the workbook is generated after the call, not before.

## Fields this block does not carry

`team-enablement-program` also asks for two things with no slot here, both from its "ask for, but proceed with a gap marker" list:

- Existing automations or AI tools already in place, and whether anything is being replaced
- Session cadence and format

The call agenda already asks the first (*"what was bought and never adopted, what has been tried before and failed"*), so the answer exists and has nowhere to land. Add both as `TO CONFIRM ON CALL` lines at the end of the block rather than discovering the gap in the middle of the next skill.

One count to respect: the receiving skill requires **three to seven** repeated tasks. A block that carries two candidates satisfies nothing.
