# Taksonomija kategorija

Osam kategorija. Nastale spajanjem pet ručnih kategorija (`problem-aware`, `poređenje`, `cena`, `lokalno`, `brendirano`) sa objavljenim taksonomijama: Conductor (8-intent enum), Nightwatch (4-tip), Otterly (5-tip), SE Ranking (5-tip), MaxAEO (objavljena kompozicija po vertikali). Izvori i puna obrazloženja u `research-basis.md`.

Ovaj fajl je referenca za Fazu 4/5 (formulisanje upita) — SKILL.md telo drži samo kvota tabelu. Čitaj ovde kad treba da odlučiš u koju kategoriju upit ide, ili da vidiš primer formulacije.

## Sadržaj

1. [problem_aware](#1-problem_aware)
2. [category_shortlist](#2-category_shortlist)
3. [use_case](#3-use_case)
4. [comparison](#4-comparison)
5. [pricing](#5-pricing)
6. [local](#6-local)
7. [trust_risk](#7-trust_risk)
8. [branded](#8-branded)

---

## 1. `problem_aware`

**Šta pokriva:** simptom ili zadatak izražen bez imena kategorije proizvoda/usluge. Kupac zna da ima problem, ne zna (ili ne piše) kako se rešenje zove. JTBD-izvedeno (jobs to be done) — pitaj "šta kupac pokušava da uradi", ne "šta mi prodajemo".

**Awareness stadijum:** `unaware` (ne zna ni da postoji kategorija rešenja) ili `problem_aware` (zna da ima problem, ne zna za rešenja). Uključivanje `unaware` nivoa je namerno — to je nivo koji "funnel počinje od kategorije" razmišljanje sistemski propušta.

**Kvota:** 15–22% seta.

**intent_type:** skoro uvek `informational`. **micro_moment:** `i_want_to_know` ili `i_want_to_do`.

**Primeri (CloudFlow CRM, B2B SaaS):**
1. "gubim previše vremena na ručno praćenje kontakata i ponuda" (`unaware`)
2. "kako da prestanem da gubim lead-ove između prodavaca" (`problem_aware`)
3. "zašto mi se prodajni tim gubi u excel tabelama" (`problem_aware`)

**Anti-primer:** "najbolji CRM za praćenje lead-ova" — ovo već zna ime kategorije (CRM), ide u `category_shortlist` ili `use_case`.

---

## 2. `category_shortlist`

**Šta pokriva:** "najbolji {kategorija} u {zemlja/region}", listicle ili rangiranje bez dodatnog filtera. Kupac zna kategoriju, traži opštu listu opcija.

**Awareness stadijum:** `solution_aware`.

**Kvota:** 22–30% seta — najveća pojedinačna kategorija, jer je ovo najčešći oblik AI-search upita u kategoriji (Conductor, Profound).

**intent_type:** `commercial_investigation`. **micro_moment:** `i_want_to_know`. **expected_answer_type:** obično `list`, ponekad `single_recommendation` kad je upit uži ("koji CRM preporučujete...").

**Primeri:**
1. "najbolji CRM za male firme"
2. "koji su najbolji CRM alati u Srbiji"
3. "koji CRM softver ima najbolje ocene korisnika"

**Razlika od `use_case`:** shortlist nema segment/scenario filter. Čim upit doda "za {ko/šta konkretno}", ide u `use_case`.

---

## 3. `use_case`

**Šta pokriva:** "najbolji {kategorija} za {segment/scenario}" — isti nivo svesti kao shortlist, ali sa filterom koji menja koji odgovor je tačan (druga lista za "CRM za nekretnine" nego za "CRM za male firme").

**Awareness stadijum:** `solution_aware`.

**Kvota:** 15–22%.

**intent_type:** `commercial_investigation`. **micro_moment:** `i_want_to_do` (naglasak je na zadatku/scenariju, ne na goloj listi).

**Primeri:**
1. "najbolji CRM za prodaju nekretnina"
2. "koji CRM koristiti za timove koji rade na terenu"
3. "kako izabrati CRM za mali tim od 5 ljudi"

**Zašto posebna kategorija od shortlist-a:** segment menja rangiranje — GEO merenje koje ne razdvaja ova dva sistemski potceni vertikalne/niche igrače koji dominiraju u use-case pretragama a ne u opštim.

---

## 4. `comparison`

**Šta pokriva:** "{A} vs {B}", "alternativa za {X}", "šta je bolje", "razlika između {A} i {B}". Kupac već ima 2+ opcije na radaru.

**Awareness stadijum:** `solution_aware` ili `product_aware`.

**Kvota:** 12–20%. Ovo je kategorija koja bez pravog istraživanja konkurenata (Faza 3) ostaje prazan placeholder — vidi O3 u SKILL.md.

**intent_type:** `commercial_investigation`. **expected_answer_type:** `comparison_table`.

**Integritet (G10):** svaki upit MORA sadržati ime iz `competitors[]` ILI obrazac "alternativa za" ({en}: "alternative to"). Upit koji kaže samo "sa čime da poredim CRM" bez imena ide u `category_shortlist`, ne ovde.

**Primeri:**
1. "CloudFlow CRM ili Pipedrive, šta je bolje"
2. "alternativa za HubSpot koja je jeftinija"
3. "da li je bolji Followup CRM ili CloudFlow"

---

## 5. `pricing`

**Šta pokriva:** "koliko košta", "cenovnik", "da li se isplati". Tri različita intenta unutar iste kategorije — vidi `locale-sr.md` za zašto se ne tretiraju kao sinonimi.

**Awareness stadijum:** `product_aware` — kupac već zna KOJI proizvod, pita o ceni.

**Kvota:** 8–12%.

**intent_type:** `transactional` (gola cena) ili `commercial_investigation` ("da li se isplati" je jak signal razmatranja, ne gole činjenice). **expected_answer_type:** `fact` ili `explanation`.

**Primeri:**
1. "koliko košta CloudFlow CRM za mesec dana"
2. "da li se isplati platiti godišnju CloudFlow pretplatu"
3. "cenovnik CloudFlow CRM za tim od 10 ljudi"

---

## 6. `local`

**Šta pokriva:** "{kategorija} u {grad}", "blizu mene", radno vreme/lokacija/logistika. Jedina kategorija čija kvota zavisi od `geo_scope` ulaznog parametra.

**Awareness stadijum:** sve — lokalni upit se pojavljuje u bilo kom stadijumu svesti (neko ko ne zna ni kategoriju i dalje može pitati "ima li neko blizu mene ko rešava X").

**Kvota:** 5–15%. **Ako `geo_scope == "global"`, kvota je 0** i budžet se preraspoređuje na `use_case` i `category_shortlist` u odnosu 60/40 (vidi SKILL.md footnote 1).

**intent_type:** `navigational` ili `informational`. **micro_moment:** `i_want_to_go` — ovo je osa koja tera geo upite koje funnel-only razmišljanje ispušta.

**Primeri (nacionalni B2B SaaS sa sedištem u jednom gradu — lokalni intent je i dalje relevantan za podršku/kancelariju, ne za sam proizvod):**
1. "CloudFlow CRM podrška u Beogradu"
2. "gde se nalazi kancelarija CloudFlow CRM u Beogradu"
3. "da li CloudFlow CRM ima predstavnika u Beogradu"

**Za lokalni servis (npr. stomatološka ordinacija) umesto SaaS-a**, `local` nosi mnogo veći udeo prirodno — "najbolja ordinacija za implantologiju u Novom Sadu" je i `category_shortlist` I `local` istovremeno u smislu teme, ali kategoriju određuje da li je grad STRUKTURNI deo upita (ide u `local`) ili je opšti listicle bez geo-filtera (ide u `category_shortlist`). Vidi G7b u SKILL.md — ova dva upita namerno smeju da dele većinu reči.

---

## 7. `trust_risk`

**Šta pokriva:** "iskustva", "recenzije", "da li je pouzdan", žalbe, garancija. Kupac proverava rizik pre odluke.

**Awareness stadijum:** `product_aware`.

**Kvota:** 5–10%.

**intent_type:** `informational` ili `commercial_investigation`. Ovi upiti su često `inferred: true` jer firma retko sama piše svoje negativne recenzije — grounding dolazi iz spoljnih izvora koje skill ne garantuje da će naći, pa je poštenije obeležiti kao pretpostavku.

**Primeri:**
1. "kakva su iskustva korisnika sa CloudFlow CRM"
2. "da li je CloudFlow CRM pouzdan za veće timove"
3. "CloudFlow CRM žalbe korisnika"

---

## 8. `branded`

**Šta pokriva:** ime brenda u upitu, BEZ imena konkurenta (čim se pojavi konkurent, ide u `comparison`, ne ovde).

**Awareness stadijum:** `product_aware` ili `most_aware`.

**Kvota:** 8–15%, **HARD CAP 15%** (`floor`, ne `ceil` — vidi kvantizaciju u SKILL.md). Kad ime brenda već stoji u upitu, pominjanje u AI odgovoru je skoro zagarantovano — prevelik udeo ove kategorije sistemski naduvava izmereni skor vidljivosti. Ovo je #2 failure mode posle prompt-set bias-a (vidi `research-basis.md`, Conductor 75/25 split).

**Primeri:**
1. "CloudFlow CRM prijava na nalog"
2. "kako da otkažem CloudFlow CRM pretplatu"
3. "da li CloudFlow CRM nudi besplatnu probu"

---

## Kritično pravilo — ćelije pre teksta

Kvota se popunjava ĆELIJAMA matrice `kategorija × persona × grad` (Faza 4 u SKILL.md), ne slobodnim pisanjem "30–50 upita". Slobodno generisanje pouzdano klasteruje oko onoga što model prvo pomisli — to je tačno prompt-set bias koji je razlog postojanja ovog skilla (vidi SKILL.md uvod).
