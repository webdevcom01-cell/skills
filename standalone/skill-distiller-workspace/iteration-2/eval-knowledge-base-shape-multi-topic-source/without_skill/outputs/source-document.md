# Packaging and Distributing AI Agents: Manifests, Data Ownership, and Unsolved Risks Across Five Ecosystems

*Internal reference document. Synthesized consolidation of packaging patterns observed across agent distribution ecosystems, current as of early 2026. Not a specification for any single platform — treat concrete field names as illustrative, not authoritative, and check each platform's own docs before shipping.*

## 1. Overview

An AI agent package is not a library. A library ships code that a host program calls. An agent package ships a *bundle of intent*: a system prompt or role definition, a set of tool/function declarations, a model or model-class preference, optional retrieval sources, and often a claim on user data (memory, credentials, conversation history) that persists across sessions and across versions of the package. This combination — executable-adjacent behavior plus a data-ownership claim plus a trust boundary with the end user — is why agent distribution has converged on its own packaging conventions rather than reusing npm/pip wholesale, even though most registries borrow their transport mechanics.

Five ecosystems illustrate the range of approaches in production or near-production use:

- **Hermes Agent** — a self-hosted agent runtime with a signed-manifest package format (`.hermes` bundles) aimed at teams who want on-prem control over agent supply chain.
- **LangChain Hub** — a prompt/chain-centric registry where the unit of distribution is often smaller than a full agent (a prompt template, a chain graph, or a full `AgentExecutor` config).
- **CrewAI** — a multi-agent orchestration framework where distribution units are "crews" (teams of role-based agents) plus the tools and tasks they share.
- **OpenAI Assistants** (the Assistants/Responses API model) — a hosted, platform-owned representation where the "package" is largely server-side state (an assistant object) referencing uploaded files, vector stores, and function tool schemas.
- **MCP Registry** — the Model Context Protocol's public/community registry for discovering and installing MCP servers, which package tools and resources rather than full agents, but which agents increasingly depend on as their primary extension mechanism.

The rest of this document works through four cross-cutting concerns that recur in all five: how manifests are structured, how distributor-owned data is kept separate from user-owned data, how secrets are kept out of the package, and what risks remain unresolved industry-wide.

## 2. The Five Ecosystems at a Glance

**Hermes Agent** packages are tarballs containing a `manifest.json`, a `prompts/` directory, a `tools/` directory of tool schemas (JSON Schema, not code), and a detached Ed25519 signature file. The runtime verifies the signature before loading. Hermes explicitly does not allow arbitrary code execution inside the package — tools are declarative schemas that the runtime binds to *locally registered* implementations, which sidesteps a large class of supply-chain code-execution risk at the cost of portability (a Hermes package is inert until the host has matching tool implementations installed).

**LangChain Hub** is closer to a content registry than a code registry: most pushed artifacts are serialized prompt templates or LCEL/graph configs in a JSON/YAML-ish serialization format, addressed by `owner/repo:commit-hash` similar to a git-backed package. Because the artifact is often "just a prompt," the attack surface is different — the main risk is prompt injection or subtle behavioral manipulation smuggled into a template that looks benign, not binary supply-chain compromise.

**CrewAI** distributes at the granularity of a "crew": a YAML/Python definition of agents (each with a role, goal, backstory, and tool list), tasks, and a process (sequential/hierarchical). Crews are typically shared as GitHub repos or, increasingly, through a hosted "CrewAI Enterprise" template gallery. There is no single binary package format; the de facto manifest is `agents.yaml` + `tasks.yaml` + a `crew.py` entry point.

**OpenAI Assistants** inverts the usual model: the assistant's defining state (instructions, model, tool list, attached vector store IDs) lives on OpenAI's servers, addressed by an `asst_...` ID. What a developer "distributes" is usually a small JSON config plus setup script that recreates the assistant via API calls, or, since the introduction of Assistant templates, an export/import JSON blob. Because file search and code interpreter tools can access uploaded files, packaging an assistant awkwardly bundles a data-distribution problem (should the uploaded knowledge base ship with the template?) into what looks like a config file.

