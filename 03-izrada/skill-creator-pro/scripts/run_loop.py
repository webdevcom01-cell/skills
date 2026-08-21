#!/usr/bin/env python3
# Modified from anthropics/skills@b29e7cf6 (skills/skill-creator) by
# buky <webdevcom01@gmail.com>, 2026-07-30. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md.
"""Run the eval + improve loop until all pass or max iterations reached.

Combines run_eval.py and improve_description.py in a loop, tracking history
and returning the best description found. Supports train/test split to prevent
overfitting.
"""

import argparse
import json
import random
import sys
import tempfile
import time
import webbrowser
from pathlib import Path

from scripts.generate_report import generate_html
from scripts.improve_description import improve_description
from scripts.run_eval import find_project_root, run_eval
from scripts.utils import parse_skill_md, load_json_arg


# Ceiling on `claude -p` processes for one run, enforced before the first call.
#
# Derived, not picked: the documented invocation (20 queries, 3 runs per query,
# 5 iterations) plans 304-308 processes, so 500 clears the documented path with
# room for a larger eval set while still catching the accidents that motivate a
# limit at all — `--runs-per-query 10 --max-iterations 20` plans over 4000.
# `--max-calls 0` turns the limit off for someone who means it.
DEFAULT_MAX_CALLS = 500


def plan_calls(n_queries: int, runs_per_query: int, max_iterations: int) -> dict:
    """How many `claude -p` processes this configuration will start.

    Exact, not an estimate, and derived from the loop's own structure:

      eval      n_queries x runs_per_query, once per iteration
      improve   once per iteration EXCEPT the last — run_loop breaks out before
                the rewrite on the final iteration, so it is max_iterations - 1
      retries   improve_description retries once when the rewritten description
                comes back over the 1024-character limit, so at most one extra
                per rewrite

    `improve_retries` is a worst case and is reported as such; the others are
    what will run.
    """
    evals = n_queries * runs_per_query * max_iterations
    improve = max(0, max_iterations - 1)
    return {
        "eval": evals,
        "improve": improve,
        "improve_retries": improve,
        "total": evals + improve + improve,
    }


def dedupe_by_query(eval_set: list[dict]) -> tuple[list[dict], list[str]]:
    """Collapse repeated query texts to their first occurrence.

    A query that appears more than once is a data error, not a signal: it used
    to be sent into BOTH the train and the test split (the test filter matches
    by query text, so a duplicate lands wherever its first copy did and the
    holdout is no longer held out), AND it got double weight because run_eval
    aggregates by query text. Both facets are N-36. Deduping here — before the
    split — makes the split disjoint and the reported sizes match the number of
    queries actually measured. A dropped duplicate that carried a *different*
    should_trigger is flagged, since that is a contradictory label, not a
    harmless repeat.
    """
    seen: dict[str, dict] = {}
    warnings: list[str] = []
    deduped: list[dict] = []
    for item in eval_set:
        q = item["query"]
        if q not in seen:
            seen[q] = item
            deduped.append(item)
        elif seen[q].get("should_trigger") != item.get("should_trigger"):
            warnings.append(
                f"duplicate query with a conflicting should_trigger kept as "
                f"{seen[q].get('should_trigger')!r}, dropped {item.get('should_trigger')!r}: "
                f"{q[:60]!r}")
        else:
            warnings.append(f"duplicate query dropped: {q[:60]!r}")
    return deduped, warnings


def split_eval_set(eval_set: list[dict], holdout: float, seed: int = 42) -> tuple[list[dict], list[dict]]:
    """Split eval set into train and test sets, stratified by should_trigger.

    Deduplicates first (N-36): with duplicates present the two halves could
    share a query, which defeats the point of a held-out set.
    """
    random.seed(seed)

    eval_set, _ = dedupe_by_query(eval_set)

    # Separate by should_trigger
    trigger = [e for e in eval_set if e["should_trigger"]]
    no_trigger = [e for e in eval_set if not e["should_trigger"]]

    # Shuffle each group
    random.shuffle(trigger)
    random.shuffle(no_trigger)

    # Calculate split points
    n_trigger_test = max(1, int(len(trigger) * holdout))
    n_no_trigger_test = max(1, int(len(no_trigger) * holdout))

    # Split
    test_set = trigger[:n_trigger_test] + no_trigger[:n_no_trigger_test]
    train_set = trigger[n_trigger_test:] + no_trigger[n_no_trigger_test:]

    return train_set, test_set


