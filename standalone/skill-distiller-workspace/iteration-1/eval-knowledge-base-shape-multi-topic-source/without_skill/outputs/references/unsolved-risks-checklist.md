# Unsolved Distribution Risks — Checklist

None of the five ecosystems surveyed (Hermes Agent, LangChain Hub, CrewAI,
OpenAI Assistants, MCP Registry) has fully solved the risks below. Use this
checklist when someone asks whether a packaging design is "safe" or
"production-ready" — the honest answer names which of these remain residual
risk rather than implying they're solved by a good manifest alone.

1. **No cross-ecosystem capability model.** A capability declared in a
   Hermes manifest, a CrewAI tool binding, and an MCP `server.json` mean
   three different things with three different enforcement mechanisms (one
   signed and OS-enforced, one a Python import with no sandboxing, one
   entirely dependent on the MCP client's own policy). An agent assembled
   from parts across ecosystems has no single place to reason about "what
   can this actually do."

2. **Namespace squatting / typosquatting.** LangChain Hub and MCP Registry
   both use free-text or lightly-gated namespaces; neither has shipped a
   verified-publisher badge that's load-bearing (i.e., that a client
   actually checks before auto-installing). A malicious `acme-weathr`
   sitting next to a legitimate `acme-weather` is a live risk in both.

3. **Version pinning is advisory, not enforced, in three of five.** Hermes
   and MCP Registry support lockfile-style exact-version pinning.
   LangChain Hub and CrewAI (via pip) resolve at pull/install time against
   whatever is "latest" or matches a loose range, so a compromised or
   simply *changed* upstream package can silently alter behavior for every
   installer who didn't pin.

4. **Transitive tool permission escalation.** A CrewAI crew or LangChain
   chain that wires in a third-party tool inherits whatever that tool can
   do, with no re-declaration or re-consent step at the point the sub-tool
   is added. Permissions granted to the top-level package are implicitly
   extended to everything it pulls in, and no ecosystem here re-surfaces
   that expanded set to the installer for confirmation.

5. **No standard revocation / kill-switch.** If a published agent is later
   found to be malicious or badly broken, none of the five has a mechanism
   that reaches already-installed copies. At best (Hermes, MCP Registry)
   the registry can stop serving new installs of that version; already-
   deployed instances keep running until someone notices and manually
   removes them.

6. **Telemetry and privacy disclosure is inconsistent.** Whether a
   distributed agent phones home (usage analytics, crash reports,
   "check for updates" pings) is up to the publisher's own code in four of
   the five ecosystems (all but OpenAI Assistants, where all calls are
   already visible as API traffic to the account holder). None require a
   manifest-level declaration of outbound network behavior an installer
   could audit before running.

7. **Manifest fields lose meaning across export/import between
   ecosystems.** Community "convert my CrewAI crew to a LangChain agent" or
   "export my Assistant to a portable format" tools exist, but capability
   and permission metadata is exactly the part that doesn't survive
   translation — it's the least standardized field, so converters either
   drop it silently or map it to the loosest equivalent in the target
   ecosystem, which quietly widens the effective permission set.

8. **Vector store / knowledge base contents are sometimes bundled by
   accident.** Because "distributor-owned" (schema, chunking config) and
   "user-owned" (the actual ingested documents) live in the same on-disk
   structure in several agent frameworks, a publisher packaging a bundle
   from their working directory has, more than once, shipped their own
   ingested customer documents along with the agent that was supposed to
   process generic ones. Cross-reference: `data-ownership-separation.md`.

9. **No standard for expressing cost / rate-limit expectations.** None of
   the five manifest formats let a publisher declare "this agent will make
   roughly N model calls per run" or "expect a K% chance of invoking the
   web-search tool," which means installers have no package-level signal
   for expected spend before running something pulled from a registry.

## How to use this list in a review

- Don't present a package or manifest design as "secure" without checking
  it against each item — most of these apply regardless of how well the
  manifest itself is designed, because they're gaps in the surrounding
  ecosystem (registry policy, client behavior, tooling), not in any single
  file format.
- Where a risk is structural and unsolved industry-wide (items 1, 2, 5, 7
  in particular), say so plainly rather than implying a workaround fully
  closes it — a partial mitigation (e.g., pinning versions to blunt #3, or
  reference-only credentials to blunt secrets exposure) is still worth
  doing, but it doesn't retire the underlying risk.
