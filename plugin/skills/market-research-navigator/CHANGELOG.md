# Changelog

## Version History

- v3.3.0 (2026-08): Three additions to Response Guidelines and Quick Mode, prompted by a
  gap-analysis review (unrelated skill audit surfaced that this skill had no way to flag
  disagreeing sources, no privacy/independence guardrail for named individuals and
  self-reported competitor claims, and no escalation path when Quick Mode surfaces a
  legal/regulatory/financial red flag). Added: 🔀 CONFLICTING data-quality indicator plus
  two new "Always" rules (never silently resolve conflicting sources; never cite an
  AI-generated search summary as the source); a "Privacy & Source Independence" subsection;
  an Escalation Trigger under Quick Mode. No existing template, output format, mode, or
  wording was changed — this is additive only.
- v3.2.0 (2026-07): Structural refactor. Long sections moved verbatim into `references/`
  and the regional guide moved from the skill root to `references/serbia-balkans.md`, so
  the SKILL.md body fits under 500 lines / 5,000 tokens and no longer loses sections to
  auto-compaction. Frontmatter gained `license` and `metadata.version`; LICENSE.txt added.
  One behavioural addition: the 🌍+🇷🇸 Combined scope now instructs reading
  `references/serbia-balkans.md`, which previously only the 🇷🇸 Regional scope did.
  No template, output format or wording was otherwise changed.

- v3.1.0 (2025-01): Added Serbian language triggers, language detection, diaspora market, startup/funding ecosystem, regulatory overview, improved data quality warnings
- v3.0.0 (2025-01): Added Geographic Scope (Global / Serbia-Balkans / Combined), regional data sources, PPP adjustments, localized search strategies
- v2.0.0 (2025-01): Global English version with Quick Mode, Confidence Indicators, Post-Analysis Iteration, Export Options
- v1.1.0 (2025-01): Added B2B Research Mode with supply chain, margin analysis
- v1.0.0 (2025-01): Initial release with 4 research modes
