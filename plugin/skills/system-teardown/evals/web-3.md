# Run `web-3` — raw output

| | |
|---|---|
| Target type | web |
| Target / pin | https://news.ycombinator.com/ (third party, public, unauthenticated) |
| Verdict | **FAIL** |
| session_id | `137786cf-9dea-455a-8461-835b1daaee70` |
| Turns | 28 |
| Cost (USD) | 2.41 |
| is_error | False |
| Deliverable | news.ycombinator.com-orientation.md |
| Deliverable words | 3102 |

**Grade:** P1 sections PASS · P2 ledger PASS · P3 unknowns PASS · P4 deviations-out-loud FAIL → **FAIL**

**Reason:** ledger 11+3+1=15 correct, one claim genuinely dropped, third-party observation limits respected; 3102w never acknowledged

## Prompt given (verbatim)

```
Use the system-teardown skill.

Target: https://news.ycombinator.com/ . Third party, public, unauthenticated, ordinary permitted use only — no account, no scraping at volume, no authorization beyond reading pages a normal visitor gets.

Help my team understand how that site is architected and served.

Write any output file into the current working directory and tell me the path.
```

## Agent stdout (verbatim)

```
**`/private/tmp/claude-501/-Users-buda007--claude-skills/c1fe6555-a560-4f4a-9571-e36f24c52787/scratchpad/td-runs/web-3/news.ycombinator.com-orientation.md`**

Working-depth orientation memo. Scope held to what a logged-out visitor gets: `robots.txt` read first and honoured (no request to any `Disallow` path), ~25 hand-paced requests across 13 paths, no account created.

Headline findings your team should know:

- **No CDN.** `news.ycombinator.com` is one origin IP in a San Diego colo (AIS/M5), rDNS matching, zero CDN headers — while `www.ycombinator.com` is Cloudflare and the apex is CloudFront. Route 53 A-record TTL is **1 second**, which is the failover story instead.
- **The nginx/app seam is directly observable.** `ETag: "6a0f772b-1461"` decodes to size 5217 and mtime 2026-05-21 21:20:43, both matching the other headers exactly — nginx's own format, so static comes off disk and everything else is proxied. Dynamic routes are `chunked` with no Content-Length.
- **Render is nearly free.** A 273 KB comment page and a 34 KB front page have the same TTFB (0.650 s vs 0.653 s), both within 12–40 ms of a static file. The latency is RTT to one distant origin, not server work.
- **5,217 bytes of JavaScript total**, unminified, no framework, no bundler, no third-party scripts or analytics anywhere.
- **Comment trees are flat** — 167 sibling rows with an `indent="0..8"` attribute, not nested DOM. Model the sequence, not the tree.
- **Security-header gap:** `/` and `/item` carry the full set; `news.css`, `hn.js`, `newsfaq.html` (all 200) and the 404 carry **none**. A scanner sampling only the homepage reports clean.

Ledger: N=15, 11 confirmed / 3 unconfirmed / 1 dropped; alternatives explicitly ruled out on 9 of 15. The dropped row was mine — I first read "JS interception is members-only" off an exact-match grep that missed `class="togg clicky"`.

Three things I deliberately did **not** establish: the application language (widely reported as Arc; not observable from the target, and the FAQ doesn't say, so it's flagged UNCONFIRMED rather than filled in from memory), anything behind login, and a second network vantage to fully exclude anycast.

One note on format: the prose body lands at about two pages as the template intends, but the 15-row ledger pushes the file past that. That's apparatus, not scope creep — the remaining gaps in §7 are access-limited, not effort-limited, so Full depth wouldn't close them without an account your organisation holds under its own name.
```

## Deliverable written by the run — `news.ycombinator.com-orientation.md` (verbatim)

# Orientation: Hacker News (news.ycombinator.com)

## 0. Provenance

- **Pin** — `https://news.ycombinator.com/`, captured 2026-08-20 16:29–16:36 UTC, from a single
  US vantage point, **unauthenticated**, no account, default (logged-out) view.
