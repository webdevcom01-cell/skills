# Target: codebase you did not write

Recovering the architecture of source code you can read. The tradition here is the
oldest and best-formalized of the four, so use its vocabulary — it is what a reviewing
architect expects.

## Vocabulary that matters

From Chikofsky & Cross (IEEE Software, 1990), still the standard taxonomy:

- **Reverse engineering** — *"the process of analyzing a subject system to identify the
  system's components and their interrelationships, and to create representations of the system
  in another form or at a higher level of abstraction."* Analysis only; it does not change the
  subject. The paper's stated purpose — gaining enough design-level understanding to maintain,
  enhance, or replace — is the motivation, not the definition.
- **Redocumentation** — recovering lost documentation at the *same* abstraction level.
  The horizontal move.
- **Design recovery** — reproducing everything needed to understand what a program does,
  how, and *why*. Raises abstraction level, and requires domain knowledge from outside
  the code. The vertical move, and the harder one.
- **Reengineering** — *"the examination and alteration of a subject system to reconstitute it
  in a new form and the subsequent implementation of the new form."* Loosely: reverse
  engineering followed by restructuring and/or forward engineering.

Being explicit about which of these the user actually wants prevents the most common
scoping failure: producing a redocumentation when they needed a design recovery.

## Phase sequence

Phases 0–3 are mechanical. Phases 4–8 require hypothesis discipline and are where the
value is.

**Phase 0 — Scope, legality, freeze**
Confirm authorization. Record the license of the code. Pin a commit SHA — every artifact
references it. Record reproducibility state: does it build, does it have tests, does CI
pass. Architecture docs without a SHA are unfalsifiable.

**Phase 1 — Census, no reading yet**
LOC by language, file count, largest files, churn × complexity hotspot map from
`git log`, contributor map.

Build the **exclusion manifest first**: `vendor/`, `node_modules/`, generated protobuf,
migrations, minified bundles, lockfiles. This single action has the highest leverage in
the entire phase sequence — without it every downstream graph is dominated by noise and
every metric is wrong.

**Phase 2 — Boundaries and I/O, outside-in**
Entry points: `main`, HTTP route registration, CLI parsers, cron and scheduler entries,
queue consumers, lambda handlers, WSGI/ASGI apps, Dockerfile CMD/ENTRYPOINT.
Egress: outbound HTTP clients, DB drivers, SDK clients, file paths, sockets.
Config surface: env vars, YAML/env/ini, feature flags, DI container registrations.
Build and deploy: Makefile, Dockerfile, k8s manifests, Terraform, CI workflows — these
are architecturally load-bearing, not incidental.

Output is a C4 Level 1 System Context diagram plus an external interface table.

**Phase 3 — Structural fact extraction**
Module dependency graph, call graph, import graph, type hierarchy, live DB schema.

Prefer **symbol-level** dependencies over include- or file-level — measured 12% more accurate
by a2a and 7% by MoJoFM (Lutellier et al., ICSE 2015), on a mostly C/C++ corpus. Store facts in something queryable (SQLite, CodeQL
database, Joern CPG) so hypotheses can be tested programmatically instead of eyeballed.

**Phase 4 — Dynamic observation**
Run the test suite with coverage. Trace the top business scenarios end to end. Capture
HTTP request → handler → query paths.

**Do not skip this** where there is reflection, dependency injection, an ORM, or plugin
loading — and say so explicitly when you cannot run it.

The measured warning: across 13 static analysis tools on **1,000 Android apps**, static call
graphs missed on average **61%** of dynamically-executed methods, at least 40% even in the best
case (ISSTA 2024, arXiv 2407.07804). Read the scope honestly — the number is driven by Android
framework callbacks and entry-point modelling, and the dynamic ground truth came from short
fuzzing runs at roughly 8% coverage. It is the strongest published warning about DI- and
reflection-heavy stacks, not a measured constant for every language. Cite it that way.

**When the system will not run** — no build, no test suite, no environment — do Phases 0–3 and
5 only, label the Reflexion diff *static-only*, ship every behavioral claim UNCONFIRMED, and
record "dynamic observation not performed" in the deliverable's unknowns section. Do not skip
it silently, and do not let a static-only diff be reported as a completed falsification.

