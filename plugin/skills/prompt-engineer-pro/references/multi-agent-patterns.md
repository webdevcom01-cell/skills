# Multi-Agent Patterns — Deep Reference

## Architect + Builder Pattern (Detalji)

### Kada koristiti

```
✅ KORISTI Architect+Builder kad:
  - Projekat ima 3+ fajlova za kreiranje/menjanje
  - Treba arhitekturalna odluka pre implementacije
  - Budget je bitan (60-70% ušteda)
  - Kvalitet planiranja je kritičan

❌ NE KORISTI kad:
  - Jednostavan bug fix (1 fajl, jasno šta treba)
  - Quick script (< 50 linija)
  - Exploratory coding ("pokušaj ovo i vidi")
```

### Architect Prompt Template

```markdown
# Task
Analiziraj sledeći zahtev i napravi detaljan implementacioni plan.

## Zahtev
{{user_request}}

## Codebase kontekst
{{relevant_files_and_structure}}

## Output format
Napravi plan sa sledećom strukturom:

### Arhitekturalne Odluke
- Odluka 1: [opis] — Razlog: [zašto]
- Odluka 2: [opis] — Razlog: [zašto]

### Tasks (u redosledu izvršavanja)
Za svaki task:
- **Task N: [naziv]**
  - Fajl: `path/to/file.ts`
  - Akcija: CREATE / MODIFY / DELETE
  - Opis: Šta tačno treba uraditi
  - Pseudo-kod ili key logic (5-10 linija)
  - Zavisnosti: [koji taskovi moraju biti gotovi pre ovog]

### Rizici
- Rizik 1: [opis] — Mitigacija: [kako]

### Estimacija
- Ukupno taskova: N
- Procenjena kompleksnost: Low/Medium/High
```

### Builder Prompt Template

```markdown
# Task {{task_number}}
{{task_description_from_architect}}

## Kontekst
Ovaj task je deo većeg plana. Prethodni taskovi su završeni:
{{completed_tasks_summary}}

## Fajl
{{file_path}} — {{CREATE/MODIFY}}

## Instrukcije
1. Implementiraj tačno ono što je opisano u tasku
2. Prati konvencije projekta iz CLAUDE.md
3. Napiši testove za novu funkcionalnost
4. Pokreni testove i fix-uj ako padaju
5. Ne menjaj fajlove koji nisu navedeni u tasku

## Pseudo-kod iz plana
{{pseudocode_from_architect}}
```

### Real-World Primer: Authentication Feature

```bash
# KORAK 1: Architect planira (Opus)
claude --model opus << 'EOF'
Projekat: Next.js 14 e-commerce app
Zahtev: Dodaj email/password authentication sa:
- Registration, Login, Logout
- Protected routes
- JWT tokens u HTTP-only cookies
- Password hashing sa bcrypt

Codebase:
- src/app/ (App Router)
- src/lib/prisma.ts (Prisma client)
- prisma/schema.prisma (User model već postoji ali nema password)

Napravi implementacioni plan.
EOF

# KORAK 2: Builder izvršava svaki task (Sonnet)
claude --model sonnet "Task 1: Ažuriraj Prisma schema..."
claude --model sonnet "Task 2: Kreiraj auth utility funkcije..."
claude --model sonnet "Task 3: Implementiraj API routes..."
claude --model sonnet "Task 4: Kreiraj login/register forme..."
claude --model sonnet "Task 5: Dodaj middleware za protected routes..."

# KORAK 3: Architect review-uje (Opus)
claude --model opus "Review-uj implementaciju. Proveri:
1. Security (SQL injection, XSS, CSRF)
2. Error handling (sve moguće greške pokrivene?)
3. Edge cases (concurrent login, expired tokens)
4. Code quality (DRY, naming, structure)"
```

---

## Specialist Chain Pattern

Različiti promptovi za različite faze development-a:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ ANALYZER │───►│ DESIGNER │───►│  CODER   │───►│ REVIEWER │
│          │    │          │    │          │    │          │
│ Razume   │    │ Definiše │    │ Piše     │    │ Proverava│
│ zahtev   │    │ API i    │    │ kod i    │    │ kvalitet │
│          │    │ strukturu│    │ testove  │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

**Svaki specialist ima fokusiran prompt:**