- **Depth** — working (orientation memo).
- **Access basis** — third party, no authorization beyond ordinary permitted use. Public pages,
  response headers, public DNS/TLS, and the site's own documented public API only. `robots.txt`
  was read first and honoured: no request was made to any `Disallow` path (`/vote`, `/x?`, `/r?`,
  `/context?`, `/reply?`, `/hide?`, `/fave?`, `/flag?`, `/collapse?`, `/login`, `/logout`,
  `/submitlink?`). ~25 requests total across 13 distinct paths — hand-paced, nothing automated.
- **What was NOT examined** — anything behind login (so: submission, voting, moderation, profile,
  and email flows), any paid or privileged tier, the admin surface, and 15 of the 16 derived list
  views. No account was created, deliberately: creating one binds the reader to HN's terms, and
  the terms are the thing that turns a lawful teardown into a contract problem. No fuzzing, no
  enumeration, no probing for vulnerabilities.

## 1. What this system is

Hacker News is a single-purpose social link aggregator run by Y Combinator: users submit URLs and
text posts, vote on them, and discuss them in threaded comments, with a ranking algorithm and
active human moderation deciding what reaches the front page. Architecturally the interesting
thing about it is not what it does but what it refuses to do — it is a high-traffic, twenty-year-old
site that serves fully server-rendered HTML from a **single origin server in a colo**, with no CDN,
no client-side framework, no third-party scripts, no analytics, and 5 KB of hand-written JavaScript
for the entire site. Almost every architectural decision below is downstream of that one posture.

## 2. System context

```
                    ┌─────────────────────────┐
   readers,         │   Reader / member       │
   logged-out ─────▶│   (browser)             │
   and members      └───────────┬─────────────┘
                                │ HTTPS, server-rendered HTML
                                │ (+ tiny XHR for vote/collapse)
                                ▼
   ┌────────────────────────────────────────────────────────┐
   │  news.ycombinator.com                                  │
   │  single origin: 209.216.230.207 / 2606:7100:1:67::26   │
   │  colo (American Internet Services / M5, San Diego)     │
   │  nginx  ──▶  bespoke application server                │
   │  NO CDN in front. Route 53 A-record TTL = 1s.          │
   └───┬────────────────┬──────────────────┬────────────────┘
       │                │                  │
       │ mirrors        │ search is        │ login/recaptcha
       │ ranking state  │ handed off       │ assets only
       ▼                ▼                  ▼
 ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐
 │ Firebase     │ │ Algolia      │ │ Google reCAPTCHA,      │
 │ public API   │ │ hn.algolia   │ │ cdnjs, account.ycombi- │
 │ (GCP)        │ │ .com (GCP)   │ │ nator.com (per CSP)    │
 │ 3rd-party    │ │ full-text    │ │ — not loaded on the    │
 │ clients, bots│ │ search UI    │ │ logged-out front page  │
 └──────────────┘ └──────────────┘ └────────────────────────┘
```

Sibling YC properties sit on CDNs and show it — `www.ycombinator.com` is a Cloudflare CNAME, the
apex is CloudFront, `account.ycombinator.com` is Cloudflare. HN alone is not. That asymmetry is
the single most load-bearing fact in this memo.

## 3. How it's put together

**A two-layer origin, and you can see the seam in the headers (C2).** nginx serves static files straight
off disk and the application handles everything else. The tell is exact rather than circumstantial:
`hn.js` comes back with `ETag: "6a0f772b-1461"`, which decodes as nginx's `hex(mtime)-hex(size)` —
`0x1461` = 5217 bytes, matching `Content-Length` precisely, and `0x6a0f772b` = 2026-05-21 21:20:43,
matching `Last-Modified` to the second. Dynamic pages carry no ETag, no Last-Modified and no
Content-Length at all — just `Transfer-Encoding: chunked`. Knowing which layer answered a given URL
is the fastest way to reason about anything else here.

