#!/usr/bin/env python3
# Modified from anthropics/skills@b29e7cf6 (skills/skill-creator) by
# buky <webdevcom01@gmail.com>, 2026-07-30. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md.
"""
Aggregate individual run results into benchmark summary statistics.

Reads grading.json files from run directories and produces:
- run_summary with mean, stddev, min, max for each metric
- delta between with_skill and without_skill configurations

Usage:
    python aggregate_benchmark.py <benchmark_dir>

Example:
    python aggregate_benchmark.py benchmarks/2026-01-15T10-30-00/

The script supports two directory layouts:

    Workspace layout (from skill-creator iterations):
    <benchmark_dir>/
    └── eval-N/
        ├── with_skill/
        │   ├── run-1/grading.json
        │   └── run-2/grading.json
        └── without_skill/
            ├── run-1/grading.json
            └── run-2/grading.json

    Legacy layout (with runs/ subdirectory):
    <benchmark_dir>/
    └── runs/
        └── eval-N/
            ├── with_skill/
            │   └── run-1/grading.json
            └── without_skill/
                └── run-1/grading.json
"""

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path


# Known naming conventions used by SKILL.md's two workflows:
#   - "Creating a new skill":       with_skill  vs. without_skill
#   - "Improving an existing skill": with_skill  vs. old_skill
# The "with_skill" (or "new_skill") side is always the one we measure
# improvement *from the baseline*, so delta = primary - baseline.
PRIMARY_CONFIG_NAMES = {"with_skill", "new_skill"}
BASELINE_CONFIG_NAMES = {"without_skill", "old_skill"}

# Distinct exit codes, so a caller (or an agent reading the exit status) can tell
# "you invoked me wrong" apart from "there was nothing to aggregate". The second
# case used to exit 0 with a full report of zeros.
EXIT_OK = 0
EXIT_USAGE = 1
EXIT_NO_DATA = 3


def pick_primary_and_baseline(configs: list[str]) -> tuple[str | None, str | None]:
    """Determine which config is primary (with the skill / new version) and
    which is baseline (without the skill / old version).

    Bug history: this used to take configs[0]/configs[1] in whatever order
    the `results` dict happened to have them in, which came from
    sorted(Path.iterdir()) — alphabetical directory order. That silently
    inverted the delta's sign whenever the baseline directory name sorted
    before the primary one, e.g. "old_skill" < "with_skill" alphabetically
    (the "improving an existing skill" workflow always hits this — its
    baseline dir is named "old_skill" per SKILL.md). A skill that actually
    improved would then show up with a *negative* delta.

    Resolve explicitly by known name instead. Alphabetical order is only a
    last-resort fallback for unrecognized naming schemes, and prints a
    warning so a wrong-sign delta is never silent again.
    """
    primary = next((c for c in configs if c in PRIMARY_CONFIG_NAMES), None)
    baseline = next((c for c in configs if c in BASELINE_CONFIG_NAMES), None)

    if primary and baseline:
        return primary, baseline

    remaining = [c for c in configs if c not in (primary, baseline)]

    # A name was explicitly recognized (as primary OR baseline) even though
    # its counterpart is missing — e.g. a single-config directory left over
    # from an interrupted benchmark, or a rerun of just one side. Keep that
    # recognition rather than falling through to the unrecognized-name
    # fallback below, which would silently relabel a *known* baseline (e.g.
    # a lone "old_skill" dir) as primary. Pair it with `remaining[0]` only
    # if there's an actual unrecognized directory to pair it with.
    if primary and not baseline:
        if remaining:
            baseline = remaining[0]
        return primary, baseline
    if baseline and not primary:
        if remaining:
            primary = remaining[0]
        return primary, baseline

    # Neither name was recognized at all.
    if len(configs) >= 2:
        primary, baseline = configs[0], configs[1]
        print(
            f"Warning: unrecognized configuration names {configs!r} - falling back to "
            f"alphabetical order for delta calculation (primary={primary!r}, "
            f"baseline={baseline!r}). Verify this matches the direction you expect; "
            f"delta is computed as primary - baseline.",
            file=sys.stderr,
        )
    elif len(configs) == 1:
        primary, baseline = configs[0], None

    return primary, baseline


