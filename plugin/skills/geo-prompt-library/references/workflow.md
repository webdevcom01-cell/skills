# Radni tok — puna mehanika Faza 1–9

SKILL.md telo drži samo tanak orkestrator (imena faza, jedna rečenica svaka) zato što telo ima budžet od 5000 tokena i taj budžet mora prvo pripasti pravilima koja moraju preživeti skraćivanje (anti-halucinacija, matrica pre teksta, fail-closed — vidi SKILL.md). Ovaj fajl je pun tekst svih 9 faza.

**Zašto je čitanje ovog fajla preduslov, ne preporuka:** izlazni JSON sam svedoči o svakoj fazi, pa preskočena referenca nije tiha degradacija kvaliteta nego PAD GATE-a, primetan i merljiv:
- `matrix_plan` u izlazu dokazuje da se Faza 4 dogodila u ispravnom obliku — G16 poredi taj plan sa stvarnim brojem intenata po ćeliji, i pada ako plan nedostaje ili ne odgovara stvarnosti.
- `competitors[]` sa `how_found`/`confidence` i `source_url`/citat na `company.offerings[]` dokazuju Faze 2–3 — bez njih G12 (grounding pokrivenost) i G10 (comparison integritet) padaju.
- `validation.passed` (i `retry_count`, `first_attempt_failures`) je sama Faza 7 — nema ga bez pokretanja gate-a.
- `coverage_status` u izveštaju je sama Faza 8 — polje ne postoji ako se `verify_grounding.py` nije pozvao.

Model koji improvizuje ceo proces umesto da pročita ovaj fajl neće proizvesti te artefakte u ispravnom obliku, i to hvata fail-closed gate (SKILL.md, "QA gate — pravila"), ne dobra volja modela. To je prava garancija ove podele na dva fajla.

## Sadržaj

