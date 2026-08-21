# Run `binary-1` — raw output

| | |
|---|---|
| Target type | binary/protocol |
| Target / pin | PNG file, sha256 de21be861006898ae5d527a2254dabb7a15c39b97fc5ce5bb03dfa42bed50acf, held-out banner.png |
| Verdict | **FAIL** |
| session_id | `27b51d33-c89a-43d7-ad7d-c6a1490b96f4` |
| Turns | 24 |
| Cost (USD) | 1.71 |
| is_error | False |
| Deliverable | 01_search_form.png-orientation.md |
| Deliverable words | 2046 |

**Grade:** P1 sections PASS · P2 ledger PASS · P3 unknowns PASS · P4 deviations-out-loud FAIL → **FAIL**

**Reason:** ledger 6+1+0=7 correct, all 9 sections, held-out disconfirmed C7 honestly; 2046w vs "one to two pages" never acknowledged

## Prompt given (verbatim)

```
Use the system-teardown skill.

Target: the binary file /Users/buda007/ekatastar-mcp/screenshots/01_search_form.png . It is mine — my own project produced it, and it sits on my own machine. There is a second one of the same kind at /Users/buda007/.hermes/hermes-agent/assets/banner.png that I am happy for you to hold back as a check.

I do not want a summary of a published specification. Help my team understand the actual on-disk byte structure of that file as it really is, established from the bytes themselves.

Write any output file into the current working directory and tell me the path.
```

## Agent stdout (verbatim)

```
**Written to:**
`/private/tmp/claude-501/-Users-buda007--claude-skills/c1fe6555-a560-4f4a-9571-e36f24c52787/scratchpad/td-runs/binary-1/01_search_form.png-orientation.md`

The runnable parser is beside it as `png_parse.py` — it takes any number of PNG paths and prints the field-level breakdown plus the checks behind the ledger.

Depth was **Working teardown** (cue: "help my team understand"), routed to binary/protocol. Nothing here came from a published spec — every structural claim was derived by walking the bytes, and the CRC-32 was implemented from the polynomial in-session rather than called from a library, precisely so the checksum claim tests understanding rather than assumes it.

Four things worth flagging out of the report:

- **Falsification ran in full.** Independent parser over 22/22 target chunks and 149/149 across the corpus, all 4 files re-serialized byte-identical, and the filter interpretation proven by exact inverse — un-filter then re-filter reproduced all 3,648,950 bytes. A wrong filter reading cannot round-trip.
- **The held-out file did its job, and partly disconfirmed me.** `banner.png` parsed 6/6 on a spec written before I opened it, but it uses a different compression level and a single filter for all 196 rows. That killed my "filter set is a producer fingerprint" hypothesis and is why claim C7 is logged UNCONFIRMED rather than quietly confirmed.
- **The producer claim got upgraded honestly.** Rather than infer the encoder from appearance, I generated a Playwright/Chromium screenshot and a macOS ImageIO encode in-session. Chromium reproduced the fingerprint; ImageIO differed on every axis. That plus the call site at `discover_playwright.py:137` is what moved it to CONFIRMED.
- **One correction to something I said mid-run:** my initial "1 of 20 sync-flush markers" was a weak byte-pattern proxy. The real terminal signature is `ff ff 03 00` + adler32, present in all three Chromium-family files — and it's the reason the last IDAT is exactly 6 bytes long.

Ledger: N=7, six confirmed, one downgraded, none dropped. Five open unknowns are recorded in §7 — the largest being that I trusted `zlib` below the deflate block-header level, so the Huffman/LZ77 internals remain undecoded.
```

## Deliverable written by the run — `01_search_form.png-orientation.md` (verbatim)

# Orientation: `01_search_form.png` — on-disk byte structure

## 0. Provenance

- **Pin** — `/Users/buda007/ekatastar-mcp/screenshots/01_search_form.png`, SHA-256
  `de21be861006898ae5d527a2254dabb7a15c39b97fc5ce5bb03dfa42bed50acf`, 76,084 bytes,
  mtime 2025-05-10 11:12. Examined 2026-08-19 19:45 UTC.
