#!/usr/bin/env python3
"""
circuit_breaker.py

Sprovodi Hard Ceiling i detekciju "beskonačne refleksije" (ponovljena
greška ili nulti napredak kroz više iteracija). Namerno je OVO orkestrator-
skript, van modelovog domašaja - agent koji je zapao u petlju se ne može
osloniti da sam primeti da je premašio limit.

Poziva se posle SVAKE iteracije (posle checker-verify.sh), sa rezultatom
te iteracije. Ažurira loop_state.json i vraća odluku: CONTINUE / STOP.

Usage:
    python3 circuit_breaker.py --state .agent/loop_state.json \
        --verify-status FAIL --error-signature "<hash ili tekst greske>" \
        --lines-changed 3

Exit codes:
    0 = CONTINUE (dozvoljena sledeća iteracija)
    1 = STOP - Hard Ceiling (max iteracija ili wall-clock) dostignut
    2 = STOP - Circuit breaker "otvoren" (ponovljena greška, nema napretka,
        oštećen/neočekivan state, ili detektovan clock skew) - sve ove
        slučajeve tretiramo kao STOP, ne kao crash, jer je "stani i pitaj
        čoveka" bezbedniji default od "nastavi bez nadzora kad nešto ne
        razumemo o sopstvenom stanju"
    3 = STOP - Verify PASS, zadatak završen (model-based exit)

NAPOMENA (treći krug provere, nezavisna verifikacija): prva verzija je
pretpostavljala da je `loop_state.json` uvek dobro-formiran (npr.
`error_signatures` je lista, `max_iterations` postoji) i da je `started_at`
uvek u prošlosti. Oštećen state fajl ili pomeren sistemski sat bi izazvao
nezahvaćen crash (loše: nejasan exit kod, agent možda ne zna da li da stane)
ili tih pogrešan rezultat (npr. negativan "elapsed" bi trajno onesposobio
wall-clock ogradu). Ispravljeno da oba slučaja eksplicitno vode ka STOP.

STAVKA #4 OJAČAVANJA (16. sept 2026 - nema file-lock ako se ikad doda drugi
pisac u loop_state.json): dizajn je bio jedan-proces-po-worktree-u, pa je
originalno load_state/save_state (read-modify-write BEZ ikakve zaštite)
bio bezopasan U TOM SPECIFIČNOM kontekstu. Ali ovo je TAČNO isti oblik
lost-update rase koji je već nađen i ispravljen u registry_write.py (vidi
tamošnju napomenu o TOCTOU bagu i "30 paralelnih pisaca" testu) - samo nad
loop_state.json umesto registry.json. Baseline test (20 KONKURENTNIH
circuit_breaker.py poziva na isti loop_state.json, bez lock-a): 9/20 (45%)
upisa izgubljeno - iteration_count završio na 11 umesto 20, error_signatures
i lines_changed_history nizovi isto skraćeni. Ovo je OZBILJNIJE od
registry.json slučaja jer je circuit_breaker.py SAMA bezbednosna ograda
(Hard Ceiling, repeated-error/no-progress trip) - izgubljeni upisi bi
mogli tiho onesposobiti baš tu ogradu (iteration_count potcenjen =
Hard Ceiling nikad ne okine; izgubljeni error_signatures/lines_changed_history
unosi = repeated-error/no-progress trip nikad ne okine) ako se ikad pojavi
drugi pisac (npr. supervizor/monitoring proces, ili bag koji duplira poziv).
Ispravka: ISTI, već proveren obrazac kao registry_write.py - `fcntl.flock()`
ekskluzivni lock na posebnom `.lock` fajlu, drži se kroz CELU
read-modify-write kritičnu sekciju (od load_state do save_state/rename).
Posle ispravke, isti test (20 konkurentnih poziva) ponovljen: 20/20 upisa,
bez gubitka - vidi OJACAVANJE-stavka4-circuit-breaker-lock.md.

RUNDA REVIEW (nezavisan review, 16. sept 2026, isti dan): potvrdio glavni
mehanizam (baseline/retest/regresija/stres test nezavisno reprodukovani),
ali našao dva nalaza u samoj lock-ispravci - H3 (CONFIRMED bag: lock fajl
kao direktorijum je bacao goli traceback umesto STOP+JSON) i H1 (legitiman
nov rizik: beskonačno blokirajući flock bez timeout-a, u tenziji sa
filozofijom "STOP je bezbedniji default"). Oba ispravljena - vidi main()
niže i "Runda review" sekciju u OJACAVANJE-stavka4-circuit-breaker-lock.md.
"""
import argparse
import json
import hashlib
import time
import calendar
import os
import fcntl
import sys

REPEATED_ERROR_THRESHOLD = 3   # ista greška N puta zaredom -> trip
NO_PROGRESS_THRESHOLD = 3      # N iteracija sa ~0 izmenjenih linija -> trip
NO_PROGRESS_LINE_FLOOR = 2     # "skoro nula" izmena