1. [Faza 1 — Normalizacija ulaza](#faza-1--normalizacija-ulaza)
2. [Faza 2 — Ekstrakcija profila firme](#faza-2--ekstrakcija-profila-firme)
3. [Faza 3 — Istraživanje konkurenata](#faza-3--istraživanje-konkurenata)
4. [Faza 4 — Konstrukcija matrice](#faza-4--konstrukcija-matrice)
5. [Faza 5 — Formulisanje SR upita](#faza-5--formulisanje-sr-upita)
6. [Faza 6 — EN parovi](#faza-6--en-parovi)
7. [Faza 7 — Deterministički QA gate](#faza-7--deterministički-qa-gate)
8. [Faza 8 — Provera grounding-a](#faza-8--provera-grounding-a)
9. [Faza 9 — Isporuka](#faza-9--isporuka)

---

## Faza 1 — Normalizacija ulaza

Popuni default-e (vidi SKILL.md, sekcija "Ulaz / Izlaz"). `n_intents < 30` → upozori na marginu greške (~±11pp pri n=50 prompt-run-ova i 20% stopi pominjanja). Zapamti tačno ono što je korisnik EKSPLICITNO dao (nasuprot onome što će se tek izvesti u Faza 2-4) — piše se u izlaz kao `inputs` u Fazi 9 (`references/schema.md`, sekcija `inputs`): `url`, `locale`, `vertical` (ili `null` ako se izvodi sa sajta), `n_intents`, `geo_scope` (ili `null` ako se izvodi), `competitors_source` (`"user_provided"` ako je korisnik dao listu, inače `"researched"`).

## Faza 2 — Ekstrakcija profila firme

Evidence-first. WebFetch homepage + do 6 podstranica (usluge → cene → o nama → kontakt/lokacije → FAQ → blog). Svaki fakt sa `source_url` + doslovnim citatom. **Anti-halucinacijsko pravilo:** nijedan upit ne sme sadržati uslugu/proizvod/grad/segment koje sajt ne potvrđuje citatom — osim uz `"inferred": true` i `rationale`; gate pada iznad 25% `inferred`. Fallback za JS-only/prazan sajt: traži od korisnika 5 stvari (šta prodaju, kome, gradovi, 3 konkurenta, opseg cena); u neinteraktivnom režimu generiši sa `confidence: "low"` i upozorenjem.

## Faza 3 — Istraživanje konkurenata

Preskoči ako je korisnik dao listu. Inače 3 WebSearch upita (`najbolji {kategorija} {lokacija}`, `{kategorija} {zemlja}`, `{brend} alternativa OR konkurenti`) → uzmi 3–5, svaki sa `how_found` + `confidence`; isključi sam brend i agregatore.

## Faza 4 — Konstrukcija matrice

Izračunaj ciljne brojeve po kategoriji (kvantizacija u SKILL.md, sekcija "Kategorije i kvote"), rasporedi po ćelijama `kategorija × persona × grad`. Ovo je tabela pre nego što je bilo šta napisano — i **upisuje se u izlaz** kao `matrix_plan` (planned po ćeliji + `planned_total`), ne drži se samo u radnoj memoriji. G16 posle poredi taj plan sa stvarnim brojem intenata po ćeliji — revizorski trag pokrivenosti, ne nagađanje iz kategorija.

### 4a/4b — dva odvojena poteza, ne jedan

Pisanje teksta upita za jednu ćeliju i provera te ćelije prema dokazu su dva različita poteza koja moraju ići TIM redosledom. Spajanje u jedan potez — gledaj citat, pa piši upit — je koren stvarne, ponovljene greške u prvoj verziji ovog skilla (vidi obrazloženje ispod), ne stilska preferenca.

**4a — Napiši upit kao kupac koji nikad nije video sajt.** Za ćeliju matrice imaš samo `category`, `persona`, `awareness_stage` i grad (ako je `local`). Ne otvaraj `company.offerings[]`/citate iz Faze 2 dok pišeš tekst — samo kategorija i persona određuju šta se pita. Cilj je glas stvarnog kupca koji ne zna kako se firma zove niti šta tačno piše na sajtu.

**4b — Tek onda proveri dopustivost prema dokazu iz Faze 2.** Pročitaj upit napisan u 4a i uporedi ga sa `company.offerings[]`/citatima iz Faze 2. Ako upit pominje uslugu, grad ili segment koji dokaz ne potvrđuje — ili prepravi upit da ostane unutar potvrđenog, ili označi `"inferred": true` + `rationale` (anti-halucinacijsko pravilo, Faza 2). Dokaz ovde radi kao FILTER na već napisan tekst, ne kao IZVOR teksta.

**Zašto je redosled nosiv, ne kozmetički.** Kad se citat čita PRE pisanja, model prirodno prepisuje frazu iz dokaza u upit, jer mu je citat doslovno pred očima dok formuliše rečenicu — dokaz treba da ograničava šta je DOZVOLJENO da uđe u upit, ne da isporučuje šta se PITA. Svaki loš primer u tabeli ispod nosi otisak svog izvornog citata: "Situated next to the old town of Budva" → "...u Budvi blizu starog grada"; CEO/o-nama stranica → "ko je vlasnik ili direktor"; hrvatska destinacijska stranica → "...preko crnogorskog chartera". Model u tim slučajevima nije izmislio činjenicu — nije to G12/anti-halucinacijski problem — nego je citat oblikovao SAMU REČENICU, ne samo njenu dopustivost. Grounding disciplina je procurela u glas upita. 4a/4b razdvajanje to sprečava strukturno: u 4a dokaz fizički nije deo konteksta pisanja, pa nema šta da procuri.

### Registar — obavezan miks

Kupac ne zna kako se firma zove, ne mari gde je registrovana, i ne koristi reč "provajder". Piši mešavinu:

- **~40% kratki, pretraživački** oblik: "Montenegro Charter iskustva", "gliser Budva cijena"
- **~60% razgovorni, sebičan** oblik, iz ugla kupca sa konkretnom situacijom: "tražim brod za osmoro u Boki krajem avgusta, šta mi preporučuješ"

**Zabranjen enciklopedijski registar** — nikad u obliku ankete ili kataloga: "koje su najbolje kompanije za X u Y", "koji su najpouzdaniji provajderi za Z", "ima li agencija za W". Taj oblik zvuči kao anketno pitanje, ne kao čovek koji nešto traži za sebe.

**Odnos 40/60 je orijentir, NE kvota.** Nikad ne produžavaj upit koji već zvuči prirodno samo da bi pogodio raspodelu — nesrazmera je jeftinija od naduvane rečenice. (Nalaz iz A/B-a montenegrocharter v1↔v2: kad se split pogodi tačno, model zna da konvertuje i ono što nije trebalo dirati — "bez iskusnog skipera" postaje "bez iskusnog skipera na brodu", "kako da rezervišem" postaje "kako mogu da rezervišem", samo da odnos ispadne tačan.)

### Loši naspram dobrih primera

Leva kolona je stvaran izlaz ovog skilla pre ove izmene (montenegrocharter v1) — puna rečenica, precizna, knjiška, i nosi informaciju koju kupac NEMA pre nego što pita. Desna kolona je isti intent kako bi ga čovek stvarno napisao.

| alat je napisao | čovek bi napisao |
|---|---|
| ima li charter agencija za brze glisere u Budvi blizu starog grada | gdje da iznajmim gliser u Budvi |
| kakva su iskustva klijenata sa Montenegro Charter agencijom | Montenegro Charter iskustva |
| da li se može iznajmiti jahta u Dubrovniku preko crnogorskog chartera | najam jahte Dubrovnik |
| koje su najbolje kompanije za charter motornih jahti u Boki Kotorskoj | najbolji charter jahti Boka |
| šta ako charter jahta otkaže rezervaciju u zadnji čas | šta ako mi otkažu charter |
| ko je vlasnik ili direktor Montenegro Charter kompanije | ko stoji iza Montenegro Chartera |
| koji su najpouzdaniji charter provajderi za porodičan odmor na moru | tražim brod za porodicu sa djecom, šta je najbolje |

## Faza 5 — Formulisanje SR upita

Pravila u `references/locale-sr.md`. Pun rečenični, konverzacijski oblik sa ispravnim padežima (hipoteza, ne merena studija — eksplicitno je tako označeno u referenci), 5–16 reči, za tech/B2B mešani kod (SR okvir + EN termin, npr. "kako da odaberem CRM za mali biznis"), nikad placeholder u finalnom tekstu.

## Faza 6 — EN parovi

Isti intent, ne doslovan prevod — engleski govornik bi drugačije formulisao. Isti `category`/`awareness_stage`/`geo`.

## Faza 7 — Deterministički QA gate

Pokreni `scripts/validate_library.py` (pun spisak G1–G16 pravila: SKILL.md, sekcija "QA gate — pravila"). Pad → pročitaj greške, regeneriši samo pogođene ćelije (ne ceo set). Pri određivanju KOJIH ćelija: **ignoriši pravila sa `"derived": true`** u `validation.checks` — to je isti koren kao neko drugo pravilo iz iste liste (G16 kad je pao i G4/G11/G13, G15 kad je pao i G6), ne dodatna pogođena ćelija. Regenerišeš ćelije koje pokazuje root pravilo; derived se samo od sebe popravi. Zapamti pokušaj 1 rezultat (`first_attempt_failures` — koja G-pravila su pala na prvi poziv, pre bilo kog retry-ja; ide u rezime, Faza 9). Max 3 pokušaja, pa isporuči sa `passed: false` i punim izveštajem — nikad tiho. Ortografske varijante (ascii **i** cyrillic) generiše `scripts/orthographic_variants.py` (deterministički `š→s, ž→z, č→c, ć→c, đ→dj`; č i ć oba kolabiraju u c — nema pokušaja round-trip-a nazad), ne model.

Ako `scripts/validate_library.py` izađe sa **exit 2** (ne 0, ne 1) — gate se NIJE izvršio (npr. nedostaje `jsonschema` u interpreteru), pročitaj FATAL poruku na stderr i ispravi okruženje pre nego što bilo šta zaključiš o biblioteci. Ne tretiraj exit 2 kao G1 pad.

## Faza 8 — Provera grounding-a

Tek pošto gate iz koraka 7 prođe, pokreni `scripts/verify_grounding.py <slug>-library-v<N>.json`. Ovo je **zaseban skript, ne G-pravilo** — gate mora ostati brz i offline jer se vrti u retry petlji (korak 7), ovaj korak zahteva mrežu po jedinstvenom `source_url` i sme da traje/padne iz prolaznih razloga. Gate proverava samo da `source_url`/`evidence`/`grounding.quote` POSTOJE; ovaj skript proverava da citat STVARNO STOJI na toj stranici — bez ovoga, model koji drži `inferred` nisko jednostavno piše uverljiv citat i gate ga pusti. Pročitaj `passed` **i** `coverage_status` iz izveštaja, ne samo exit kod:

- `coverage_status: "ok"` → nastavi na Fazu 9.
- `claims_not_found > 0` (citat koji nije na stranici — proverili smo i lažan je) → **tvrd pad**, ne isporučuj, vrati se na Fazu 2 za taj intent/offering.
- `coverage_status: "insufficient"` ili `"no_data"` (mreža nije dozvolila da se dovoljno toga proveri — `coverage < 0.5`, ili čak 0 tvrdnji stvarno provereno) → **ovo NIJE isto što i lažan citat**, ali isto tako nije "sve u redu": ne tretiraj `passed`/exit-kod izolovano, pročitaj `coverage_status` eksplicitno. Pokušaj ponovo (mreža je možda privremeno nedostupna — Cloudflare, rate limit), a ako se ponovi, isporuči uz jasno upozorenje korisniku da grounding NIJE nezavisno potvrđen (razlikuj to od "potvrđen i tačan" u rezimeu, Faza 9).
- `coverage_status: "no_claims"` → nema šta da se proveri (npr. ceo set `inferred: true`, thin-site fallback), u redu je, nastavi.

## Faza 9 — Isporuka

Zapiši 3 fajla. `schema_version: "1.1.0"` (ne `"1.0.0"`) — od ove verzije `inputs` je uslovno obavezan po šemi (`1.0.x` je izuzet, samo za stare fixture-e), pa `1.0.0` znači da G1 neće ni tražiti `inputs`. Uključi `inputs` iz Faze 1 u glavni JSON (`references/schema.md`, sekcija `inputs`) pre nego što izračunaš `content_hash` — hash se računa NAD sadržajem koji uključuje `inputs` i `schema_version`, ne pre njih, inače je hash pogrešan čim se dodaju. Kratak rezime korisniku (uključi `retry_count` iz koraka 7 i `coverage_status` iz koraka 8 — vidi SKILL.md, sekcija "Ulaz / Izlaz"). Ako je `coverage_status` bio `"insufficient"`/`"no_data"`, to MORA biti vidljivo u rezimeu, ne samo u JSON izveštaju — korisnik ne sme da pročita "isporučeno" i pretpostavi da je grounding nezavisno potvrđen kad zapravo nije bio proveren.
