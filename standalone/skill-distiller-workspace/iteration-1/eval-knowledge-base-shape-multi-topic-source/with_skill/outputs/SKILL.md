---
name: agent-packaging-patterns
description: "Reference for how five agent ecosystems (Hermes Agent, LangChain Hub, CrewAI, OpenAI Assistants, MCP Registry) package and distribute agents/tools -- manifest field design, separating distributor-owned data from user-owned runtime state, excluding secrets from published packages, and a checklist of unsolved risks (typosquatting, no signing standard, silent version drift, no revocation signal, among others). Use when designing or reviewing a manifest schema, deciding how installs should separate publisher-owned files from user customization, deciding how to scan a package for embedded credentials, or auditing an agent-distribution design for gaps. Trigger phrases -- design a manifest for this agent, how should I package or distribute this agent, keep secrets out of the package, distributor vs user data. Do NOT use for a specific SOMA/AgentStack agent (soma-agent-debugger), an MCP server's code (mcp-builder), or a Claude Skill itself (skill-creator-pro)."
metadata:
  version: "1.0.0"
---

# Agent packaging patterns

Five ecosystems answer the same four questions differently: what goes in the
manifest, how distributor-owned data stays separate from user-owned data,
how secrets stay out of the published artifact, and what's still unsolved.
No ecosystem surveyed gets all four fully right — the value here is seeing
which trade-off each one made, so a new design can make its trade-offs on
purpose instead of by accident.

## The five ecosystems, at a glance

| Ecosystem | What gets distributed | Hosts the artifact itself? |
|---|---|---|
| Hermes Agent | `.hagent` bundle (`agent.json` + skills + assets) | Yes |
| LangChain Hub | Content-hashed prompt/chain/graph object | Yes |
| CrewAI | Plain Python package (`agents.yaml`/`tasks.yaml`/`crew.py`) | No — delegates to PyPI/git |
| OpenAI Assistants | Server-side `Assistant` object (no local artifact) | N/A — one owner, no publisher/installer split |
| MCP Registry | `server.json` pointing at npm/PyPI/OCI/`.mcpb` | No — indexes only |

## Core decision rules (apply regardless of which ecosystem you're modeling on)

- **Never let update-managed and user-managed data share one directory or
  object.** The one ecosystem that got this wrong first (bundled "default
  config" meant to be hand-edited, then silently destroyed on update) fixed
  it structurally — two separate trees with no shared write surface — not
  by trying to detect edits after the fact. Detecting edits via checksum
  diffing was tried and abandoned as unreliable. Full breakdown, including
  the alternative of never mutating in place at all:
  `references/data-ownership-separation.md`.
- **A manifest schema should have no field for credentials, and a
  publish-time scan for secret-shaped values should hard-block, not warn.**
  Two ecosystems converged on this independently: a rejected publish is
  recoverable, a leaked-and-already-pulled key is not. Full pattern,
  including the "declare the secret's name, not its value" convention:
  `references/secrets-exclusion.md`.
- **A registry that only indexes an artifact (rather than hosting or
  content-hashing it) can validate manifest shape but never artifact
  safety — say this limitation out loud rather than letting it be assumed
  away.** Full manifest-field comparison across all five:
  `references/manifest-design.md`.
- **Mutable/floating version references are the default failure mode for
  silent behavior change, and no ecosystem surveyed forces pinning.**
  Relevant whenever a design lets a version reference resolve differently
  over time (a `:latest` tag, a floating dependency pin). Part of the
  broader open-risks list: `references/unsolved-risks-checklist.md`.

## Reference index

- `references/manifest-design.md` — load when choosing manifest fields,
  identity/namespacing scheme, or versioning approach; has the full
  field-by-field comparison table across all five ecosystems.
- `references/data-ownership-separation.md` — load when designing
  install/update semantics; covers both the structural-separation pattern
  and the content-addressed sidestep, with the trade-offs of each.
- `references/secrets-exclusion.md` — load when deciding how a publish flow
  should handle credentials; covers the hard-block-scan pattern, the
  declare-name-not-value pattern, and documented gaps even where a scanner
  exists.
- `references/unsolved-risks-checklist.md` — load when auditing a design
  end-to-end; seven open items (typosquatting, no signing standard, silent
  version drift, no revocation signal, unscanned secret surfaces, unmodeled
  transitive trust, no deprecation convention), explicitly unranked.
