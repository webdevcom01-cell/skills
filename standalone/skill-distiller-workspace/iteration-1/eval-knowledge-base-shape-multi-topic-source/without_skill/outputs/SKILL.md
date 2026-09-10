---
name: agent-packaging-patterns
description: Guidance for designing how an AI agent (or agent-adjacent tool) gets packaged, published, and installed across ecosystems like Hermes Agent, LangChain Hub, CrewAI, OpenAI Assistants, and the MCP Registry. Covers manifest schema design, separating distributor-owned data from user-owned/runtime data, keeping secrets out of published artifacts, and a checklist of distribution risks that are not yet solved by any ecosystem. Use when designing or reviewing a manifest/package format for an agent, chain, crew, assistant, or MCP server; when deciding what belongs in a published bundle versus local install-time config; when auditing a package for embedded secrets before publishing; or when the user asks about agent distribution, agent packaging, manifest design, or publishing agents/tools to a registry.
---

# Agent Packaging & Distribution Patterns

## When to use this skill

Reach for this skill when the task is about the *distribution boundary* of
an agent — the line between "what ships in the package" and "what only
exists once someone installs and runs it" — rather than the agent's
internal logic. Concretely:

- Designing or reviewing a manifest format (`manifest.json`, `crew.yaml`,
  `server.json`, an assistant export, etc.) for an agent/tool/chain.
- Deciding whether a field belongs in the published package or should stay
  local to the installer (config, credentials, account-scoped IDs).
- Auditing a package, bundle, or export before publishing it to a registry,
  specifically for embedded secrets or leaked local context.
- Reasoning about what could go wrong when an agent is pulled from a
  registry and installed somewhere else (squatting, stale pins, permission
  creep, no revocation path).

Do not reach for this skill for the agent's own prompt engineering, tool
implementation, or orchestration logic — those are separate concerns from
how the finished thing gets packaged and handed to someone else.

## The four questions a manifest has to answer

Every packaging format in this space (Hermes Agent, LangChain Hub, CrewAI,
OpenAI Assistants exports, MCP Registry) is ultimately answering the same
four questions with wildly different rigor. Use these as a checklist when
designing or reviewing any manifest:

1. **Identity + version** — name, namespace, version, provenance. Nearly
   every ecosystem gets this right.
2. **How to install/run it** — entrypoint, runtime/engine requirement,
   install method (package registry, docker image, bundle). Also generally
   solid across ecosystems.
3. **What it's allowed to touch** — declared capabilities/permissions. This
   is where ecosystems diverge sharply: structured and checkable in some
   (Hermes, MCP Registry), advisory prose or entirely absent in others
   (LangChain Hub, CrewAI). Treat this as the field most worth getting
   right, because it's the one every audit and every risk in this space
   traces back to.
4. **What must NOT ship in it** — credentials, account-scoped resource IDs,
   local paths, real internal context accidentally left in flavor-text
   fields. See `references/secrets-exclusion.md` and
   `references/data-ownership-separation.md`.

For full manifest schemas and field-by-field comparison across the five
ecosystems, see `references/manifest-design.md`.

## Quick reference: manifest field maturity by ecosystem

| Ecosystem | Manifest artifact | Structured capability declaration? | Secrets kept out by construction? | Version pinning enforced? |
|---|---|---|---|---|
| Hermes Agent | `hermes.manifest.json` (signed) | Yes — typed `capabilities` array | Mostly — `env:` reference pattern, but free-text prompt field can leak | Yes |
| LangChain Hub | `hub_manifest.yaml` + README | No — prose only | No — no scanning of prompt/example bodies beyond regex on push | No |
| CrewAI | `crew.yaml` / `pyproject.toml` table | No — tools referenced by class name, resolved at install | Mostly — tools referenced not embedded, but `backstory` fields are an untyped leak vector | No (pip range resolution) |
| OpenAI Assistants | `assistant.json` (community export) | Partial — `tools` array has schemas, no permission model | Yes by default (server-side object); risk shifts to export/import tooling | N/A (server-hosted) |
| MCP Registry | `server.json` | Partial — `capabilities.tools/resources` is a preview, not authoritative | Yes by construction — registry never holds credential values | Yes |

This table is a starting point for triage, not a substitute for reading the
relevant reference file when you're actually designing a manifest.

## The core rule for data placement

When in doubt about whether a field belongs in the published package: ask
whether the value would be **the same for every installer** (distributor-
owned — ships in the package) or **necessarily different per installer**
(user-owned — must be supplied at install/run time, never baked in). A
credential, an account-scoped ID, a local file path, or free-text "flavor"
fields that tempt an author to paste real internal context are the
recurring failure points. Full taxonomy and per-ecosystem leak patterns:
`references/data-ownership-separation.md`.

## Before publishing anything

Run through `references/secrets-exclusion.md` for the three real secrets-
exclusion patterns (reference-don't-embed, pre-publish scanning, and
scoped/short-lived credentials issued post-install) and their actual
failure modes — self-attested "we promise not to hardcode secrets" rules
and after-the-fact key rotation are not real mitigations; know why before
relying on either.

## Known unsolved risks

No ecosystem surveyed here has solved cross-ecosystem capability modeling,
namespace squatting, transitive permission escalation, or revocation of
already-installed packages. Before telling a user a design is "secure" or
"safe to publish," check it against `references/unsolved-risks-checklist.md`
— these are structural gaps in the space, not things a single manifest
field can fix, and a design review should name them as residual risk rather
than imply they're solved.
