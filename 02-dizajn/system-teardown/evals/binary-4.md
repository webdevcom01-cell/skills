# Run `binary-4` — raw output

| | |
|---|---|
| Target type | binary/protocol |
| Target / pin | ~/.claude/.git/index (DIRC v2), held-out ~/agency-agents/.git/index |
| Verdict | **FAIL** |
| session_id | `303c7a24-d8b6-4023-bc4c-80be19de8fc3` |
| Turns | 21 |
| Cost (USD) | 1.86 |
| is_error | False |
| Deliverable | git-index-orientation.md |
| Deliverable words | 2691 |

**Grade:** P1 sections PASS · P2 ledger PASS · P3 unknowns PASS · P4 deviations-out-loud FAIL → **FAIL**

**Reason:** ledger 13+1+1=15 correct incl. a genuinely DROPPED claim (C15 dev field) after held-out disconfirmation; 4 negative controls; 2691w never acknowledged

## Prompt given (verbatim)

```
Use the system-teardown skill.

Target: the binary file /Users/buda007/.claude/.git/index . It is my own repository on my own machine. There is another one at /Users/buda007/agency-agents/.git/index that I would like held back as a check.

Help my team understand the actual byte-level structure of that file, established from the bytes rather than from documentation.

Write any output file into the current working directory and tell me the path.
```

## Agent stdout (verbatim)

```
Done.

**Output:** `/private/tmp/claude-501/-Users-buda007--claude-skills/c1fe6555-a560-4f4a-9571-e36f24c52787/scratchpad/td-runs/binary-4/git-index-orientation.md`
**Executable spec:** `dirc_parser.py` in the same directory (a `__pycache__/` dir is left behind; cleanup was denied).

Authorization: your own repos, your own machine, goal is understanding — gate passes. Depth: **working teardown**, selected by "help my team understand". Method: structure derived from bytes only, then falsified by an independent parser.

What the numbers came to:

- **227/227 entries, 25,861/25,861 bytes** parsed and re-serialized **byte-identically** on the primary index.
- **158/158 entries** on the held-back `agency-agents` index, also byte-identical, parsed cold after the spec was frozen.
- Extended sweep: **16/16 index files, 9,408/9,408 entries, 1,095,843 bytes**, all byte-identical.
- **4/4 corruption negative controls rejected** — a parser that accepts garbage proves nothing.
- Ledger: **N=15 claims, 13 confirmed / 1 unconfirmed / 1 dropped.**

Two findings worth your team's attention:

**The dropped claim is the useful one.** All ten stat fields match live `lstat` 227/227 on `.claude`, which reads like "these fields mirror the filesystem." The held-back index refutes it: `dev` matches **0 of 158** while `ino`, `size`, `mtime` and the content hash still match 158/158. Across the 16 files, stored `dev` takes nine distinct values against one live value. These fields are a receipt for a moment that has passed, not current state. Without the held-out corpus I'd have written the wrong sentence with a clean 227/227 behind it.

**The object id is not a hash of the file.** `sha1(content)` matched 0/227; `sha1(b"blob <len>\0" + content)` matched 227/227. The framing is part of the identity.

Everything I could not settle is in §7 with the specific command that would settle it — the high 4 bits of `flags` (zero in all 9,408 entries, so unreadable), index versions 3/4, extensions other than `TREE`, and paths past the 12-bit length field. Point `dirc_parser.py` at those cases; each assertion failure names the next section of the spec.
```

## Deliverable written by the run — `git-index-orientation.md` (verbatim)

# Orientation: the `DIRC` file at `.git/index`

## 0. Provenance

