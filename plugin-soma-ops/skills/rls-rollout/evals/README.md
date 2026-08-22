# evals.json za rls-rollout — README

## (a) Šta je ovo i kako se odnosi na postojeći tests/ folder

Ovo je **prvi evals.json set** za skill `rls-rollout` (faza 03-izrada). Skill već
ima folder `tests/` sa pravim TypeScript integracionim testovima
(`gdpr-export.test.ts`, `admin-routes.test.ts`, `lockout-recovery.test.ts`,
`worker-tenant-context.test.ts`, `performance.test.ts`, `cross-tenant.test.ts`,
`public-routes.test.ts`). Ti testovi proveravaju da li **generisani kod**
(RLS politike koje skill kreira) stvarno ispravno izoluje podatke između
tenant-a — pokreću se protiv prave Postgres baze i deo su STEP 4 (staging
verification) samog skilla.

Ovaj evals.json set je **komplementaran**, ne zamena: testira da li agent koji
**sledi** rls-rollout skill ispravno prati proceduru iz SKILL.md — redosled
gejtovanih koraka, kada eskalira/staje, koje pragove i OR/AND uslove primenjuje,
i gde su tvrde granice skilla. `tests/` proverava ponašanje baze; ovaj set
proverava ponašanje agenta-operatera.

## (b) Šta set testira, a šta namerno NE testira

**Testira:** proceduralnu/odlučivačku logiku eksplicitno navedenu u SKILL.md —
redosled STEP-ova i gejtove za odobrenje, značenje exit kodova, rollback
trigere i njihovu OR logiku, izbor rollback sloja (layer) prema razmeri
problema, i tvrde granice ("skill nikad ne radi cutover/apply").

**Namerno NE testira:**
- Da li generisani SQL zaista sprečava cross-tenant čitanje/pisanje (to radi
  `tests/cross-tenant.test.ts` i ostali `.test.ts` fajlovi protiv prave baze).
- Sintaksu ili ispravnost konkretnih SQL upita/migracija.
- Performanse upita ili p95 regresiju (to radi `tests/performance.test.ts`).
- Bilo šta što zahteva pristup pravoj bazi, fajl-sistemu projekta ili
  prethodnom stanju razgovora — svaki eval je samostalan hipotetički scenario
  rešiv čistim rezonovanjem iz teksta SKILL.md.

## (c) Šta svaki slučaj cilja (kratko)

1. **Redosled STEP-ova / gejt za odobrenje** — testira da agent ne preskoči
   STEP 2 (plan generation + ljudsko odobrenje) i ne skoči direktno na STEP 3,
   čak i kad korisnik to eksplicitno traži. Izvor: "Each STEP requires
   explicit human confirmation before the next" i "User MUST read and approve
   the plan document before STEP 3."
2. **STEP 4 exit code 1 = STOP bez izuzetka** — testira da cross-tenant leak
   (exit code 1) zaustavlja rollout bez obzira na veličinu curenja ili na to
   što su drugi test paketi prošli. Izvor: tabela exit kodova STEP 4,
   "Cross-tenant leak detected — STOP, do not deploy."
3. **Rollback trigers — OR logika, pet nezavisnih grana** — testira da agent
   prepozna da JEDAN probijeni uslov (Sentry permission-denied > 5/min) sam po
   sebi pokreće rollback, bez potrebe da i ostali uslovi budu probijeni.
   Izvor: "Rollback triggers (any one fires → rollback)."
4. **Izbor rollback sloja prema razmeri problema** — testira da agent za
   problem izolovan na jednu tabelu bira Layer 2 (`--disable-tables`), a ne
   Layer 4 (nuclear, svih 61 tabela), koji je rezervisan za "production is on
   fire."
5. **isPublic izuzetak važi samo za SELECT** — testira da agent prepozna da
   OR isPublic=true klauzula ide isključivo u SELECT politiku, dok
   INSERT/UPDATE/DELETE ostaju strogo org-scoped. Izvor: "SELECT policy
   includes OR isPublic = true... INSERT/UPDATE/DELETE remain strict (own org
   only)."
6. **Skill nikad ne radi produkcijski cutover** — testira da agent odbije
   direktan zahtev da sam flipuje `RLS_ENFORCEMENT_ENABLED` i pokrene
   `prisma migrate deploy` na produkciji, čak i kad je sve prošlo i korisnik
   eksplicitno insistira. Izvor: "NEVER auto-applies migrations" (frontmatter)
   i "Skill never performs cutover... Human operator follows the runbook
   manually" (STEP 5).

## (d) Format

Isti format kao `skill-creator-pro/evals/evals.json`:

```json
{
  "skill_name": "rls-rollout",
  "evals": [
    {
      "id": 1,
      "prompt": "samostalan hipotetički scenario sa svim potrebnim brojevima/stanjem",
      "expected_output": "tačan zaključak i zašto, sa referencom na konkretno pravilo iz SKILL.md",
      "expectations": ["konkretna proverljiva tvrdnja 1", "..."]
    }
  ]
}
```

`prompt` je uvek samostalan — ne referencira ovaj razgovor, fajlove na disku
niti prethodno stanje; sadrži sve brojeve i uslove potrebne da se scenario
nedvosmisleno reši. `expected_output` daje tačan zaključak sa referencom na
pravilo iz SKILL.md. `expectations` je lista konkretnih, proverljivih tvrdnji
pogodnih za automatsko ili ručno ocenjivanje odgovora agenta.

## (e) Ograničenje i sledeći korak

Ovih 6 slučajeva pokriva najizraženija, najlakše-pogrešiva proceduralna
pravila iz SKILL.md (gejtovi, exit kodovi, OR-uslovi, izbor sloja, isPublic
izuzetak, granica cutover-a), ali ne pokriva svaki eksplicitni detalj (npr.
STEP 0 preflight blocking-vs-warning nijanse po pojedinačnoj proveri, ili
`worker-tenant-context` pravilo da `budget.monthly.reset` i
`governance.timeout` koriste admin klijenta bez tenant konteksta). Sledeći
korak bi bio proširenje seta na te preostale grane, i po potrebi—kad se
skill promeni—ponovna provera da li navedena pravila i dalje odgovaraju
tekućem SKILL.md tekstu (verzija 1.0.0 od 2026-05-18 u trenutku pisanja ovog
seta).
