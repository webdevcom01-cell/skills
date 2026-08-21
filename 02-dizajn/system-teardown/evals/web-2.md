# Run `web-2` — raw output

| | |
|---|---|
| Target type | web |
| Target / pin | https://jsonplaceholder.typicode.com/ (third party, public, unauthenticated) |
| Verdict | **FAIL** |
| session_id | `d60219ea-b2e0-44b1-99e5-d724448d9f33` |
| Turns | 24 |
| Cost (USD) | 1.68 |
| is_error | False |
| Deliverable | jsonplaceholder-orientation.md |
| Deliverable words | 2618 |

**Grade:** P1 sections PASS · P2 ledger PASS · P3 unknowns PASS · P4 deviations-out-loud FAIL → **FAIL**

**Reason:** ledger 8+2+0=10 correct, 10 of 10 INFERRED rows given a named alternative, refused to call C8 globally dead from one vantage point; 2618w never acknowledged

## Prompt given (verbatim)

```
Use the system-teardown skill.

Target: the public API at https://jsonplaceholder.typicode.com/ . Third party, public, unauthenticated; I have ordinary permitted use only and no written authorization.

Help me understand how that service is put together.

Write any output file into the current working directory and tell me the path.
```

## Agent stdout (verbatim)

```
**Path:** `/private/tmp/claude-501/-Users-buda007--claude-skills/c1fe6555-a560-4f4a-9571-e36f24c52787/scratchpad/td-runs/web-2/jsonplaceholder-orientation.md`

Headline findings:

**It's stock `json-server` v0.x on Heroku behind Cloudflare.** Confirmed against the project's own public source at v0.17.4 — the CORS config, gzip, the byte-level 2-space JSON indentation, and a vestigial `Pragma: no-cache`/`Expires: -1` pair all match `defaults.js` verbatim. v1 syntax (`_per_page`, `_sort=-id`) is inert, which pins it to the v0 line. A thin custom middleware adds rate-limit headers, `nosniff`, and a 12h `Cache-Control` that overrides json-server's `no-cache` — you can see the seam.

**The real API is ~3× what the site documents.** `_embed`, `_expand`, `_sort`/`_order`, `q`, `_gte`/`_lte`, `X-Total-Count` + RFC 5988 `Link`, and `GET /db` (whole 1.38 MB database in one response) all work and none are on the site.

Three traps worth knowing before you build against it:

- **Unknown query fields are silently ignored.** `?nosuchfield=1` returns all 500 comments; `?postId=99999` correctly returns 0. So undocumented nested routes like `/users/1/comments` return `200` with the entire unfiltered collection — plausible-looking success, wrong data. Assert on length, not status.
- **All 5,000 photo URLs point at `via.placeholder.com`, which served me nothing** — TLS handshake fails outright, HTTP returns `403 Request forbidden by administrative rules`. Only observed from one vantage point, so it's logged UNCONFIRMED, but the JSON is intact and the images aren't.
- **`X-RateLimit-Remaining` is meaningless as delivered** — Cloudflare caches the headers, so you can get `remaining: 999` with `age: 24822` and a `reset` two days in the past.

Falsification ledger: N=10, 8 confirmed / 2 downgraded / 0 dropped; all 10 inferred rows given a named alternative, 8 ruled out. Full coverage of the resource graph (6/6 collections, 5,910/5,910 records) from a single network vantage point — which is precisely what leaves the dead-image-host claim unsettled.
```

## Deliverable written by the run — `jsonplaceholder-orientation.md` (verbatim)

# Orientation: JSONPlaceholder (jsonplaceholder.typicode.com)

## 0. Provenance

- **Pin** — `https://jsonplaceholder.typicode.com/`, captured 2026-08-20T16:02Z–16:10Z from a
  Cloudflare VIE (Vienna) edge. TLS leaf `CN=typicode.com`, issuer Google Trust Services WE1,
  valid 2026-07-29 → 2026-10-28. No version string is published by the service.