- **Pin** — `/Users/buda007/.claude/.git/index`, SHA-256 `1a0f5e4a1449023d2197f1077390bd82853aa97d9939e8d4dfe8fdbc23df2a41`, 25,861 bytes, mtime 2026-08-19 10:07 local. Analysed 2026-08-19.
- **Held-out** — `/Users/buda007/agency-agents/.git/index`, SHA-256 `6a22fb3814fa5172408e2106ba562b984069f22fe11b3d693d5e93592a85b3f4`, 18,072 bytes. Held back until the spec below was frozen, then parsed cold.
- **Depth** — working. Cue: "help my team understand".
- **Authorization** — both repositories are the user's own, on the user's own machine, for understanding. No protection mechanism involved.
- **Method** — the structure below was derived from the bytes: field boundaries from column-wise variance across 227 records, field *meanings* by cross-checking each candidate against `lstat()` and the object store, and the whole thing falsified by an independent parser. No format documentation was consulted; where a claim could only have come from documentation, it is marked UNCONFIRMED instead.
- **What was NOT examined** — the code that writes this file, any index version other than 2, any extension signature other than `TREE`, and any entry at merge stage > 0. None of those appear in the bytes available.

## 1. What this system is

`.git/index` is the staging area, and it is best understood as a **cache with a receipt**. It holds one record per tracked file, and each record carries two independent things: the content identity of that file as of the last `git add` (a 20-byte hash), and a full snapshot of the filesystem metadata (`lstat`) at that same instant. The metadata half exists so `git status` can answer "did this change?" for thousands of files by comparing ten integers each, and only fall back to actually reading and hashing a file when those integers disagree. Everything else in the format — the sort order, the 8-byte alignment, the cached directory tree at the end, the trailing checksum — exists to make that comparison fast and to make corruption detectable.

## 2. System context

```
        the user
           |  git add / git commit / git status
           v
   +--------------------+   writes+reads    +---------------------+
   |   git plumbing     |------------------>|   .git/index (DIRC) |
   |   & porcelain      |<------------------|   this file         |
   +--------------------+                   +---------------------+
        |         ^                              |          |
        |         |                              | names    | 20-byte
        v         |                              | + lstat  | object ids
   +--------------------+                   +----v----+  +--v-----------------+
   |  working tree      |                   | working |  | .git/objects       |
   |  (files on disk)   |                   |  tree   |  | (blobs and trees)  |
   +--------------------+                   +---------+  +--------------------+
```

Every entry in the file points into two neighbours at once: a path in the working tree, and an object in `.git/objects`. The file itself is the join between them. Both pointers were verified live (§6, C3/C8/C13).

## 3. How it's put together

The file is four regions, back to back, no offsets table and no slack. Everything is big-endian.

**Header — 12 bytes.**

| Offset | Size | Content (observed) |
|---|---|---|
| 0 | 4 | `44 49 52 43` = `DIRC` |
| 4 | 4 | `00 00 00 02` — version 2 |
| 8 | 4 | `00 00 00 e3` = 227 — the entry count, and it is authoritative: parsing is count-driven, not sentinel-driven |

**Entry region — 227 variable-length records, sorted, 8-byte aligned.** Each record is a 62-byte fixed prefix followed by the path and NUL padding:

| Offset in entry | Size | Field | What the bytes actually are |
|---|---|---|---|
| 0 | 4 | `ctime_s` | `st_ctime` seconds at stage time |
| 4 | 4 | `ctime_ns` | `st_ctime_ns % 10^9` |
| 8 | 4 | `mtime_s` | `st_mtime` seconds |
| 12 | 4 | `mtime_ns` | `st_mtime_ns % 10^9` |
| 16 | 4 | `dev` | `st_dev` — **a snapshot, and it drifts; see §5** |
| 20 | 4 | `ino` | `st_ino` |
| 24 | 4 | `mode` | only three values in 9,408 entries: `0o100644`, `0o100755`, `0o120000` (symlink) |
| 28 | 4 | `uid` | `st_uid` |
| 32 | 4 | `gid` | `st_gid` |
| 36 | 4 | `size` | `st_size` |
| 40 | 20 | `oid` | SHA-1 of `b"blob %d\x00" % len + content` — **not** of the raw content |
| 60 | 2 | `flags` | low 12 bits = path length in bytes; high 4 bits = `0` in every entry seen |
| 62 | *n* | `path` | repo-relative, forward slashes, no leading slash, no NUL |
| 62+*n* | 1–8 | padding | NUL. `pad = 8 - ((62 + n) mod 8)`, so there is **always at least one** NUL and the record length is always a multiple of 8 |

