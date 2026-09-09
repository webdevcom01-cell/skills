---
name: idea-to-project
description: "Use when someone has a raw idea and wants a real deliverable built through Idea→Spec→Build→Test→Deploy; hands off React/Next/Vite UI decisions to react-design:director first."
---

# Skill: idea-to-project
*Version: 1.2 — generated 2026-08-21, first run: SOMA Vitals dashboard (Agent Studio health check). Updated 2026-09-03 (T-35): added a BUILD-step handoff to react-design:director for React/Next/Vite UI work — see Constraints and Rules #6 and the STEP 3 table. Updated 2026-09-09 (two edit passes, same day): pass 1 added a BUILD-table route from repo-scoped code/feature/module deliverables to `sdd-workflow` (STEP 3 table) and, in this skill's STEP 4 (TEST), an independent-verification requirement modeled on sdd-workflow's CONVERGE step (its Step 7); pass 2 tied the boundary between that row and the plain Write/Edit row to sdd-workflow's own "Trivial" rigor bar (1–2 files, no new dependency, no new user-visible behavior), after adversarial-verify found pass 1's row wording ambiguous for a small in-repo edit.*

---

## Trigger

Use this skill when someone has a raw idea and wants it to become a real, working deliverable —
not just advice about the idea. Typical openers:
- "imam ideju za projekat X, hajde da je uradimo"
- "želim da automatizujem proces od ideje do gotovog projekta"
- "build me a [dashboard/tool/report/app] that does X"
- "hoću novi projekat, ali ne znam odakle da krenem"

Do NOT use this skill for:
- A quick factual question or a one-shot edit — just do it directly.
- A request that already includes a full written spec — jump straight to STEP 3 (BUILD).
- Continuing work on a project this same conversation already spec'd — reuse that spec instead
  of restarting the pipeline.
- A React/Next.js/Vite project where the ask is specifically about UI/component library/theme/
  design-system decisions, not the overall idea→spec framing — hand off to `react-design:director`
  for that layer instead.

## What This Skill Does

Forces five phases to happen **in order, each one a visible artifact**, so an idea can't quietly
evaporate between "sounds cool" and "nothing got built":

```
IDEA  →  SPEC  →  BUILD  →  TEST  →  DEPLOY
(talk)   (file)   (thing)  (proof)  (shipped)
```

The single most important rule: **SPEC is a file, not a paragraph in the chat.** The bottleneck
this skill exists to fix is ideas dying in the "sounds good, let's do it" phase without anyone
writing down scope, data source, and what "done" means. If that file doesn't get written, this
skill hasn't been followed — no matter how much was built.

---

## STEP 0 — Task List

Call `TaskCreate` for each phase before starting:
- "Napravi SPEC dokument"
- "Sakupi/proveri realne podatke ili sadržaj" (skip if the project needs none)
- "Napravi [deliverable]"
- "Proveri [deliverable] protiv definicije gotovo"
- "Isporuči/objavi [deliverable]"

Mark each `in_progress` before starting, `completed` when done. This mirrors the phases back to
the person so they can see where the idea actually is.

## STEP 1 — IDEA: Pin down what's actually being asked

An idea stated in one sentence almost always hides three unstated decisions: **what it's for**,
**how big it should be**, and **whether this is a one-off or something to keep**. Surface them
before writing anything:

- If the person is present and the request is ambiguous on scope, format, or a fork in the
  approach → use `AskUserQuestion`. Keep it to 1–2 rounds; more than that stalls momentum on
  something that's still just an idea.
- If working unattended (scheduled run, user known to be away) → state the assumption plainly
  and proceed; don't block on a question no one will answer.
- If the person offers to let you pick (e.g. "smisli ti nešto") → propose 2–4 concrete,
  scoped options via `AskUserQuestion` rather than guessing silently — this keeps the choice
  theirs even when the idea is yours.

Capture, in your own head or notes at this point (this is not the spec file yet):
problem/motivation, who it's for, rough scope, and what "finished" would look like.