- **Depth** — working.
- **Authorization** — third party, public, unauthenticated, no written authorization. Everything
  below comes from **ordinary permitted use and public artifacts only**: the site's own two HTML
  pages, its documented endpoints, its documented HTTP verbs, response headers, DNS, the TLS
  certificate, and the public source of the OSS project the site itself links to. No enumeration,
  no fuzzing, no auth or rate-limit circumvention, no accounts (none exist). Approximately 55
  requests total against a published limit of 1000.
- **What was NOT examined** — no HAR or browser session, no observation from a second geography,
  no load or latency profiling, no Heroku-side configuration, and no attempt to reach the origin
  other than through Cloudflare.

## 1. What this system is

JSONPlaceholder is a free, public, read-mostly fake REST API that front-end developers point at
when they need realistic JSON to build against and do not yet have a backend. It serves one
fixed, shared, immutable dataset — a small blog-and-users world of 5,910 records — and it accepts
write requests only to *pretend* to honour them: a POST returns `201` with a plausible new id,
and the record does not exist a second later. Its entire value proposition is being permanently
available, requiring zero setup, and never changing under you. It is maintained by one person
(typicode) as the public showcase for their own open-source project, `json-server`.

## 2. System context

```
        ┌──────────────────────────┐
        │  Front-end developer /   │   reads docs, copy-pastes fetch() snippets
        │  tutorial / test suite   │
        └────────────┬─────────────┘
                     │ HTTPS, unauthenticated, CORS-enabled from any origin
                     ▼
        ┌──────────────────────────────────────────────┐
        │        Cloudflare  (DNS + CDN + TLS)         │──► Google Trust Services (cert)
        │  caches GET for 12h; terminates HTTP/2 & /3  │
        └────────────┬─────────────────────────────────┘
                     │ origin fetch on cache MISS
                     ▼
        ┌──────────────────────────────────────────────┐
        │   Heroku router ──► Node/Express dyno         │──► nel.heroku.com (error reporting)
        │   custom middleware (rate limit, nosniff,     │
        │   cache policy) wrapping stock json-server    │
        │   + static landing page & guide               │
        └────────────┬─────────────────────────────────┘
                     │ reads
                     ▼
        ┌──────────────────────────────────────────────┐
        │  In-memory JSON database (6 collections)     │
        │  posts/comments/albums/photos/users/todos    │
        └──────────────────────────────────────────────┘

  Also referenced, but NOT operated by this system:
    • via.placeholder.com — image host named by all 5,000 photo records (see §5)
    • cdnjs.cloudflare.com — Prism syntax highlighter on the docs pages
    • Google Analytics 4, property G-E3C3GCQVBN — on the docs pages only
```

## 3. How it's put together

**It is stock `json-server` v0.x, not a bespoke API.** This is the single most useful thing to
know, because it means the *real* API surface is `json-server`'s README, not JSONPlaceholder's
own guide — and the README documents roughly three times more capability than the site does. The
whole v0 query grammar is live and undocumented here: `_limit`, `_page`, `_start`/`_end`,
`_sort`/`_order`, `q` for full-text search, `_embed` to inline children, `_expand` to inline the
parent, and `_gte`/`_lte` range operators. Paginated responses carry `X-Total-Count` and a proper
RFC 5988 `Link` header with `first`/`prev`/`next`/`last`, both explicitly CORS-exposed.

**`GET /db` returns the entire database in one 1.38 MB response.** It is a stock `json-server`
route, undocumented on the site, and it is the fastest way to get the whole corpus — worth knowing
if you were about to write a loop that makes six requests, or 5,000.

**The data model is a regular, synthetic blog schema** with no ragged edges: 10 users, each owning
10 posts, 10 albums, and 20 todos; each post carrying exactly 5 comments; each album exactly 50
photos. 90 of 200 todos are `completed`. Foreign keys are dense and complete — every `userId` is
1–10, every `postId` and `albumId` is 1–100. `users` is the only collection with nested objects
(`address.geo`, `company`), which makes it the only one useful for exercising nested rendering.

