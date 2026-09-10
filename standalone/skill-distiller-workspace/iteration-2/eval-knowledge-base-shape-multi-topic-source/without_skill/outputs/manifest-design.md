# Manifest Design Across Agent Distribution Ecosystems

Reference for: designing a new agent/package manifest, or reviewing an existing one for completeness.

## The six field categories every mature manifest converges on

1. **Identity fields** — name, namespace/owner, version.
   - Hermes Agent and MCP Registry use semver (`"1.4.0"`).
   - LangChain Hub addresses artifacts by `owner/repo:commit-hash` rather than semver.
   - OpenAI Assistants uses an opaque, server-assigned ID (`asst_...`); there is no user-authored identity field at all.

2. **Compatibility fields** — the minimum runtime/protocol version and target model hints.
   - Examples: Hermes's `hermes-runtime: >=2.3`, MCP's `protocolVersion`, CrewAI's `llm:` field, Assistants' `model:` field.
   - A manifest without a compatibility field is a common failure mode in early-stage ecosystems (CrewAI crews shared as raw repos frequently omit any pinned model or framework version, so a crew that worked against one CrewAI release silently breaks against the next).

3. **Capability declarations** — the tools/functions the package exposes or requires.
   - Hermes and MCP Registry declare these as JSON Schema up front, reviewable before install.
   - CrewAI declares them as references to importable tool classes (not schema — the actual capability is whatever the referenced Python class does, which may not match its name or docstring).
   - Assistants declare a `tools` array at assistant-creation time, but built-in tools (file_search, code_interpreter) carry broad, non-granular capability grants (e.g., "may read any file in this vector store") rather than fine-grained scopes.

4. **Behavioral payload** — the system prompt, role/goal/backstory text, or chain graph. This is the field most exposed to prompt-injection risk when pulled from an untrusted registry, since in most default installs it becomes part of the effective system prompt with no review step.

5. **Data references** — pointers to external resources needed at runtime (a vector store ID, a knowledge-base path, an MCP resource URI). Well-designed manifests store *references only*, never the resolved data and never resolved credentials. See `data-ownership-separation.md` for what happens when this rule is violated, and `secrets-exclusion.md` for the credential-specific version of the same rule.

6. **Permission/scope declarations** — increasingly present but still optional in most ecosystems today. Hermes has a `scopes:` block modeled on OAuth scopes; MCP Registry is only beginning to standardize a `capabilities.permissions` extension. Absence of this field is itself flagged as an unsolved risk (see `unsolved-risks-checklist.md`, "late-bound capability disclosure").

## A minimal, ecosystem-agnostic baseline schema

Use this as a starting point when no existing ecosystem format fits, or as a checklist against an existing one:

```json
{
  "name": "acme/invoice-triage-agent",
  "version": "1.4.0",
  "runtime": { "protocol": "mcp", "minVersion": "1.2" },
  "entrypoint": "stdio:./server.js",
  "capabilities": {
    "tools": ["fetch_invoice", "flag_anomaly"],
    "resources": ["invoices://recent"]
  },
  "dataRefs": {
    "vectorStore": "env:INVOICE_KB_STORE_ID"
  },
  "secrets": ["INVOICE_API_KEY"],
  "signature": "ed25519:base64..."
}
```

Design choices worth keeping if you copy this:
- `dataRefs` values are always a resolution instruction (`env:NAME`, `vault:path/to/key`), never a literal store ID or URI to a specific tenant's data.
- `secrets` is a list of *names* the host must inject, matched at validation time against an identifier pattern (e.g. `^[A-Z_][A-Z0-9_]*$`) so the field cannot hold a value that looks like a real key.
- `signature` is present even for packages that don't strictly require it — an unsigned-but-signable format ages better than one that has to retrofit signing later.

## Per-ecosystem manifest comparison

| Field category | Hermes Agent | LangChain Hub | CrewAI | OpenAI Assistants | MCP Registry |
|---|---|---|---|---|---|
| Identity | name + semver, signed | `owner/repo:commit` | repo-implicit, no formal field | server-assigned opaque ID | name + semver |
| Compatibility | `hermes-runtime` range | none (commit-pinned instead) | `llm:` hint only, often absent | `model:` field | `protocolVersion` |
| Capabilities | JSON Schema, upfront | n/a (not a code artifact) | class references (opaque) | `tools` array, coarse-grained built-ins | discovered late, post-connect |
| Behavioral payload | `prompts/` dir | the artifact itself | `backstory`/`goal` in YAML | `instructions` field | n/a (server, not agent) |
| Data references | `dataRefs` block, reference-only | none (stateless artifact) | ad hoc, often embedded paths | `vector_store_id` (assistant- or thread-level) | resource URIs, per-server convention |
| Permission scopes | `scopes:` block | none | none | none (implicit in tool grant) | draft `capabilities.permissions` (2026, not yet standard) |

## What to check when reviewing an unfamiliar manifest format

- Does every field in the "data references" category hold a pointer, or does at least one field's type allow a literal value?
- Is there a compatibility field at all, or is version compatibility purely assumed?
- Are capabilities declared upfront and reviewable, or only discoverable after the package is already running (MCP Registry's model — powerful, but underspecifies the manifest as a security review artifact)?
- Is there any permission/scope concept, or is every declared tool implicitly full-trust?
