# Target: live web product, no source access

**Most of this file is work the user runs, not work you run.** You have no DevTools, no HAR
export, no proxy, and no way to sign up for accounts. WebFetch gives you HTML, JS bundles, and
public files — not response headers, not XHR traffic, not timing. Your job is to specify
exactly what to capture, then interpret what comes back.

Steps are marked **[MODEL]** — you can do this — or **[USER]** — you specify it and they run
it. Never narrate a capture you did not receive.

The discipline that fails most often in this target is provenance: fingerprints get reported as
facts, and vendor estimates get reported as measurements.

## Scope the teardown to a decision

State up front the decision the teardown will inform — "should we build X", "how should we
price Y", "can we migrate off Z". Every section then terminates in an implication for that
decision. A descriptive teardown with no decision attached is content marketing; a
decision-linked one is a deliverable.

Then pick a scope layer and hold it: features, workflows, design, technical stack, or business
model. Covering all five at depth produces five shallow sections.

## Stack fingerprinting

Detection is signature matching over observable artifacts. Signal families carry different
weight, and **absence of a signature is weak evidence of absence** — record it UNCONFIRMED,
never REFUTED. Vendors publish evasion guides for these tools.

| Signal | Who | What to pull | Yields |
|---|---|---|---|
| HTML + meta | **[MODEL]** | generator tags, plugin comments with version strings | CMS, plugin inventory |
| Global JS vars | **[MODEL]** | `window.__NEXT_DATA__`, `__NUXT__`, `__remixContext`, `Shopify` | framework, rendering strategy |
| Asset paths | **[MODEL]** | `/_next/static/`, `/_nuxt/`, `/wp-content/`, `cdn.shopify.com` | framework, CMS, commerce platform |
| `.well-known/` | **[MODEL]** | `security.txt`, `openid-configuration` | security posture, identity provider |
| JS bundle contents | **[MODEL]** | imported library names, SDK keys' vendor prefixes, feature-flag client | analytics, payments, flags, auth vendor |
| Response header names | **[USER]** | `Server`, `X-Powered-By`, `X-Vercel-*`, `CF-Ray`, `X-Amz-Cf-Id` | server, framework, CDN, hosting |
| Header *order* | **[USER]** | raw ordering, not values — **HTTP/1.1 only** | server family when values are scrubbed |
| Cookies | **[USER]** | `JSESSIONID`, `PHPSESSID`, `_shopify_*`, `__cf_bm`, `ajs_*` | framework, platform, analytics vendor |
| TLS / HTTP2 fingerprint | **[USER]** | JA3/JA4, H2 SETTINGS and frame order | server stack behind a normalizing CDN |
| Error pages | **[USER]** | 400/404/500 bodies | IIS/ASP.NET, nginx, Express defaults |
| DNS | **[USER]** | CNAME chains, MX, TXT verification tokens | CDN, email provider, SaaS vendors in use |
| TLS cert | **[USER]** | issuer, SAN list | infrastructure, sibling domains |
| Favicon hash | **[USER]** | Shodan `http.favicon.hash` | platform family |

Header-order fingerprinting is an HTTP/1.1 technique. HTTP/2 and /3 lowercase and compress
headers, and most targets sit behind a CDN that normalizes them — which is why TLS and H2
fingerprints are the modern equivalents.

Tools: Wappalyzer (commercial since 2023; the open fingerprint set survives in community forks
such as `wappalyzergo`), BuiltWith (largely passive historical crawl — gives *adoption
timelines*, often more informative than current state), WhatWeb, Netcraft.

What a fingerprint tells you beyond the tech: the analytics and experimentation stack reveals
measurement maturity; a feature-flag vendor reveals release discipline; support and CRM tooling
reveals the go-to-market motion; the infra footprint gives an order-of-magnitude read on team
size and cost structure.

## Sourcemap recovery — **[MODEL]**, with a warning

The highest-yield technique when available, and the one most likely to disqualify a rebuild.

1. Check every JS and CSS bundle for a trailing `//# sourceMappingURL=` comment.
2. Blind-probe `<bundle>.js.map`. Check the `X-SourceMap` header if the user can see headers.
3. If found: `unwebpack-sourcemap`, `sourcemapper`, or `reverse-sourcemap` reconstruct the
   original source tree.
4. If absent: `webcrack` unminifies and unbundles webpack output — structure without names.

**Contamination.** A published sourcemap is served voluntarily, so retrieving it is observation.
But the recovered artifact is the target's copyrighted source code, and **whoever reads it is
contaminated for clean-room purposes**. If the user's goal is to build something comparable,
say this before opening the map and let them decide who reads it — see `legal-boundaries.md`.
Reading it is not the mistake; reading it and then writing the implementation is.

## API surface discovery

1. **[MODEL] Spec probing** — `/openapi.json`, `/swagger.json`, `/v3/api-docs`, `/redoc`,
   `/.well-known/openapi`, `sitemap.xml`.
2. **[MODEL] GraphQL** — locate the endpoint (`/graphql`, `/api/graphql`, `/query`), then
   introspection: `{__schema{types{name fields{name}}}}`. If introspection is disabled,
   field-suggestion error differentials leak the schema incrementally.
3. **[USER] Network sweep** — DevTools → Network → XHR/Fetch, exercise every flow, export HAR.
   Ask for the HAR file; cluster it by host, path prefix, and method when it arrives.
