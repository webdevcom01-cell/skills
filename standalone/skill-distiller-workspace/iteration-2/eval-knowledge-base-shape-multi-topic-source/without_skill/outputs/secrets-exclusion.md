# Secrets Exclusion in Agent Packages

Reference for: making sure a package about to be published (or a manifest format being designed) cannot carry a literal secret, and auditing an existing one.

## Why this is different from ordinary package hygiene

Every ecosystem examined agrees, in principle, that secrets (API keys, OAuth tokens, database credentials, per-tenant signing keys) must never be embedded as literal values in a distributed package. In practice, enforcement ranges from "structurally impossible" to "purely a documentation convention," and the gap between those two ends is the single best predictor of whether an ecosystem has had public leak incidents.

## Four-tier strength model, strongest to weakest

1. **Reference-by-name, resolve-at-install (strongest).** The manifest declares a *name* the host must supply (an env var name, a secret-manager key path); the package format has no field capable of holding a resolved value. Hermes Agent's `secrets:` array works this way — the installer refuses to complete installation until every declared name resolves against the host's configured secret backend (env, Vault, or OS keychain), and the field type is validated as a bare identifier (`^[A-Z_][A-Z0-9_]*$`), not a URI or blob, so a literal-looking value fails schema validation outright.

2. **Convention plus scanning (moderate).** MCP Registry does not structurally prevent a `server.json` or bundled `.env.example` from containing a real key, but the submission pipeline runs a secret-scanning pass (regex + entropy heuristics, similar in spirit to `gitleaks`/`trufflehog`) before publishing, rejecting submissions that trip it. Catches accidental leaks, not deliberately obfuscated ones (base64-encoded, split across strings, embedded in "test fixture" data).

3. **Documentation-only (weakest, but common).** CrewAI and LangChain Hub have no enforced mechanism at all; guidance is "use environment variables and a `.env` file, and gitignore it." Because crews and chains are frequently shared as full repo forks rather than through a package manager with an install-time hook, there is often no chokepoint at which any scanner could run before the content is visible to whoever clones the repo. Real-world pattern: public CrewAI template repos found with committed `.env` files containing live OpenAI keys; LangChain Hub template pushes with working webhook secrets left in example payloads. Both classes of leak are typically discovered by the key owner's own monitoring, not by the registry.

4. **Platform custody (a different category, not a ranking position).** OpenAI Assistants sidesteps package-level secrets entirely by keeping the developer's management credential outside anything "distributed" — what's shared is an assistant ID or export JSON with no embedded key. The risk moves instead to *tool-call* credentials: if an assistant's custom function tool calls an external API, that API's key is managed by the developer's own backend, subject to whatever discipline that backend's deployment pipeline has. The assistant package itself is clean by construction; the surrounding system may not be — so "the platform holds the secret" is not the same claim as "the secret cannot leak."

## Pre-publish checklist

- [ ] Does the manifest schema make it **structurally impossible** to hold a resolved secret value (type-level enforcement, e.g. identifier-only fields), or is it only conventionally discouraged?
- [ ] Is there an **install-time or publish-time chokepoint** where a scanner can run, or can the artifact reach a consumer through a path (a raw `git clone`, a repo fork) that bypasses the registry — and any scanning it does — entirely?
- [ ] Are secret **names namespaced per-package**, so two packages both declaring e.g. `API_KEY` don't collide and cause one package to receive another's credential at resolution time?
- [ ] Is there a documented **rotation story** — can a user rotate a credential a package depends on without reinstalling the package?
- [ ] Are secrets excluded from **any diagnostic bundle, crash report, or telemetry payload** the runtime might collect? This is the leak vector most often missed: the manifest can be clean while the runtime's own error logs or observability integration echo resolved env values at debug level.
- [ ] If the package bundles example config or a `.env.example`, does it contain only placeholder text (`YOUR_KEY_HERE`), not a working-looking value, a test key that happens to be a real key, or a value copied from a live account "just for the demo"?

## Rule of thumb

If a field's *type* would technically accept a live secret value and validation doesn't reject it, assume it will eventually contain one — convention-only guidance ("please don't put real keys here") has repeatedly failed across every ecosystem examined that relies on it alone.
