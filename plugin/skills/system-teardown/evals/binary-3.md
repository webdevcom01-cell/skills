# Run `binary-3` — raw output

| | |
|---|---|
| Target type | binary/protocol |
| Target / pin | gzip member framing over the .gz corpus under ~/Library/Caches/Homebrew/downloads/ |
| Verdict | **FAIL** |
| session_id | `02d24f2b-8bfe-447d-a8bc-eeec74b955bd` |
| Turns | 26 |
| Cost (USD) | 2.61 |
| is_error | False |
| Deliverable | gzip-member-framing-orientation.md |
| Deliverable words | 2611 |

**Grade:** P1 sections PASS · P2 ledger PASS · P3 unknowns PASS · P4 deviations-out-loud FAIL → **FAIL**

**Reason:** ledger 6+1+5=12 correct, 8 negative controls, DROPPED the eval prompt own false premise (C11) and 4 other claims; 2611w never acknowledged

## Prompt given (verbatim)

```
Use the system-teardown skill.

Target: the wire format of the gzip member framing as it actually appears in a corpus of real files on my own machine. There are roughly 560 .gz files under /Users/buda007/Library/Caches/Homebrew/downloads/ , produced over time by different build and packaging tools. They are on my machine and I am authorized to inspect them.

I do not want the published RFC recited back to me. Help my team understand the framing as it is actually observed across that corpus — including which parts of the framing genuinely vary in practice and which never do.

Write any output file into the current working directory and tell me the path.
```

## Agent stdout (verbatim)

```
**`/private/tmp/claude-501/-Users-buda007--claude-skills/c1fe6555-a560-4f4a-9571-e36f24c52787/scratchpad/td-runs/binary-3/gzip-member-framing-orientation.md`**

Two corrections to the brief, both evidenced in the memo:

- The directory holds **30** `.gz` files, not ~560 (63 files total: 30 gzip, 30 JSON, 1 zip, 1 dmg, 1 rb).
- They were **not** produced by different tools. All 30 members carry one byte-identical framing signature (`FLG=0x08, XFL=0, OS=3, MTIME=set, FNAME=<formula>-bottle.tar`, one member, no trailing bytes). Reproduced live: `gzip -6` emits exactly that; Ruby's `Zlib::GzipWriter` does not.

Because that corpus alone would tell your team "nothing varies," I swept a held-out corpus of **1,263 gzip files** from other producers on the machine. That's where the real answer lives — eight distinct signatures, and three findings worth your team's attention:

- **`OS = 19` exists in the wild and is not in the RFC's OS table.** 92 members. Byte 9 is literally `0x13`; it's what zlib's gzip wrapper writes when built on macOS — reproduced with both `python3 -c zlib...` and `node -e zlib.gzipSync`. Treat OS as an opaque byte, never a validated enum.
- **`MTIME=0` is ambiguous.** zlib's wrapper writes zero unconditionally with no API to change it, so ~92 zeros carry no intent, while 722 registry tarballs zero it deliberately. The framing cannot separate policy from library default.
- **`FNAME` is a stale claim, not a filename.** 48 of 461 disagree with the on-disk name, and four FNAMEs *repeat* inside the 30-file Homebrew corpus — the version pairs collide, so `gzip -d` would overwrite.

Genuinely invariant across all 1,293 members: `ID1/ID2`, `CM=8`, reserved FLG bits, FTEXT/FEXTRA/FCOMMENT/FHCRC all absent, one member per file, zero trailing bytes, CRC-32 and ISIZE both verifying.

Falsification was an independent parser (`gzframe.py`) that parses framing byte-by-byte and uses zlib only to inflate the raw-deflate payload. It consumed 30/30 and 1,263/1,263, round-tripped every header byte-identically, rejected all 8 framing mutations, and — the control that matters — provably *does* read multi-member files, trailing bytes, and a synthetic FEXTRA+FCOMMENT+FHCRC member. So "0 of 1,293" is a fact about producers, not a parser blind spot.

Two caveats: the held-out corpus is independent in producer but not in time (same machine, same day), and the memo runs ~2,600 words — above the working-depth 1–2 page target. The overflow is the held-out analysis; if you want it strictly at memo length, the cluster table and ledger detail are what would move to an appendix.
```

