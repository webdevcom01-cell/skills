# Ojačavanje, stavka #5: most sdd-workflow → agentic-loop-engineer (nikad ranije testiran)

**Kontekst:** poznata, dugo priznata rupa — `sdd-workflow`-ov `tasks.md` izlaz i
`agentic-loop-engineer`-ov `task_spec.md` ulaz nisu povezani na nivou koda i
nikad nisu testirani zajedno, end-to-end, na pravom zadatku.

**Metod:** stvarno pokrenut `sdd-workflow` skill (učitan preko Skill alata, ne
iz memorije) na sintetičkom, ali feature-sized zadatku sa pravom logikom
("word-freq" — CLI koji vraća N najčešćih reči, sa tie-breakom i opcionim
stopword filterom) u novom repou na Mac-u (`sdd-bridge-test`). Sve faze
(Constitution → Specify → Plan → Tasks) odrađene po pravim šablonima iz
skill-ovih reference fajlova, ne improvizovano.

---

## Nalaz 1 — Maker strana mosta RADI, i to jednostavnije nego što je pretpostavljeno

Umesto ručnog "prevođenja" svake `tasks.md` stavke u bogat, samodovoljan
`task_spec.md` (kako je rađeno u ranijem cirilica-konverter demou), testirana je
**tanka verzija**: `task_spec.md` samo kaže "pročitaj `specs/word-freq/{spec,plan,tasks}.md`
u ovom worktree-u, odradi T1-T5 odatle". Ovo radi mehanički bez ikakve dodatne
infrastrukture, iz jednostavnog razloga: `git worktree add` pravi PUN checkout
grane, pa ako su `spec.md`/`plan.md`/`tasks.md` komitovani u repo (prirodna
posledica toga što ih sam sdd-workflow tako piše), oni su fizički prisutni u
svakom worktree-u koji se od te grane napravi. Maker (izolovan worktree agent)
ih vidi bez ikakvog dodatnog mehanizma.

**Rezultat**: implementacija (`wordfreq.py` + `test_wordfreq.py`, 8 testova,
UC-1/2/3 + AC1-AC5 iz spec.md) napisana striktno na osnovu tog tankog
task_spec.md + spec/plan/tasks fajlova, `python3 -m pytest -q` → 8/8 PASS,
`checker-verify.sh` → `PASS`/`CONFIRMED`.

## Nalaz 2 — Checker strana mosta NIJE radila (stvaran bag, ispravljen)

`prepare-checker-bundle.sh` kopira Checker-u SAMO tri fajla (`task_spec.md`,
`diff.patch`, `verify_result.json`) — namerno, da Checker ne vidi Maker-ovo
privatno rezonovanje (`scratchpad.md`/`task_log.md`). Problem: tanak
`task_spec.md` upućuje Checker-a da pročita `specs/word-freq/spec.md` itd., ali
ti fajlovi **nisu bili deo bundle-a** — i nisu ni deo `diff.patch`-a, jer su
postojali već u base commit-u PRE nego što se grana odvojila (`git diff`
prirodno ne prikazuje ono što se nije promenilo). Rezultat bi bio Checker koji
dobije uputstvo da pročita fajl koji fizički ne postoji u njegovom izolovanom
direktorijumu.

**Ovo NIJE isti tip rizika kao scratchpad/task_log izolacija** — `spec.md`/
`plan.md`/`tasks.md` su UGOVOR dogovoren PRE nego što je Maker počeo, ne
Maker-ovo rezonovanje. Sam `sdd-workflow`-ov Converge korak
(`references/converge-and-verify.md`) eksplicitno traži da nezavisni verifier
dobije baš spec+plan+tasks+diff — dakle isporučeni `prepare-checker-bundle.sh`
je bio NEPOTPUN u odnosu na ono što `sdd-workflow` sam sebi propisuje za
Converge, ne samo u odnosu na agentic-loop-engineer.

**Ispravka (prva verzija)**: `prepare-checker-bundle.sh` kopira `specs/` folder
(kad postoji) u bundle, uz ažuriran `README-CHECKER.md` koji objašnjava da to
NIJE Maker-ovo rezonovanje, slobodno se koristi. (Ova verzija je posle,
u Rundi 2 ispod, još jednom doterana — vidi tamo.)

## Nalaz 3 — nezavisna Checker provera POTVRDILA da ispravka radi

Pokrenut pravi, odvojen subagent (fresh kontekst, nula znanja o ovom
razgovoru) sa pristupom ISKLJUČIVO `checker_bundle/` direktorijumu na Mac-u.
Verdikt: **CONFIRMED**, uz eksplicitnu potvrdu na direktno pitanje "da li je
bundle bio dovoljan, bez nagađanja van njega" — DA. Nezavisno je, red po red,
ručno proverio da li svaki UC/AC iz `spec.md` ima odgovarajući, ISPRAVAN test
(ne samo da test postoji) i da implementacija zaista radi ono što tvrdi.
Jedina primedba (ne obara verdikt): `verify_result.json` ne beleži broj/imena
pojedinačnih testova, samo agregatni PASS — postojeći, sitan, već poznat
limit sloja determinističke provere, ne posledica ovog mosta.

