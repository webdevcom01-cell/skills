# Claim forensics

Techniques for tracing a circulating claim back to what it actually came from. Read this when a claim is attributed but unlinked, described as brand new without a date, spreading mainly through social posts, or carrying suspiciously specific details — and only when that claim is load-bearing for the user's decision. SKILL.md has the "when not to" list; respect it.

The governing question is not *"is this true"* but *"what artifact does this trace back to."* Most viral misattributions are not invented from nothing — they are a real thing, described wrongly. Finding the real thing usually settles the claim and gives the reader something more useful than a debunk.

**Sections:** 1 dates · 2 attribution · 3 contradiction between retellings · 4 finding the real artifact · 5 distorted statistics · 6 benchmark numbers · 7 vendor vs community terminology · 8 one word, two meanings

**Scope the effort to the stakes, and stop early.** Most claims resolve in two steps. Work down only as far as you need:

1. Start with **§4** — search the claim's most distinctive detail. If the real artifact turns up, you are done; nearly everything else follows from it.
2. Then **§1**, recover the real date. A "just released" thing that is two years old is usually the whole story.
3. Go further only if the claim is still unresolved *and* the user's decision genuinely depends on it.

Sections 3, 6, and 7 are the expensive ones — cross-account tables, tracing a benchmark to its paper, auditing a vendor's doc corpus for a word. Reach for them when cheaper routes came back empty, not as a checklist to complete. Stopping with a partial answer and saying what you didn't check is a legitimate result, and usually the right one for a casual question. A three-line answer with a primary-source link beats a forensic report nobody asked for.

---

## 1. Recover the real date

A claim's plausibility often rests entirely on it being recent. "Just released" is doing load-bearing work, and it is frequently false.

**Platform IDs often encode their own timestamp.** X/Twitter post IDs are snowflake IDs: `(id >> 22) + 1288834974657` gives a UTC timestamp in milliseconds. The value is embedded in the number itself, so it survives even when the page is unfetchable and cannot be edited after the fact.

Caveats that matter:

- **Compute this with a tool, not in your head.** It is 64-bit arithmetic and an off-by-one-digit error produces a confidently wrong date. In JavaScript you must use `BigInt` — `>>` truncates to 32 bits and Numbers lose precision above 53 bits. If you have no execution tool, say you could not decode the ID rather than estimating.
- **Pre-snowflake IDs fail silently.** Posts from before 2010-11-04 don't encode a timestamp; they decode to within seconds of `2010-11-04T01:42:54Z`. Any result at that instant is a null result, not a finding.
- **Not every X ID is a snowflake.** Posts, Articles, DMs, and lists are; Spaces use alphanumeric IDs, and legacy user IDs are small sequential integers that also decode to the epoch.
- **Corroborate before it carries weight.** Before a decoded timestamp becomes the basis of a REFUTED verdict, confirm it by one independent route — the page itself, an archive snapshot, a date quoted elsewhere.

Discord snowflakes work the same way with epoch `1420070400000` and the same 22-bit shift.

**Other date recovery routes**, with their reliability:

- **arXiv**: the identifier's `v1` is the original submission (`arXiv:YYMM.numbervV`, versions start at v1); a bare identifier resolves to the latest revision. In the API, `<published>` is the v1 date and `<updated>` is the retrieved version's.
- **GitHub**: repository `created_at` and `pushed_at` are server-set and trustworthy. Commit `author.date` and `committer.date` are **client-supplied and trivially forged** (`git commit --date`), so treat them as unverified.
- **YouTube**: oEmbed does **not** return a date — the oEmbed spec has no date field at all, so this applies to every provider, not just YouTube. Use the Data API v3 `videos.list?part=snippet` → `snippet.publishedAt`, noting that for a video that was private and later made public this is when it became public, not when it was uploaded.
- **JSON-LD `datePublished`** (schema.org, "date of first publication") is the right property name, but it is publisher-controlled and CMSs routinely rewrite it on republish. It is an assertion, not evidence.
- **PDF metadata** lives in two places that often disagree: the document information dictionary (`/CreationDate`, `/ModDate`, in `D:YYYYMMDDHHmmSS±HH'mm` form, deprecated in PDF 2.0) and the XMP stream (`xmp:CreateDate`, `xmp:ModifyDate`). A mismatch between them is itself a signal. All of these reflect the authoring machine's clock, often carry wrong or missing timezone offsets, and can be edited in seconds — weak evidence standing alone. Where present, `xmpMM:History` gives a much stronger chain of custody than any single timestamp.

