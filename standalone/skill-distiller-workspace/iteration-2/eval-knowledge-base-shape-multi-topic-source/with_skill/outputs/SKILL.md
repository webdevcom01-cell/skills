---
name: agent-distribution-patterns
description: Reference for how AI agent/skill ecosystems (Hermes Agent, LangChain Hub, CrewAI, OpenAI Assistants, MCP Registry) structure distribution manifests, separate distributor-owned from user-owned data, and exclude secrets from published packages — plus a checklist of distribution risks none of them fully solve. Use when designing or reviewing a manifest/schema for a package, skill, or agent registry; deciding whether a config field belongs to the publisher or the installer; auditing a manifest for how it represents credentials; or checking a new distribution mechanism against known-unsolved risks (namespace collisions, revocation, secret rotation, inconsistent versioning, supply-chain provenance, license propagation). Do NOT use for building an MCP server (use mcp-builder), packaging a Claude Agent Skill (use skill-creator-pro or skill-distiller), or debugging one deployed agent's own distribution setup — check whether soma-distribution already covers that first.
license: Apache-2.0
metadata:
  version: "0.1.0"
  provenance: "distilled from a synthesized composite retrospective, not a line-by-line audit of live vendor docs — see source-document.md and the caveat below"
---

# Agent distribution & packaging patterns

Cross-ecosystem reference covering how five agent/skill distribution systems
— Hermes Agent, LangChain Hub, CrewAI, OpenAI Assistants, MCP Registry —
handle manifest design, distributor/user data separation, and secrets
exclusion, plus a running list of risks none of them fully solve.

**Provenance caveat:** the per-ecosystem specifics here (exact field names,
numeric limits like the OpenAI metadata pair count) were assembled for a
comparative retrospective, not verified line-by-line against current vendor
documentation. Treat named fields and general patterns as reliable; verify
any specific number against live docs before it drives a production
decision.

## Core mental model

Every distribution manifest — regardless of ecosystem — is answering three
questions, and most design mistakes trace back to one of them being answered
implicitly instead of on purpose:

1. **What does this package claim to be** — identity, version, entrypoints,
   capabilities — and how much of that claim is actually machine-checked
   versus just asserted?
2. **Who owns each piece of data the manifest or its runtime touches** — the
   publisher/registry, or the installing user? A field with no explicit
   owner tends to silently default to whichever side happens to be easiest,
   which is how publisher data leaks into every install or user data ends
   up entangled with public package metadata.
3. **Can a secret's value ever end up in what gets published** — not just
   "is there a `secrets` field," but is a literal value structurally
   possible to place there, or only stoppable by convention?

## Decision rules (apply to any manifest, not just these five)

- **A manifest may declare that a secret is required. It must never be able
  to declare what that secret's value is.** Check whether this is enforced
  by the schema itself (a value field simply doesn't exist) or only by
  convention (a plain string field that happens to usually hold a
  reference) — those are very different guarantees. See
  `references/secrets-exclusion.md`.
- **Interpolation syntax (`${VAR}`-style references) is a runtime
  convenience, not a schema constraint**, unless the schema structurally
  forbids a literal value in that field. If it's just a plain string, a
  literal secret can sit there undetected by any schema validator — the
  only real defense is a raw-text scan over the *whole* file, not a diff.
- **Give every manifest field an explicit owner — distributor or user —
  during design, not after a bug report.** A resource pointer that isn't
  clearly re-scoped per install (e.g. a "default" ID left pointing at the
  publisher's own data) is the most common way this goes wrong. See
  `references/data-ownership-separation.md`.
- **"Schema-valid" and "behavior-safe" are two different claims.** A
  correctly-structured, even correctly-signed, manifest says nothing about
  whether the code it ships is safe to run. Don't let schema validation
  quietly stand in for a security review, and don't imply one when
  describing the other.
- **Don't assume a packaging problem is solved just because it isn't visible
  in the ecosystem you're currently looking at.** Revocation, secret
  rotation, namespace collisions, and license propagation are unsolved to
  varying degrees in all five systems studied — see
  `references/unsolved-risks-checklist.md` before treating any of them as a
  solved problem elsewhere.

## References

Load only the file that matches what you're actually doing — these are
written to stand alone, not to be read front-to-back.

- `references/manifest-design.md` — load when designing or reviewing a
  manifest/schema itself: what fields the five ecosystems declare, how
  versioning and entrypoints are represented, what's actually enforced
  versus merely documented, and takeaways for a new schema.
- `references/data-ownership-separation.md` — load when deciding whether a
  given field or piece of runtime data belongs to the publisher/registry or
  to the installing user, or auditing an existing manifest for where that
  line is (or isn't) drawn.
- `references/secrets-exclusion.md` — load when publishing, reviewing, or
  scanning any manifest/config that references credentials, or when
  deciding how a schema should represent a required secret.
- `references/unsolved-risks-checklist.md` — load before assuming a new or
  unfamiliar distribution mechanism has already solved a trust, lifecycle,
  or privacy problem that these five haven't — use it as a checklist when
  reviewing a registry or packaging design, your own or someone else's.

## Source

`source-document.md` (in this same directory) is the synthesized composite
retrospective this skill was distilled from — kept for inspection, not
loaded as part of normal use of this skill.
