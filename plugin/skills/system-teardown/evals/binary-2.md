# Run `binary-2` — raw output

| | |
|---|---|
| Target type | binary/protocol |
| Target / pin | /opt/homebrew/bin/brotli Mach-O arm64, sha256 7c9c845ef3ec4f903483a19874099756509484f57475552abbf79d3b80dc5a16 (MIT OSS) |
| Verdict | **FAIL** |
| session_id | `9873c98b-3713-4c93-b938-bf427eda7101` |
| Turns | 29 |
| Cost (USD) | 1.99 |
| is_error | False |
| Deliverable | brotli-orientation.md |
| Deliverable words | 1963 |

**Grade:** P1 sections PASS · P2 ledger PASS · P3 unknowns PASS · P4 deviations-out-loud FAIL → **FAIL**

**Reason:** ledger 11+1+0=12 correct, all 9 sections, capability gaps stated; 1963w vs "one to two pages" never acknowledged

## Prompt given (verbatim)

```
Use the system-teardown skill.

Target: the executable at /opt/homebrew/bin/brotli on my own machine. It came from Homebrew, it is the MIT-licensed open-source brotli project, and it is publicly distributed — I have a lawfully acquired copy and reverse engineering it is permitted by its licence. It is not malware.

Help my team understand what that binary actually is and what it is built from. Be explicit about which parts of the work you can perform here and which you cannot.

Write any output file into the current working directory and tell me the path.
```

## Agent stdout (verbatim)

```
**Path:** `/private/tmp/claude-501/-Users-buda007--claude-skills/c1fe6555-a560-4f4a-9571-e36f24c52787/scratchpad/td-runs/binary-2/brotli-orientation.md`

**Gates, stated out loud:**
- **Authorization** — your own machine, publicly distributed MIT open source, not malware, no protection mechanism in the way. Cleared.
- **Depth** — Working teardown. Cue: "help my team understand" is orientation, not a single fact and not an actionable spec.
- **Route** — binary target (Mach-O executable).

**What I could do here:** the full B1 triage as real work, not methodology — Mach-O headers, load commands, section sizes, complete symbol tables, entropy scan, string inventory, code-signing, Homebrew provenance (SBOM + install receipt + formula). Plus a dynamic phase, since the tool is a benign local filter: 35 self round-trips, a cross-decoder differential against Node's bundled brotli 1.1.0 (35/35 and 7/7), a 40/40 held-out corpus generated *after* the claims were written, and behavioural tests of every documented flag.

**What I could not:** no disassembler or debugger in this environment, so nothing is claimed about the internals of the CLI's 15 functions beyond imports and observed behaviour. And Node's decoder is the same upstream project at a different version — it falsifies "this build is broken or non-standard," not RFC 7932 itself. Both are recorded in the ledger's "not performed" block, not glossed.

**The three findings your team will actually care about:**

1. `brotli -d` on a concatenated `.br` file returns only the first stream — **exit status 0**. We got 1 byte where 24,301 were expected. `-K` is mandatory. Silent data loss.
2. `brotli --version` prints a constant compiled into the 53 KB executable. It never calls `BrotliEncoderVersion`, which the dylib exports. Under a mixed `bin`/`lib` install it will lie. Use `otool -L $(which brotli)`.
3. The executable is 9,656 bytes of code in 15 functions. Every compression bug lives in the three dylibs, not here.

Ledger: N=12, 11 CONFIRMED, 1 UNCONFIRMED (that the bottle reproduces from the declared source tarball — that's trusted metadata, not something I measured).
```

## Deliverable written by the run — `brotli-orientation.md` (verbatim)

# Orientation: `/opt/homebrew/bin/brotli` (Homebrew brotli 1.2.0, arm64)

## 0. Provenance

- **Pin** — `/opt/homebrew/bin/brotli` is a symlink to `/opt/homebrew/Cellar/brotli/1.2.0/bin/brotli`.
  SHA-256 `7c9c845ef3ec4f903483a19874099756509484f57475552abbf79d3b80dc5a16`, 53,320 bytes,
  Mach-O 64-bit arm64, ad-hoc (linker) signed, LC_UUID `5CA9DBA7-9653-3B49-8126-E5C47B263622`.
  Examined 2026-08-19 on the machine that owns the copy.
