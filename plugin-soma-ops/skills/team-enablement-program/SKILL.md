---
name: team-enablement-program
description: Builds a client-ready 14-week AI enablement program (Week 0 baseline, 12 training weeks, Week 13 handoff) tailored to a company's real tools and real repeated tasks, producing a markdown program plan, a Week 0 baseline workbook (.xlsx), a one-page governance card and an HTML dashboard. Use whenever the user wants to train a team to run AI themselves instead of buying a custom build or an agency retainer, or says "AI enablement program", "team training program", "12-week AI curriculum", "AI adoption plan", "AI rollout plan", "train the team instead of building", or Serbian "program obuke", "obuka tima za AI", "napravi program za klijenta", "plan uvođenja AI-ja", "kurikulum za tim", "predlog obuke". Also use when asked how to prove ROI on AI training, how to measure hours saved, or who owns an AI workflow once the consultant leaves. Do NOT use to deliver the sessions, to build an agent (agent-scaffolder), or to write one skill (skill-creator-pro).
compatibility: No MCP dependency. Python 3 with the openpyxl package (scripts/requirements.txt) builds the Week 0 baseline .xlsx via scripts/build_baseline_xlsx.py; scripts/build_dashboard.py (stdlib only) builds the HTML dashboard. scripts/selftest.py covers both.
---

# Team Enablement Program

## What this produces and why it exists

A consultant-grade, client-specific program that transfers AI capability into a client's own team over 14 weeks. The commercial premise: a custom build starts depreciating the day it ships, while a trained team compounds. But most enablement programs fail at exactly two points — they never measured anything before starting, so they cannot prove value at the end; and they never name an owner, so the capability leaves with whoever happened to learn it. This skill exists to close both gaps, which is why the program runs Week 0 → Week 13 rather than Week 1 → Week 12.

Four deliverables come out of one run:

| File | Purpose |
|---|---|
| `<client>-enablement-program.md` | The 14-week plan. The main document you send. |
| `<client>-week0-baseline.xlsx` | Measurement workbook filled in before training starts. |
| `<client>-ai-governance.md` | One-page data + escalation card the team keeps. |
| `<client>-program-dashboard.html` | Visual 14-week tracker the client opens to follow progress. |
| `<client>-engagement-terms.md` | Scope, fees, exclusions and dependencies. Without it the plan gets read as the contract. |

## The two rules that govern everything

**1. Every tool, task, person, and number in the output must come from the intake — never from assumption.**

A program that says "Week 4: connect Slack and HubSpot" to a client who uses Teams and Pipedrive is worse than no program, because it tells the client you did not listen. The same applies to hours: if the client has not measured how long a task takes today, the program says `TO BE MEASURED IN WEEK 0`, never a plausible-sounding estimate. Invented baselines are the single fastest way to destroy a consultant's credibility at the Week 12 review, because the client will check.

When something required is missing, ask for it. When something optional is missing, mark it explicitly as unknown in the deliverable so the gap is visible rather than papered over.

**2. No deliverable claims that anything is compliant, lawful, defensible or approved, names a law the consultant cannot cite, or promises an outcome the consultant does not control.**

These are the sentences that get quoted back in a dispute. `references/engagement.md` §3 lists them with the rewrite for each; read it before writing the governance card or any section that touches data, law or results. A deliverable naming a statute or regulator carries the mandatory notice from §4 at the top, not the last page.

## Step 1 — Intake

Collect these before writing anything. Ask for whatever is missing, in one batch rather than one question at a time.

**Required — do not proceed without these:**

- Client / company name, and which team(s) the program is for (sales, finance, marketing, ops…)
- Number of participants and their comfort level with AI today (none / occasional chat use / already prompting daily)
- **The actual tool stack** — every named tool the team lives in daily (CRM, email, chat, docs, spreadsheets, ticketing, whatever) and which AI assistant they have access to, on which plan
- **Three to seven repeated tasks** the team does over and over — the raw material for every skill they will write. Ask for them in the team's own words.
  Task names become literal match keys in the baseline workbook, so unconfirmed guesses cost more than a delay: rename a task after Week 0 and every hour logged against it moves to the UNMATCHED row. If the tasks are still candidates rather than the team's own words, write the programme and generate the workbook after they are confirmed.
- The executive sponsor by name and role — the person who ordered this

**Ask for, but proceed with an explicit gap marker if unavailable:**

- Data sensitivity constraints (regulated data, NDA-bound client work, personal data)
- Existing automations or AI tools already in place, and whether anything is being replaced
- Session cadence and format (weekly 1h is the default; note deviations)
- Language for the deliverables — match the client, not the consultant

If the user says "just use placeholders", produce the program with clearly bracketed `[CLIENT TOOL]` markers rather than inventing a stack, and tell them which markers need filling before it goes out.