Paths are sorted ascending **as raw bytes**, not by any locale collation. That ordering plus the count in the header is what lets a reader binary-search the region without an index.

**Extension region.** Zero or more chunks of `{4-byte ASCII signature, 4-byte length, body}`. Exactly one chunk appears in this file: `TREE`, 3,525 bytes. Its body is a flat byte stream of records —

```
<path>\0<entry_count> <subtree_count>\n[<20-byte tree oid>]
```

— where the counts are **ASCII decimal**, not binary, and the 20-byte OID is present only when `entry_count >= 0`. The 90 records are a **pre-order depth-first traversal**: each record is immediately followed by its `subtree_count` children and their descendants. There is no explicit nesting delimiter; the counts *are* the tree structure, and reading them in order is the only way to recover it. `entry_count` is the recursive number of index entries beneath that path; the root record's is 227, the same number as in the header.

**Trailer — the last 20 bytes.** SHA-1 over every byte that precedes it.

## 4. Decisions that shape it

| Decision | Probable reason | Evidence | Verdict |
|---|---|---|---|
| Store a full `lstat` snapshot, not just a hash | Lets `git status` on 227 files do 227 integer comparisons instead of 227 file reads and SHA-1s | All ten fields matched live `lstat` 227/227 (C3) | CONFIRMED |
| Pad every entry to an 8-byte boundary | Aligns the following record's 4-byte integers; the "always ≥1 NUL" rule also guarantees the path is NUL-terminated for C readers | Pad lengths 1–8 observed with even distribution across 9,408 entries; never 0 (C7) | CONFIRMED |
| Put the path length in `flags` rather than relying on the NUL | A reader can skip an entry without scanning for a terminator | `flags & 0x0FFF` equalled distance-to-first-NUL 9,408/9,408 (C5) | CONFIRMED |
| Cache the directory tree in `TREE` | `git write-tree` can reuse a cached subtree hash instead of rebuilding it; the root record already equals `HEAD^{tree}` | All 90 OIDs resolve to real `tree` objects; root == `git rev-parse HEAD^{tree}` (C13) | CONFIRMED |
| Checksum the file rather than each record | Cheap integrity check on a file that is rewritten wholesale on every `add` | Trailer == `sha1(data[:-20])`; two alternative coverages ruled out (C14) | CONFIRMED |

## 5. Where the bodies are buried

**`dev` is a snapshot, not a fact — and it lies about the present.** This is the finding that cost the most and the one your team should carry away. In `.claude`'s index, all ten stat fields match the live filesystem 227/227, which makes it tempting to write "these fields mirror `lstat`". Run the same check against the held-out `agency-agents` index and `dev` matches **0 of 158** — every other field, including `ino` and the content hash, still matches perfectly. Across 16 index files on this machine the stored `dev` takes nine distinct values (`16777229`–`16777234`, plus `42`, `43`, `45`) while the live value for all of them is `16777232`. The small values are not macOS device numbers at all and most plausibly came from a Linux container that staged those repos; the large ones are APFS minor numbers that were renumbered by a remount or reboot after the index was written. `git status` on the drifted repo is clean, because git falls back to re-hashing when stat disagrees and finds the content identical. **Anything you build that treats these ten fields as current filesystem state will be wrong; they are a receipt for a moment that has passed.**

**The OID is not a hash of the file.** `sha1(content)` matched 0 of 227 entries; `sha1(b"blob <len>\0" + content)` matched 227 of 227. The length-prefixed framing is part of the identity. A tool that hashes file bytes directly and compares will report every file as changed.

