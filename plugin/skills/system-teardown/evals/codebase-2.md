# Run `codebase-2` — raw output

| | |
|---|---|
| Target type | codebase |
| Target / pin | ~/aifreshdaily-next @ 038e016ad671e765dae6a8a6909bd7a5e52dc07c (Next.js 15 App Router + Supabase) |
| Verdict | **PASS** |
| session_id | `58e3bab1-d3ba-4bdc-b05e-bf7f1a69d926` |
| Turns | 69 |
| Cost (USD) | 4.83 |
| is_error | False |
| Deliverable | aifreshdaily-next-as-built.md |
| Deliverable words | 8698 |

**Grade:** P1 sections PASS · P2 ledger PASS · P3 unknowns PASS · P4 deviations-out-loud PASS → **PASS**

**Reason:** escalated to FULL and named the cue ("onboard a developer next week"); all 16 as-built sections incl. 16a; ledger 12+3+0=15 correct; capability gaps tabulated (no service-role Supabase access) rather than papered over

## Prompt given (verbatim)

```
Use the system-teardown skill.

I own the Next.js project at /Users/buda007/aifreshdaily-next. I inherited it, there is no design doc, and I need to onboard a developer onto it next week. Help them understand how this codebase works.

Write any output file into the current working directory and tell me the path.
```

## Agent stdout (verbatim)

```
**Output:** `/private/tmp/claude-501/-Users-buda007--claude-skills/c1fe6555-a560-4f4a-9571-e36f24c52787/scratchpad/td-runs/codebase-2/aifreshdaily-next-as-built.md`

**Gates**

- **Capability:** full — checkout on disk, build runs, four test suites run and hit the live DB. Missing: Supabase service-role access (MCP returned `Unauthorized`), so no true ERD or RLS listing.
- **Authorization:** your own project, own machine, onboarding handover. One line, no interrogation needed.
- **Depth: Full / as-built spec.** Cue: "onboard a developer onto it next week" is a handover someone will act on, not a passing question. The system is small enough (12k LOC, ~5.9k live) that full coverage was actually achievable.
- **Freeze:** commit `038e016a`, `main`, 2026-08-20.

**What the developer most needs to know**

1. **It's an App Router app that renders almost nothing on the server.** All 19 `sections/` are `"use client"` and fetch from Supabase in `useEffect` — from the browser, directly. The prerendered homepage contains **zero** article links (`grep -c "article/" .next/server/app/index.html` → 0). Article pages are the exception and are properly SSR'd with JSON-LD.
2. **Why:** it was ported from a client SPA in one squashed commit (`658db1c0`); a leftover comment at `Sidebar.tsx:18` still references `App.tsx`.
3. **`components/ui/` — 53 files, 6,093 LOC, 51% of the tree — is imported by nothing.** Verified for alias, relative, and dynamic imports. It drags 42 of 48 runtime dependencies with it; only 6 are reachable.
4. **The production database is the only copy of the schema.** No DDL for `articles`; `increment_view_count` exists only in the live DB. And `sprint*.test.js` run against production.
5. **`/sitemap.xml` is baked at build time** — 546 URLs frozen at deploy, on a site claiming 4-hour publishing.
6. **README is untouched create-next-app boilerplate** and points at a file that doesn't exist.

**Falsification:** Reflexion diff, 19 relations, 4 non-convergent, all 4 resolving to the same root cause. 15 inferred claims — 12 confirmed, 3 downgraded to UNCONFIRMED. The three downgrades are the RLS state on six tables, PostgREST filter-injection exploitability, and the scream test I did not run because it would modify your repo. Eight unknowns are in §16a with the exact query or command that settles each.

The one to act on before anything else is §16a item 2: a five-minute `pg_class` / `pg_policies` query telling you whether anonymous users can write to your content tables. I could not answer it without a service-role credential.
```

## Deliverable written by the run — `aifreshdaily-next-as-built.md` (verbatim)

# As-built: AI Fresh Daily (`aifreshdaily-next`)

An AI-news publishing site built on Next.js 15 App Router + Supabase, reconstructed from the
source, the git history, a production build, and the project's own test suites. Written for a
developer joining the project with no prior exposure.

---

## 0. Provenance and method

| | |
|---|---|
| **Pin** | commit `038e016ad671e765dae6a8a6909bd7a5e52dc07c`, branch `main`, clean except untracked `.next.teardown-bak/` |
| **Depth** | full |
| **Analysis date** | 2026-08-20 |
| **Environments observed** | local checkout; local production build (`next build`); the **live production Supabase project** `kcqfaghyixwfewyudcgb` read through the anon key, via the repo's own test suites |
| **Authorization basis** | user's own project, own machine, local checkout, goal = onboarding handover |

**Tools used**

| Tool | Command | What it produced |
|---|---|---|
| git | `git log --pretty=format: --name-only`, `git shortlog -sn` | churn map, authorship, history window |
| TypeScript | `npx tsc --noEmit` | zero diagnostics printed |
| Next.js 15.5.12 | `npm run build` | route table, static/dynamic classification, prerendered HTML |
| Node 24 | `node sprint4.test.js` … `sprint7.test.js` | 136/136 passing, incl. 16+ live-DB assertions |
| python3 | ad-hoc import-graph extractor over 112 `.ts`/`.tsx` files | module dependency edges (§5) |
| grep/ripgrep | table, RPC, env-var, href, `"use client"` sweeps | inventories in §3, §7, §8a |

**What was NOT examined, and why**

- `components/ui/` (53 files, 6,093 LOC) was scanned for imports but not read. §11b establishes it
  is unreachable from live code, so reading it would not inform the reader.
- `node_modules/`, `.next/` (except as build evidence), `public/` — exclusion manifest.
- No browser session was driven; no Vercel dashboard, logs, or analytics were consulted.

**Capability gaps and what they cost you**

| Gap | Cost to the reader |
|---|---|
| No Supabase **admin/service-role** access — the MCP server returned `Unauthorized` for `list_tables`, `execute_sql`, and `get_advisors` | No true ERD from `information_schema`; no RLS policy listing; no index inventory. The schema in §8a is reconstructed from client code + observed query success, not read from the database. **This is the single largest unknown in this document** (§16a). |
| No production runtime access (Vercel logs, real traffic) | Latency and error-rate figures in §10 are absent, not estimated. |
| No access to whatever writes the `articles` table | The content ingestion pipeline is out of scope and undocumented (§16a). |

---

## 0.1 Falsification ledger

