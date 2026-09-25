#!/usr/bin/env python3
"""
registry_write.py

Sigurno upisuje u deljeni registry.json koji prati sve aktivne
agent-worktree-ove.

NAPOMENA (posle nezavisnog audita - treći krug provere): prva verzija ovog
fajla je tvrdila da radi "compare-and-swap" (pročitaj hash -> proveri hash
ponovo -> upiši ako se poklapa), ali je to bio TOCTOU (time-of-check-to-
time-of-use) bag, ne stvarna zaštita: druga provera hash-a se dešavala
odmah posle prve, u istom procesu, bez ičega što bi sprečilo DRUGI proces
da upiše u procepu između te provere i stvarnog `os.rename()`. Nezavisan
test (30 paralelnih pisaca na različite task-id-jeve) je pokazao da se
gubi ~30% upisa - potvrđeno i drugim nezavisnim testom (subagent) na
većem broju paralelnih pisaca sa sličnim rezultatom. To NIJE bila stvarna
optimistic-concurrency zaštita.

Ispravka: prava međusobna isključivost (mutual exclusion) preko
`fcntl.flock()` na posebnom `.lock` fajlu, drži se tokom CELE
read-modify-write kritične sekcije (uključujući atomični `os.rename`).
Ovo je standardan, industrijski obrazac za bezbedan konkurentan upis u
deljeni fajl (isti princip kao npr. Python `filelock` biblioteka ili
SQLite-ov file locking) - jednostavniji i STVARNO ispravan, za razliku od
prethodne "optimistic" verzije koja je zvučala sofisticirano ali nije
radila. `fcntl.flock` je POSIX-specifičan (radi na Linux/macOS, ne na
Windows-u) - dovoljno za ovaj kontekst (macOS/Linux dev mašine).

Posle ove ispravke, isti test (30 paralelnih pisaca) je ponovljen i SVIH
30 zadataka je upisano bez gubitka - vidi references/AUDIT-nalaz.md.
"""
import argparse
import json
import os
import time
import fcntl
import sys


def load_registry(path: str):
    if not os.path.exists(path):
        return {"version": 0, "tasks": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def atomic_write(path: str, data: dict):
    tmp_path = f"{path}.tmp.{os.getpid()}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.rename(tmp_path, path)  # atomično na POSIX


def upsert_task(registry: dict, task_id: str, **fields):
    registry.setdefault("tasks", {})
    entry = registry["tasks"].setdefault(task_id, {})
    entry.update(fields)
    entry["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    registry["version"] = registry.get("version", 0) + 1
    return registry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--branch")
    ap.add_argument("--worktree")
    ap.add_argument("--status", required=True)
    args = ap.parse_args()

    registry_dir = os.path.dirname(args.registry) or "."
    os.makedirs(registry_dir, exist_ok=True)

    lock_path = f"{args.registry}.lock"
    # Otvaramo lock fajl (kreira se ako ne postoji) i držimo ekskluzivni
    # OS-level lock kroz CELU kritičnu sekciju - ovo je stvarna zaštita,
    # ne hash provera koja se dešava prerano.
    with open(lock_path, "w") as lockf:
        fcntl.flock(lockf, fcntl.LOCK_EX)  # blokira dok se ne oslobodi
        try:
            registry = load_registry(args.registry)

            fields = {"status": args.status}
            if args.branch:
                fields["branch"] = args.branch
            if args.worktree:
                fields["worktree"] = args.worktree

            updated = upsert_task(registry, args.task_id, **fields)
            atomic_write(args.registry, updated)
            print(f"OK: task '{args.task_id}' upisan (registry version={updated['version']})")
            return 0
        except (OSError, json.JSONDecodeError) as e:
            print(f"GREŠKA: registry_write nije uspeo: {e}", file=sys.stderr)
            return 2
        finally:
            fcntl.flock(lockf, fcntl.LOCK_UN)


if __name__ == "__main__":
    raise SystemExit(main())
