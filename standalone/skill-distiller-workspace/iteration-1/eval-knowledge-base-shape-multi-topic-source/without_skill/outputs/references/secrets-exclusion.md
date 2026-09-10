# Secrets Exclusion Patterns

Three real patterns for keeping credentials out of a published agent
package show up across the five ecosystems, with different reliability.
Use this when designing a publish pipeline, or when deciding whether a
proposed safeguard is a real mitigation or just self-attestation.

## Pattern A — Reference, don't embed

The manifest/config holds a *name* (`OPENAI_API_KEY`, `SLACK_BOT_TOKEN`)
that the runtime resolves from the local environment, OS keychain, or a
secrets manager at execution time — never the value itself.

- **Hermes**: `env:` prefix in tool-binding fields resolves against the
  host environment at launch.
- **MCP Registry**: servers declare an `environment_variables` array
  naming what they expect, never the values. Many `server.json` entries
  include this purely for UX, so the installing client can prompt the user
  for each one at install time.

This is the correct default pattern. Recommend it whenever you're
designing a new manifest field that touches credentials at all — the field
should hold a *name*, never accept a literal value.

## Pattern B — Pre-publish secret scanning

Because Pattern A is only a convention and not an enforced constraint,
every ecosystem with a hosted registry has bolted on scanning at publish
time. LangChain Hub runs a regex/entropy scanner (similar in spirit to
`gitleaks` / `trufflehog`) over any pushed YAML/README before accepting a
push, rejecting pushes that match a high-confidence secret pattern (AWS key
prefixes, PEM headers, JWT shapes).

Known limitation: false negatives are common for anything that doesn't
match a recognizable key format — a plain database password or an internal
bearer token with no distinctive prefix sails through untouched. Treat
pre-publish scanning as a floor, not a guarantee: it catches the class of
mistake where someone pastes a cloud-provider key, not the class where
someone pastes an internal secret with no recognizable shape.

## Pattern C — Scoped/short-lived credentials issued post-install, never published at all

OpenAI Assistants sidesteps the embedding problem almost entirely because
there is no client-distributed artifact — the API key used to call the
Assistants API never enters the assistant object; it's supplied by whoever
calls the API at call time.

The residual risk moves rather than disappears: it becomes "does the
community export/import tooling accidentally serialize a secret from the
exporter's local environment into the export blob." This has actually
happened — early AssistantHub-style tools dumped `os.environ` into export
metadata for troubleshooting during development, and that debug path
shipped to production. When reviewing an export/import tool built on top of
a server-hosted agent platform, check specifically for debug/diagnostic
code paths that serialize environment state, not just the "normal" export
fields.

## What does NOT work as a mitigation

- **Manifest-level self-attestation** — a field or style guide where the
  publisher promises "I did not hardcode secrets," with nothing that
  verifies the claim. CrewAI's community style guide recommends this; it
  catches nothing on its own and should not be presented as a control.
- **After-the-fact key rotation as the primary mitigation.** Rotating a
  key after a leak is discovered doesn't undo exposure to whoever already
  pulled the package before the rotation. None of the five ecosystems has
  an install-time freshness check that would even tell a publisher how many
  installers pulled a bad version before a fix shipped — so rotation
  closes the door going forward but gives no visibility into who already
  walked through it.

## Practical checklist before publishing a package

1. Confirm every credential-shaped field is a *name reference* (Pattern A),
   never a literal value.
2. Don't rely solely on regex/entropy scanning (Pattern B) to catch
   non-standard secret shapes — manually review free-text fields
   (`backstory`, `permissions.prompt`, README prose, few-shot examples)
   since these are exactly where scanners have the highest false-negative
   rate.
3. If the package was produced by an export tool, check the tool's own
   debug/diagnostic paths for accidental environment serialization — this
   is a known failure mode (Pattern C), not a hypothetical one.
4. Do not treat "we'll rotate the key if something leaks" as a substitute
   for not shipping it in the first place; rotation is cleanup, not
   prevention.
