#!/usr/bin/env python3
"""
coverage_check.py <base_branch> <coverage_json_path>

Stavka #3 ojacavanja (checker-verify.sh gruba heuristika "test pokriva
promenu"). Umesto "da li je BILO KOJI test fajl dotaknut negde u diff-u",
ovo racuna jaci signal: da li su LINIJE koje su stvarno IZMENJENE u
ne-test .py fajlovima stvarno IZVRSENE tokom test run-a (coverage.py
podaci), ne samo da li test fajl postoji negde u istom diff-u.

Ulaz:
  <base_branch>       - grana protiv koje se racuna git diff (single-ref,
                         isti obrazac kao prepare-checker-bundle.sh - vidi
                         napomenu tamo o "git diff <base>" vs dve-tacke opsegu)
  <coverage_json_path> - putanja do coverage.py JSON izvestaja
                         (`coverage json` / `pytest --cov-report=json:<path>`)

Izlaz (stdout, JSON):
  {"checked": true, "all_changed_lines_covered": bool,
   "files": {"<path>": {"changed_lines": [...], "covered_lines": [...],
                          "uncovered_lines": [...]}}}
  ili
  {"checked": false, "reason": "..."}  - caller (checker-verify.sh) MORA
  tada pasti nazad na (ispravljenu) heuristiku, ne sme tiho tvrditi
  pokrivenost koju nije uspeo da izmeri.

Fail-safe pravilo: ako promenjeni fajl uopste nije pomenut u coverage.json
(nije uvezen tokom testova, ili je putanja drugacije normalizovana),
tretira se kao POTPUNO nepokriven, ne preskace se cutke - bolje potceniti
pokrivenost nego lazno je precenti.

NEZAVISAN REVIEW (16. sept 2026, Runda review stavke #3) - tri nalaza
ispravljena ovde:
  B2 - `git diff` po default-u (core.quotePath=true) kvotuje/oktalno-eskejpuje
       putanje sa ne-ASCII karakterima (npr. cirilica - ovaj projekat ima
       zive cirilica-konverter/cirilica-history-cleanup demo worktree-ove) u
       `+++ ` header-ima, pa se path parsiranje ovde potpuno lomilo za takve
       fajlove (nikad se ne poklopi sa coverage.json kljucem, SVAKA linija
       lazno prijavljena kao nepokrivena). Ispravka: `-c core.quotePath=false`
       na git diff pozivu.
  B3 - is_test_file() nije prepoznavao `spec/` direktorijum ni
       `spec_*.py`/`*_spec.py` obrazac, za razliku od bash classify_file()
       u checker-verify.sh (koji ima `*/spec/*` granu) - spec-stil test
       fajlovi su bili pogresno tretirani kao "logika koju treba pokriti".
       Ispravka: isti obrazac dodat ovde.
  B4 - changed_python_lines() je vracao CEO opseg hunk header-a, ukljucujuci
       prazne linije i komentare, koje coverage.py nikad ne belezi u
       executed_lines (nisu "statements") - pa je SVAKA takva linija bila
       lazno prijavljena kao "nepokrivena", cak i za funkciju koja je 100%
       pokrivena a promena je bila cisto kozmeticka (komentar/prazna linija).
       Ispravka: presek promenjenih linija sa "trackable" skupom
       (executed_lines UNION missing_lines iz coverage.json) - linije van tog
       skupa (nisu statements) se potpuno izbacuju iz razmatranja, ne broje
       se ni kao pokrivene ni kao nepokrivene. Kad `missing_lines` nije
       prisutan u coverage.json (stariji coverage.py bez tog polja), trackable
       skup se ne moze pouzdano odrediti - pada se nazad na STARO ponasanje
       (ceo promenjeni opseg), namerno konzervativno umesto tiho pogresno.
"""
import sys
import os
import json
import re
import subprocess