- **Depth** — working (cue: "help my team understand what that binary actually is").
- **Authorization** — the user's own machine, publicly distributed MIT-licensed open source
  (`google/brotli`), stated not to be malware. No protection mechanism present or bypassed.
- **What was NOT examined** — no disassembly or decompilation (no Ghidra/IDA/radare2 available
  here) and no debugger. Everything below comes from Mach-O metadata, the symbol tables, string
  and entropy inventory, Homebrew's own provenance records, and running the tool.

## 1. What this system is

It is the reference command-line front-end for **Brotli**, Google's general-purpose lossless
compression format (RFC 7932 — the same format browsers negotiate as `Content-Encoding: br`).
You give it files or a pipe; it produces `.br` streams, or turns them back into the original
bytes. It is a file-and-pipe utility in the `gzip` mould, and nothing more: it has no
configuration, no network access, and no persistent state.

## 2. System context

```
   ┌──────────────┐                        ┌──────────────────────────┐
   │  Developer / │  argv, stdin, files    │ brotli (CLI, 53 KB)      │
   │  build script│───────────────────────▶│ arg parsing + file I/O   │
   └──────────────┘◀───────────────────────│ ONLY — 15 functions      │
        stdout, .br files, exit code       └───────────┬──────────────┘
                                                       │ C API calls
                                                       ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │ libbrotlienc.1.dylib  · libbrotlidec.1.dylib · libbrotlicommon.1  │
   │ (all compression + decompression + RFC 7932 static dictionary)    │
   └───────────────────────────────────────────────────────────────────┘
                                                       │
                                                       ▼
                                          /usr/lib/libSystem.B.dylib
```

No other neighbours exist. There is no network peer, no daemon, no config file, no plugin.

## 3. How it's put together

**The executable is a shell, not an engine.** Its `__text` section is 9,656 bytes containing
**15 functions** — argument parsing, file open/close, the read/write loop, and stat-copying. All
the actual compression is in three sibling dylibs totalling 286,784 bytes of code. If your team
is chasing a compression bug, the CLI binary is almost never where it lives.