**What to do with the result.** If the artifact predates the claim about it by months or years, the "just released" framing is false and everything built on it is suspect. A conference talk given two years ago and recirculated as new is the most common shape this takes.

## 2. Check the attribution separately from the artifact

"An engineer at [Company] released X" contains two claims that fail independently:

- **Does the artifact exist?** Often yes.
- **Was it made in that capacity?** Often no.

People change employers. A talk someone gave while at company A gets attributed to company B after they move — which quietly converts an individual's past work into an institutional position of their current employer. Check where the person worked *when the artifact was made*, not where they work now.

**Look for the author's own response.** People frequently reply to viral misattributions of their own work, and that reply is the strongest evidence available. Search for the named person's account or blog around the date the claim spread. A creator saying "this is from two years ago, before I worked there" ends the inquiry.

## 3. Read contradiction between retellings carefully

When several accounts describe the same alleged artifact with **mutually incompatible specifics**, that tells you something — but less than it first appears.

Build a small comparison table: who posted, when, and what specific details each gave. Watch for divergence in exactly the details that would be fixed if the thing were real:

- Page counts (a 7-page, 11-page, 12-page and 15-page version of "the same PDF")
- Number of stages or steps in a described pipeline, and their names
- Who the author supposedly is (a named person vs "a senior engineer" vs "two engineers")
- Timestamps in a described video that don't match between posts

A single real document has one page count. But divergence proves only that the posters were not looking at the same artifact when they wrote — and that has **two** explanations you must distinguish. Either they are generating plausible detail (fabrication), or they are each describing a different version, excerpt, screenshot, or format of something real that has been through several retellings (distortion). **Distortion is the more common of the two.** Before concluding fabrication, spend one search on §4 and look for the real artifact the details were mangled from. If you find one, the verdict is MISLEADING, not REFUTED.

Contradiction between retellings, on its own, is grounds to distrust the specifics. It is not by itself grounds to declare the underlying thing didn't happen.

**Check whether the accounts share a template.** Engagement-farming accounts run a repeating format — "[Famous person] just dropped a [N]-page PDF on [current buzzword]" — across many topics. Looking at an account's other recent posts is fast and often decisive.

### Write about accounts carefully

Account-pattern evidence is legitimate for establishing *how a claim spread*. It is not license to characterize a real person's motives in a document the user may forward, post, or attach to an email.

- Say the **claim** is false. Do not say a **person** lied, fabricated, or made it up, unless you have them presenting it as their own original reporting *and* direct evidence they knew otherwise. Nearly everyone in a viral chain is repeating in good faith.
- Do not apply labels like "engagement farm", "bot", "grifter", or "fabricator" to an identifiable account in the report. Describe the observable facts — "this account posted the claim on [date]; several other accounts posted near-identical wording the same day" — and let the reader draw the inference.
- Name organizations, publications, and published artifacts freely. For individuals who are not public figures acting in a public capacity, prefer role over handle ("an aggregator account", "a newsletter") unless the user specifically needs the identity, for instance because they are deciding whether to trust that source.
- Earliest poster is not author. The first post you can find is the earliest *you found*, not the origin.
- Mark inference as inference. "Consistent with an automated reposting pattern" is a finding. "This is an engagement farm" is an accusation.

## 4. Find the real artifact the claim was mangled from

If the described thing does not exist, look for what does. Take the most distinctive details in the claim — a specific example, an unusual pairing of names, a named schema, an oddly precise number — and search for those rather than for the claim's headline.

Distinctive details are fingerprints. A claim describing "entity resolution that unifies two names with zero character overlap" plus a specific pair of names will lead straight to the actual source document, even when the claim's framing (author, format, date, title) is entirely wrong.