def changed_python_lines(base_branch):
    """Vraca ({filepath: set(izmenjenih/dodatih linija u NOVOJ verziji)}, None)
    ili (None, greska), parsiranjem `git diff -U0 <base_branch> -- *.py`
    unified diff hunk header-a (@@ -a,b +c,d @@). Cisto-delete hunk (+0
    linija u novoj verziji) se preskace - nema novih/izmenjenih linija koje
    bi trebalo da budu pokrivene."""
    try:
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "diff", "-U0", base_branch, "--", "*.py"],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return None, f"git diff nije uspeo da se pokrene: {e}"
    if result.returncode != 0:
        return None, f"git diff je vratio gresku (exit {result.returncode}): {result.stderr.strip()[:300]}"

    files = {}
    current_file = None
    for line in result.stdout.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path == "/dev/null":
                current_file = None
                continue
            current_file = path[2:] if path.startswith("b/") else path
            continue
        if line.startswith("@@") and current_file is not None:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if not m:
                continue
            start = int(m.group(1))
            count = int(m.group(2)) if m.group(2) is not None else 1
            if count == 0:
                continue
            files.setdefault(current_file, set()).update(range(start, start + count))
    return files, None


def is_test_file(path):
    base = os.path.basename(path)
    if base.startswith("test_") or base.endswith("_test.py"):
        return True
    if base.startswith("spec_") or base.endswith("_spec.py"):
        return True
    parts = path.split("/")[:-1]
    return any(p in ("tests", "test", "__tests__", "spec") for p in parts)


def main():
    if len(sys.argv) != 3:
        print(json.dumps({"checked": False, "reason": "usage: coverage_check.py <base_branch> <coverage_json_path>"}))
        return

    base_branch, coverage_json_path = sys.argv[1], sys.argv[2]

    changed, err = changed_python_lines(base_branch)
    if err:
        print(json.dumps({"checked": False, "reason": err}))
        return

    changed = {f: lines for f, lines in changed.items() if not is_test_file(f) and lines}
    if not changed:
        print(json.dumps({"checked": False, "reason": "nema izmenjenih ne-test .py fajlova sa dodatim/izmenjenim linijama"}))
        return

    if not os.path.isfile(coverage_json_path):
        print(json.dumps({"checked": False, "reason": f"{coverage_json_path} ne postoji (coverage run nije proizveo izvestaj)"}))
        return
    try:
        with open(coverage_json_path, "r", encoding="utf-8") as f:
            cov = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(json.dumps({"checked": False, "reason": f"coverage.json necitljiv: {e}"}))
        return

    cov_files = cov.get("files", {})
    result_files = {}
    all_covered = True
    for path, lines in changed.items():
        # coverage.py kljucevi su obicno relativni putevi od cwd-a gde je
        # `coverage`/`pytest --cov` pokrenut - probaj nekoliko uobicajenih
        # normalizacija pre nego sto odustanemo.
        entry = (
            cov_files.get(path)
            or cov_files.get("./" + path)
            or cov_files.get(os.path.normpath(path))
        )
        if entry is None:
            # Fail-safe: fajl uopste nije u coverage.json (nikad uvezen) -
            # ne mozemo znati koje su linije "trackable", pa CEO promenjeni
            # opseg tretiramo kao nepokriven (konzervativno, ne cutke).
            covered = []
            uncovered = sorted(lines)
        else:
            executed = set(entry.get("executed_lines", []))
            missing = entry.get("missing_lines")
            if missing is None:
                # B4 fallback: bez missing_lines ne mozemo razlikovati
                # "nepokriven statement" od "prazna linija/komentar" - staro,
                # konzervativno ponasanje (ceo promenjeni opseg).
                covered = sorted(lines & executed)
                uncovered = sorted(lines - executed)
            else:
                trackable = executed | set(missing)
                considered = lines & trackable  # ignorisi prazne/komentar linije
                covered = sorted(considered & executed)
                uncovered = sorted(considered - executed)
        result_files[path] = {
            "changed_lines": sorted(lines),
            "covered_lines": covered,
            "uncovered_lines": uncovered,
        }
        if uncovered:
            all_covered = False

    print(json.dumps({
        "checked": True,
        "all_changed_lines_covered": all_covered,
        "files": result_files,
    }))


if __name__ == "__main__":
    main()
