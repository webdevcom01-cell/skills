#!/usr/bin/env python3
# Modified from anthropics/skills@b29e7cf6 (skills/skill-creator) by
# buky <webdevcom01@gmail.com>, 2026-07-30. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md.
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.
"""

import argparse
import json
import os
import select
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import parse_skill_md, validate_skill_name, load_json_arg

# Marker embedded in every temp command file this script creates, so cleanup
# can positively identify "ours" and never touch a real command file that
# happens to share a naming pattern.
TEMP_FILE_MARKER = "<!-- skill-creator:trigger-eval-temp-file -->"

# How old a leftover temp file must be before we consider it abandoned rather
# than belonging to another eval run currently in flight. Normal runs finish
# in seconds; this is generous headroom, not a tight race.
STALE_FILE_AGE_SECONDS = 600


def find_project_root() -> Path:
    """Find the project root by walking up from cwd looking for .claude/.

    Mimics how Claude Code discovers its project root, so the command file
    we create ends up where claude -p will look for it.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


def cleanup_stale_command_files(
    project_commands_dir: Path,
    skill_name: str,
    min_age_seconds: int = STALE_FILE_AGE_SECONDS,
) -> int:
    """Remove leftover temp command files from a previous run that didn't
    clean up after itself (e.g. the process was killed with SIGKILL, or the
    host timed out, before the per-file `finally` block in run_single_query
    could run — Python cannot intercept SIGKILL, so that cleanup path can be
    skipped entirely).

    Without this, an abandoned "{skill_name}-skill-<hex>.md" file stays
    registered as a real slash-command in the user's actual project
    indefinitely. This is a self-healing sweep: run once at the start of
    every eval session, before any new temp files are created, so a crash in
    one run doesn't leave a permanent trace for the user to find later.

    `min_age_seconds` defaults to the fixed STALE_FILE_AGE_SECONDS, but
    callers whose own `--timeout` can exceed that should pass a larger
    value: a query legitimately still in flight under a long timeout can
    otherwise be older than the fixed threshold while still being very much
    "in flight, not abandoned" — a second, concurrently-started eval session
    sweeping with the fixed 600s threshold would then delete its command
    file mid-run. See run_eval()'s call site, which sizes this from its own
    `timeout` argument.

    Returns the number of files removed.
    """
    if not project_commands_dir.is_dir():
        return 0

    removed = 0
    now = time.time()
    for path in project_commands_dir.glob(f"{skill_name}-skill-*.md"):
        try:
            if now - path.stat().st_mtime < min_age_seconds:
                continue  # young enough to plausibly belong to a run in flight
            content = path.read_text(errors="replace")
            if TEMP_FILE_MARKER not in content:
                continue  # not one of ours — never delete a real user command file
            path.unlink()
            removed += 1
        except OSError:
            continue  # best-effort; a file that vanished/changed mid-check is fine

    return removed


def _skill_field_patterns(skill_name: str) -> list[str]:
    """Raw-text patterns that identify a `Skill` tool_use call selecting
    exactly `skill_name`, matched against the (possibly still-streaming)
    JSON text of the tool's input. Checked as substrings rather than
    parsed JSON because this runs mid-stream, before the input is
    necessarily complete/valid JSON yet.

    Two spacing variants are needed because different JSON serializers
    (and streamed partial-JSON reconstructions) don't consistently include
    a space after the colon.
    """
    return [f'"skill":"{skill_name}"', f'"skill": "{skill_name}"']