def sig_hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:16]


def load_state(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(path: str, state: dict):
    # STAVKA #4: PID-sufiks na tmp imenu, isti obrazac kao registry_write.py
    # atomic_write - nije striktno neophodno sad kad je pristup serijalizovan
    # preko fcntl.flock-a (samo jedan proces drži lock u datom trenutku), ali
    # je jeftina odbrambena doslednost sa već proverenim obrascem.
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.rename(tmp, path)


def _run(args) -> int:
    """Cela postojeca logika, nepromenjena - sad se poziva ISKLJUCIVO dok je
    fcntl.flock ekskluzivni lock drzan (vidi main())."""
    try:
        state = load_state(args.state)
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({
            "decision": "STOP", "reason": "state_file_unreadable", "detail": str(e),
            "escalate_to_human": True,
        }, ensure_ascii=False))
        return 2

    # Odbrambena validacija oblika state-a (posle audita) - ne pretpostavljati
    # da je fajl dobro-formiran; STOP + eskalacija je bezbedniji default od
    # nezahvaćenog crash-a ili tihog nastavka sa pogrešnim vrednostima.
    required = ["iteration_count", "max_iterations", "started_at", "max_wall_clock_sec"]
    missing = [k for k in required if k not in state]
    if missing:
        print(json.dumps({
            "decision": "STOP", "reason": "state_missing_fields", "missing": missing,
            "escalate_to_human": True,
        }, ensure_ascii=False))
        return 2
    if not isinstance(state.get("error_signatures"), list):
        state["error_signatures"] = []
    if not isinstance(state.get("lines_changed_history"), list):
        state["lines_changed_history"] = []

    state["iteration_count"] += 1

    # --- Model-based exit ---
    if args.verify_status == "PASS":
        state["status"] = "completed"
        save_state(args.state, state)
        print(json.dumps({"decision": "STOP", "reason": "verify_passed"}, ensure_ascii=False))
        return 3

    # --- Hard Ceiling: max iteracije ---
    if state["iteration_count"] >= state["max_iterations"]:
        state["status"] = "blocked_hard_ceiling_iterations"
        save_state(args.state, state)
        print(json.dumps({
            "decision": "STOP",
            "reason": "hard_ceiling_iterations",
            "iteration_count": state["iteration_count"],
            "max_iterations": state["max_iterations"],
        }, ensure_ascii=False))
        return 1

    # --- Hard Ceiling: wall clock ---
    # NAPOMENA (fix posle audita): started_at je UTC (generisan sa `date -u`).
    # time.mktime() interpretira struct_time kao LOKALNO vreme, pa bi na
    # bilo kojoj mašini van UTC+0 (npr. Europe/Podgorica, UTC+2) elapsed
    # bio pogrešno preračunat i wall-clock circuit breaker bi okidao u
    # pogrešnom trenutku. calendar.timegm() ispravno tretira struct_time
    # kao UTC, bez konverzije vremenske zone.
    try:
        started = time.strptime(state["started_at"], "%Y-%m-%dT%H:%M:%SZ")
        started_epoch_utc = calendar.timegm(started)
    except ValueError as e:
        print(json.dumps({
            "decision": "STOP", "reason": "invalid_started_at", "detail": str(e),
            "escalate_to_human": True,
        }, ensure_ascii=False))
        return 2
    elapsed = time.time() - started_epoch_utc
    if elapsed < 0:
        # Clock skew (sistemski sat pomeren unazad, ili started_at pokvaren
        # ručnom izmenom) - "nastavi kao da ništa nije prošlo" bi trajno
        # onesposobilo wall-clock ogradu. Failuj bezbedno: stani i eskaliraj.
        print(json.dumps({
            "decision": "STOP", "reason": "clock_skew_detected", "elapsed_sec": int(elapsed),
            "escalate_to_human": True,
        }, ensure_ascii=False))
        return 2
    if elapsed >= state["max_wall_clock_sec"]:
        state["status"] = "blocked_hard_ceiling_wallclock"
        save_state(args.state, state)
        print(json.dumps({
            "decision": "STOP",
            "reason": "hard_ceiling_wallclock",
            "elapsed_sec": int(elapsed),
        }, ensure_ascii=False))
        return 1

    # --- Circuit breaker: ponovljena greška ---
    if args.error_signature:
        h = sig_hash(args.error_signature)
        state.setdefault("error_signatures", []).append(h)
        recent = state["error_signatures"][-REPEATED_ERROR_THRESHOLD:]
        if len(recent) == REPEATED_ERROR_THRESHOLD and len(set(recent)) == 1:
            state["status"] = "blocked_repeated_error"
            save_state(args.state, state)
            print(json.dumps({
                "decision": "STOP",
                "reason": "repeated_error",
                "signature": h,
                "occurrences": REPEATED_ERROR_THRESHOLD,
                "escalate_to_human": True,
            }, ensure_ascii=False))
            return 2

    # --- Circuit breaker: nema napretka ---
    state.setdefault("lines_changed_history", []).append(args.lines_changed)
    recent_progress = state["lines_changed_history"][-NO_PROGRESS_THRESHOLD:]
    if (len(recent_progress) == NO_PROGRESS_THRESHOLD
            and all(n <= NO_PROGRESS_LINE_FLOOR for n in recent_progress)):
        state["status"] = "blocked_no_progress"
        save_state(args.state, state)
        print(json.dumps({
            "decision": "STOP",
            "reason": "no_progress",
            "recent_lines_changed": recent_progress,
            "escalate_to_human": True,
        }, ensure_ascii=False))
        return 2

    # --- Nastavi ---
    save_state(args.state, state)
    print(json.dumps({
        "decision": "CONTINUE",
        "iteration_count": state["iteration_count"],
        "max_iterations": state["max_iterations"],
    }, ensure_ascii=False))
    return 0