def run_loop(
    eval_set: list[dict],
    skill_path: Path,
    description_override: str | None,
    num_workers: int,
    timeout: int,
    max_iterations: int,
    runs_per_query: int,
    trigger_threshold: float,
    holdout: float,
    model: str,
    verbose: bool,
    live_report_path: Path | None = None,
    log_dir: Path | None = None,
    max_calls: int = DEFAULT_MAX_CALLS,
    cost_per_call: float | None = None,
    refresh_seconds: int = 0,
) -> dict:
    """Run the eval + improvement loop."""
    # argparse accepts --max-iterations 0 (type=int has no minimum), but zero
    # iterations means the loop body never runs, `history` stays empty, and the
    # `max(history, ...)` that picks the best iteration raises
    # "ValueError: max() arg is an empty sequence" — a crash with no output after
    # possibly a lot of paid eval calls. Refuse the degenerate value up front with
    # a clear reason (main turns this into a clean non-zero exit) (N-40).
    if max_iterations < 1:
        raise ValueError(
            f"max_iterations must be at least 1, got {max_iterations}; "
            f"nothing would be optimized.")

    project_root = find_project_root()
    name, original_description, content = parse_skill_md(skill_path)
    current_description = description_override or original_description

    # Dedupe once up front so both the holdout and the no-holdout paths, and the
    # reported set sizes, all rest on the same unique-query set (N-36).
    eval_set, dedupe_warnings = dedupe_by_query(eval_set)
    for w in dedupe_warnings:
        print(f"Warning: {w}", file=sys.stderr)

    # ---- Pre-flight: say what this will spend, BEFORE spending any of it -----
    #
    # The defaults here start 300+ `claude -p` processes and nothing said so.
    # Deduping happens above, so the count below is over the set that will
    # actually run, not the one that was passed in.
    plan = plan_calls(len(eval_set), runs_per_query, max_iterations)
    print(
        f"Plan: up to {plan['total']} `claude -p` processes "
        f"({plan['eval']} eval = {len(eval_set)} queries x {runs_per_query} runs "
        f"x {max_iterations} iterations, "
        f"+{plan['improve']} description rewrites, "
        f"+ up to {plan['improve_retries']} rewrite retries). "
        f"Fewer if every train query passes before the last iteration — the loop "
        f"stops there.",
        file=sys.stderr)

    # Money is deliberately NOT invented. There is no per-call price anywhere in
    # this repo, and the real one depends on the model, the plan and the context
    # length. Printing a plausible number would be the same defect this codebase
    # warns about elsewhere: a value that looks filled in but was made up. So the
    # count is always shown (it is exact) and the currency only when the caller
    # supplies the rate they are actually on.
    if cost_per_call is not None:
        print(f"       at {cost_per_call} per call that is about "
              f"${plan['total'] * cost_per_call:.2f} "
              f"(your rate, not a measured or promised price).",
              file=sys.stderr)

    if max_calls and plan["total"] > max_calls:
        raise ValueError(
            f"planned {plan['total']} `claude -p` processes, over the "
            f"--max-calls limit of {max_calls}; nothing was run and nothing was "
            f"spent. Lower --max-iterations ({max_iterations}), "
            f"--runs-per-query ({runs_per_query}) or the eval set "
            f"({len(eval_set)} queries), or raise --max-calls "
            f"(--max-calls 0 disables the limit).")

    # Split into train/test if holdout > 0
    if holdout > 0:
        train_set, test_set = split_eval_set(eval_set, holdout)
        if verbose:
            print(f"Split: {len(train_set)} train, {len(test_set)} test (holdout={holdout})", file=sys.stderr)
    else:
        train_set = eval_set
        test_set = []

    # A holdout that leaves nothing to train on is not a valid run: with an empty
    # train set, `train_summary["failed"]` is 0 of 0, and the loop below would
    # report exit_reason "all_passed" without having measured anything (N-35).
    # Refuse loudly instead of producing that false green. (Reachable with a tiny
    # eval set, e.g. one positive + one negative and any holdout > 0, where each
    # class contributes its single member to the test split.)
    if not train_set:
        raise ValueError(
            f"eval set too small to hold out: the train set is empty "
            f"(holdout={holdout} sent every query to the test split). "
            f"Lower --holdout or add more eval cases so training has data.")

    # Train that is missing a whole class cannot teach the optimizer that side of
    # the decision. Most often this is the negative class disappearing (a single
    # negative example is entirely consumed by the test split), which lets the
    # description drift toward over-triggering unchecked. Proceed, but say so —
    # on stderr, since the documented invocation runs in the background (N-35).
    eval_polarities = {bool(e["should_trigger"]) for e in eval_set}
    train_polarities = {bool(e["should_trigger"]) for e in train_set}
    for polarity in eval_polarities - train_polarities:
        kind = "positive (should_trigger=True)" if polarity else "negative (should_trigger=False)"
        print(f"Warning: train set has no {kind} examples — the optimizer cannot "
              f"learn that side and may drift (N-35). Add more eval cases or lower "
              f"--holdout.", file=sys.stderr)

    history = []
    exit_reason = "unknown"
    runs_lost = 0
    runs_attempted = 0

    for iteration in range(1, max_iterations + 1):
        if verbose:
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"Iteration {iteration}/{max_iterations}", file=sys.stderr)
            print(f"Description: {current_description}", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)

        # Evaluate train + test together in one batch for parallelism
        all_queries = train_set + test_set
        t0 = time.time()
        all_results = run_eval(
            eval_set=all_queries,
            skill_name=name,
            description=current_description,
            num_workers=num_workers,
            timeout=timeout,
            project_root=project_root,
            runs_per_query=runs_per_query,
            trigger_threshold=trigger_threshold,
            model=model,
        )
        eval_elapsed = time.time() - t0

        # Split results back into train/test by matching queries
        train_queries_set = {q["query"] for q in train_set}
        # Runs that errored out are paid for if they reached the model, and their
        # evidence is thrown away. run_eval catches per-run exceptions, counts
        # them and moves on — which is right, but it made the loss invisible: a
        # rate-limit burst across 10 workers silently shrinks the sample the
        # winning description is chosen on. Accumulate it and say so at the end.
        runs_lost += sum(r.get("errors", 0) for r in all_results["results"])
        runs_attempted += sum(r.get("runs", 0) + r.get("errors", 0)
                              for r in all_results["results"])

        train_result_list = [r for r in all_results["results"] if r["query"] in train_queries_set]
        test_result_list = [r for r in all_results["results"] if r["query"] not in train_queries_set]

        train_passed = sum(1 for r in train_result_list if r["pass"])
        train_total = len(train_result_list)
        train_summary = {"passed": train_passed, "failed": train_total - train_passed, "total": train_total}
        train_results = {"results": train_result_list, "summary": train_summary}

        if test_set:
            test_passed = sum(1 for r in test_result_list if r["pass"])
            test_total = len(test_result_list)
            test_summary = {"passed": test_passed, "failed": test_total - test_passed, "total": test_total}
            test_results = {"results": test_result_list, "summary": test_summary}
        else:
            test_results = None
            test_summary = None

        history.append({
            "iteration": iteration,
            "description": current_description,
            "train_passed": train_summary["passed"],
            "train_failed": train_summary["failed"],
            "train_total": train_summary["total"],
            "train_results": train_results["results"],
            "test_passed": test_summary["passed"] if test_summary else None,
            "test_failed": test_summary["failed"] if test_summary else None,
            "test_total": test_summary["total"] if test_summary else None,
            "test_results": test_results["results"] if test_results else None,
            # For backward compat with report generator
            "passed": train_summary["passed"],
            "failed": train_summary["failed"],
            "total": train_summary["total"],
            "results": train_results["results"],
        })

        # Write live report if path provided
        if live_report_path:
            partial_output = {
                "original_description": original_description,
                "best_description": current_description,
                "best_score": "in progress",
                "iterations_run": len(history),
                "holdout": holdout,
                "train_size": len(train_set),
                "test_size": len(test_set),
                "history": history,
            }
            live_report_path.write_text(generate_html(
                partial_output, skill_name=name, refresh_seconds=refresh_seconds))

        if verbose:
            def print_eval_stats(label, results, elapsed):
                pos = [r for r in results if r["should_trigger"]]
                neg = [r for r in results if not r["should_trigger"]]
                tp = sum(r["triggers"] for r in pos)
                pos_runs = sum(r["runs"] for r in pos)
                fn = pos_runs - tp
                fp = sum(r["triggers"] for r in neg)
                neg_runs = sum(r["runs"] for r in neg)
                tn = neg_runs - fp
                total = tp + tn + fp + fn
                precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
                accuracy = (tp + tn) / total if total > 0 else 0.0
                # Queries whose every run errored contribute 0 runs, so they
                # vanish from tp/fp/fn/tn — and when they dominate, the line reads
                # "0/0 correct, precision=100% recall=100%", which is the same
                # uncertainty-discarding as the HTML report (N-14). Surface the
                # inconclusive count so that reassuring precision/recall is not
                # read as a real measurement.
                inconclusive = sum(1 for r in results if r.get("inconclusive"))
                errored = sum(r.get("errors", 0) for r in results)
                inconclusive_note = (
                    f", {inconclusive} inconclusive ({errored} errored runs)"
                    if inconclusive else "")
                print(f"{label}: {tp+tn}/{total} correct, precision={precision:.0%} recall={recall:.0%} accuracy={accuracy:.0%}{inconclusive_note} ({elapsed:.1f}s)", file=sys.stderr)
                for r in results:
                    status = "PASS" if r["pass"] else "FAIL"
                    rate_str = f"{r['triggers']}/{r['runs']}"
                    print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:60]}", file=sys.stderr)

            print_eval_stats("Train", train_results["results"], eval_elapsed)
            if test_summary:
                print_eval_stats("Test ", test_results["results"], 0)

        if train_summary["failed"] == 0:
            exit_reason = f"all_passed (iteration {iteration})"
            if verbose:
                print(f"\nAll train queries passed on iteration {iteration}!", file=sys.stderr)
            break

        if iteration == max_iterations:
            exit_reason = f"max_iterations ({max_iterations})"
            if verbose:
                print(f"\nMax iterations reached ({max_iterations}).", file=sys.stderr)
            break

        # Improve the description based on train results
        if verbose:
            print(f"\nImproving description...", file=sys.stderr)

        t0 = time.time()
        # Strip test scores from history so improvement model can't see them
        blinded_history = [
            {k: v for k, v in h.items() if not k.startswith("test_")}
            for h in history
        ]
        # The rewrite is a paid network call and it can fail: improve_description
        # runs `claude -p` with timeout=300, whose TimeoutExpired used to
        # propagate all the way out of run_loop. A failure in iteration 3 of 5
        # then took the whole run down, and since results.json is only written
        # after the loop returns, everything measured in iterations 1-2 never
        # reached machine-readable output — paid for, and gone (N-21d).
        #
        # The except is scoped to this one call, not the loop body: a wider one
        # would swallow failures that should be seen. The reason is named in
        # exit_reason, so the run ends with "the rewrite timed out" rather than
        # with silence.
        try:
            new_description = improve_description(
                skill_name=name,
                skill_content=content,
                current_description=current_description,
                eval_results=train_results,
                history=blinded_history,
                model=model,
                log_dir=log_dir,
                iteration=iteration,
            )
        except Exception as e:
            exit_reason = (f"improve_description failed on iteration {iteration}: "
                           f"{type(e).__name__}: {e}")
            print(f"Error: {exit_reason}. Stopping here and keeping the "
                  f"{len(history)} iteration(s) already measured.",
                  file=sys.stderr)
            break
        improve_elapsed = time.time() - t0

        if verbose:
            print(f"Proposed ({improve_elapsed:.1f}s): {new_description}", file=sys.stderr)

        current_description = new_description

    # Find the best iteration by TEST score (or train if no test set)
    if test_set:
        best = max(history, key=lambda h: h["test_passed"] or 0)
        best_score = f"{best['test_passed']}/{best['test_total']}"
    else:
        best = max(history, key=lambda h: h["train_passed"])
        best_score = f"{best['train_passed']}/{best['train_total']}"

    if verbose:
        print(f"\nExit reason: {exit_reason}", file=sys.stderr)
        print(f"Best score: {best_score} (iteration {best['iteration']})", file=sys.stderr)

    # Always reported, not only under --verbose: the documented invocation runs in
    # the background with stderr redirected, and a loss that only shows up in
    # verbose output is a loss nobody sees.
    if runs_lost:
        share = (runs_lost / runs_attempted * 100) if runs_attempted else 0.0
        print(f"Lost {runs_lost} of {runs_attempted} runs to errors "
              f"({share:.0f}%). Those runs were paid for if they reached the "
              f"model, and their evidence is gone -- the description was chosen "
              f"on the runs that survived. There is no retry: see the known "
              f"limitation in SKILL.md.", file=sys.stderr)

    return {
        "exit_reason": exit_reason,
        "original_description": original_description,
        "best_description": best["description"],
        "best_score": best_score,
        "best_train_score": f"{best['train_passed']}/{best['train_total']}",
        "best_test_score": f"{best['test_passed']}/{best['test_total']}" if test_set else None,
        "final_description": current_description,
        "iterations_run": len(history),
        "holdout": holdout,
        "train_size": len(train_set),
        "test_size": len(test_set),
        "runs_lost_to_errors": runs_lost,
        "runs_attempted": runs_attempted,
        "planned_calls": plan,
        "history": history,
    }


