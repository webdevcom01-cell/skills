# Distributor-owned vs. user-owned data separation

Load this when deciding whether a manifest field, resource pointer, or
piece of runtime data belongs to the publisher/registry or to the
installing user — or when auditing an existing manifest for where (or
whether) that line is drawn.

## The distinction, as a working test

Ask of any piece of data a package or its manifest touches: *does this stay
the same across every install of this exact version, or does it vary per
installer?* If it's the same everywhere, it's distributor-owned. If it
varies — or should vary — per install, it's user-owned. Treat "no clear
answer yet" as a design gap to close, not a detail to leave implicit; an
implicit answer tends to resolve itself toward whichever side was easiest
to implement, not whichever side is correct.

| Category | Distributor-owned | User-owned |
|---|---|---|
| Identity | package id, version, publisher signature | local install path, per-user API keys |
| Usage/telemetry | aggregate download or install counts | an individual's session/conversation logs |
| Content | shipped default prompts/templates | documents or fine-tune data the user supplies |
| Configuration | the schema and its defaults, as declared in the manifest | the resolved runtime values / environment variables |

## Two failure patterns worth checking for specifically

**Stale default resource pointers.** A field meant to hold a resource
reference (a vector-store ID, a file ID, a database connection) ships with
the *publisher's own* value still in place instead of a placeholder that
forces re-scoping. Every install that doesn't manually override it ends up
reading — or in the worst case, writing to — the publisher's own private
data rather than the installer's. This is a design defect in the field
itself (nothing forced a value to be supplied per-install), not a one-off
mistake by whoever published that particular package.

**Entangled usage records.** A registry stores its own per-user analytics
(who installed what, when) in the same record as the package's public
listing metadata. This makes two operations that should be independent —
"remove this package listing" and "honor one user's request to delete their
installation record" — collapse into a single operation, which complicates
any deletion or export request that was only ever supposed to touch one
side.

## How the five ecosystems handle this

Only **Hermes Agent** makes the split explicit in the manifest itself, via
a `data_scope` object with two lists — `distributor` and `user` — naming
what each side is expected to own. This is the only one of the five where
"who owns this field" is answerable by reading the schema rather than by
inference.

**LangChain Hub** doesn't formalize it. A bare prompt or chain object is
distributor-owned by construction — there's nothing user-specific in a
template — but the moment someone customizes and republishes a fork, there
is no documented rule for whose data the fork's differences actually
represent.

**CrewAI**'s `memory_backend` setting controls *where* user-side
conversation memory is stored, but that setting lives in the same
`crew.yaml` as the crew definition itself, with nothing distinguishing
"this configures the crew" from "this configures where a user's data will
live."

**OpenAI Assistants** is comparatively clean by construction: its
`tool_resources` field holds workspace-scoped resource IDs rather than
embedded content, so ownership is implicit in the ID's scope. The stale
default pointer failure pattern above is the documented exception to that
cleanliness — nothing stops an exported `assistant.json` from still
pointing at the original author's vector store.

**MCP Registry** has essentially no user-data concept at the manifest level
at all: an MCP server's own runtime storage is entirely outside anything
the registry's `server.json` describes, so this question simply doesn't
have an answer at the registry layer — it has to be answered by whatever
the server itself does at runtime.

## Checklist when adding a field to a manifest or config schema

- Does this field's value stay identical across every install of this
  version, or should it vary per installer? Pick one on purpose.
- If it's a resource pointer, does the schema force a per-install value, or
  does it silently accept the publisher's own default?
- If it's usage or telemetry data, is it stored separately enough from
  public package metadata that one can be modified or deleted without
  touching the other?
- Would this ecosystem's own answer to "who owns this" survive being
  written down explicitly, the way Hermes's `data_scope` does — or is it
  currently just an assumption nobody has had to defend yet?