**Metodološka slabost, nađena tek u Rundi 2 (ispod)**: ovaj Nalaz 3 nema
trajni artefakt — nije sačuvan transkript te subagent sesije, samo prozni
rezime u ovom dokumentu. Ubuduće, izlaz nezavisnog Checker/reviewer subagenta
treba čuvati kao fajl (ne samo prepričavati), da bi bio proverljiv unazad.

---

## Runda 2 — nezavisan adversarijalni review (16. sept, pre prelaska na stavku #2)

Na Bukyjev zahtev, isti metod kao za stavku #1: pokrenut svež, nula-kontekst
`general-purpose` subagent, ovlašćen isključivo činjenicama (ne zaključcima),
sa zadatkom da preko `device_bash`-a na pravom Mac-u nezavisno proveri svih 5
gornjih tvrdnji (Nalaz 1-3 + dve prateće) i aktivno traži bilo šta izostavljeno.

### Verdikt po tvrdnji

- **Tvrdnja 1** (spec.md/plan.md/tasks.md su pravi, feature-sized, sa
  UC-1/2/3 + AC1-5) — **CONFIRMED**, pročitao fajlove direktno.
- **Tvrdnja 2** (task_spec.md je stvarno tanak pointer) — **CONFIRMED**.
- **Tvrdnja 3** (implementacija radi, 8/8 testova) — **CONFIRMED** — reviewer je
  SAM pokrenuo `python3 -m pytest -v` (ne verovao prijavljenom rezultatu) i
  ručno proverio 3 testa red-po-red protiv spec.md (uklj. tie-break i
  case-insensitive stopword test) — nisu plitki/tautološki.
- **Tvrdnja 4** (bundle bag nađen i ispravljen, scratchpad/task_log i dalje
  isključeni) — **CONFIRMED**, uz jednu poštenu napomenu: ispravka je i dalje
  bila nekomitovana (radna kopija) — što je već i ranije bilo eksplicitno
  priznato u ovom dokumentu, ne skriven nalaz.
- **Tvrdnja 5** (nezavisna Checker sesija zaista bila izolovana, fresh
  kontekst) — **PLAUSIBLE, ne može se nezavisno potvrditi**. Reviewer nije
  našao NIKAKAV trajni artefakt (transkript, log) te sesije — samo prozni
  navod u `verify.md` i u ovom dokumentu. Ne znači da se nije desilo kako je
  opisano, ali nije proverljivo unazad. Vidi napomenu na kraju Nalaza 3 gore —
  ovo je upravo taj isti gap, sad formalno potvrđen kao nedostatak procesa,
  ne samo nagađanje.

### Dodatni nalazi (van 5 tvrdnji) — dva su prava bagovi u samoj ispravci, ispravljeni i testirani

1. **Curenje specifikacija van scope-a (ispravljeno).** Prvobitna ispravka
   ("kopiraj CEO `specs/` kad postoji") u repou sa VIŠE feature-slug-ova bi
   Checker-u dala specs/ ZA SVE feature-e, ne samo za onaj iz task_spec.md —
   bez ikakve oznake koji je relevantan. Reproduktovano na sintetičkom repou
   (`specs/feature-a` + `specs/feature-b`, task_spec pominje samo
   `feature-a`). **Ispravljeno**: skripta sad grep-uje `task_spec.md` za
   `specs/<slug>` reference i kopira SAMO te poddirektorijume; ako
   task_spec.md ne pominje konkretan slug (stariji/ručno pisan task_spec),
   vraća se na staro ponašanje (kopiraj sve). Testirano na istom sintetičkom
   repou posle ispravke: bundle sada sadrži SAMO `specs/feature-a`.
2. **`cp -R` ne prati simboličke linkove (ispravljeno).** Ako je `specs/` (ili
   slug unutar njega) symlink — plauzibilno u monorepo/deljena-specs setupu —
   bundle bi završio sa samim symlink-om, ne sadržajem: Checker koji striktno
   poštuje "ne gledaj van bundle direktorijuma" bi dobio mrtvu referencu, ili
   bi (ako njegov sandbox ipak prati linkove) tiho probio izolaciju koju
   bundle mehanizam postoji da sprovede. Reproduktovano na sintetičkom repou
   (`specs` kao symlink na `real_specs/`). **Ispravljeno**: `cp -R` → `cp -RL`
   (prati linkove, kopira stvaran sadržaj). Testirano posle ispravke: bundle
   sadrži pravi direktorijum sa pravim sadržajem, ne symlink.