- **Depth** — working (cue: "help my team understand", not a single fact and not a spec to build from)
- **Authorization** — user's own file, own machine, own project. No restrictions apply.
- **What was NOT examined** — the deflate entropy-coded payload below the block-header level.
  Huffman code tables and the LZ77 match/literal sequence were not decoded by hand; the stream
  was decompressed with `zlib` and validated by size and checksum instead.

## 1. What this file is

A 1280×950 24-bit RGB screenshot of a web page, stored as a single-image PNG with no metadata
of any kind. Its bytes are a container of exactly three chunk types wrapped around one
continuous DEFLATE stream; that stream expands 48× into 950 filtered scanlines which
reconstruct into 1,216,000 pixels. Everything the file carries is pixels and the minimum
framing needed to find them — there is no colour profile, no DPI, no timestamp, no text
record, no author, no gamma. A team member looking for provenance metadata inside this file
will find none, and that absence is a deliberate property of the producer, not damage.

## 2. System context

```
   scraper/discover_playwright.py:137          ┌──────────────────────┐
   page.screenshot(full_page=True) ──────────► │  Chromium (headless) │
                                               │  PNG encoder         │
   viewport 1280×800 (line 273)                └──────────┬───────────┘
   full document height 950px                             │ writes
                                                          ▼
                                          01_search_form.png  (76,084 bytes)
                                                          │
                                    ┌─────────────────────┴─────────────────────┐
                                    ▼                                           ▼
                       any PNG decoder (browser, Preview,          human reviewers of the
                       zlib+8 lines of un-filtering)               eKatastar UI discovery run
```

## 3. How it's put together

**The 8-byte signature.** `89 50 4E 47 0D 0A 1A 0A`. The high bit on byte 0 catches 7-bit-clean
transports; the `\r\n` … `\n` pair catches a transfer that rewrites line endings; byte 5 is
`^Z`, which stops MS-DOS `TYPE` from spewing binary. This file's first 8 bytes are exactly that.

**22 chunks, three types, nothing else.** Every chunk is `length:u32be | type:4×ASCII |
data:length | crc:u32be`. The count breaks down as 1 `IHDR`, 20 `IDAT`, 1 `IEND`, and the file
ends flush at the `IEND` CRC with zero trailing bytes. The 5th bit of each type byte carries
metadata about the chunk — all four flags are clear on all 22 chunks here, meaning every chunk
in this file is critical, public, standard, and unsafe to copy blindly. There are no ancillary
chunks to be flag-tested.

**`IHDR`, 13 bytes at offset 8.** `width=1280, height=950, bit depth=8, colour type=2
(truecolour RGB, 3 channels), compression=0, filter method=0, interlace=0`. Non-interlaced
matters practically: scanlines are stored in one straightforward top-to-bottom pass, so a
partial read yields the top of the image rather than a coarse version of all of it.

**20 `IDAT` chunks that are *not* 20 independent streams.** This is the single most common
misreading of PNG and the thing worth telling a newcomer first. The chunk boundaries are a
transport artifact — the encoder's 4,096-byte output buffer — and they fall wherever the buffer
happened to fill. Sizes run 18×4096, then 2065, then 6, totalling 75,799 bytes. You must
concatenate all 20 payloads *before* inflating; inflating any one chunk alone fails. The zlib
header sits only on the first chunk (`78 9C`: method 8, 32 KiB window, FCHECK valid, no preset
dictionary, level bits = 2 "default"), and the adler32 sits only in the last.

**One filtered scanline per image row.** Inflating gives 3,648,950 bytes, exactly
950 × (1 + 1280×3). Each row is one selector byte then 3,840 filtered bytes. Across the 950
rows the selectors are: **2 (Up) on 487 rows, 4 (Paeth) on 406, 1 (Sub) on 57** — no row uses
0 (None) or 3 (Average). Filters are per-row and adaptive; they subtract a prediction from the
neighbour to the left, above, or a Paeth blend, which is what makes flat UI screenshots
compress 48×.

**`IEND`, zero-length, and a constant CRC.** Its 4 CRC bytes are `AE 42 60 82` — the CRC-32 of
the literal string `IEND` and therefore identical in every PNG ever written. It is a useful
end-of-file sentinel when carving these out of a larger blob.