4. **[USER] Proxy capture → spec generation** — route through mitmproxy, then
   `mitmproxy2swagger` to derive an OpenAPI document from observed traffic. The highest-leverage
   automation in this target: it converts an ad-hoc capture into a structured, diffable artifact
   you can falsify against. Specify it; they run it.
5. **[USER] WebSockets** — DevTools WS frames. Ask for the message envelope, heartbeat interval,
   subscription model, and whether auth is per-connection or per-message.
6. **[MODEL] Auth flow** — the identity provider's `/.well-known/openid-configuration` is public
   and enumerates the whole flow. Login redirects reveal the IdP host, `code_challenge` implies
   PKCE.
7. **[USER] Limits and shape** — `X-RateLimit-*`, `Retry-After`, pagination style, error taxonomy.

**The API resource graph is the true domain model.** The UI is a projection of it. When the two
disagree, the API is the more reliable read on how the team thinks about their domain.

## Feature and flow mapping — **[USER]**, and read this first

**Before signing up for anything on a target the user does not own:** creating an account binds
them to the target's terms, and essentially every SaaS ToS prohibits competitive analysis and
automated access. This is the step that converts a lawful teardown into a contract claim — see
`legal-boundaries.md`, "Contract". Use only accounts the organization already holds under its
own name. Record in the deliverable which tiers could **not** be observed rather than acquiring
them. Never create an account under a false identity or a throwaway domain.

With that settled:

1. **Account matrix** — what differs across the plan tiers and personas they can legitimately
   access. Feature gating *is* the packaging strategy.
2. **Flow reconstruction** — signup → activation → first value → habit loop → upgrade → cancel.
   Timestamp each step; count clicks, fields, required decisions. Cancel flows and empty states
   are the most information-dense surfaces and the least commonly copied.
3. **Information architecture** — nav, URL taxonomy, sitemap, in-app search facets, API resource
   names. Partly **[MODEL]** from public pages.
4. **Onboarding funnel** — awareness → activation → engagement → retention → monetization,
   marking friction added versus value delivered per step.
5. **Pricing teardown — [MODEL]** — value metric, tier boundaries, gating type, annual discount,
   seat vs usage vs hybrid, enterprise threshold, trial vs freemium. Diff the pricing page
   against archive.org snapshots: **direction of travel beats current state**.
6. **Design and performance** — design tokens from CSS custom properties; Lighthouse and Core
   Web Vitals as a proxy for engineering investment.

## Traffic and business-model inference — **[MODEL]**

Legitimately inferable from public data: ranked keywords and content clusters, backlink profile,
paid ad presence, job postings (roles reveal team shape, listed tech confirms the stack,
locations reveal cost base), customer logos, case studies, integration directory, changelog and
status-page cadence, review volume and velocity, public GitHub activity, funding filings.

**The caveat belongs in the deliverable, not just in your head.** Third-party traffic estimates
from Similarweb, Semrush, and Ahrefs diverge substantially from each other and from ground
truth, and degrade sharply for low-traffic domains and non-US geographies. Use them for **rank
ordering and trend direction only**. Never build absolute revenue math on them. Report the
cross-vendor spread, not a point estimate.

## The falsification step: attack the evidence table

Every conclusion goes in a table with four columns. **The fourth column is the falsification** —
and it is a column precisely because instructions that are only prose do not get followed.

| Conclusion | Evidence | Provenance | Alternative explanation ruled out | Verdict |
|---|---|---|---|---|
| Frontend is Next.js 14 | `window.__NEXT_DATA__`; `/_next/static/` paths | `[OBSERVED]` | a static export mimicking the path convention — ruled out, `__NEXT_DATA__` carries a runtime build ID | CONFIRMED |
| Auth via Auth0 | login redirects to `*.auth0.com`; IdP metadata endpoint returns Auth0 fields | `[OBSERVED]` | a self-hosted OIDC server on a vanity domain — ruled out, cert SAN is Auth0's | CONFIRMED |
| ~40k monthly visits | Similarweb 38k, Semrush 52k, Ahrefs 29k | `[TOOL]` | 1.8× vendor spread; no ground truth available | UNCONFIRMED |
| Roughly 15 engineers | 6 open eng roles; 22 eng profiles; commit cadence | `[INFERRED]` | heavy contractor use, or profiles stale after layoffs — **not ruled out** | UNCONFIRMED |

Rules for the fourth column:

- Every `[INFERRED]` row must name at least one alternative explanation that produces the same
  evidence, and say whether it was ruled out and how.
- A row whose alternative was not ruled out is UNCONFIRMED. It may stay in the table — it may
  not be written as a fact anywhere else in the document.
- Count the rows. `INFERRED rows given a named alternative: x of y` goes in the ledger.

An unattacked evidence table is labelling, not falsification.

## Hard boundary

Discovery means observing traffic that the user's **own authorized session** generates.

Enumerating other users' object IDs, fuzzing for hidden admin endpoints, replaying another
account's token, automated credential or parameter fuzzing, or probing for vulnerabilities is
**penetration testing** — written authorization required, out of scope here without it. Fake or
pretextual accounts have supported a fraud theory in court.

State the exclusion in the deliverable's methodology section. Read `legal-boundaries.md` before
any automated collection or any account creation.