## Step 2 — Write the program document

Read `references/curriculum.md`. It contains the full week-by-week spine: objective, the exercise, what gets produced, and the completion check for each of Weeks 0–13.

Adapting it means rewriting each week's exercise so it uses the client's named tools and their named repeated tasks. The spine — what capability each week builds and in what order — stays fixed, because the order is load-bearing: people cannot write a reusable skill (Week 5) before they can reliably get one good output (Weeks 1–2), and cannot schedule anything unattended (Week 8) before they have a pass/fail check (Week 6).

Write the result to `<client>-enablement-program.md`. **Step 5 parses this file to build the dashboard, so the week headings and field labels have to be in a form the parser recognises.** Use this shape for every one of Weeks 0–13:

```markdown
### Week 5 — Writing your first skill
**Objective.** Convert one high-hour repeated task into a reusable skill.
**Exercise.** Take the top task from the Week 0 rollup and write down every decision…
**Deliverable.** One skill per participant, targeting a task with a known baseline.
**Completion check.** Someone other than the author runs it and gets a usable result.
```

The heading needs 2–4 `#` marks, the word `Week` (or `Nedelja`), then the number. Field labels may also be written as list items (`- **Objective:** …`) and in Serbian (`Cilj`, `Vežba`, `Isporuka`, `Provera`) — the parser accepts both. Anything else and the dashboard script stops with an explanation rather than emitting blank cards, so a format mistake costs a re-run, not a bad deliverable.

Two adaptations are legitimate and expected:

- **Pace.** A team already prompting daily can compress Weeks 1–3 into two sessions; a team starting cold may need Week 1 twice. Adjust and say why in the plan.
- **Depth of Month 3.** If nobody on the team will ever build an internal tool, Weeks 9–11 become "evaluate and buy" weeks instead of vibe-coding weeks. Never silently delete them — a program that quietly drops a third of its content reads as padding.

What should not be adapted away: Week 0, Week 6, and Week 13. Those three are the difference between this program and a curriculum anyone can copy off a blog post.

## Step 3 — Build the Week 0 baseline workbook

Week 0 creates a per-employee record of how long each person's work takes, handed to the person who signs their pay. Before it is generated, read `references/engagement.md` §2 — the client issues a short written notice to participants first, and the workbook uses initials or role labels rather than full names unless the client has asked otherwise. The Week 12 comparison works identically either way, and a workforce that suspects a performance audit produces numbers not worth having.

Read `references/baseline.md` for the measurement method, then run:

```bash
python3 scripts/build_baseline_xlsx.py \
  --client "Client Name" \
  --team "Sales" \
  --tasks "task one" "task two" "task three" \
  --participants "Ana Marić" "Marko Petrović" \
  --output "<client>-week0-baseline.xlsx"
```

The workbook has five sheets: a Read Me cover, the Week 0 task log, a **separate Week 12 log** for the end-of-programme measurement, a rollup of Week 0 hours by task, and a comparison sheet that fills itself once both logs are complete.

The two logs are separate for a specific reason. Re-measuring into the same sheet destroys the baseline the moment it is re-measured — every total is a live formula over that one sheet, so the before column becomes the after column and the delta reads zero. The entire commercial argument rests on that one comparison.

Three things about the rollup are worth knowing before you present it:

- Task names are matched **literally**, including capitalisation. This is deliberate: the spreadsheet functions that match loosely also treat `*` and `?` as wildcards, so a task called "unos *svih* podataka" would quietly absorb every other row beginning with "unos" and inflate the baseline.
- The team total is summed from the task log itself, not from the rollup rows, so it is right even when a task name is mistyped. Any hours that do not match a listed task appear in an **UNMATCHED** row that turns red — that is the signal to add the missing task before the sponsor signs off, not something to ignore.
- Pass every intake task to `--tasks`. The script raises the row count automatically so every task has a row and two stay blank per person for tasks the week turns up. Rows added *below* the block fall outside every total, so the blank rows and the blank Rollup rows are what discovery is for — the sheet says so in three places.

Run `python3 scripts/build_baseline_xlsx.py --help` for all options.

## Step 4 — Write the governance card

Read `references/governance.md` and adapt the three-tier data rules to the client's actual sensitivity constraints. Write it to `<client>-ai-governance.md`. A generic card is nearly useless; a card that names the client's own systems and their own regulator gets pinned to a wall.

Keep it to one page. The moment it becomes a policy document nobody reads it, and an unread policy is worse than none because it creates false assurance.

## Step 5 — Build the dashboard

```bash
python3 scripts/build_dashboard.py \
  --program "<client>-enablement-program.md" \
  --client "Client Name" \
  --output "<client>-program-dashboard.html"
```