LOCK_TIMEOUT_SEC = 30       # H1 (Runda review stavke #4) - vidi napomenu ispod
LOCK_POLL_INTERVAL_SEC = 0.1


def _stop_json(reason: str, **extra) -> int:
    payload = {"decision": "STOP", "reason": reason, "escalate_to_human": True}
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False))
    return 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--verify-status", required=True, choices=["PASS", "FAIL"])
    ap.add_argument("--error-signature", default="")
    ap.add_argument("--lines-changed", type=int, default=0)
    args = ap.parse_args()

    # STAVKA #4: ekskluzivni fcntl.flock na posebnom `.lock` fajlu, drzan
    # kroz CELU read-modify-write kriticnu sekciju (_run) - isti obrazac kao
    # vec proveren u registry_write.py. Lock fajl je pored samog state fajla
    # (npr. .agent/loop_state.json.lock), pravi se ako ne postoji.
    #
    # RUNDA REVIEW (nezavisan review, 16. sept 2026) - dva nalaza ispravljena:
    #
    # H3 (CONFIRMED bag): otvaranje lock fajla (i os.makedirs njegovog
    # direktorijuma) nije bilo nicim zasticeno - ako `{state}.lock` VEC
    # POSTOJI kao DIREKTORIJUM (ili je nedostupan iz nekog drugog OSError
    # razloga), skripta je bacala GOLI Python traceback (IsADirectoryError),
    # BEZ strukturiranog STOP JSON-a na stdout, sa pogresnim exit kodom 1
    # (koji pozivalac moze pogresno protumaciti kao Hard Ceiling, ne kao
    # crash). Ispravka: uhvati OSError oko makedirs/open, vrati isti
    # STOP+JSON+escalate obrazac kao sve ostale greske u ovom fajlu.
    #
    # H1 (legitiman, nov arhitektonski rizik): `fcntl.flock` BEZ `LOCK_NB`/
    # timeout-a blokira NEODREDJENO. Pre ove ispravke nijedan lock nije
    # postojao, pa zaglavljen proces NIKAD nije mogao blokirati drugi - sad
    # MOZE (npr. hipoteticki buduci drugi pisac koji ostane ziv ali
    # zaglavljen, ne ubijen - `kill -9` slucaj je testiran i OS ispravno
    # automatski oslobadja flock, ali "ziv i zaglavljen" ostaje rizik). Ovo
    # je u tenziji sa filozofijom ovog fajla ("STOP je bezbedniji default od
    # tihog visenja bez nadzora" - vidi npr. clock_skew_detected iznad).
    # Ispravka: ogranicen broj pokusaja sa `LOCK_EX | LOCK_NB` (ne beskonacno
    # blokirajuci goli `LOCK_EX`) do LOCK_TIMEOUT_SEC - ako lock nikad ne
    # oslobodi u tom roku, vrati STOP+JSON (reason="lock_timeout",
    # escalate_to_human=true) umesto vecnog cekanja.
    lock_dir = os.path.dirname(args.state) or "."
    lock_path = f"{args.state}.lock"
    try:
        os.makedirs(lock_dir, exist_ok=True)
        lockf = open(lock_path, "w")
    except OSError as e:
        return _stop_json("lock_unavailable", detail=str(e))

    try:
        deadline = time.monotonic() + LOCK_TIMEOUT_SEC
        acquired = False
        while time.monotonic() < deadline:
            try:
                fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except BlockingIOError:
                time.sleep(LOCK_POLL_INTERVAL_SEC)
        if not acquired:
            return _stop_json("lock_timeout", timeout_sec=LOCK_TIMEOUT_SEC)
        try:
            return _run(args)
        finally:
            fcntl.flock(lockf, fcntl.LOCK_UN)
    finally:
        lockf.close()


if __name__ == "__main__":
    raise SystemExit(main())
