# Curriculum spine — Weeks 0 to 13

Each week below gives four things: the **objective** (the capability being installed), the **exercise** (what participants actually do in the hour), the **deliverable** (what exists afterwards that did not exist before), and the **completion check** (how you know the week landed rather than merely happened).

Rewrite every exercise so it names the client's own tools and their own repeated tasks. Keep the objectives and the order.

**Contents**

- [Week 0 — Baseline](#week-0--baseline)
- [Month 1: Use it (Weeks 1–4)](#month-1-use-it)
- [Month 2: Make it yours (Weeks 5–8)](#month-2-make-it-yours)
- [Month 3: Build with it (Weeks 9–12)](#month-3-build-with-it)
- [Week 13 — Handoff](#week-13--handoff)
- [Facilitation notes](#facilitation-notes)

---

## Week 0 — Baseline

**Objective.** Establish the numbers that Week 12 will be measured against. Nothing is taught this week.

**Exercise.** Each participant lists their five most repeated tasks and logs, for one working week, roughly how many hours each consumes and which tool they use. Rough is fine — consistency of method matters more than precision, because the comparison at Week 12 uses the same method.

**Deliverable.** The baseline workbook, filled in, one row per participant per task, with a signed-off rollup total.

**Completion check.** The sponsor has seen the rollup and agrees the numbers are plausible. If the sponsor is surprised by where the hours go, that surprise is itself a finding worth recording — it usually reorders which tasks get automated first.

**Why this week is non-negotiable.** Week 12 asks "what did this save?" There is no honest answer without this week, and a dishonest answer discovered later costs more than the whole engagement was worth.

---

## Month 1: Use it

The easy month. By the end, everyone gets reliable output and their assistant is connected to the systems they already live in.

### Week 1 — Structured prompting

**Objective.** Move from one-line asks to prompts that specify role, context, and required output format.

**Exercise.** Each participant takes one real task from their baseline list and writes a structured prompt for it. Run it, then have a neighbour run the same prompt and compare outputs — variation between two people running the same prompt is the fastest way to teach why specificity matters.

**Deliverable.** One structured prompt per participant, saved somewhere shared.

**Completion check.** The participant can state, without prompting, what happens to the output if they remove the format instruction.

### Week 2 — Making it check itself

**Objective.** Stop trusting first drafts. Install the habit of making the model criticise and verify its own output before a human relies on it.

**Exercise.** Take last week's output and ask the model to find what is wrong with it, what it cannot verify, and what it assumed. Then introduce the rule the team will use from here on: **any factual claim in output that leaves the team must be traceable to a source, or explicitly flagged as unverified.**

**Deliverable.** A short self-check prompt the team reuses, plus the team's own list of "things this model gets wrong about our domain".

**Completion check.** A participant catches a real error in their own output during the session. If nobody does, the tasks chosen were too low-stakes — pick harder ones.

### Week 3 — Making it know you

**Objective.** Stop re-explaining the company every session.

**Exercise.** Set up custom instructions and a shared project or workspace containing the company's context: what it sells, to whom, in what tone, with which constraints. Test by running a Week 1 prompt stripped of all its context and confirming the output is still usable.

**Deliverable.** A shared, named workspace with company context, owned by one person.

**Completion check.** The stripped-down prompt produces output the participant would still send.

### Week 4 — Connecting your tools

**Objective.** Get the assistant reading real data from the systems the team already uses, without code.

**Exercise.** Connect the client's actual stack — name the specific tools from intake. Each participant runs one query that could not have been answered without the connection.

**Deliverable.** Working connections, plus a written note of what each connection can and cannot see.

**Completion check.** Someone asks a question about live data and gets a correct answer they can verify independently in the source system. Verify it in the source system during the session; an unverified first connection is how teams learn to trust a broken integration.

---

## Month 2: Make it yours

Where compounding starts. A **skill** is a repeated task written down once so it runs the same way every time.

### Week 5 — Writing your first skill

**Objective.** Convert one high-hour repeated task into a reusable, written skill.

**Exercise.** Each participant picks a task from near the top of their own rows in the Week 0 rollup — their own list, not the team's single largest, so nobody spends the month automating someone else's work. Write down every decision the person currently makes while doing it — including the ones they make unconsciously, which is where most of the value hides. Turn that into a skill file.

**Deliverable.** One skill per participant, targeting a task with a known baseline number.

**Completion check.** Someone other than the author runs the skill and gets a usable result. If only the author can run it, the tacit decisions were not captured.

### Week 6 — Testing a skill

**Objective.** Replace "it seemed fine" with a written, repeatable pass/fail check.

**Exercise.** For each skill, write down what a correct output must contain and what it must never contain — concretely enough that two different people grading the same output would agree. Then run the skill against several real cases, including one deliberately awkward one, and grade it.

**Deliverable.** A written acceptance check per skill, and a grading result. Skills that fail get fixed or shelved this week, not later.

**Completion check.** At least one skill fails its own check. A test set where everything passes on the first attempt is not a test set — it is a demonstration, and it will not catch the failure that eventually matters.

**Why this is the week that separates a real program from a curriculum.** Weeks 7 and 8 make skills run further and run unattended. Both multiply whatever Week 6 let through.

### Week 7 — Chaining skills

**Objective.** Wire skills so one's output becomes another's input.

**Exercise.** Connect two skills from Week 5 into a sequence covering a longer stretch of real work. Grade the end of the chain against Week 6's acceptance check, not just the middle.

**Deliverable.** One working chain per participant or pair.

**Completion check.** The chain is run end to end on a real case, and the failure point is identified when a bad input is deliberately fed in at the front.

### Week 8 — Scheduling a skill

**Objective.** Let a skill run on a schedule, unattended — safely.

**Exercise.** Schedule one proven chain. Before it goes live, record the four facts the governance card requires: who owns it, how they find out it broke, what the manual fallback is meanwhile, and how to stop it — including who is allowed to.

**Deliverable.** One scheduled workflow with an owner, an alert, a fallback, and a kill switch. An automation missing any of the four does not get scheduled.

**Completion check.** The owner is a named person who knows they are the owner. "The team owns it" means nobody owns it.

---

## Month 3: Build with it

The payoff month. The team stops buying software for every small need and starts building it by describing what it should do.

### Week 9 — Vibe coding basics

**Objective.** Specify first, build second. Produce a small internal tool from a plain-language description.

**Exercise.** Write a one-page spec — who uses it, what goes in, what comes out, what must never happen — then build against the spec. The habit of speccing first is the whole point; the tool is a by-product.

**Deliverable.** A running internal tool solving one real annoyance, plus its spec.

**Completion check.** The tool matches its spec, and the participant can name one thing they deliberately left out.

### Week 10 — Giving it a database

**Objective.** Enough data and backend literacy that a tool can store and recall things.

**Exercise.** Add persistence to Week 9's tool. Cover, at minimum: where the data physically lives, who can read it, and what happens if it is lost.

**Deliverable.** The tool, now with storage, and a one-line answer to each of those three questions.

**Completion check.** The participant can say where the data is stored and who else can see it. If they cannot, stop — this is a data incident in slow motion, and the governance card exists precisely for this moment.

### Week 11 — Shipping it

**Objective.** Deploy to a real URL, and understand the line between what the team builds and what needs a professional engineer.

**Exercise.** Deploy Week 10's tool. Then draw the line explicitly with the team: internal tools with non-sensitive data on one side; anything customer-facing, handling payments, holding personal data, or becoming a dependency for others on the far side.

**Deliverable.** A live internal tool, and the team's own written green/red line.

**Completion check.** The team can classify three hypothetical projects on the correct side of their own line.

### Week 12 — Prove it or kill it

**Objective.** Measure honestly against Week 0 and keep only what earned its place.

**Exercise.** Re-run the Week 0 measurement using the same method. Fill in the comparison sheet. For every skill and tool built, decide: keep, fix, or kill. Killing things is the point — a program that keeps everything measured nothing.

**Deliverable.** The completed comparison sheet, and a keep/fix/kill decision per artefact with the sponsor present.

**Completion check.** At least one thing gets killed, and the hours saved figure traces to two measurements taken the same way rather than to an estimate.

---

## Week 13 — Handoff

**Objective.** Make the capability outlive the individuals who learned it, and outlive the consultant.

**Exercise.** For every surviving skill, chain, and tool, record: the named owner, the backup owner, where it is documented, how it is tested, the alert that fires when it breaks, the manual fallback, the kill switch and who may use it, and what happens when the owner leaves the company. For anything scheduled, this is the same set of four facts Week 8 required — the register is where they finally live. Then the consultant deliberately does not answer a support question that the team can answer, and the team answers it.

**Deliverable.** An ownership register covering every surviving artefact, plus a 30/60/90-day review date in the sponsor's calendar.

**Completion check.** Every surviving artefact has a human name against it, and the team resolved one real issue during the session without the consultant.

**Why this week exists.** Without it, the knowledge walks out with whoever learned it, and the client is back where they started — the exact failure mode enablement was supposed to avoid. A trained team that documented nothing is just a build with a shorter half-life.

---

## Facilitation notes

**Format.** One hour, weekly, whole team present, everyone on their own live work. Twelve teaching hours total plus Week 0 and Week 13.

**Sequencing is load-bearing.** Each month depends on the one before: fluency enables skills, skills enable building. Teams that skip ahead to Month 3 build tools they cannot evaluate.

**Adapt pace, not order.** Teams already prompting daily can compress Weeks 1–3. Teams starting cold may need Week 1 twice. Note any change in the delivered plan with the reason, so the client sees a decision rather than an omission.

**When Month 3 does not apply.** If nobody will build internal tools, convert Weeks 9–11 into evaluate-and-buy weeks: write the spec (Week 9), assess options against it including data location (Week 10), run a scoped trial and decide (Week 11). Week 12 is unchanged — the measurement matters either way.

**Attendance is a leading indicator.** Track it per person from Week 1. Participation drops before results do, and a sponsor who misses two consecutive weeks predicts a stalled programme more reliably than any other signal.