def main():
    parser = argparse.ArgumentParser(description="Run eval + improve loop")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override starting description")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max improvement iterations")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--holdout", type=float, default=0.4, help="Fraction of eval set to hold out for testing (0 to disable)")
    parser.add_argument("--model", required=True, help="Model for improvement")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    parser.add_argument("--report", default="auto", help="Generate HTML report at this path (default: 'auto' for temp file, 'none' to disable)")
    parser.add_argument("--results-dir", default=None, help="Save all outputs (results.json, report.html, log.txt) to a timestamped subdirectory here")
    parser.add_argument("--report-refresh", type=int, default=0, metavar="SECONDS",
                        help="Reload the live report every N seconds while the "
                             "loop runs. Off by default: a page that reloads "
                             "under you loses scroll position and selection "
                             "mid-comparison. Pass e.g. 15 if you want to watch "
                             "it, and reload by hand otherwise.")
    parser.add_argument("--max-calls", type=int, default=DEFAULT_MAX_CALLS,
                        help=f"Refuse to start if the run would exceed this many "
                             f"`claude -p` processes (default {DEFAULT_MAX_CALLS}; "
                             f"0 disables). The planned count is printed before "
                             f"anything is spent.")
    parser.add_argument("--cost-per-call", type=float, default=None,
                        help="Your price per `claude -p` call, used only to turn "
                             "the planned call count into a rough total. There is "
                             "no default on purpose: the real rate depends on your "
                             "model, plan and context length, and a made-up number "
                             "here would read as measured. For scale, 0.108-0.197 "
                             "was observed in one sandbox with 148 slash commands "
                             "loaded; yours will differ.")
    args = parser.parse_args()

    eval_set = load_json_arg(args.eval_set, what="eval set")
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, _, _ = parse_skill_md(skill_path)

    # Set up live report path
    if args.report != "none":
        if args.report == "auto":
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            live_report_path = Path(tempfile.gettempdir()) / f"skill_description_report_{skill_path.name}_{timestamp}.html"
        else:
            live_report_path = Path(args.report)
        # Open the report immediately so the user can watch
        # No forced refresh here either: the placeholder used to reload every 5s
        # regardless, so even the "nothing has happened yet" page moved under the
        # reader (N-16). It refreshes only if the caller asked for a period.
        _osvezi = (f"<meta http-equiv='refresh' content='{args.report_refresh}'>"
                   if args.report_refresh > 0 else "")
        live_report_path.write_text(
            "<html lang='en'><body><h1>Starting optimization loop...</h1>"
            + _osvezi + "</body></html>")
        webbrowser.open(str(live_report_path))
    else:
        live_report_path = None

    # Determine output directory (create before run_loop so logs can be written)
    if args.results_dir:
        timestamp = time.strftime("%Y-%m-%d_%H%M%S")
        results_dir = Path(args.results_dir) / timestamp
        results_dir.mkdir(parents=True, exist_ok=True)
    else:
        results_dir = None

    log_dir = results_dir / "logs" if results_dir else None

    try:
        output = run_loop(
            eval_set=eval_set,
            skill_path=skill_path,
            description_override=args.description,
            num_workers=args.num_workers,
            timeout=args.timeout,
            max_iterations=args.max_iterations,
            runs_per_query=args.runs_per_query,
            trigger_threshold=args.trigger_threshold,
            holdout=args.holdout,
            model=args.model,
            verbose=args.verbose,
            live_report_path=live_report_path,
            log_dir=log_dir,
            max_calls=args.max_calls,
            cost_per_call=args.cost_per_call,
            refresh_seconds=args.report_refresh,
        )
    except ValueError as e:
        # Degenerate configuration (e.g. empty train set, N-35) — report the
        # reason on stderr and exit non-zero rather than crash with a traceback.
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Save JSON output
    json_output = json.dumps(output, indent=2)
    print(json_output)
    if results_dir:
        (results_dir / "results.json").write_text(json_output)

    # Write final HTML report (without auto-refresh)
    if live_report_path:
        live_report_path.write_text(generate_html(output, auto_refresh=False, skill_name=name))
        print(f"\nReport: {live_report_path}", file=sys.stderr)

    if results_dir and live_report_path:
        (results_dir / "report.html").write_text(generate_html(output, auto_refresh=False, skill_name=name))

    if results_dir:
        print(f"Results saved to: {results_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
