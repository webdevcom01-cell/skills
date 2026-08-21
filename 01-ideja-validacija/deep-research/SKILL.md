---
name: deep-research
description: "Conducts systematic, multi-step web research on a target topic, filters for high-quality primary and authoritative secondary sources, synthesizes key themes, and produces a structured, readable markdown report with citations. Use this skill whenever the user asks for deep research, a research report, market or industry research, competitive intelligence, a literature review, a state-of-the-art overview, fact-finding with citations, or wants multiple sources compared and synthesized on a specific topic — even if they don't say \"research\" explicitly (e.g. \"what's the latest on X\", \"find me credible sources on Y\", \"how do experts view Z\", \"compare what's been reported about W\"). Do NOT use for market-sizing, competitor-landscape, or business-validation research (use market-research-navigator instead), or to verify one external claim end-to-end (use skill-research instead)."
---

# Deep Web Research & Curation

Conducts systematic, multi-step web research, filters for high-quality sources,
synthesizes key themes, and formats the output into a structured, readable report.

---

## 📋 Context & Preferences

* **Thick Context:** Act as an elite Lead Researcher. Avoid generic web summaries,
  secondary blog posts, and "slop" aggregators regardless of source tier.
* **Source Tiers:** Distinguish two tiers and prefer Tier 1 whenever it exists; use
  Tier 2 to corroborate, add context, or fill gaps Tier 1 doesn't cover.
  * **Tier 1 — Primary:** official statistics and government data, company
    filings/press releases/regulatory documents, patents, direct
    transcripts/interviews/quotes, raw datasets.
  * **Tier 2 — Authoritative secondary/analytical:** academic preprints (arXiv),
    reputable news (Reuters, Bloomberg), industry analyst reports (Gartner,
    McKinsey). These are strong corroboration, not primary evidence — label them
    accordingly rather than treating them as equivalent to Tier 1.
* **Visual Style:** Highly readable markdown with generous whitespace, clear
  dividers (`---`), and structured tables.
* **Key Inputs Required:**
    1. `Target Topic`: The core subject to research.
    2. `Scope & Constraints`: Specific time period (e.g., last 12 months) or source
       preferences.

---

## 🛠️ Step-by-Step SOP Workflow

### Step 1: Scope, Then Clarify If Needed

Run one broad exploratory search first — initial results usually clarify scope
faster than asking blind, and reduce how often a clarifying question turns out to be
unnecessary.

* If the topic is still genuinely ambiguous after that first pass (it could mean
  more than one thing, or the timeframe materially changes the answer), ask **one**
  clarifying question before going further.
* Plan searches across distinct angles instead of repeating similar queries: a
  broad landscape query, a query targeting concrete data/statistics, a query
  surfacing counter-arguments or skeptical takes, and a query for the most recent
  developments. Aim for roughly 3-6 distinct queries, and stop once additional
  queries stop surfacing new information rather than continuing on a fixed count.

### Step 2: Information Gathering & Filtering

* Prioritize depth and diversity over raw volume. For a genuinely "deep" report,
  aim for enough sources to cover the topic from multiple independent angles —
  typically 5-10 — and require them to span more than one or two
  publishers/domains rather than clustering on a single outlet.
* Filter out low-value, repetitive AI-generated articles. Look for concrete data,
  numbers, and primary quotes.
* If a source is unreachable (dead link, paywall, scraping block), try an
  alternate query or a cached/snippet version before dropping it. If it stays
  unreachable, say so in the report instead of silently omitting it — a gap the
  reader can see is more trustworthy than one they can't.
* Extract crucial metadata for each source: Title, URL, Publisher, Date, and a
  1-sentence significance summary.
* Check each source's publish date against the requested scope (e.g. "last 12
  months"). Exclude out-of-window sources, or clearly label the ones kept for
  historical background as such.

### Step 3: Synthesis & Theme Extraction

Do not just list what the sources say — analyze what they *mean* together:

* Identify **3 key themes** across all gathered sources.
* Highlight any contradictions, tensions, or consensus across the industry.
* Before a quote or statistic goes into the report, confirm it's actually present
  in the source text itself, not just implied by a search snippet — this is what
  keeps the report's core credibility promise intact.
* When a quote or statement is attributed to a specific named person or entity,
  confirm the name in your report matches the exact name adjacent to that quote in
  the source sentence — not just that the quote's content appears somewhere in the
  source. A correct fact paired with the wrong name is still a citation failure.

### Step 4: Format and Polish

Construct the final output using these visual constraints:

* **Title:** Clear, bold header matching the topic.
* **Summary Table:** A markdown table at the top:
  `| # | Title | Publisher | Key Takeaway | URL |`
* **Detailed Breakdown:** Separate sections using dividers (`---`) with plenty of
  whitespace. Roughly 800-1500 words is a reasonable target for the breakdown,
  scaling up or down with how broad the topic is.
* **Theme Synthesis:** Highlight the 3 key themes using bold text for readability.
* If the environment supports delivering files, save the finished report as a
  markdown file rather than only posting it inline.
* Before finalizing, count the words in the Detailed Breakdown section. If it runs
  significantly past ~1500 words, either trim the least-essential source discussion
  (never cut source citations or the summary table to make room) or say so
  explicitly in the report rather than silently shipping an oversized one.

**Example — summary table row:**

| # | Title | Publisher | Key Takeaway | URL |
|---|-------|-----------|--------------|-----|
| 1 | EU Finalizes AI Act Enforcement Timeline | Reuters | Sets phased compliance deadlines through 2027, with the heaviest penalties tied to high-risk system violations | https://example.com/eu-ai-act-timeline |

**Example — theme synthesis:**

> **Regulatory fragmentation is accelerating, not converging.** While the EU AI Act
> sets a compliance baseline, the US and UK are pursuing sector-specific rules
> instead of a single framework — meaning multinational firms face three separate
> compliance tracks rather than one, a tension none of the three regulators have
> publicly addressed.

---

## 🔄 Self-Improvement Loop

Only run this reflection if this execution hit friction — a workaround, an
unreachable source, unusually noisy results — or if the user corrected or rejected
something. Skip it silently on a clean, uneventful run; it exists to catch real
signal, not to append a report to every response.

If triggered, evaluate:

1. **Did any step fail or require a workaround?** (e.g., dead URLs, scraping
   blocks, or broad/noisy search results)
2. **Did the user correct or reject anything meaningful?** (e.g., requested more
   depth, corrected a theme, preferred a different layout)
3. **Did this run reveal a new optimization or rule that a future run of this
   skill would benefit from?**

### Rule for Proposing Updates:

* Only propose a change if it's a substantial improvement to this SOP — minor
  aesthetic or redundant edits aren't worth the churn.
* Most Claude environments treat the on-disk skill file as a read-only cache, so
  this session usually can't save a change directly back to the user's saved
  skill. Instead of asking to "apply" the update, prepare the complete revised
  `SKILL.md` content and offer to deliver it as a file for the user to save or
  re-upload themselves.
* Ask the user something like: *"[X] didn't go smoothly this run — I've drafted an
  updated version of this skill to fix it. Want me to send it over?"*