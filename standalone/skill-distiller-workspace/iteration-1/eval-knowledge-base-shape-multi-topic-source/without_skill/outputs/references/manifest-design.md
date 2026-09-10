# Manifest Design Across Ecosystems

Detailed field-by-field reference for the five packaging formats. Use this
when actually writing or reviewing a manifest, not just triaging (for
triage, the table in `SKILL.md` is enough).

## Hermes Agent — `hermes.manifest.json`

Required top-level fields:

- `name` — publisher-namespaced identifier.
- `version` — semver.
- `entrypoint` — path inside the bundle to the runnable module.
- `capabilities` — array of scoped permission strings, e.g. `fs.read`,
  `http.egress`, `process.spawn`. Typed and enumerable, not free text.
- `runtime` — `{ "engine": "hermes-rt", "min_version": "2.3" }`.
- `signature` — Ed25519 signature over a hash that covers **the manifest
  itself**, not just the payload. This closes a "swap the manifest after
  signing the payload" attack that most other ecosystems remain exposed to,
  because most sign the archive, not the declared-capabilities text inside it.

Optional fields worth using:

- `permissions.prompt` — human-readable justification shown to an installer
  before a capability grant is accepted. Treat this as display text only;
  never put a real value (key, token, URL with embedded credentials) here —
  see `secrets-exclusion.md` for why this specific field is a known leak
  vector in practice.
- `dependencies` — other Hermes bundles by name + version range.

Design takeaway: Hermes is the only one of the five where the *thing you'd
want to audit* (capabilities) is both structured and covered by the
signature. If you're designing a new manifest format from scratch, replicate
this: make the capability list a typed enum, and make the signature cover
it.

## LangChain Hub — `hub_manifest.yaml` + `README.md`

Required: `repo` (owner/name), `type` (`prompt` | `chain` | `agent`),
`lc_version`.

Optional but increasingly common: `input_schema` (JSON Schema block) — as of
this writing roughly a third of published agents still omit it, so treat its
absence as normal rather than a red flag on its own.

What's missing entirely: any capability or permission declaration. A pulled
chain can invoke whatever tools the puller wires it to; the hub ships
prompt/graph structure only, with no execution sandboxing and nothing in the
manifest that would let an installer know what a chain is *supposed* to be
allowed to touch. If you're reviewing a LangChain Hub-style manifest for
completeness, the README's prose description of "expected tools" is the
closest thing to a capability declaration that exists — read it as
documentation, not as an enforceable contract.

## CrewAI — `crew.yaml` (or `pyproject.toml [tool.crewai]` table)

Required:

- `agents` — list of role manifests: `role`, `goal`, `backstory`,
  `allow_delegation`.
- `tasks` — list with `description`, `agent`, `expected_output`.
- `process` — `sequential` | `hierarchical`.

Tool bindings are declared by class name (`tools: [SerperDevTool,
FileReadTool]`) and resolved at **install time** against whatever tool
classes are importable in the consumer's environment. This makes the
manifest describe an *interface*, not a concrete capability grant — the same
`crew.yaml` can produce different real-world capabilities depending on what
the installer's environment happens to have importable. When reviewing a
crew manifest, check what tool classes actually resolve in the target
environment, not just what names are listed.

`studio_meta` (from CrewAI Studio exports) is non-normative UI layout only;
safe to ignore outside Studio.

## OpenAI Assistants — `assistant.json` (community export format)

Not a first-party manifest — OpenAI's API has no package concept, only a
live server object addressed by `asst_...` ID. The de facto community export
format (used by tools like AssistantHub-style dashboards) captures:

- `model`
- `instructions`
- `tools` — array of `{type, function}`, `function` includes a full JSON
  Schema.
- `tool_resources` — **references** to vector store / code-interpreter file
  IDs, not the files themselves.
- `metadata` — free-form key-value, capped at 16 pairs / 512 chars each by
  the API.

Portability caveat: `tool_resources` file IDs and vector store IDs are
account-scoped. Re-importing an exported `assistant.json` into a different
account requires re-uploading every referenced file and rewriting the ID
map — a step import tools handle inconsistently, sometimes silently
producing an assistant with a dangling file reference. If you're building or
reviewing an import path for this format, treat "does it re-upload and
remap `tool_resources`, or does it silently drop/break it" as the single
most important correctness question.

## MCP Registry — `server.json`

Required: `name` (reverse-DNS-style namespace, e.g.
`io.github.acme/weather`), `description`, `version`, `packages` (array of
install methods — npm, pip, docker image, or remote URL — each with its own
`registry_type` and `identifier`).

Increasingly present: `capabilities.tools` / `capabilities.resources` as a
declarative preview. Treat this as advisory only — the authoritative
capability list is whatever the server actually returns at runtime via
`tools/list`. A `server.json` preview and a server's real `tools/list`
output can diverge (stale preview, version skew), so don't build logic that
trusts the manifest preview over a live `tools/list` call.

Note on scope: `server.json` describes a *tool provider*, not an agent. In
practice, a large share of registry entries are thin wrappers exposing an
entire external agent or workflow as a single MCP tool — so when reviewing
one of these, the packaging questions in this skill still apply, just one
layer removed (the "agent" is behind the tool call, not the manifest).

## Cross-ecosystem pattern

All five manifest formats are answering the same three underlying
questions — identity+version, how to install/run, what it's allowed to
touch — but only Hermes, and MCP Registry to a lesser (advisory-only)
extent, treat the third question as structured, checkable data rather than
prose or an implicit consequence of whatever gets wired up at install time.
When designing a new manifest format, that's the property worth copying
first.