**The app streams, and the render is nearly free (C3, C4).** A 273 KB comment page and a 34 KB front page
have the *same* time-to-first-byte (0.650 s vs 0.653 s), and both are within 12–40 ms of a static
file from the same vantage (0.641 s). So: nginx is not buffering the proxied response, the app
starts emitting HTML immediately, and the actual cost of assembling a front page is tens of
milliseconds. The 0.64 s floor is round-trip time to one distant origin, not server work.

**The comment tree is flat (C7).** 167 comments on the page we read are 167 sibling `<tr class="athing
comtr">` rows in one table, each carrying `class="ind" indent="N"` with N from 0 to 8. The tree is
flattened server-side into a pre-order sequence plus a depth integer; nothing is nested in the DOM.
Collapse is therefore a pure client-side sibling walk — `hn.js` compares `indent` values until it
finds one at or above the starting depth — and the toggle anchors ship a precomputed subtree size
(`n="33"`). If you are modelling HN's data, model the flat sequence, not the tree.

**All the JavaScript, all of it, is 5,217 bytes (C14).** One unminified `<script src>`, no bundler, no
sourcemap, no framework, no module wrapper — plain function declarations and `document.getElementById`.
Voting is optimistic and fire-and-forget: `function send (url) { var req = new XMLHttpRequest();
req.open('GET', url); req.send(); }` — the response is never read. The front page pulls exactly four
same-origin subresources (`news.css`, `hn.js`, `y18.svg`, and `s.gif`, a spacer GIF) and zero
third-party assets. No analytics, no tag manager, no fonts.

**Two pagination schemes, split by view semantics (C8).** Ranked views page by ordinal — the front page's
"More" is `?p=2`. Chronological views page by cursor — `/newest`'s is `newest?next=49376497&n=31`,
an item ID plus a count. That is the right split: offset paging into a list that grows at the head
would duplicate and skip rows, and `/newest` grows at the head constantly.

