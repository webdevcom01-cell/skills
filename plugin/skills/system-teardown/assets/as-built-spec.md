# As-built technical specification — template

## How to use this template — do not copy this block into the deliverable

Structure derived from arc42. Sections 1–12 keep arc42's canonical numbering so anyone using
arc42 tooling or review checklists keeps the mapping; reverse-engineering additions are
lettered (`3a`, `4a`, `8a`…) rather than renumbering the canon.

**Copy only the headings and tables below the line.** Every line of italic guidance is an
instruction to you, not content for the reader. A spec that lectures its reader is a spec they
stop reading.

Drop sections that do not apply rather than padding them. Three are never dropped: **§0
Provenance**, **§0.1 Falsification ledger**, and **§16a What we could not determine**.

Every claim carries one provenance tag — `[OBSERVED]` / `[TOOL]` / `[INFERRED]` — and one
verdict — CONFIRMED / REFUTED / MISLEADING / UNCONFIRMED. Tag at the level of a table row or a
discrete finding, not every clause of prose. There is no separate confidence scale; the verdict
*is* the confidence.

This template is for Full depth only. Working depth has its own template,
`assets/orientation-memo.md` — a different register (explanation, not reference) and a
different length (1-2 pages), not a subset of this one. If you are tempted to fill a
shortened version of this file instead, that is the signal to go use the other template.

---

# As-built: [system name]

## 0. Provenance and method

- **Pin** — commit SHA / URL + capture timestamp / SHA-256 / endpoint + date
- **Depth** — quick / working / full
- **Environments observed** — which, under what account or tier
- **Tools used** — name, version, exact command or query
- **Analysis window** — dates
- **What was NOT examined** — and why
- **Authorization basis** — whose system, what access path, what permission
- **Capability gaps** — what STEP -1 said you could not do, and what that costs the reader

## 0.1 Falsification ledger

```
FALSIFICATION LEDGER
Target: <codebase|web|ai|binary>   Depth: <working|full>
Method: <Reflexion diff | evidence-column attack | ablation + differential | independent parser>

Inferred claims (one row each — this list IS N):
  C1  <claim>  → CONFIRMED    evidence: <the row/case that settled it>
  C2  <claim>  → UNCONFIRMED  evidence: <attempted, why unsettled>
  C3  <claim>  → DROPPED      evidence: <disconfirming result>
  ...
  N = <row count>   confirmed a / downgraded b / dropped c   (a+b+c=N)

Coverage denominator (countable, not chosen): <edges in the diff | INFERRED rows | messages captured>
System scale examined: <e.g. 12 of ~340 files · 3 of 18 endpoints>

Unresolved, filed to §16a: k
Falsification NOT performed, and why: <or "none">
```

*Every CONFIRMED claim in this document appears by ID above, and every ID above appears in the
document. N is the length of the list, not an asserted integer — a reviewer counts the rows and
checks each evidence pointer resolves to a real row elsewhere. That is what makes it hard to
fake.*

## 1. Purpose and business context

What the system does. Who depends on it. Business criticality. Upstream and downstream owners.
The decision this document is meant to inform.

## 2. Constraints

Regulatory, licensing, platform and runtime pinning, end-of-life dependencies.

## 3. Context and scope

C4 Level 1 System Context, plus the external interface inventory:

| Direction | Interface | Protocol | Auth | Data classification | Owner | Criticality | Provenance | Verdict |
|---|---|---|---|---|---|---|---|---|

## 4. Solution strategy

The design approach **as evidenced**, not as claimed by surviving documentation. Technology
stack inventory with versions and support status.

### 4a. Documentation divergence

*Where the code contradicts the README, the wiki, or an existing ADR, record it here with the
MISLEADING verdict — say what the documentation gets right first, then what it gets wrong.
This section is usually the highest-value page in the whole document for the team that
inherited the system.*

## 5. Building block view

C4 L2 Container and L3 Component. Module dependency graph. Cycles. Layering violations.

**Reflexion diff** — the falsification evidence for this section:

| Relation | Predicted | Present in code | Verdict | Explanation |
|---|---|---|---|---|
| A → B | yes | yes | convergence | — |
| C → D | no | yes | divergence | [why] |
| E → F | yes | no | absence | [why] |

*Every divergence and absence is explained, accepted, or filed with an owner. If dynamic
observation was not possible, label this table **static-only** here, not only in §0.*

## 6. Runtime view

Sequence diagrams for the top business scenarios, chosen by business value and risk. Startup and
shutdown. Error and retry paths. State machines.

*Mark each scenario **traced** or **read**. A traced scenario is evidence; a read one is a
hypothesis, and belongs in the ledger's inferred count.*

## 7. Deployment view

Environments, topology, infrastructure-as-code references, scaling and HA, network boundaries.

## 8. Crosscutting concepts

Authentication and authorization, session model, error handling, logging and observability,
transactions and consistency, caching, i18n, concurrency model, configuration and secrets
management, feature flags.

### 8a. Data architecture

ERD from the **live schema**, not from ORM model classes. Ownership per table. Retention.
Migration state. Data flows and lineage. PII inventory.

*Include shared-state coupling here: tables written by more than one component, queue topics,
shared cache namespaces, shared filesystem paths. These are real dependency edges that no
import graph will show you.*

## 9. Architectural decisions

Retroactive ADRs, Nygard template extended for reverse engineering:

**Title** · **Status:** `Accepted (retroactive — reconstructed)` · **Context** · **Decision** ·
**Consequences** · **Evidence:** `file:line@SHA` or equivalent · **Verdict**

*The Evidence field is what separates a reconstructed decision from a guess.*

## 10. Quality requirements

Measured, not aspirational. Observed latency and throughput. Known limits. Failure modes.
Security posture. State the measurement method for each number; an unmeasured number is
`[INFERRED]` and UNCONFIRMED.

### 10a. Interfaces and contracts

Public API surface — OpenAPI, gRPC, or GraphQL schema, extracted or reconstructed. Event
schemas. File formats. Backward-compatibility guarantees. State whether each contract was found
or inferred.

## 11. Risks and technical debt

Ranked, with blast radius and estimated remediation cost.

### 11a. Build, release, operate

How to build from a clean checkout. Test strategy and **actual measured** coverage. CI/CD
pipeline. Deployment procedure. Rollback. Runbooks. On-call surface.

### 11b. Dead and suspicious code register

| Candidate | Static evidence | Coverage evidence | Verdict | Scream-tested? |
|---|---|---|---|---|

*Both static and dynamic evidence are required before a candidate is listed. Without coverage
data, nothing goes in this table — say the register could not be produced.*

## 12. Glossary

The ubiquitous language, with the source of each term.

## 16a. What we could not determine

**Required. Never omitted. Never empty.**

| Unknown | Why unresolved | What would resolve it |
|---|---|---|

*A specification without this section presents the boundary of the investigation as the boundary
of the system, and the reader has no way to see the difference. That is the single most damaging
thing a teardown can do.*

## 18a. Appendices

Commands to regenerate every artifact. Raw tool outputs. Fact-database schema. Capture files.