def calculate_stats(values: list[float]) -> dict:
    """Calculate mean, stddev, min, max, and n for a list of values.

    `n` is carried through so downstream display can say how many runs a
    statistic rests on. With n=1 the sample stddev is undefined, not zero:
    reporting "± 0" reads as perfect reproducibility when in fact nothing was
    measured twice (N-09). `stddev` stays a number here (0.0 at n=1) so the
    JSON consumer — eval-viewer/viewer.html — keeps working, but the markdown
    layer uses `n` to render "(n=1)" instead of the misleading "± 0"; the
    viewer's own n-aware rendering is folded into the renderBenchmark refactor
    (T-06).
    """
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0, "n": 0}

    n = len(values)
    mean = sum(values) / n

    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0

    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "n": n,
    }


class RunRejected(Exception):
    """A run's grading data cannot be used as a measurement.

    Raised instead of substituting a default, because a default is
    indistinguishable from a measured value once it reaches the statistics.
    """


def _number(container: dict, key: str, default, *, where: str) -> float:
    """Read a numeric field that feeds the statistics.

    A missing key means "not recorded" and is documented as optional
    (agents/grader.md: timing and execution_metrics are "if available"), so the
    default applies. A key that is *present* holding null — or a string, or a
    list — is corrupt data, not absence: `dict.get(key, default)` does NOT
    protect against it, since the default only applies when the key is absent.
    Letting it through reaches `calculate_stats` as None and raises TypeError
    deep in the arithmetic, which is why this is a hard reject with the file
    named in the message.
    """
    if key not in container:
        return default
    value = container[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RunRejected(f"field {where}.{key} is not a number (got {value!r})")
    return value


def _string_list(container: dict, key: str, *, source: Path, warnings: list) -> list:
    """Read a narrative (non-measurement) list field.

    Deliberately more forgiving than `_number`: notes do not enter any
    statistic, so a malformed notes field must not disqualify an otherwise
    valid measurement. It is still reported, because `list.extend(None)` used
    to raise TypeError here and silence is what made that indistinguishable
    from "no notes".
    """
    if key not in container:
        return []
    value = container[key]
    if not isinstance(value, list):
        warnings.append(f"{source}: field user_notes_summary.{key} is not a list "
                        f"(got {value!r}) - notes ignored for this run")
        return []
    return [str(v) for v in value]


def _run_number(run_dir: Path, fallback: int, *, warnings: list) -> int:
    """Parse the run number out of a `run-<N>` directory name.

    The identical pattern for eval directories (`int(name.split("-")[1])`) is
    already wrapped in try/except ValueError; this one was not, so a directory
    named `run-retry` — which `glob("run-*")` happily matches — took down the
    whole aggregation. The run number is a label, not a measurement, so fall
    back to the positional index and say so.
    """
    try:
        return int(run_dir.name.split("-")[1])
    except (IndexError, ValueError):
        warnings.append(f"{run_dir}: directory name is not run-<number>, "
                        f"numbering it {fallback} by position")
        return fallback


def load_run_results(benchmark_dir: Path) -> tuple[dict, dict]:
    """
    Load all run results from a benchmark directory.

    Returns (results, report). `results` is a dict keyed by config name
    (e.g. "with_skill"/"without_skill", or "new_skill"/"old_skill"), each
    containing a list of run results. `report` carries the counts and
    diagnostics the caller needs to tell "nothing was measured" apart from
    "everything measured zero":

        {"loaded": int, "rejected": int, "searched": [str], "warnings": [str]}
    """
    report = {"loaded": 0, "rejected": 0, "searched": [], "warnings": []}

    # Support both layouts: eval dirs directly under benchmark_dir, or under runs/
    runs_dir = benchmark_dir / "runs"
    if runs_dir.exists():
        search_dir = runs_dir
    elif list(benchmark_dir.glob("eval-*")):
        search_dir = benchmark_dir
    else:
        report["warnings"].append(
            f"No eval-* directories found in {benchmark_dir} or {runs_dir}")
        return {}, report

    results: dict[str, list] = {}

    for eval_idx, eval_dir in enumerate(sorted(search_dir.glob("eval-*"))):
        report["searched"].append(str(eval_dir))
        metadata_path = eval_dir / "eval_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path) as mf:
                    eval_id = json.load(mf).get("eval_id", eval_idx)
            except (json.JSONDecodeError, OSError):
                eval_id = eval_idx
        else:
            try:
                eval_id = int(eval_dir.name.split("-")[1])
            except ValueError:
                eval_id = eval_idx

        # Discover config directories dynamically rather than hardcoding names
        for config_dir in sorted(eval_dir.iterdir()):
            if not config_dir.is_dir():
                continue
            # A configuration is a directory that holds either run-* subdirs
            # (legacy layout) or a grading.json of its own. The second case is
            # the layout SKILL.md:180 and agents/grader.md:92 actually prescribe
            # — outputs go to <config>/outputs/ and grading.json is written as a
            # sibling of outputs, with no run-* level at all. Requiring run-*
            # here meant the documented layout produced zero runs, an all-zero
            # summary and exit 0.
            run_dirs = sorted(config_dir.glob("run-*"))
            if not run_dirs and not (config_dir / "grading.json").is_file():
                continue                        # inputs/, outputs/, etc.
            config = config_dir.name
            if config not in results:
                results[config] = []

            # `None` marks "the config directory is itself the single run".
            for fallback, run_dir in enumerate(run_dirs or [None], start=1):
                if run_dir is None:
                    run_dir = config_dir
                    run_number = 1
                else:
                    run_number = _run_number(run_dir, fallback,
                                             warnings=report["warnings"])
                grading_file = run_dir / "grading.json"

                if not grading_file.exists():
                    report["warnings"].append(
                        f"{run_dir}: grading.json not found - run skipped")
                    report["rejected"] += 1
                    continue

                try:
                    with open(grading_file) as f:
                        grading = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    report["warnings"].append(
                        f"{grading_file}: unreadable ({e}) - run skipped")
                    report["rejected"] += 1
                    continue

                try:
                    result = _build_result(grading, run_dir, grading_file,
                                           eval_id, run_number,
                                           warnings=report["warnings"])
                except RunRejected as e:
                    report["warnings"].append(f"{grading_file}: {e} - run skipped")
                    report["rejected"] += 1
                    continue

                results[config].append(result)
                report["loaded"] += 1

    # How many usable runs each *discovered* configuration ended up with. A
    # configuration that appears here with 0 was found on disk but produced
    # nothing usable — which is not the same as scoring zero, and must not be
    # rendered as "0% ± 0%".
    report["configurations"] = {c: len(r) for c, r in results.items()}

    return results, report


def _build_result(grading: dict, run_dir: Path, grading_file: Path,
                  eval_id, run_number: int, *, warnings: list) -> dict:
    """Turn one grading.json into a run result, or raise RunRejected.

    Every field that enters `calculate_stats` goes through `_number`, so a
    corrupt value is refused here — where the file name is still known — rather
    than becoming a plausible zero in the summary table.
    """
    if not isinstance(grading.get("summary"), dict):
        raise RunRejected(
            "no 'summary' object (pass_rate/passed/failed/total must be nested "
            "under 'summary' - see references/schemas.md)")
    summary = grading["summary"]

    result = {
        "eval_id": eval_id,
        "run_number": run_number,
        "pass_rate": _number(summary, "pass_rate", 0.0, where="summary"),
        "passed": _number(summary, "passed", 0, where="summary"),
        "failed": _number(summary, "failed", 0, where="summary"),
        "total": _number(summary, "total", 0, where="summary"),
    }

    # Extract timing — check grading.json first, then sibling timing.json
    timing = grading.get("timing") or {}
    if not isinstance(timing, dict):
        raise RunRejected(f"field 'timing' is not an object (got {timing!r})")
    result["time_seconds"] = _number(timing, "total_duration_seconds", 0.0,
                                     where="timing")
    timing_file = run_dir / "timing.json"
    if result["time_seconds"] == 0.0 and timing_file.exists():
        try:
            with open(timing_file) as tf:
                timing_data = json.load(tf)
        except (json.JSONDecodeError, OSError) as e:
            # timing.json is optional (agents/grader.md:113 "if it exists"), so
            # an unreadable one must not disqualify the run. Previously only
            # JSONDecodeError was caught here while the eval_metadata.json read
            # above catches OSError too — the same problem crashed in one place
            # and was tolerated in the other.
            warnings.append(f"{timing_file}: unreadable ({e}) - timing ignored")
            timing_data = {}
        if not isinstance(timing_data, dict):
            warnings.append(f"{timing_file}: not a JSON object - timing ignored")
            timing_data = {}
        result["time_seconds"] = _number(timing_data, "total_duration_seconds",
                                         0.0, where="timing.json")
        if "total_tokens" in timing_data:
            result["tokens"] = _number(timing_data, "total_tokens", 0,
                                       where="timing.json")

    # Extract metrics if available
    metrics = grading.get("execution_metrics") or {}
    if not isinstance(metrics, dict):
        raise RunRejected(
            f"field 'execution_metrics' is not an object (got {metrics!r})")
    result["tool_calls"] = _number(metrics, "total_tool_calls", 0,
                                   where="execution_metrics")
    # output_chars is a *character* count (grader.md:207 calls it a "proxy for
    # tokens"), NOT a token count. It is kept as its own field and never fed
    # into `tokens`. Previously, when no real token count was present, this
    # line did `result["tokens"] = output_chars`, so the "Tokens" column and
    # the token delta reported characters — and, worse, mixed real tokens
    # (from timing.json) against characters across configurations, producing a
    # meaningless delta an order of magnitude too large (N-07). A run with no
    # measured token count now carries tokens = None ("not measured"), which
    # is distinct from a measured zero.
    if "output_chars" in metrics:
        result["output_chars"] = _number(metrics, "output_chars", 0,
                                         where="execution_metrics")
    result.setdefault("tokens", None)
    result["errors"] = _number(metrics, "errors_encountered", 0,
                               where="execution_metrics")

    # Extract expectations — viewer requires fields: text, passed, evidence
    raw_expectations = grading.get("expectations") or []
    if not isinstance(raw_expectations, list):
        raise RunRejected(
            f"field 'expectations' is not a list (got {raw_expectations!r})")
    for exp in raw_expectations:
        if not isinstance(exp, dict) or "text" not in exp or "passed" not in exp:
            warnings.append(
                f"{grading_file}: expectation missing required fields "
                f"(text, passed, evidence): {exp}")
    result["expectations"] = raw_expectations

    # Extract notes from user_notes_summary
    notes_summary = grading.get("user_notes_summary") or {}
    if not isinstance(notes_summary, dict):
        warnings.append(f"{grading_file}: field 'user_notes_summary' is not an "
                        f"object (got {notes_summary!r}) - notes ignored")
        notes_summary = {}
    notes: list = []
    for key in ("uncertainties", "needs_review", "workarounds"):
        notes.extend(_string_list(notes_summary, key, source=grading_file,
                                  warnings=warnings))
    result["notes"] = notes

    return result


def aggregate_results(results: dict) -> dict:
    """
    Aggregate run results into summary statistics.

    Returns run_summary with stats for each configuration and delta.
    """
    run_summary = {}
    configs = list(results.keys())

    for config in configs:
        runs = results.get(config, [])

        if not runs:
            run_summary[config] = {
                "pass_rate": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0, "n": 0},
                "time_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0, "n": 0},
                "tokens": None,
            }
            continue

        pass_rates = [r["pass_rate"] for r in runs]
        times = [r["time_seconds"] for r in runs]

        # A token statistic is only meaningful if EVERY run in the config
        # carries a real, measured token count. If any run is missing one
        # (tokens is None — see _build_result), the aggregate is None
        # ("not measured"), never a number computed from a partial or
        # char-count-substituted set. This is what stops the mixed-unit delta
        # in N-07: with_skill measured in tokens, without_skill in nothing,
        # must not produce a token delta at all.
        token_values = [r.get("tokens") for r in runs]
        if token_values and all(t is not None for t in token_values):
            token_stat = calculate_stats(token_values)
        else:
            token_stat = None

        run_summary[config] = {
            "pass_rate": calculate_stats(pass_rates),
            "time_seconds": calculate_stats(times),
            "tokens": token_stat,
        }

    # Determine primary (with-skill/new) vs. baseline (without-skill/old) by
    # known name, not by dict/alphabetical order — see pick_primary_and_baseline.
    primary_name, baseline_name = pick_primary_and_baseline(configs)
    primary = run_summary.get(primary_name, {}) if primary_name else {}
    baseline = run_summary.get(baseline_name, {}) if baseline_name else {}

    delta_pass_rate = primary.get("pass_rate", {}).get("mean", 0) - baseline.get("pass_rate", {}).get("mean", 0)
    delta_time = primary.get("time_seconds", {}).get("mean", 0) - baseline.get("time_seconds", {}).get("mean", 0)
    # Token delta only exists when BOTH sides have a real token statistic. If
    # either is None (not measured, or measured in a different currency), there
    # is no comparison to report — "n/a", never a number (N-07).
    primary_tokens = primary.get("tokens")
    baseline_tokens = baseline.get("tokens")
    if isinstance(primary_tokens, dict) and isinstance(baseline_tokens, dict):
        delta_tokens = primary_tokens.get("mean", 0) - baseline_tokens.get("mean", 0)
    else:
        delta_tokens = None

    # Re-key run_summary so primary comes before baseline, regardless of the
    # alphabetical order configs happened to be discovered in. This matters
    # beyond just this function's own return value: benchmark.json serializes
    # this dict as-is, and eval-viewer/viewer.html's Benchmark tab picks its
    # two display columns via `Object.keys(summary)[0]` / `[1]` — i.e. it
    # trusts JSON key order to mean "primary, then baseline". Leaving the
    # dict in alphabetical order here would have fixed the delta *number*
    # (above) but left the browser table's column headers swapped for the
    # same "old_skill" (baseline) vs "with_skill" (primary) case that caused
    # the original bug, since "old_skill" < "with_skill" alphabetically.
    ordered_summary = {}
    for name in (primary_name, baseline_name):
        if name and name in run_summary:
            ordered_summary[name] = run_summary[name]
    for name in configs:
        if name not in ordered_summary:
            ordered_summary[name] = run_summary[name]

    ordered_summary["delta"] = {
        "pass_rate": f"{delta_pass_rate:+.2f}",
        "time_seconds": f"{delta_time:+.1f}",
        "tokens": f"{delta_tokens:+.0f}" if delta_tokens is not None else "n/a",
    }

    return ordered_summary


