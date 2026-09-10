#!/usr/bin/env python3
"""Record one acceptance-test case as a tamper-evident evidence file.

Why this is a script and not a prompt instruction
-------------------------------------------------
The verdict on an acceptance test case must not be an opinion. It is computed
here from a stated rule and the agent's actual response text. The model running
the skill supplies the raw tool payloads; it does not get to say PASS.

Two payloads are required, because one is not checkable:

  --chat     the verbatim JSON returned by as_chat_with_agent
  --exec     the verbatim JSON returned by as_get_recent_executions

The chat payload is what the agent said. The execution payload is the server's
own record that a run happened, carrying a server-side timestamp and an id that
any third party with MCP access can look up later. This script cross-checks the
two and records how strong that corroboration is. It never upgrades a weak
corroboration to a strong one.

Exit codes: 0 recorded, 1 verdict FAIL recorded (still written), 2 unusable input.
"""

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "adp-evidence-1"


def finite(value):
    """Replace non-finite numbers, which json.loads accepts and json.dumps cannot write."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: finite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [finite(v) for v in value]
    return value

# ---------------------------------------------------------------- verdict rules

def _json_load(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def apply_rule(rule, response):
    """Return (verdict, explanation). Rules are exact and few on purpose.

    A rule language that can express anything can also express a rule that
    always passes. These five cannot be bent into always-true by accident.
    """
    if ":" not in rule:
        raise ValueError(f"rule must be kind:value, got {rule!r}")
    kind, value = rule.split(":", 1)
    kind = kind.strip().lower()

    if kind == "contains":
        ok = value in response
        return ok, f"response {'contains' if ok else 'does not contain'} {value!r}"
    if kind == "not_contains":
        ok = value not in response
        return ok, f"response {'does not contain' if ok else 'contains'} {value!r}"
    if kind == "regex":
        if re.search(r"\([^)]*[+*][^)]*\)\s*[+*]", value):
            raise ValueError(
                "regex rule nests one quantifier inside another, which can run for hours "
                "on an ordinary response; write the check as contains: or json_has_key:")
        try:
            ok = re.search(value, response, re.S) is not None
        except re.error as e:
            raise ValueError(f"regex rule does not compile: {e}")
        return ok, f"pattern {value!r} {'matched' if ok else 'did not match'}"
    if kind == "json_has_key":
        obj = _json_load(response.strip())
        if obj is None:
            return False, "response is not parseable JSON"
        ok = isinstance(obj, dict) and value in obj
        return ok, f"parsed JSON {'has' if ok else 'lacks'} key {value!r}"
    if kind == "json_key_in":
        if "=" not in value:
            raise ValueError("json_key_in needs key=a,b,c")
        key, allowed = value.split("=", 1)
        allowed = [a.strip() for a in allowed.split(",") if a.strip()]
        obj = _json_load(response.strip())
        if obj is None:
            return False, "response is not parseable JSON"
        if not isinstance(obj, dict) or key not in obj:
            return False, f"parsed JSON lacks key {key!r}"
        ok = str(obj[key]) in allowed
        return ok, f"{key}={obj[key]!r} {'is' if ok else 'is not'} one of {allowed}"

    raise ValueError(f"unknown rule kind {kind!r}")


# --------------------------------------------------------------- corroboration

_WS = re.compile(r"\s+")


def squeeze(text):
    return _WS.sub("", text or "")


def preview_fragments(preview):
    """Pull comparable content out of an execution outputPreview.

    The preview is the raw flow output — a {"messages":[...]} envelope holding
    JSON that has itself been pretty-printed and escaped, and it is truncated
    mid-string. The chat response is the final compacted message. So the two are
    never byte-equal and a naive equality check would fail on every honest run.
    """
    if not preview:
        return []
    frags = []
    obj = _json_load(preview)
    if isinstance(obj, dict) and isinstance(obj.get("messages"), list):
        for m in obj["messages"]:
            if isinstance(m, dict) and isinstance(m.get("content"), str):
                frags.append(m["content"])
    if not frags:
        # Truncation cuts the preview mid-string, so it will not parse. Unescape
        # the raw text and, where possible, drop the {"messages":[{"role":...}]}
        # envelope, which is server plumbing and appears in no agent response.
        raw = preview.encode("utf-8", "ignore").decode("unicode_escape", "ignore")
        frags.append(raw)
        for m in re.finditer(r'"content"\s*:\s*"?', raw):
            tail = raw[m.end():]
            if tail.strip():
                frags.append(tail)
    return [f for f in frags if f.strip()][:6]


MIN_OVERLAP = 40  # characters of whitespace-stripped content


def corroborate(response, execution):
    """CONFIRMED / WEAK / NONE — and never anything stronger than the evidence."""
    if not execution:
        return "NONE", "no server execution record was supplied"
    if not isinstance(execution, dict):
        return "NONE", "the execution entry is not an object, so nothing can be read from it"
    if not execution.get("id"):
        return "NONE", "execution record carries no id, so it cannot be looked up again"

    status = execution.get("status")
    if status not in ("SUCCESS", "COMPLETED"):
        return "WEAK", f"execution {execution['id']} is recorded with status {status!r}"

    r = squeeze(response)
    for frag in preview_fragments(execution.get("outputPreview")):
        f = squeeze(frag)[:8000]
        if len(f) < MIN_OVERLAP:
            continue
        # Neither end of the preview can be trusted to align with the response:
        # the front may carry a server envelope, the back is truncated. So look
        # for any run of MIN_OVERLAP characters that appears in both, then
        # extend it to report how much actually matched.
        for start in range(0, len(f) - MIN_OVERLAP + 1, 5):
            if f[start:start + MIN_OVERLAP] not in r:
                continue
            end = start + MIN_OVERLAP
            while end < len(f) and f[start:end + 20] in r:
                end += 20
            return "CONFIRMED", (
                f"execution {execution['id']} started {execution.get('startedAt')} "
                f"and its stored output matches the response over {end - start} characters"
            )
    return "WEAK", (
        f"execution {execution['id']} exists and succeeded, but its stored preview "
        "could not be matched against the response text"
    )


def pick_execution(exec_payload, agent_id, response, exec_id=None):
    """Choose the execution record that belongs to this response.

    Returns (execution, matching_ids, pinned).

    Not simply the newest one: several cases are often run before the execution
    list is fetched once, so the newest record belongs to the last case.

    And not necessarily a unique one either. Two different refusal cases can
    produce byte-identical output — a live run of a gated agent showed exactly
    that — in which case content cannot distinguish their execution records.
    Every match is returned so the evidence can say so, rather than picking one
    and implying a certainty that does not exist.

    --exec-id decides which execution is recorded. It does not decide that the
    others stopped producing the same output, so the matches are computed either
    way and a pinned choice among several stays 'ambiguous'. Pinning is the
    runner's assertion about run order; it is not new evidence.
    """
    if not exec_payload:
        return None, [], False
    if not isinstance(exec_payload, dict):
        sys.stderr.write("--exec payload is not an as_get_recent_executions object\n")
        raise SystemExit(2)
    execs = exec_payload.get("executions") or []
    if not isinstance(execs, list) or any(not isinstance(e, dict) for e in execs):
        sys.stderr.write("--exec payload has an 'executions' list this script cannot read\n")
        raise SystemExit(2)
    if agent_id and exec_payload.get("agentId") and exec_payload["agentId"] != agent_id:
        return None, [], False
    matches = [e for e in execs if corroborate(response, e)[0] == "CONFIRMED"]
    match_ids = [e.get("id") for e in matches]
    if exec_id:
        for e in execs:
            if e.get("id") == exec_id:
                # Pinning an execution whose stored output matches nothing does
                # not attribute it. It stays unmatched, and says so.
                if exec_id not in match_ids:
                    return e, [], True
                others = [i for i in match_ids if i != exec_id]
                return e, [exec_id] + others, True
        sys.stderr.write(f"--exec-id {exec_id} is not in the supplied execution list\n")
        raise SystemExit(2)
    if matches:
        return matches[0], match_ids, False
    return (execs[0] if execs else None), [], False


# ----------------------------------------------------------------------- main

def read_json_arg(path, what):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.stderr.write(f"{what}: file not found: {path}\n")
        raise SystemExit(2)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        sys.stderr.write(f"{what}: not readable as UTF-8 JSON ({e})\n")
        raise SystemExit(2)


def main():
    p = argparse.ArgumentParser(description="Record one acceptance-test case, or one configuration fact.")
    p.add_argument("--case-id", required=True, help="e.g. AT-01, or CFG-01 for a configuration record")
    p.add_argument("--label", required=True, help="what this record holds, in plain words")
    p.add_argument("--kind", choices=["case", "config"], default="case",
                   help="case = an acceptance run; config = a snapshot of how the agent is set up")
    p.add_argument("--intent", choices=["pass", "block"],
                   help="pass = should do the job; block = should refuse")
    p.add_argument("--rule",
                   help="contains:X | not_contains:X | regex:X | json_has_key:X | json_key_in:k=a,b")
    p.add_argument("--expected", help="what the client should see, in their words")
    p.add_argument("--chat", help="file holding as_chat_with_agent JSON")
    p.add_argument("--exec", dest="execf", help="file holding as_get_recent_executions JSON")
    p.add_argument("--exec-id", help="pin a specific execution id when several match")
    p.add_argument("--payload", help="file holding as_get_agent JSON, for --kind config")
    p.add_argument("--out-dir", default="evidence")
    args = p.parse_args()

    # A case id becomes a file name. It may not become a path.
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", args.case_id or ""):
        sys.stderr.write("--case-id must be letters, digits, hyphens and underscores only\n")
        return 2

    out = Path(args.out_dir)

    # A configuration fact — the model, the node count, the flow id — is not
    # behaviour, and no chat/execution pair can evidence it. It gets a record of
    # its own so the claim in the document resolves to a retained artefact
    # instead of to the author's memory of a tool call.
    if args.kind == "config":
        if not args.payload:
            sys.stderr.write("--kind config needs --payload FILE holding the as_get_agent JSON\n")
            return 2
        payload = read_json_arg(args.payload, "--payload")
        blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        record = {
            "schema": SCHEMA,
            "kind": "config",
            "case_id": args.case_id,
            "label": args.label,
            "source": "as_get_agent",
            "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "recorded_by": "the runner — this is a snapshot, not a server-side attestation",
            "payload": payload,
            "payload_sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        }
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{args.case_id}.json"
        path.write_text(
            json.dumps(finite(record), ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n",
            encoding="utf-8")
        print(f"{args.case_id}: configuration snapshot recorded — {args.label}")
        print(f"  written: {path}")
        return 0

    missing = [f for f, v in (("--intent", args.intent), ("--rule", args.rule),
                              ("--expected", args.expected), ("--chat", args.chat)) if not v]
    if missing:
        sys.stderr.write(f"--kind case needs {', '.join(missing)}\n")
        return 2

    chat = read_json_arg(args.chat, "--chat")
    if not isinstance(chat, dict) or "response" not in chat:
        sys.stderr.write("--chat payload has no 'response' field; this is not an as_chat_with_agent result\n")
        return 2
    response = chat["response"]
    if not isinstance(response, str) or not response.strip():
        sys.stderr.write("agent response is empty — record the failure, do not record a pass\n")
        return 2

    exec_payload = read_json_arg(args.execf, "--exec") if args.execf else None
    execution, matching_ids, pinned = pick_execution(
        exec_payload, chat.get("agentId"), response, args.exec_id)
    unmatched = execution is not None and not matching_ids

    try:
        ok, why = apply_rule(args.rule, response)
    except ValueError as e:
        sys.stderr.write(f"{e}\n")
        return 2

    corr, corr_note = corroborate(response, execution)

    record = {
        "schema": SCHEMA,
        "case_id": args.case_id,
        "label": args.label,
        "intent": args.intent,
        "agent": {"id": chat.get("agentId"), "name": chat.get("agentName")},
        "sent": {
            "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "recorded_by": "the runner, not the server — the server timestamp is under server_execution",
        },
        "returned": {
            "response": response,
            "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
            "conversation_id": chat.get("conversationId"),
            "round_trip_ms": chat.get("durationMs"),
        },
        "server_execution": {
            "id": execution.get("id"),
            "status": execution.get("status"),
            "started_at": execution.get("startedAt"),
            "completed_at": execution.get("completedAt"),
            "duration_ms": execution.get("durationMs"),
            "error": execution.get("error"),
        } if execution else None,
        "server_execution_note": (
            f"execution {execution['id']} was recorded for this case, but nothing in its stored "
            "output ties it to this response, so it may belong to a different case"
            if unmatched else None
        ),
        "corroboration": corr,
        "corroboration_note": corr_note,
        "attribution": (
            "unique" if len(matching_ids) == 1 else
            "ambiguous" if len(matching_ids) > 1 else
            # No execution list at all is a different failure from a list that
            # held nothing matching, and the gate should not confuse them.
            "unmatched" if execution else "unrecorded"
        ),
        "attribution_note": (
            (f"pinned to {args.exec_id}, but " if pinned else "")
            + f"{len(matching_ids)} executions in the supplied list produce this same output, "
              f"so a run is proven but this exact execution id is not: {matching_ids}"
            if len(matching_ids) > 1 else None
        ),
        "expected": args.expected,
        "verdict_rule": args.rule,
        "verdict": "PASS" if ok else "FAIL",
        "verdict_basis": why,
    }

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{args.case_id}.json"
    path.write_text(
        json.dumps(finite(record), ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n",
        encoding="utf-8")

    print(f"{args.case_id}: {record['verdict']} — {why}")
    print(f"  corroboration: {corr} — {corr_note}")
    if len(matching_ids) > 1:
        print(f"  attribution: ambiguous — {len(matching_ids)} executions share this output"
              + ("; pinning chose which one is recorded, not which one ran"
                 if pinned else "; re-run with --exec-id to choose which is recorded"))
    elif unmatched:
        print("  attribution: unmatched — the recorded execution could not be tied to this "
              "response; treat its id and timestamp as unconfirmed")
    print(f"  written: {path}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