## STEP 2 — SPEC: Write it down before building anything

Write an actual file (markdown is fine) using this template — trim sections that genuinely don't
apply, but don't skip the file itself:

```
# SPEC: <Project Name>

**Status:** Draft → Approved for build
**Faza:** Ideja → Spec → Build → Test → Deploy

## 1. Problem / Ideja
What's broken or missing today, in plain language.

## 2. Cilj
One or two sentences: what this needs to accomplish.

## 3. Obim (Scope)
**Ulazi u obim (v1):** the smallest version that's actually useful.
**Van obima (v1):** explicitly named things being deferred — this is what keeps v1 small.

## 4. Izvor podataka / sadržaja
Where the real content comes from (a tool, a document, an MCP source, the user).
Never plan around placeholder or invented data.

## 5. Izgled / Format
What kind of deliverable this is (artifact, document, spreadsheet, script, page) and its shape.

## 6. Publika i distribucija
Who sees it, and therefore how it should be delivered (see STEP 5).

## 7. Definicija "gotovo" (test faza)
Concrete, checkable criteria — not "looks good," but things you can actually verify.

## 8. Sledeći koraci
What v2 would add, if this proves useful.
```

Show or send this file before moving on. For a present, responsive user, a brief pause here
("evo spec, kreni dalje?") is cheap insurance; for an unattended run, proceed once the file is
written — the file itself is the checkpoint.

## STEP 3 — BUILD: Spec becomes the real thing

Match tools to the deliverable named in Section 5 of the spec — do not default to one output
type:

| Spec says... | Reach for |
|---|---|
| React/Next.js/Vite app UI (component library, theme, tokens not yet decided) | `react-design:director` skill first, then build |
| Dashboard, tool, page, UI | `artifact-design` skill + `dataviz` skill (if it shows data) → `Artifact` tool |
| Word document / report | `docx` skill |
| Spreadsheet / data | `xlsx` skill |
| Slide deck | `pptx` skill |
| PDF | `pdf` skill |
| Code / feature / module in an existing or new repo, at or above `sdd-workflow`'s own "Trivial" bar (new module/endpoint, touches multiple files or subsystems, adds a dependency, or adds new user-visible behavior — i.e. it needs its own spec/plan) | `sdd-workflow` skill (Specify→Plan→Tasks→Implement→Converge), not a generic Write/Edit pass |
| A change inside an existing repo that stays within `sdd-workflow`'s own "Trivial" bar (1–2 files, no new dependency, no new user-visible behavior — e.g. a typo fix, a log message, a one-line bug fix — i.e. it needs no new spec/plan), or a genuine one-off script with no repo at all | Write/Edit directly, no format skill needed |

Before writing a line of content: **go get the real data or material named in Section 4 of the
spec.** Never placeholder or invent it — if a live source is available (an MCP tool, a file, a
health-check skill, a search), pull from it now. This is the same rule the parent process
follows: research/data first, output-format mechanics second.

If the project needs its own domain skill first (e.g. a status dashboard needs a health-check
skill to produce the numbers), run that before the format skill — content before presentation,
always in that order. The same ordering applies to the React/Next/Vite row above: `react-design:director`
sequences the component-library/theme/token decisions before any screen gets written, exactly so
those decisions don't get made after three screens already exist.

## STEP 4 — TEST: Prove it against Section 7, not against vibes

