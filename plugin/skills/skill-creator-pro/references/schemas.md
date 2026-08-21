<!-- Modified from anthropics/skills@b29e7cf6 (skills/skill-creator) by buky <webdevcom01@gmail.com>, 2026-07-31. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md. -->

# JSON Schemas

This document defines the JSON schemas used by skill-creator.

## Contents
- evals.json
- history.json
- grading.json
- metrics.json
- timing.json
- benchmark.json
- comparison.json
- analysis.json

---

## evals.json

Defines the evals for a skill. Located at `evals/evals.json` within the skill directory.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's example prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/sample1.pdf"],
      "expectations": [
        "The output includes X",
        "The skill used script Y"
      ]
    }
  ]
}
```

**Fields:**
- `skill_name`: Name matching the skill's frontmatter
- `evals[].id`: Unique integer identifier
- `evals[].prompt`: The task to execute
- `evals[].expected_output`: Human-readable description of success
- `evals[].files`: Optional list of input file paths (relative to skill root)
- `evals[].expectations`: List of verifiable statements

**Terminology:** `SKILL.md` calls these **assertions**; this schema, `agents/*.md` and
the scripts call them **expectations**. They are the same thing. `expectations` is the
one that matters, because it is the key the tooling reads. `assertions` is not a valid
key anywhere: nothing validates it away, so a `grading.json` that uses it is not
rejected — it is read as an empty list (`scripts/aggregate_benchmark.py:398`,
`grading.get("expectations") or []`) and the run silently grades zero expectations.
When you write a skill of your own, pick one term and use it everywhere; this note
exists because this skill did not.

---

## history.json

Tracks version progression in Improve mode. Located at workspace root.

```json
{
  "started_at": "2026-01-15T10:30:00Z",
  "skill_name": "pdf",
  "current_best": "v2",
  "iterations": [
    {
      "version": "v0",
      "parent": null,
      "expectation_pass_rate": 0.65,
      "grading_result": "baseline",
      "is_current_best": false
    },
    {
      "version": "v1",
      "parent": "v0",
      "expectation_pass_rate": 0.75,
      "grading_result": "won",
      "is_current_best": false
    },
    {
      "version": "v2",
      "parent": "v1",
      "expectation_pass_rate": 0.85,
      "grading_result": "won",
      "is_current_best": true
    }
  ]
}
```

**Fields:**
- `started_at`: ISO timestamp of when improvement started
- `skill_name`: Name of the skill being improved
- `current_best`: Version identifier of the best performer
- `iterations[].version`: Version identifier (v0, v1, ...)
- `iterations[].parent`: Parent version this was derived from
- `iterations[].expectation_pass_rate`: Pass rate from grading
- `iterations[].grading_result`: "baseline", "won", "lost", or "tie"
- `iterations[].is_current_best`: Whether this is the current best version

---

## grading.json

Output from the grader agent. Located at `<run-dir>/grading.json`.

```json
{
  "expectations": [
    {
      "text": "The output includes the name 'John Smith'",
      "passed": true,
      "evidence": "Found in transcript Step 3: 'Extracted names: John Smith, Sarah Johnson'"
    },
    {
      "text": "The spreadsheet has a SUM formula in cell B10",
      "passed": false,
      "evidence": "No spreadsheet was created. The output was a text file."
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 1,
    "total": 3,
    "pass_rate": 0.67
  },
  "execution_metrics": {
    "tool_calls": {
      "Read": 5,
      "Write": 2,
      "Bash": 8
    },
    "total_tool_calls": 15,
    "total_steps": 6,
    "errors_encountered": 0,
    "output_chars": 12450,
    "transcript_chars": 3200
  },
  "timing": {
    "executor_duration_seconds": 165.0,
    "grader_duration_seconds": 26.0,
    "total_duration_seconds": 191.0
  },
  "claims": [
    {
      "claim": "The form has 12 fillable fields",
      "type": "factual",
      "verified": true,
      "evidence": "Counted 12 fields in field_info.json"
    }
  ],
  "user_notes_summary": {
    "uncertainties": ["Used 2023 data, may be stale"],
    "needs_review": [],
    "workarounds": ["Fell back to text overlay for non-fillable fields"]
  },
  "eval_feedback": {
    "suggestions": [
      {
        "assertion": "The output includes the name 'John Smith'",
        "reason": "A hallucinated document that mentions the name would also pass"
      }
    ],
    "overall": "Assertions check presence but not correctness."
  }
}
```

**Fields:**
- `expectations[]`: Graded expectations with evidence
- `summary`: Aggregate pass/fail counts
- `execution_metrics`: Tool usage and output size (from executor's metrics.json)
- `timing`: Wall clock timing (from timing.json)
- `claims`: Extracted and verified claims from the output
- `user_notes_summary`: Issues flagged by the executor
- `eval_feedback`: (optional) Improvement suggestions for the evals, only present when the grader identifies issues worth raising

---

## metrics.json

Output from the executor agent. Located at `<run-dir>/outputs/metrics.json`.

```json
{
  "tool_calls": {
    "Read": 5,
    "Write": 2,
    "Bash": 8,
    "Edit": 1,
    "Glob": 2,
    "Grep": 0
  },
  "total_tool_calls": 18,
  "total_steps": 6,
  "files_created": ["filled_form.pdf", "field_values.json"],
  "errors_encountered": 0,
  "output_chars": 12450,
  "transcript_chars": 3200
}
```

**Fields:**
- `tool_calls`: Count per tool type
- `total_tool_calls`: Sum of all tool calls
- `total_steps`: Number of major execution steps
- `files_created`: List of output files created
- `errors_encountered`: Number of errors during execution
- `output_chars`: Total character count of output files
- `transcript_chars`: Character count of transcript

---

## timing.json

Wall clock timing for a run. Located at `<run-dir>/timing.json`.

**How to capture:** When a subagent task completes, the task notification includes `total_tokens` and `duration_ms`. Save these immediately — they are not persisted anywhere else and cannot be recovered after the fact.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3,
  "executor_start": "2026-01-15T10:30:00Z",
  "executor_end": "2026-01-15T10:32:45Z",
  "executor_duration_seconds": 165.0,
  "grader_start": "2026-01-15T10:32:46Z",
  "grader_end": "2026-01-15T10:33:12Z",
  "grader_duration_seconds": 26.0
}
```

---

## benchmark.json

Output from Benchmark mode. Located at `benchmarks/<timestamp>/benchmark.json`.

```json
{
  "metadata": {
    "skill_name": "pdf",
    "skill_path": "/path/to/pdf",
    "executor_model": "claude-sonnet-4-20250514",
    "analyzer_model": "most-capable-model",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2, 3],
    "runs_per_configuration": 3,
    "runs_per_configuration_by_config": {"with_skill": 3, "without_skill": 3},
    "runs_loaded": 6,
    "runs_rejected": 0
  },

  "runs": [
    {
      "eval_id": 1,
      "eval_name": "Ocean",
      "configuration": "with_skill",
      "run_number": 1,
      "result": {
        "pass_rate": 0.85,
        "passed": 6,
        "failed": 1,
        "total": 7,
        "time_seconds": 42.5,
        "tokens": 3800,
        "output_chars": 12450,
        "tool_calls": 18,
        "errors": 0
      },
      "expectations": [
        {"text": "...", "passed": true, "evidence": "..."}
      ],
      "notes": [
        "Used 2023 data, may be stale",
        "Fell back to text overlay for non-fillable fields"
      ]
    }
  ],

  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.85, "stddev": 0.05, "min": 0.80, "max": 0.90, "n": 3},
      "time_seconds": {"mean": 45.0, "stddev": 12.0, "min": 32.0, "max": 58.0, "n": 3},
      "tokens": {"mean": 3800, "stddev": 400, "min": 3200, "max": 4100, "n": 3}
    },
    "without_skill": {
      "pass_rate": {"mean": 0.35, "stddev": 0.08, "min": 0.28, "max": 0.45, "n": 3},
      "time_seconds": {"mean": 32.0, "stddev": 8.0, "min": 24.0, "max": 42.0, "n": 3},
      "tokens": {"mean": 2100, "stddev": 300, "min": 1800, "max": 2500, "n": 3}
    },
    "delta": {
      "pass_rate": "+0.50",
      "time_seconds": "+13.0",
      "tokens": "+1700"
    }
  },

  "data_quality": [],

  "notes": [
    "Assertion 'Output is a PDF file' passes 100% in both configurations - may not differentiate skill value",
    "Eval 3 shows high variance (50% ± 40%) - may be flaky or model-dependent",
    "Without-skill runs consistently fail on table extraction expectations",
    "Skill adds 13s average execution time but improves pass rate by 50%"
  ]
}
```

**Fields:**
- `metadata`: Information about the benchmark run
  - `skill_name` / `skill_path` / `executor_model` / `analyzer_model`: **the four
    identity fields.** None of them is present anywhere in the run inputs, so all
    four are supplied by the caller (`--skill-name`, `--skill-path`,
    `--executor-model`, `--analyzer-model`). When one is not supplied it is
    recorded as `"unspecified"` and a warning naming it goes to **both** stderr and
    `data_quality` — never a `<skill-name>` / `<path/to/skill>` / `<model-name>`
    template placeholder, which would silently make the whole benchmark
    non-reproducible while looking merely unfilled.

    The name is **not** derived from the workspace directory even though
    `SKILL.md` prescribes `<skill-name>-workspace/`. Measured on a real run whose
    workspace was named `workspace`, derivation produces `"workspace"` — a
    plausible-looking wrong identity, which is worse than a visibly absent one.
  - `timestamp`: When the benchmark was run
  - `evals_run`: List of eval names or IDs
  - `runs_per_configuration`: The **measured** number of usable runs per
    configuration, **across all evals** — not a fixed 3. If the configurations
    disagree, this is the low end and `runs_per_configuration_by_config` spells out
    each.
  - `runs_per_configuration_by_config`: `{config: count}` of usable runs.
  - `runs_per_config_per_eval`: The **measured** number of usable runs behind each
    individual eval, per configuration — counted, never
    `runs_per_configuration / len(evals_run)`, which would invent a number whenever
    the layout is uneven. This is the sample size behind any per-eval claim; the
    per-configuration figure above is typically several times larger, and
    `benchmark.md` therefore prints both, each next to the noun it counts.
  - `runs_per_config_per_eval_is_uniform`: `false` when the evals disagree, in
    which case `runs_per_config_per_eval` is the low end and `benchmark.md` says
    "at least".
  - `runs_loaded` / `runs_rejected`: How many runs entered the statistics and how
    many were refused (bad/`null` fields, unreadable files). A shrinking `n` is
    invisible without these — one surviving run and nine look identical in the
    summary table otherwise.
- `runs[]`: Individual run results
  - `eval_id`: Numeric eval identifier
  - `eval_name`: Human-readable eval name (used as section header in the viewer)
  - `configuration`: Must be `"with_skill"` or `"without_skill"` (the viewer uses this exact string for grouping and color coding)
  - `run_number`: Integer run number (1, 2, 3...)
  - `result`: Nested object with `pass_rate`, `passed`, `failed`, `total`,
    `time_seconds`, `tokens`, `output_chars`, `tool_calls`, `errors`
    - `tokens`: The **real** token count for the run, from `timing.json`'s
      `total_tokens`. It is `null` when no token count was measured — `null` is
      distinct from a measured `0`. It is **never** substituted with a character
      count.
    - `output_chars`: Total output character count (grader.md's "proxy for
      tokens"). A separate field; it is a character count, **not** a token count,
      and must never be written into `tokens`.
- `run_summary`: Statistical aggregates per configuration
  - **Key order is part of the contract.** The viewer does not look for the names
    `with_skill` and `without_skill`; it takes whatever keys are present, in insertion
    order, and assigns the **first key to column A and the second to column B**
    (`eval-viewer/viewer.html:1264-1266`):

    ```javascript
    const configs = Object.keys(summary).filter(k => k !== "delta");
    const configA = configs[0] || "config_a";
    const configB = configs[1] || "config_b";
    ```

    Writing `without_skill` first therefore swaps the columns and flips the sign of
    every `delta` — silently, with no warning and no validation error. When you write
    `benchmark.json` by hand, put the baseline **second**, and keep `delta` computed as
    first minus second.
  - `with_skill` / `without_skill`: Each contains `pass_rate`, `time_seconds`,
    and `tokens` stat objects with `mean`, `stddev`, `min`, `max`, and `n`.
    - `n`: how many runs the statistic rests on. At `n == 1` the sample stddev is
      undefined; consumers should show `(n=1)` rather than reading `± 0` as
      reproducibility.
    - `tokens`: the stat object, or `null` for the whole configuration when any
      run in it lacks a real token count (a partial average would be a fiction).
  - `delta`: difference strings like `"+0.50"`, `"+13.0"`, `"+1700"`. `tokens` is
    the string `"n/a"` when either side has no token statistic — the two sides
    must be in the same currency for a delta to mean anything.
- `data_quality`: List of problems encountered while producing this benchmark.
  Two kinds: **per-file** (rejected runs, unreadable timing, malformed fields) and
  **per-identity** (an identity field the caller did not supply, which makes the
  benchmark non-reproducible from itself). Empty when everything loaded cleanly and
  all four identity fields were given. Carried in the artifact, not only on stderr,
  because the documented invocations redirect output — a stderr-only diagnostic
  reaches nobody.
- `notes`: Freeform observations from the analyzer

**Important:** The viewer reads these field names exactly. Using `config` instead of `configuration`, or putting `pass_rate` at the top level of a run instead of nested under `result`, will cause the viewer to show empty/zero values. Always reference this schema when generating benchmark.json manually.

---

## comparison.json

Output from blind comparator. Located at `<grading-dir>/comparison-N.json`.

```json
{
  "winner": "A",
  "reasoning": "Output A provides a complete solution with proper formatting and all required fields. Output B is missing the date field and has formatting inconsistencies.",
  "rubric": {
    "A": {
      "content": {
        "correctness": 5,
        "completeness": 5,
        "accuracy": 4
      },
      "structure": {
        "organization": 4,
        "formatting": 5,
        "usability": 4
      },
      "content_score": 4.7,
      "structure_score": 4.3,
      "overall_score": 9.0
    },
    "B": {
      "content": {
        "correctness": 3,
        "completeness": 2,
        "accuracy": 3
      },
      "structure": {
        "organization": 3,
        "formatting": 2,
        "usability": 3
      },
      "content_score": 2.7,
      "structure_score": 2.7,
      "overall_score": 5.4
    }
  },
  "output_quality": {
    "A": {
      "score": 9,
      "strengths": ["Complete solution", "Well-formatted", "All fields present"],
      "weaknesses": ["Minor style inconsistency in header"]
    },
    "B": {
      "score": 5,
      "strengths": ["Readable output", "Correct basic structure"],
      "weaknesses": ["Missing date field", "Formatting inconsistencies", "Partial data extraction"]
    }
  },
  "expectation_results": {
    "A": {
      "passed": 4,
      "total": 5,
      "pass_rate": 0.80,
      "details": [
        {"text": "Output includes name", "passed": true}
      ]
    },
    "B": {
      "passed": 3,
      "total": 5,
      "pass_rate": 0.60,
      "details": [
        {"text": "Output includes name", "passed": true}
      ]
    }
  }
}
```

---

## analysis.json

Output from post-hoc analyzer. Located at `<grading-dir>/analysis.json`.

```json
{
  "comparison_summary": {
    "winner": "A",
    "winner_skill": "path/to/winner/skill",
    "loser_skill": "path/to/loser/skill",
    "comparator_reasoning": "Brief summary of why comparator chose winner"
  },
  "winner_strengths": [
    "Clear step-by-step instructions for handling multi-page documents",
    "Included validation script that caught formatting errors"
  ],
  "loser_weaknesses": [
    "Vague instruction 'process the document appropriately' led to inconsistent behavior",
    "No script for validation, agent had to improvise"
  ],
  "instruction_following": {
    "winner": {
      "score": 9,
      "issues": ["Minor: skipped optional logging step"]
    },
    "loser": {
      "score": 6,
      "issues": [
        "Did not use the skill's formatting template",
        "Invented own approach instead of following step 3"
      ]
    }
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "instructions",
      "suggestion": "Replace 'process the document appropriately' with explicit steps",
      "expected_impact": "Would eliminate ambiguity that caused inconsistent behavior"
    }
  ],
  "transcript_insights": {
    "winner_execution_pattern": "Read skill -> Followed 5-step process -> Used validation script",
    "loser_execution_pattern": "Read skill -> Unclear on approach -> Tried 3 different methods"
  }
}
```