def generate_benchmark(benchmark_dir: Path, skill_name: str = "",
                       skill_path: str = "", executor_model: str = "",
                       analyzer_model: str = "") -> tuple[dict, dict]:
    """
    Generate complete benchmark.json from run results.

    Returns (benchmark, report). The report is the caller's only way to tell
    "measured zero" from "measured nothing" — see load_run_results.
    """
    results, report = load_run_results(benchmark_dir)
    run_summary = aggregate_results(results)

    # Build runs array for benchmark.json. Order configs primary-first (same
    # resolution as aggregate_results) so the viewer's per-eval breakdown
    # table lists the with-skill/new column before baseline/old, consistent
    # with the summary table above rather than falling back to whatever
    # order the config directories were discovered on disk.
    primary_name, baseline_name = pick_primary_and_baseline(list(results.keys()))
    ordered_configs = [c for c in (primary_name, baseline_name) if c and c in results]
    ordered_configs += [c for c in results if c not in ordered_configs]

    runs = []
    for config in ordered_configs:
        for result in results[config]:
            runs.append({
                "eval_id": result["eval_id"],
                "configuration": config,
                "run_number": result["run_number"],
                "result": {
                    "pass_rate": result["pass_rate"],
                    "passed": result["passed"],
                    "failed": result["failed"],
                    "total": result["total"],
                    "time_seconds": result["time_seconds"],
                    # None ("not measured"), never 0 — a real 0-token run and a
                    # run with no token count must stay distinguishable (N-07).
                    "tokens": result.get("tokens"),
                    # Character count kept as its own field; it is NOT a token
                    # count and never populates `tokens`.
                    "output_chars": result.get("output_chars"),
                    "tool_calls": result.get("tool_calls", 0),
                    "errors": result.get("errors", 0)
                },
                "expectations": result["expectations"],
                "notes": result["notes"]
            })

    # Determine eval IDs from results.
    #
    # Sorted with a type-partitioning key rather than plain `sorted()`: eval_id
    # comes from eval_metadata.json without coercion, so two eval directories
    # where one declares `"eval_id": null` and the other a number used to raise
    # TypeError: '<' not supported between 'int' and 'NoneType' (N-41).
    #
    # This deliberately does NOT coerce or normalise the value. Replacing a
    # non-numeric eval_id with an index here would stop a payload from ever
    # reaching eval-viewer/viewer.html:1133 — which still interpolates
    # metadata.evals_run without escaping — and would make N-02b look fixed
    # while the viewer stays exploitable via a hand-written benchmark.json
    # (SKILL.md:231 explicitly permits writing that file by hand). The escaping
    # belongs in the viewer, not here.
    def _eval_id_key(value):
        if value is None:
            return (0, 0.0, "")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return (2, 0.0, str(value))
        return (1, float(value), "")

    eval_ids = sorted(
        {r["eval_id"] for config in results.values() for r in config},
        key=_eval_id_key,
    )

    # Runs per configuration, MEASURED — not the hardcoded 3 that used to sit
    # here regardless of how many runs were actually aggregated (N-09). A
    # benchmark built from a single run announced "3 runs each per
    # configuration", which reads as triple the statistical weight it has.
    # report["configurations"] maps each discovered config to its usable-run
    # count. When they agree, one integer describes them all; when they differ,
    # `runs_per_configuration` carries the range's low end and the per-config
    # breakdown is spelled out separately so the disagreement is visible.
    per_config = report.get("configurations", {})
    counts = sorted(set(per_config.values()))
    if len(counts) == 1:
        runs_per_configuration = counts[0]
    elif counts:
        runs_per_configuration = counts[0]
    else:
        runs_per_configuration = 0

    # Runs per configuration PER EVAL, also MEASURED — never runs_per_configuration
    # divided by len(evals_run).
    #
    # N-09 fixed the number on the line below; it did not fix the noun that number
    # sits next to. `runs_per_configuration` counts a configuration across ALL evals,
    # but benchmark.md printed it glued to the eval list — "Evals: 1,2,3,4,5 (20 runs
    # each per configuration)" — which reads as 20 runs behind each eval. Measured on
    # a real 40-run benchmark the per-eval figure was 4, so every individual per-eval
    # claim carried five times less weight than the line implied (N-50). Same failure
    # as the "3 runs each" one directly above, one level of granularity down.
    #
    # Division would invent a number whenever the layout is uneven, which is exactly
    # the class of silent wrongness this file exists to refuse. Counting cannot.
    per_eval_counts = sorted({
        len([r for r in runs_of_config if r["eval_id"] == eid])
        for runs_of_config in results.values()
        for eid in {r["eval_id"] for r in runs_of_config}
    })
    runs_per_config_per_eval = per_eval_counts[0] if per_eval_counts else 0
    runs_per_config_per_eval_is_uniform = len(per_eval_counts) <= 1

    # Identity of the measurement, and a complaint when it is missing.
    #
    # All four fields default to "" and none is `required` on the command line, so a
    # benchmark could be produced that does not say what was measured or with which
    # model — and say nothing about it. Two of them used to receive a "<...>" template
    # placeholder: exactly the shape the comment below forbids, applied to the models
    # but not to the skill's own name and path (N-49). Measured on a real 40-run
    # benchmark: `skill_path: "<path/to/skill>"`, both models "unspecified", exit 0,
    # empty stderr — an artifact that looks complete and identifies nothing.
    #
    # Deriving the name from the workspace directory (the way
    # eval-viewer/generate_review.py:498 does) was tried and REJECTED by measurement:
    # on the real run the workspace was literally named "workspace", so derivation
    # would have written "workspace" as the skill name — a plausible-looking wrong
    # answer, which is worse than a visibly absent one.
    #
    # Not `required=True`: a benchmark without identity is still usable, just not
    # reproducible. The right strength is a loud warning with a working output, not a
    # hard refusal that breaks every existing caller.
    identity = {
        "skill_name": (skill_name, "--skill-name"),
        "skill_path": (skill_path, "--skill-path"),
        "executor_model": (executor_model, "--executor-model"),
        "analyzer_model": (analyzer_model, "--analyzer-model"),
    }
    for field, (value, flag) in identity.items():
        if not value:
            report.setdefault("warnings", []).append(
                f"metadata.{field} not supplied ({flag}); recorded as "
                f"\"unspecified\". The benchmark cannot be reproduced from itself "
                f"without it."
            )

    benchmark = {
        "metadata": {
            # One word for all four kinds of not-knowing. "unspecified" is an honest
            # statement of absence; "<skill-name>" looks like a field someone forgot
            # to fill in, and a reader cannot tell the two apart at a glance.
            "skill_name": skill_name or "unspecified",
            "skill_path": skill_path or "unspecified",
            # An unfilled "<model-name>" template silently makes the whole
            # benchmark non-reproducible — you cannot tell which model produced
            # it (N-09). The model is not present anywhere in the run inputs, so
            # it must be supplied by the caller; absent that, say "unspecified"
            # honestly rather than leave a placeholder that looks fillable.
            "executor_model": executor_model or "unspecified",
            "analyzer_model": analyzer_model or "unspecified",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": eval_ids,
            "runs_per_configuration": runs_per_configuration,
            "runs_per_configuration_by_config": per_config,
            "runs_per_config_per_eval": runs_per_config_per_eval,
            "runs_per_config_per_eval_is_uniform": runs_per_config_per_eval_is_uniform,
            # How many runs actually made it into the statistics, and how many
            # were refused. Without these two numbers a shrinking n is
            # invisible: a benchmark built from one surviving run and a
            # benchmark built from nine look identical in the summary table.
            "runs_loaded": report["loaded"],
            "runs_rejected": report["rejected"]
        },
        "runs": runs,
        "run_summary": run_summary,
        # Every file-level problem encountered while loading, verbatim. Carried
        # into the artifact and not only onto stderr, because SKILL.md:238-244
        # prescribes running these scripts with output redirected, where a
        # stderr-only diagnostic reaches nobody.
        "data_quality": list(report["warnings"]),
        "notes": []  # To be filled by analyzer
    }

    return benchmark, report