```
FALSIFICATION LEDGER
Target: codebase   Depth: full
Method: Reflexion Model diff (Murphy/Notkin/Sullivan) — hypothesized box-and-arrow model vs
        extracted import facts — plus dynamic corroboration from a production build and
        four live test-suite runs.

Inferred claims (one row each — this list IS N):
  C1   Despite being an App Router app, essentially all content rendering is client-side;
       the homepage ships an empty shell.
       → CONFIRMED   evidence: §5 diff (18 app→sections edges, all targets "use client") +
                     §6 Scenario A — prerendered .next/server/app/index.html contains
                     0 occurrences of "article/"
  C2   components/ui/ (53 files, 6,093 LOC) is unreferenced dead code.
       → CONFIRMED   evidence: §5 diff rows R9/R10 (absence) + §11b register
  C3   Only 6 of 48 runtime dependencies are reachable from live code.
       → CONFIRMED   evidence: §4 stack table, "reachable" column
  C4   The codebase began as a client-side SPA (react-router / App.tsx) and was ported to
       Next.js App Router in one squashed commit; the client-everything shape is inherited,
       not chosen.
       → CONFIRMED   evidence: §4a row 2 — components/Sidebar.tsx:18 "matching App.tsx router"
                     + commit 658db1c0 "migrate to Next.js 15 App Router with SSR + SEO"
  C5   sitemap.xml is frozen at build time and omits articles published since the last deploy.
       → CONFIRMED   evidence: §10 row S1 — build marks /sitemap.xml as ○ (Static);
                     .next/server/app/sitemap.xml.body written at build with 546 <loc> entries
  C6   The repository cannot recreate the database from scratch.
       → CONFIRMED   evidence: §8a migration-state table — increment_view_count is called by
                     lib/supabase.ts:302 and exercised live by sprint4.test.js:99, but no DDL
                     for it (or for any table) exists in the repo
  C7   The test suites overwhelmingly assert on source text, not behavior.
       → CONFIRMED   evidence: §11a — 83 of 99 machine-classified tests (sprint5–7) read a
                     source file and assert a substring; only 16 touch the database
  C8   Content ingestion happens outside this repository; the app is read-only against
       `articles`.
       → CONFIRMED   evidence: §3 egress table + zero .insert/.update/.upsert/.delete calls
                     across app/, sections/, components/, lib/, hooks/
  C9   Anonymous callers can write to public tables because RLS is not enabled outside
       `newsletter_subscribers`.
       → UNCONFIRMED evidence: only newsletter_subscribers has `enable row level security`
                     in repo SQL (sprint7_migrations.sql:15); the other six tables' RLS state
                     is unreadable without service-role access. Filed to §16a with the exact
                     query that settles it. Treat as a live security question, not a finding.
  C10  User search input is interpolated unescaped into a PostgREST filter string, permitting
       filter manipulation.
       → UNCONFIRMED evidence: the code shape is OBSERVED at components/SearchOverlay.tsx:128
                     (`.or(\`headline.ilike.%${q}%,...\`)`); exploitability was NOT tested —
                     probing the live API was out of scope. §16a records the test.
  C11  The category taxonomy is duplicated across six files with no single source of truth.
       → CONFIRMED   evidence: §11 risk R3 — six independent literal lists enumerated; five
                     agree on all 8 slugs, sections/IndustryDeepDive.tsx:8 omits `learn`
  C12  Three navigation links point at routes that do not exist.
       → CONFIRMED   evidence: §11 risk R4 — /accessibility, /login, /sitemap appear in JSX
                     hrefs; none appears in the build's 14-route table (§7)
  C13  Article detail pages are the exception to C1: they ARE server-rendered with full
       metadata and JSON-LD.
       → CONFIRMED   evidence: §6 Scenario B — build marks /article/[id] as ƒ (Dynamic);
                     app/(main)/article/[id]/page.tsx awaits fetchArticleById in both
                     generateMetadata and the page body
  C14  README.md is unmodified create-next-app boilerplate and actively misdirects.
       → CONFIRMED   evidence: §4a row 1 — README says "edit app/page.tsx"; that file does
                     not exist (the homepage is app/(main)/page.tsx)
  C15  The build cannot fail on type or lint errors; type safety is unenforced in CI.
       → CONFIRMED   evidence: §11a — next.config.ts sets typescript.ignoreBuildErrors and
                     eslint.ignoreDuringBuilds; build log prints "Skipping validation of
                     types" / "Skipping linting"

  N = 15   confirmed 12 / downgraded 3 / dropped 0   (12+3+0 = 15)

Coverage denominator (countable, not chosen):
  divergences+absences resolved: 4 of 4, out of y = 19 total relations in the Reflexion diff
  (§5). All four non-convergent relations reduce to a single root cause — the unwired
  shadcn/ui install — and are explained there.

System scale examined:
  · 29 of 59 live source files read in full or substantial part; all 112 .ts/.tsx files
    machine-scanned for imports, env vars, table names, and hrefs
  · 14 of 14 routes observed in the production build; 10 of 14 page sources read
  · 7 of 7 database tables named from code; 0 of 7 introspected with admin access;
    6 of 7 confirmed anon-readable by live test execution
  · 4 of 4 test suites executed (136 assertions, 136 passing)
  · 2 of 2 SQL migration files in the repo read; DDL for the other ~5 tables does not exist
  · 17 of 17 commits reviewed (entire history)

Unresolved, filed to §16a: 8
Falsification NOT performed, and why:
  · Scream-testing (deleting components/ui on a branch and running the suite) was NOT run —
    it would modify the user's repository. §11b marks the register "not scream-tested" and
    §18a gives the command.
  · Live-API probing for C10 was NOT run — out of scope for a read-only teardown.
  · Database-level falsification (RLS, indexes, true schema) was NOT possible — no
    service-role credential. This is the gap that C9 and four §16a rows all trace back to.
```

---

## 1. Purpose and business context

AI Fresh Daily is a public, unauthenticated AI-news publication. It renders a stream of AI news
articles — headline, image, summary, key points, "why it matters", body — plus a set of
editorial widgets (model scoreboard, regulation tracker, AI timeline, stock ticker, notable
quotes) and collects newsletter signups.

- **Users** — anonymous web readers. There is no login, no user account, no session (§8).
- **Business criticality** — this *is* the product. There is no other surface.
- **Upstream** — an **unidentified content pipeline** writes the `articles` table. It is not in
  this repository (C8). The site's own metadata claims "Original articles updated every 4 hours"
  and "written by AI, verified by editors" (`app/layout.tsx:12,27`) `[OBSERVED]`, which implies
  an automated ingestion or generation job somewhere outside this checkout. Finding and
  documenting that job should be the new developer's **first** task after reading this document.
- **Downstream** — Vercel hosting, Google/Bing crawlers (sitemap + RSS + JSON-LD), and
  newsletter subscribers.
- **Decision this document informs** — how to safely make changes to a codebase with no design
  doc, one author, and six months of no commits.

---

## 2. Constraints

| Constraint | Detail | Provenance | Verdict |
|---|---|---|---|
| Runtime pinning | Next.js `^15.5.12`, React `19.2.3` (exact pin), TypeScript `5.9.3` (exact pin) | `package.json` | `[OBSERVED]` CONFIRMED |
| Install workaround | `vercel.json` forces `npm install --legacy-peer-deps` — the dependency tree does not resolve cleanly under strict peer resolution | `vercel.json:4` | `[OBSERVED]` CONFIRMED |
| Framework detection workaround | `vercel.json` exists solely to force Next.js detection (commit `4e7ed9bd`) | `vercel.json`, git log | `[OBSERVED]` CONFIRMED |
| Tailwind version split | `tailwindcss ^3.4.19` as a devDependency alongside `@tailwindcss/postcss ^4` — a v3/v4 mix | `package.json` | `[OBSERVED]` CONFIRMED — fragile; see §11 R7 |
| Licensing | No LICENSE file. Private repo (`"private": true`) | repo root | `[OBSERVED]` CONFIRMED |
| Single-author history | 17 commits, all by `webdevcom01`, all on 2026-02-20/21. **No commits in the six months since.** | `git shortlog -sn`, `git log` | `[OBSERVED]` CONFIRMED |

---

## 3. Context and scope

### C4 Level 1 — System Context

```mermaid
graph LR
  Reader["Anonymous reader<br/>(browser)"]
  Crawler["Search crawlers /<br/>RSS readers"]
  Pipeline["❓ Content pipeline<br/>(NOT in this repo)"]
  App["AI Fresh Daily<br/>Next.js 15 on Vercel"]
  DB[("Supabase Postgres<br/>kcqfaghyixwfewyudcgb")]
  Img["Unsplash / Pexels /<br/>Google favicons"]

  Reader -->|HTTPS, no auth| App
  Reader -.->|"PostgREST, anon key,<br/>DIRECT from the browser"| DB
  Crawler -->|/sitemap.xml, /feed.xml, /robots.txt| App
  App -->|"PostgREST, anon key<br/>(SSR paths only)"| DB
  Pipeline ==>|"writes articles<br/>❓ unknown mechanism"| DB
  App -->|next/image remote patterns| Img
