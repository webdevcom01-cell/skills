---
name: adversarial-verify
description: "Adversarially verify a claim, a document, a skill, a report, or a code diff by extracting its discrete claims and having independent agents try to REFUTE each one — only claims that survive with positive evidence are CONFIRMED. Use when the user says verify this, fact-check, adversarially review, red-team this, poke holes in, prove this wrong, is this actually true, check every claim, or Serbian: provjeri ovo, obori ako mozes, fakticka provjera, adversarijalna revizija, da li je ovo tacno, provjeri svaku tvrdnju, nadji rupe. Runs as a dynamic workflow when a workflow engine is available, and falls back to spawning verifier subagents when it is not. Do NOT use to verify a single external fact end to end (use skill-research), to reconstruct how an undocumented system is built (use system-teardown), or to write or improve a prompt or skill rather than check one (use prompt-engineer-pro or skill-creator-pro)."
---

# Adversarial Verify

Take an artifact — a set of claims, a document, a skill, a report, a code diff — pull out the
things it asserts, and try to knock each one down. What survives an honest attempt at
refutation, with positive evidence behind it, is CONFIRMED. Everything else is REFUTED,
UNVERIFIED, or flagged as opinion. The point is to replace a confident read with a checkable one.

## Core rule: refutation is the default, evidence is required

A claim is not confirmed because nobody argued against it. It is confirmed only when an agent
that *tried* to refute it failed and found positive support instead. This inverts the usual bias.

**The verdict is a function of the votes, computed deterministically — not decided by a model.**
The refuters gather evidence; the rule below is applied in code by the bundled workflow script
(or, in the fallback, by you mechanically). This is what stops a plausible falsehood from being
talked into CONFIRMED.

- **CONFIRMED** — a majority of independent refuters found positive supporting evidence **with a
  concrete evidence pointer**, and none refuted it. "Could not refute" alone is **not** CONFIRMED —
  that is UNVERIFIED.
- **REFUTED** — a majority found positive disconfirming evidence. A failed search is not evidence.
- **UNVERIFIED** — could not be settled either way; say what would settle it.
- **Opinion / unfalsifiable** — a value judgement, prediction, preference, or a superlative with no
  objective agreed metric ("fastest", "best") is **not a verifiable fact**. It is flagged and
  never "confirmed." Do not launder an opinion into a fact.

**Enforced, not merely requested:** any CONFIRMED or REFUTED whose evidence is blank or "none" is
downgraded to UNVERIFIED automatically by the adjudication code. A ledger with verdicts but no
evidence is theatre.

Each verdict also carries a **confidence** read off the vote: `low` for a single refuter (quick
depth — one un-cross-checked agent), `medium` for a majority, `high` for unanimous. A quick-depth
verdict is a triage signal, not an authoritative one.

## How to run it

### Preferred — as a dynamic workflow

If the Workflow tool is available in this session, use it — it does extract → refute → adjudicate
with real parallelism, and the verdict math runs in plain code, not in a model's head.

Call `Workflow` with the **exact script below**, verbatim, as the `script` parameter, and
`args = { artifact: "<the text / claims / path to verify>", depth: "quick" | "standard" | "deep", focus: "<optional narrowing>" }`.
`artifact` is required. `depth` defaults to `"standard"` if omitted.

Depth controls how many independent refuters challenge each claim:

| Depth | Refuters/claim | Verdict confidence | Use for |
|---|---|---|---|
| quick | 1 | low (single refuter) | a fast triage pass, a short artifact — not authoritative |
| standard | 3 (majority) | medium/high | the default — a document, a skill, a report |
| deep | 5 + source audit on survivors | medium/high | high-stakes, or claims that lean on cited sources |

At **deep**, every CONFIRMED claim whose evidence contains a URL gets one more independent agent
that checks the cited source is real, reachable, and actually says what the claim needs — a
survivor whose source does not hold is downgraded to UNVERIFIED.

Scale to the artifact. A 3-claim note does not need deep; a legal memo or a shipping report does.
The script logs a warning when a run would spawn a large number of agents (roughly
claims × refuters) — read it before launching a run against a long document. Cost note, measured
directly: a 2-claim smoke test at standard depth (6 refuter calls total) ran ~370K tokens end to
end — cost scales with how much web searching each refuter does, not just claim count, so treat
`focus` and `depth: "quick"` as real cost levers, not just correctness knobs.

