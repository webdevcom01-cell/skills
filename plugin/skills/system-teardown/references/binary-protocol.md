# Target: binary artifact or network protocol

**Split the labour honestly, and say which half you are doing.**

**B1 triage is executable here.** `file`, `strings`, `objdump`, `readelf`, `nm`, `sha256sum` and
`python3` are available — enough for a real GO/NO-GO decision plus a string, import and entropy
inventory. Do that work; do not hand back methodology when you could hand back findings.
(`binwalk` and `xxd` are not present; entropy is a ten-line Python script.)

**B2 and B3 are user-run.** No disassembler, no debugger, no VM, no packet capture. Steps are
marked **[MODEL]** or **[USER]** accordingly. Your role there is to direct the method and
interpret what comes back — say that plainly rather than pretending to analyze a binary that was
never opened.

## Gate before starting

1. **Lawfully acquired?** Owned copy, licensed, publicly distributed, or captured from
   traffic the user is a party to.
2. **What is the purpose?** Interoperability, security research, migration, or
   compatibility. These are the purposes that legal exemptions are written around.
3. **What does the EULA say?** Many prohibit reverse engineering by contract; several
   jurisdictions void such clauses for interoperability, several do not.
4. **Is it malware?** If yes, stop. This skill declines malware analysis.
5. **Is a protection mechanism in the way?** DRM, license enforcement, anti-tamper,
   integrity checks. If circumventing it is the goal, stop — read `legal-boundaries.md`
   for why, and what remains available.

Record the SHA-256 of the artifact. Every finding references it.

## Binary workflow

**B1 — Triage. [MODEL]** Decide whether to continue before spending real effort.

`file`, `strings` (both ASCII and UTF-16 — UTF-16 is where Windows artifacts hide),
headers and import/export tables, section entropy (high entropy implies packing or
encryption), runtime and language
detection (Go, Rust, .NET, and Python-frozen binaries each need a different toolchain),
code-signing certificate and version resources.

Output is a GO/NO-GO decision plus a target list of interesting strings, imports, and
exports.

**B2 — Static analysis. [USER runs, you interpret]**
Auto-analyze in Ghidra or IDA. Apply signature libraries (FLIRT, FunctionID) to strip
statically-linked library code — skipping this wastes enormous effort on zlib and libc.
Load symbols or debug info if any exist.

Anchor on strings, imports, and exports: work outward from the few named things toward
the many unnamed ones. Recover structures. Rename functions with a **verdict prefix**
convention so later readers can tell a guess from a certainty. Map the call graph. Flag
obfuscation for the dynamic phase rather than fighting it statically.

**B3 — Dynamic analysis. [USER runs, you interpret]**
Snapshot a disposable VM first. Run with process monitoring, packet capture, and fake
network services so the artifact reaches something and reveals its protocol. Attach a
debugger with breakpoints on interesting APIs. If packed: unpack, dump, fix the import
table, and return to B2 on the unpacked image.

Hook parsing and crypto functions with Frida to observe plaintext before encryption and
after decryption — this is usually far cheaper than defeating the crypto. Use emulation
or symbolic execution for hard constraint-solving.

**Stop condition:** when no further change to the environment evokes new behavior. Stating
this condition is what keeps the dynamic phase from running forever.

**B4 — Reconstruction. [MODEL]** Write the format spec and the independent parser from what came back. Falsify it.

## Tools by role

| Role | Tools |
|---|---|
| Triage | `file`, `strings`, `objdump`, `readelf`, `nm` (all available here); `binwalk`, `xxd`, DIE (not available) |
| Disassembly / decompilation | Ghidra, IDA Pro, Binary Ninja, radare2/rizin, `objdump` |
| .NET / JVM | ILSpy, dnSpy, JADX, Procyon |
| Debugging | gdb, lldb, x64dbg, WinDbg |
| Instrumentation | Frida, Pin, DynamoRIO |
| Emulation / symbolic | Unicorn, angr, Triton, Qiling |
| Traffic capture | Wireshark, tcpdump, mitmproxy, Burp |
| Packet crafting | Scapy |
| Format specification | Kaitai Struct (`.ksy`), 010 Editor templates (`.bt`) |
| Protocol inference | Netzob, and the academic line of Discoverer / PULSAR / PRISMA |

## Protocol reverse engineering

Two families of approach, and they answer different questions:

- **Network-trace based** — infer format and state machine from captured traffic. Works
  without the binary. Cannot see intent.
- **Execution based** — observe how the program parses the buffer. Requires the binary.
  Far more accurate on field semantics, because you watch the code read the field.

Use both when possible; they falsify each other.

**Netzob's model is the cleanest mental frame:** a protocol has a **vocabulary** (message
formats — fields, types, boundaries) and a **grammar** (the state machine — which message
may follow which). Recover them in that order; grammar inference on a wrong vocabulary
produces confident nonsense.

