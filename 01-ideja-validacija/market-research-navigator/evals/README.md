# Evals for market-research-navigator

Phase 5 of the systematic eval-coverage effort (following the same pattern applied to
28 other skills across 4 prior phases). This is the first eval set for this skill.

## `evals.json` — 6 cases

Every case is a self-contained hypothetical scenario answerable from SKILL.md alone —
no reference to prior conversation, dates, or filesystem state. Each is grounded in an
explicit rule, table row, or threshold from SKILL.md (cited in `expected_output`), not
an invented scenario.

Coverage, one case per rule that is easy to get wrong in practice:

| # | Rule under test | SKILL.md anchor |
|---|---|---|
| 1 | Geographic-scope default: local competitors / "ovde" / "kod nas" → 🇷🇸 Regional, even when a Serbian city is named (not enough alone to pull to Combined) | "Default behavior if user doesn't specify" |
| 2 | Geographic-scope default: business idea + Serbia mentioned → 🌍+🇷🇸 Combined, even with no "ovde"/local-competitor phrasing | "Default behavior if user doesn't specify" |
| 3 | Quick Mode escalation trigger: a legal/regulatory red flag (lawsuit) surfaced mid-quick-check must not be compressed into one bullet — must say explicitly it changes the picture and recommend full analysis | "⚡ Quick Mode → Escalation Trigger" |
| 4 | Data Quality Indicators: conflicting sources must be marked 🔀 CONFLICTING and both shown, never silently resolved/averaged | "Response Guidelines → Data Quality Indicators" + "Always:" list |
| 5 | Sourcing integrity: a competitor's own-site claims are self-reported, distinct from independently verified data; never cite an AI-generated search summary as the source | "Privacy & Source Independence" + "Always:" list |
| 6 | "When NOT to Use": a company-financials-only question gets redirected to APR.gov.rs (Serbia) / SEC / Crunchbase instead of being answered directly | "When NOT to Use" |

Each case ships 3-5 expectations that are independently checkable against the response
text (no execution harness required — this skill has no scripts to run, unlike
`skill-creator-pro`). A grader (human or LLM) reads the agent's response to the prompt
and checks each expectation as met / not met.

### Why these six and not others

The task brief called out the rules in this skill most likely to be silently dropped
under normal-sounding pressure:

- The three geographic-scope defaults are easy to blur together, especially because the
  Serbian Trigger Phrases table separately says "Srbija"/"Balkan"/"region" → Regional/Combined,
  which could tempt a match on country name alone. Cases 1 and 2 each construct a prompt
  where a *tempting but wrong* trigger is present (a Serbian city in case 1, idea-language
  in case 2) alongside the *actually correct* signal, so the eval checks the more specific
  rule wins rather than a surface keyword match.
- The Quick Mode escalation trigger is the one most likely to get lost precisely because
  the user explicitly asked for brevity — case 3 puts the red flag (a lawsuit, one of the
  rule's own named examples) directly in the user's message so the check is self-contained
  without depending on live search results.
- Cases 4 and 5 both embed the conflicting/self-reported data directly in the prompt for
  the same reason: grading must not depend on what a live web search happens to return for
  a fictitious company on a given day.
- Case 6 tests the boundary of the skill's own stated scope, which is easy to blur because
  a financials question can look superficially like a market-research request.

## Running / interpreting

There is no automated runner bundled here (this skill, unlike `skill-creator-pro`, has no
`scripts/` to invoke). To use this set:

1. Run each `prompt` against a fresh agent that has the skill loaded, with no other
   context in the conversation.
2. Compare the response against that case's `expectations`, one by one — each bullet
   should be checkable as clearly met or clearly not met, without judgment calls.
3. A case passes only if all of its expectations are met. `expected_output` is a
   one-sentence description of the ideal answer's shape, citing the rule it exercises —
   use it to sanity-check the response before scoring the individual expectations.

Note that cases 3, 4, and 5 deliberately supply the "world state" (the lawsuit, the two
conflicting figures, the self-reported website claim) inside the prompt itself, rather
than relying on the agent's live web search to surface it. This keeps grading
deterministic and keeps every case self-contained per the eval-writing constraint — a
prompt that depends on what a real search happens to return on a given day is not a
reliable eval of the skill's *handling* of that situation.
