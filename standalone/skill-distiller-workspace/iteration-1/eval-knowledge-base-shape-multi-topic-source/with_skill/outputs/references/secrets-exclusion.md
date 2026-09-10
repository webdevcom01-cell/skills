# Keeping secrets out of the distributed package

Load this when deciding how a manifest/publish flow should handle
credentials — what the schema should (and shouldn't) hold, whether to scan,
and how strict that scan should be.

## The convergent pattern: no credential field, hard-block on anything that looks like one

Hermes Agent and the MCP Registry arrived at the same design independently:

- The manifest schema (`agent.json`, `server.json`) has **no field for
  credentials of any kind.**
- Publish-time validation actively scans the manifest for values that look
  like live secrets and **rejects the publish outright** — not a warning,
  a hard block with no override flag, when something matching is found.
- Hermes' scan specifically looks for high-entropy strings adjacent to keys
  named `key`/`token`/`secret`/`password`, and common provider key prefixes
  (e.g. `sk-`).

**Rationale stated in the source (Hermes' publishing docs):** a rejected
publish is recoverable — fix and republish. A leaked key baked into a
package that's already been pulled by users is not. This asymmetry — cheap
to be strict before publish, expensive to be lenient — is the reason both
ecosystems chose a hard block over a warning.

## The declare-name-not-value pattern

Instead of embedding a secret, the manifest names what the agent needs and
the value is supplied later, outside the artifact:

- **Hermes:** `agent.json` carries a `required_secrets` list — just a name
  and a human-readable description per entry (e.g. `{"name":
  "OPENAI_API_KEY", "description": "Used for the summarization step"}`).
  At install time, Hermes prompts the user for each named secret and stores
  it in the OS-native secret store (Keychain on macOS, Credential Manager
  on Windows, `libsecret` on Linux where available, a permissions-restricted
  file as fallback) — never inside the bundle-managed tree
  (`~/.hermes/agents/`) and never inside the user-state tree
  (`~/.hermes/state/`).
- **MCP Registry:** a server that needs a credential documents the required
  environment variable in the manifest's description/README-equivalent
  field; the *host application* prompts the user and injects the value as
  an environment variable into the server's process at launch — never
  persisted inside the installed package tree.

Both patterns share the same shape: **the manifest says what's needed, not
what the value is; the value enters the system at install/launch time
through a channel the manifest itself has no access to.**

## Where there is no gate at all — it's entirely on author discipline

Three of the five ecosystems surveyed have no publish-time secret check of
any kind:

- **LangChain Hub** — a pushed prompt/chain/graph object isn't expected to
  contain credentials (tool bindings reference tools by name, not by
  embedding auth), so the Hub built no scanning step. Nothing stops a user
  from pushing a chain with a hardcoded key baked into a prompt's example
  text.
- **CrewAI** — a crew is plain Python distributed like any other package;
  secret hygiene is standard `os.environ`/`.env`-file practice with no
  CrewAI-specific enforcement. The source calls out a recurring community
  pattern: crews built from tutorials often ship with a committed `.env`
  because the tutorial's quick-start has the user create one in the project
  root without mentioning `.gitignore`.
- **OpenAI Assistants** — structurally different from the other two: a
  function-calling tool definition only declares a JSON schema for
  arguments the model should request; actual execution — and any
  credential that requires — happens in the caller's own code entirely
  outside the API. There is structurally no field in the `Assistant` object
  where an execution credential could even be embedded. The one remaining
  leak surface is the free-text `instructions` string, if an author pastes
  a real key while drafting a prompt — nothing validates or scans that
  field's content.

## Known gaps, even where a scanner exists

- **Free-text fields are unscanned everywhere.** Every scanner surveyed
  (Hermes, MCP Registry) only looks at defined manifest fields. None looks
  inside free-text description/documentation/README-equivalent fields. A
  secret pasted into a description or a docstring passes uncaught in every
  case surveyed.
- **Referenced artifacts are invisible to the scan.** When a manifest only
  points at an artifact instead of containing it — MCP Registry's
  `packages` entries, CrewAI's PyPI dependency tree, LangChain Hub's
  tool-references-by-name — nothing in the manifest-level scan can see
  inside the referenced package's own source. That has to be caught, or
  not, by whatever the underlying package registry (npm/PyPI/OCI) does on
  its own, which varies and is out of the distributing ecosystem's control.
- **Hermes' entropy scan has a documented false negative:** a secret split
  across two concatenated string literals evades single-string entropy
  detection — this was observed during a registry audit as an obfuscation
  attempt. A multi-string-concatenation-aware scanner was tracked as an open
  issue but had not shipped as of the source's writing. Treat this as a
  specific, sourced limitation of entropy-based scanning generally, not
  something unique to Hermes' implementation.

## Applying this when designing something new

1. Prefer no-field-for-credentials-plus-hard-block-on-detection over a
   credential field with documentation telling authors not to fill it in —
   the two ecosystems that converged on this independently both treat a
   rejected publish as cheap and a leaked-and-already-pulled key as not.
2. If you scan, decide explicitly whether the scan covers free-text fields
   and referenced-but-not-hosted artifacts — the source found every real
   scanner surveyed skips both, which is worth being deliberate about
   rather than silently inheriting.
3. A warning-only scan is a materially weaker choice than a hard block,
   given the stated rationale above (recoverable vs. not) — don't default
   to "warn" without confirming that trade-off is actually acceptable for
   your artifact's blast radius.