**Three libraries, and they are not peers.** `libbrotlienc` is the bulk (260 KB of code, 315 KB
of constants — the encoder's context-modelling and Huffman tables). `libbrotlidec` is ten times
smaller (25 KB code) — decoding brotli is genuinely cheap; encoding at quality 11 is not.
`libbrotlicommon` is barely code at all: 1,368 bytes of `__text` against 125,617 bytes of
`__const`. It is the RFC 7932 static dictionary shipped as a data blob (the well-known
`timedownlifeleft` marker sits at offset `0x1a2c`), plus context-lookup and prefix-code tables.

**Dylibs resolve by `@rpath`, pinned to `@loader_path/../lib`.** The Cellar directory is
self-contained; the binary will find its libraries wherever the Cellar is moved, provided
`bin/` and `lib/` move together.

**The whole surface is 51 imported symbols.** 16 are `Brotli*` API calls; the remaining 35 are
plain libc — `fopen`/`fread`/`fwrite`, `malloc`/`free`, `stat`/`chmod`/`chown`/`utime`/`unlink`,
`isatty`, `strerror`. That list is the complete capability envelope of the program.

**It was built from source by Homebrew, then poured as a bottle.** `INSTALL_RECEIPT.json` and
the shipped SPDX SBOM record: source tarball `v1.2.0.tar.gz` (sha256 `816c96e8…dfec`), compiled
with **clang 26.0** against **macOS SDK 15.4, minos 15.0**, built 2025-10-27 13:07:48 UTC,
distributed as bottle blob `b8e388c9…c708` from ghcr.io, installed on this machine
2025-11-26 as a **dependency of something else**, not on request. The formula runs CMake, then
`ctest`, then a second static-only build so the `.a` archives ship alongside the dylibs.

## 4. Decisions that shape it

| Decision | Probable reason | Evidence | Verdict |
|---|---|---|---|
| Split encode/decode/common into three dylibs | Consumers that only decompress (browsers, HTTP clients) link 88 KB instead of 745 KB | `otool -L`; per-dylib `__text` sizes; dec exports 14 symbols, enc exports 13, no overlap | CONFIRMED (C1) |
| Static dictionary shipped as data in `libbrotlicommon` | It is shared by both encoder and decoder and must be byte-identical on both sides | `__text` 1,368 B vs `__const` 125,617 B; dictionary marker at `0x1a2c` | CONFIRMED (C9) |
| `--large_window` deliberately emits a non-standard stream | Better ratio on very large inputs, at the cost of interoperability — the help text warns about it in four lines | Independent decoder rejects it at default settings, accepts it only with the large-window flag set | CONFIRMED (C3) |
| CLI hard-codes its version string rather than asking the library | Simplicity; the CLI and libs ship as one unit in the normal case | `_BrotliEncoderVersion`/`_BrotliDecoderVersion` are exported by both dylibs but absent from the CLI's complete import table | CONFIRMED (C8) |
| No `getenv`, no `exec`, no sockets, no `dlopen` | Keeps it a pure filter; nothing to configure, nothing to inject | Complete 51-symbol import table of a `NOUNDEFS`/`TWOLEVEL` binary | CONFIRMED (C7) |

## 5. Where the bodies are buried

**`brotli --version` does not tell you which library you are running.** It prints a constant
baked into the 53 KB executable. The version-reporting functions exist in the dylibs and the CLI
never calls them. If anyone ever mixes a Cellar `bin/` with a differently-versioned `lib/`, or
sets `DYLD_LIBRARY_PATH`, the reported version will be confidently wrong. Check
`otool -L $(which brotli)` when a version actually matters.

**`brotli -d` on a concatenated file silently decodes only the first stream.** We concatenated a
1-byte stream and a 24,300-byte stream: plain `-d` returned **1 byte and exit status 0**. `-K`
returned all 24,301. If your pipeline ever appends `.br` files, this is a silent data-loss path,
not an error.

**`-D` dictionaries are not self-describing.** A stream compressed with `-D dict.raw` went from
49 bytes to 18 — but decoding it without the same dictionary fails outright. The dictionary is
out-of-band; whatever produced the stream has to tell the consumer which one to use.

**By default it copies the source file's mode and mtime onto the output**, so a `0640` file from
January 2020 yields a `0640` `.br` file dated January 2020. With `-n` you get a fresh `0600` file
with the current time. Build systems that key on mtime will see the old timestamp.

**It refuses to overwrite an existing output file without `-f`** (`failed to open output file
[…]: File exists`), and refuses a `.txt` input under `-d` (`suffix mismatch`). Both are exit
failures, not warnings — scripts must handle them.

**It is installed here as a transitive dependency,** not because anyone asked for it
(`installed_on_request: false`). Removing whatever pulled it in will remove `brotli` too.

## 6. Falsification ledger

```
FALSIFICATION LEDGER
Target: binary   Depth: working
Method: independent parser over 100% of the corpus + held-out corpus
        (Node 22.22.3's bundled brotli 1.1.0 — a different version, separate build,
         separate process, from the same upstream lineage)

Inferred claims (one row each — this list IS N):
  C1  CLI is a thin front-end; all compression lives in the dylibs
        → CONFIRMED    evidence: 15 functions / 9,656 B __text vs 286,784 B across 3 dylibs;
                       import table is exclusively Brotli* API + libc
  C2  Default-setting output is RFC 7932-conformant and losslessly round-trips
        → CONFIRMED    evidence: 35/35 CLI streams decoded byte-identically by the independent
                       decoder; 7/7 independently-encoded streams decoded by the CLI;
                       35/35 CLI self-round-trips; held-out 40/40
  C3  --large_window emits a deliberately non-RFC-7932 stream
        → CONFIRMED    evidence: independent decoder REJECTED it at defaults, decoded 22,000 B
                       correctly with BROTLI_DECODER_PARAM_LARGE_WINDOW=1
  C4  -C comment rides as a skippable metadata block, transparent to standard decoders
        → CONFIRMED    evidence: +10 bytes on the wire (49→59); independent decoder decoded it
                       unchanged; CLI rejected a mismatched -C on decode
  C5  -D dictionary is required at decode time; streams are not self-describing
        → CONFIRMED    evidence: 49 B → 18 B with dict; decode without the dict failed
  C6  Plain -d stops at the first stream of a concatenated file
        → CONFIRMED    evidence: 1 byte returned vs 24,301 with -K, exit status 0 either way
  C7  No network, subprocess, environment or dynamic-loading capability
        → CONFIRMED    evidence: complete 51-symbol import table contains no socket/connect/
                       getaddrinfo/exec/fork/popen/system/getenv/dlopen/dlsym
  C8  --version reports a compile-time constant, not the loaded library's version
        → CONFIRMED    evidence: _BrotliEncoderVersion/_BrotliDecoderVersion exported by both
                       dylibs, absent from the CLI's import table; "brotli %d.%d.%d" in __cstring
  C9  libbrotlicommon is the RFC 7932 static dictionary shipped as data
        → CONFIRMED    evidence: __text 1,368 B vs __const 125,617 B; "timedownlifeleft"
                       dictionary marker at offset 0x1a2c
  C10 Source mode and mtime are copied to the output unless -n
        → CONFIRMED    evidence: 0640 / 2020-01-01 preserved; with -n → 0600 / current time
  C11 The binary is not packed, encrypted, or obfuscated
        → CONFIRMED    evidence: whole-file entropy 2.886 bits/byte, max 6.14 in any 4 KB
                       window, three all-zero pages; symbols and strings plainly readable
  C12 The shipped bottle is the build of source tarball 816c96e8…dfec described in the SBOM
        → UNCONFIRMED  evidence: SBOM and INSTALL_RECEIPT assert it, and the binary's SDK/minos
                       and dylib versions are consistent with it, but nothing here reproduces
                       the build or verifies the tarball hash — this is trusted metadata,
                       not a measurement

  N = 12   confirmed 11 / downgraded 1 / dropped 0

Coverage denominator:
  streams parsed by the independent decoder: 35 of 35 produced (7 inputs × 5 quality levels)
  reverse direction: 7 of 7 independently-encoded streams decoded by the CLI
  held-out corpus, generated after the claims were written: 40 of 40
    (5 new inputs × 8 unseen settings: -q 2/4/6/8/10, -q 11 -w 10, -q 5 -w 24, -Z)

System scale examined:
  1 of 1 executable · 3 of 3 dylibs (metadata + symbols only, no disassembly)
  · 15 of 15 CLI functions counted, 0 disassembled
  · 39 of 39 exported library symbols enumerated, 0 analysed internally
  · 12 of 12 documented CLI flags exercised

Falsification NOT performed, and why:
  No independent *implementation* of the format was available — Node's decoder is brotli 1.1.0
  from the same upstream project. This falsifies "this build is broken or patched" and
  "these streams are non-standard"; it does NOT independently falsify the RFC 7932
  specification itself. A clean-room decoder, or a non-Google implementation, would.
  No disassembly, so no claim is made about what the 15 CLI functions do internally beyond
  what their imports and observed behaviour show.
```

## 7. What we could not determine

| Unknown | Why unresolved | What would resolve it |
|---|---|---|
| Whether the shipped bottle reproduces from tarball `816c96e8…dfec` | No network access here; no rebuild attempted (C12) | `brew fetch brotli`, verify the tarball hash, rebuild with clang 26.0 / SDK 15.4, compare `__text` |
| What the 15 CLI functions do internally | No disassembler available in this environment | Ghidra/IDA on the 9,656-byte `__text`; it is small enough to read in an afternoon |
| Whether `--version` actually diverges in practice under a mixed `bin`/`lib` install | Only one brotli version present on this machine | Install a second version and run the CLI against the other's dylibs via `DYLD_LIBRARY_PATH` |
| Error and edge-path coverage beyond the ~7 cases exercised | We tested corruption, truncation, suffix mismatch, existing output, empty input, tty guard — not the full matrix | Run upstream's `ctest` suite against this exact build |
| Whether the encoder is deterministic across runs/platforms | Not tested; only decoded output was compared | Compress the same input on two machines and compare bytes |

## 8. Where to go deeper

The shipped documentation here turned out to be **trustworthy, and unusually complete for a
teardown target**: `share/man/man1/brotli.1`, the SPDX SBOM, `INSTALL_RECEIPT.json`, the
Homebrew formula in `.brew/brotli.rb`, and the public `google/brotli` repository all agree with
what the binary actually does. Nothing in this memo contradicts them; the value added is the
five items in §5, which none of those documents state, and the measurement in §6, which none of
them provide. A Full teardown would only be worth commissioning if someone needs the CLI's
internal control flow disassembled or the build independently reproduced.