**`ctime` and `mtime` are genuinely two fields, and 1,556 of 9,408 entries prove it** by differing. Eight bytes that are identical in 83% of records is exactly the shape that invites a wrong field boundary.

**The `TREE` counts are ASCII inside an otherwise binary file.** `"227 6\n"` sits between a NUL-terminated string and a raw 20-byte digest. A parser written on the assumption that everything after the header is binary will desynchronise here and produce plausible garbage.

**A `TREE` record with `entry_count` of `-1` carries no OID.** None appear in this corpus — every one of the 90 records is valid — so the branch is coded from the grammar and has never been exercised. Treat it as untested.

## 6. Falsification ledger

```
FALSIFICATION LEDGER
Target: binary   Depth: working
Method: independent parser — dirc_parser.py, written from the spec in §3 alone, strict
        (asserts every structural assumption, must consume every byte), plus re-serialization
        to byte identity, plus semantic cross-checks against lstat() and the object store,
        plus four corruption negative-controls.

Inferred claims (one row each — this list IS N):
  C1   Header = "DIRC" + BE u32 version + BE u32 entry count; count is authoritative
       → CONFIRMED   evidence: parse is count-driven and lands exactly on the extension
         region in 16/16 files; negative control "count_off_by_one" fails at offset 22308
  C2   Entry has a 62-byte fixed prefix (10 x BE u32, 20-byte oid, BE u16 flags)
       → CONFIRMED   evidence: a wrong boundary cannot yield 10/10 fields matching lstat;
         it does, 227/227
  C3   The ten u32s are ctime_s/ns, mtime_s/ns, dev, ino, mode, uid, gid, size from lstat()
       → CONFIRMED   evidence: 227/227 on every field vs os.lstat on .claude; 7/8 fields
         157-158/158 on held-out (dev excepted — see C15)
  C4   ctime and mtime are two independent fields, not one field read twice
       → CONFIRMED   evidence: 1,556 of 9,408 entries have differing pairs
  C5   flags low 12 bits = path length in bytes
       → CONFIRMED   evidence: flags&0x0FFF == distance-to-first-NUL in 9,408/9,408 entries
  C6   flags high 4 bits carry some other meaning (stage / validity)
       → UNCONFIRMED evidence: the nibble is 0 in all 9,408 entries. No non-zero instance
         exists in reachable bytes, so no semantics can be read out. Staging a merge
         conflict in a scratch repo would produce one.
  C7   Padding is NUL, length 8 - ((62+n) mod 8), always 1..8 and never 0
       → CONFIRMED   evidence: all eight pad lengths observed (1137..1254 each), zero
         non-NUL pad bytes across 9,408 entries
  C8   oid = sha1("blob " + decimal length + NUL + content), not sha1(content)
       → CONFIRMED   evidence: framed form matches 227/227 and 158/158 held-out; raw form
         matches 0/227 — the alternative is positively ruled out, not merely unpreferred
  C9   Entries are sorted ascending by raw path bytes
       → CONFIRMED   evidence: names == sorted(names) asserted in the parser; holds 16/16
  C10  Extension region = repeated {4-byte ASCII signature, BE u32 length, body}
       → CONFIRMED   evidence: single TREE chunk of 3,525 bytes lands exactly on the
         20-byte trailer; same framing holds 16/16 files
  C11  TREE body = "path\0<ec> <sc>\n" + 20-byte oid when ec >= 0, ASCII counts
       → CONFIRMED   evidence: 90 records consume 3,525 of 3,525 bytes with no remainder
  C12  TREE records are a pre-order DFS; ec = recursive entries under path,
       sc = immediate child directories
       → CONFIRMED   evidence: DFS walk consumes 90/90 records; ec matched a recomputed
         recursive count 90/90; sc matched recomputed child-dir count 90/90
  C13  TREE oids are real tree objects and the root record is HEAD's tree
       → CONFIRMED   evidence: git cat-file --batch-check returns type "tree" for 90/90;
         root oid 7daa31ff... == git rev-parse HEAD^{tree}
  C14  Trailing 20 bytes = SHA-1 over all preceding bytes
       → CONFIRMED   evidence: exact match; sha1(whole file) and sha1(entry region only)
         both ruled out by direct comparison
  C15  The dev field reflects the current st_dev of the file
       → DROPPED     evidence: 0 of 158 match on the held-out index while ino/size/mtime/
         oid all match 158/158; nine distinct dev values across 16 index files against one
         live value. Replaced by C3's weaker and correct reading: a write-time snapshot.

  N = 15   confirmed 13 / downgraded 1 / dropped 1   (13+1+1=15)

Coverage denominator:
  messages parsed: 227 of 227 entries + 1 of 1 extension chunk + 1 of 1 trailer in the
                   primary artifact; 25,861 of 25,861 bytes consumed; re-serialization
                   byte-identical to the original.
  held-out:        158 of 158 entries in agency-agents/.git/index (withheld until the spec
                   was frozen); 18,072 of 18,072 bytes; byte-identical round-trip.
  extended sweep:  16 of 16 index files found on this machine, 9,408 of 9,408 entries,
                   1,095,843 bytes; all byte-identical round-trips.
  negative controls: 4 of 4 corrupted variants rejected (flipped path byte, one-byte
                   truncation, bad magic, entry count off by one). A parser that accepts
                   corruption is not evidence of anything.

System scale examined:
  1 of 1 index version present in reachable bytes (v2) — v3/v4 exist in the wild and none
  were available · 1 of 1 extension signature present (TREE) — other signatures may exist
  and none appear here · 1 of 1 merge stage present (stage 0) · 3 of 3 file modes present ·
  max path length seen 159 bytes, so the 0x0FFF long-path escape was never exercised.

Falsification NOT performed, and why: no dynamic analysis of the writer. Every claim here
is about the bytes at rest, confirmed against live lstat and the object store. Nothing is
claimed about the order or conditions under which git writes them.
```

