# Distributor-owned vs. user-owned data separation

Load this when designing update/install semantics for a distributed agent —
specifically, how to keep what the publisher ships separate from what the
installing user customizes or accumulates at runtime, so an update doesn't
destroy local state.

## The core lesson: never let update-managed and user-managed data share a directory or object

Hermes Agent's packaging model is built around a hard filesystem split:
distributor-owned bundle content lives under
`~/.hermes/agents/<id>/<version>/`, wholesale-deleted and recreated on every
update; user-owned state (conversation history, per-user config overrides,
anything the agent writes at runtime) lives under a separate tree,
`~/.hermes/state/<id>/`, which the update process never touches, and which a
manifest cannot declare files into — the only path into it is Hermes' own
state API, which enforces the path prefix.

This split is described in the source as a fix arrived at only after an
earlier failure mode: pre-split Hermes agents shipped bundled "default
config" files that users were expected to hand-edit in place, and every one
of those agents corrupted user customization on the next update, because the
update process had no way to distinguish a hand-edited file from a
shipped-as-is one. Detecting the edit after the fact (diffing against a
shipped-file checksum) was tried and abandoned — unreliable across
line-ending and formatting-only changes. **The fix that held was structural,
not detective: don't let the two kinds of data share a directory at all**,
rather than trying to tell them apart once they already do.

## Two ways ecosystems achieve the separation

**Platform-enforced structural separation** — the platform itself makes it
impossible for update-managed and user-managed data to collide:
- Hermes: two directory trees under different filesystem paths, one behind
  an API write boundary.
- OpenAI Assistants: two distinct object types. The `Assistant` object
  (`model`, `instructions`, `tools`) is replaced wholesale on
  `assistants.update()` — same wholesale-replace failure mode Hermes solved
  structurally, except here there's no second copy to protect, because
  there generally isn't a customization step distinct from editing the
  config itself. `Thread`/`Message` objects are a wholly separate type
  explicitly designed to outlive assistant updates — updating an
  assistant's instructions or tools does not touch any existing thread's
  message history. This is the one place in the OpenAI Assistants model
  that enforces a separation comparable to Hermes' two-directory split; it's
  just expressed as two object types in one API rather than two directories
  on a filesystem.

**Convention-only separation** — nothing in the tooling enforces it; it
works only if the project author follows the pattern:
- CrewAI: the installed package (site-packages, or a pinned git/path
  dependency) is distributor-owned and replaced wholesale on
  `pip install --upgrade`. Anything `crew.py` reads from outside the
  package — a local `.env`, a config directory pointed at by an environment
  variable, a local override YAML merged over the packaged `agents.yaml` at
  construction time — is user-owned only by the convention individual
  project authors choose to adopt. CrewAI's own tooling neither provides
  nor requires any of this.
- MCP Registry: the calling host supplies a server's runtime configuration
  (API endpoints, working directories, feature flags) via environment
  variables or CLI arguments at launch, not via any file inside the
  installed package — but nothing in the Registry model prevents a poorly
  built server from writing its own config into its own install directory
  anyway.

## The alternative that sidesteps the problem instead of solving it

LangChain Hub doesn't need Hermes' two-tree split because its distribution
model has no "installed copy that gets overwritten" in the first place:
content is pulled by exact hash or by an explicitly re-resolved mutable tag,
and the puller's local cache is keyed by hash — pulling a new version adds a
new cache entry rather than mutating an old one.

This avoids the overwrite failure mode entirely, but at a real cost the
source is explicit about: **nothing in the Hub's model represents "the
user's local customization of what they pulled" as a first-class concept
at all.** If a user pulls a prompt and edits it locally, that edit lives
entirely in the calling application's own state (an in-memory object, or
whatever the application itself persists) — the Hub has no visibility into
the edit and no mechanism to merge a later upstream update with it. Treat
this as a genuine trade-off, not a strictly worse or better answer than
Hermes': content-addressed, never-mutate-on-pull distribution removes the
need to solve the merge/overwrite problem, but only by giving up on
representing "installed + locally customized" as a state the system
understands at all.

## Applying this when designing something new

1. Decide up front whether your distribution model will ever let a user
   hand-edit something the publisher also updates. If yes, you need either
   the structural split (separate directories/objects, no shared write
   surface) or the content-addressed sidestep (never mutate in place —
   always add a new version alongside the old). Detecting edits after the
   fact via checksums is the option the source explicitly reports failing.
2. If you delegate installation to an existing package ecosystem (CrewAI →
   pip, MCP Registry → npm/PyPI/OCI for the referenced artifact), you
   inherit that ecosystem's separation properties — or lack of them —
   rather than getting to define your own. Say so explicitly rather than
   implying your layer adds a guarantee it doesn't.