```

The dotted arrow is the one that surprises people: **the reader's browser talks to Supabase
directly.** For most of the site, the Next.js server is a static file host, not a data layer
(C1).

### External interface inventory

| Direction | Interface | Protocol | Auth | Data classification | Owner | Criticality | Provenance | Verdict |
|---|---|---|---|---|---|---|---|---|
| In | `/` and 13 other routes | HTTPS | none | public | this repo | critical | `[OBSERVED]` build route table | CONFIRMED |
| In | `/feed.xml` | HTTPS/RSS 2.0 | none | public | `app/feed.xml/route.ts` | medium | `[OBSERVED]` | CONFIRMED |
| In | `/sitemap.xml`, `/robots.txt` | HTTPS | none | public | `app/sitemap.ts`, `app/robots.ts` | high (SEO) | `[OBSERVED]` | CONFIRMED |
| Out | Supabase PostgREST — 6 tables, read | HTTPS | anon JWT (public) | public content | Supabase | critical | `[OBSERVED]` `.from()` sweep | CONFIRMED |
| Out | Supabase RPC — 4 `SECURITY DEFINER` functions | HTTPS | anon JWT | mixed; `subscribe_email` handles **PII (email)** | Supabase | high | `[OBSERVED]` `.rpc()` sweep | CONFIRMED |
| Out | Remote images: `images.unsplash.com`, `source.unsplash.com`, `images.pexels.com`, `**.supabase.co`, `www.google.com`, `**.githubusercontent.com` | HTTPS | none | public | third parties | low | `[OBSERVED]` `next.config.ts:8-16` | CONFIRMED |
| **Absent** | Any write path to `articles` | — | — | — | **unknown** | **critical** | `[OBSERVED]` zero insert/update/upsert | CONFIRMED (C8) |

### Config surface

| Key | Default in code | Consumers | Blast radius |
|---|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `'https://placeholder.supabase.co'` | `lib/supabase.ts:5`, `app/feed.xml/route.ts:30`, `app/(main)/analytics/page.tsx:37` | total — every piece of content |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `'placeholder-key'` | same three | total |

Those are the **only two** environment variables in the entire codebase `[TOOL]` (grep for
`process.env` across all non-build sources) CONFIRMED.

Both are `NEXT_PUBLIC_`, i.e. **compiled into the client bundle and publicly visible**. That is
normal and intended for a Supabase anon key — it is a public identifier, not a secret — but it
means *all* database security rests on Postgres row-level security and grants, not on hiding the
key. See C9 / §16a.

> **Note on the placeholder fallbacks** (`lib/supabase.ts:5-8`): these were added deliberately
> (commit `bf093339`, "safe supabase client init … to prevent build crash"). The consequence is
> that a **misconfigured deploy builds and serves successfully but shows no content** — the
> failure is silent. See §11 R6.

---

## 4. Solution strategy

**The design as evidenced:** a component-per-section marketing-style news site, where each
visual section is an independent client component that mounts, fires its own Supabase query in
`useEffect`, renders a skeleton while waiting, and degrades to empty or to hardcoded fallback
data on error. Next.js App Router provides routing, metadata, and three server-rendered SEO
endpoints; it provides almost no data rendering (C1).

There is no service layer beyond `lib/supabase.ts`, no state management library, no API layer of
the project's own, and no caching layer.

### Technology stack inventory

| Package | Version | Reachable from live code? | Role |
|---|---|---|---|
| `next` | ^15.5.12 | ✅ | framework, App Router |
| `react` / `react-dom` | 19.2.3 (pinned) | ✅ | UI runtime |
| `@supabase/supabase-js` | ^2.97.0 | ✅ | the entire data layer |
| `lucide-react` | ^0.575.0 | ✅ | every icon in the app |
| `next-themes` | ^0.4.6 | ✅ | dark mode (`components/ThemeProvider.tsx`) |
| `tailwindcss` | ^3.4.19 (+ `@tailwindcss/postcss ^4`) | ✅ | all styling |
| `clsx` + `tailwind-merge` | — | ⚠️ only via `lib/utils.ts` `cn()`, which is imported **only by `components/ui/`** | dead in practice |
| 26 × `@radix-ui/*`, `recharts`, `cmdk`, `vaul`, `embla-carousel-react`, `react-hook-form`, `@hookform/resolvers`, `zod`, `date-fns`, `input-otp`, `react-day-picker`, `react-resizable-panels`, `sonner`, `class-variance-authority`, `tailwindcss-animate` | — | ❌ **none** | pulled in by the unwired shadcn/ui install (C2/C3) |

`[TOOL]` — external-import sweep over `app/`, `sections/`, `components/` (excluding `ui/`),
`hooks/`, `lib/`. **6 of 48 runtime dependencies are reachable.** CONFIRMED (C3).

### 4a. Documentation divergence

This is the highest-value section for anyone inheriting this repo. Verdicts are MISLEADING —
each describes something real but gets a material fact wrong.

| Artifact | What it gets right | What it gets wrong | Verdict |
|---|---|---|---|
| `README.md` | It is a Next.js project; `npm run dev` on :3000 is correct | Everything else is unmodified `create-next-app` boilerplate. It tells you to "start editing `app/page.tsx`" — **that file does not exist.** The homepage is `app/(main)/page.tsx`. It says the project uses `next/font` and Geist — it does not; fonts come from `app/globals.css` + `tailwind.config.ts`. It mentions nothing about Supabase, which is the entire data layer. | MISLEADING (C14) |
| `components/Sidebar.tsx:18-21` | Correctly describes the nav→`/category/:slug` mapping still in force | Says routes match "**App.tsx router**" — there is no `App.tsx`; that is a leftover from the pre-migration client SPA. Also promises "sub-category filtering (Phase 2)" that was never built — sub-category links still go to `/tag/*`, not filtered category views. This comment is the main surviving evidence for C4. | MISLEADING |
| Sprint test names, e.g. `sprint7.test.js` "analytics page is a Server Component" | The assertion is literally true | These read as behavioral guarantees but are `readFileSync` + `String.includes` checks. "StockTicker clears interval on unmount (memory leak!)" passes if the *string* `clearInterval` appears anywhere in the file. See §11a (C7). | MISLEADING |
| `sprint6_migrations.sql` / `sprint7_migrations.sql` headers ("Run in Supabase Dashboard → SQL Editor") | Accurately describes the actual deployment process | Implies the repo's SQL is the schema of record. It is not — it covers only sprints 6 and 7. The `articles` table itself, `increment_view_count`, and four other tables have no DDL anywhere in the repo (C6). | MISLEADING |
| `app/robots.ts:8` disallows `/bookmarks`, `/login`, `/api/` | `/bookmarks` is real and correctly excluded | `/login` and `/api/` do not exist — vestigial from the SPA era | MISLEADING |

---

## 5. Building block view

### C4 L2 / L3 — containers and components

```mermaid
graph TD
  subgraph Vercel["Vercel — Next.js 15 runtime"]
    RootLayout["app/layout.tsx<br/>(server) — metadata, ThemeProvider"]
    MainLayout["app/(main)/layout.tsx<br/>⚠️ 'use client' — chrome + scroll-to-top"]
    Pages["14 routes<br/>10 static ○ / 4 dynamic ƒ"]
    SEO["app/sitemap.ts · robots.ts · feed.xml/route.ts<br/>(server-only, the real SSR)"]
  end
  subgraph Browser["Browser bundle"]
    Sections["sections/ — 19 files, 2,531 LOC<br/>ALL 'use client'"]
    Comps["components/ — 11 files<br/>ALL 'use client'"]
    Hooks["hooks/ — useBookmarks, use-mobile,<br/>useIntersectionObserver"]
  end
  Lib["lib/supabase.ts — 346 LOC<br/>THE data layer: 15 fetchers + 4 RPC wrappers"]
  UI["components/ui/ — 53 files, 6,093 LOC<br/>💀 UNREFERENCED (C2)"]
  DB[("Supabase")]

  RootLayout --> MainLayout --> Pages
  Pages --> Sections
  Sections --> Comps
  Sections --> Lib
  Pages --> Lib
  Comps --> Lib
  Comps --> Hooks
  SEO --> Lib
  Lib --> DB
  Sections -.->|"browser fetch"| DB
  UI -.->|"lib/utils cn() only"| Lib
```

### Module dependency facts

`[TOOL]` — import-graph extraction over all 112 `.ts`/`.tsx` files, `@/`-alias edges, counted:

| From | To | Edges |
|---|---|---|
| `components/ui` | `lib` | 50 |
| `components/ui` | `components/ui` | 20 |
| `app` | `sections` | 18 |
| `sections` | `lib` | 16 |
| `sections` | `types` | 12 |
| `app` | `lib` | 7 |
| `app` | `hooks` | 4 |
| `app` | `types` | 4 |
| `sections` | `components` | 3 |
| `app` | `components` | 2 |
| `components` | `types` | 2 |
| `components` | `hooks` | 1 |
| `components` | `lib` | 1 |
| `components/ui` | `hooks` | 1 |
| `lib` | `types` | 1 |

**Cycles: none.** **Layering violations: none among live modules** — `lib` imports only `types`;
nothing imports upward. Two files matched no box (`next.config.ts`, `tailwind.config.ts`) and
are correctly outside the model.

### Reflexion diff — the falsification evidence for this section

Hypothesized model drawn from directory structure and domain vocabulary before extraction.
19 relations predicted; each checked against the extracted facts.

| Relation | Predicted | Present in code | Verdict | Explanation |
|---|---|---|---|---|
| R1 `app` → `sections` | yes | yes (18) | convergence | — |
| R2 `app` → `components` | yes | yes (2) | convergence | — |
| R3 `app` → `lib` | yes | yes (7) | convergence | — |
| R4 `app` → `hooks` | yes | yes (4) | convergence | — |
| R5 `app` → `types` | yes | yes (4) | convergence | — |
| R6 `sections` → `components` | yes | yes (3) | convergence | — |
| R7 `sections` → `lib` | yes | yes (16) | convergence | — |
| R8 `sections` → `types` | yes | yes (12) | convergence | — |
| R9 `sections` → `components/ui` | yes | **no (0)** | **absence** | shadcn/ui was installed but never adopted; sections hand-roll their markup with raw Tailwind |
| R10 `components` → `components/ui` | yes | **no (0)** | **absence** | same root cause as R9 |
| R11 `components` → `lib` | yes | yes (1) | convergence | `SearchOverlay` only |
| R12 `components` → `hooks` | yes | yes (1) | convergence | — |
| R13 `components` → `types` | yes | yes (2) | convergence | — |
| R14 `lib` → `types` | yes | yes (1) | convergence | — |
| R15 `lib` → `sections`/`components` (upward) | no | no | convergence | clean layering confirmed |
| R16 `components/ui` → `lib` | no (leaf) | **yes (50)** | **divergence** | every shadcn primitive imports `cn()` from `lib/utils.ts`; `lib/utils.ts` has **no other consumer** |
| R17 `components/ui` → `hooks` | no (leaf) | **yes (1)** | **divergence** | `use-mobile` — same root cause |
| R18 `components/ui` → `components/ui` | yes | yes (20) | convergence | — |
| R19 `lib` → Supabase SDK | yes | yes | convergence | — |

**All 4 non-convergent relations (R9, R10, R16, R17) reduce to one finding:** a complete
shadcn/ui component library sits in the tree, wired only to itself and to `cn()`, and is imported
by nothing the application renders. Resolved 4 of 4; carried forward as C2 and into §11b.

*This table is corroborated by dynamic observation (a production build and four live test-suite
runs), not static-only.*

---

## 6. Runtime view

### Scenario A — a reader loads the homepage **(traced)**

```mermaid
sequenceDiagram
  participant B as Browser
  participant V as Vercel (static HTML)
  participant S as Supabase (PostgREST)
  B->>V: GET /
  V-->>B: prerendered shell — nav, section headings,<br/>skeletons, FALLBACK stock tickers. ZERO articles.
  B->>B: hydrate ~171 kB JS
  Note over B,S: 14 sections each fire their own query, in parallel, from the browser
  B->>S: articles ORDER BY published_at LIMIT 6      (LatestNews)
  B->>S: articles WHERE is_featured LIMIT 3          (FeaturedSection)
  B->>S: articles WHERE is_breaking LIMIT 5          (BreakingNews)
  B->>S: articles ORDER BY view_count LIMIT 5        (MostPopular)
  B->>S: articles WHERE image NOT NULL AND (…) LIMIT 3 (HeroSection)
  B->>S: articles WHERE category='learn' / 'tools'   (GreatReads, CodingSection)
  B->>S: articles WHERE is_video LIMIT 6             (VideosSection)
  B->>S: articles RANGE 0..11                        (IndustryDeepDive)
  B->>S: articles SELECT tags LIMIT 200              (TrendingTopics — counts client-side)
  B->>S: model_scores / regulations / timeline_events / ai_voices / stock_tickers
  B->>S: rpc get_newsletter_stats                    (NewsletterSection)
  S-->>B: JSON ×~15
  B->>B: setState → first article paint
  loop every 60 s
    B->>S: stock_tickers (StockTicker REFRESH_MS)
  end
```

**Evidence for "ZERO articles":** `grep -c "article/" .next/server/app/index.html` → **0**.
The prerendered HTML's visible text is chrome only — nav labels, section headings ("Latest AI
News", "Most Read", "Regulation Tracker"), the footer link farm, and the nine hardcoded
`FALLBACK_TICKERS` from `sections/StockTicker.tsx:14-24` `[OBSERVED]` CONFIRMED (C1).

**~15 uncoordinated round trips, all from the browser, all uncached, on every cold homepage
load.** No request deduplication, no shared cache, no `Promise.all`. This is the defining
performance and SEO characteristic of the site.

### Scenario B — a reader opens an article **(traced)**

```mermaid
sequenceDiagram
  participant B as Browser
  participant N as Next.js server (ƒ dynamic)
  participant S as Supabase
  B->>N: GET /article/:id
  N->>S: fetchArticleById(id)   ← call 1, from generateMetadata
  N->>S: fetchArticleById(id)   ← call 2, from the page body
  N-->>B: full HTML + OG/Twitter tags + NewsArticle JSON-LD +<br/>article passed to ArticleClient as initialArticle
  B->>B: hydrate; ArticleClient skips its fetch (initialArticle present)
  B->>S: fetchRelatedByTags(tags, id, category) — overlaps(), falls back to same-category
  B->>S: rpc increment_view_count(id)
```

**This route is the exception to C1** (C13) — it is genuinely server-rendered, with correct
canonical URL, Open Graph, Twitter card, and `schema.org/NewsArticle` JSON-LD. Article pages are
SEO-sound; the homepage and category/tag pages are not.

Note the **duplicate `fetchArticleById`** at `app/(main)/article/[id]/page.tsx:12` and `:74` —
two identical uncached round trips per request. Supabase-js is not wrapped in React `cache()`, so
Next.js does not dedupe it `[INFERRED]` — the double call itself is `[OBSERVED]`.

### Scenario C — newsletter signup **(traced, live)**

`NewsletterSection` or `/subscribe` → `subscribeEmail()` → `rpc('subscribe_email')`, a
`SECURITY DEFINER` function that regex-validates the address and upserts into
`newsletter_subscribers` (RLS on, no anon SELECT policy). Returns `{success:true}` or
`{success:false, error:'invalid_email'}`. The client then writes
`localStorage['ai_fresh_daily_subscribed'] = 'true'` and optimistically bumps the displayed
subscriber count. `[OBSERVED]` `sprint7_migrations.sql`, `lib/supabase.ts:246-259`; the RPC path
is exercised live by `sprint7.test.js` CONFIRMED.

**This is the correct pattern in this codebase** — a locked-down table plus a narrow
`SECURITY DEFINER` RPC. Copy it for any new write path.

### Error and retry paths

- `app/(main)/error.tsx` and `app/(main)/article/[id]/error.tsx` — React error boundaries with a
  `reset()` button and the Next.js error `digest` shown to the user `[OBSERVED]`.
- **Every section swallows its own failures.** The dominant idiom is
  `.catch(() => {})` or `if (!error && data) setState(...)`. A Supabase outage therefore renders
  as a *silently empty page*, not an error boundary `[OBSERVED]` across `sections/` CONFIRMED.
- Three deliberate fallbacks: `StockTicker` → hardcoded tickers; `fetchMostPopular` → recency
  sort if `view_count` is missing; `fetchRelatedByTags` → same-category if no tag overlap.

---

## 7. Deployment view

| | |
|---|---|
| Platform | Vercel (`vercel.json`, framework `nextjs`) `[OBSERVED]` |
| Build | `npm run build` → `next build`; install `npm install --legacy-peer-deps` |
| Environments | one production Supabase project (`kcqfaghyixwfewyudcgb`). **No staging, no dev database** was found `[INFERRED]` from a single URL across all config and test files — UNCONFIRMED, see §16a |
| Database migration | manual — paste `sprint*_migrations.sql` into the Supabase Dashboard SQL Editor `[OBSERVED]` from the file headers |
| CI/CD | **none in the repo** — no `.github/`, no pipeline config. Deploys are Vercel's git integration `[OBSERVED]` |
| Rollback | Vercel deployment rollback only. **Database changes have no rollback** — the SQL files are forward-only and `create or replace` |

### Route table `[TOOL]` — `next build` output at the pinned SHA

| Route | Rendering | First Load JS | Note |
|---|---|---|---|
| `/` | ○ Static | 171 kB | empty shell; content client-side |
| `/analytics` | ○ Static + ISR 300 s | 102 kB | the only true server-data page |
| `/article/[id]` | ƒ Dynamic | 162 kB | full SSR + JSON-LD |
| `/category/[slug]` | ƒ Dynamic | 162 kB | server shell only; data client-side |
| `/tag/[slug]` | ƒ Dynamic | 161 kB | same |
| `/feed.xml` | ƒ Dynamic | — | RSS, `s-maxage=3600` |
| `/bookmarks`, `/subscribe` | ○ Static | ~160 kB | localStorage-driven |
| `/cookies`, `/privacy`, `/terms` | ○ Static | ~106 kB | legal copy |
| `/sitemap.xml`, `/robots.txt` | ○ Static | — | **⚠️ sitemap frozen at build (C5)** |
| `/_not-found` | ○ Static | 103 kB | |

14 routes. Shared baseline 102 kB.

> Build warning worth fixing: Next.js inferred the workspace root as `/Users/buda007` because a
> stray `package-lock.json` sits in the home directory. Harmless locally, confusing on a new
> machine.

---

## 8. Crosscutting concepts

| Concern | As-built | Provenance | Verdict |
|---|---|---|---|
| **Authentication** | **None.** No login, no session, no user table, no auth SDK usage. A "Log in" link exists in the header and points at `/login`, which does not exist | `[OBSERVED]` | CONFIRMED |
| **Authorization** | Entirely delegated to Postgres: the public anon key + grants + (unverified) RLS. Four `SECURITY DEFINER` RPCs are the only privileged paths | `[OBSERVED]` / C9 | CONFIRMED / UNCONFIRMED |
| **Client state** | React `useState` per component. No Redux/Zustand/Context beyond `ThemeProvider`. Cross-component state does not exist | `[OBSERVED]` | CONFIRMED |
| **Persistent client state** | `localStorage`, three keys: `ai-pulse-bookmarks` (note the **stale product name**), `ai-freshdaily-recent-searches`, `ai_fresh_daily_subscribed`. Also `next-themes` writes `theme` | `[OBSERVED]` `hooks/useBookmarks.ts:4`, `components/SearchOverlay.tsx:9`, `app/(main)/subscribe/page.tsx:31` | CONFIRMED |
| **Error handling** | Two error boundaries; otherwise silent swallow (§6) | `[OBSERVED]` | CONFIRMED |
| **Logging / observability** | One `console.error` in `app/(main)/error.tsx:15`. **No Sentry, no analytics, no OTel, no structured logging anywhere** | `[TOOL]` grep | CONFIRMED |
| **Caching** | `/analytics` ISR 300 s; `/feed.xml` `s-maxage=3600`. Everything else uncached — every client query hits Postgres | `[OBSERVED]` | CONFIRMED |
| **Transactions** | None. All writes are single-statement RPCs | `[OBSERVED]` | CONFIRMED |
| **i18n** | None. `lang="en"`, `en-US` date formatting hardcoded | `[OBSERVED]` | CONFIRMED |
| **Feature flags** | None | `[TOOL]` | CONFIRMED |
| **Secrets management** | Two `NEXT_PUBLIC_` vars only; `.env.local` locally, Vercel env vars in production. **The anon key and project URL are also hardcoded into the four committed `sprint*.test.js` files.** The anon key is public by design so this is not a leak, but it means rotating the project pins four source files | `[OBSERVED]` `sprint7.test.js:13-14` | CONFIRMED |
| **Design tokens** | HSL CSS variables in `app/globals.css` (shadcn convention) + an `--ai-*` brand palette (`#6C3CE1` purple, `#00D4FF` cyan) + Tailwind `ai-*` utilities. Dark mode is the **default** and system preference is disabled (`app/layout.tsx:44-46`) | `[OBSERVED]` | CONFIRMED |

### 8a. Data architecture

> **Reconstructed from client code and confirmed-successful live queries — NOT read from
> `information_schema`.** No service-role credential was available (§0). Column lists are the
> columns the application *uses*; the real tables may have more. Types are inferred from the
> TypeScript row interfaces.

```mermaid
erDiagram
  articles {
    text id PK
    text headline
    text excerpt
    text summary
    text body
    text image
    text category
    text author
    text read_time
    timestamptz published_at
    text original_url
    bool is_exclusive
    bool is_featured
    bool is_breaking
    bool is_video "❓ used by fetchVideoArticles, untested"
    text source_name
    text source_url
    text source_favicon
    text_array key_points
    text why_it_matters
    text_array tags
    int word_count
    int view_count
  }
  model_scores {
    int id PK
    text name
    text company
    numeric score_overall
    numeric score_coding
    numeric score_reasoning
    numeric score_creative
    int vote_count
    text context_window
    text highlight
  }
  regulations {
    int id PK
    text title
    text region
    text status
    text impact
    date deadline
    text description
    text source_url
    int sort_order
  }
  timeline_events {
    int id PK
    text year
    text quarter
    text title
    text description
    text type
    int sort_order
  }
  ai_voices {
    int id PK
    text name
    text title
    text company
    text avatar
    text quote
    text article_link
    int sort_order
  }
  stock_tickers {
    int id PK
    text symbol
    text name
    numeric change_pct
    text type
    timestamptz updated_at
  }
  newsletter_subscribers {
    bigint id PK
    text email UK "PII"
    timestamptz subscribed_at
    bool is_active
  }
```

**There are no foreign keys between these tables.** `articles` is joined to nothing; the
"related articles" feature works by Postgres array overlap on `tags`, not by a relation
`[OBSERVED]` `lib/supabase.ts:307-336`.

#### Table ownership and shared-state coupling

Import graphs cannot show these edges. This table can.

| Table | Read by | Written by | Coupling note |
|---|---|---|---|
| `articles` | 20 call sites across `lib/supabase.ts`, `SearchOverlay`, `analytics`, `feed.xml`, `sitemap` — **the hub of the entire system** | ❓ **an external pipeline** (C8); plus `increment_view_count` RPC bumps `view_count` | Any schema change here breaks up to 20 call sites and the RSS feed. `view_count` is written by readers and read by `MostPopular` + `/analytics` — a genuine shared-state edge |
| `model_scores` | `ModelScoreboard`, `/analytics` | `vote_for_model` RPC | `vote_count` is a shared counter; **votes are unauthenticated and unthrottled**, and the client also keeps a parallel localStorage tally (`ModelScoreboard`) |
| `stock_tickers` | `StockTicker` (polled every 60 s), `sprint4/7` tests | ❓ external | if nothing updates it, the ticker shows stale data with a "Xm ago" label |
| `regulations`, `timeline_events`, `ai_voices` | one section each | ❓ external / manual | editorial reference data |
| `newsletter_subscribers` | `get_newsletter_stats` RPC only (RLS blocks anon SELECT) | `subscribe_email` RPC | **PII**. The only table with confirmed RLS |

#### Database functions (all `SECURITY DEFINER`, granted to `anon`)

| Function | Purpose | DDL in repo? |
|---|---|---|
| `subscribe_email(p_email text) → jsonb` | regex-validate + upsert subscriber | ✅ `sprint7_migrations.sql:20` |
| `get_newsletter_stats() → table(total_subscribers bigint)` | count active subscribers | ✅ `sprint7_migrations.sql:44` |
| `vote_for_model(p_model_id int) → void` | `vote_count = vote_count + 1` | ✅ `sprint6_migrations.sql:15` |
| `increment_view_count(article_id) → ?` | bump `articles.view_count` | ❌ **exists only in the live database** |

#### Migration state — C6

| Object | DDL in repo | Exists in live DB |
|---|---|---|
| `articles` and all its columns | ❌ none | ✅ (486 rows at build time, §10) |
| `model_scores`, `regulations`, `timeline_events`, `ai_voices`, `stock_tickers` | ❌ none | ✅ queried successfully by the test suites |
| `model_scores.vote_count` + `vote_for_model` | ✅ sprint 6 | ✅ |
| `newsletter_subscribers` + 2 RPCs | ✅ sprint 7 | ✅ |
| `articles.view_count` | ❌ none | ✅ |
| `increment_view_count` | ❌ **none** | ✅ — called at `lib/supabase.ts:302`, exercised live at `sprint4.test.js:99`, passing |

**You cannot stand up a second environment from this repository.** There is no
`supabase/migrations/` directory, no `schema.sql`, no ORM. The production database is the only
copy of the schema. Fixing this is §11 R1.

#### PII inventory

`newsletter_subscribers.email` is the only PII in the system. It is protected by RLS with no anon
SELECT policy and is reachable only through `SECURITY DEFINER` functions — the aggregate RPC
returns a count, never addresses `[OBSERVED]` CONFIRMED. There is no documented retention policy,
no unsubscribe endpoint (`is_active` exists but nothing flips it to false), and no export path.

---

## 9. Architectural decisions (retroactive, reconstructed)

### ADR-001 — Supabase PostgREST called directly from the browser, with no backend of our own

- **Status:** `Accepted (retroactive — reconstructed)`
- **Context:** the project needed a data layer fast; content is entirely public; there is no
  authentication requirement.
- **Decision:** ship the public anon key to the client and let each component query PostgREST
  directly. `lib/supabase.ts` is a thin typed wrapper, not a service boundary. No API routes
  exist except the RSS feed.
- **Consequences:** zero backend to operate; **but** all authorization lives in Postgres grants
  and RLS (C9), every schema change is a breaking client change, there is no request
  coalescing or caching layer, and query shapes are visible to anyone reading the bundle.
- **Evidence:** `lib/supabase.ts:5-10@038e016a`; 24 import sites; zero files under `app/api/`.
- **Verdict:** CONFIRMED

### ADR-002 — Client-side rendering retained after the App Router migration

- **Status:** `Accepted (retroactive — reconstructed)`
- **Context:** commit `658db1c0` "migrate to Next.js 15 App Router with SSR + SEO" ported an
  existing client SPA. Converting 19 sections to Server Components would have been a rewrite.
- **Decision:** wrap the ported components in App Router routing and mark
  `app/(main)/layout.tsx` `"use client"`. Recover SEO selectively — via `generateMetadata` +
  JSON-LD on article pages, `sitemap.ts`, `robots.ts`, and `feed.xml` — rather than by moving
  data fetching to the server.
- **Consequences:** article pages are SEO-sound (C13); the homepage, category and tag pages
  render empty to a crawler that does not execute JavaScript (C1). ~15 uncoordinated client
  round trips per homepage load. The entire `sections/` layer ships to the browser.
- **Evidence:** `app/(main)/layout.tsx:1@038e016a`; all 19 `sections/*.tsx` begin `"use client"`;
  `components/Sidebar.tsx:18` "matching App.tsx router"; prerendered `index.html` with 0 article
  links.
- **Verdict:** CONFIRMED (this is C1 + C4)

### ADR-003 — Privileged writes via `SECURITY DEFINER` RPCs instead of table grants

- **Status:** `Accepted (retroactive — reconstructed)`
- **Context:** anonymous users must be able to subscribe, vote, and increment view counts without
  being granted write access to any table.
- **Decision:** lock the table (or leave it read-only to anon) and expose one narrow
  `SECURITY DEFINER` function per operation, granted to `anon, authenticated`.
- **Consequences:** the correct pattern, and the one to follow for new writes. But the functions
  are **unthrottled and unauthenticated** — `vote_for_model` and `increment_view_count` can be
  called in a loop by anyone (§11 R5).
- **Evidence:** `sprint6_migrations.sql:15-31`, `sprint7_migrations.sql:20-56`.
- **Verdict:** CONFIRMED

### ADR-004 — Type checking and linting disabled at build time

- **Status:** `Accepted (retroactive — reconstructed)` — **recommend revisiting**
- **Context:** commit `9a6036eb` "resolve all TypeScript errors in `components/ui/chart.tsx`"
  suggests the vendored shadcn/ui code fought the build.
- **Decision:** set `typescript.ignoreBuildErrors: true` and `eslint.ignoreDuringBuilds: true`.
- **Consequences:** a type error cannot fail a deploy. The good news, measured today: `npx tsc
  --noEmit` at this SHA prints **zero diagnostics**, so the escape hatch is not currently hiding
  anything. Since `components/ui/` is dead (C2), removing it likely removes the original reason
  for this setting.
- **Evidence:** `next.config.ts:4-9@038e016a`; build log "Skipping validation of types /
  Skipping linting"; `npx tsc --noEmit` clean.
- **Verdict:** CONFIRMED (C15)

---

## 10. Quality requirements — measured, not aspirational

| ID | Property | Measurement | Method | Verdict |
|---|---|---|---|---|
| Q1 | Homepage JS payload | **171 kB** First Load JS; 102 kB shared baseline | `next build` route table | `[TOOL]` CONFIRMED |
| Q2 | Homepage server-rendered article content | **0 articles**, 0 `article/` links in prerendered HTML | `grep -c` on `.next/server/app/index.html` | `[OBSERVED]` CONFIRMED (C1) |
| Q3 | Homepage client queries per cold load | **~15**, uncoordinated, uncached | source read of all 14 homepage sections + layout | `[OBSERVED]` CONFIRMED |
| Q4 | Article-page DB round trips per request | **2 server-side** (duplicate `fetchArticleById`) **+ 2 client-side** (related, view-count) | source read `app/(main)/article/[id]/` | `[OBSERVED]` CONFIRMED |
| Q5 | Corpus size | **486 articles**, 50 tag pages, 8 categories = 546 sitemap URLs | `grep -c '<loc>'` on the built sitemap | `[TOOL]` CONFIRMED |
| S1 | Sitemap freshness | **frozen at build time** — `/sitemap.xml` is ○ Static, no `revalidate` | build route table + build artifact timestamp | `[OBSERVED]` CONFIRMED (C5) |
| Q6 | Build time | ~1.4 s compile; 14/14 static pages generated | `npm run build` | `[TOOL]` CONFIRMED |
| Q7 | Type health | `npx tsc --noEmit` → **no diagnostics**, despite being disabled at build | direct run | `[TOOL]` CONFIRMED |
| Q8 | Test suite | **136 assertions, 136 passing** across 4 suites | direct run of all four | `[TOOL]` CONFIRMED |
| — | Production latency, error rate, traffic, Core Web Vitals | **not measured** — no runtime access | — | UNCONFIRMED, §16a |

### Security posture

| Item | State |
|---|---|
| Anon key exposure | Public by design; also hardcoded in four committed test files. Not a leak; a rotation-friction issue |
| RLS coverage | **Confirmed only on `newsletter_subscribers`.** Unknown on the other six tables — C9, §16a |
| PII | One field (`email`), correctly protected behind RLS + `SECURITY DEFINER` |
| Input validation | `subscribe_email` regex-validates server-side ✅. `SearchOverlay` interpolates raw user input into a PostgREST `.or()` filter string ⚠️ — C10 |
| Rate limiting | **None anywhere.** `vote_for_model` and `increment_view_count` are unauthenticated and unthrottled |
| XSS | One `dangerouslySetInnerHTML`, at `app/(main)/article/[id]/page.tsx:64`, and it renders `JSON.stringify` of a JSON-LD object — the standard safe pattern. No user-generated content is rendered anywhere |
| CSRF | Not applicable — no cookies, no sessions, no same-origin mutating endpoints |
| Dependency risk | 42 unused runtime dependencies still in the lockfile and still in the deploy's install step |

### 10a. Interfaces and contracts

The site publishes no API of its own beyond three crawler endpoints:

| Contract | Shape | Found or inferred | Compatibility guarantee |
|---|---|---|---|
| `GET /feed.xml` | RSS 2.0, 50 most recent articles, `<enclosure>` for images, `<category>` per tag, `ttl=60` | found — `app/feed.xml/route.ts` | none stated; XML is escaped by a hand-rolled `escapeXml` |
| `GET /sitemap.xml` | `MetadataRoute.Sitemap`, 546 URLs | found — `app/sitemap.ts` | none |
| `GET /robots.txt` | allow `/`, disallow `/bookmarks`, `/login`, `/api/` | found — `app/robots.ts` | none |
| JSON-LD `NewsArticle` | embedded per article page | found — `app/(main)/article/[id]/page.tsx:45-67` | schema.org |

The de-facto contract that matters most is **the shape of the `articles` table**, jointly owned
by this repo and the unidentified pipeline (C8). It is written down nowhere except
`ArticleRow` in `lib/supabase.ts:12-33`. Treat that interface as the system's real API.

---

## 11. Risks and technical debt

Ranked by blast radius × likelihood.

| ID | Risk | Blast radius | Evidence | Remediation |
|---|---|---|---|---|
| **R1** | **Schema exists only in production.** No migrations for `articles` or 5 other tables; `increment_view_count` has no DDL anywhere | Total — no staging, no rebuild, no review of schema change | C6, §8a | ~½ day: `supabase db pull` (or `pg_dump --schema-only`) into `supabase/migrations/`, commit, adopt the CLI |
| **R2** | **Sitemap frozen at build.** A news site publishing every 4 hours tells Google about articles only at deploy time | High — the site's primary acquisition channel | C5, S1 | ~1 line: add `export const revalidate = 3600` to `app/sitemap.ts` |
| **R3** | **Homepage is invisible to non-JS crawlers**; category and tag pages too | High — SEO on the highest-traffic route | C1, Q2 | Large. Convert `LatestNews`/`HeroSection`/`FeaturedSection` to Server Components fetching on the server and passing props. Article pages already show the pattern |
| **R4** | **Unverified RLS on six tables.** If RLS is off and anon holds table grants, anyone can rewrite the site's content | Catastrophic if true, zero if false — **unknown today** | C9 | 5 minutes: run the query in §16a. Do this first |
| **R5** | **Unthrottled anonymous write RPCs.** `vote_for_model`, `increment_view_count` are trivially scriptable | Medium — data integrity of votes and view counts, both shown publicly on `/analytics` | ADR-003 | Supabase rate limiting, or a per-IP/day guard inside the function |
| **R6** | **Misconfiguration fails silently.** Placeholder Supabase credentials produce a successful build and an empty site | Medium — a bad deploy looks healthy | `lib/supabase.ts:5-8` | Fail fast in production: throw when the env vars are absent and `NODE_ENV === 'production'` |
| **R7** | **6,093 LOC / 53 files of dead UI code** plus 42 unused dependencies | Medium — every reader wastes time on it; install time and supply-chain surface | C2, C3, §11b | ~1 hour: delete `components/ui/`, `lib/utils.ts`, prune `package.json`, rebuild the lockfile |
| **R8** | **Category taxonomy duplicated in six files** with no single source of truth. Currently in sync on all 8 slugs **except** `sections/IndustryDeepDive.tsx:8`, which omits `learn` | Medium — silent divergence on the next taxonomy change | C11 | ~1 hour: one `lib/taxonomy.ts` export consumed by all six |
| **R9** | **Three dead navigation links** shipped to users: `/accessibility`, `/login`, `/sitemap` (the last is a footer link; the real route is `/sitemap.xml`) | Low but user-visible 404s | C12 | Minutes: fix or remove |
| **R10** | **Tests do not test behavior** — 83 of 99 classified assertions are substring checks against source files | High, and deceptive: "136/136 passing" reads as safety it does not provide | C7, §11a | Adopt Vitest + Playwright for the flows in §6; keep the 16 live-DB checks as smoke tests |
| **R11** | **Type/lint enforcement disabled at build** | Medium — currently clean (Q7), so cheap to re-enable now | C15, ADR-004 | Delete the two `ignore*` flags in `next.config.ts` after R7 |
| **R12** | Unescaped user input in a PostgREST `.or()` filter | Unknown — code shape confirmed, exploitability untested | C10 | Escape or drop the `.or()` fallback; the `textSearch` primary path is already parameterized |
| **R13** | **Bus factor 1, and the bus already left.** One author, 17 commits, all on two days in Feb 2026, none since | High — organizational | git history | This document is step one |
| **R14** | Tailwind v3 + `@tailwindcss/postcss` v4 in the same tree; `--legacy-peer-deps` required to install | Low today, blocks upgrades | §2 | Pick one Tailwind major |
| **R15** | `articles.is_video` is queried by `fetchVideoArticles` but appears in no test and no migration. If the column is absent, `VideosSection` silently renders nothing | Low — one section | `lib/supabase.ts:87`, `sections/VideosSection.tsx:19-21` | Confirm the column exists; add a smoke test |

### 11a. Build, release, operate

**From a clean checkout:**

```bash
git clone <repo> && cd aifreshdaily-next
npm install --legacy-peer-deps          # plain `npm install` will fail on peer deps
cp .env.local.example .env.local        # then fill in the two NEXT_PUBLIC_SUPABASE_* values
npm run dev                             # http://localhost:3000
npm run build                           # production build
node sprint4.test.js                    # …and sprint5/6/7 — these hit the LIVE production DB
```

⚠️ **The test suites read and write the production database.** `sprint4.test.js` calls
`increment_view_count` against a real article. There is no test database.

**Test strategy, measured `[TOOL]`:**

| Suite | Assertions | Source-text checks | Live-DB checks |
|---|---|---|---|
| `sprint4.test.js` | 37 (10 groups) | 6 groups | 4 groups |
| `sprint5.test.js` | 30 | 22 | 8 |
| `sprint6.test.js` | 32 | 30 | 2 |
| `sprint7.test.js` | 37 | 31 | 6 |
| **Total** | **136, all passing** | **83 of 99 classified (sprint5–7)** | **16 of 99** |

There is **no unit test framework, no component test, and no E2E test**. Measured code coverage
is **0%** — no coverage tooling exists in the project. A "source-text check" is
`readFileSync(file).includes('clearInterval')`: it passes if the string is present and fails if
someone renames a variable. It cannot detect a behavioral regression (R10).

**CI/CD:** none in-repo. Vercel builds on push to `main`. Rollback is Vercel-only; database
changes are forward-only.

**Runbook gaps:** no on-call surface, no alerting, no error tracking, no uptime monitoring
(§8 observability row). If the site breaks, the first signal is a human looking at it.

### 11b. Dead and suspicious code register

| Candidate | Static evidence | Dynamic evidence | Verdict | Scream-tested? |
|---|---|---|---|---|
| `components/ui/` — 53 files, 6,093 LOC | Zero inbound imports from `app/`, `sections/`, `components/`, `hooks/`, `lib/`. Verified for `@/`-alias, relative (`./ui`, `../ui`), and dynamic (`next/dynamic`, `import()`, `require()`) forms — all zero | Production build succeeds and produces a 102 kB shared baseline with no shadcn chunks; no runtime path can reach it | **DEAD** — CONFIRMED (C2) | ❌ not scream-tested (would modify the repo — command in §18a) |
| `lib/utils.ts` (`cn()`) | Imported 50× — **exclusively** by `components/ui/` | dies with the above | **DEAD once `components/ui/` is removed** | ❌ |
| 42 of 48 runtime dependencies (26 Radix packages, recharts, cmdk, vaul, embla, react-hook-form, zod, date-fns, …) | Not imported by any live module | not present in any live chunk | **DEAD** — CONFIRMED (C3) | ❌ |
| `types/index.ts` — `AIStock`, `Video`, `NavItem`, `AIModel`, `AIModelScores`, `RegulationItem` | Sections declare their own local row interfaces instead; these exports appear unused | build unaffected | **SUSPECTED DEAD** — UNCONFIRMED, not exhaustively verified | ❌ |
| `robots.ts` disallow entries `/login`, `/api/` | No such routes in the 14-route build table | — | **VESTIGIAL** — CONFIRMED | n/a |

*Nothing enters this table on static evidence alone; each row above pairs an import-graph fact
with a build or runtime observation. The register is complete for `components/ui/` and the
dependency set; the `types/` row is explicitly marked unconfirmed.*

---

## 12. Glossary

| Term | Meaning here | Source |
|---|---|---|
| **Section** | A full-width homepage block that owns its own data fetch (`sections/*.tsx`). Not a shadcn "section" | directory + code |
| **Category** | One of exactly 8 slugs — `models`, `agents`, `tools`, `research`, `business`, `policy`, `hardware`, `learn`. Stored as `articles.category`, a plain text column with no lookup table | `app/(main)/category/[slug]/page.tsx:4-13` |
| **Tag** | A free-form string in the `articles.tags` text array. Powers `/tag/[slug]`, "related articles" (via array overlap), and Trending Topics (counted client-side over the 200 most recent articles) | `lib/supabase.ts:307`, `:266` |
| **Breaking / Featured / Exclusive** | Three independent booleans on `articles` driving three different sections. The Hero uses `OR` across all three plus a non-empty image | `lib/supabase.ts:119-131` |
| **Key points / Why it matters** | AI-generated article furniture: `key_points` (text array) and `why_it_matters` (text). Rendered only when `body` is absent (commit `adfec1d1`) | `types/index.ts:24-25` |
| **Model Scoreboard** | Editorial LLM ranking in `model_scores`, sorted by `score_overall`, with an unauthenticated community `vote_count` | `sections/ModelScoreboard.tsx` |
| **Sprint N** | The author's own iteration label. Commits, test files, and SQL files are named by sprint; there were 7, all in two days | git log |
| **`ai-pulse-bookmarks`** | The localStorage key for saved articles — a **stale product name** predating "AI Fresh Daily". Renaming it will silently drop every existing user's bookmarks | `hooks/useBookmarks.ts:4` |

---

## 16a. What we could not determine

**Required. Never omitted. Never empty.**

| # | Unknown | Why unresolved | What would resolve it |
|---|---|---|---|
| 1 | **What writes the `articles` table** — the ingestion/generation pipeline, its schedule, its failure modes, who owns it | It is not in this repository; there is no reference to it anywhere in the code, config, or git history | Check the Supabase dashboard for Edge Functions, `pg_cron` jobs, and Database Webhooks; check for a second repo, an n8n/Make/Zapier workspace, or a Vercel cron in another project. **Start here** |
| 2 | **RLS state and policies on `articles`, `model_scores`, `regulations`, `timeline_events`, `ai_voices`, `stock_tickers`** (C9) | Supabase MCP returned `Unauthorized` for `list_tables` / `execute_sql` / `get_advisors`; no service-role credential available | Run in the SQL Editor: `select relname, relrowsecurity from pg_class where relnamespace='public'::regnamespace and relkind='r';` then `select * from pg_policies where schemaname='public';` and `select grantee, table_name, privilege_type from information_schema.role_table_grants where grantee='anon';` Also run the dashboard's Security Advisor |
| 3 | **The true schema** — real column lists, types, nullability, indexes, defaults, constraints | Same credential gap; §8a is reconstructed from client code | `supabase db pull`, or `pg_dump --schema-only` |
| 4 | **Whether `articles.is_video` exists** (R15) | No test, no migration, and a failing query is swallowed by `VideosSection` | One `select is_video from articles limit 1;` |
| 5 | **Whether the `.or()` filter interpolation is exploitable** (C10) | Live-API probing was out of scope for a read-only teardown | Against a **non-production** project, issue searches containing `,`, `)`, and `.` and observe whether the filter tree changes |
| 6 | **Whether a staging/preview environment exists** | Only one Supabase URL appears anywhere in the repo; Vercel project settings were not inspected | Check Vercel project → Settings → Environment Variables for a preview-scoped `NEXT_PUBLIC_SUPABASE_URL` |
| 7 | **Production behaviour** — traffic, latency, error rate, Core Web Vitals, whether crawlers actually index the homepage | No runtime or dashboard access | Vercel Analytics + Speed Insights; Google Search Console "Coverage" and URL Inspection on `/` |
| 8 | **Why development stopped after 2026-02-21**, and whether the site is still deployed and serving | Outside the repository | Ask the previous owner; check the Vercel deployment list |

---

## 18a. Appendices — regenerate every artifact

```bash
cd /Users/buda007/aifreshdaily-next
git rev-parse HEAD                       # must print 038e016ad671e765dae6a8a6909bd7a5e52dc07c

# §1 census
find . -path ./node_modules -prune -o -path ./.next -prune -o -path ./.git -prune \
     -o -type f -print | sed 's/.*\.//' | sort | uniq -c | sort -rn

# §5 client/server classification
for f in $(find app sections components hooks -name '*.ts*' | grep -v components/ui); do
  head -3 "$f" | grep -q "use client" && echo "CLIENT $f" || echo "server $f"; done

# §5 import graph (the Reflexion diff input) — see the python block used in this teardown
# §3 egress inventory
grep -rhoE "\.from\('[a-z_]+'\)" app sections components lib hooks | sort | uniq -c
grep -rhoE "\.rpc\('[a-z_]+'"    app sections components lib hooks | sort | uniq -c
grep -rn "\.insert(\|\.update(\|\.upsert(\|\.delete()" app sections components lib hooks   # expect: none

# §11b dead-code verification
grep -rn "components/ui\|from '\.\./ui\|from './ui" app sections components hooks lib | grep -v '^components/ui/'

# §10 build evidence
npm run build
grep -c "article/" .next/server/app/index.html            # expect 0  (Q2)
grep -c '<loc>'    .next/server/app/sitemap.xml.body      # expect 546 (Q5)
npx tsc --noEmit                                          # expect no output (Q7)

# §11a test evidence — WARNING: these hit the production database
node sprint4.test.js && node sprint5.test.js && node sprint6.test.js && node sprint7.test.js

# scream test for §11b (NOT run during this teardown — run it on a branch)
git checkout -b scream/remove-ui && git rm -r components/ui lib/utils.ts \
  && npm run build && node sprint7.test.js
```

---

## Suggested first week for the new developer

1. **Day 1 — read this document, then `lib/supabase.ts` end to end.** It is 346 lines and it is
   the entire data layer. Every query in the product is in that one file.
2. **Day 1 — run §16a item 2** (the RLS query). It is five minutes and it is the only open
   question in this document that could be an emergency.
3. **Day 1–2 — answer §16a item 1**: find what writes `articles`. Nothing else about the system
   can be reasoned about safely until that pipeline is identified.
4. **Day 2 — capture the schema** (R1). `supabase db pull` into `supabase/migrations/`. This is
   the highest-leverage half-day in the backlog.
5. **Day 3 — ship two one-line wins**: `revalidate` on the sitemap (R2) and the three dead links
   (R9). Small, safe, and they prove the deploy path works end to end.
6. **Day 4 — delete `components/ui/` on a branch and scream-test it** (R7 + §18a). Then re-enable
   type checking (R11).
7. **Day 5 — write the first real test**: a Playwright check that `/` renders at least one
   article headline after hydration. That single test would have caught R3, and it is the
   beginning of an answer to R10.
