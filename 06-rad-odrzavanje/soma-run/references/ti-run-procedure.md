# TI Run Procedure (STEP 4)

> Loaded from `soma-run` STEP 4 — the longest and most safety-critical step. Covers: building the TI message (mandatory date prefix), the fire-and-poll call pattern (never resend on timeout — a resend is a second full server-side chain), confirming the fetched source matches the input, capturing/validating output, the Context Quality Gate (4f) that decides PASS/WARN/ABORT before handoff to HW, and building the structured `{ti_handoff}` block (4g).

## STEP 4 — TI: Run Trend Intelligence

### 4a — Mark task in_progress

### 4b — Build TI message

Construct the message as follows (date injection is mandatory):
```
Today is {YYYY-MM-DD}. {trend_input}
```

Example:
```
Today is 2026-05-16. Anthropic released Claude Sonnet 4 — 40% SWE-bench improvement.
```

**CRITICAL:** The `Today is {date}` prefix MUST be included. Without it, TI runs without
date context and may misclassify freshness. This was confirmed as a bug on 2026-05-15.

### 4c — Call TI (fire-and-poll — do NOT wait for the reply)

Before sending, record the current latest execution id:

```
as_get_recent_executions(agent_name: "Trend Intelligence", limit: 1)
```

Store it as `{exec_before}`. Then send exactly ONE request:

```
as_chat_with_agent(
  agent_name:     "Trend Intelligence",
  message:        "Today is {YYYY-MM-DD}. {trend_input}",
  timeout_seconds: 300
)
```

**A timeout here is expected, not a failure.** The client aborts at 60 s; the run keeps
going server-side. When the tool returns a timeout error:

- do **NOT** send the message again — a second send is a second full chain
- wait ~120 s, then poll `as_get_recent_executions(agent_name: "Trend Intelligence", limit: 3)`
- the run whose `startedAt` is after `{exec_before}` is yours; wait until its `status` leaves
  `RUNNING`

If more than one new execution appears, the client retried underneath. Keep **only the
earliest** one — later retries lose the URL from the message (see the measured limit section
above) and must not be logged as trends.

### 4c-bis — Confirm the source that was actually fetched

```
as_list_agent_calls(callee_agent_name: "Security Supervisor", since_hours: 1, limit: 5)
```

The `inputPreview` of the call belonging to your run begins with `Title: ... URL Source: ...`.
If that URL is not the one in `{trend_input}`, the run is grounded in the wrong article →
mark the run `DISCARD`, do not log it, and re-run. This check costs one call and is the only
thing standing between a wrong-topic run and the winners-log.

### 4d — Capture output

Store the full reply text as `{ti_output}`. If the reply never arrived (timeout), read the
outcome from `as_get_recent_executions` `outputPreview` instead — and if that is truncated,
log the run as `RESPONSE_NOT_RECEIVED` rather than reconstructing it (see Hard rules).

### 4e — Validate TI output

Check `{ti_output}` against abort sentinels:
- If ABORT condition matched → mark TI as `FAILED`, log entry with flag `ABORT`, stop pipeline.
  Report: "⛔ TI vrati prazan ili nevalidan output. Pipeline abortiran. Provjeri agent ili input."
- If OK → extract from TI output:
  - `{ti_trend}`: the trend name/title TI identified (first sentence or headline)
  - `{ti_confidence}`: confidence rating (look for ⭐ symbols — ⭐⭐⭐ = HIGH, ⭐⭐ = MED, ⭐ = LOW/EVERGREEN)
  - `{ti_angle}`: the content angle TI suggested
  - Set `{ti_status}` = `"yes"` (hook_writer_triggered)

### 4f — Evaluate TI output quality (Context Quality Gate)

*Skip entirely if `pipeline_scope == "TI"` — no HW run means no handoff needed.*

Before passing context to HW, evaluate whether `{ti_output}` contains the three
elements HW needs to generate quality hooks. Implements the EVALUATE phase of
iterative context retrieval.

**Element check — use values already extracted in 4e:**

| Element | Variable | Present if |
|---|---|---|
| topic | `{ti_trend}` | non-empty AND len > 5 chars |
| confidence | `{ti_confidence}` | contains at least one ⭐ |
| angle | `{ti_angle}` | non-empty AND len > 10 chars |

```
topic_present      = {ti_trend} non-empty AND len({ti_trend}) > 5
confidence_present = {ti_confidence} contains "⭐"
angle_present      = {ti_angle} non-empty AND len({ti_angle}) > 10

quality_score = (topic_present + confidence_present + angle_present) / 3
```

**Note:** `{ti_angle}` extraction is best-effort — TI output is unstructured LLM text.
`angle_present = True` confirms the field was populated, not that the content is a
valid angle. False positives are possible but acceptable — the full `{ti_output}` in
the `<<SOMA_CONTEXT_START>>` block remains available for HW regardless.

**Decision logic:**

```
quality_score = 1.0  → {ti_quality_status} = "PASS"
                        → proceed to 4g
quality_score ≥ 0.33 → {ti_quality_status} = "WARN: missing [topic|confidence|angle]"
                        (list only the missing elements)
                        → proceed to 4g with "not found" for missing elements
quality_score = 0.0  → {ti_quality_status} = "ABORT"
                        → mark TI as FAILED, do not proceed to HW or 4g
                        Report: "⛔ TI output ne sadrži nijedan potreban element
                        (topic/confidence/angle). Pipeline abortiran —
                        provjeri TI sistem prompt i KB wiring."
```

Store `{ti_quality_status}` for use in STEP 9 report. Do NOT write to TI evo-log
(TI evo-log format has no notes field — adding one would break existing parsers).

### 4g — Construct structured handoff: TI → HW

*Skip entirely if `pipeline_scope == "TI"` — no HW run means no handoff needed.*
*Skip if `{ti_quality_status}` = "ABORT" — pipeline already stopped in 4f.*

Build a structured handoff block that gives HW both a parseable header and the full
original TI context. Implements the REFINE phase of iterative context retrieval.

**Extraction rules for optional fields (scan `{ti_output}`):**

| Field | What to scan for | If not found |
|---|---|---|
| `platform_hint` | Platform names: LinkedIn, X, Twitter, YouTube, Instagram, TikTok, TT, LI, IG | `"not specified"` |
| `audience_hint` | Audience words: founders, developers, marketers, engineers, CTOs, product managers | `"not specified"` |
| `timing_signal` | Urgency words: breaking, just released, announced today, this week, trending now | `"not specified"` |

If found → extract the surrounding sentence (verbatim from `{ti_output}`).
If not found → use `"not specified"`. Never generate these values from memory.

**Construct `{ti_handoff}`:**

```
<<SOMA_HANDOFF_START>>
TREND: {ti_trend}
CONFIDENCE: {ti_confidence}
ANGLE: {ti_angle}
PLATFORM_HINT: {platform_hint}
AUDIENCE_HINT: {audience_hint}
TIMING: {timing_signal}
<<SOMA_CONTEXT_START>>
{ti_output}
<<SOMA_HANDOFF_END>>
```

Store result as `{ti_handoff}`.

**Critical:** `{ti_output}` between `<<SOMA_CONTEXT_START>>` and `<<SOMA_HANDOFF_END>>`
must be the complete, verbatim TI output. Never truncate or summarize.
The `<<...>>` delimiters are chosen to avoid collision with TI output content
(TI uses standard markdown, not angle-bracket delimiters).

---