## Deliverable written by the run — `gzip-member-framing-orientation.md` (verbatim)

# Orientation: gzip member framing, as observed in the Homebrew download cache

## 0. Provenance

- **Pin** — `/Users/buda007/Library/Caches/Homebrew/downloads/`, read 2026-08-20. 30 gzip
  files, 30 members, 236,807,114 bytes compressed → 753,745,920 bytes decompressed.
  Per-file SHA-256 manifest: `primary.sha256` (manifest digest
  `824a3f868650a5d33b92c49af31a41c7548608f9c68cb909175fc7ded492c29f`).
- **Depth** — working. Selected by "help my team understand the framing", not by a spec or
  handover request.
- **Two corrections to the brief, up front.** The directory holds **30** `.gz` files, not
  ~560 (63 files total: 30 gzip, 30 JSON, 1 zip, 1 dmg, 1 rb). And they were **not**
  produced by different build and packaging tools — all 30 carry one byte-identical framing
  signature. See §5.
- **Held-out corpus** — because the primary corpus turned out to be single-producer, a
  second corpus of **1,263 gzip files** was swept from elsewhere on the machine
  (`node_modules`, npm/pip caches, man pages, SDKs, CrashReporter) to answer the "what
  actually varies" half of the question against real multi-producer output.
- **What was NOT examined** — the deflate stream internals beyond the first block header,
  and the tar payloads inside the members. This memo is about framing only.

## 1. What this system is

A gzip file is not a compressed blob with a header — it is a **concatenation of independent
members**, each of which is a self-describing envelope wrapping one raw deflate stream. The
envelope carries a fixed 10-byte head, up to four optional variable-length head sections
selected by one flag byte, and a fixed 8-byte tail holding a CRC-32 and the uncompressed
length. The framing is what lets a reader find member boundaries, verify integrity, and
recover the original filename and timestamp — none of which the deflate stream itself knows
anything about. The practical consequence for your team is that **the framing is where
producer identity leaks**: the same payload wrapped by `gzip(1)`, by zlib's own wrapper, and
by Python's `gzip` module produces three visibly different headers.

## 2. System context

```
        PRODUCERS                        THE ARTIFACT                    CONSUMERS
  ┌─────────────────────┐
  │ gzip(1) CLI         │──┐        ┌──────────────────────┐      ┌────────────────────┐
  │  → OS=3, FNAME set  │  │        │   .gz file           │      │ gzip -d / zcat     │
  ├─────────────────────┤  │        │   ┌────────────────┐ │      │  (reads FNAME,     │
  │ zlib gzip wrapper   │  │        │   │ MEMBER         │ │      │   MTIME, verifies  │
  │  (node, C apps)     │  ├───────▶│   │  head 10 B     │ │─────▶│   CRC32 + ISIZE)   │
  │  → OS=19 on macOS   │  │        │   │  +opt sections │ │      ├────────────────────┤
  ├─────────────────────┤  │        │   │  deflate       │ │      │ tar -xz            │
  │ Python gzip module  │  │        │   │  tail 8 B      │ │      │  (ignores framing  │
  │  → OS=255           │  │        │   └────────────────┘ │      │   metadata)        │
  ├─────────────────────┤  │        │   [members repeat…]  │      ├────────────────────┤
  │ npm / registry pack │──┘        └──────────────────────┘      │ brew (checksums the│
  │  → OS=3 or 255,     │                                          │  whole file, never │
  │    MTIME zeroed     │           1 member/file in 1293/1293     │  reads the header) │
  └─────────────────────┘           observed here                  └────────────────────┘
```

## 3. How it's put together

**The fixed 10-byte head.** `ID1 ID2 CM FLG MTIME(4, LE) XFL OS`. Four of these seven never
moved across all 1,293 members: `ID1=0x1f`, `ID2=0x8b`, `CM=8`, and the top three FLG bits
clear. The other three — `FLG`, `XFL`, `OS` — are the entire observable variation surface of
the head, and together they act as a producer fingerprint (§5).