def _read_path_pattern(skill_name: str) -> str:
    """Raw-text pattern identifying a `Read` tool_use call targeting the
    real, installed skill's directory (as opposed to our synthetic temp
    command file, which is matched separately via clean_name)."""
    return f"/skills/{skill_name}/"


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> tuple[bool, str | None, list[str]]:
    """Run a single query and return (triggered, via, tools_seen).

    `tools_seen` je lista imena alata vidjenih u transkriptu, redom pojavljivanja.
    Postoji zbog N-46: `trigger_rate: 0.0` moze da znaci dve razlicite stvari —
    (a) opis nije privukao, pa je model posegnuo za DRUGIM alatima, ili
    (b) upit nije trazio alat, pa model nije pozvao NIJEDAN.
    Bez ovog podatka te dve nule izgledaju identicno, a razlikuju se samo u
    transkriptu — koji se do sada odbacivao. Izmereno dvaput (CAL-01, CAL-03/P3):
    u oba slucaja nijedan alat, a izvestaj `0/3, errors=0, inconclusive=false`.

    OGRANICENJE: run koji OKINE vraca se rano i proces se ubija, pa je njegov
    `tools_seen` NEPOTPUN. Dijagnostika je smislena samo za runove koji nisu
    okinuli — a to su tacno oni kod kojih nula treba objasnjenje.

    `via` is "decoy" when our synthetic per-call command fired, "real_skill"
    when the real, already-installed skill of the same name fired instead
    (see below), or None when `triggered` is False.

    Creates a command file in .claude/commands/ so it appears in Claude's
    available_skills list, then runs `claude -p` with the raw query.
    Uses --include-partial-messages to detect triggering early from
    stream events (content_block_start) rather than waiting for the
    full assistant message, which only arrives after tool execution.

    Trigger detection accepts TWO signals, not just one: our synthetic
    command (`clean_name`, unique per call) firing, OR the real, already-
    installed skill of the same name (`skill_name`) firing. The second
    signal matters whenever this harness runs from an account/session that
    already has a real skill installed under the same name being tested
    (e.g. testing skill-creator's own description from within a session
    that already has skill-creator installed) — Claude will reasonably
    prefer the real, already-known skill over our decoy slash-command, and
    without this, that would be misreported as "did not trigger" even
    though the (identical, since we never edit the description field
    itself) description clearly did cause the model to reach for the
    skill. Caveat: when both the real skill and our decoy are present,
    this is not a perfectly clean measurement of the description in
    isolation — see the caller's notes on this limitation.
    """
    # Checked here as well as in main(), and before anything is built from it:
    # this function is also called directly (tests, other callers), and when it
    # runs inside the ProcessPoolExecutor a late failure would be recorded as a
    # per-query error rather than refusing the run outright (N-33).
    validate_skill_name(skill_name)

    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    skill_field_patterns = _skill_field_patterns(skill_name)
    read_path_pattern = _read_path_pattern(skill_name)
    project_commands_dir = Path(project_root) / ".claude" / "commands"
    command_file = project_commands_dir / f"{clean_name}.md"

    try:
        project_commands_dir.mkdir(parents=True, exist_ok=True)
        # Use YAML block scalar to avoid breaking on quotes in description
        indented_desc = "\n  ".join(skill_description.split("\n"))
        command_content = (
            f"---\n"
            f"description: |\n"
            f"  {indented_desc}\n"
            f"---\n\n"
            f"{TEMP_FILE_MARKER}\n\n"
            f"# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n"
        )
        command_file.write_text(command_content)

        cmd = [
            "claude",
            "-p", query,
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])

        # Remove CLAUDECODE env var to allow nesting claude -p inside a
        # Claude Code session. The guard is for interactive terminal conflicts;
        # programmatic subprocess usage is safe.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        # stderr goes to a temporary FILE, not to DEVNULL and not to a PIPE.
        #
        # DEVNULL was the original, and it threw away the only explanation a
        # failing call ever gives: up to 300 calls per run whose failure existed
        # solely as one "query failed: <exception>" line with nothing from the
        # CLI itself (N-21e).
        #
        # PIPE is the obvious replacement and it is WRONG here — measured, not
        # assumed. The read loop below drains stdout only; with an undrained
        # stderr pipe the child blocks as soon as it fills the pipe buffer
        # (~64 KB) and never exits. A probe confirmed it: with PIPE the child
        # was still unfinished after 6s (poll() = None), with a temp file it
        # exited immediately and all 300 KB was readable afterwards. Using PIPE
        # would have turned "lost diagnostics" into "every chatty call hangs
        # until --timeout" — quietly worse than the defect being fixed.
        stderr_file = tempfile.TemporaryFile()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=stderr_file,
            cwd=project_root,
            env=env,
        )

        triggered = False
        tools_seen: list[str] = []  # N-46: dokaz koji razlikuje dve vrste nule
        # Which signal produced the (eventual) trigger decision: "decoy" for
        # our synthetic per-call command, "real_skill" for the real,
        # already-installed skill of the same name (see the docstring above
        # — this signal doesn't prove the *candidate* description under test
        # is what caused the trigger, only that a same-named skill fired),
        # or None if nothing triggered / not yet known.
        via = None
        start_time = time.time()
        buffer = ""
        # Track state for stream event detection
        pending_tool_name = None
        accumulated_json = ""

        try:
            while time.time() - start_time < timeout:
                process_ended = process.poll() is not None
                if process_ended:
                    remaining = process.stdout.read()
                    if remaining:
                        buffer += remaining.decode("utf-8", errors="replace")
                    # The line-parsing loop below only picks up complete
                    # ("\n"-terminated) lines. If the process's very last
                    # write wasn't newline-terminated, that trailing line —
                    # possibly the final `result` event, e.g. carrying
                    # is_error — would otherwise sit in `buffer` forever and
                    # never get parsed. The process has exited, so no more
                    # data is coming: treat EOF itself as the terminator.
                    if buffer and not buffer.endswith("\n"):
                        buffer += "\n"
                else:
                    ready, _, _ = select.select([process.stdout], [], [], 1.0)
                    if not ready:
                        continue

                    chunk = os.read(process.stdout.fileno(), 8192)
                    if not chunk:
                        # stdout closed (EOF). The process may not have been
                        # reaped yet — re-check before deciding what this means.
                        process_ended = process.poll() is not None
                        if not process_ended:
                            continue
                    else:
                        buffer += chunk.decode("utf-8", errors="replace")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Early detection via stream events
                    if event.get("type") == "stream_event":
                        se = event.get("event", {})
                        se_type = se.get("type", "")

                        if se_type == "content_block_start":
                            cb = se.get("content_block", {})
                            if cb.get("type") == "tool_use":
                                tool_name = cb.get("name", "")
                                if tool_name and tool_name not in tools_seen:
                                    tools_seen.append(tool_name)  # N-46
                                if tool_name in ("Skill", "Read"):
                                    pending_tool_name = tool_name
                                    accumulated_json = ""
                                else:
                                    # A tool_use block for some other tool
                                    # (TodoWrite, Glob, Bash, ...) is not evidence
                                    # either way. The model routinely calls other
                                    # tools before reaching for the skill —
                                    # SKILL.md:491 explicitly tells it to put steps
                                    # in its TodoList, i.e. call TodoWrite. Ignore
                                    # this block and keep scanning; only
                                    # message_stop / end-of-stream is terminal.
                                    # Previously this returned False, so any run
                                    # where the skill was not the very first tool
                                    # call was misreported as "did not trigger"
                                    # (N-04).
                                    pending_tool_name = None

                        elif se_type == "content_block_delta" and pending_tool_name:
                            delta = se.get("delta", {})
                            if delta.get("type") == "input_json_delta":
                                accumulated_json += delta.get("partial_json", "")
                                if clean_name in accumulated_json:
                                    return True, "decoy", tools_seen
                                if pending_tool_name == "Skill" and any(p in accumulated_json for p in skill_field_patterns):
                                    return True, "real_skill", tools_seen
                                if pending_tool_name == "Read" and read_path_pattern in accumulated_json:
                                    return True, "real_skill", tools_seen

                        elif se_type in ("content_block_stop", "message_stop"):
                            if pending_tool_name:
                                if clean_name in accumulated_json:
                                    return True, "decoy", tools_seen
                                if pending_tool_name == "Skill" and any(p in accumulated_json for p in skill_field_patterns):
                                    return True, "real_skill", tools_seen
                                if pending_tool_name == "Read" and read_path_pattern in accumulated_json:
                                    return True, "real_skill", tools_seen
                                # This Skill/Read block was not ours. Same reason
                                # as above: it is not terminal. Reset and keep
                                # scanning — a later block may still be our skill
                                # (e.g. the model Reads some other file, then
                                # invokes the skill). Previously this returned
                                # False here, which is the same premature-negative
                                # as the non-Skill/Read case (N-04).
                                pending_tool_name = None
                            # `message_stop` NIJE terminalan (N-48). Zavrsava JEDNU
                            # assistant poruku, a potez ih rutinski ima vise: izmereno
                            # 2026-07-31 na stvarnom transkriptu — tri poruke, i tek
                            # druga nosi Read, treca tekst. Vracanje False ovde je
                            # prijavljivalo "nije okinuo" za svaki potez u kome prva
                            # poruka nije okinula. Terminalni su samo `result` i kraj
                            # procesa; oba vec vracaju (triggered, via) ispravno.

                    # Fallback: full assistant message (exact field comparison,
                    # since the JSON is complete and parsed here — more precise
                    # than the raw-text patterns used mid-stream above)
                    elif event.get("type") == "assistant":
                        message = event.get("message", {})
                        for content_item in message.get("content", []):
                            if content_item.get("type") != "tool_use":
                                continue
                            tool_name = content_item.get("name", "")
                            if tool_name and tool_name not in tools_seen:
                                tools_seen.append(tool_name)  # N-46
                            tool_input = content_item.get("input", {})
                            if tool_name == "Skill":
                                selected = tool_input.get("skill", "")
                                if clean_name in selected:
                                    triggered = True
                                    via = "decoy"
                                elif selected == skill_name:
                                    triggered = True
                                    via = "real_skill"
                            elif tool_name == "Read":
                                file_path = tool_input.get("file_path", "")
                                if clean_name in file_path:
                                    triggered = True
                                    via = "decoy"
                                elif read_path_pattern in file_path:
                                    triggered = True
                                    via = "real_skill"
                            # Scan ALL tool_use items, not just the first. The
                            # return used to sit inside this loop, so a message
                            # whose first tool_use was anything other than our
                            # Skill/Read (e.g. TodoWrite) was reported as "did not
                            # trigger" even when the skill was invoked in a later
                            # item (N-04). Stop early only once we have a match.
                            if triggered:
                                break
                        # Poruka BEZ naseg tool_use NIJE terminalna (N-48). Sa
                        # ukljucenim extended thinking prva assistant poruka je uvek
                        # blok razmisljanja, bez ijednog tool_use — pa je bezuslovni
                        # `return` ovde prijavljivao "nije okinuo" pre nego sto model
                        # uopste stigne da pozove alat. Izmereno: Skill je bio na
                        # dogadjaju 15, a ovaj return je pucao na dogadjaju 13.
                        # Isto obrazlozenje kao N-04 u T-09, samo dosledno sprovedeno.
                        if triggered:
                            return triggered, via, tools_seen

                    elif event.get("type") == "result":
                        if event.get("is_error"):
                            raise RuntimeError(
                                "claude -p returned an error result "
                                f"(terminal_reason={event.get('terminal_reason')!r}): "
                                f"{str(event.get('result', ''))[:300]}"
                            )
                        return triggered, via, tools_seen

                if process_ended:
                    # The process has exited and we've now parsed everything
                    # it ever wrote to stdout (including any trailing output
                    # read in this same iteration, above) without any branch
                    # above returning a decision — no `result` event was ever
                    # found. That means the process crashed or exited before
                    # producing one, not that the skill "did not trigger".
                    if process.returncode not in (0, None):
                        raise RuntimeError(
                            f"claude -p exited with code {process.returncode} "
                            "without producing a result event"
                        )
                    return triggered, via, tools_seen
            else:
                # The while condition became false (timeout elapsed) without
                # ever hitting a `break`/`return`/`raise` above — the process
                # was still running and never reached a decision in time.
                raise TimeoutError(
                    f"claude -p did not complete within {timeout}s timeout"
                )
        finally:
            # Clean up process on any exit path (return, exception, timeout)
            if process.poll() is None:
                process.kill()
                process.wait()
            # Whatever the CLI said on its way out, attached to the failure so it
            # is not lost. Read on EVERY exit path, including timeout, because a
            # timeout is exactly when the reason matters. TemporaryFile is
            # unlinked on close, so nothing is left behind even if this run dies.
            try:
                stderr_file.seek(0)
                stderr_tail = stderr_file.read().decode("utf-8", errors="replace")
            except Exception:
                stderr_tail = ""
            finally:
                stderr_file.close()
            if stderr_tail.strip() and process.returncode not in (0, None):
                print(f"claude -p stderr (exit {process.returncode}): "
                      f"{stderr_tail.strip()[-800:]}", file=sys.stderr)
    finally:
        if command_file.exists():
            command_file.unlink()


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results."""
    results = []

    # Self-healing sweep: remove any temp command files a previous, abnormally
    # terminated run left behind for this skill, before creating new ones.
    # Size the staleness threshold from this run's own `timeout` (with a
    # margin) so a concurrently-running session with a long --timeout can't
    # have its still-in-flight command file swept out from under it.
    removed = cleanup_stale_command_files(
        Path(project_root) / ".claude" / "commands",
        skill_name,
        min_age_seconds=max(STALE_FILE_AGE_SECONDS, timeout + 60),
    )
    if removed:
        print(f"Cleaned up {removed} stale temp command file(s) from a previous run.", file=sys.stderr)

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_errors: dict[str, int] = {}
        # Runs that triggered via the real, already-installed skill rather
        # than our synthetic decoy. These are ambiguous evidence for the
        # *candidate* description under test — see run_single_query's
        # docstring — so callers can use this to judge how much of a
        # query's trigger_rate rests on that weaker signal.
        query_real_skill_matches: dict[str, int] = {}
        # N-46: dokaz koji razlikuje "opis nije privukao" od "upit nije trazio alat".
        query_no_tool_runs: dict[str, int] = {}
        query_tools_seen: dict[str, set] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
                query_errors[query] = 0
                query_real_skill_matches[query] = 0
                query_no_tool_runs[query] = 0
                query_tools_seen[query] = set()
            try:
                triggered, via, tools_seen = future.result()
                query_triggers[query].append(triggered)
                if triggered and via == "real_skill":
                    query_real_skill_matches[query] += 1
                # N-46: run koji nije okinuo a nije pozvao NIJEDAN alat nije isto
                # sto i run koji je posegnuo za drugim alatom. Prvo znaci da upit
                # nije trazio alat; drugo da opis nije privukao. Bez ove razlike
                # obe nule izgledaju identicno.
                query_tools_seen[query].update(tools_seen)
                if not triggered and not tools_seen:
                    query_no_tool_runs[query] += 1
            except Exception as e:
                # A run that errored (API failure, process crash, timeout —
                # see run_single_query) produced NO evidence either way about
                # whether the description triggers. Counting it as a
                # non-trigger (the old behavior) silently passes negative
                # eval items whose runs never actually completed, and
                # silently deflates positive items' trigger rate. Track it
                # separately instead, so it's visible in the JSON output
                # itself — not just a stderr line only a human watching the
                # terminal would ever see.
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_errors[query] += 1

    for query, triggers in query_triggers.items():
        item = query_items[query]
        should_trigger = item["should_trigger"]
        errors = query_errors[query]
        completed_runs = len(triggers)

        if completed_runs == 0:
            # Every run for this query errored. We have zero evidence, so we
            # cannot judge a pass/fail — reporting one either way would be a
            # fabricated result. Surface it as explicitly inconclusive
            # instead of defaulting to a trigger_rate of 0.0, which would be
            # indistinguishable from "genuinely never triggered."
            results.append({
                "query": query,
                "should_trigger": should_trigger,
                "trigger_rate": None,
                "triggers": 0,
                "runs": 0,
                "errors": errors,
                "real_skill_matches": query_real_skill_matches[query],
                "runs_without_any_tool": query_no_tool_runs[query],
                "tools_seen": sorted(query_tools_seen[query]),
                "pass": False,
                "inconclusive": True,
            })
            continue

        trigger_rate = sum(triggers) / completed_runs
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": completed_runs,
            "errors": errors,
            # How many of `triggers` fired via the real, already-installed
            # skill rather than our decoy — see query_real_skill_matches
            # above. A non-zero value here means part of this query's
            # trigger_rate is not clean evidence for the candidate
            # description specifically; it's visible here rather than
            # silently folded into the same number as a decoy match.
            "real_skill_matches": query_real_skill_matches[query],
            "runs_without_any_tool": query_no_tool_runs[query],
            "tools_seen": sorted(query_tools_seen[query]),
            "pass": did_pass,
            "inconclusive": False,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = load_json_arg(args.eval_set, what="eval set")
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    # Refuse once, loudly, before any work — rather than once per worker.
    try:
        validate_skill_name(name)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)
            # N-46: nula nikad ne sme da stoji sama. Ako upit nije okinuo a model
            # nije pozvao NIJEDAN alat, to nije dokaz da opis ne privlaci — to je
            # dokaz da upit nije trazio alat. Bez ove linije se te dve stvari
            # citaju identicno, sto se stvarno desilo (CAL-01, CAL-03/P3).
            bez = r.get("runs_without_any_tool", 0)
            if r.get("trigger_rate") == 0 and bez:
                alati = ", ".join(r.get("tools_seen") or []) or "nijedan"
                print(f"         ^ {bez}/{r['runs']} runova nije pozvalo nijedan alat "
                      f"(vidjeni alati: {alati}) - nula mozda nije o opisu",
                      file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
