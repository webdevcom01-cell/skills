# Manifest design across agent-distribution ecosystems

Load this when designing, evaluating, or comparing the metadata schema an
agent/tool package publishes — what fields to require, how to version, and
whether the registry can validate the artifact or only the manifest shape.

## Cross-ecosystem comparison

| Ecosystem | Manifest artifact | Identity scheme | Versioning | Validated at publish/share time? |
|---|---|---|---|---|
| Hermes Agent | `agent.json` inside `.hagent` bundle | Reverse-DNS `id`, registry-enforced uniqueness | Strict semver, must strictly increase per `id` | Yes — registry rejects the publish on collision, non-increasing version, or a failed skill-linter pass |
| LangChain Hub | No separate manifest — the pushed prompt/chain/graph object carries its own inline metadata (`lc_hub_owner`, `lc_hub_repo`, `readme`, `tags`) | `owner/repo-name` handle | Content hash (exact) or mutable tag like `:latest` | No separate schema to validate against — a chain can reference a tool by name the Hub never checks exists |
| CrewAI | `agents.yaml` + `tasks.yaml`, loaded by `crew.py`; no standardized bundle format | Whatever the enclosing Python package/repo uses (PyPI name, git URL) | Inherited entirely from Python packaging (`pyproject.toml`/`requirements.txt`) | No — malformed YAML or a `tasks.yaml` entry pointing at a nonexistent agent role fails at crew-construction time in the consumer's process, because there is no separate publish time |
| OpenAI Assistants | The `Assistant` object itself (`model`, `instructions`, `tools`, `tool_resources`) | Account-scoped `assistant_id` — no cross-account identity at all | No `version` field; a team versions the creation payload in its own VCS if it wants that | N/A — there is one owner (the account), not a publisher/installer split, so there's nothing to validate at share time; sharing = handing over the creation payload for the recipient to call `create()` with |
| MCP Registry | `server.json`, pointing at the real package (npm/PyPI/OCI/`.mcpb`), not hosting it | DNS-verified reverse-domain namespace (e.g. `io.github.acme/weather`) — ownership proven before publish | Semver in `server.json`; separately, each `packages` entry pins a version/tag in *its* registry | Manifest shape only — required fields present, namespace ownership proven. The Registry cannot validate that the referenced package version still exists, is unchanged, or is safe; that's downstream of npm/PyPI/OCI's own guarantees |

## Decision rules

**A namespaced, ownership-verified identity plus a strictly-increasing
version is the recurring pattern for anything the registry itself hosts or
indexes with authority over publish.** Hermes (`id`, registry-enforced
uniqueness) and MCP Registry (DNS-verified reverse-domain `name`) both landed
on this independently. Where an ecosystem instead uses an unverified
owner/repo-style handle (LangChain Hub), namespace collision and
impersonation risk is correspondingly higher — see
`unsolved-risks-checklist.md`, item 1.

**If there's no dedicated manifest schema separate from the shared object
itself, publish-time validation has nothing to check against, so the burden
shifts entirely to whoever consumes the package.** LangChain Hub (the pushed
object carries its own metadata) and CrewAI (plain YAML loaded by
project-specific code) both work this way; both defer "does this actually
run" checking to construction/runtime, not publish/share time. This is a
legitimate design choice when the ecosystem doesn't control the consuming
runtime — but a manifest schema with a validation gate at publish time can
catch problems ahead of the consumer, which the object-carries-its-own-
metadata pattern can never do since there is nothing to check it against.

**Content-addressing (hashing) and strict semver solve different problems
and aren't interchangeable.** A content hash guarantees byte-identical
fetches — a client with hash `a1b2c3d` cached never needs to re-fetch it,
which is what makes LangChain Hub's cache layer safe. Semver gives humans a
legible ordering and compatibility signal a hash never can. A design that
needs both cache-safety and human-legible ordering needs both mechanisms,
not one standing in for the other.

**When a registry only indexes and doesn't host the actual artifact (MCP
Registry, and CrewAI's reliance on PyPI), it can only validate manifest
*shape* — never artifact safety.** State this limitation explicitly to
anyone relying on the registry's validation; the source treats this as the
single structural feature that makes the MCP Registry's trust model
different from Hermes' or LangChain Hub's, where the registry directly
holds (or content-hashes) what actually gets distributed.

**Capability/dependency declarations inside a manifest are advisory-only in
every case surveyed — none of the five enforce them structurally.** Hermes'
`model_requirements` (minimum context window, tool-use/vision) is surfaced
to the installing user as a warning only, never enforced. Hermes' `skills`
list (which bundled skill IDs a package uses) is a flat list used for the
registry's own reverse-index/impact-analysis tooling, not a verified
dependency graph — the source names this as the closest thing to a
dependency declaration among the five, and notes it still falls short of an
enforced graph (see `unsolved-risks-checklist.md`, item 6).

**Keep manifest-to-bundled-file cross-references shallow.** Not directly
stated as a rule in the source's ecosystem survey, but consistent with every
example in it: every manifest surveyed points at files or objects directly
(an `entrypoint` path, a `tool_resources` file ID, a `packages` registry
reference) — none of them chain through an intermediate reference to reach
the actual artifact.
