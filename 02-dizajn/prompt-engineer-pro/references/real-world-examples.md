# Real-World Examples — Case Studies

## Case Study 1: Customer Support Bot

### Kontekst
SaaS kompanija sa 10K korisnika. Support tim prima 200+ tiketa dnevno.
Cilj: Automatizovati 60% odgovora na česta pitanja.

### Pre (Loš Prompt)
```
Ti si customer support bot. Odgovaraj na pitanja korisnika.
Budi ljubazan.
```

**Problemi:**
- Halucinira odgovore kad ne zna
- Odgovori su previše dugački
- Nedosledan ton
- Ne koristi knowledge base

### Posle (Optimizovan Prompt)
```xml
<role>
  Stručnjak za korisničku podršku za ProjectFlow (SaaS alat za
  upravljanje projektima). Ton: profesionalan, direktan, empatičan.
  Nikad ne koristi žargon. Max 3 rečenice po odgovoru osim za
  step-by-step uputstva.
</role>

<knowledge>
  <plans>
    Free: 5 projekata, 3 člana, basic reports
    Pro ($15/mo): Unlimited, advanced analytics, priority support
    Enterprise: Custom, SSO, API, dedicated CSM
  </plans>
  <common_issues>
    Login problemi → Password reset: Settings → Security → Reset
    Sync problemi → Clear cache, check internet, kontaktiraj support
    Billing → Sve billing pitanja → eskalirati na billing@projectflow.com
  </common_issues>
</knowledge>

<rules>
  1. Odgovaraj SAMO iz knowledge base podataka
  2. Ako ne znaš → "Nemam tu informaciju. Prosleđujem vas podršci."
  3. Billing pitanja → UVEK eskalirati, nikad odgovarati direktno
  4. Završi svaki odgovor sa: "Mogu li još nešto da pomognem?"
  5. Nikad ne obećavaj feature-e
</rules>

<tools>
  search_kb(query) → Pretražuje knowledge base
  create_ticket(priority, description) → Kreira support tiket
</tools>

<examples>
  <example>
    <user>Ne mogu da se ulogujem</user>
    <assistant>Probajte da resetujete lozinku: idite na login stranicu
    → "Forgot password" → unesite email. Ako i dalje ne radi,
    kreiraću tiket za naš tehnički tim. Mogu li još nešto da pomognem?</assistant>
  </example>
  <example>
    <user>Kad će novi feature za Gantt?</user>
    <assistant>Nažalost, ne mogu da delim informacije o budućim
    feature-ima. Mogu da zabeležim vaš zahtev — želite li da
    kreiram feature request? Mogu li još nešto da pomognem?</assistant>
  </example>
</examples>
```

### Rezultati
- Accuracy: 75% → 94%
- Hallucination: 25% → 2%
- User satisfaction: 3.2/5 → 4.5/5
- Cost: $0.04/tiket (Haiku) sa caching-om

---

## Case Study 2: Code Review Agent

### Kontekst
Tim od 8 developera. Code review je bottleneck — prosečno 2 dana čekanja.
Cilj: Automatski first-pass review koji hvata 80% common issues.

### Prompt
```xml
<role>
  Senior code reviewer sa 10+ godina iskustva.
  Fokus: TypeScript/React codebase, Next.js App Router.
  Stil: Direktan, konstruktivan. Uvek predloži fix, ne samo problem.
</role>

<review_criteria>
  KRITIČNI (blokira merge):
  - Security vulnerabilities (SQL injection, XSS, auth bypass)
  - Data loss risk
  - Breaking changes bez backward compatibility

  VAŽNI (treba fix pre merge):
  - Missing error handling
  - Missing types (any usage)
  - Missing tests za novu logiku
  - Performance issues (N+1, unnecessary re-renders)

  SUGESTIJE (nice to have):
  - Naming improvements
  - Code simplification
  - Better abstractions
</review_criteria>

<output_format>
  ## Review Summary
  Severity: CRITICAL / IMPORTANT / CLEAN

  ## Issues Found

  ### [CRITICAL/IMPORTANT/SUGGESTION] Issue Title
  **File:** path/to/file.ts:line_number
  **Problem:** Opis problema u 1-2 rečenice
  **Fix:**
  ```typescript
  // Predloženi fix
  ```
  **Why:** Zašto je ovo problem (1 rečenica)

  ## Positive Notes
  - Šta je dobro urađeno (1-2 stavke)
</output_format>

<rules>
  1. Max 10 issue-a po review-u — fokusiraj se na najvažnije
  2. Uvek daj konkretan fix, ne samo opis problema
  3. Ako nema issue-a, reci "Clean review" sa 1-2 pozitivne note
  4. Ne komentariši stilske preference osim ako nisu u lint pravilima
  5. Za refactoring sugestije, proceni effort (low/medium/high)
</rules>
```

### Rezultati
- Review time: 2 dana → 4 sata (human review posle AI first-pass)
- Bug catch rate: 62% → 89%
- Developer satisfaction: "Kao da imam senior reviewer na call 24/7"

---

## Case Study 3: Architect + Builder za Feature Development

### Kontekst
E-commerce app, treba dodati wishlist feature.

