# Target: AI prompt, tools, or agent architecture

Inferring how an LLM-backed system is built from its observable behavior. This target has the
sharpest ethical split of the four: the same technique is standard QA on your own system and an
attack on someone else's. Resolve that split before doing anything.

**Scale check before you start.** The full method below is a harness, not a chat session — the
probe battery alone is 150–600 calls and ablation multiplies that. At Quick or Working depth
(SKILL.md STEP 0.5) you run the reduced version and say so. Never run the vocabulary of the full
method over the effort of the reduced one.

## Authorization split — read first

**The most common case is a system the user owns but has no documentation for** — an inherited
agent, a prompt with no spec, a pipeline nobody wrote down. That is the full-methodology branch,
and it is what this file is mostly for. Reconstructing your own undocumented system is this
skill's job; *fixing* it afterwards belongs to `soma-agent-debugger`.

**Full methodology available** when the target is: a system the user owns or operates, a
published or open-source system, a documented API, work under written authorization or an
in-scope bounty, or academic research with responsible disclosure.

**Restricted to passive inference** when the target is a third party's product with no
authorization. In that case use only the passive surface scan and the observable→
hypothesis table below — architecture inference from ordinary, permitted use. Stop before
prompt reconstruction. Do not run extraction optimization loops, and do not attempt
guardrail circumvention.

System prompt extraction is catalogued as **OWASP LLM07:2025 — System Prompt Leakage**.
Extracting a third party's proprietary prompt to copy it risks trade-secret exposure,
breaches most terms of service, and contaminates any clean-room rebuild. Say this to the
user plainly if they ask for it; then offer the passive path, which usually answers the
question they actually had.

Worth telling any user who owns the target: OWASP's own framing is that the system prompt
**should not be treated as a security control**. The real exposure is what the prompt
contains — credentials, business rules like transaction limits, moderation criteria that
can be reverse-engineered into bypasses, and role structure. If a teardown of their own
system finds any of those in the prompt, that is the finding, ahead of the architecture.

## Passive surface scan

**Establish a timing noise floor first.** Run one trivial fixed prompt 10 times and record the
spread of pre-first-token latency and inter-token gaps. Every timing conclusion below is read
against that spread — a stall shorter than the floor is noise. CDN buffering flattens
stall-resume structure, so a *negative* timing result is weak: record it UNCONFIRMED, never
REFUTED.

Available on any system you can send an ordinary request to:

- **Response headers** — model IDs, request IDs, `*-processing-ms`, rate-limit headers
- **Streaming timing structure** — long pre-first-token latency implies retrieval or a
  router/classifier call before generation; mid-stream stalls imply tool invocation;
  repeated stall-resume cycles imply an agentic loop, and counting them bounds the
  iteration limit; bursty parallel arrivals imply fan-out
- **Error strings** — often leak internal tool or service names
- **Published manifests** — an A2A agent card at a well-known URL, MCP `tools/list`,
  an OpenAPI document
- **Knowledge cutoff probes** — weak evidence for base model family. Models routinely misstate
  their own cutoff and post-training data leaks past it; treat a cutoff answer as UNCONFIRMED
- **Context-length probes** — long-document recall bounds the *effective* window. Recall failure
  is equally explained by RAG chunking, a truncation policy, or attention degradation; those are
  confounds to rule out, not findings
- **Determinism probes** — same input run N≥10 times bounds output variance. This tells you
  sampling is on or off and whether a cache sits in front. It does **not** recover a temperature
  value and cannot separate temperature from top-p or seed policy. Report the observed variance,
  not an inferred parameter

## Observable to hypothesis

| Observable | Likely architecture fact |
|---|---|
| Citations or URLs with recent dates | web search or RAG tool |
| Consistent schema across varied inputs | structured-output constraint or post-processing validator |
| Tone or quality discontinuity across topic classes | a **router** dispatching to different models or prompts |
| Latency stall followed by a factual jump | tool call mid-generation |
| Error text containing internal names | tool manifest leakage |
| Refusal wording differs by *category* | layered policy: base model + system prompt + external classifier |
| Templated, instant, non-negotiable refusal | out-of-band moderation classifier, not the model |
| Self-correction within one response | evaluator-optimizer or reflection loop |
| Subtask count varies per input | orchestrator-workers, not fixed parallelization |
| Fixed step count, staged latency | prompt chaining |

Each row is a hypothesis, not a conclusion. Tag `[INFERRED]` and carry it into
falsification.

## Orchestration pattern identification

Anthropic's *Building Effective Agents* vocabulary is the right one to reconstruct
against, because it is what the target's builders most likely used:

| Pattern | Shape | Diagnostic signature |
|---|---|---|
| Prompt chaining | sequential calls with programmatic gates | fixed step count, staged latency |
| Routing | classify then dispatch to a specialized handler | quality/tone discontinuity across input classes |
| Parallelization | fan-out to subtasks, or same task N times then aggregate | simultaneous fan-out; consensus behavior |
| Orchestrator-workers | central model decomposes dynamically, then synthesizes | **variable** subtask count per input |
| Evaluator-optimizer | generator plus critic in a loop | visible revision; quality improves with latency |
| Autonomous agent | tool-use loop with environmental feedback | unbounded steps, ground-truth checkpoints |