When you find it, note precisely how the real artifact differs: format (a notebook is not a PDF), authorship (institutional, not a named individual), date, and structure (four stages, not five). Those deltas are what distinguishes MISLEADING from REFUTED, so record them specifically rather than summarizing.

### Nearby is not the same as upstream

Searching a claim's distinctive details will often surface something real on the same subject. That is not the same as having found what the claim came from, and treating it as such invents an origin story the evidence does not support.

Before you write that a claim is a garbled version of artifact X, ask what actually connects the two. Real links look like: shared distinctive wording or a shared specific example, a citation trail from the claim back toward X, dates that run in the right order, or someone in the chain naming X. A shared topic is not a link. Neither is "X is the only thing on this subject I could find" — that is a statement about your search, not about the claim's history.

When you find something real and relevant but cannot establish that link, say exactly that, and keep the two apart in the write-up:

> Could not confirm the claim as stated. Separately, here is a real thing on the same subject — but nothing found connects the claim to it, so treat this as context, not as the claim's origin.

The verdict in that situation stays **UNCONFIRMED**. MISLEADING requires a demonstrated relationship between the claim and the real thing, not a plausible one. This matters because a reader takes MISLEADING to mean "someone garbled a real thing," and if nobody did, you have handed them a false explanation on top of an unanswered question — which is worse than leaving the question open.

The failure has a recognizable feel: you searched, found nothing matching, found something adjacent, and the story assembled itself. Assembling easily is not evidence.

## 5. Ask whether a statistic is a distortion of a different real statistic

Numbers that circulate without a link are frequently real numbers about something else. The number survives the retelling; the subject does not.

The pattern to check for: same figure, shifted noun. "80% of our engineers use X" against "80% of the code we merge is written by X" — the 80% is real and sourceable, the subject was swapped for a more striking one. Search the exact figure alongside the organization's own materials, not alongside the claim.

Report both halves. "This statistic is unsourced" is weak; "this statistic is a distortion of the following real, sourced statistic, which says something materially different" is strong, and is the part the reader can actually use.

## 6. Trace benchmark numbers to the study, and read its scope

Performance claims — "18% more accurate", "85% cheaper", "40% faster" — usually originate in one real paper and are then generalized far past what it measured.

Find the paper. Then check three things before repeating the number:

- **Sample size and domain.** A result from 19 questions about one diagram in one industry is not a general law about the technique.
- **What the baseline actually was.** "18% better" against a raster image, or "85% cheaper" than dumping a whole raw file, are not the comparisons the claim implies. Any competent method beats a deliberately weak baseline.
- **Whether independent work replicates it.** Vendor papers reporting on their own product are evidence, but weak evidence. Search for benchmark studies and negative results specifically — these are systematically under-shared relative to positive ones, so they will not surface from a neutral query.

Where independent evidence is mixed or negative, say so with the same prominence as the original claim.

## 7. Separate vendor-official from community terminology

A recurring failure in fast-moving technical topics: a term coined by the community gets attributed backwards onto a vendor, and then the vendor is described as "introducing" or "calling it" something they have never said.

Check the vendor's own docs, blog, and changelog for the literal word before writing that they use it. Absence is a reportable finding: "across N of the vendor's own orchestration documents spanning [dates], the words X, Y, and Z do not appear" is a strong, checkable claim — but only bother when the terminology is actually contested and load-bearing for the user's question.

Note that absence of a term is not opposition to the idea. A vendor may ship exactly the described capability under different vocabulary. Report both: they never use the word, *and* here is what they actually ship that corresponds to it. Do not let the terminology finding become an overclaim that the vendor rejects the concept.

## 8. Watch for one word carrying two meanings

When a term goes viral, it often gets stretched across two genuinely different concepts that share a name. Content about the second meaning then gets relabeled with the buzzword from the first, and evidence for one is cited as evidence for the other.

If a term seems to cover suspiciously much ground, split it explicitly. Establish which meaning the term originated in, which meaning each source is actually discussing, and whether any evidence is being transplanted across the boundary. Sources that police the distinction themselves ("this is not the same as...") are useful corroboration that the conflation is real and not your invention.

---

Record every claim you checked in the report's "Claims checked" section — SKILL.md has the format and the verdict definitions.