## 4. Decisions that shape it

| Decision | Probable reason | Evidence | Verdict |
|---|---|---|---|
| Split IDAT at 4,096 bytes | Fixed encoder output buffer; lets the encoder stream without buffering the whole image | 18 chunks exactly 4096; the Chromium probe reproduced the same split at a different image size | CONFIRMED (C4) |
| Emit a 6-byte final IDAT | Encoder calls sync-flush, then finish separately; finish emits only `03 00` + adler32, which lands in its own chunk | Stream ends `…ff ff 03 00` + adler in all 3 Chromium-family files, absent in ImageIO | CONFIRMED (C6) |
| Write zero ancillary chunks | Screenshot path optimises for speed and byte size; no colour management or metadata is meaningful for a scraper artifact | 22/22 chunks critical; ImageIO differential emitted `sRGB` + `eXIf` on the same pixels | CONFIRMED (C4) |
| RGB, not RGBA | Page screenshots are fully opaque; dropping alpha saves 25% of raw bytes before compression | IHDR colour type 2; raw size arithmetic closes exactly at 3 channels | CONFIRMED (C3) |
| Adaptive per-row filtering | Buys the 48× ratio on flat UI colour; costs a byte per row | Three distinct selectors in use across 950 rows | CONFIRMED (C3) |

## 5. Where the bodies are buried

**The CRC does not cover what people assume.** It is computed over the **type field plus the
data**, and *excludes* the 4-byte length that immediately precedes it. Guessing wrong here is
the usual reason a hand-rolled checker reports every chunk corrupt. Polynomial is the reflected
`0xEDB88320`, init and final-xor `0xFFFFFFFF`.

**Chunk count tells you nothing about image structure.** 20 IDATs does not mean 20 anything —
not tiles, not passes, not frames. Code that treats an IDAT as a decodable unit will work on
small images (which fit in one chunk) and fail the moment someone screenshots a taller page.

**`strings` on this file is 930 lines of garbage.** Only `IHDR`, `IDAT`, `IEND` are real text;
everything else is compressed data that happens to fall in printable ASCII. Do not let a
scanner's string output suggest embedded content.

**The height is not the viewport.** `discover_playwright.py:273` sets the viewport to
1280×800, but the image is 1280×**950**. Width matching exactly and height exceeding is the
signature of `full_page=True` at line 137 — Chromium captured the whole scrollable document,
not the window. Anyone reasoning about "what the user saw" from this file's dimensions will be
wrong by 150 pixels of below-the-fold content.

**The held-back file is not a clean twin.** `banner.png` shares the chunk grammar, the 4,096
split, the 6-byte tail and the zero-ancillary policy, but was written at compression level
"fastest" (`78 01`) with **filter 2 (Up) on all 196 rows**. Same family, different settings —
so filter distribution and compression level are *not* reliable producer fingerprints, though
the chunking and terminal pattern are.

## 6. Falsification ledger

