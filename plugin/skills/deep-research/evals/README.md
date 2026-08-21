# Evals for deep-research

Six self-contained cases in `evals.json`, following the same schema and quality bar as
`skill-creator-pro/evals/evals.json` (5th phase of the library-wide eval effort, after
28 skills across 4 prior phases). Every case is grounded in an explicit rule, threshold,
or ordering requirement quoted or closely paraphrased from `SKILL.md` — none are
invented — and each is answerable by a fresh agent given only the SKILL.md text and the
prompt itself: no reference to prior turns, disk paths, or other external state.

## What's covered

| # | Rule under test | Where in SKILL.md |
|---|---|---|
| 1 | Step 1 order: run one broad exploratory search *before* asking a clarifying question; ask at most one question, only if still genuinely ambiguous; 3-6 distinct-angle queries | "Step 1: Scope, Then Clarify If Needed" |
| 2 | Tier 1 vs Tier 2 source distinction; Tier 2 labeled as corroboration, never equivalent to Tier 1; 5-10 sources spanning more than one or two publishers/domains | "Source Tiers" (Context & Preferences) + "Step 2: Information Gathering & Filtering" |
| 3 | Unreachable-source protocol: try an alternate query or cached/snippet version first; if still unreachable, say so explicitly rather than silently dropping the source | "Step 2: Information Gathering & Filtering" |
| 4 | Both Step 3 verification checks: a quote must actually appear in the fetched source text (not just be implied by a snippet); a named attribution must match the exact name adjacent to the quote — a correct fact with the wrong name is still a citation failure | "Step 3: Synthesis & Theme Extraction" |
| 5 | ~800-1500 word target for the Detailed Breakdown; when trimming an oversized draft, never cut source citations or the summary table — trim discussion text instead, or say so explicitly | "Step 4: Format and Polish" |
| 6 | Self-Improvement Loop only triggers on friction or a user correction/rejection, and is skipped silently on a clean run; it cannot save changes back to the on-disk skill file, only prepare a revised SKILL.md and offer to deliver it | "🔄 Self-Improvement Loop" |

Each case targets a rule that's easy to get wrong in practice — e.g., asking a
clarifying question before searching, treating Reuters/Bloomberg/Gartner coverage as
equal to a primary filing, silently dropping a paywalled source, accepting a quote on
snippet evidence alone, fixing a wrong quote but not a wrong name, cutting a source
citation to hit a word count, or claiming to have saved a skill update directly to disk.

## How to run

Feed each case's `prompt` to a fresh agent instance that has loaded `deep-research`'s
`SKILL.md` and nothing else about this task (no prior conversation, no filesystem
state). Compare the agent's response and any actions it takes against that case's
`expectations`.

## How to interpret

- `expected_output` is a short prose description of the compliant outcome — a rubric
  anchor, not a literal string match.
- `expectations` are the individually checkable pass/fail bullets. A case passes only
  if all of its bullets hold; a single violated bullet (e.g., silently dropping an
  unreachable source, or cutting a source citation to save words) fails the case even
  if the rest of the response looks polished.
- Cases 1-5 test single-turn procedural compliance. Case 6 is two paired sub-scenarios
  (Run A / Run B) in one prompt — both halves must be handled correctly for the case to
  pass, since the point of the rule under test is the *contrast* between the skip and
  trigger conditions.
