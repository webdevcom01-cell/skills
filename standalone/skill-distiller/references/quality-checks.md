# Quality checks

Advisory checks — flag findings to the user, never silently block a skill from
being finished over these. Each targets a specific, observed failure mode in
distilled skills, not a stylistic preference.

## Verbatim source overlap (mechanical, not just an instruction to remember)

**What it catches:** long runs of source text reproduced word-for-word in
the distilled output, despite the instruction not to. This check exists
because prose instruction alone was empirically shown insufficient: a real
distillation run reproduced up to 29 consecutive words from its source
while its own self-report claimed no verbatim copying had occurred. Telling
the executor not to copy verbatim is necessary but not sufficient — this is
the mechanical backstop.

**The mechanism:** `scripts/check_verbatim_overlap.py <source-file>
<skill-folder>` tokenizes both the source and every produced `SKILL.md` /
`references/*.md` file, and flags any run of 15+ consecutive matching words
(the same threshold used elsewhere in this project for quotation limits).
Run it *during* distillation, while the source is still available as a
file — not after, since by the time `lint_skill.py` runs the original
source is typically no longer present to compare against.

**Real limitation, stated plainly:** this only catches *exact* word-for-word
runs. A close paraphrase — reordered clauses, synonym swaps, same sentence
structure with different words — will not trigger it. It is a backstop
against literal copy-paste, not a general originality checker. Passing this
check is necessary, not sufficient, for good distillation; Step 4 of
`distillation-algorithm.md` (structure, not summary) is what actually
produces good output — this check only catches the specific, observed
failure of literal copying slipping through despite instructions.

## Fidelity to source (accuracy, not just structure)

**What it catches:** confident, specific-sounding claims in the distilled
output — a number, a named threshold, a rule stated as absolute — that
don't actually trace back to anything the source said. This is a different
failure from `incident-log-shape`: that one catches rules still wearing an
incident's clothing; this one catches rules that were never really in the
source at all, manufactured during distillation because a vague source
"felt like" it should have a crisp rule.

**The test:** for any specific claim (a number, a named rule, a hard
boundary), find the exact sentence or passage in the source that supports
it. If you can't, one of two things is true: either the source genuinely
doesn't specify it — in which case say so explicitly in the output ("the
source doesn't give an exact threshold here") — or the claim needs to be
loosened to match what the source actually supports (a described tendency,
not a fixed rule).

This matters more than it might seem: a distilled skill that states things
with false confidence is worse than a source-accurate one that's honest
about its own gaps, because whoever relies on the skill later has no way to
tell confidently-wrong from actually-verified without going back and
re-reading the original source themselves — which defeats the purpose of
distilling it in the first place.

## Worth distilling

Before writing anything, check: is this actually worth becoming a skill?
Three concrete signals, not a general sense of "this was hard":

1. The same multi-step procedure will plausibly need to run again.
2. A dead end was hit and a working path around it was found — worth keeping
   the failure *and* the fix together, not just the fix.
3. Someone corrected an approach — worth keeping so the same mistake doesn't
   repeat.

A skill should not restate what's already reliably available elsewhere in the
loaded context (system instructions, tool schemas, a CLAUDE.md-equivalent
file) — check for that redundancy before writing. And a single one-off answer
that won't recur is not skill material, no matter how much effort it took.

## Always-on vs on-demand

For every piece of content, ask: *would an agent need to know this BEFORE it
can even decide whether it needs the rest of this skill?*

- **Yes** → goes in the `SKILL.md` body itself (always loaded once the skill
  triggers): the central mental model, the decision rule used in most
  invocations, anything needed to navigate the rest.
- **No, only relevant to one sub-case or one specific question** → goes in
  `references/`, consulted only when that specific case comes up.

This is an economic split, not an aesthetic one: content that's only needed
occasionally but gets loaded every time is a standing cost paid on every
invocation regardless of whether it's used. Keep the `SKILL.md` body itself
under roughly 500 lines and 5,000 tokens — both limits apply together, and
the token count is the one no structural validator checks for you, so measure
it yourself before calling a skill finished.

## incident-log-shape — a rule that only works with the story still attached

**What it catches:** a "principle" or instruction written in a way that only
makes sense with the originating incident's specific details (a ticket
number, a date, a specific error message from one occurrence) still attached
— rather than as a standalone rule.

**The test:** delete every ticket/PR/issue number, every specific date, and
every proper name of a one-off event from the sentence. Does the rule still
stand on its own and make sense? If not, it hasn't actually been distilled
into a rule yet — it's still a log entry wearing a rule's clothing.

Bad (fails the test): "Per the fix in PR #4821, always check the cache
invalidation order before deploying to staging on a Friday."

Good (passes, same underlying lesson): "Check cache invalidation order before
any deploy that changes shared state — invalidating before the dependent
write completes causes stale reads under load."

This shows up most often when a skill (or a reference file) is written
directly from a transcript of "what happened" rather than from a deliberate
distillation pass. If several instructions in a draft read like log entries,
that's a signal to go back through Step 4 of the distillation algorithm again
— extract the *rule*, not the *event*.

## references-sprawl — an index that's actually a log

**What it catches:** a `references/` directory whose file count grows with
the number of *sessions* that touched this skill rather than the number of
genuinely distinct *topics* it covers — usually one new file per work
session instead of new content getting folded into the topic file it belongs
to.

**Rough threshold to watch:** once a `references/` directory passes roughly
50-60 files, treat it as a signal worth checking, not an automatic problem —
a large, carefully organized knowledge-base skill can legitimately have that
many topic files. What actually matters is whether each file name describes
a *topic* (`aws-deployment.md`, `retry-policies.md`) or an *event*
(`session-2026-08-14.md`, `fix-for-bug-203.md`). Any of the latter is the
real signal, regardless of total count.

**The fix is never "delete files."** It's to merge same-topic files together
and strip the incident-narrative framing out of what's kept — the same
correction as `incident-log-shape`, just applied at the level of file
organization instead of a single sentence. This is the direct converse of
the fold-in check in the distillation algorithm: that check prevents sprawl
before it starts; this one catches it if it already happened.

## Description quality (the actual triggering mechanism)

`description` is not documentation — it is read on every session regardless
of whether the skill is used, and it is the only thing deciding whether the
skill triggers at all. Concretely:

- Third person, state what the skill does *and* when to use it — both halves
  matter equally; a description of only the mechanism without trigger
  contexts under-triggers.
- Include concrete trigger phrases a real user would actually say (in every
  language the skill's users actually use it in — do not default to English
  trigger phrases only, if the intended users work in another language).
- Add an explicit "Do NOT use for X — use Y instead" when there is a
  neighboring skill this one could plausibly be confused with. This is the
  single most effective way observed to prevent two skills from fighting over
  the same trigger.
- Stay within roughly 1,024 characters — this is the one frontmatter
  constraint enforced in code by at least one major implementation studied,
  and nothing is gained by writing past it since some clients truncate
  silently rather than reject.