```javascript
export const meta = {
  name: 'adversarial-verify',
  description: 'Extract claims from an artifact and adversarially refute each one; only claims that survive independent refutation attempts with positive evidence are CONFIRMED',
  phases: [
    { title: 'Extract' },
    { title: 'Refute' },
    { title: 'Adjudicate' },
    { title: 'Audit' },
  ],
}

const DEPTH_REFUTERS = { quick: 1, standard: 3, deep: 5 }
const LENSES = ['factual accuracy', 'internal consistency', 'source integrity', 'overstatement', 'hidden assumption']

const depth = (args && args.depth) || 'standard'
const artifact = args && args.artifact
const focus = args && args.focus

if (!artifact) {
  throw new Error('adversarial-verify: args.artifact is required — the text, claims, or path to verify')
}

const refutersPerClaim = DEPTH_REFUTERS[depth] || DEPTH_REFUTERS.standard

phase('Extract')

const EXTRACT_SCHEMA = {
  type: 'object',
  properties: {
    claims: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          text: { type: 'string' },
          type: { type: 'string', enum: ['factual', 'opinion'] },
        },
        required: ['id', 'text', 'type'],
      },
    },
  },
  required: ['claims'],
}

const extractPrompt = `Read the artifact below and list every discrete, checkable claim it makes as its own short, self-contained statement (no pronouns that need the surrounding context). Split compound sentences into separate claims.

Tag each claim:
- "factual" — checkable against evidence (a fact, a number, a quote, a causal or historical statement).
- "opinion" — a value judgement, prediction, preference, or a superlative with no objective agreed metric ("fastest", "best", "should"). These are never adjudicated as true/false.

Give each claim a short id: C1, C2, C3, ...
${focus ? `\nFocus especially on claims related to: ${focus}\n` : ''}
ARTIFACT:
"""
${artifact}
"""`

const extracted = await agent(extractPrompt, { schema: EXTRACT_SCHEMA, label: 'extract' })
const allClaims = (extracted && extracted.claims) || []
const factualClaims = allClaims.filter(c => c && c.type === 'factual')
const opinionClaims = allClaims.filter(c => c && c.type === 'opinion')

log(`Extracted ${allClaims.length} claims: ${factualClaims.length} factual, ${opinionClaims.length} opinion. Depth: ${depth} (${refutersPerClaim} refuter(s)/claim).`)

if (factualClaims.length === 0) {
  return {
    depth,
    claims_total: allClaims.length,
    confirmed: [],
    refuted: [],
    unverified: [],
    opinion: opinionClaims,
    note: 'No factual claims extracted — nothing to adjudicate.',
  }
}

if (factualClaims.length * refutersPerClaim > 60) {
  log(`Warning: this run spawns ${factualClaims.length * refutersPerClaim} refuter agents. Large run — consider "quick" depth or narrowing with "focus".`)
}

const REFUTE_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['refuted', 'support', 'falsifiable'] },
    evidence: { type: 'string' },
    pointer: { type: 'string' },
  },
  required: ['verdict', 'evidence'],
}

function refutePrompt(claim, lens) {
  const webNote = lens === 'internal consistency'
    ? 'Reason over the artifact text only for this lens — no outside lookup.'
    : 'Use web search if it helps check this claim against outside reality.'
  return `You are an adversarial fact-checker. Try to DISPROVE the claim below — do not try to confirm it, default to skepticism. A failed search or "I couldn't find a problem" is NOT support — support requires positive evidence.

CLAIM: "${claim.text}"

Check it through the lens of: ${lens}. ${webNote}

Return exactly one verdict:
- "refuted" — you found positive disconfirming evidence. State it in "evidence", with a source/quote/pointer in "pointer".
- "support" — you looked for a problem, found none, AND found positive supporting evidence (not just absence of objection). State it in "evidence" and "pointer".
- "falsifiable" — you could not settle it either way with what you have. Put in "evidence" exactly what would settle it.

Be concrete and specific — no vague "seems plausible."