**Procedure. [USER runs the capture, crypto, and probing; you direct each step and interpret
what comes back.]** The one exception is step 4 onward once you have the corpus — alignment,
clustering, entropy analysis, and writing the parser are **[MODEL]** work you can do on the
bytes the user hands over.

1. **Strip crypto first.** TLS or application-layer encryption makes everything downstream
   impossible. Extract the key, hook the crypto calls, or use a proxy with a trusted
   certificate on a device you control. If crypto cannot be removed legitimately, the
   protocol target ends here.
2. **Build a corpus.** Many sessions, deliberately varied — different inputs, different
   sizes, error paths, reconnections. A corpus of one happy path yields a spec that
   describes one happy path.
3. **Reassemble before aligning.** For TCP, reconstruct the byte stream and recover message
   boundaries — length-prefix, delimiter, or fixed size — before treating anything as a message.
   **Packet boundaries are not message boundaries.** Confirm the framing rule holds across the
   whole corpus before going further, and check the capture snaplen: a truncated capture looks
   exactly like a variable-length field. Alignment over unreassembled segments is the single most
   productive source of confident nonsense in this target.
4. **Tokenize and align.** Sequence alignment (Needleman-Wunsch and relatives) across messages
   exposes constant regions and variable regions.
5. **Cluster** messages into types by structural similarity.
6. **Find the structural fields** — length fields, delimiters, checksums, magic bytes,
   sequence numbers, timestamps. See heuristics below.
7. **Per-offset entropy and variance** across the corpus: constant offsets are magic or
   version; low-cardinality offsets are enums or flags; high-entropy offsets are
   identifiers, nonces, or payload.
8. **Active differential probing** — where permitted, send a message with exactly one byte
   changed and observe the response delta. This is the fastest route to field semantics
   and requires authorization against anything you do not own.
9. **Infer the state machine** — prefix tree acceptor plus state merging, or L\*-style
   active automaton learning where you can query freely.

## Field inference heuristics

- **Length field** — an integer at a fixed offset that correlates with remaining message
  size. Test the correlation across the entire corpus, not on three examples.
- **Checksum / CRC** — trailing bytes that change when any earlier byte changes but carry
  no independent information. Confirm by computing candidate algorithms over the covered
  range.
- **Magic / version** — constant across all messages of a type; often at offset 0.
- **Sequence number** — monotonic within a session, resets across sessions.
- **Timestamp** — plausible epoch value that advances with wall-clock time.
- **Enum / flags** — very low cardinality across a large corpus.
- **Padding / alignment** — zero runs at offsets that make the following field align to 2,
  4, or 8.
- **Nested TLV** — a type byte, a length that matches the following span, then a value.
  Recursion here is common and easy to miss.

## The falsification step: independent parser

The only accepted proof that a format specification is correct:

1. Write a parser from the specification alone, without consulting the original code.
2. Run it against **100% of the corpus**, including error and edge cases.
3. Any message it cannot parse is a finding to triage, in this order: a **truncated capture**
   (check snaplen), **unreassembled framing**, a **second protocol version** mixed into the
   corpus, and then — most often — a wrong specification. Record which of the four it was.
   Never discard the message to make the number look better.
4. Then run it against a **held-out corpus** captured after the spec was written. Passing
   the corpus you derived the spec from proves much less than passing one you did not.
5. Where legitimate, round-trip: re-serialize a parsed message and confirm byte identity
   with the original.

State parse coverage as a number in the deliverable. "The parser handles 1,847 of 1,847
captured messages, plus 312 of 312 in a held-out capture" is a claim someone can check.
"We reverse-engineered the protocol" is not.

## Deliverables

1. **Machine-readable format spec [MODEL]** — Kaitai Struct `.ksy` or a 010 Editor template.
   Machine-readable because it is executable, and therefore falsifiable.
2. **Message catalogue** — type, direction, purpose, trigger conditions
3. **Field tables per message [MODEL]** — offset, size, type, semantics, verdict
4. **State machine diagram** with transition triggers and error transitions
5. **Wireshark dissector or Scapy layer [MODEL]**, if ongoing analysis is intended
6. **Annotated database export [USER]** (Ghidra/IDA) with the verdict-prefix convention
   documented
7. **Report** with a verdict per claim, the unknowns, the parse coverage number, and the
   legal basis for the work

## Known hard problems

Know these before claiming a result — each one produces confident wrong answers:

- **Encrypted or compressed payloads** defeat trace-based inference entirely. Nothing
  downstream is valid until this is handled.
- **Variable-length and nested structures** are where alignment-based inference most often
  produces plausible garbage.
- **Semantics versus syntax** — finding a field boundary is tractable; knowing what the
  field *means* usually requires execution-based analysis or documentation.
- **State machine inference from passive traces alone** is incomplete by construction: you
  only ever see the transitions that happened to occur.
- **Corpus bias** — a protocol spec is only as complete as the behaviors your corpus
  provoked. Report what you did not exercise.