**Ranking is a set of named, precomputed views (C5 is the open question here).** `/lists` enumerates sixteen of them — `front`,
`pool`, `invited`, `highlights`, `best`, `bestcomments`, `active`, `noobstories`, `classic`,
`whoishiring`, `launches` and others. Several are explicitly editorial (`pool` is "links selected
for a second chance at the front page"; `invited` is "overlooked links, invited to repost"). The
ranking pipeline has human operators wired into it as first-class inputs, not as an afterthought.

**The public API is the same state, not a parallel one (C6).** `hacker-news.firebaseio.com/v0/topstories.json`
returned 500 IDs whose first five — `49372583, 49347543, 49373456, 49362689, 49374269` — are
identical, and in identical order, to the first five story IDs in the front-page HTML captured four
minutes earlier. The Firebase API is a mirror of the ranking the site itself renders.

## 4. Decisions that shape it

| Decision | Probable reason | Evidence | Verdict |
|---|---|---|---|
| No CDN; one origin in a colo, with a 1-second DNS TTL | Content is per-user (vote arrows, collapse state, `cache-control: private`), so edge caching buys little; a 1 s Route 53 TTL gives origin failover without an anycast layer to debug | Single A/AAAA record; rDNS = the hostname; netblock is AIS/M5 San Diego; zero `CF-Ray`/`X-Amz-Cf-Id`/`Via`/`Age`/`X-Cache` headers; authoritative TTL = 1 | CONFIRMED (C1) |
| Server-render everything; ship 5 KB of JS | Optimises the thing that actually matters here — TTFB and text — and removes an entire build/deploy/dependency surface | One 5,217-byte script; no bundler or sourcemap output; `Transfer-Encoding: chunked` on every dynamic route | CONFIRMED (C3, C14) |
| Hand-write the security headers, and scope them to dynamic 2xx | Retrofitted onto a pre-existing app over time (the disclosure log shows exactly this drip); attached at the proxy/app boundary rather than globally | Full header set on `/` and `/item`; **none** on `news.css`, `hn.js`, `newsfaq.html`, or the 404 | CONFIRMED as observed; mechanism unresolved (C9) |
| Delegate search entirely to Algolia | Full-text search over 20 years of comments is a different engineering problem than serving ranked lists; renting it keeps it out of the origin | Footer form posts `method="get" action="//hn.algolia.com/"`; that host resolves into GCP; no search endpoint observed on the origin | CONFIRMED (C13) |
| One global asset version token instead of per-file hashes | Simplest possible cache-busting for exactly two files | `news.css` and `hn.js` share the token `?DSX7V05cFJdNqZFnAs6i` despite `Last-Modified` dates 4.5 months apart (2026-01-04 vs 2026-05-21) | CONFIRMED (C12) |

## 5. Where the bodies are buried

**Static assets and error responses have no security headers (C9).** This is the finding most likely to
mislead someone auditing the site. Fetch `/` and you get a complete, carefully-written set: `CSP`,
`X-Frame-Options: DENY`, `X-Content-Type-Options`, `Referrer-Policy`, HSTS. Fetch `/news.css`,
`/hn.js` or `/newsfaq.html` — all HTTP 200 — and you get *none of them*. The 404 gets none either.
A scanner that samples the homepage will report a clean bill of health for a surface that is only
partly covered. The likely mechanism is an nginx `add_header` in the proxy location without
`always` (nginx's default status list excludes 404s, which fits exactly), but app-level emission
fits the same evidence and we could not separate them from outside.

**`cache-control: private; max-age=0` uses a semicolon where the spec requires a comma.** Parsers
that split strictly on `,` will read this as a single unknown directive named
`private; max-age=0` and fall back to their default heuristic. Harmless in practice — everything
downstream treats it as uncacheable anyway — but it is a reliable signal that these headers are
assembled by hand rather than by a framework, and it will confuse a strict cache-conformance tool.

**`/lists` is not a UI convenience, it is the ranking pipeline's surface area.** Someone new will
read the front page as *the* algorithm. It is one of sixteen views, and at least two of them
(`pool`, `invited`) are moderator-curated queues that feed the front page. Any model of "how does
something get to the top of HN" that omits the human step is wrong.

**The 404 is `text/plain` and the body is the single word `Unknown.`** It is generated by the
application, not by nginx — nginx's default 404 is HTML with `<center>nginx</center>` in it. So
unmatched paths are reaching the app, which means routing is the app's job, not the proxy's.

**Vote links behave differently logged-out, and it is easy to mis-read.** We initially read the
absence of `class="clicky"` on the front page as "JS interception is members-only" — that was
wrong, and we dropped it (C15 below). `togg clicky` *is* present on comment toggles for
logged-out readers; what is actually absent is the `auth=` CSRF token on vote URLs. Collapse works
without an account; voting does not.

**The origin is a single point of failure by design (C1), and the 1-second DNS TTL is the mitigation.**
If your team's mental model is "there's a CDN in front, so an origin blip is absorbed" — there
isn't, and it isn't.

## 6. Falsification ledger

```
FALSIFICATION LEDGER
Target: web   Depth: working
Method: evidence-column attack — each inferred claim given a named alternative explanation,
        then ruled out or explicitly left standing

Inferred claims (one row each — this list IS N):
  C1  Served from a single colo origin, not behind a CDN
      → CONFIRMED    evidence: 1 A + 1 AAAA record, rDNS = hostname, netblocks AIS/M5 (colo, not a
        CDN ASN), zero CDN headers. Alternative "anycast CDN with scrubbed headers" ruled out three
        ways: connect=0.24s / TLS=0.49s is a distant single origin, not an edge PoP; a 1s DNS TTL is
        pointless under anycast; sibling YC hosts DO use CDNs and expose them plainly.
  C2  nginx serves static files from disk; the app serves everything else
      → CONFIRMED    evidence: ETag "6a0f772b-1461" decoded = size 5217 (= exact Content-Length) and
        mtime 2026-05-21 21:20:43 (= exact Last-Modified), i.e. nginx's own hex(mtime)-hex(size)
        format; plus Accept-Ranges and split Cache-Control lines. Alternative "app imitates nginx's
        header format" ruled out — it would have to reproduce the hex encoding coincidentally.
  C3  The app streams; nginx does not buffer the proxied response
      → CONFIRMED    evidence: Transfer-Encoding: chunked, no Content-Length, on every dynamic route;
        TTFB for a 273 KB page (0.650s) equals TTFB for a 34 KB page (0.653s) while total grows to
        1.49s. Alternative "proxy_buffering on" ruled out — it would scale TTFB with body size.
  C4  Dynamic render adds only ~12–40 ms over serving a static file
      → CONFIRMED    evidence: dyn TTFB 0.653/0.656/0.681 vs static 0.641, same vantage. Alternative
        "measurement noise" ruled out by three consistent samples.
  C5  That speed reflects precomputed/in-memory ranking state rather than per-request queries
      → UNCONFIRMED  evidence: consistent with C4 but not settled by it. A reverse-proxy micro-cache
        or a warm database cache produces the same timing. Not separable from outside.
  C6  The public Firebase API and the HTML are driven by the same ranking state
      → CONFIRMED    evidence: /v0/topstories.json first five IDs identical and identically ordered
        to the front page's first five, ~4 min apart, from a 500-item list. Alternative "coincidence"
        ruled out on combinatorics. (Direction of derivation remains unknown — see §7.)
  C7  Comment trees are flat pre-order sequences with an explicit depth attribute
      → CONFIRMED    evidence: 167 sibling `athing comtr` rows, indent="0".."8", histogram
        46/44/33/20/14/6/2/1/1; hn.js collapses by walking siblings on that attribute. Alternative
        "nested markup flattened by the browser" ruled out — depth is an attribute, not nesting.
  C8  Two pagination schemes, split ranked vs chronological
      → CONFIRMED    evidence: `/` → `?p=2`; `/newest` → `newest?next=49376497&n=31`. Alternative
        "one scheme with an optimisation" ruled out — the split tracks view type systematically.
  C9  Security headers cover dynamic 2xx only, not static assets or errors
      → CONFIRMED (observable) / mechanism UNCONFIRMED   evidence: full set on `/` and `/item`; none
        on news.css, hn.js, newsfaq.html (all 200) or the 404. Two mechanisms — nginx add_header
        without `always`, or app-level emission — fit identically and were NOT separated.
  C10 The application language/runtime
      → UNCONFIRMED  evidence: signals constrain it (op="<handler>" on <html>, opaque /x? and /r?
        continuation endpoints in robots.txt, a bare "Unknown." text/plain 404, relative-URL
        generation, hand-rolled everything) — all consistent with a bespoke non-framework server.
        HN is widely *reported* to run on Arc; that is not observable from the target and the FAQ
        does not state it, so it is not asserted here.
  C11 Password hashing is bcrypt today
      → UNCONFIRMED  evidence: HN's own /security.html states bcrypt as of the 2017-04-30 entry.
        That is a first-party statement about 2017, not about now; no current observation is
        possible without an account, which was out of scope.
  C12 Asset versioning is one global token, not per-file content hashing
      → CONFIRMED    evidence: identical token ?DSX7V05cFJdNqZFnAs6i on two files whose Last-Modified
        differ by 4.5 months. Alternative "hash collision" ruled out on probability.
  C13 User-facing search is delegated off-site to Algolia
      → CONFIRMED (as scoped)  evidence: footer form action="//hn.algolia.com/", host in GCP; no
        search endpoint on the origin in any page read. Alternative "an unlinked internal search
        also exists" NOT ruled out — we did not enumerate, by design.
  C14 Total client JS is 5,217 bytes, no framework or bundler (logged-out)
      → CONFIRMED (as scoped)  evidence: Content-Length 5217, sole <script src>, unminified, no
        sourceMappingURL. Alternative "more JS for members" NOT ruled out — CSP permits cdnjs and
        reCAPTCHA, neither loaded on the logged-out page. Claim is scoped to logged-out accordingly.
  C15 JS click-interception is members-only
      → DROPPED      evidence: disconfirmed. An exact-match grep for class="clicky" missed
        class="togg clicky", which IS present logged-out on comment toggles. What is actually absent
        logged-out is the auth= CSRF token on vote URLs.

  N = 15   confirmed 11 / downgraded 3 / dropped 1   (11+3+1 = 15)

Coverage denominator:
  INFERRED rows with an alternative explicitly ruled out: 9 of 15
  (not ruled out: C5, C9-mechanism, C10, C11, C13; disconfirmed: C15)

System scale examined:
  13 distinct paths fetched on the origin, of an unenumerated total · ~25 requests · 1 external API
  queried · 1 of 16 derived list views inspected · 1 comment thread (167 comments) read · 5 of 6+
  page templates seen · 0 of 2 authentication states observed (logged-out only) · 1 network vantage
  point, 1 capture window.

Falsification NOT performed, and why:
  - No multi-vantage check of C1. One vantage cannot fully exclude geographic anycast; ruled out by
    RTT shape and netblock ownership instead, which is weaker than a second-continent probe.
  - No authenticated-session observation of anything. Deliberate: an account binds the reader to
    HN's terms, which prohibit competitive/automated use. This is the largest single gap.
  - No HAR/DevTools capture of the member-side XHR surface, for the same reason.
```

## 7. What we could not determine

| Unknown | Why unresolved | What would resolve it |
|---|---|---|
| Application language, runtime, and process model | Not observable from outside; the site's own FAQ does not state it; refusing to fill it from memory (C10) | A first-party statement, published source, or a maintainer conference talk |
| Whether one origin host means one *server* | A single IP can front a load balancer or a multi-process host; nothing in the response distinguishes them | Origin-side knowledge; or a `Connection`/timing side-channel study we did not consider proportionate |
| Whether ranking state is in-memory, cached, or queried per request (C5) | Timing is consistent with all three | Source access, or a first-party description |
| Direction of derivation between the site and the Firebase API (C6) | They demonstrably agree; which one is upstream is not visible | First-party documentation of the export path |
| Which layer emits the security headers (C9) | nginx `add_header` without `always` and app-level emission fit the same evidence | Origin config; or a response class that separates the two |
| Everything behind login: submit, vote, moderate, profile, email, rate limits, `/x?` and `/r?` semantics | Out of authorized scope — no account, and `robots.txt` disallows those paths | The organisation's own account under its own name, if HN's terms permit the use |
| Current password hashing (C11) | Only a 2017 first-party statement is public | A current first-party statement |
| Traffic volume, infrastructure cost, team size | Not inferable from what we observed; third-party estimators diverge widely and were not used | Not resolvable from public observation with useful precision |

## 8. Where to go deeper

The site's own pages turned out to be the trustworthy sources and are worth reading directly:
`/security.html` is a first-party disclosure log — 25 named vulnerabilities from 2009 to 2026-07,
which doubles as a candid history of the site's security posture (bcrypt in 2017, SameSite cookies
in 2021, an XSS in poll options in 2025). `/lists` documents the ranking views. `/newsfaq.html`
describes ranking inputs in prose but says nothing about implementation — do not mine it for stack
detail.

The one thing a Full teardown would genuinely add is the authenticated surface, and it should only
be commissioned if the organisation already holds an account under its own name and its counsel is
comfortable that the intended use fits HN's terms. Absent that, this memo is close to the ceiling
of what public observation supports, and the gaps in §7 are honest limits rather than missing work.
