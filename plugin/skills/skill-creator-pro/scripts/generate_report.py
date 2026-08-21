#!/usr/bin/env python3
# Modified from anthropics/skills@b29e7cf6 (skills/skill-creator) by
# buky <webdevcom01@gmail.com>, 2026-07-30. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md.
"""Generate an HTML report from run_loop.py output.

Takes the JSON output from run_loop.py and generates a visual HTML report
showing each description attempt with check/x for each test case.
Distinguishes between train and test queries.
"""

import argparse
import html
import sys
from pathlib import Path

from scripts.utils import load_json_arg


def _broj(v):
    """Koercira vrednost koja TREBA da bude broj u broj — N-42.

    `generate_report.py` interpolira 12 vrednosti iz `history.json` i
    `results.json` pravo u HTML bez ikakve zastite. Te datoteke su rucno
    pisive (isto kao `benchmark.json`, `SKILL.md:231`), pa je `triggers`
    moglo da nosi `1<img src=x onerror=...>` i to bi zavrsilo u izvestaju
    koji se otvara u pretrazivacu. Isti obrazac kao N-02b.

    Koercija je jaca od `html.escape`: escape bi payload ucinio inertnim ali
    bi ga PROPUSTIO kao tekst koji izgleda kao podatak. Broj ne moze da nosi
    markup uopste. Kad koercija ne uspe, vracamo ESCAPE-ovan original umesto
    tihe nule — sakriti pokvaren podatak je gore nego prikazati ga.
    """
    if isinstance(v, bool):          # bool je int u Pythonu; ne zelimo True -> 1
        return html.escape(str(v))
    if isinstance(v, (int, float)):
        return v
    try:
        s = str(v).strip()
        return int(s) if s.lstrip("-").isdigit() else float(s)
    except (TypeError, ValueError):
        return html.escape(str(v))