**A thin custom middleware layer wraps the stock server.** Three headers appear that `json-server`
v0 does not emit: `X-RateLimit-Limit: 1000` with `-Remaining`/`-Reset`, `X-Content-Type-Options:
nosniff`, and `Cache-Control: max-age=43200`. That last one overrides `json-server`'s default
`no-cache` — you can see the seam, because the two headers set alongside it in the same stock
middleware block, `Pragma: no-cache` and `Expires: -1`, are still there, now contradicting it.

**Cloudflare in front, Heroku behind.** `Server: cloudflare` + `CF-Ray` + Cloudflare nameservers on
the edge; `Via: 2.0 heroku-router`, `X-Powered-By: Express` and Heroku-signed NEL reporting tokens
from the origin. The 12-hour cache TTL is what makes a free single-dyno app survive being one of
the most-hit teaching APIs on the internet — most requests never reach Node at all.

**The docs site is served by the same Express process**, out of `json-server`'s static directory:
two hand-written HTML pages, one local stylesheet, Prism from cdnjs, and GA4. There is no
front-end framework, no build step, and no `.map` files. The guide page still reads "© 2024".

## 4. Decisions that shape it

| Decision | Probable reason | Evidence | Verdict |
|---|---|---|---|
| Run the maintainer's own OSS project rather than a custom API | The site is `json-server`'s live demo; zero marginal maintenance, and the demo *is* the marketing | C2, C3 — full v0 param grammar, `GET /db`, 2-space pretty-print, vestigial `Pragma`/`Expires` | CONFIRMED |
| Fake all writes instead of rejecting them | Tutorials need `POST`/`PUT`/`DELETE` to appear to work; real writes on a shared public dataset would be vandalised within minutes | C5 — `201` with id 101, then `404` on `/posts/101`; `PUT`/`DELETE` on `/posts/1` succeed, title unchanged | CONFIRMED |
| 12-hour CDN cache in front of one dyno | The dataset never changes, so caching is free correctness-wise and is the only reason a free-tier origin can carry this traffic | C1, C9 — `cf-cache-status: HIT` with `age` up to 24,822s; forced MISS reaches Heroku | CONFIRMED |
| Fully permissive CORS with credentials | The entire audience calls it from `fetch()` in a browser from arbitrary origins | C2 — preflight reflects `Access-Control-Allow-Origin: https://example.com`, `-Credentials: true`, matching `cors({origin:true, credentials:true})` | CONFIRMED |
| Document ~30% of the surface | Keeps the landing page teachable; the rest is deliberately delegated to `json-server`'s README | C2, C7 — `_embed`/`_sort`/`q`/`/db` all work, none documented on-site | CONFIRMED |

## 5. Where the bodies are buried

**Unknown query fields are silently ignored, so a wrong filter returns the entire collection
rather than an error.** `GET /comments?nosuchfield=1` returns all 500 comments, and
`?postId=99999` correctly returns 0 — so the filter works for fields that exist and quietly
evaporates for fields that do not. The trap this sets is in the nested routes. The guide lists
five nested routes; the routing is generic, so `/users/1/comments` and `/posts/1/todos` also
return `200` — with all 500 comments and all 200 todos, unfiltered. If you build against a nested
route that isn't on the documented list, you get a plausible-looking success and silently wrong
data. Assert on the length of what comes back, not on the status code.

**All 5,000 photo URLs point at a host that did not serve me an image.** Every `photos` record
names `via.placeholder.com`. From this vantage point that host fails the TLS handshake outright
(no peer certificate) and returns `403 Request forbidden by administrative rules` over plain HTTP,
with and without a browser User-Agent. The JSON is intact; the pictures it promises are not. If
you are demoing an image grid, substitute your own placeholder source. (Single vantage point — see
C8 in the ledger.)

**`X-RateLimit-Remaining` is meaningless as delivered.** Because Cloudflare caches the response
including its headers, a `HIT` can hand you `remaining: 999` alongside `age: 24822` and a `reset`
timestamp roughly two days in the past. Only on a forced cache MISS does the counter move
(I watched it go 999 → 990 → 987). Do not write client back-off logic against these numbers.