Coverage is also the cheapest dead-code candidate list you will get.

**Phase 5 — Hypothesis and Reflexion iteration**
See the falsification section below. This is the core of the phase sequence.

**Phase 6 — Behavior recovery**
Sequence diagrams for the top 5–10 business scenarios, chosen by business value and risk
rather than by code size. State machines for stateful entities. ERD from the live schema,
not from ORM model classes — they drift. Data flow and lineage. Business rules extracted
with `file:line@SHA` citations; an uncited rule is hallucination surface.

**Phase 7 — Documentation**
As-built spec (`assets/as-built-spec.md`), retroactive ADRs marked as *reconstructed*
with status `Accepted (retroactive)` and an added Evidence section, C4 L1–L3, glossary
of the ubiquitous language, risk and tech-debt register, open questions.

**Phase 8 — Validation**
Walk the document with a system owner or operator if one exists. Then run falsification
tests: for each claimed dependency, can you deliberately break it and see the predicted
failure? For each dead-code candidate, delete it in a branch and run the suite plus a
smoke test — the scream test.

## Artifacts by phase

| Phase | Artifact | Notation |
|---|---|---|
| 1 | LOC census; churn × complexity hotspots | table; scatter |
| 2 | C4 L1 System Context | C4 / Structurizr DSL / Mermaid |
| 2 | External interface inventory | table: direction, protocol, auth, owner, criticality |
| 2 | Config and feature-flag surface | table: key, default, consumers, blast radius |
| 3 | Module dependency graph; cycle list | DOT / GraphML |
| 3 | Call graph per entry point | DOT |
| 3 | Type hierarchy | UML class diagram |
| 3 | ERD | from live schema introspection |
| 4 | Runtime traces; coverage report | flamegraph, lcov, OTel trace |
| 5 | Reflexion diff | box-arrow + convergence/divergence/absence table |
| 5 | C4 L2 Container, L3 Component | C4 |
| 6 | Sequence diagrams per scenario | Mermaid `sequenceDiagram` |
| 6 | State machines | Mermaid `stateDiagram` |
| 7 | Retroactive ADRs | Nygard template + Evidence section |
| 7 | Dead-code register | table with evidence set and verdict |

## Tooling

Prefer tools that emit **queryable facts** over tools that emit pictures. A picture
cannot be tested against a hypothesis.

| Category | Tools | Availability¹ |
|---|---|---|
| Census | `scc`, `cloc`, `tokei` | not checked |
| Churn / behavioral | CodeScene, `code-maat`, `git log --numstat` pipelines | not checked |
| Language-agnostic AST | tree-sitter, `ast-grep`, Comby, srcML | not checked |
| Queryable code DB | CodeQL, Joern (AST+CFG+PDG), Semgrep, Sourcegraph/SCIP | Sourcegraph: ✓ live, free — see note |
| Comprehension IDE | SciTools Understand, Structure101, NDepend, CAST Imaging | Structure101: ✗ discontinued standalone — see note |
| JS/TS graphs | dependency-cruiser (rules can encode a Reflexion Model as lint), madge, `ts-morph` | not checked |
| Python | pyreverse, pydeps, import-linter, Pyan | Pyan: ✓ actively maintained — see note |
| JVM | jdeps, ArchUnit, Soot/SootUp, WALA | not checked |
| C/C++ | clangd, include-what-you-use, Doxygen+Graphviz, cscope | not checked |
| Diagram-as-code | Structurizr DSL, Mermaid, PlantUML, Graphviz, D2 | not checked |
| Dynamic tracing | OpenTelemetry, `py-spy`, `perf`, `strace`, JFR, `rr`, coverage tools | not checked |
| Schema | `pg_dump --schema-only`, SchemaSpy, SchemaCrawler, dbt lineage | not checked |
| Conformance in CI | ArchUnit, dependency-cruiser rules, import-linter, Konsist | not checked |