Go back to the spec's "Definicija gotovo" and check each line item concretely:
- Data/numbers on the deliverable match the source they came from (spot-check, don't assume).
- For a visual deliverable: render it and actually look — screenshot both light and dark theme
  if it's an Artifact/HTML page (a quick Playwright/Chromium screenshot is enough), check for
  overlap, overflow, or illegible contrast.
- For a document: read it back, don't just trust that it was written correctly.
- Anything Section 3 explicitly deferred should NOT quietly appear half-built — either it's in,
  or it's out, not a broken stub.
- **Verification is not self-verification.** Check Section 7 in a pass independent of the one
  that built the deliverable — spawn a subagent with only Section 7 and the actual deliverable
  (not the build conversation) to check it against each acceptance criterion; if subagents
  aren't available, do a deliberately fresh re-read yourself, one Section 7 line at a time,
  rather than trusting that "the build finished" means the spec is satisfied. Same rule as
  `sdd-workflow`'s CONVERGE step (Step 7): an agent checking its own work in the same reasoning
  pass that produced it shares all its own blind spots.

Keep the corresponding task `in_progress` until every checkable item in Section 7 has actually
been checked — not marked done because the build step finished.

## STEP 5 — DEPLOY: Ship it where Section 6 says it'll get used

Don't default to "paste it in chat." Decide from the spec's audience/distribution section:
- Something the person will revisit, update, or share → persist it (`Artifact` tool, or the
  desktop-bridge artifact flow if that's what's available).
- A file for their own machine or another app → `SendUserFile`, and write it into their
  connected folder if one exists.
- Something that needs to stay current on a schedule → set up a scheduled task
  (`create_trigger`/the scheduled-task tools) — never an in-process cron, it won't survive.
- A one-off / "just to see" → `SendUserFile` alone; don't clutter a gallery with a throwaway.

## STEP 6 — CLOSE THE LOOP

- Update the spec file's "Sledeći koraci" section with anything real that came up during build
  or test — this is what makes v2 possible without re-discovering the same scope questions.
- Tell the person, in a short paragraph (not a re-cap of every step), what shipped and where
  it lives. They watched the task list; they don't need the play-by-play repeated.
- If something genuinely worth remembering surfaced (a decision, a recurring gotcha), offer —
  don't force — logging it (e.g. `obsidian-knowledge-logger` if that fits their setup).

---

## Constraints and Rules

1. **The spec file is mandatory, even for small ideas.** Skipping it because the idea "seems
   obvious" is exactly how the ideja→spec bottleneck this skill exists to fix happens again.
2. **No invented data or placeholder content in the built deliverable.** If Section 4's source
   isn't reachable, say so and adjust scope — don't fill the gap with something made up.
3. **Don't silently expand or shrink scope during BUILD.** If reality forces a scope change
   (e.g. a tool returns different data than expected), update Section 3 of the spec and say so,
   rather than quietly building something else.
4. **TEST is a separate, real step**, even under time pressure — a build that "looks right" and
   a build that's been checked against Section 7 are not the same thing.
5. **DEPLOY follows Section 6, not habit.** Don't reflexively persist everything as an Artifact,
   and don't reflexively leave everything as a chat attachment — the spec already decided this.
6. **A React/Next/Vite UI deliverable routes through `react-design:director` first.** (T-35,
   2026-09-03) Found via a trigger eval on `react-design:director`: this skill's own BUILD table
   had no route to it, so a "react app idea, library/theme undecided" request either fell into
   the generic Dashboard/UI row (meant for one-off Artifacts, not real npm/React codebases) or
   skipped design decisions entirely under the Code/script row. Section 5 of the spec naming
   React/Next/Vite is the signal to reach for `react-design:director` before any screen gets
   written — same reasoning as rule 4: a build that "looks right" and one where the library/
   theme/token order was actually followed are not the same thing.

---

## Worked example

First run of this skill: a snapshot health dashboard for an Agent Studio system (18 agents).
IDEA → clarified scope was "software project, bottleneck = ideja→spec" then narrowed to a
concrete test case. SPEC → written as a standalone file before any data was pulled. BUILD →
`soma-skills:agent-health-check` supplied the real numbers (18 agents, 1 critical wiring bug,
1 broken-flow warning), then `artifact-design` + `dataviz` shaped them into a single-page
console-style dashboard. TEST → rendered and screenshotted in light and dark before shipping.
DEPLOY → published as a persisted `Artifact` (dashboards get revisited, so they get a durable
link, not a one-time chat file).