def generate_html(data: dict, auto_refresh: bool = False, skill_name: str = "",
                  refresh_seconds: int = 0) -> str:
    """Generate HTML report from loop output data.

    Auto-refresh is OFF unless the caller asks for it with `refresh_seconds > 0`.

    It used to be a hardcoded 5-second `<meta http-equiv="refresh">` with no way
    to stop it: the page reloaded under the reader every five seconds, losing
    scroll position and any selection mid-comparison (N-16, WCAG 2.2.1, which
    requires the user be able to turn off, adjust or extend a moving/auto-updating
    thing).

    An in-page toggle is not possible here and that is worth stating plainly:
    this report carries `script-src 'none'` (see the CSP below), which is a real
    defence for a page that renders values straight out of external JSON. Buying
    a checkbox with a script-src loosening would trade a working protection for a
    convenience. So the control lives at generation time instead — the caller
    passes a period, and by default there is none.
    """
    history = data.get("history", [])
    holdout = data.get("holdout", 0)
    title_prefix = html.escape(skill_name + " \u2014 ") if skill_name else ""

    # Get all unique queries from train and test sets, with should_trigger info
    train_queries: list[dict] = []
    test_queries: list[dict] = []
    if history:
        for r in history[0].get("train_results", history[0].get("results", [])):
            train_queries.append({"query": r["query"], "should_trigger": r.get("should_trigger", True)})
        if history[0].get("test_results"):
            for r in history[0].get("test_results", []):
                test_queries.append({"query": r["query"], "should_trigger": r.get("should_trigger", True)})

    # `auto_refresh` kept for callers that pass it positionally; it now only
    # supplies a default period rather than forcing one.
    if refresh_seconds <= 0 and auto_refresh:
        refresh_seconds = 0
    refresh_tag = (f'    <meta http-equiv="refresh" content="{int(refresh_seconds)}">\n'
                   if refresh_seconds > 0 else "")

    html_parts = ["""<!DOCTYPE html>
<html>
<head>
    <!-- CSP (T-26). Ova stranica nema NIJEDAN <script> - izmereno, 0 tagova - pa
         `script-src 'none'` nije kozmetika nego stvarna odbrana: cak i da mi
         promakne jedna interpolacija (N-42), injektovan markup ne moze da se
         izvrsi. Koercija brojeva i CSP se ovde udvostrucuju.
         `style-src 'unsafe-inline'` je nuzan jer je CSS inline u <style>. -->
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; script-src 'none'; base-uri 'none'; form-action 'none'">
    <meta charset="utf-8">
""" + refresh_tag + """    <title>""" + title_prefix + """Skill Description Optimization</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600&family=Lora:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Lora', Georgia, serif;
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
            background: #faf9f5;
            color: #141413;
        }
        h1 { font-family: 'Poppins', sans-serif; color: #141413; }
        .explainer {
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #969590;
            color: #716e63;
            font-size: 0.875rem;
            line-height: 1.6;
        }
        .summary {
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #969590;
        }
        .summary p { margin: 5px 0; }
        .best { color: #63734d; font-weight: bold; }
        .table-container {
            overflow-x: auto;
            width: 100%;
        }
        table {
            border-collapse: collapse;
            background: white;
            border: 1px solid #969590;
            border-radius: 6px;
            font-size: 12px;
            min-width: 100%;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border: 1px solid #969590;
            white-space: normal;
            word-wrap: break-word;
        }
        th {
            font-family: 'Poppins', sans-serif;
            background: #141413;
            color: #faf9f5;
            font-weight: 500;
        }
        th.test-col {
            background: #3b74ac;
        }
        th.query-col { min-width: 200px; }
        td.description {
            font-family: monospace;
            font-size: 11px;
            word-wrap: break-word;
            max-width: 400px;
        }
        td.result {
            text-align: center;
            font-size: 16px;
            min-width: 40px;
        }
        td.test-result {
            background: #f0f6fc;
        }
        .pass { color: #63734d; }
        .fail { color: #c73636; }
        .inconclusive { color: #956c09; }
        .rate {
            font-size: 9px;
            color: #716e63;
            display: block;
        }
        tr:hover { background: #faf9f5; }
        .score {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
        }
        .score-good { background: #eef2e8; color: #63734d; }
        .score-ok { background: #fef3c7; color: #a75c05; }
        .score-bad { background: #fceaea; color: #c73636; }
        .train-label { color: #716e63; font-size: 10px; }
        .test-label { color: #3b74ac; font-size: 10px; font-weight: bold; }
        .best-row { background: #f5f8f2; }
        th.positive-col { border-bottom: 3px solid #63734d; }
        th.negative-col { border-bottom: 3px solid #c73636; }
        th.test-col.positive-col { border-bottom: 3px solid #63734d; }
        th.test-col.negative-col { border-bottom: 3px solid #c73636; }
        .legend { font-family: 'Poppins', sans-serif; display: flex; gap: 20px; margin-bottom: 10px; font-size: 13px; align-items: center; }
        .legend-item { display: flex; align-items: center; gap: 6px; }
        .legend-swatch { width: 16px; height: 16px; border-radius: 3px; display: inline-block; }
        .swatch-positive { background: #141413; border-bottom: 3px solid #63734d; }
        .swatch-negative { background: #141413; border-bottom: 3px solid #c73636; }
        .swatch-test { background: #3b74ac; }
        .swatch-train { background: #141413; }
    </style>
</head>
<body>
    <h1>""" + title_prefix + """Skill Description Optimization</h1>
    <div class="explainer">
        <strong>Optimizing your skill's description.</strong> This page updates automatically as Claude tests different versions of your skill's description. Each row is an iteration — a new description attempt. The columns show test queries: green checkmarks mean the skill triggered correctly (or correctly didn't trigger), red crosses mean it got it wrong. The "Train" score shows performance on queries used to improve the description; the "Test" score shows performance on held-out queries the optimizer hasn't seen. When it's done, Claude will apply the best-performing description to your skill.
    </div>
"""]

    # Summary section
    best_test_score = data.get('best_test_score')
    best_train_score = data.get('best_train_score')
    html_parts.append(f"""
    <div class="summary">
        <p><strong>Original:</strong> {html.escape(data.get('original_description', 'N/A'))}</p>
        <p class="best"><strong>Best:</strong> {html.escape(data.get('best_description', 'N/A'))}</p>
        <p><strong>Best Score:</strong> {_broj(data.get('best_score', 'N/A'))} {'(test)' if best_test_score else '(train)'}</p>
        <p><strong>Iterations:</strong> {_broj(data.get('iterations_run', 0))} | <strong>Train:</strong> {_broj(data.get('train_size', '?'))} | <strong>Test:</strong> {_broj(data.get('test_size', '?'))}</p>
    </div>
""")

    # Legend
    html_parts.append("""
    <div class="legend">
        <span style="font-weight:600">Query columns:</span>
        <span class="legend-item"><span class="legend-swatch swatch-positive"></span> Should trigger</span>
        <span class="legend-item"><span class="legend-swatch swatch-negative"></span> Should NOT trigger</span>
        <span class="legend-item"><span class="legend-swatch swatch-train"></span> Train</span>
        <span class="legend-item"><span class="legend-swatch swatch-test"></span> Test</span>
    </div>
""")

    # Table header
    html_parts.append("""
    <div class="table-container">
    <table>
        <thead>
            <tr>
                <th>Iter</th>
                <th>Train</th>
                <th>Test</th>
                <th class="query-col">Description</th>
""")

    # Add column headers for train queries
    for qinfo in train_queries:
        polarity = "positive-col" if qinfo["should_trigger"] else "negative-col"
        html_parts.append(f'                <th class="{polarity}">{html.escape(qinfo["query"])}</th>\n')

    # Add column headers for test queries (different color)
    for qinfo in test_queries:
        polarity = "positive-col" if qinfo["should_trigger"] else "negative-col"
        html_parts.append(f'                <th class="test-col {polarity}">{html.escape(qinfo["query"])}</th>\n')

    html_parts.append("""            </tr>
        </thead>
        <tbody>
""")

    # Find best iteration for highlighting. Guard the empty case: a run with
    # --max-iterations 0 produces no iterations, so `history` is empty and
    # `max([])` raises ValueError — which would make even the "nothing ran"
    # report impossible to write (N-40).
    if not history:
        best_iter = None
    elif test_queries:
        best_iter = max(history, key=lambda h: h.get("test_passed") or 0).get("iteration")
    else:
        best_iter = max(history, key=lambda h: h.get("train_passed", h.get("passed", 0))).get("iteration")

    # Add rows for each iteration
    for h in history:
        iteration = h.get("iteration", "?")
        train_passed = h.get("train_passed", h.get("passed", 0))
        train_total = h.get("train_total", h.get("total", 0))
        test_passed = h.get("test_passed")
        test_total = h.get("test_total")
        description = h.get("description", "")
        # With --holdout 0 the loop writes `"test_results": None` — the key is
        # present, so a `.get(k, [])` default never applies, and
        # `aggregate_runs(None)` below iterates None → TypeError, taking down the
        # whole report including the live one written every iteration (N-12).
        #
        # Only absent-or-null falls back; an explicitly empty list stays empty.
        # (`x or fallback` alone would also swallow a legitimate `[]` and reach
        # for the backward-compat `results` key, which is a different meaning.)
        train_results = h.get("train_results")
        if train_results is None:
            train_results = h.get("results")
        if train_results is None:
            train_results = []
        test_results = h.get("test_results") or []

        # Create lookups for results by query
        train_by_query = {r["query"]: r for r in train_results}
        test_by_query = {r["query"]: r for r in test_results} if test_results else {}

        # Compute aggregate correct/total runs across all retries
        def aggregate_runs(results: list[dict]) -> tuple[int, int]:
            correct = 0
            total = 0
            for r in results:
                runs = r.get("runs", 0)
                triggers = r.get("triggers", 0)
                total += runs
                if r.get("should_trigger", True):
                    correct += triggers
                else:
                    correct += runs - triggers
            return correct, total

        train_correct, train_runs = aggregate_runs(train_results)
        test_correct, test_runs = aggregate_runs(test_results)

        # Determine score classes
        def score_class(correct: int, total: int) -> str:
            if total > 0:
                ratio = correct / total
                if ratio >= 0.8:
                    return "score-good"
                elif ratio >= 0.5:
                    return "score-ok"
            return "score-bad"

        train_class = score_class(train_correct, train_runs)
        test_class = score_class(test_correct, test_runs)

        row_class = "best-row" if iteration == best_iter else ""

        html_parts.append(f"""            <tr class="{row_class}">
                <td>{_broj(iteration)}</td>
                <td><span class="score {train_class}">{_broj(train_correct)}/{_broj(train_runs)}</span></td>
                <td><span class="score {test_class}">{_broj(test_correct)}/{_broj(test_runs)}</span></td>
                <td class="description">{html.escape(description)}</td>
""")

        def result_cell(r: dict, extra_class: str = "") -> str:
            """Render one query's cell.

            An inconclusive result — every run of the query errored, so there is
            NO evidence either way (trigger_rate is None, runs is 0) — must not be
            drawn as a plain fail. A "✗ 0/0" is indistinguishable from a query
            that genuinely never triggered, which silently discards the modeled
            uncertainty run_eval took care to record (N-14). Draw it as a warning
            that names the error count instead, so a human reading the report can
            see the difference between "measured, did not trigger" and "could not
            be measured".
            """
            base = f"result {extra_class}".strip()
            if r.get("inconclusive"):
                errors = r.get("errors", 0)
                return (f'                <td class="{base} inconclusive" '
                        f'title="inconclusive: all runs errored">⚠'
                        f'<span class="rate">inconclusive ({_broj(errors)} errors)</span></td>\n')
            did_pass = r.get("pass", False)
            triggers = r.get("triggers", 0)
            runs = r.get("runs", 0)
            icon = "✓" if did_pass else "✗"
            css_class = "pass" if did_pass else "fail"
            return (f'                <td class="{base} {css_class}">{icon}'
                    f'<span class="rate">{_broj(triggers)}/{_broj(runs)}</span></td>\n')

        # Add result for each train query
        for qinfo in train_queries:
            html_parts.append(result_cell(train_by_query.get(qinfo["query"], {})))

        # Add result for each test query (with different background)
        for qinfo in test_queries:
            html_parts.append(result_cell(test_by_query.get(qinfo["query"], {}),
                                          extra_class="test-result"))

        html_parts.append("            </tr>\n")

    html_parts.append("""        </tbody>
    </table>
    </div>
""")

    html_parts.append("""
</body>
</html>
""")

    return "".join(html_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate HTML report from run_loop output")
    parser.add_argument("input", help="Path to JSON output from run_loop.py (or - for stdin)")
    parser.add_argument("-o", "--output", default=None, help="Output HTML file (default: stdout)")
    parser.add_argument("--skill-name", default="", help="Skill name to include in the report title")
    args = parser.parse_args()

    data = load_json_arg(args.input, what="report data")

    html_output = generate_html(data, skill_name=args.skill_name)

    if args.output:
        Path(args.output).write_text(html_output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(html_output)


if __name__ == "__main__":
    main()