def generate_markdown(benchmark: dict) -> str:
    """Generate human-readable benchmark.md from benchmark data."""
    metadata = benchmark["metadata"]
    run_summary = benchmark["run_summary"]

    # Determine config names (excluding "delta"). Use the same primary/baseline
    # resolution as aggregate_results() so the table's column order and the
    # delta sign always agree with each other, regardless of alphabetical
    # directory-name order (see pick_primary_and_baseline).
    configs = [k for k in run_summary if k != "delta"]
    primary_name, baseline_name = pick_primary_and_baseline(configs)
    config_a = primary_name or (configs[0] if configs else "config_a")
    config_b = baseline_name or (configs[1] if len(configs) >= 2 else "config_b")
    label_a = config_a.replace("_", " ").title()
    label_b = config_b.replace("_", " ").title()

    # Runs line: every count next to the noun it actually counts.
    #
    # This used to be one parenthesis glued to the eval list, so the
    # per-configuration total read as a per-eval total (N-50). The two numbers now
    # sit on their own line, and the per-eval figure — the one behind each
    # individual eval claim — is stated rather than left to be inferred by division.
    per_config = metadata.get("runs_per_configuration_by_config", {})
    if len(set(per_config.values())) > 1:
        runs_line = ", ".join(f"{c}: n={n}" for c, n in per_config.items())
    else:
        runs_line = f"{metadata['runs_per_configuration']} per configuration"

    n_evals = len(metadata.get("evals_run", []))
    per_eval = metadata.get("runs_per_config_per_eval")
    if per_eval:
        # "at least N" when the evals disagree, because one number that fits none
        # is the defect this line is fixing.
        prefix = "" if metadata.get("runs_per_config_per_eval_is_uniform", True) \
            else "at least "
        runs_line += f" ({prefix}{per_eval} per eval x {n_evals} evals)"

    lines = [
        f"# Skill Benchmark: {metadata['skill_name']}",
        "",
        f"**Model**: {metadata['executor_model']}",
        f"**Date**: {metadata['timestamp']}",
        f"**Evals**: {', '.join(map(str, metadata['evals_run']))}",
        f"**Runs**: {runs_line}",
        "",
        "## Summary",
        "",
        f"| Metric | {label_a} | {label_b} | Delta |",
        "|--------|------------|---------------|-------|",
    ]

    a_summary = run_summary.get(config_a, {})
    b_summary = run_summary.get(config_b, {})
    delta = run_summary.get("delta", {})

    def fmt(stat, *, pct=False, secs=False):
        """One cell. At n=1 the stddev is undefined, so show "(n=1)" instead of
        the misleading "± 0" (N-09). `None` stat (e.g. tokens not measured) is
        an em dash."""
        if not isinstance(stat, dict) or stat.get("n", 0) == 0:
            return "—"
        n = stat["n"]
        mean = stat["mean"]
        if pct:
            body = f"{mean*100:.0f}%"
            spread = f" ± {stat['stddev']*100:.0f}%"
        elif secs:
            body = f"{mean:.1f}s"
            spread = f" ± {stat['stddev']:.1f}s"
        else:
            body = f"{mean:.0f}"
            spread = f" ± {stat['stddev']:.0f}"
        return f"{body}{spread} (n={n})" if n > 1 else f"{body} (n=1)"

    lines.append(f"| Pass Rate | {fmt(a_summary.get('pass_rate'), pct=True)} | {fmt(b_summary.get('pass_rate'), pct=True)} | {delta.get('pass_rate', '—')} |")
    lines.append(f"| Time | {fmt(a_summary.get('time_seconds'), secs=True)} | {fmt(b_summary.get('time_seconds'), secs=True)} | {delta.get('time_seconds', '—')}s |")
    lines.append(f"| Tokens | {fmt(a_summary.get('tokens'))} | {fmt(b_summary.get('tokens'))} | {delta.get('tokens', '—')} |")

    # Data quality section — every run that was refused, and why. Placed before
    # Notes because it qualifies the table above it: a reader who does not know
    # that runs were dropped reads the summary as complete.
    rejected = metadata.get("runs_rejected", 0)
    if rejected or benchmark.get("data_quality"):
        lines.extend([
            "",
            "## Data Quality",
            "",
            f"Runs loaded: {metadata.get('runs_loaded', '?')}. "
            f"Runs refused: {rejected}.",
            ""
        ])
        for problem in benchmark.get("data_quality", []):
            lines.append(f"- {problem}")

    # Notes section
    if benchmark.get("notes"):
        lines.extend([
            "",
            "## Notes",
            ""
        ])
        for note in benchmark["notes"]:
            lines.append(f"- {note}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate benchmark run results into summary statistics"
    )
    parser.add_argument(
        "benchmark_dir",
        type=Path,
        help="Path to the benchmark directory"
    )
    parser.add_argument(
        "--skill-name",
        default="",
        help="Name of the skill being benchmarked"
    )
    parser.add_argument(
        "--skill-path",
        default="",
        help="Path to the skill being benchmarked"
    )
    parser.add_argument(
        "--executor-model",
        default="",
        help="Model that produced the runs (recorded in metadata for "
             "reproducibility; the run inputs do not carry it)"
    )
    parser.add_argument(
        "--analyzer-model",
        default="",
        help="Model used by the analyzer/grader (recorded in metadata)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output path for benchmark.json (default: <benchmark_dir>/benchmark.json)"
    )

    args = parser.parse_args()

    if not args.benchmark_dir.exists():
        print(f"Directory not found: {args.benchmark_dir}", file=sys.stderr)
        sys.exit(EXIT_USAGE)

    # Generate benchmark
    benchmark, report = generate_benchmark(args.benchmark_dir, args.skill_name,
                                           args.skill_path, args.executor_model,
                                           args.analyzer_model)

    # Diagnostics go to stderr so `... | jq` on stdout keeps working.
    for problem in report["warnings"]:
        print(f"Warning: {problem}", file=sys.stderr)

    # Fail loud when nothing was measured.
    #
    # This is the whole point of the ticket. Previously zero loaded runs still
    # produced a complete-looking benchmark.json and benchmark.md — "0% ± 0%"
    # in both columns and a "+0.00" delta — and exited 0. A skill that scored
    # 100% against a 0% baseline was reported as no improvement, and nothing in
    # the output said the aggregation had read nothing at all.
    if report["loaded"] == 0:
        print(f"Error: no usable runs found under {args.benchmark_dir}.",
              file=sys.stderr)
        if report["searched"]:
            print("  Eval directories searched:", file=sys.stderr)
            for path in report["searched"]:
                print(f"    {path}", file=sys.stderr)
            print("  Expected, per configuration directory, either "
                  "run-<N>/grading.json or grading.json directly.",
                  file=sys.stderr)
        print(f"  Runs refused: {report['rejected']}. "
              f"No benchmark.json or benchmark.md was written.", file=sys.stderr)
        sys.exit(EXIT_NO_DATA)

    # Same failure one level down: a configuration that was found on disk but
    # whose every run was refused ends up with an empty list, and
    # aggregate_results fills it with the all-zeros block — so the table shows
    # "0% ± 0%" for a configuration that was never measured, and the delta is
    # computed against that fabricated zero. A benchmark compares two
    # configurations; if one of them has no data there is no comparison to
    # report, so refuse to write a half-benchmark rather than a misleading one.
    unmeasured = sorted(c for c, n in report["configurations"].items() if n == 0)
    if unmeasured:
        print(f"Error: no usable runs for configuration(s): "
              f"{', '.join(unmeasured)}.", file=sys.stderr)
        print("  These directories exist but every run in them was refused - "
              "see the warnings above.", file=sys.stderr)
        print("  Reporting them as 0% would be indistinguishable from a "
              "measured zero, so no benchmark.json or benchmark.md was "
              "written.", file=sys.stderr)
        sys.exit(EXIT_NO_DATA)

    # Determine output paths
    output_json = args.output or (args.benchmark_dir / "benchmark.json")
    output_md = output_json.with_suffix(".md")

    # Write benchmark.json
    with open(output_json, "w") as f:
        json.dump(benchmark, f, indent=2)
    print(f"Generated: {output_json}")

    # Write benchmark.md
    markdown = generate_markdown(benchmark)
    with open(output_md, "w") as f:
        f.write(markdown)
    print(f"Generated: {output_md}")

    # Print summary
    run_summary = benchmark["run_summary"]
    configs = [k for k in run_summary if k != "delta"]
    delta = run_summary.get("delta", {})

    print(f"\nSummary:")
    for config in configs:
        pr = run_summary[config]["pass_rate"]["mean"]
        label = config.replace("_", " ").title()
        print(f"  {label}: {pr*100:.1f}% pass rate")
    print(f"  Delta:         {delta.get('pass_rate', '—')}")


if __name__ == "__main__":
    main()