Full artifact, for context only:
"""
${artifact}
"""`
}

function adjudicate(claim, votes) {
  const valid = v => v && v.evidence && v.evidence.trim().length > 0 && v.evidence.trim().toLowerCase() !== 'none'
  const refuted = votes.filter(v => v && v.verdict === 'refuted' && valid(v))
  const supported = votes.filter(v => v && v.verdict === 'support' && valid(v))
  const n = votes.length
  let status, evidence
  if (n === 0) {
    status = 'UNVERIFIED'
    evidence = 'No refuter votes were returned for this claim.'
  } else if (refuted.length > n / 2) {
    status = 'REFUTED'
    evidence = refuted.map(v => `[${v.lens}] ${v.evidence}${v.pointer ? ' (' + v.pointer + ')' : ''}`).join(' | ')
  } else if (supported.length > n / 2 && refuted.length === 0) {
    status = 'CONFIRMED'
    evidence = supported.map(v => `[${v.lens}] ${v.evidence}${v.pointer ? ' (' + v.pointer + ')' : ''}`).join(' | ')
  } else {
    status = 'UNVERIFIED'
    evidence = votes.map(v => `[${v.lens}] ${v.verdict}: ${v.evidence || '(none)'}`).join(' | ')
  }
  let confidence
  if (n <= 1) confidence = 'low'
  else if (status === 'CONFIRMED' && supported.length === n) confidence = 'high'
  else if (status === 'REFUTED' && refuted.length === n) confidence = 'high'
  else confidence = 'medium'
  return { id: claim.id, text: claim.text, status, confidence, evidence, votes }
}

phase('Refute')

let ledger = await pipeline(
  factualClaims,
  claim => parallel(
    Array.from({ length: refutersPerClaim }, (_, i) => LENSES[i % LENSES.length]).map(lens => () =>
      agent(refutePrompt(claim, lens), { schema: REFUTE_SCHEMA, phase: 'Refute', label: `refute:${claim.id}` })
        .then(v => ({ lens, verdict: v && v.verdict, evidence: v && v.evidence, pointer: v && v.pointer }))
    )
  ),
  (votes, claim) => adjudicate(claim, (votes || []).filter(Boolean))
)

phase('Adjudicate')
ledger = ledger.filter(Boolean)

const confirmedCount = ledger.filter(c => c.status === 'CONFIRMED').length
const refutedCount = ledger.filter(c => c.status === 'REFUTED').length
const unverifiedCount = ledger.filter(c => c.status === 'UNVERIFIED').length
log(`After refutation: ${confirmedCount} CONFIRMED, ${refutedCount} REFUTED, ${unverifiedCount} UNVERIFIED.`)

if (depth === 'deep') {
  phase('Audit')
  const AUDIT_SCHEMA = {
    type: 'object',
    properties: { holds: { type: 'boolean' }, reason: { type: 'string' } },
    required: ['holds', 'reason'],
  }
  const withSource = ledger.filter(c => c.status === 'CONFIRMED' && /https?:\/\//i.test(c.evidence || ''))
  if (withSource.length > 0) {
    const audited = await parallel(withSource.map(c => () =>
      agent(`Audit a source cited to support a CONFIRMED claim. Claim: "${c.text}". Cited evidence: "${c.evidence}". Is it real, reachable, and does it actually say what the claim needs? Return holds=false if not, with why in "reason".`, { schema: AUDIT_SCHEMA, phase: 'Audit', label: `audit:${c.id}` })
        .then(a => ({ id: c.id, holds: a && a.holds, reason: a && a.reason }))
    ))
    const auditMap = {}
    for (const a of audited.filter(Boolean)) auditMap[a.id] = a
    ledger = ledger.map(c => {
      const a = auditMap[c.id]
      if (a && a.holds === false) {
        return { ...c, status: 'UNVERIFIED', confidence: 'low', evidence: `${c.evidence} [SOURCE AUDIT FAILED: ${a.reason}]` }
      }
      return c
    })
  }
}

const confirmed = ledger.filter(c => c.status === 'CONFIRMED')
const refuted = ledger.filter(c => c.status === 'REFUTED')
const unverified = ledger.filter(c => c.status === 'UNVERIFIED')

log(`Final: ${confirmed.length} CONFIRMED, ${refuted.length} REFUTED, ${unverified.length} UNVERIFIED, ${opinionClaims.length} OPINION.`)

return {
  depth,
  claims_total: allClaims.length,
  factual_total: factualClaims.length,
  confirmed,
  refuted,
  unverified,
  opinion: opinionClaims,
}
```