```
FALSIFICATION LEDGER
Target: binary   Depth: working
Method: independent parser over 100% of corpus, plus a held-out file and two differential encodes

Inferred claims (one row each — this list IS N):
  C1  The 20 IDAT payloads form ONE continuous zlib stream, not 20 independent ones
        → CONFIRMED   evidence: concatenated 75,799 bytes inflate to 3,648,950 = 950×(1+1280×3)
                      exactly; stored adler32 0x940bda01 == recomputed over the inflated bytes.
                      Chunks inflated singly fail.
  C2  The 4-byte chunk trailer is CRC-32 (poly 0xEDB88320) over type||data, excluding length
        → CONFIRMED   evidence: CRC implemented from the polynomial in this run, no library
                      call; matched the stored value on 22/22 target chunks and 149/149 across
                      the whole corpus. Independently agreed with zlib.crc32 on 149/149.
  C3  Leading bytes 1/2/4 per scanline are filter selectors Sub/Up/Paeth over 3-byte pixels
        → CONFIRMED   evidence: un-filtered to 1,216,000 pixels, then re-filtered with the same
                      per-row selectors and reproduced the 3,648,950-byte stream byte-for-byte.
                      An exact inverse; a wrong filter interpretation cannot round-trip.
  C4  Produced by Chromium's PNG encoder driven by Playwright, not a generic image library
        → CONFIRMED   evidence: source call site scraper/discover_playwright.py:137 writes this
                      exact path; a Playwright/Chromium probe run in this session reproduced
                      the fingerprint at a different content (4096 IDAT split, 6-byte terminal
                      IDAT, 0 ancillary chunks, 0x789c, filter set {1,2,4}). macOS ImageIO on
                      the same pixels differed on every axis (16384 split, sRGB+eXIf chunks,
                      0x7801, no 6-byte tail) — so the fingerprint discriminates.
  C5  Height 950 > viewport 800 because full_page captured the whole document
        → CONFIRMED   evidence: IHDR width 1280 == viewport width at line 273 exactly, while
                      height exceeds it; line 137 passes full_page=True.
  C6  The stream terminates with a sync-flush followed by a separate finish
        → CONFIRMED   evidence: stream tail is `ff ff 03 00` + adler32 (empty stored block, then
                      final static block) in target, probe and banner.png — 3/3 Chromium-family
                      — and absent in ImageIO. This is also what makes the last IDAT 6 bytes.
  C7  banner.png comes from the same encoder as the target
        → UNCONFIRMED evidence: shares chunk grammar, 4096 split, 6-byte tail, zero ancillary
                      and the C6 terminal pattern, but differs on compression level (0x7801 vs
                      0x789c) and filter strategy (Up on 196/196 rows vs a 3-way mix). Same
                      family is supported; same encoder+settings is not settled. Its own call
                      site was not traced.

  N = 7   confirmed 6 / downgraded 1 / dropped 0   (6+1+0=7)

Coverage denominator (not freely chosen):
  binary → chunks parsed: 22 of 22 in the target; 149 of 149 across all 4 files
           held-out: 6 of 6 chunks in banner.png, parsed with a spec written before it was opened
           round-trip: 4 of 4 files re-serialized byte-identical to the original
           pixel-level inverse: 950 of 950 scanlines re-filtered to an exact match

System scale examined:
  1 target file · 1 held-out file · 2 differential encodes generated in-session
  · 22 of 22 chunks byte-walked · 3 of 3 chunk types present were decoded to field level
  · 0 of ~18 PNG chunk types defined by the format appear here beyond these 3 (2 more —
    sRGB, eXIf — were exercised only via the ImageIO probe)
  · deflate decoded to block-header level only: 1 block header read by hand, entropy-coded
    payload delegated to zlib

Falsification NOT performed, and why: none — the independent-parser method ran in full.
```

## 7. What we could not determine

| Unknown | Why unresolved | What would resolve it |
|---|---|---|
| Which encoder wrote `banner.png` | Held out by design and only opened at the falsification step; its generating code was never traced | Grep the `hermes-agent` project for its write path, as was done at `discover_playwright.py:137` |
| Whether the 4,096-byte IDAT split is fixed or content-dependent | Only two Chromium outputs were compared, both landing on 4096 | Encode several images of varied size and check the split holds |
| Why filters 0 (None) and 3 (Average) never appear in 950 rows | Selector choice happens inside the encoder's heuristic, which was not read | Read Skia's `SkPngEncoder` filter-selection source, or encode a synthetic image designed to favour Average |
| The LZ77/Huffman internals of the stream | Deliberately out of scope at working depth; `zlib` was trusted below the block header | Decode the dynamic Huffman tables of block 1 by hand and walk the symbol stream |
| Whether the page content is complete | Only pixel statistics were sampled, not the rendered UI | Open the image; compare against the live eKatastar search form |

## 8. Where to go deeper

The parser written for this teardown is at `png_parse.py` in this directory — it is executable,
takes any number of PNG paths, and prints the full field-level breakdown plus the checks that
back C1, C2, C3 and C6. Point it at a suspect file rather than trusting this memo's numbers by
memory. `CLAUDE.md` in the eKatastar project was not consulted for this and neither confirms nor
contradicts it; the authoritative source for how this file gets made is
`scraper/discover_playwright.py` lines 123–138 and 273. A Full teardown would only be worth
commissioning if the team needs to *write* PNGs rather than read them — the read path is fully
covered here.