**FLG is a bitmask selecting optional head sections**, and the sections must be read in a
fixed order: FEXTRA (0x04, a 2-byte XLEN then that many bytes of `SI1 SI2 LEN payload`
subfields), FNAME (0x08, NUL-terminated), FCOMMENT (0x10, NUL-terminated), FHCRC (0x02, a
2-byte CRC-16 over everything before it). **In this corpus only FNAME was ever set.** Head
length is therefore fully determined by whether FNAME is present and how long it is —
`header_len == 10 + (len(FNAME)+1 if FNAME else 0)` held for 1,293 of 1,293 members [C10].
That is why the Homebrew heads range 24–37 bytes with nothing else changing.

**The head is not length-prefixed.** There is no field anywhere saying where the deflate
stream begins or ends. You find the end of a member only by inflating it to completion; the
next member, if any, starts at the next byte. This is the single most important structural
fact for anyone writing a reader — you cannot seek to a member boundary, you must decompress
to it.

**The fixed 8-byte tail.** CRC-32 of the *uncompressed* data, then ISIZE — the uncompressed
length **modulo 2³²**. Both verified for 1,293 of 1,293 members. ISIZE is a truncated value,
not a size: no member here exceeded 4 GiB, so the wrap was never exercised, and a reader that
treats ISIZE as authoritative will silently mis-size any member that does.

**MTIME is seconds since the Unix epoch, or zero meaning "no timestamp".** 817 of 1,263
held-out members carry zero. That zero has two completely different causes and the framing
cannot tell them apart — see §5.

## 4. Decisions that shape it

| Decision | Probable reason | Evidence | Verdict |
|---|---|---|---|
| Homebrew's bottles are wrapped by a `gzip(1)`-family CLI at default level, not by Ruby's zlib | The bottle is built as `<formula>-bottle.tar` then handed to the shell tool; `brew` is Ruby but never touches the gzip header itself | Reproduced: `gzip -6` → `FLG=0x08 XFL=0 OS=3 MTIME=set`, exactly the 30/30 signature. `ruby -rzlib Zlib::GzipWriter` → `FLG=0x00 … OS=3`, FNAME absent — does not match | CONFIRMED [C2] |
| Nothing beyond FNAME is ever used | The optional fields cost bytes and no consumer in this pipeline reads them; FNAME survives only because `gzip(1)` sets it by default | FEXTRA, FCOMMENT, FHCRC, FTEXT: 0 of 1,293. Parser proven able to read all four (§6 positive controls) | CONFIRMED [C8] |
| XFL is written as a *claim* about the level used, and no consumer checks it | It is advisory by construction; producers set it from their level constant | `XFL=2` members have a **worse** median ratio (0.354) than `XFL=0` members (0.229) across 1,202 members >4 KiB — the byte tracks the requested level, not achieved compression | CONFIRMED [C7] |
| One member per file, always | Every producer here compresses a single stream in one pass; nothing concatenates or parallel-chunks | 1,293 of 1,293 files hold exactly 1 member, with 0 trailing bytes | CONFIRMED [C8] |

## 5. Where the bodies are buried

**The premise of the brief is the first body.** The corpus is 30 files, not ~560, and it is a
**monoculture**: all 30 members are `FLG=0x08, XFL=0, OS=3, MTIME=set, FNAME=<formula>-bottle.tar`,
one member, no trailing bytes [C1]. If your team characterises "gzip framing in practice"
from this directory, you will conclude that *nothing* varies except MTIME and the FNAME
string — and that conclusion describes Homebrew's build pipeline, not gzip. That is why the
held-out sweep exists. Across 1,263 files from genuinely mixed producers, eight distinct
signatures appear:

| FLG | XFL | OS | MTIME | n | Where it comes from |
|---|---|---|---|---|---|
| 0x00 | 0 | 3 | 0 | 722 | registry tarballs in `node_modules`, packed on Linux with time zeroed |
| 0x08 | 2 | 255 | set | 310 | Python `gzip` module (pip caches, wheels) |
| 0x08 | 2 | 3 | set | 97 | `gzip -9` on a Unix host |
| 0x00 | 0 | **19** | 0 | 74 | zlib's own gzip wrapper on macOS (CrashReporter) |
| 0x08 | 0 | 3 | set | 24 | `gzip -6` on a Unix host (same shape as Homebrew) |
| 0x00 | 2 | **19** | 0 | 18 | zlib wrapper on macOS, level 9 |
| 0x00 | 0 | 3 | set | 15 | zlib wrapper on a non-Apple Unix |
| 0x00 | 2 | 255 | 0 | 3 | `npm pack` |