**`PUT` replaces, `PATCH` merges — and the response shapes differ accordingly.** `PATCH /posts/1`
returns the full merged record; `PUT /posts/1` returns only the fields you sent plus `id`. Neither
is persisted, so a test that round-trips a `PUT` and then re-reads will always see the original.

**The landing page's "one level of nested route" is true and load-bearing.** `/users/1/albums/1/photos`
is not a route. Compose with query parameters instead.

## 6. Falsification ledger

```
FALSIFICATION LEDGER
Target: web   Depth: working
Method: evidence-column attack (each INFERRED conclusion given a named alternative explanation,
        then tested against a differential probe or a public source artifact)

Inferred claims (one row each — this list IS N):
  C1  Cloudflare edge in front of a Heroku-hosted Node origin
      → CONFIRMED   evidence: Server/CF-Ray/CF-Cache-Status + Cloudflare NS on the edge;
        Via: 2.0 heroku-router + X-Powered-By: Express + NEL endpoint at nel.heroku.com from the
        origin. ALT "a self-hosted proxy forging the Via header" — ruled out: the NEL/Report-To
        headers carry a signed Heroku token and session id a forgery has no reason to synthesise.
  C2  The API is stock json-server, not a bespoke Express app imitating it
      → CONFIRMED   evidence: the complete v0 grammar responds (_limit/_page/_start/_end/
        _sort/_order/q/_embed/_expand/id_gte), X-Total-Count + RFC5988 Link, and GET /db returns
        the whole 1.38 MB db keyed by collection. Corroborated against the project's own public
        source at v0.17.4: cors({origin:true,credentials:true}) matches the observed preflight,
        compression() matches the gzip, express().set('json spaces', 2) matches the byte-level
        2-space indentation, and the defaults block's Pragma/Expires pair is present verbatim.
        ALT "hand-written API deliberately mimicking json-server" — ruled out as an explanation
        for the coincidence set: nobody reimplements GET /db, the exact pretty-print width, and a
        vestigial IE-era Pragma/Expires pair.
  C3  It is the v0 line specifically, not json-server v1
      → CONFIRMED   evidence: v1 syntax is inert — _per_page=5&_page=2 returns 10 items (v0
        default page size), _sort=-id returns ascending — while v0 syntax _sort=id&_order=desc
        works. ALT "v1 running a v0 compatibility shim" — ruled out: v1 would still honour its
        own native syntax.
  C4  A custom middleware layer wraps the stock server (rate limit, nosniff, cache policy)
      → CONFIRMED   evidence: X-RateLimit-* and X-Content-Type-Options are absent from v0's
        defaults.js (read directly), and Cache-Control: max-age=43200 replaces the default
        no-cache while Pragma: no-cache and Expires: -1 from the same stock block survive —
        proving a later middleware sets Cache-Control alone. ALT "Cloudflare or the Heroku router
        injects these" — ruled out: an edge rewrite would have normalised Pragma/Expires too, and
        the rate-limit counter decrements only on cf-cache-status MISS, i.e. at the origin.
  C5  Writes are never observable afterwards; the dataset is immutable and shared
      → CONFIRMED   evidence: POST /posts → 201 {id:101}, then GET /posts/101 → 404; PUT and
        DELETE on /posts/1 both return success, and /posts/1 still returns its original title.
        ALT "persisted to a per-dyno in-memory db and my read hit a different dyno" — ruled out
        for the claim as stated, which is about observability, not storage: no ordering of dynos
        makes a written record retrievable.
  C6  The mechanism of the write simulation (no-op middleware vs. per-request state reset)
      → UNCONFIRMED evidence: both mechanisms produce identical observable output from outside.
        Distinguishing them needs origin logs or config, which is not available under ordinary
        permitted use.
  C7  Unknown query fields are silently ignored, so undocumented nested routes return the full
      unfiltered collection
      → CONFIRMED   evidence: differential — /comments?nosuchfield=1 → 500 items while
        /comments?postId=99999 → 0 items; /users/1/comments → 500, /posts/1/todos → 200.
        ALT "/users/1/comments is a deliberately supported all-comments route" — ruled out by the
        nosuchfield differential, which exposes the generic ignore-unknown-field rule underneath.
  C8  The image host named by all 5,000 photo records is dead
      → UNCONFIRMED evidence: via.placeholder.com fails the TLS handshake with no peer
        certificate and returns 403 "Request forbidden by administrative rules" over HTTP, with
        and without a browser UA; DNS resolves to AWS addresses. ALT "geo-block or ASN-block
        affecting only this vantage point" — NOT ruled out; one client, one location. What would
        settle it: the same two requests from a second network and a second country. The
        narrower claim — that it does not serve images from here — is observed.
  C9  Rate-limit headers are unreliable to clients because the CDN caches them
      → CONFIRMED   evidence: on cf-cache-status HIT, x-ratelimit-remaining: 999 arrives with
        age: 24822 and an x-ratelimit-reset ~2 days stale; on a forced MISS the counter moves
        (999 → 990 → 987). ALT "multiple origin dynos with independent counters" — this would
        also explain the counter jumps and is NOT ruled out, but it cannot explain a header
        delivered with a 6.9-hour age, so the caching claim stands on its own.
  C10 The docs pages are served by the same Express process, not a separate static host
      → CONFIRMED   evidence: GET / returns text/html carrying Via: 2.0 heroku-router and
        X-Powered-By: Express, and json-server's defaults mount express.static ahead of the
        router. ALT "Cloudflare Pages serving HTML, Heroku serving only /api" — ruled out by
        those two origin headers on the HTML response itself.

  N = 10   confirmed 8 / downgraded 2 / dropped 0   (8+2+0=10)

Coverage denominator (not freely chosen):
  INFERRED rows given a named alternative: 10 of 10 (y = every INFERRED row in this document)
  Alternatives actually ruled out: 8 of 10

System scale examined:
  6 of 6 published collections traced · 5,910 of 5,910 records retrieved · 2 of 2 site pages read
  · ~55 HTTP requests against a 1000 limit · 1 of 1 network vantage points (Cloudflare VIE)
  · 0 authenticated tiers (the service has none) · 0 of 0 sourcemaps (none published)

Falsification NOT performed, and why:
  No HAR / proxy capture and no mitmproxy2swagger-derived OpenAPI diff — this is a documented
  JSON API consumed directly, so the capture would have reproduced what curl already showed.
  No multi-geography check, which is exactly what leaves C8 unconfirmed.
```