3. **`scratchpad.md`/`task_log.md` u stvarnom word-freq-bridge Maker run-u su
   ostali prazni template-i (nije bag, ali je nalaz o disciplini demoa).**
   Maker-ov Think→Act→Observe→Verify trag, koji ceo Maker-Checker dizajn
   pretpostavlja kao auditovanu radnu memoriju, u ovom konkretnom demo run-u
   nikad nije stvarno popunjen — samo placeholder skele. Ne utiče na ispravnost
   koda/testova, ali znači da se, za OVAJ run, ne može unazad proveriti šta je
   Maker stvarno probao. Nije popravljeno retroaktivno (bilo bi neiskreno
   izmišljati log) — samo iskreno zapisano ovde kao ograničenje ovog
   konkretnog demoa, ne kao dokazan bag u samom mehanizmu.
4. **Sitna higijena repoa** (nevezano za ispravku): necomitovan `dump.bin`
   (~2MB) i `.DS_Store` fajlovi rasuti/tracked-ovani kroz `loops/`,
   `sdd-bridge-test/`, `agentic-loop-demo/` i oba worktree-a — nije bag, samo
   zapisano da ne bi kasnije zbunilo neki novi chat zašto `git status` nije čist.

### Šta je urađeno po ovom review-u

- Obe stvarne slabosti ispravke (curenje van scope-a, symlink) **ispravljene
  i testirane** na sintetičkom repou (regresija na pravom
  `worktrees/word-freq-bridge` bundle-u takođe potvrđena — i dalje sadrži
  tačno `specs/word-freq/`, ništa više, ništa manje).
- Metodološka slabost (Tvrdnja 5, nema trajnog artefakta nezavisne Checker
  sesije) — **zapisana kao proces-lekcija**, ne nešto što se može retroaktivno
  popraviti: ubuduće, pun izlaz nezavisnog review/Checker subagenta treba
  sačuvati kao fajl (ne samo prepričati u prozi), da bude proverljiv unazad.
- Prazni scratchpad/task_log iz stvarnog run-a — **ostavljeni kako jesu**
  (retroaktivno punjenje bi bilo izmišljanje), samo iskreno zapisani kao
  ograničenje ovog demoa.
- Higijena repoa (dump.bin, .DS_Store) — **nije dirana**, van scope-a ove
  stavke; Buky treba da odluči da li i kada da se počisti.

---

## Otvoreno pitanje — nije odlučeno, treba Bukyjeva odluka

**Granularnost**: testirana je varijanta "ceo feature (T1-T5) = jedan
`task_spec.md` = jedan worktree spawn". Alternativa (netestirana): jedan
`task_spec.md` PO POJEDINAČNOM tasku iz `tasks.md` (T1 svoj worktree, T2 svoj,
itd.) — veća izolacija/paralelizam, ali tasks kao T2 ("dodaj stopwords
parametar") zavise od T1 (funkcija mora prvo postojati), pa bi zahtevalo
eksplicitno redosledno grananje (worktree za T2 mora početi OD T1-ove grane,
ne od `main`). Nije testirano jer sadašnji nalaz (cela grupa taskova kao jedan
spawn) već rešava osnovni, do sada nepostojeći problem — sitnija granularnost
je optimizacija, ne blokirajući nedostatak.

## Šta NIJE urađeno

- Ispravka (uključujući obe dopune iz Runde 2) je i dalje u radnoj kopiji
  (`agentic-loop-demo/agentic-loop-engineer/scripts/prepare-checker-bundle.sh`
  na Mac-u), **NIJE upakovana** u distributivni `.skill` fajl — isto stanje kao
  stavka #1, čeka zajedničko repakovanje.
- `sdd-bridge-test` repo i `worktrees/word-freq-bridge` su OSTAVLJENI na Mac-u
  (ne obrisani) — ovo je jedini konkretan, radni primer kako ceo lanac izgleda
  end-to-end, vredi da ostane kao referenca/template za sledeći pravi feature.
- Higijena repoa (dump.bin, .DS_Store) — nije dirana, van scope-a.

## Zaključak

Stavka #5 je testirana (Runda 1), pa nezavisno adversarijalno proverena
(Runda 2). Sve suštinske tvrdnje su potvrđene direktnim, samostalnim
testiranjem od strane reviewera (ne verovanjem prijavljenim rezultatima), uz
dva stvarna, dosad neprimećena nedostatka same ispravke (curenje specs/ van
scope-a kod više feature-a; `cp -R` ne prati symlink) — oba pronađena
testiranjem na sintetičkom repou, oba ispravljena i ponovo testirana (uklj.
regresiju na pravom word-freq-bridge bundle-u). Jedina tvrdnja koja ostaje na
nivou PLAUSIBLE (ne CONFIRMED) je da je Checker provera iz Nalaza 3 zaista bila
izolovana fresh-kontekst sesija — nema trajnog artefakta koji to dokazuje;
zapisano kao proces-lekcija za ubuduće (čuvati pune izlaze review subagenata
kao fajlove).

**Sledeće u dogovorenom redosledu: stavka #2 — regex guardrail bypass (alias, eval, env-var indirekcija, base64).**