The script parses the program markdown and renders a self-contained HTML tracker — one card per week found, each showing objective, exercise, deliverable, completion check and a status toggle. It is single-file with inline CSS so it can be emailed or dropped on a shared drive without breaking.

Read what it prints. It stops outright if no week or no field content was found, and warns when individual cards came out empty or when a week number appears twice. Those warnings mean the program markdown drifted from the format in Step 2 — fix it and re-run rather than sending a page of blank cards.

## Step 5b — Write the engagement terms annex

Read `references/engagement.md` §1 and write `<client>-engagement-terms.md`. Skipping this is the single most consistent complaint reviewers make about the package: the plan is full of conditions on the client and states none on the consultant, and with no fee, no exclusions and no stop point there is nothing for the client to sign.

Where a number is not yet agreed, write `[TO AGREE]`. A marked blank reads as an open item; a missing heading reads as an oversight. Then add one line to the top of the programme document: *"This plan is a working document, not a contract. The engagement terms annex and the signed agreement govern."*

## Step 6 — Deliver and flag the gaps

Send all five files. Then, in the message, state plainly:

- Which fields still need client input before the program can start (unmeasured baselines, unnamed owners, unconfirmed tools)
- Which weeks were adapted from the standard spine and why
- The one week you expect this specific team to resist most, and your reasoning

That last point is worth more to the client than the plan itself. Resistance concentrates where the real work is: the week a team pushes back hardest is usually the one where their current process is most fragile and most defended. Naming it before the program starts turns a mid-program derailment into a scheduled conversation.

## Program structure at a glance

```
Week 0   Baseline          measure hours per repeated task, per person
Weeks 1-4   USE IT         structured prompting → self-checking → context → connect their tools
Weeks 5-8   MAKE IT YOURS  write a skill → pass/fail check → chain → schedule with a failure plan
Weeks 9-12  BUILD WITH IT  spec → data → ship → prove it or kill it (vs. Week 0 numbers)
Week 13  Handoff           named owner per skill, documented, break/fix path, offboarding rule
```

## The five rules that decide whether it works

These belong in the delivered program document, near the front, stated as conditions of engagement rather than suggestions. Programs that fail almost always failed one of these in the first month, not the third.

1. **The sponsor is in the room every single week, doing their own real work.** Not observing. Rollouts that die are the ones where the person who ordered it ran the kickoff and then vanished — the team correctly reads that absence as a signal about priority.
2. **Everyone works on their own live task, never a demo exercise.** A toy exercise teaches the tool; a real task teaches the judgment, and produces something worth keeping.
3. **No skill is trusted until it has a written pass/fail check.** "It seemed fine" is not a test. Week 6 exists because the alternative is a team that trusts unreliable output right up until it costs them a client.
4. **Nothing runs unattended without four facts recorded: owner, alert, fallback, kill switch.** A named person, how they learn it broke, how the work gets done meanwhile, and how to stop it. An automation nobody owns is an outage waiting for an audience; one nobody can stop is worse.
5. **Measure in Week 0 or make no ROI claim in Week 12.** Unmeasured savings are opinion. The whole commercial argument for enablement over building rests on this one number, so it is not optional.

## Reference files

- `references/curriculum.md` — full Week 0–13 spine: objective, exercise, deliverable, completion check
- `references/baseline.md` — how to run the Week 0 measurement so the numbers survive scrutiny
- `references/governance.md` — the three-tier data card, escalation path, and break/fix protocol
- `references/engagement.md` — engagement terms annex, the Week 0 employee notice, the claims that must never appear in a deliverable, and the mandatory legal notice
- `scripts/build_baseline_xlsx.py` — generates the measurement workbook
- `scripts/build_dashboard.py` — generates the HTML progress tracker
- `scripts/selftest.py` — regression suite for both scripts; run it after any change to either, and once before the first client delivery. Each case corresponds to a defect that once shipped, most of them arithmetic errors in the baseline totals that were invisible without recalculating the workbook.

## Honest limits — say these out loud to the client

Enablement is not universally superior to building, and overselling it invites a bad review at Week 12.

- **Speed favours a build.** A fixed-scope build lands in months at a known price. A trained team takes a quarter to become useful. When a deadline is real, the build wins on timing.
- **The realistic outcome is a hybrid** — someone builds, someone in-house owns it. This program's actual job is manufacturing that in-house owner, without whom the hybrid collapses the day the builder leaves.
- **It does not work on everyone.** Some participants hit one error, conclude the tool is broken, and hand it back. No curriculum fixes that. The program finds the people who do not want to wait and gives them the keys; measure adoption per person, not per team, so this shows up early rather than at the end.
- **Published failure statistics are contested.** If the deliverable cites industry research on AI project failure rates, cite the study by name with its sample size and note the methodological criticism. A client who checks the source and finds it overstated will discount everything else in the document.