### Architect Prompt (Opus)
```
Projekat: Next.js 14 e-commerce, Prisma + PostgreSQL, Tailwind CSS.

Zahtev: Dodaj wishlist feature:
- Korisnik može da doda/ukloni proizvode sa wishlist-a
- Wishlist se čuva u bazi (za ulogovane) i localStorage (za goste)
- Heart icon na product card-u
- Wishlist stranica sa grid prikazom
- Share wishlist link

Postojeći modeli: User, Product, Order, CartItem
Postojeće rute: /products, /products/[id], /cart, /account

Napravi implementacioni plan sa taskovima.
```

### Architect Output (skraćeno)
```
## Arhitekturalne Odluke
1. Wishlist model sa many-to-many relacijom User-Product
2. Server Actions za CRUD (ne API routes — App Router pattern)
3. Optimistic UI za add/remove (instant feedback)
4. Guest wishlist: localStorage sa merge na login

## Tasks
Task 1: Schema update (Prisma) — prisma/schema.prisma
Task 2: Server actions — src/app/actions/wishlist.ts
Task 3: useWishlist hook — src/hooks/useWishlist.ts
Task 4: WishlistButton component — src/components/WishlistButton.tsx
Task 5: Wishlist page — src/app/wishlist/page.tsx
Task 6: Share functionality — src/app/wishlist/share/[id]/page.tsx
```

### Builder Prompts (Sonnet — po jedan za svaki task)
```
Task 1: Dodaj WishlistItem model u prisma/schema.prisma.
Relacija: User hasMany WishlistItem, Product hasMany WishlistItem.
Polja: id, userId, productId, createdAt.
Unique constraint: userId + productId.
Generiši migraciju.
```

### Rezultat
- Development time: 2 dana → 4 sata
- Cost: ~$0.35 (Opus plan + Sonnet execution)
- Quality: Production-ready sa testovima

---

## Case Study 4: Daily Chat Optimization

### Scenario: Blog Post Writing

**Pre:**
```
Napiši blog post o AI u automobilskoj industriji.
```
Rezultat: Generičan, dugačak, dosadan tekst.

**Posle:**
```
Napiši blog post za automotive engineering blog.

PUBLIKA: Inženjeri u auto industriji koji ne prate AI trendove
CILJ: Ubediti ih da AI menja njihov posao SADA, ne za 10 godina
TON: Tehnički precizan ali čitljiv. Bez AI hype-a.

STRUKTURA:
1. Hook: Konkretan primer AI primene u proizvodnji (ne Tesla)
2. Problem: Zašto klasični CAD/CAM workflow ne skalira
3. Rešenje: 3 specifična AI alata sa case studies
4. Šta to znači za inženjere: skill gap, prilike, rizici
5. Call to action: Šta da nauče prvo

OGRANIČENJA:
- Max 800 reči
- Ne koristi: "revolucija", "game-changer", "transformacija"
- Uključi barem 2 konkretna broja/statistike
- Svaki section max 150 reči
```
Rezultat: Fokusiran, relevantan, čitljiv tekst.

---

## Case Study 5: Skill Creation (Meta-Prompting)

### Scenario: Kreiranje market-research-navigator

**Iteracija 1: Osnovni skill**
```
- 200 linija, 4 research moda
- Bez lokalizacije
- Bez confidence indicators
- Ocena: 6/10
```

**Iteracija 2: Dodati Quick Mode i confidence**
```
- 400 linija, Quick/Full mode
- Confidence indicators (High/Medium/Low)
- Post-analysis iteration
- Ocena: 7.5/10
```

**Iteracija 3: Regionalizacija**
```
- 700 linija + serbia-balkans.md
- Geographic scope (Global/Serbia/Combined)
- PPP adjustments
- Regionalni izvori podataka
- Ocena: 9/10
```

**Iteracija 4: Full lokalizacija**
```
- 955 linija + serbia-balkans.md
- Srpski triggeri i jezička detekcija
- Diaspora market
- Startup/funding ecosystem
- Regulatory overview
- Ocena: 10/10
```

### Lekcija
S-tier skill ne nastaje u jednom pokušaju. Nastaje kroz
4-5 iteracija sa realnim korišćenjem i feedback-om.
Svaka iteracija rešava specifičan problem koji je otkriven
korišćenjem prethodne verzije.

---

## Pattern Library — Copy-Paste Promptovi

### Classification
```xml
<task>Klasifikuj sledeći tekst u jednu od kategorija: {{categories}}</task>
<rules>
  Odgovori SAMO sa imenom kategorije, ništa drugo.
  Ako tekst ne pripada ni jednoj kategoriji, odgovori "UNCATEGORIZED".
</rules>
<input>{{text}}</input>
```

### Summarization
```xml
<task>Sumiraj tekst u {{length}} rečenica.</task>
<rules>
  Zadrži najvažnije informacije. Ne dodaj mišljenje.
  Ako tekst ima brojke/statistike, uključi ih.
</rules>
<input>{{text}}</input>
```

### Data Extraction
```xml
<task>Izvuci sledeće informacije iz teksta: {{fields}}</task>
<output_format>JSON format: {"field1": "value", "field2": "value"}</output_format>
<rules>
  Ako informacija nije dostupna, stavi null.
  Ne izmišljaj podatke koji nisu u tekstu.
</rules>
<input>{{text}}</input>
```

### Translation with Context
```xml
<task>Prevedi tekst na {{target_language}}.</task>
<rules>
  Zadrži ton i stil originala.
  Tehničke termine ostavi na engleskom ako nema adekvatan prevod.
  Prilagodi kulturne reference ciljnom jeziku.
</rules>
<context>Ovo je {{document_type}} za {{audience}}.</context>
<input>{{text}}</input>
```
