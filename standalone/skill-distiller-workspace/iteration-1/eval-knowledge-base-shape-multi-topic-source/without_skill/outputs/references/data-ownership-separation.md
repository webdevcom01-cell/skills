# Distributor-Owned vs. User-Owned Data

The recurring bug class across every agent packaging ecosystem is
conflating data the *publisher* is responsible for with data that only
makes sense in the *installer's* environment. Use the taxonomy below when
deciding where a field belongs, and the per-ecosystem leak list when
auditing an existing package.

## The taxonomy

**Distributor-owned — travels in/with the package, identical for every
installer:**

- Identity: name, namespace/publisher ID, version, changelog.
- Structural definition: prompt templates, task graphs, role/task
  descriptions, tool *interfaces* (names + schemas — not live credentials),
  the process graph (sequential/hierarchical), entrypoint code or bundle
  hash.
- Declared capability/permission requirements (what the agent *asks for*,
  as opposed to what it's actually granted at install time).
- Signature / provenance metadata.

**User-owned — must never be baked into the package; created at
install/run time, different for every installer:**

- Credentials and API keys for any tool the agent will call.
- Account-scoped resource IDs (OpenAI file IDs, vector store IDs, a
  specific Slack workspace ID, a specific database connection string).
- Local file paths, working directory, OS-specific settings.
- Runtime state: conversation history, memory/vector-store *contents* (the
  schema may be distributor-owned; the data inside it is not),
  usage/billing counters, rate-limit state.
- User preferences that override defaults (verbosity, temperature, a
  personal system-prompt suffix).

**The one-line test:** if the value would be identical no matter who
installed the package, it's distributor-owned and belongs in the manifest
or bundle. If it would necessarily differ per installer, it's user-owned
and must be supplied at install/run time — never shipped as a literal
value.

## Where each ecosystem draws the line, and where it actually leaks

- **Hermes** keeps the line clean at the manifest schema level
  (capabilities are declared, not embedded), but the `permissions.prompt`
  free-text field is sometimes abused by publishers to embed a real API key
  "for testing, remove before prod." A lint rule catches obvious key-shaped
  strings via regex but not creatively encoded ones (base64, split across
  two fields, etc.).
- **LangChain Hub** has no user-owned/distributor-owned distinction in the
  manifest schema at all. A pulled chain frequently has `.env`-style values
  hardcoded into a prompt template's few-shot examples by an author who was
  testing locally, because nothing in the tooling flags "this looks like a
  value that shouldn't be here."
- **CrewAI**'s `crew.yaml` is clean in principle (tools referenced by class
  name only), but `backstory` fields — meant to be flavor text for the LLM
  persona — are a common dumping ground for real internal context (a
  company name, a real project deadline, an internal ticket ID) the author
  didn't intend to publish, precisely because the field is untyped prose
  with no validation.
- **OpenAI Assistants** mixes the two by necessity: `tool_resources` file
  IDs are account-scoped (user-owned) but sit in the same JSON object as
  `instructions` (distributor-owned) with no schema-level marker
  distinguishing them. Import tools have to guess which fields are portable
  by field name alone.
- **MCP Registry** is the cleanest of the five here: `server.json` never
  contains credentials by construction, because the server process reads
  its own credentials from its host environment at runtime — the registry
  entry only ever describes how to *install* the server, never how to
  *authenticate* it. The trade-off: credential UX is entirely offloaded to
  whatever MCP client the user runs, with no standard for how that client
  should prompt for or store them.

## Practical checklist when reviewing a package for this issue

1. For every field in the manifest, ask the one-line test above.
2. Pay special attention to **untyped free-text fields** (`backstory`,
   `permissions.prompt`, README prose, `metadata` blobs) — these are where
   real user-owned data leaks into distributor-owned packages in practice,
   because validation tooling generally only checks typed/structured
   fields.
3. Check whether any field holds an **account-scoped ID** (file ID, vector
   store ID, workspace ID, connection string) rather than a portable
   reference — these look like configuration but behave like user-owned
   data, and don't survive being installed somewhere else.
4. If the package was built by exporting from a working local environment
   (a common CrewAI/LangChain pattern), check for anything that reflects
   *that specific environment* — local file paths, real ingested documents
   sitting alongside the schema that's supposed to be the only distributed
   part (see risk #8 in `unsolved-risks-checklist.md`).
