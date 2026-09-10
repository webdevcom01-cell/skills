# Unsolved risks checklist — agent packaging and distribution

Load this when auditing a new or existing agent/tool distribution design for
gaps, or when someone asks "what could still go wrong" after the manifest,
data-separation, and secrets design are already settled.

These seven are recorded in the source as **open items across all five
ecosystems surveyed (Hermes Agent, LangChain Hub, CrewAI, OpenAI Assistants,
MCP Registry) — not a ranked priority list.** Which one matters most depends
entirely on deployment context: a single-user local install has a very
different risk profile than a registry entry pulled by unknown third
parties. Don't present these as ordered by severity; the source explicitly
declines to rank them.

1. **Typosquatting / name confusion.** Namespacing with verified ownership
   (Hermes' reverse-DNS `id`, MCP Registry's DNS-verified reverse-domain
   `name`) reduces impersonation *within* a namespace but does not prevent a
   visually similar name in a *different*, unverified namespace
   (`com.acme.support-bot` vs. `com.acme-.support-bot`). LangChain Hub's
   unverified `owner/repo-name` handle has the same weakness with no
   namespace-ownership check at all. CrewAI, distributed over PyPI,
   inherits whatever typosquatting exposure PyPI itself already carries.

2. **No cross-ecosystem provenance/signing standard.** None of the five
   cryptographically signs the published artifact itself in a way
   verifiable independent of trusting the registry's own infrastructure —
   namespace ownership (which several do have) is a different guarantee
   from artifact-integrity signing (which none do). A compromised registry
   backend could serve a modified artifact under an unchanged version
   number in four of the five models. OpenAI Assistants is the stated
   exception: there's no separate artifact to substitute, since the account
   itself is the trust boundary.

3. **Update-time silent behavior change.** Mutable/floating references exist
   in more than one ecosystem — LangChain Hub's `:latest` tag, a container
   image tag referenced from `server.json`, a crew's floating
   `requirements.txt` pin — so an agent can change behavior with no action
   by whoever configured it. Nothing common across the five forces pinning,
   and a floating reference is the default or at least the easy path in
   every one of them.

4. **No standard revocation/yank signal.** None of the five has a
   first-class "yank this version and notify everyone who pulled it"
   mechanism with guaranteed delivery. At best (Hermes, MCP Registry) a
   publisher can push a new version and hide the old one from fresh listings
   — but an existing install that doesn't proactively check for updates
   never learns anything changed.

5. **Secret-shaped values outside the fields designed to catch them.** Every
   scanning mechanism surveyed (Hermes, MCP Registry) only looks at the
   manifest's defined fields — never free-text description/documentation
   fields, and never inside a *referenced* artifact when the manifest only
   points at one instead of containing it. See `secrets-exclusion.md` for
   the full breakdown; listed here because it's also a standing,
   cross-ecosystem gap in its own right.

6. **Dependency/transitive trust is unmodeled almost everywhere.** CrewAI
   inherits whatever a crew's Python dependencies pull in transitively, with
   no agent-specific reasoning layer over it at all. The MCP Registry
   indexes the top-level server but says nothing about that server's own
   package-manager dependency tree. Hermes' `skills` field is the closest
   thing to a dependency declaration among the five, and even that is a
   flat list used only for the registry's own impact-analysis tooling — not
   an enforced or verified dependency graph.

7. **No shared deprecation/pruning convention.** There is no cross-ecosystem
   norm for what happens to a package whose publisher account is deleted,
   abandoned, or whose namespace-ownership proof (a DNS record, a GitHub
   org) lapses. Each ecosystem surveyed handles this differently, or not at
   all, and a client has no standard way to detect that a package's
   provenance claim has gone stale after the fact.

## Using this checklist

Run it against a specific distribution design by asking, per item: does this
design mitigate it structurally (the platform enforces it), by convention
only (works if authors follow the pattern, nothing enforces it), or not at
all? The source's own survey shows every one of the five ecosystems lands on
a different mix of these three answers across the seven items — there is no
ecosystem surveyed that fully solves all seven, so "not fully solved" on
several items is not, by itself, a sign of a bad design; it's the current
baseline across the field.