¹ Checked 2026-08-19, web search, three tools only — the rest of this table has not been
re-verified and "not checked" means exactly that, not "assumed fine."
- **Sourcegraph public code search** — still live and free at sourcegraph.com/search
  (2M+ open-source repos indexed). Sourcegraph itself went source-available (not OSS) in
  2023 and has pivoted toward Cody/AI coding assistant as its core business, but the public
  search product is still up.
- **Structure101** — no longer sold as a standalone product. Acquired by Sonar
  (SonarSource); Sonar's own FAQ states new Structure101 sales have stopped and its
  architecture-analysis capability is being folded into the Sonar platform. Existing
  customers get support only, at structure101.com/resources.
- **Pyan** (`pyan3` on PyPI) — actively maintained. The `Technologicat/pyan` fork is now
  the sole official repository (the older stable repo was archived), was revived in
  February 2026, supports Python 3.10-3.14, and shipped v2.6.0 on 2026-04-30.

## The falsification step: Reflexion Model

Murphy, Notkin & Sullivan (FSE 1995). This is the step that separates a teardown from a
guess, and it is mechanical enough to be repeatable.

1. **Draft the hypothesized high-level model** — boxes and permitted arrows. Source it
   from directory structure, team ownership, deployment units, and domain vocabulary.
   *Not* from clustering output.
2. **Write the mapping** — regex or path rules assigning every source entity to a box.
   Entities that match nothing are themselves a finding.
3. **Compute the diff** against the extracted dependency facts. Three outcomes:
   - **Convergence** — an arrow you predicted and the code has. Confirmed.
   - **Divergence** — an arrow the code has and you did not predict. Either your model is
     wrong or the code violates its own architecture. Both are findings.
   - **Absence** — an arrow you predicted and the code does not have. Usually your model
     is wrong; occasionally a component is dead.
4. **Iterate.** Adjust model or mapping and recompute. Stop only when every divergence
   and absence is explained, accepted, or filed as tech debt with an owner.

Run automated clustering (ACDC/ARC-style) as a **second opinion** only. Clustering output
presented as the primary architecture is one of the ten failure modes below.

Encode the settled model as CI rules (ArchUnit, dependency-cruiser, import-linter) so the
reflexion diff stays at zero after you leave. This turns a one-off teardown into a
standing guarantee.

## Eleven failure modes

1. **Static call graphs are unsound** wherever there is reflection, DI, or dynamic dispatch —
   see Phase 4 for the measured recall figures and their scope. Never present static structure
   as observed behavior.
2. **Framework magic / IoC** — annotations, decorators, and DI containers wire things no
   static edge shows. Enumerate framework entry points explicitly.
3. **Config-driven behavior** — the same binary behaves differently per environment.
   Read the config surface as part of the architecture, not as deployment trivia.
4. **Dead code false positives** — reflection, dynamic dispatch, and cron-only paths look
   dead and are not. Require both static *and* coverage evidence, then scream-test.
5. **Reverse engineering the code instead of the domain** — producing a perfect map of
   the implementation that answers no business question. Anchor scenarios in business
   value.
6. **Clustering output presented as truth** — algorithmic module detection has measured
   accuracy well below what its confident output implies.
7. **Stale or ambiguous provenance** — a finding without a SHA cannot be rechecked.
8. **Vendored and generated code polluting metrics** — fix with the Phase 1 exclusion
   manifest, before anything else.
9. **Confirmation bias in hypothesis refinement** — when evidence fits, ask what else
   would produce the same evidence before accepting it.
10. **Assuming tests describe intended behavior** — tests encode what someone once
    believed, including bugs that got baked into assertions.
11. **Coupling through shared state.** Two components writing the same database table,
    producing and consuming the same queue topic, sharing a cache key namespace, or sharing a
    filesystem path are tightly coupled with **no static edge and no import to find**. In
    service-oriented systems this is the most common reason a recovered architecture is simply
    missing arrows. Enumerate table writers, topic producers and consumers, and shared paths as
    first-class dependency edges in Phase 3, or the Reflexion diff will happily converge on an
    incomplete model.