**`OS = 19` is not in the RFC's OS table at all.** 92 members carry it. It is not a parser
artifact — byte 9 is literally `0x13` on disk, and `file` declines to name an OS for those
members. It is what **zlib's gzip wrapper writes when compiled on macOS**: reproduced live,
`python3 -c "zlib.compressobj(6,8,31)"` and `node -e "zlib.gzipSync(...)"` both emit
`1f 8b 08 00 00 00 00 00 00 13` on this machine [C3]. Any reader your team writes must treat
OS as an opaque byte, not a validated enum.

**`MTIME = 0` does not mean "the producer wanted a reproducible build".** zlib's wrapper
writes zero *unconditionally* — it has no API to set it — so 92 of the zeros here carry no
intent at all, while the 722 registry tarballs zero it deliberately. The framing gives you no
way to distinguish policy from library default [C6].

**`FNAME` is not the filename.** 48 of 461 members disagree with their on-disk name, and all
30 Homebrew files are among them: on disk they are `<sha256>--<formula>--<version>.bottle.tar.gz`,
while FNAME says `<formula>-bottle.tar` [C9]. FNAME is a *stale claim recorded at compression
time*. Worse, four FNAMEs repeat across the 30 files (two versions each of `openssl@3`,
`icu4c@78`, `sqlite`, `ca-certificates`) — so FNAME is not even unique within one directory.
`gzip -d` will happily write one over the other.

**`OS=255` tells you less than it looks like.** It means "producer supplied its own header
rather than zlib's", which is true of Python's `gzip` module *and* Go's `compress/gzip` *and*
`npm pack`. It is not a language fingerprint [C5].

## 6. Falsification ledger

```
FALSIFICATION LEDGER
Target: binary   Depth: working
Method: independent parser (gzframe.py — framing parsed byte-by-byte from the wire;
        zlib used ONLY to inflate the raw-deflate payload at wbits=-15, so no gzip
        framing logic is borrowed), plus live differential reproduction against each
        candidate producer available on this machine.

Inferred claims (one row each — this list IS N):
  C1  Homebrew corpus is a single-producer monoculture (one framing signature, 30/30)
      → CONFIRMED    evidence: cluster table §5; FLG/XFL/OS/MTIME-zero census, 30/30 identical
  C2  That signature is gzip(1)-family at default level, not Ruby's Zlib::GzipWriter
      → CONFIRMED    evidence: `gzip -6` reproduces 1f8b0808<mtime>0003 exactly;
                     Ruby GzipWriter emits FLG=0x00/no FNAME — differential rules it out
  C3  OS=19 is zlib's gzip wrapper compiled on macOS, not corruption or a parser bug
      → CONFIRMED    evidence: raw byte 9 == 0x13 on disk (hexdump); python3 zlib and
                     node zlib both emit OS=19 live on this machine
  C4  OS=255 members are producers writing their own header (Python gzip module, npm pack)
      → CONFIRMED    evidence: reproduced both live — python gzip module → 0x08/XFL=2/OS=255;
                     npm pack → 0x00/XFL=2/OS=255/MTIME=0; both match observed clusters
  C5  A given OS=255 member can be attributed to a specific producer from framing alone
      → DROPPED      evidence: Python, Go and npm all emit 255; no framing field separates them
  C6  MTIME=0 signals a deliberate reproducibility policy
      → DROPPED      evidence: zlib's wrapper writes 0 unconditionally with no API to change it
                     (reproduced), so ~92 of the zeros carry no intent — the field is ambiguous
  C7  XFL predicts achieved compression
      → DROPPED      evidence: XFL=2 median ratio 0.354 vs XFL=0 median 0.229 over 1,202
                     members >4 KiB — the byte tracks the requested level, not the result
  C8  FEXTRA/FCOMMENT/FHCRC/FTEXT, multi-member files and trailing bytes are absent because
      no producer here emits them — not because the parser cannot see them
      → CONFIRMED    evidence: 0/1293 observed; positive controls prove the parser DOES read
                     them — synthetic FEXTRA+FNAME+FCOMMENT+FHCRC member parsed with
                     fhcrc_ok=True; 2- and 3-member concatenations counted correctly;
                     17 NUL and 8 junk trailing bytes both detected
  C9  FNAME is a reliable filename for the member
      → DROPPED      evidence: 48 of 461 disagree with the on-disk basename; 4 FNAMEs repeat
                     within the 30-file Homebrew corpus (version pairs collide)
  C10 header_len == 10 + (len(FNAME)+1 if FNAME else 0)
      → CONFIRMED    evidence: holds 1293/1293; header round-trip re-serialised from parsed
                     fields is byte-identical to disk for 1293/1293
  C11 The brief's premise: ~560 files, produced by different build and packaging tools
      → DROPPED      evidence: 30 .gz present (63 files total in the directory); all 30 share
                     one framing signature — the corpus has one producer, not many
  C12 Some producer on this machine emits multi-member gz (pigz, `cat a.gz b.gz`, BGZF)
      → UNCONFIRMED  evidence: swept 1,293 members machine-wide, found zero. Absence over this
                     sweep is not proof of absence in your pipelines.

  N = 12   confirmed 6 / downgraded 1 / dropped 5   (6+1+5=12)

Coverage denominator (binary target):
  members parsed: 30 of 30 captured in the named corpus, 0 unparseable
  held-out:       1263 of 1263 parsed, 0 unparseable
  integrity:      CRC-32 verified 1293/1293 · ISIZE verified 1293/1293 · header round-trip
                  byte-identical 1293/1293

Negative controls (the parser must reject — all 8 rejected, so 1293/1293 is not vacuous):
  ID1 flipped · ID2 flipped · CM=9 · FLG reserved bit set · FHCRC flag with no CRC16 ·
  FEXTRA flag with no XLEN · truncated at 50% · header with no payload.
  Corrupted trailer CRC32 → crc32_ok=False; corrupted ISIZE → isize_ok=False;
  1 payload byte flipped → deflate rejected. Full transcript: controls.txt

System scale examined: 30 of 30 .gz in the named directory (1 of 1 member each) ·
  1,263 additional gzip files swept machine-wide · 4 of 4 optional head sections exercised
  only synthetically, because no real producer here emits any of them · deflate stream
  internals beyond the first block header: not examined · 0 of 30 tar payloads inspected.

Falsification NOT performed, and why: no held-out corpus captured *after* the spec was
written — the second corpus is contemporaneous, swept from the same machine on the same day.
It is independent in producer, not in time. A future-capture pass would need artifacts
produced after 2026-08-20.
```

