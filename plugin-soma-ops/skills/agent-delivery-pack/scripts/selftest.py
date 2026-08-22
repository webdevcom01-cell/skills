#!/usr/bin/env python3
"""Self-test for record_evidence.py and check_pack.py.

Three layers, because the first two have fooled us before:

  1. cases the gate must flag, and cases it must let through
  2. end-to-end recording from payloads shaped exactly like the live server's
  3. mutations — the checker is deliberately weakened and the suite must notice

Layer 3 exists because a suite that stays green after a branch is deleted is
not a suite. Run:  python3 selftest.py
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE / "check_pack.py"
RECORD = HERE / "record_evidence.py"

# --------------------------------------------------------------------- fixtures

# Shaped after a real as_chat_with_agent payload.
CHAT = {
    "agentId": "cmpvcm2my00aps601oqykk7nu",
    "agentName": "Lead Scorer",
    "conversationId": "cms8pyduj00gxog01lysm1fgh",
    "response": '{"company":"Silbo d.o.o.","score":15,"fit":"low","reasons":["Company size is 528 employees, which exceeds the ICP size range of 5-150 employees","Industry is food distribution and logistics, not B2B SaaS"],"confidence":"3 stars"}',
    "waitForInput": False,
    "messageCount": 2,
    "durationMs": 20463,
}

# Shaped after a real as_get_recent_executions payload: pretty-printed, escaped,
# truncated mid-string, and with a duration that does NOT equal the round trip.
_INNER = json.dumps({
    "company": "Silbo d.o.o.", "score": 15, "fit": "low",
    "reasons": ["Company size is 528 employees, which exceeds the ICP size range of 5-150 employees",
                "Industry is food distribution and logistics, not B2B SaaS"],
    "confidence": "3 stars",
}, indent=2)
EXEC = {
    "agentId": "cmpvcm2my00aps601oqykk7nu",
    "agentName": "Lead Scorer",
    "count": 1,
    "executions": [{
        "id": "cms8pyfsz00h2og01h01bvy0b",
        "status": "SUCCESS",
        "startedAt": "2026-07-31T09:07:22.115Z",
        "completedAt": "2026-07-31T09:07:36.936Z",
        "durationMs": 15854,
        "error": None,
        "outputPreview": json.dumps({"messages": [{"role": "assistant", "content": _INNER}]})[:300],
    }],
}

# ------------------------------------------------------------- gate: must flag

# (name, line, expected category). The category matters: a mutation that
# downgrades a refused phrase to an escapable claim has weakened the checker
# even though the line is still reported.
MUST_FLAG = [
    ("guarantee", "The agent guarantees that every malformed lead is blocked.", "FORBIDDEN"),
    ("guarantee first person", "We guarantee a response within one working day.", "FORBIDDEN"),
    ("guarantee sr first person", "Garantujemo odgovor u roku od jednog radnog dana.", "FORBIDDEN"),
    ("guarantee after unrelated negation",
     "We do not send email. We guarantee a score for every lead.", "FORBIDDEN"),
    ("guarantee after negation same sentence",
     "Although no security review was carried out, we guarantee the agent blocks bad input.", "FORBIDDEN"),
    ("guarantee sr", "Agent garantuje da nijedan pogrešan lead neće proći.", "FORBIDDEN"),
    ("absolute rate", "It classifies leads with 100% accuracy across all inputs.", "FORBIDDEN"),
    ("near-absolute", "Uptime has been 99.9% since deployment.", "FORBIDDEN"),
    ("never fails", "The gate never fails, so no manual review is needed.", "FORBIDDEN"),
    ("zero errors", "Runs since May have produced zero errors in production.", "FORBIDDEN"),
    ("fully automated", "Lead qualification is now fully automated end to end.", "FORBIDDEN"),
    ("compliance", "The data flow is compliant with GDPR.", "FORBIDDEN"),
    ("compliance sr", "Obrada podataka je usklađena sa zakonom o zaštiti podataka.", "FORBIDDEN"),
    ("bug free", "The validator is bug-free after the June rewrite.", "FORBIDDEN"),
    ("always", "The agent always returns a numeric score between 0 and 100.", "FORBIDDEN"),
    ("forbidden plus gap", "The agent guarantees a score, though this is NOT TESTED.", "FORBIDDEN"),
    ("forbidden plus tag", "The pipeline is compliant with GDPR [EV:AT-01].", "FORBIDDEN"),
    ("untagged pct", "The agent scored 87% of test leads correctly.", "FIGURE"),
    ("untagged ratio", "It passed 7 of 7 acceptance cases.", "FIGURE"),
    ("untagged slash", "Acceptance result: 7/7.", "FIGURE"),
    ("untagged seconds", "A typical scoring call completes in 20 s.", "FIGURE"),
    ("untagged hours", "The team saves 12 hours a week on lead triage.", "FIGURE"),
    ("untagged multiple", "Throughput is 3x what it was.", "FIGURE"),
    ("figure plus gap", "It handled 87% of cases, though the basis for that is TO CONFIRM.", "MIXED"),
    ("figure plus hedge sr", "Obradio je 87% slučajeva, mada je osnova ZA POTVRDU.", "MIXED"),
    ("claim untagged", "The agent blocks any input that contains no lead at all.", "CLAIM"),
    ("claim sr", "Agent blokira svaki unos koji ne sadrži lead.", "CLAIM"),
    ("claim tested", "We tested the agent against seven representative leads.", "CLAIM"),
    ("claim verified", "Behaviour on malformed input was verified before handover.", "CLAIM"),
]

MUST_PASS = [
    ("tagged figure", "The agent returned a score for all seven cases [EV:AT-01]."),
    ("tagged claim", "It blocks input that contains no lead [EV:AT-02]."),
    ("gap marked", "Behaviour on non-Latin input is NOT TESTED."),
    ("gap marked sr", "Ponašanje na ćirilici NIJE TESTIRANO."),
    ("negation", "The agent does not send email and does not write to your CRM."),
    ("negation sr", "Agent ne šalje poštu i ne menja podatke u vašem sistemu."),
    ("question", "Who owns this agent after handover?"),
    ("method prose", "To run this test, open Agent Studio and paste the input below."),
    ("method sr", "Da biste pokrenuli test, otvorite Agent Studio i nalepite unos ispod."),
    ("short", "Owner: Marko."),
    ("plain heading prose", "This document lists what was handed over."),
    ("year alone", "The agent was built in 2026 and revised since."),
    ("list numbering", "3. Open the agent."),
    # Disclaiming a guarantee is the wording the reference file prescribes. A
    # checker that refuses it forces the author to delete the safest sentence
    # in the document.
    ("disclaims guarantee", "These are intentions, not guarantees, and no level of availability is promised."),
    ("disclaims guarantee 2", "We do not guarantee any particular response time."),
    ("disclaims guarantee sr", "Ovo su namere, a ne garancija, i nijedan nivo dostupnosti se ne obećava."),
    ("nothing detects", "Nothing in the acceptance suite detects a score that is plausible and wrong."),
    ("none of the cases", "None of the cases checks whether the score is the right score."),
    ("no case", "No case here verifies accuracy."),
]


def run_check(text, evidence=None, strict=False, extra_files=None, evidence_files=None):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        f = td / "pack.md"
        f.write_text(text, encoding="utf-8")
        evd = td / "evidence"
        evd.mkdir()
        for cid, rec in (evidence or {}).items():
            (evd / f"{cid}.json").write_text(json.dumps(rec), encoding="utf-8")
        # Files whose name deliberately differs from the case_id inside them.
        for fname, rec in (evidence_files or {}).items():
            (evd / fname).write_text(json.dumps(rec), encoding="utf-8")
        cmd = [sys.executable, str(CHECK), str(f), "--evidence", str(evd)]
        if strict:
            cmd.append("--strict")
        for name, body in (extra_files or {}).items():
            p = td / name
            p.write_text(body, encoding="utf-8")
            cmd.insert(3, str(p))
        return subprocess.run(cmd, capture_output=True, text=True)


def ev_record(cid, verdict="PASS", corr="CONFIRMED", **extra):
    rec = {"schema": "adp-evidence-1", "case_id": cid, "verdict": verdict,
           "corroboration": corr, "corroboration_note": "test fixture",
           "label": "fixture", "intent": "pass"}
    rec.update(extra)
    return rec


def ev_timed(cid, round_trip_ms, verdict="PASS"):
    return ev_record(cid, verdict=verdict, returned={"round_trip_ms": round_trip_ms})


EV_ALL = {c: ev_record(c) for c in ("AT-01", "AT-02", "AT-03")}




def check_frontmatter():
    """Refuse to pass if SKILL.md would be rejected on save.

    The platform caps `description` at 1024. It is not documented whether that
    counts characters or bytes, and these descriptions carry diacritics, so both
    are held under 1000. A skill that will not save is a skill that does not
    exist, and nothing else in this suite would have noticed.
    """
    import re as _re
    md = (HERE.parent / "SKILL.md").read_text(encoding="utf-8")
    parts = md.split("---")
    problems = []
    if len(parts) < 3:
        problems.append("SKILL.md has no --- frontmatter block")
    else:
        fm = parts[1]
        if not _re.search(r"^name:\s*\S", fm, _re.M):
            problems.append("no name field")
        m = _re.search(r"^description:\s*(.*?)(?=^\w+:|\Z)", fm, _re.S | _re.M)
        if not m:
            problems.append("no description field")
        else:
            d = m.group(1).strip()
            if d.startswith(">"):
                d = " ".join(l.strip() for l in d.splitlines()[1:] if l.strip())
            if len(d) > 1000:
                problems.append(f"description is {len(d)} characters; the platform refuses over 1024")
            if len(d.encode("utf-8")) > 1000:
                problems.append(f"description is {len(d.encode('utf-8'))} bytes; diacritics cost extra")
    print("== frontmatter ==")
    for p in problems:
        print(f"  FAIL {p}")
    if problems:
        raise SystemExit(1)

def main():
    check_frontmatter()
    passed = failed = 0
    fails = []

    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            fails.append(f"{name}: {detail}")


    print("== gate: must flag ==")
    for name, line, kind in MUST_FLAG:
        r = run_check(line, EV_ALL)
        check(f"flag/{name}", r.returncode == 1 and kind in r.stdout,
              f"exit {r.returncode}, expected {kind}, out={r.stdout.strip()[:150]}")

    print("== gate: must pass ==")
    for name, line in MUST_PASS:
        r = run_check(line, EV_ALL)
        check(f"pass/{name}", r.returncode == 0, f"exit {r.returncode}, out={r.stdout.strip()[:200]}")

    print("== gate: structural ==")
    r = run_check("The agent handles malformed leads [EV:AT-99].", EV_ALL)
    check("dangling tag", "DANGLING" in r.stdout, r.stdout[:200])

    r = run_check("Case AT-01: PASS.", EV_ALL)
    check("unsourced verdict", "UNSOURCED_VERDICT" in r.stdout, r.stdout[:200])

    r = run_check("Case AT-01 [EV:AT-01]: PASS.", EV_ALL)
    check("sourced verdict ok", "UNSOURCED_VERDICT" not in r.stdout, r.stdout[:200])

    r = run_check("Fee is [TO AGREE] per month.", EV_ALL)
    check("placeholder flagged", "PLACEHOLDER" in r.stdout, r.stdout[:200])

    r = run_check("DRAFT — NOT YET SENT\n\nFee is [TO AGREE] per month.", EV_ALL)
    check("placeholder ok in draft", "PLACEHOLDER" not in r.stdout, r.stdout[:200])

    ev = dict(EV_ALL)
    ev["AT-04"] = ev_record("AT-04", verdict="FAIL")
    r = run_check("Everything cited [EV:AT-01].", ev)
    check("buried fail", "BURIED_FAIL" in r.stdout, r.stdout[:300])

    ev2 = {"AT-01": ev_record("AT-01", corr="NONE")}
    r = run_check("Cited [EV:AT-01].", ev2)
    check("uncorroborated", "UNCORROBORATED" in r.stdout, r.stdout[:300])

    ev3 = {"AT-01": ev_record("AT-01", corr="WEAK")}
    r = run_check("Cited [EV:AT-01].", ev3)
    check("weak passes lenient", r.returncode == 0, r.stdout[:300])
    r = run_check("Cited [EV:AT-01].", ev3, strict=True)
    check("weak fails strict", "WEAK_CORROBORATION" in r.stdout, r.stdout[:300])

    # Hard-wrapped prose must not split a claim from its tag.
    wrapped = "The agent blocks any input\nthat contains no lead at all [EV:AT-02]."
    r = run_check(wrapped, EV_ALL)
    check("hard wrap joined", r.returncode == 0, r.stdout[:300])

    # Code fences must not be read as claims.
    fenced = "```\nThe agent guarantees 100% accuracy.\n```\n"
    r = run_check(fenced, EV_ALL)
    check("fence ignored", r.returncode == 0, r.stdout[:300])

    r = subprocess.run([sys.executable, str(CHECK), "/no/such/file.md"], capture_output=True, text=True)
    check("missing file exit 2", r.returncode == 2, f"exit {r.returncode}")

    print("== record_evidence ==")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "chat.json").write_text(json.dumps(CHAT), encoding="utf-8")
        (td / "exec.json").write_text(json.dumps(EXEC), encoding="utf-8")

        def rec(rule, extra=()):
            return subprocess.run(
                [sys.executable, str(RECORD), "--case-id", "AT-01", "--label", "valid lead",
                 "--intent", "pass", "--rule", rule, "--expected", "a score comes back",
                 "--chat", str(td / "chat.json"), "--exec", str(td / "exec.json"),
                 "--out-dir", str(td / "evidence"), *extra],
                capture_output=True, text=True)

        r = rec('json_has_key:score')
        check("record pass", r.returncode == 0, r.stdout + r.stderr)
        rec_json = json.loads((td / "evidence" / "AT-01.json").read_text())
        check("verdict PASS", rec_json["verdict"] == "PASS", str(rec_json.get("verdict")))
        check("corroborated", rec_json["corroboration"] == "CONFIRMED", rec_json.get("corroboration_note", ""))
        check("server id kept", rec_json["server_execution"]["id"] == "cms8pyfsz00h2og01h01bvy0b", "")
        check("server time kept", rec_json["server_execution"]["started_at"] == "2026-07-31T09:07:22.115Z", "")
        check("round trip differs from execution",
              rec_json["returned"]["round_trip_ms"] != rec_json["server_execution"]["duration_ms"],
              "the two durations must be allowed to differ")
        check("hash present", len(rec_json["returned"]["response_sha256"]) == 64, "")

        r = rec('contains:BLOCKED')
        check("record fail exit 1", r.returncode == 1, f"exit {r.returncode}")
        check("verdict FAIL", json.loads((td / "evidence" / "AT-01.json").read_text())["verdict"] == "FAIL", "")

        r = rec('json_key_in:fit=low,medium,high')
        check("json_key_in pass", r.returncode == 0, r.stdout + r.stderr)
        r = rec('json_key_in:fit=high')
        check("json_key_in fail", r.returncode == 1, f"exit {r.returncode}")

        r = rec('nonsense:x')
        check("bad rule exit 2", r.returncode == 2, f"exit {r.returncode}")

        # No execution payload at all → corroboration NONE, never CONFIRMED.
        r = subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "AT-09", "--label", "x", "--intent", "pass",
             "--rule", "json_has_key:score", "--expected", "x", "--chat", str(td / "chat.json"),
             "--out-dir", str(td / "evidence")], capture_output=True, text=True)
        check("no exec → NONE",
              json.loads((td / "evidence" / "AT-09.json").read_text())["corroboration"] == "NONE", r.stdout)

        # A mismatched execution must not be laundered into CONFIRMED.
        bad = json.loads(json.dumps(EXEC))
        bad["executions"][0]["outputPreview"] = json.dumps(
            {"messages": [{"role": "assistant", "content": "completely unrelated output text here"}]})
        (td / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
        subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "AT-10", "--label", "x", "--intent", "pass",
             "--rule", "json_has_key:score", "--expected", "x", "--chat", str(td / "chat.json"),
             "--exec", str(td / "bad.json"), "--out-dir", str(td / "evidence")],
            capture_output=True, text=True)
        check("mismatch → WEAK",
              json.loads((td / "evidence" / "AT-10.json").read_text())["corroboration"] == "WEAK", "")

        # Two executions carrying the same output — a live run of a gated agent
        # produced exactly this, because two different refusals emit one message.
        twin = json.loads(json.dumps(EXEC))
        twin["executions"] = [
            dict(twin["executions"][0], id="exec-newer"),
            dict(twin["executions"][0], id="exec-older"),
        ]
        (td / "twin.json").write_text(json.dumps(twin), encoding="utf-8")

        def rec_twin(extra=()):
            return subprocess.run(
                [sys.executable, str(RECORD), "--case-id", "AT-12", "--label", "x", "--intent", "block",
                 "--rule", "json_has_key:score", "--expected", "x", "--chat", str(td / "chat.json"),
                 "--exec", str(td / "twin.json"), "--out-dir", str(td / "evidence"), *extra],
                capture_output=True, text=True)

        rec_twin()
        twin_rec = json.loads((td / "evidence" / "AT-12.json").read_text())
        check("twin → ambiguous", twin_rec["attribution"] == "ambiguous", str(twin_rec.get("attribution")))
        check("twin still corroborated", twin_rec["corroboration"] == "CONFIRMED", "")
        check("twin names both ids", "exec-older" in (twin_rec.get("attribution_note") or ""), "")

        rec_twin(["--exec-id", "exec-older"])
        pinned = json.loads((td / "evidence" / "AT-12.json").read_text())
        check("pinned id used", pinned["server_execution"]["id"] == "exec-older", "")

        # Pinning inside a list where only one execution matches is genuinely unique.
        solo = json.loads(json.dumps(EXEC))
        (td / "solo.json").write_text(json.dumps(solo), encoding="utf-8")
        subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "AT-14", "--label", "x", "--intent", "pass",
             "--rule", "json_has_key:score", "--expected", "x", "--chat", str(td / "chat.json"),
             "--exec", str(td / "solo.json"), "--exec-id", "cms8pyfsz00h2og01h01bvy0b",
             "--out-dir", str(td / "evidence")], capture_output=True, text=True)
        solo_rec = json.loads((td / "evidence" / "AT-14.json").read_text())
        check("pinned sole match → unique", solo_rec["attribution"] == "unique",
              str(solo_rec.get("attribution")))

        r = rec_twin(["--exec-id", "exec-nonexistent"])
        check("unknown exec-id exit 2", r.returncode == 2, f"exit {r.returncode}")

        # Empty response is unusable, not a pass.
        empty = dict(CHAT, response="   ")
        (td / "empty.json").write_text(json.dumps(empty), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "AT-11", "--label", "x", "--intent", "pass",
             "--rule", "not_contains:zzz", "--expected", "x", "--chat", str(td / "empty.json"),
             "--out-dir", str(td / "evidence")], capture_output=True, text=True)
        check("empty response exit 2", r.returncode == 2, f"exit {r.returncode}")

        # Pinning must not erase the fact that content could not distinguish the
        # executions. A record that says "unique" when two runs share an output
        # has upgraded the evidence, which is the one thing this script may not do.
        rec_twin(["--exec-id", "exec-older"])
        pinned2 = json.loads((td / "evidence" / "AT-12.json").read_text())
        check("pinned keeps ambiguity", pinned2["attribution"] == "ambiguous",
              f'attribution={pinned2.get("attribution")!r} — pinned one of two identical outputs')
        check("pinned ambiguity names the twin",
              "exec-newer" in (pinned2.get("attribution_note") or ""),
              str(pinned2.get("attribution_note")))
        check("pinned id still used", pinned2["server_execution"]["id"] == "exec-older", "")

        # An execution that matches nothing must not be presented as this case's
        # server record without saying so.
        nomatch = json.loads(json.dumps(EXEC))
        nomatch["executions"][0]["outputPreview"] = json.dumps(
            {"messages": [{"role": "assistant", "content": "output belonging to a different case entirely"}]})
        (td / "nomatch.json").write_text(json.dumps(nomatch), encoding="utf-8")
        subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "AT-13", "--label", "x", "--intent", "pass",
             "--rule", "json_has_key:score", "--expected", "x", "--chat", str(td / "chat.json"),
             "--exec", str(td / "nomatch.json"), "--out-dir", str(td / "evidence")],
            capture_output=True, text=True)
        nm = json.loads((td / "evidence" / "AT-13.json").read_text())
        check("unmatched flagged in record", nm["attribution"] == "unmatched", str(nm.get("attribution")))
        check("unmatched carries a warning", bool(nm.get("server_execution_note")),
              "server_execution holds a foreign execution id with nothing saying so")
        r = run_check("Cited [EV:AT-13].", {"AT-13": nm})
        check("unmatched reported by the gate", "UNATTRIBUTED" in r.stdout, r.stdout[:250])

        # Configuration facts — model, node count, flow id — need a channel of
        # their own; they are not behaviour and no chat/exec pair can carry them.
        agent_json = {"id": "cmpvcm2my00aps601oqykk7nu", "name": "Lead Scorer",
                      "model": "gpt-4.1-mini", "nodeCount": 8, "updatedAt": "2026-06-27T10:00:00Z"}
        (td / "agent.json").write_text(json.dumps(agent_json), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "CFG-01", "--kind", "config",
             "--label", "agent configuration as read on the day",
             "--payload", str(td / "agent.json"), "--out-dir", str(td / "evidence")],
            capture_output=True, text=True)
        check("config record written", r.returncode == 0, r.stdout + r.stderr)
        cfg_path = td / "evidence" / "CFG-01.json"
        check("config file exists", cfg_path.exists(), "")
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text())
            check("config kind", cfg.get("kind") == "config", str(cfg.get("kind")))
            check("config keeps raw payload", cfg.get("payload") == agent_json, "")
            check("config hashed", len(cfg.get("payload_sha256") or "") == 64, "")
            r = run_check("Model: gpt-4.1-mini [EV:CFG-01].", {"CFG-01": cfg}, strict=True)
            check("config record satisfies the gate", r.returncode == 0, r.stdout[:250])

    print("== truth of the tag, not just its presence ==")

    evf = {"AT-01": ev_record("AT-01", verdict="FAIL")}
    r = run_check("Case AT-01 returned a score for a valid lead: PASS [EV:AT-01].", evf)
    check("verdict contradicts record", "VERDICT_MISMATCH" in r.stdout, r.stdout[:250])
    r = run_check("Case AT-01 did not return a score: FAIL [EV:AT-01]. We are fixing it.", evf)
    check("verdict agrees with record", "VERDICT_MISMATCH" not in r.stdout, r.stdout[:250])
    r = run_check("Case AT-01: PROŠAO [EV:AT-01].", evf)
    check("sr verdict contradicts record", "VERDICT_MISMATCH" in r.stdout, r.stdout[:250])

    evd = {"AT-01": ev_timed("AT-01", 20463), "AT-03": ev_timed("AT-03", 9730)}
    r = run_check("Round-trip times ranged from about 10 s to 21 s [EV:AT-01] [EV:AT-03].", evd, strict=True)
    check("duration outside the records it cites", "FIGURE_OUTSIDE" in r.stdout, r.stdout[:300])
    r = run_check("Round-trip times ranged from about 10 s to 20 s [EV:AT-01] [EV:AT-03].", evd, strict=True)
    check("duration inside the records it cites", r.returncode == 0, r.stdout[:300])
    r = run_check("A call took 20463 ms [EV:AT-01], and AT-03 was quicker [EV:AT-03].", evd, strict=True)
    check("exact millisecond figure accepted", r.returncode == 0, r.stdout[:300])
    r = run_check("The agent scored 87% of leads correctly [EV:AT-01] [EV:AT-03].", evd, strict=True)
    check("non-duration figure untouched", r.returncode == 0, r.stdout[:300])

    print("== evidence directory hygiene ==")

    r = run_check("Nothing cited here at all.", None, strict=True, evidence_files={
        "aaa-old.json": ev_record("AT-01", verdict="FAIL"),
        "zzz-new.json": ev_record("AT-01", verdict="PASS"),
    })
    check("duplicate case_id reported", "DUPLICATE" in r.stdout, r.stdout[:300])

    print("== which files the gate reads ==")

    r = run_check("**INTERNAL — NOT FOR THE CLIENT.**\n\nFive cases, five PASS, and I am uneasy about AT-05.", EV_ALL)
    check("internal file not gated", r.returncode == 0, r.stdout[:250])
    check("internal skip is announced", "internal" in r.stdout.lower(), r.stdout[:250])

    fenced_verdict = "How to run it yourself:\n\n```\n$ run case AT-01\nexpected: PASS\nfee: [TO AGREE]\n```\n\nOwner: Marko.\n"
    r = run_check(fenced_verdict, EV_ALL)
    check("fenced verdict not read", "UNSOURCED_VERDICT" not in r.stdout, r.stdout[:250])
    check("fenced placeholder not read", "PLACEHOLDER" not in r.stdout, r.stdout[:250])

    print("== forbidden vocabulary the documentation promises ==")

    for nm, line in (("secure", "The system is secure and your data is protected."),
                     ("secure sr", "Sistem je bezbedan i podaci su zaštićeni."),
                     ("production-ready tagged", "The deployment is production-ready [EV:AT-01].")):
        r = run_check(line, EV_ALL)
        check(f"flag/{nm}", r.returncode == 1 and "FORBIDDEN" in r.stdout,
              f"exit {r.returncode}, out={r.stdout.strip()[:150]}")

    for nm, line in (("security review wording", "No security review has been carried out."),
                     ("security review sr", "Bezbednosni pregled nije rađen."),
                     ("disclaimed secure", "This agent is not secure by any assessment we have made.")):
        r = run_check(line, EV_ALL)
        check(f"pass/{nm}", r.returncode == 0, f"exit {r.returncode}, out={r.stdout.strip()[:200]}")

    print("== configuration claims in prose ==")

    for nm, line in (("model", "Model: gpt-4.1-mini."),
                     ("model prose", "It runs on gpt-4.1-mini through your own account."),
                     ("node count", "Flow: 8 nodes, last changed 27 June 2026."),
                     ("eval suite", "The evaluation suite is the Lead Scorer golden set.")):
        r = run_check(line, EV_ALL)
        check(f"config/{nm}", "CONFIG_CLAIM" in r.stdout, f"exit {r.returncode}, out={r.stdout.strip()[:200]}")

    for nm, line in (("model tagged", "Model: gpt-4.1-mini [EV:AT-01]."),
                     ("model gap", "The model it runs on is TO CONFIRM."),
                     ("kb negation", "It does not write to your knowledge base.")):
        r = run_check(line, EV_ALL)
        check(f"config-ok/{nm}", r.returncode == 0, f"exit {r.returncode}, out={r.stdout.strip()[:200]}")

    print("== draft marker ==")

    pad = "Ordinary prose a client reads before the fees. " * 30  # comfortably past the window
    r = run_check("DRAFT — NOT FOR SIGNATURE\n\n" + pad + "\nFee is [TO AGREE] per month.", EV_ALL)
    check("draft at the top", r.returncode == 0, r.stdout[:250])
    r = run_check(pad + "\nDRAFT — NOT FOR SIGNATURE\n\nFee is [TO AGREE] per month.", EV_ALL)
    check("draft below the documented window", "PLACEHOLDER" in r.stdout, r.stdout[:250])
    check("draft window named in the message", "top" in r.stdout.lower() or "1000" in r.stdout,
          f"message must say where the marker has to go: {r.stdout[:200]}")

    print("== adversarial: evasion ==")

    ev_f6 = dict(EV_ALL); ev_f6["AT-06"] = ev_record("AT-06", verdict="FAIL")

    # An unterminated fence must not blind the gate for the rest of the file.
    # This is the hole the fence fix opened: two scans now read a blanked copy.
    unclosed = ("```\npython3 check_pack.py delivery.md\n\n"
                "The agent guarantees a correct score and is production-ready.\n"
                "Model: gpt-4.1-mini across 8 nodes. Case AT-06 PASS [EV:AT-06].\n")
    r = run_check(unclosed, ev_f6)
    check("unclosed fence still gated", "FORBIDDEN" in r.stdout, r.stdout[:300])
    check("unclosed fence announced", "UNCLOSED_FENCE" in r.stdout, r.stdout[:300])

    # "internal" in ordinary prose must not exempt a client document.
    r = run_check("# Delivery note\n\nIt hands the result to your internal CRM.\n"
                  "It guarantees a correct score and is production-ready.\n", EV_ALL)
    check("lowercase internal does not exempt", "FORBIDDEN" in r.stdout, r.stdout[:300])
    r = run_check("**INTERNAL — NOT FOR THE CLIENT.**\n\nIt guarantees everything.", EV_ALL)
    check("real internal marker still exempts", r.returncode == 0, r.stdout[:200])

    # A verdict must be compared with the record nearest it, not with the set of
    # every record cited nearby — swapping two table rows inverts both verdicts.
    swapped = "| AT-01 | FAIL [EV:AT-01] |\n| AT-06 | PASS [EV:AT-06] |\n"
    r = run_check(swapped, ev_f6)
    check("swapped verdict rows", "VERDICT_MISMATCH" in r.stdout, r.stdout[:300])
    correct = "| AT-01 | PASS [EV:AT-01] |\n| AT-06 | FAIL [EV:AT-06] |\n"
    r = run_check(correct, ev_f6)
    check("correct verdict rows clean", "VERDICT_MISMATCH" not in r.stdout, r.stdout[:300])
    r = run_check("Case AT-06 passed and the client accepted it [EV:AT-06].", ev_f6)
    check("lowercase verdict contradicts record", "VERDICT_MISMATCH" in r.stdout, r.stdout[:300])

    # A hedge elsewhere in the sentence must not switch the checker off.
    for nm, line in (("config plus hedge", "Model: gpt-4.1-mini, nothing else."),
                     ("claim plus hedge", "It blocks every malformed lead, though nothing is perfect.")):
        r = run_check(line, EV_ALL)
        check(f"hedged/{nm}", r.returncode == 1, f"exit {r.returncode}, out={r.stdout.strip()[:200]}")
    r = run_check("It does not run on your own infrastructure.", EV_ALL)
    check("genuine negation of a config fact", r.returncode == 0, r.stdout[:200])
    # A clause that continues a negated one is still governed by that negation.
    r = run_check("They are not a measure of accuracy — no case here checks whether a score is the "
                  "right score, only that the agent answers in the agreed shape and refuses what "
                  "it should refuse.", EV_ALL)
    check("continuation clause keeps the negation", r.returncode == 0, r.stdout[:250])
    r = run_check("No case measures accuracy, merely that it returns a score.", EV_ALL)
    check("continuation clause, second form", r.returncode == 0, r.stdout[:250])

    # Units and spellings the first pass missed.
    r = run_check("Median round trip was 45000 milliseconds [EV:AT-01] [EV:AT-03].",
                  {"AT-01": ev_timed("AT-01", 20463), "AT-03": ev_timed("AT-03", 9730)})
    check("spelled-out milliseconds", "FIGURE_OUTSIDE" in r.stdout, r.stdout[:300])
    r = run_check("Each lead takes 1500 milliseconds.", EV_ALL)
    check("untagged spelled-out unit", "FIGURE" in r.stdout, r.stdout[:250])
    for nm, line in (("ready for production", "The flow is ready for production."),
                     ("en dash", "The agent is production–ready."),
                     ("near absolute 99.95", "Accuracy was 99.95% on the sample [EV:AT-01].")):
        r = run_check(line, EV_ALL)
        check(f"evasion/{nm}", "FORBIDDEN" in r.stdout, f"exit {r.returncode}, out={r.stdout.strip()[:200]}")
    r = run_check("It uses Claude Sonnet 4.5 for scoring.", EV_ALL)
    check("model name without a hyphen", "CONFIG_CLAIM" in r.stdout, r.stdout[:250])

    print("== adversarial: honest sentences that must survive ==")

    SURVIVE = [
        ("secure as a verb", "Before the handover call we will secure your written sign-off."),
        ("secure as a topic", "Keep the API key in a secure password manager."),
        ("secure network", "The venue provides a secure guest network for the workshop."),
        ("secure sr transport", "Podaci se prenose bezbedno, preko HTTPS-a."),
        ("explicit disclaimer", "We do not claim that the agent is secure."),
        ("explicit disclaimer 2", "Nothing in this pack should be read as production-ready."),
        ("explicit disclaimer 3", "The pack does not promise 100% accuracy."),
        ("explicit disclaimer sr", "Ne tvrdimo da je sistem bezbedan niti da je spreman za produkciju."),
        ("pricing model", "Our pricing model: a fixed fee, invoiced on handover."),
        ("engagement model", "The engagement model: two workshops, one pilot, one handover."),
        ("workshop date", "The workshop runs on 12 September in your Belgrade office."),
        ("account prose", "The pilot runs on your own Agent Studio account."),
        ("model sr", "Naš model naplate: fiksna cena po fazi."),
        ("timeout threshold", "AT-01 finished in 20 s, inside the 60 s timeout configured on the flow [EV:AT-01]."),
        ("longer-than threshold", "If a run takes longer than 5 minutes, cancel it and re-run the case [EV:AT-01]."),
    ]
    ev_s = {"AT-01": ev_timed("AT-01", 20463)}
    for nm, line in SURVIVE:
        r = run_check(line, ev_s)
        check(f"survive/{nm}", r.returncode == 0, f"exit {r.returncode}, out={r.stdout.strip()[:200]}")

    print("== adversarial: malformed input must not crash ==")

    for nm, blob in (("list", "[]"), ("null", "null"), ("number", "5"), ("string", '"x"')):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "d.md").write_text("Owner: Marko.", encoding="utf-8")
            evd = td / "evidence"; evd.mkdir()
            (evd / "BAD.json").write_text(blob, encoding="utf-8")
            out = subprocess.run([sys.executable, str(CHECK), str(td / "d.md"), "--evidence", str(evd)],
                                 capture_output=True, text=True)
        check(f"evidence/{nm} not a record", "SETUP" in out.stdout and "Traceback" not in out.stderr,
              f"exit {out.returncode}, err={out.stderr.strip()[:120]}")

    r = run_check("Each lead takes 9 hours [EV:N1].",
                  {"N1": ev_record("N1", returned={"round_trip_ms": float("nan")})})
    check("NaN duration degrades cleanly", r.returncode == 0 and "Traceback" not in r.stderr,
          f"exit {r.returncode}, err={r.stderr.strip()[:120]}")

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "chat.json").write_text(json.dumps(CHAT), encoding="utf-8")
        for nm, blob in (("execution is a string", '{"executions":["oops"]}'),
                         ("payload is a list", '[{"id":"1"}]')):
            (td / "bad.json").write_text(blob, encoding="utf-8")
            out = subprocess.run(
                [sys.executable, str(RECORD), "--case-id", "AT-30", "--label", "x", "--intent", "pass",
                 "--rule", "json_has_key:score", "--expected", "x", "--chat", str(td / "chat.json"),
                 "--exec", str(td / "bad.json"), "--out-dir", str(td / "evidence")],
                capture_output=True, text=True)
            check(f"record/{nm}", out.returncode == 2 and "Traceback" not in out.stderr,
                  f"exit {out.returncode}, err={out.stderr.strip()[:140]}")

        # A pinned execution that matches nothing is still unmatched.
        nomatch = json.loads(json.dumps(EXEC))
        nomatch["executions"][0]["outputPreview"] = json.dumps(
            {"messages": [{"role": "assistant", "content": "unrelated output from another case entirely"}]})
        (td / "nm.json").write_text(json.dumps(nomatch), encoding="utf-8")
        subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "AT-31", "--label", "x", "--intent", "pass",
             "--rule", "json_has_key:score", "--expected", "x", "--chat", str(td / "chat.json"),
             "--exec", str(td / "nm.json"), "--exec-id", "cms8pyfsz00h2og01h01bvy0b",
             "--out-dir", str(td / "evidence")], capture_output=True, text=True)
        pin_nm = json.loads((td / "evidence" / "AT-31.json").read_text())
        check("pinned non-match is unmatched", pin_nm["attribution"] == "unmatched",
              str(pin_nm.get("attribution")))

        # A case id is a file name; it may not be a path.
        out = subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "../../pwned", "--label", "x", "--intent", "pass",
             "--rule", "json_has_key:score", "--expected", "x", "--chat", str(td / "chat.json"),
             "--out-dir", str(td / "evidence")], capture_output=True, text=True)
        check("case id may not traverse", out.returncode == 2, f"exit {out.returncode}")

    # A configuration record cannot stand in for an acceptance run.
    cfg_only = {"CFG-01": {"schema": "adp-evidence-1", "kind": "config", "case_id": "CFG-01",
                           "label": "cfg", "payload": {"model": "gpt-4.1-mini"}}}
    r = run_check("Case AT-06 PASS [EV:CFG-01].", cfg_only)
    check("verdict cited to a config record", "WRONG_RECORD_KIND" in r.stdout, r.stdout[:300])
    r = run_check("The run took 20 s [EV:CFG-01].", cfg_only)
    check("duration cited to a config record", "WRONG_RECORD_KIND" in r.stdout, r.stdout[:300])
    r = run_check("Model: gpt-4.1-mini [EV:CFG-01].", cfg_only)
    check("config fact cited to a config record", r.returncode == 0, r.stdout[:300])

    print("== adversarial: second round ==")

    ev_r2 = dict(EV_ALL)
    ev_r2["AT-03"] = ev_record("AT-03", verdict="FAIL")
    ev_r2["AT-04"] = ev_record("AT-04", verdict="PASS")
    ev_t = {"AT-01": ev_timed("AT-01", 20463), "AT-02": ev_timed("AT-02", 15900)}

    # Invisible characters must not smuggle a refused phrase past the gate.
    for nm, line in (("zero width in figure", "Accuracy is 1\u200b00% on your leads [EV:AT-01]."),
                     ("zero width in word", "The agent g\u200buarantees a correct band [EV:AT-01]."),
                     ("soft hyphen", "The pack is production\u00ad-ready [EV:AT-01].")):
        r = run_check(line, EV_ALL)
        check(f"invisible/{nm}", "FORBIDDEN" in r.stdout, f"exit {r.returncode}, out={r.stdout.strip()[:160]}")

    # A heading is prose a client reads, and was never gated at all.
    r = run_check("# Delivery note\n\n## Fully automated scoring, guaranteed\n\nOwner: Marko.\n", EV_ALL)
    check("heading is gated", "FORBIDDEN" in r.stdout, r.stdout[:250])
    r = run_check("# Lead Scorer — delivery note\n\n## What it deliberately does not do\n\nOwner: Marko.\n", EV_ALL)
    check("ordinary heading clean", r.returncode == 0, r.stdout[:250])

    # A disclaimer governs its own clause, not everything after it.
    for nm, line in (("disclaimer then guarantee",
                      "We do not claim the agent is secure, but it guarantees a correct band."),
                     ("disclaimer then figure",
                      "We make no promise about uptime; the agent achieves 97% accuracy on your leads."),
                     ("disclaimer then automated",
                      "Nothing in this note should be read as a warranty, and the agent is fully automated.")):
        r = run_check(line, EV_ALL)
        check(f"disclaimer-scope/{nm}", r.returncode == 1, f"exit {r.returncode}, out={r.stdout.strip()[:180]}")

    # A results list puts the verdict after its own tag; the next row's tag is nearer.
    listed_ok = ("- [EV:AT-01] a real lead is scored — PASS\n"
                 "- [EV:AT-03] a message with no lead is refused — FAIL\n"
                 "- [EV:AT-04] an off-topic question is refused — PASS\n")
    r = run_check(listed_ok, ev_r2)
    check("correct results list is clean", "VERDICT_MISMATCH" not in r.stdout, r.stdout[:300])
    listed_lie = ("- [EV:AT-01] a real lead is scored — FAIL\n"
                  "- [EV:AT-03] a message with no lead is refused — FAIL\n")
    r = run_check(listed_lie, ev_r2)
    check("lying results list caught", "VERDICT_MISMATCH" in r.stdout, r.stdout[:300])
    # A table row holding two results attributes each verdict to its own item.
    r = run_check("| [EV:AT-01] warm lead | PASS | [EV:AT-03] duplicate | FAIL |\n", ev_r2)
    check("two results in one row", "VERDICT_MISMATCH" not in r.stdout, r.stdout[:300])

    # "failed" in ordinary prose is not a verdict.
    for nm, line in (("failed validation", "A lead that failed validation is refused rather than scored [EV:AT-01]."),
                     ("earlier attempts", "Two earlier attempts failed before we recorded the run [EV:AT-01]."),
                     ("sr pala", "Konverzija je pala u junu, pre nego što smo snimili run [EV:AT-01].")):
        r = run_check(line, EV_ALL)
        check(f"soft-verdict/{nm}", "VERDICT_MISMATCH" not in r.stdout, r.stdout[:250])
    r = run_check("Case AT-03 passed and the client accepted it [EV:AT-03].", ev_r2)
    check("named case passed contradicts record", "VERDICT_MISMATCH" in r.stdout, r.stdout[:250])

    # A bound below what was measured is a performance claim, not a setting.
    for nm, line in (("under", "The agent answers in under 2 seconds [EV:AT-01] [EV:AT-02]."),
                     ("at most", "Median round trip was at most 900 ms [EV:AT-01] [EV:AT-02]."),
                     ("minutes unit", "Each case took 4 min [EV:AT-01] [EV:AT-02].")):
        r = run_check(line, ev_t)
        check(f"lower-bound/{nm}", "FIGURE_OUTSIDE" in r.stdout, f"exit {r.returncode}, out={r.stdout.strip()[:180]}")
    r = run_check("AT-01 finished in 20 s, inside the 60 s timeout [EV:AT-01] [EV:AT-02].", ev_t)
    check("upper bound still exempt", r.returncode == 0, r.stdout[:250])

    # "only" continues a statement about the tests, not a promise about the agent.
    for nm, line in (("only after does-not", "The agent does not guess, only detects and blocks every duplicate lead."),
                     ("just after does-not", "The pack does not cover integrations, just handles scoring for every lead."),
                     ("only after do-not", "We do not disclose the vendor, only model: gpt-4.1-mini.")):
        r = run_check(line, EV_ALL)
        check(f"continuation-abuse/{nm}", r.returncode == 1, f"exit {r.returncode}, out={r.stdout.strip()[:180]}")
    r = run_check("No case here checks whether a score is the right score, only that the agent "
                  "answers in the agreed shape.", EV_ALL)
    check("continuation after no-case still exempt", r.returncode == 0, r.stdout[:250])

    # A marker is a marker, not the first word of a sentence.
    r = run_check("# Delivery note\n\nINTERNAL sections have been stripped from this document "
                  "before sending.\n\nThe agent guarantees a correct band.\n", EV_ALL)
    check("prose beginning with INTERNAL is gated", "FORBIDDEN" in r.stdout, r.stdout[:250])

    # Negation forms the clause rule exposed.
    for nm, line in (("never returns", "It never returns a decision, only a score."),
                     ("never after comma", "The agent does not store your data, and never returns it to a third party."),
                     ("neither", "Neither of the two acceptance cases blocks a valid lead."),
                     ("nijedan", "Nijedan test ne proverava da agent ocenjuje lead.")):
        r = run_check(line, EV_ALL)
        check(f"negation/{nm}", r.returncode == 0, f"exit {r.returncode}, out={r.stdout.strip()[:180]}")

    # Prose about the document is not a licence to claim inside it.
    for nm, line in (("this document shows", "This document shows the agent blocks every lead outside your ICP."),
                     ("how ... is described", "How the agent blocks every disposable domain is described below.")):
        r = run_check(line, EV_ALL)
        check(f"prose-escape/{nm}", "CLAIM" in r.stdout, f"exit {r.returncode}, out={r.stdout.strip()[:180]}")

    print("== adversarial: robustness ==")

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "chat.json").write_text(json.dumps(CHAT), encoding="utf-8")
        out = subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "R1", "--label", "l", "--intent", "pass",
             "--rule", "regex:(", "--expected", "e", "--chat", str(td / "chat.json"),
             "--out-dir", str(td / "ev")], capture_output=True, text=True)
        check("broken regex rule exits 2", out.returncode == 2 and "Traceback" not in out.stderr,
              f"exit {out.returncode}, err={out.stderr.strip()[:140]}")
        out = subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "R2", "--label", "l", "--intent", "pass",
             "--rule", "json_has_key:score", "--expected", "e", "--chat", str(td / "chat.json"),
             "--out-dir", str(td / "ev")], capture_output=True, text=True)
        r2 = json.loads((td / "ev" / "R2.json").read_text())
        check("no exec list is not an unmatched attribution", r2["attribution"] != "unmatched",
              f'attribution={r2.get("attribution")!r} with no --exec supplied')

    import time
    long_line = " , ".join(["the agent does not blocks leads"] * 2000)
    t0 = time.time()
    run_check(long_line, EV_ALL)
    check("long line does not hang", time.time() - t0 < 10, f"{time.time() - t0:.1f}s for a 60 KB line")

    print("== adversarial: third round ==")

    ev3 = dict(EV_ALL); ev3["AT-06"] = ev_record("AT-06", verdict="FAIL")
    ev_d = {"AT-01": ev_timed("AT-01", 20463), "AT-03": ev_timed("AT-03", 6390)}

    # Headings carry claims, but a section heading is not a sentence: only the
    # refused vocabulary is judged there.
    r = run_check("# Delivery note\n\n## Fully automated scoring, guaranteed\n\nOwner: Marko.\n", EV_ALL)
    check("forbidden phrase in a heading", "FORBIDDEN" in r.stdout, r.stdout[:250])
    for nm, head in (("how it scores", "## How the agent scores a lead"),
                     ("what it returns", "### What the agent returns"),
                     ("sr heading", "## Kako agent ocenjuje lead"),
                     ("response time", "## Response within 4 hours"),
                     ("results count", "## Results: 5 of 5 cases"),
                     ("sr odziv", "## Odziv u roku od 4 sata")):
        r = run_check(head + "\n\nOwner: Marko.\n", EV_ALL)
        check(f"heading-ok/{nm}", r.returncode == 0, f"exit {r.returncode}, out={r.stdout.strip()[:160]}")

    # A verdict belongs to the tag nearest it on its own row, whichever side.
    r = run_check("- PASS on the warm lead [EV:AT-01], FAIL on the duplicate [EV:AT-06]\n", ev3)
    check("verdict-first row", "VERDICT_MISMATCH" not in r.stdout, r.stdout[:300])
    r = run_check("- [EV:AT-01] a real lead is scored — PASS\n- [EV:AT-06] refused — FAIL\n", ev3)
    check("tag-first row", "VERDICT_MISMATCH" not in r.stdout, r.stdout[:300])
    r = run_check("- PASS on the warm lead [EV:AT-06]\n", ev3)
    check("verdict-first row lying", "VERDICT_MISMATCH" in r.stdout, r.stdout[:300])

    # A lower bound the runs do not contradict is not a finding.
    for nm, line in (("at least", "Allow at least 5 s per lead when you size the batch [EV:AT-01] [EV:AT-03]."),
                     ("timeout", "Each case stays inside the 60 s timeout [EV:AT-01] [EV:AT-03]."),
                     ("conditional", "If a run takes longer than 5 minutes, cancel it [EV:AT-01] [EV:AT-03].")):
        r = run_check(line, ev_d)
        check(f"bound-ok/{nm}", r.returncode == 0, f"exit {r.returncode}, out={r.stdout.strip()[:180]}")
    for nm, line in (("under", "The agent answers in under 2 seconds [EV:AT-01] [EV:AT-03]."),
                     ("shielded", "Each run stays under the 60 s timeout and typically takes 30 s [EV:AT-01] [EV:AT-03].")):
        r = run_check(line, ev_d)
        check(f"bound-flag/{nm}", "FIGURE_OUTSIDE" in r.stdout, f"exit {r.returncode}, out={r.stdout.strip()[:180]}")

    # A named case with a lower-case verdict is still a verdict.
    r = run_check("The duplicate case passed cleanly [EV:AT-06].", ev3)
    check("case + lowercase verdict", "VERDICT_MISMATCH" in r.stdout, r.stdout[:250])
    r = run_check("Slučaj sa duplikatom je prošao [EV:AT-06].", ev3)
    check("sr case + lowercase verdict", "VERDICT_MISMATCH" in r.stdout, r.stdout[:250])

    # A negation must not reach across "and" into a separate assertion.
    for nm, line in (("never after and", "The agent blocks every disposable domain and never lets one through."),
                     ("neither after and", "The scorer handles every inbound form and neither stalls nor drops a record.")):
        r = run_check(line, EV_ALL)
        check(f"and-scope/{nm}", "CLAIM" in r.stdout, f"exit {r.returncode}, out={r.stdout.strip()[:180]}")
    r = run_check("It never returns a decision, only a score.", EV_ALL)
    check("never still exempts its own clause", r.returncode == 0, r.stdout[:250])

    # Instructions to the reader about their own security are not warranties.
    for nm, line in (("make sure", "Make sure your API keys are secure before you deploy."),
                     ("ensure", "You should ensure the environment is secure."),
                     ("sr adverb", "Prenos je bezbedno obavljen preko HTTPS-a."),
                     ("sr adverb 2", "Pristup je bezbedno ograničen na vaš nalog.")):
        r = run_check(line, EV_ALL)
        check(f"secure-ok/{nm}", r.returncode == 0, f"exit {r.returncode}, out={r.stdout.strip()[:180]}")
    r = run_check("The agent is secure.", EV_ALL)
    check("predicative secure still refused", "FORBIDDEN" in r.stdout, r.stdout[:200])

    # Every character that renders as nothing, not a hand-picked seven.
    for cp in ("\u034f", "\u2061", "\u2064", "\u180e", "\ufe0f", "\u3164", "\U000e0001"):
        r = run_check(f"The agent guar{cp}antees a band [EV:AT-01].", EV_ALL)
        check(f"invisible/U+{ord(cp):04X}", "FORBIDDEN" in r.stdout, r.stdout[:160])

    # An all-caps reference line is not an INTERNAL marker.
    r = run_check("INTERNAL REF: LS-2026-014\n\nThe agent guarantees a score.\n", EV_ALL)
    check("all-caps reference is not a marker", "FORBIDDEN" in r.stdout, r.stdout[:250])
    r = run_check("# INTERNAL\n\nIt guarantees everything.\n", EV_ALL)
    check("heading marker exempts", r.returncode == 0, r.stdout[:250])

    print("== adversarial: cost ==")

    import time
    for nm, body in (("forbidden loop", "we do not claim any guarantee here, " * 3000),
                     ("verdict loop", "[EV:AT-01] PASS " * 4000)):
        t0 = time.time()
        run_check(body, EV_ALL)
        dt = time.time() - t0
        check(f"linear/{nm}", dt < 12, f"{dt:.1f}s on a {len(body) // 1024} KB line")

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "chat.json").write_text(json.dumps(CHAT), encoding="utf-8")
        t0 = time.time()
        out = subprocess.run(
            [sys.executable, str(RECORD), "--case-id", "R3", "--label", "l", "--intent", "pass",
             "--rule", "regex:(a+)+$", "--expected", "e", "--chat", str(td / "chat.json"),
             "--out-dir", str(td / "ev")], capture_output=True, text=True, timeout=60)
        check("catastrophic regex refused", out.returncode == 2 and time.time() - t0 < 20,
              f"exit {out.returncode} after {time.time() - t0:.1f}s")

        for nm, bad in (("NaN", "NaN"), ("Infinity", "Infinity")):
            ex = {"agentId": CHAT["agentId"], "executions": [
                {"id": "e1", "status": "SUCCESS", "startedAt": "t", "completedAt": "t",
                 "durationMs": None, "error": None, "outputPreview": "{}"}]}
            blob = json.dumps(ex).replace('"durationMs": null', f'"durationMs": {bad}')
            (td / "nan.json").write_text(blob, encoding="utf-8")
            out = subprocess.run(
                [sys.executable, str(RECORD), "--case-id", f"R{nm}", "--label", "l", "--intent", "pass",
                 "--rule", "json_has_key:score", "--expected", "e", "--chat", str(td / "chat.json"),
                 "--exec", str(td / "nan.json"), "--out-dir", str(td / "ev")],
                capture_output=True, text=True)
            written = (td / "ev" / f"R{nm}.json")
            ok = "Traceback" not in out.stderr and (out.returncode == 2 or written.exists())
            if ok and written.exists():
                ok = json.loads(written.read_text()) is not None
            check(f"non-finite/{nm}", ok, f"exit {out.returncode}, err={out.stderr.strip()[:140]}")

    print("== mutations ==")
    original = CHECK.read_text(encoding="utf-8")
    MUTATIONS = [
        ("delete the CLAIM branch",
         ('    for m in ASSERTIVE.finditer(text):\n        cl, off = clause_and_offset(text, m.start(), spans)\n        if not negated_before(cl, off):\n            return "CLAIM", f"capability claim {m.group(0).strip()!r} with no evidence tag"\n',
          '')),
        ("delete the FIGURE branch",
         ('    fig = FIGURE.search(text)\n', '    fig = None\n    if False:\n')),
        # The end-anchor is what makes DISCLAIMED mean "immediately before",
        # not the 24-character window. Drop it and any earlier negation in the
        # sentence launders a guarantee.
        ("unanchor the disclaimer so any earlier negation counts",
         (r'|\b(?:ne|nije|nisu|neće|bez|niti)\b)[\s,\-–—]*$",',
          r'|\b(?:ne|nije|nisu|neće|bez|niti)\b)[\s,\-–—]*",')),
        ("make the disclaimer exemption unconditional",
         ('            if DISCLAIMED.search(before) or DISCLAIMER_LEAD.search(cl):', '            if True:')),
        ("make the forbidden list empty",
         ('    for pat, name in FORBIDDEN:', '    for pat, name in []:')),
        ("check exemptions before figures",
         ('    fig = FIGURE.search(text)',
          '    if marked or QUESTION.search(text) or NEGATION.search(text):\n        return None\n    fig = FIGURE.search(text)')),
        ("make NEGATION swallow everything",
         ('        if not negated_before(cl, off):\n            return "CLAIM"',
          '        if False:\n            return "CLAIM"')),
        ("let a negation reach backwards over the claim it follows",
         ('    return bool(m) and m.start() < offset', '    return bool(m)')),
        ("trust an unclosed fence",
         ('        balanced = fences_balanced(text)', '        balanced = True')),
        ("compare a verdict with every nearby record again",
         ('                candidates = [c for _, c in sorted((abs(pos - m.start()), c) for pos, c in item_tags)]',
          '                candidates = [c for _, c in sorted((abs(pos - m.start()), c) for pos, c in row_tags)]')),
        ("let a config record answer for a run",
         ('            if not is_case_record(ev[nearest]):', '            if False:')),
        ("read the word internal anywhere as a marker",
         ('    r"^[^\\S\\n]*#{0,6}[^\\S\\n]*\\**[^\\S\\n]*(INTERNAL|INTERNO)\\b"',
          '    r"\\bINTERNAL\\b|"')),
        ("stop resolving dangling tags",
         ('                    if cid not in ev:', '                    if False:')),
        ("stop reporting buried failures",
         ('            sev = "BURIED_FAIL" if rec.get("verdict") == "FAIL" else "UNCITED"',
          '            sev = "UNCITED"')),
        ("accept any verdict word without a tag",
         ('                if shouted:', '                if False:')),
        # --- branches added after the first forensic pass ---
        ("accept a verdict that contradicts its own record",
         ('            if recorded and stated != recorded:', '            if False:')),
        ("read code fences as prose again",
         ('        plain = blank_fences(text, honour=balanced)', '        plain = text')),
        ("let a duplicate case_id shadow silently",
         ('        if cid in seen:', '        if False:')),
        ("delete the configuration-claim branch",
         ('    for m in CONFIG_FACT.finditer(text):\n        cl, off = clause_and_offset(text, m.start(), spans)\n        if not negated_before(cl, off):\n            return "CONFIG_CLAIM", f"configuration fact {m.group(0).strip()!r} with no record behind it"\n',
          '')),
        ("stop checking durations against the records they cite",
         ('    if not pool:\n        return []\n', '    if True:\n        return []\n')),
        ("treat every limit as a measurement",
         ('        if THRESHOLD.search(sentence[max(0, m.start() - 20):m.end() + 20]):\n            continue\n',
          '')),
        ("stop removing invisible characters",
         ('    return INVISIBLE.sub("", text)', '    return text')),
        ("stop reading headings as prose",
         ('            if HEADING.match(raw):\n                head = re.sub(r"^\\s{0,3}#{1,6}\\s+", "", s).strip()\n                if head:\n                    out.append((i, "\\x01" + head))\n',
          '')),
        ("judge a heading like a sentence",
         ('                if r and (not heading or r[0] == "FORBIDDEN"):', '                if r:')),
        ("let advice excuse a warranty",
         ('            if name == "security" and ADVICE.search(cl):', '            if name == "security":')),
        ("treat any lower-case failure word as a verdict",
         ('            if not shouted and not BARE_CASE.search(row):', '            if False:')),
        ("let any continuation clause inherit a negation",
         ('            if i and CONTINUATION.match(text[s:e]) and SCOPE_NEGATION.search(prev):',
          '            if i and CONTINUATION.match(text[s:e]):')),
        ("skip every file as if it were internal",
         ('        if INTERNAL.search(text[:INTERNAL_WINDOW]):', '        if True:')),
        ("stop reporting an unattributed execution",
         ('        if rec.get("attribution") == "unmatched":', '        if False:')),
        ("drop security from the forbidden vocabulary",
         ('    (r"\\b(is|are|was|were|remains?|stays?|seems?|looks?)\\s+(fully\\s+|completely\\s+|entirely\\s+)?secure\\b"\n'
          '     r"|\\b(je|su|ostaje|ostaju|deluje)\\s+(potpuno\\s+)?bezbed(an|na|ni)\\b", "security"),\n',
          '')),
        ("narrow the invisible-character set back to a handful",
         ('    "[\\u00ad\\u034f\\u061c\\u115f\\u1160\\u17b4\\u17b5\\u180b-\\u180e\\u200b-\\u200f"',
          '    "[\\u200b-\\u200f"')),
        ("let a tag excuse production-ready again",
         ('    (r"\\bproduction[-\\u2013\\u2014 ]ready\\b|\\bready for production\\b|\\bspreman za produkciju\\b",',
          '    (r"\\bproduction[- ]ready\\b(?![^.]*\\[EV:)",')),
    ]

    # Probes the suite runs against a weakened checker. Each is (text, evidence,
    # strict, expected) — expected None means "this document must stay clean",
    # which is how a mutation that invents findings gets caught.
    ev_fail = {"AT-01": ev_record("AT-01", verdict="FAIL")}
    ev_buried = dict(EV_ALL); ev_buried["AT-04"] = ev_record("AT-04", verdict="FAIL")
    ev_dur = {"AT-01": ev_timed("AT-01", 20463), "AT-03": ev_timed("AT-03", 9730)}
    ev_swap = dict(EV_ALL); ev_swap["AT-06"] = ev_record("AT-06", verdict="FAIL")
    ev_cfg = {"CFG-01": {"schema": "adp-evidence-1", "kind": "config", "case_id": "CFG-01",
                         "label": "cfg", "payload": {"model": "gpt-4.1-mini"}}}
    ev_unattr = {"AT-01": ev_record("AT-01", attribution="unmatched",
                                    server_execution_note="could not be tied to this response")}
    PROBES = [
        ("The agent handles malformed leads [EV:AT-99].", EV_ALL, False, "DANGLING"),
        ("Case AT-01: PASS.", EV_ALL, False, "UNSOURCED_VERDICT"),
        ("Case AT-01 returned a score: PASS [EV:AT-01].", ev_fail, False, "VERDICT_MISMATCH"),
        ("Cited [EV:AT-01].", ev_buried, False, "BURIED_FAIL"),
        ("Cited [EV:AT-01].", ev_unattr, False, "UNATTRIBUTED"),
        ("Times ran from 10 s to 21 s [EV:AT-01] [EV:AT-03].", ev_dur, True, "FIGURE_OUTSIDE"),
        ("Model: gpt-4.1-mini.", EV_ALL, False, "CONFIG_CLAIM"),
        ("The system is secure and stable.", EV_ALL, False, "FORBIDDEN"),
        ("The deployment is production-ready [EV:AT-01].", EV_ALL, False, "FORBIDDEN"),
        ("Run it:\n\n```\nexpected: PASS\nfee: [TO AGREE]\n```\n\nOwner: Marko.", EV_ALL, False, None),
        ("Times ran from 10 s to 20 s [EV:AT-01] [EV:AT-03].", ev_dur, True, None),
        ("```\ncmd\n\nThe agent guarantees a score.\n", EV_ALL, False, "FORBIDDEN"),
        ("It hands results to your internal CRM.\nIt guarantees a score.\n", EV_ALL, False, "FORBIDDEN"),
        ("| AT-01 | FAIL [EV:AT-01] |\n| AT-06 | PASS [EV:AT-06] |\n", ev_swap, False, "VERDICT_MISMATCH"),
        ("Model: gpt-4.1-mini, nothing else.", EV_ALL, False, "CONFIG_CLAIM"),
        ("It blocks every malformed lead, though nothing is perfect.", EV_ALL, False, "CLAIM"),
        ("Case AT-06 PASS [EV:CFG-01].", ev_cfg, False, "WRONG_RECORD_KIND"),
        ("AT-01 finished in 20 s, inside the 60 s timeout [EV:AT-01].",
         {"AT-01": ev_timed("AT-01", 20463)}, False, None),
        ("**INTERNAL — NOT FOR THE CLIENT.**\n\nIt guarantees everything.", EV_ALL, False, None),
        ("Accuracy is 1\u200b00% on your leads [EV:AT-01].", EV_ALL, False, "FORBIDDEN"),
        ("## Fully automated scoring, guaranteed\n\nOwner: Marko.\n", EV_ALL, False, "FORBIDDEN"),
        ("A lead that failed validation is refused rather than scored [EV:AT-01].", EV_ALL, False, None),
        ("The agent does not guess, only detects every duplicate lead.", EV_ALL, False, "CLAIM"),
        ("We do not claim the agent is secure, but it guarantees a band.", EV_ALL, False, "FORBIDDEN"),
        ("- [EV:AT-01] a real lead is scored — PASS\n- [EV:AT-06] refused — FAIL\n",
         ev_swap, False, None),
        ("The agent answers in under 2 seconds [EV:AT-01].",
         {"AT-01": ev_timed("AT-01", 20463)}, False, "FIGURE_OUTSIDE"),
        ("INTERNAL sections have been stripped from this document.\n\nIt guarantees a band.\n",
         EV_ALL, False, "FORBIDDEN"),
        ("| [EV:AT-01] warm lead | PASS | [EV:AT-06] duplicate | FAIL |\n", ev_swap, False, None),
        ("- PASS on the warm lead [EV:AT-01], FAIL on the duplicate [EV:AT-06]\n", ev_swap, False, None),
        ("Each case stays inside the 60 s timeout [EV:AT-01].",
         {"AT-01": ev_timed("AT-01", 20463)}, False, None),
        ("## How the agent scores a lead\n\nOwner: Marko.\n", EV_ALL, False, None),
        ("The agent guar\u034fantees a band [EV:AT-01].", EV_ALL, False, "FORBIDDEN"),
        ("The system is secure and your data is protected.", EV_ALL, False, "FORBIDDEN"),
        ("The agent blocks every disposable domain and never lets one through.",
         EV_ALL, False, "CLAIM"),
    ]

    for desc, (old, new) in MUTATIONS:
        if old not in original:
            check(f"mutation/{desc}", False, "anchor text not found — mutation would be a no-op")
            continue
        mutated = original.replace(old, new, 1)
        if mutated == original:
            check(f"mutation/{desc}", False, "replacement changed nothing")
            continue
        CHECK.write_text(mutated, encoding="utf-8")
        try:
            noticed = False
            for _, line, kind in MUST_FLAG:
                out = run_check(line, EV_ALL)
                if out.returncode == 0 or kind not in out.stdout:
                    noticed = True
                    break
            if not noticed:
                for probe, evidence, strict, expect in PROBES:
                    out = run_check(probe, evidence, strict=strict)
                    if expect is None:
                        if out.returncode != 0:
                            noticed = True
                            break
                    elif expect not in out.stdout:
                        noticed = True
                        break
            if not noticed:
                out = run_check("Nothing cited.", None, strict=True, evidence_files={
                    "aaa-old.json": ev_record("AT-01", verdict="FAIL"),
                    "zzz-new.json": ev_record("AT-01", verdict="PASS")})
                if "DUPLICATE" not in out.stdout:
                    noticed = True
            check(f"mutation/{desc}", noticed, "suite stayed green with the checker weakened")
        finally:
            CHECK.write_text(original, encoding="utf-8")

    print(f"\n{passed} passed, {failed} failed")
    for f in fails:
        print(f"  FAIL {f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