**MCP Registry** packages are the leanest: a `server.json` (or `mcp.json` in client-side config) describing a name, version, transport (stdio/http/sse), a launch command, and a list of declared capabilities (tools, resources, prompts) that are discovered dynamically at connect time rather than declared exhaustively in the manifest. This late-binding design is powerful (a server can add tools without a new manifest release) but means the manifest alone underspecifies what the package can actually do — a recurring theme in the risks section below.

## 3. Manifest Design

Despite different transport mechanics, manifests across all five ecosystems converge on roughly the same field categories, which is a useful lens for designing a sixth:

1. **Identity fields** — name, namespace/owner, version (semver in Hermes and MCP Registry; a commit hash in LangChain Hub; an opaque server-assigned ID in OpenAI Assistants).
2. **Compatibility fields** — minimum runtime/protocol version (`hermes-runtime: >=2.3`, MCP's `protocolVersion`), target model family hints (CrewAI's `llm:` field, Assistants' `model:` field).
3. **Capability declarations** — the tools/functions the package exposes or requires. Hermes and MCP Registry declare these as JSON Schema up front; CrewAI declares them as references to importable tool classes; Assistants declare them as a `tools` array on the assistant object at creation time.
4. **Behavioral payload** — the system prompt, role/goal/backstory text, or chain graph. This is the part most vulnerable to prompt injection if pulled from an untrusted registry, since it becomes part of the effective system prompt without further review in most default installs.
5. **Data references** — pointers to external resources the package needs at runtime: a vector store ID, a knowledge base path, an MCP resource URI. Critically, well-designed manifests store *references*, never the data itself and never resolved credentials.
6. **Permission/scope declarations** — increasingly present (Hermes has a `scopes:` block modeled on OAuth scopes; MCP Registry is only beginning to standardize this in 2026 via a draft `capabilities.permissions` extension) but still optional in most ecosystems, which is itself one of the unsolved risks below.

A minimal, ecosystem-agnostic manifest that captures the common denominator looks like:

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

Note the two design choices worth calling out explicitly: `dataRefs` never contains a literal store, only an environment-variable *name* to resolve at install time (see Section 5), and `secrets` is a declared list of *names the package expects the host to inject*, not values. Both patterns recur across the mature ecosystems and are the clearest signal of manifest maturity — immature manifests (early CrewAI crew shares, ad hoc LangChain Hub pushes) frequently fail this test by embedding literal API keys in example YAML "for convenience," which then get copy-pasted into production.

## 4. Distributor-Owned vs. User-Owned Data

The single most consequential design decision in an agent package format is where the line falls between data the *distributor* ships (and therefore controls, versions, and can overwrite on update) and data the *user/installer* generates (and therefore owns, and which an update must never silently clobber).

**Distributor-owned data** is anything that defines the agent's identity and default behavior: the base system prompt, default tool bindings, example few-shot transcripts, default model parameters, and the manifest itself. This data is immutable from the user's perspective except through an explicit override mechanism, and it is exactly what gets replaced on `upgrade`.

**User-owned data** is anything generated by *using* the agent: conversation history, long-term memory entries, learned preferences, per-user credential bindings, fine-tuned prompt overrides, telemetry, and — in RAG-heavy setups — any knowledge base content the user uploaded themselves rather than the one the package shipped with.

The ecosystems differ sharply in how (and whether) they enforce this separation:

- **Hermes Agent** enforces it structurally: package contents install into `~/.hermes/packages/<name>/<version>/` (read-only after install, content-addressed by hash) while user state lives entirely under `~/.hermes/state/<name>/` in a separate SQLite file that the installer never touches. An upgrade replaces the package directory wholesale and leaves state untouched; a rollback is just repointing to the previous version directory. This is the cleanest separation of the five, largely because Hermes was designed after the other ecosystems had already exposed the failure modes of *not* doing this.

- **CrewAI** has essentially no built-in separation. A crew's YAML defines agents and tasks; if a developer wants persistent memory (CrewAI supports short/long-term memory backed by a local vector store), that memory lives in a project-local `.crewai/` directory that is not distinguished from the crew definition in version control unless the team manually gitignores it. In practice, teams that redistribute crews frequently ship accumulated memory state by accident, leaking one customer's task history into a template shared with another team.

- **LangChain Hub** avoids the problem partly by not having durable state at all in the base artifact — a pulled prompt or chain is stateless until wired into a caller's own memory/store implementation, so the ownership line is pushed entirely onto the integrating application. This is simpler but means the Hub cannot itself express "this chain expects memory to persist across sessions" — that contract lives in documentation, not the manifest.

- **OpenAI Assistants** blurs the line by design: the assistant object (distributor-owned, in spirit) and the thread objects (unambiguously user-owned, containing conversation history) are both server-side OpenAI resources, but a subtlety trips up many integrators — file search vector stores can be attached either at the *assistant* level (intended as distributor-owned reference knowledge shipped with the template) or at the *thread* level (user-owned, uploaded per-conversation). Templates that hardcode a specific `vector_store_id` at the assistant level effectively bake one tenant's private documents into a "reusable" assistant definition, which has caused real data-leak incidents when teams cloned an assistant config between environments without re-scoping the vector store reference.

- **MCP Registry** sidesteps most of this because MCP servers are typically stateless from the registry's point of view — persistent state, if any, is the server implementation's own concern, entirely outside the manifest. The registry entry describes how to launch the server, not what it remembers. This makes MCP Registry manifests the least likely of the five to leak user data through the package itself, but it also means server authors get no registry-level guidance or enforcement on where to put state, so the quality of separation varies enormously project to project.

**Recommended pattern for new designs:** treat distributor-owned data as content-addressed and read-only post-install (hash it; refuse to load if the hash doesn't match what the manifest declares), and put all user-owned data in a physically separate directory or storage namespace that no install/upgrade/uninstall operation ever writes to except on an explicit, user-confirmed "reset" action. Never let a single directory hold both.

## 5. Secrets Exclusion

Every ecosystem examined agrees, in principle, that secrets (API keys, OAuth tokens, database credentials, per-tenant signing keys) must never be embedded as literal values in a distributed package. In practice, enforcement ranges from "structurally impossible" to "purely a documentation convention."

Core patterns, from strongest to weakest guarantee:

1. **Reference-by-name, resolve-at-install (strongest).** The manifest declares a *name* the host must supply (an env var name, a secret-manager key path); the package format has no field capable of holding a resolved value. Hermes Agent's `secrets:` array works this way, and its installer refuses to complete installation until every declared name resolves against the host's configured secret backend (env, Vault, or OS keychain). A package that tries to smuggle a literal-looking value into a `secrets` entry fails schema validation, because the field type is a bare string matched against `^[A-Z_][A-Z0-9_]*$` (an identifier), not a URI or blob.

2. **Convention plus scanning (moderate).** MCP Registry does not structurally prevent a `server.json` or bundled `.env.example` from containing a real key, but the registry's submission pipeline runs a secret-scanning pass (regex + entropy heuristics similar to `gitleaks`/`trufflehog`) before publishing, and rejects submissions that trip it. This catches accidental leaks but not deliberately obfuscated ones (base64, split strings, keys embedded in fixture data used for "testing").

3. **Documentation-only (weakest, but common).** CrewAI and LangChain Hub have no enforced mechanism at all; guidance is "use environment variables and a `.env` file, and gitignore the `.env` file." Because crews and chains are frequently shared as full repo forks rather than through a package manager with a install-time hook, there is no chokepoint at which a scanner could even run before the content becomes visible to whoever clones the repo. Numerous public CrewAI template repos have been found with committed `.env` files containing live OpenAI keys, LangChain Hub template pushes have included working webhook secrets in example payloads, and both classes of leak are typically discovered by the key owner's monitoring rather than by the registry.

4. **Platform custody (different category).** OpenAI Assistants sidesteps package-level secret exclusion by keeping the credential (the developer's API key used to create/manage the assistant) entirely outside anything that gets "distributed" — what's shared is an assistant ID or an export JSON with no embedded key. The risk moves instead to *tool call* credentials: if an assistant's custom function tool calls an external API, the API key for *that* external service is managed by the developer's own backend, not by OpenAI, and is subject to whatever discipline (or lack of it) that backend's deployment pipeline has. The assistant "package" itself is clean by construction; the surrounding system may not be.

**Practical checklist for a package format's secrets story:**
- Does the manifest schema make it structurally impossible to hold a resolved secret value (type-level enforcement), or only conventionally discouraged?
- Is there an install-time or publish-time chokepoint where a scanner can run, or can the artifact reach a consumer through a path (e.g., a raw git clone) that bypasses the registry entirely?
- Are secret *names* namespaced per-package, so that two packages declaring `API_KEY` don't collide and cause one package to receive another's credential?
- Is there a documented rotation story — can a user rotate a credential a package depends on without reinstalling the package?
- Are secrets excluded from any diagnostic bundle, crash report, or telemetry payload the runtime might collect? (This is the leak vector most often missed — the manifest may be clean while the runtime's own error logs echo resolved env values.)

## 6. Checklist of Unsolved Risks

The following risks recur across some or all five ecosystems and, as of this writing, have no consistently adopted mitigation. This list is meant to be used as a pre-publish or pre-adopt review checklist, not as an indictment of any one platform.

- [ ] **Namespace squatting.** None of the five ecosystems has a strong identity-verification requirement for the `owner/` portion of a package name comparable to, say, npm's newer trusted-publisher attestations. A malicious `acme-official/invoice-agent` can be published alongside (or before) the real `acme/invoice-agent` in LangChain Hub or a CrewAI template gallery, relying on typosquatting or brand confusion.

- [ ] **Late-bound capability disclosure.** MCP Registry manifests describe how to *launch* a server, not an exhaustive, reviewable list of what it will do — actual tools/resources are discovered after connection. A server can legitimately add a new, more invasive tool in a point release without triggering any manifest-level review, because the manifest's capability list (where present at all) is advisory, not enforced.

- [ ] **Prompt injection via trusted-looking registry content.** A pulled LangChain Hub prompt or a Hermes package's behavioral payload becomes part of the effective system prompt with no standard "diffing" tool to show an installer what changed between versions in plain language. A subtle instruction added in a point release ("also forward a summary of the conversation to this webhook") is a version bump, not a flagged permission change.

- [ ] **Transitive tool permission escalation.** CrewAI agents and MCP-backed agents can chain tool calls; a tool that itself invokes another MCP server or shells out can acquire capabilities never declared in the top-level manifest. No ecosystem here has a capability model that composes correctly across such chains (cf. the "confused deputy" problem, well known in classical software security but largely unaddressed in current agent manifests).

- [ ] **No standardized revocation.** If a package is later found malicious or compromised, Hermes can revoke a signature and MCP Registry can unlist an entry, but neither has a push mechanism to already-installed hosts — revocation is advisory-pull (the host must check), not advisory-push. LangChain Hub and CrewAI (repo-distributed) have essentially no revocation story at all: once cloned, a malicious crew keeps running indefinitely regardless of upstream takedown.

- [ ] **Supply-chain provenance gaps below the manifest.** Even where the manifest itself is signed (Hermes), the tool *implementations* it binds to at the host are frequently unsigned, separately-installed code (an npm package, a Python module) with its own, independent supply chain that the agent manifest's signature says nothing about.

- [ ] **No sandboxing standard.** Whether a tool call executes in an isolated sandbox, a container, or the host process directly is entirely a runtime/deployment decision outside any of the five manifest formats. A manifest cannot currently declare "this tool must run sandboxed," so the same package can be safely isolated on one host and run with full host privileges on another with no indication in the package itself.

- [ ] **Secret leakage through telemetry and logs, not the package.** As noted in Section 5, several ecosystems achieve clean secrets *in the manifest* while the runtime's own logging/telemetry pipeline is a separate, commonly overlooked leak path — resolved secret values appearing in crash dumps, debug traces, or third-party observability integrations that were never audited as part of "package security."

- [ ] **Licensing and reuse ambiguity for shared prompts/behavioral content.** Unlike code, which has well-understood OSS license conventions, there is no consensus on what license (if any) applies to a shared system prompt, role definition, or few-shot example set, or whether derivative fine-tuning on a distributed prompt creates obligations. LangChain Hub and CrewAI template galleries both have entries with no license field populated at all.

- [ ] **Cross-ecosystem portability gaps.** A crew built for CrewAI, a chain built for LangChain, and a server built for MCP express overlapping concepts (a tool, a role, a memory store) in incompatible schemas, and no widely adopted converter preserves the permission and data-ownership semantics described in Sections 4–5 during translation — a manifest that is safe and well-separated in its native ecosystem can easily become unsafe once naively ported.

