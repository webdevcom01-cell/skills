# Transcript — Distilling a Skill from a Synthesized Incident Thread (without_skill)

## Task
Synthesize a raw Slack thread about a production incident (two engineers,
referencing #4821, PR #5012, issue 6034, PR#7001, #7002, #7003) that
concludes cache invalidation must happen before a shared-state write, not
after, to avoid stale reads under concurrent load — then distill a skill
from it, using judgment about how much incident-specific detail to keep.
No skill or special instructions were loaded for this task; it was done
with general engineering judgment.

## Steps taken

1. **Created the output directory structure** with `mkdir -p`, under
   `.../without_skill/outputs/cache-invalidation-ordering/`.

2. **Synthesized the raw Slack transcript** (`outputs/raw-transcript.md`):
   a two-person back-and-forth (Dana Okafor, on-call SRE; Theo Marsh,
   service owner) in a fictional `#incident-4821` channel. Built a concrete,
   internally consistent incident around an entitlements/plan-upgrade
   service backed by Postgres + a read replica + Redis cache-aside reads.
   Gave each required reference a distinct, natural role in the story so
   none of them feel bolted on:
   - `#4821` — the customer-facing support ticket (symptom: upgraded but
     still capped).
   - `PR #5012` — the earlier change that introduced the regression
     (moved the entitlement write to an async job with a write-then-
     invalidate cache order).
   - `issue 6034` — the root-cause/postmortem tracking issue.
   - `PR#7001` — the fix (invalidate-before-write + short write lock).
   - `#7002` — the companion concurrency regression test.
   - `#7003` — rollout of the same fix to two other services sharing the
     buggy cache-aside helper.
   Added an explicit note at the top of the file stating the transcript is
   fabricated for this exercise, per the task's instruction to disclose
   that.

3. **Wrote `outputs/cache-invalidation-ordering/SKILL.md`**, the distilled
   skill: YAML frontmatter with a `name` and a trigger-oriented
   `description`, then a body organized as (a) the one-line rule, (b) why
   the ordering matters (the race-condition mechanics, generalized beyond
   the specific incident), (c) an explicit caveat that reordering alone is
   necessary but not sufficient, with three concrete mitigations (lock/
   placeholder, versioning, double-delete), (d) code-review detection
   heuristics, (e) a bad/good TypeScript pseudocode pair, and (f) a short
   "case reference" footnote citing the six tickets/PRs as provenance
   without leaning on the incident's specifics as the primary content.

4. **Wrote `outputs/cache-invalidation-ordering/checklist.md`**, a
   supporting PR-review checklist (ordering, race window, testing, blast
   radius) plus a minimal concurrency-test sketch, kept separate from
   SKILL.md so the core skill file stays scannable.

5. **Measured output sizes** with `wc -c` on each file as it was written
   (raw transcript: 5891 chars; SKILL.md: 6209 chars; checklist.md: 2878
   chars) to fill in `metrics.json` accurately rather than estimating.

6. **Wrote `outputs/metrics.json`** matching the required schema:
   `output_chars` = SKILL.md + checklist.md (9087, the produced skill
   artifact); `transcript_chars` = the raw synthesized transcript alone
   (5891). All file operations were done via `Bash` heredocs (per the
   session's active instruction to prefer Bash over dedicated file tools),
   so `tool_calls` is all-Bash: 6 calls, 0 errors.

7. **Wrote this file** (`transcript.md`), documenting the process and the
   final response given to the user.

## Design decisions / judgment calls

- **How much incident detail to keep in the skill:** kept the general
  rule, the mechanism, and the caveat about insufficiency of reordering
  alone as the primary content (this is what's reusable across incidents
  and codebases); compressed the specific incident down to a four-sentence
  "case reference" at the end of SKILL.md with the ticket numbers as
  provenance, rather than retelling the story. The PR-review checklist and
  test sketch were split into a second file so SKILL.md doesn't turn into
  a wall of process detail.
- **Technical grounding:** the transcript's engineers explicitly reason
  through *why* invalidate-before-write is the fix (closes the "write's
  own invalidation loses the race to a read the write triggered" failure
  mode) and explicitly caveat that ordering alone isn't a full fix — this
  matches real caching literature (naive reordering doesn't fully solve
  the classic cache-aside race) and made the skill's "necessary, not
  sufficient" section honest rather than a step overclaiming a silver
  bullet.
- **Reference placement:** each of the six required references was given
  a distinct narrative function (symptom ticket, regression-introducing
  PR, root-cause issue, fix PR, test PR, rollout PR) so they read as
  organic parts of an incident timeline rather than a checklist dropped
  into dialogue.

## Final response given to the user

Synthesized a fabricated (clearly labeled) Slack incident thread between
two engineers debugging stale plan-entitlement reads after a checkout
traffic spike, working through cache-metrics evidence to the conclusion
that cache invalidation must precede the shared-state write, then
distilled it into a two-file skill (`SKILL.md` + `checklist.md`) that
states the general rule, explains the race condition, gives a bad/good
code pattern, flags that reordering alone isn't sufficient without a lock
or versioning, and provides a PR-review checklist and concurrency-test
sketch — with the original incident's tickets kept only as a short
provenance footnote. All files were saved under
`iteration-2/eval-incident-log-shape-cache-invalidation/without_skill/outputs/`,
alongside `metrics.json` recording exact character counts and tool-call
tallies (6 Bash calls, 0 errors).