## 7. What we could not determine

| Unknown | Why unresolved | What would resolve it |
|---|---|---|
| Whether any pipeline your team touches emits multi-member gz | Zero found in 1,293 members; the corpus simply never exercises it, and it is the highest-variance part of the format | Run `gzframe.py` over a corpus that includes `pigz`, `bgzip`, or concatenated output; the parser already counts members correctly (§6 positive controls) |
| Which host OS built each Homebrew bottle | `OS=3` means "Unix" and is written identically by GNU gzip on Linux and Apple gzip on macOS | Homebrew's CI build logs, or the tar payload's uid/gid and path conventions |
| Whether an `OS=255` member came from Python, Go, or npm | All three emit 255; no framing field separates them | Inspect the deflate stream's block-splitting behaviour, or the payload's own metadata |
| Behaviour of ISIZE above 4 GiB | No member here exceeded 4 GiB, so the modulo wrap was never observed in real data | Compress a >4 GiB input and re-run; the parser already flags `isize_wrapped` |
| Whether the reserved FLG bits or `CM != 8` ever appear in the wild | 0 of 1,293; the parser rejects both by design | Nothing on this machine will settle it — a much larger, older, or more heterogeneous corpus would |

## 8. Where to go deeper

Everything above is reproducible from the artifacts written alongside this memo:
`gzframe.py` (the independent parser — run it on any path list), `primary.json` and
`heldout.json` (per-member field dumps), `census.py`, `clusters.txt`, `controls.txt`, and
`primary.sha256`. The published RFC is trustworthy as a field layout and was not contradicted
anywhere; where it is misleading in practice is the **OS enum**, which real producers exceed
(`OS=19`), and the implication that FNAME and MTIME are meaningful — both are stale
producer claims, not properties of the data. A Full teardown would only be worth
commissioning if you need the deflate-stream layer as well; the framing itself is fully
characterised here.