## 7. What we could not determine

| Unknown | Why unresolved | What would resolve it |
|---|---|---|
| Whether `via.placeholder.com` is globally dead or blocking this vantage point (C8) | Observed from one client on one network in one country | The same HTTP+TLS probe from a second country and a second ASN |
| How the write simulation is implemented (C6) | Externally indistinguishable from a no-op or a state reset | Origin logs or config — not obtainable under ordinary permitted use |
| The exact `json-server` patch version | The service publishes no version string, and v0.17.x behaviour is stable across patches | A behavioural probe against a v0 feature that changed mid-0.17 line, run locally |
| Whether rate limiting is actually enforced at 1000, and over what window and key | Testing it means deliberately exceeding a third party's published limit — out of scope without authorization | The maintainer's own configuration, or authorization to load-test |
| Dyno count, region, and plan tier | Heroku exposes none of this through the router; Cloudflare normalises the rest | Heroku-side access |
| Whether the middleware wrapper is public code | Not searched — the wrapper is inferred from header deltas, not from a named repo | Searching typicode's public repositories for the deploy wrapper |

## 8. Where to go deeper

The site's own `/guide/` is accurate but covers roughly a third of what the API does — trust it,
and treat the `json-server` v0.17 README as the real reference for everything else; I verified the
behaviours above against it directly rather than from memory. The "© 2024" footer is the only
misleading signal on the site, and it is cosmetic. A Full teardown would add almost nothing here:
this is a small, honest, single-purpose system, and the two things a Full pass could still settle
— the image host's global status and the write-simulation mechanism — are one extra network
vantage point and one thing you cannot see from outside at all.