```markdown
# ANALYZER prompt
Ti si requirements analyst. Tvoj jedini zadatak je da:
1. Razumeš šta korisnik želi
2. Identifikuješ nejasnoće i rizike
3. Postaviš pitanja za razjašnjenje
4. Output: Strukturiran requirements dokument
NE dizajniraj rešenje. NE piši kod.

# DESIGNER prompt
Ti si software architect. Tvoj jedini zadatak je da:
1. Na osnovu requirements dokumenta, dizajniraj rešenje
2. Definiši API contracts (input/output za svaku funkciju)
3. Odredi file structure i dependencies
4. Output: Technical design dokument sa pseudo-kodom
NE piši finalni kod. NE implementiraj.

# CODER prompt
Ti si implementator. Tvoj jedini zadatak je da:
1. Na osnovu design dokumenta, napiši produkcijski kod
2. Prati API contracts TAČNO kako su definisani
3. Napiši unit testove za svaku funkciju
4. Output: Kompletni source fajlovi
NE menjaj dizajn. NE dodaj feature-e koji nisu u specifikaciji.

# REVIEWER prompt
Ti si code reviewer. Tvoj jedini zadatak je da:
1. Proveraš da li implementacija prati dizajn
2. Nađeš bugove, security issues, performance probleme
3. Proveraš test coverage
4. Output: Review report sa konkretnim fix-ovima
NE prepisuj kod. Samo ukaži na probleme i predloži fix-ove.
```

---

## Parallel Workers Pattern

Za bulk operacije na više fajlova:

```bash
# Primer: Dodaj TypeScript types na 10 fajlova
# Kreiraj jedan master prompt, primeni na svaki fajl

MASTER_PROMPT="Dodaj TypeScript tipove na ovaj JavaScript fajl.
Pravila:
- Koristi strict tipove (ne any)
- Dodaj interface za svaki object shape
- Koristi generics gde je primerno
- Zadrži JSDoc komentare"

for file in src/utils/*.js; do
  claude --model haiku "$MASTER_PROMPT

  Fajl: $file
  Sadržaj:
  $(cat $file)"
done
```

---

## CLAUDE.md — Project Configuration

### Struktura

```markdown
# CLAUDE.md

## Projekat
[Jednolinijski opis: šta je, koji stack]

## Quick Start
[3-5 komandi za pokretanje projekta]

## Konvencije
[Coding standards, naming, patterns]

## Struktura
[File tree sa opisima direktorijuma]

## Pravila
[MUST DO / NEVER DO lista]

## Testing
[Kako pokrenuti testove, coverage zahtevi]

## Deployment
[Kako deplojovaati, environment variables]
```

### Primer: CAD/Automotive Projekat

```markdown
# CLAUDE.md

## Projekat
CAD conversion pipeline — konverzija AI-generisanih Ferrari
dizajn koncepata u tehničke crteže za Fusion 360.

## Konvencije
- Python 3.11+ za pipeline skripte
- STEP format za 3D modele (ne STL)
- Tolerancije: ±0.1mm za aerodinamičke površine
- Naming: {car_model}_{component}_{version}.step

## Struktura
pipeline/
  input/       — AI-generisane slike i mesh-evi
  processing/  — Konverzija i cleanup skripte
  output/      — STEP fajlovi za Fusion 360
  validation/  — Provera geometrije i tolerancija

## Pravila
- NIKAD ne menjaj tolerance bez potvrde
- Svaki STEP fajl mora proći validation pre outputa
- Commit poruke: {component}: {opis promene}

## Dependencies
- cadquery za programmatic CAD
- trimesh za mesh processing
- numpy za geometrijske kalkulacije
```

---

## Cost Comparison

```
Scenario: Implementacija auth feature-a (5 fajlova, ~800 linija koda)

PRISTUP 1: Opus za sve
  Input:  ~15,000 tokena × $15/M  = $0.225
  Output: ~8,000 tokena × $75/M   = $0.600
  UKUPNO: $0.825

PRISTUP 2: Architect (Opus) + Builder (Sonnet)
  Architect:
    Input:  ~3,000 tok × $15/M    = $0.045
    Output: ~1,500 tok × $75/M    = $0.113
  Builder (5 taskova):
    Input:  ~12,000 tok × $3/M    = $0.036
    Output: ~6,500 tok × $15/M    = $0.098
  UKUPNO: $0.292

  UŠTEDA: 65%

PRISTUP 3: Architect (Opus) + Builder (Haiku) — za simple tasks
  UKUPNO: ~$0.175
  UŠTEDA: 79%
```

---

## Debugging Multi-Agent Workflows

```
Problem: Builder ne prati plan
Fix: Dodaj u builder prompt: "Implementiraj TAČNO Task N.
Ne dodaj feature-e koji nisu u planu. Ne preskači korake."

Problem: Context loss između taskova
Fix: Dodaj completed tasks summary na početak svakog builder prompta.

Problem: Conflicting changes
Fix: Architect mora definisati file ownership —
koji task menja koji fajl. Nema overlap-a.

Problem: Architect plan je previše vague
Fix: Zahtevaj pseudo-kod i konkretne API contracts, ne samo opise.
```