After the workflow returns, present the ledger to the user in the format under "Output" below —
do not just dump the raw JSON.

### Fallback — no workflow engine

If no workflow engine is present (e.g. plain chat without the Workflow tool), do the same three
phases by hand with subagents. The discipline is identical — the engine only adds parallelism.
**Give each refuter its own subagent / clean context even for a small artifact** — running them in
one shared context destroys the independence the whole method rests on.

1. **Extract.** Read the artifact and list every discrete, checkable claim as its own statement.
   Split compound sentences. Tag each `factual` or `opinion` (superlatives with no objective metric
   are opinions). Opinions are set aside.
2. **Refute.** For each factual claim, run *N* independent checks (N = the depth table above), each
   a **separate** subagent prompted to **disprove** it, each on a distinct lens — factual accuracy,
   internal consistency, source integrity, overstatement, hidden assumption. Each returns
   `refuted` / `support` / `falsifiable` plus the specific evidence and pointer. Internal-consistency
   claims reason over the artifact only, no web.
3. **Adjudicate — by the rule, not by feel.** Apply the verdict rules mechanically from the counts:
   majority-refuted-with-evidence → REFUTED; majority-supported-with-evidence and none refuted →
   CONFIRMED; unfalsifiable → opinion/UNVERIFIED; otherwise UNVERIFIED. Downgrade any evidence-less
   CONFIRMED/REFUTED to UNVERIFIED yourself — you are the adjudication code in this path. At deep,
   audit each survivor's source. Then emit the ledger below.

## Output — the verdict ledger

```
VERDICT LEDGER   depth: <quick|standard|deep>   claims: <N factual, M opinion>

CONFIRMED (survived refutation, with evidence)
  C1  <claim>   confidence: <high|medium|low>   evidence: <source / quote / file:line>
  ...
REFUTED (positive disconfirming evidence)
  C4  <claim>   confidence: <...>   evidence: <the contradiction + source>
UNVERIFIED (could not settle)
  C7  <claim>   what would settle it: <...>
OPINION (not a verifiable fact — not adjudicated)
  C9  <claim>
```

Lead with the count. Carry the confidence on every CONFIRMED/REFUTED. Never move a claim to
CONFIRMED without an evidence pointer, and never list an opinion under any verdict.

## Boundaries

- **One external fact, researched end to end** → `skill-research`. This skill is for *many* claims
  in an artifact, checked adversarially in parallel — not one claim researched deeply.
- **Reconstructing how an undocumented system is built** → `system-teardown`. That recovers a
  design; this checks assertions.
- **Writing or improving** a prompt/skill/doc rather than checking it → `prompt-engineer-pro` /
  `skill-creator-pro`.

## Honest limits

A verification harness can itself be wrong — it can confirm a plausible falsehood or refute a
true-but-surprising claim. The guards are built in: refute-by-default prompting, evidence required
for any verdict, an explicit UNVERIFIED bucket, and independent agents rather than one context. But
on a claim that needs a source the environment cannot reach, the honest output is UNVERIFIED with
the exact check that would settle it — not a guess. Deep external claims still benefit from a human
or `skill-research` on the survivors.

**Status, stated plainly:** this skill's description has not yet been trigger-evaluated against the
rest of the account's skill catalog (no A/B pass-rate run against near-miss queries). An earlier
internal draft of this skill referenced an "8-claim accuracy battery, 8/8 correct" — that run could
not be independently verified from this account's saved records, so treat it as unconfirmed rather
than as a claimed result. The extract → refute → adjudicate workflow script above was smoke-tested
on a 3-claim artifact with known ground truth (one true claim, one false claim, one opinion) before
this skill was installed, and it produced the expected CONFIRMED / REFUTED / OPINION split
(371,930 tokens for that 2-factual-claim run — a real cost data point, not a guess).