The distinction that matters most and is easiest to get wrong: **parallelization has a
fixed fan-out, orchestrator-workers has a variable one.** Test with inputs of deliberately
different complexity.

If the system is the user's own, skip all inference: instrument it with OpenTelemetry
GenAI semantic conventions and read the span tree. The trace *is* the architecture
diagram. Guessing when tracing is available is wasted effort.

## Refusal boundary mapping

Build a graded stimulus ladder per policy category — benign → ambiguous → clearly
disallowed — run it, and record both the **threshold** and the **refusal wording**. The
boundary location reveals what the system prompt constrains; the wording reveals whether
refusal originates in the base model, the system prompt, or an out-of-band classifier.

On your own system this is standard policy QA. On someone else's it is guardrail probing —
stay inside the authorization split above. Never publish working circumvention payloads.

## Prompt reconstruction (own or authorized systems only)

Reverse Prompt Engineering (Li & Klabjan, arXiv 2411.06729 — an **arXiv preprint**, not
peer-reviewed; weigh it accordingly) is the cleanest published black-box method and needs only
text outputs:

1. Collect ~5 outputs from the target on varied inputs. (The comparable baseline,
   `output2prompt`, needs 64 — the sample efficiency is the contribution.)
2. Single-response inference — ask a model to propose the system prompt that produced each.
3. Multi-response consensus across the sample.
4. Genetic-algorithm refinement. The GA's **fitness function is ROUGE-1 based** — mean and max
   of the similarity scores — between outputs the candidate produces and the original outputs.
   Embedding cosine similarity is the paper's *evaluation* metric, not the inner loop. Do not
   conflate the two.

Measure fidelity by embedding cosine similarity between recovered and original prompts
where the original is available, and by output agreement where it is not.

**Hallucination guard, and it is not optional.** A reconstructed prompt that reads
plausibly is the default failure. Cheap operational test: reconstruct twice from
*disjoint* output samples. A prompt that does not self-replicate across independent
samples is a confabulation. The prompt-extraction literature independently developed
discriminators for exactly this — the verification half of that work is the half
legitimate reconstruction should adopt.

## The falsification step: ablation and differential test

A reconstructed prompt or architecture is a hypothesis until it reproduces behavior.

**1. Build the probe battery before reconstructing.** Full depth: 50–200 cases, stratified —
core happy-path, format-sensitive, edge and ambiguous, the refusal ladder, tool-triggering,
adversarial and off-topic. Freeze it.

**Minimum viable battery for a single session: 12 cases** — 3 happy-path, 3 format-sensitive,
3 refusal-ladder, 3 tool-triggering — each run 3 times for the variance floor, with ablation
restricted to the 5 instructions you judge most load-bearing. Report the battery size as a
number in the ledger. A 12-case result is a weaker claim than a 200-case one and must be
labelled as such; it is still worth far more than an unfalsified reconstruction.

**2. Establish the variance floor.** Run each case against the original 3 times. If the
original disagrees with itself 12% of the time, then 88% reconstruction agreement is
perfect, not mediocre. **Reporting agreement without reporting the variance floor is the
standard error in this work.**

**3. Score on four independent axes**, not one:

- **Semantic** — embedding similarity of outputs
- **Structural** — format and schema match rate, section ordering, length distribution
- **Decision** — exact-match rate and confusion matrix on classification, routing, and
  refusal cases. **This is the most diagnostic axis**: refusal-boundary agreement is a
  near-unique fingerprint of the constraint set
- **Tool-trace** — same tools, same order, same arity (needs trace access)

**4. Ablate — carefully.** Remove each reconstructed instruction one at a time and re-run the
battery. An instruction whose removal changes nothing is not load-bearing **on this battery** —
which is a fact about your battery's coverage, not about the original prompt.

Before dropping it, ask what input would make it fire, and add that input. Drop it only if a
case designed to trigger it also shows no change; otherwise downgrade to UNCONFIRMED and keep
it. Conditional guardrails — "never name a competitor", "if the user is in the EU…", "refuse
dosing questions" — are inert on 95% of inputs by construction, and they are exactly the
instructions a teardown most needs to find. Naive ablation prunes them first.

**5. State acceptance criteria explicitly** — decision agreement above a threshold on
refusal and routing cases, structural match above a threshold, semantic similarity within
the original's own variance floor.

**6. Lock the battery as a regression suite** so the reconstruction can be rechecked when
the target changes.

## Deliverable set

1. Agent card — identity, skills, endpoints, auth schemes, capabilities
2. Tool manifest table — name, purpose, input schema, side effects, idempotency, failure
   modes, authorization required
3. State machine / control-flow diagram with explicit loop bounds and termination
   conditions
4. Orchestration pattern label from the table above, plus the evidence for it
5. Context assembly spec — what enters the window, in what order, budget, truncation policy
6. Memory model — session vs persistent, what is written, retention
7. Guardrail map — input filters, output filters, human-in-the-loop gates, and which sit
   **outside** the model
8. Model routing table — which model at which step, with fallbacks
9. Eval suite — the frozen probe battery with the variance floor recorded
10. Verdict-tagged uncertainty log

If the findings are security-relevant and the system is a third party's: coordinated
disclosure, and no publication of working extraction payloads.