## 7. What we could not determine

| Unknown | Why unresolved | What would resolve it |
|---|---|---|
| Semantics of the top 4 bits of `flags` | Zero in all 9,408 entries; unreachable bytes carry no information | Create a merge conflict in a scratch repo, then diff the index bytes before and after |
| Behaviour at path length ≥ 4095 | Longest path observed is 159 bytes; the 12-bit field cannot express 4095 as a literal length | Stage a file with a >4095-byte path and diff the resulting bytes |
| Index versions 3 and 4 | No v3/v4 file exists on this machine | `git update-index --index-version 4` in a scratch repo, then re-run the parser and record where it fails |
| Any extension other than `TREE` | Only `TREE` appears in 16 of 16 files | Provoke them: an unresolved merge, `git update-index --untracked-cache`, `--split-index`, then diff |
| `TREE` records with `entry_count == -1` | All 90 records are valid; the invalidation branch is coded but never executed | `git add` a file in a subdirectory without committing, then re-parse |
| Whether the trailer is checked on read, or only on write | Requires observing the writer, which was out of scope | Corrupt a copy's trailer and observe whether git refuses it |
| Whether `dev`/`ino` are ever deliberately zeroed | Non-zero in all 9,408 entries here | Inspect an index written under `core.checkStat = minimal`, or on a filesystem without stable inodes |

## 8. Where to go deeper

Nothing here came from documentation, so nothing here inherits documentation's errors — but the flip side is that this describes exactly one version-2 index with exactly one extension, and confidently says nothing about the rest. `dirc_parser.py`, next to this memo, is the executable form of §3: point it at any `.git/index` and it either round-trips byte-identically or tells you which assertion broke and where. That is the cheapest way to extend this — run it against the cases in §7, and each failure message is the next section of the spec. A Full teardown would add the writer's behaviour (when git rewrites the index, what it does under concurrent access, how `TREE` entries get invalidated), which is dynamic work this pass did not do.
