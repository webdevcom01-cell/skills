# Ojačavanje, stavka #1: pravi paralelizam (nikad ranije testirano)

**Kontekst:** iz dogovorenog redosleda 1 → 5 → 2 → 3 → 4. Sve dosadašnje probe
(dva live demoa + pilot) su bile **jedan agent, jedan worktree u datom trenutku** —
plan iz `agentic-loop-engineer-analiza.md` je izričito rekao da se pravi
paralelizam testira tek posle toga, i to nikad nije odrađeno. Ovo je prvi put.

**Metod:** napravljen jednokratan `parallel-test-repo` u `loops` folderu (kopija
`agentic-loop-engineer/scripts`+`templates`), pokrenuti STVARNO konkurentni pozivi
`spawn-worktree-agent.sh` (bash `&`/`wait`, ne simulacija), direktno na tvom
Mac-u preko device bridge-a. Testni repo je obrisan na kraju.

---

## Test 1 — dva RAZLIČITA task-id-a, konkurentno

**Rezultat: PROLAZI.** Oba spawn-a uspela, `registry.json` ispravno serijalizovao
upise preko `fcntl.flock()` (verzija 1 pa 2, bez gubitka), oba worktree-a čista i
izolovana (svaki vidi svoj `README.md`), grane ispravno imenovane. Ovo je prva
end-to-end potvrda (kroz pravi `spawn-worktree-agent.sh`, ne samo kroz izolovan
stress-test `registry_write.py`-a iz prethodnog kruga) da paralelno pokretanje
RAZLIČITIH zadataka radi kako treba.

## Test 2 — ISTI task-id, konkurentno (adversarijalno) — NAĐEN PRAVI BAG

Skripta nema NIKAKVU proveru "da li se ovaj task-id već pokreće" — jedina zaštita
je bila slučajna posledica git-ovog internog ref-lock mehanizma, nikad namerno
dizajnirana niti testirana.

**Na loops folderu (preko Cowork bridge-a):** jedan od dva konkurentna pokušaja
je ostavio **osiroteli worktree** — postoji u `git worktree list`, postoji na
disku, ali NEMA unos u `registry.json` (nikad nije stigao do koraka 4) — nevidljiv
za sopstvenu evidenciju sistema. Uzrok: cleanup-trap je pokušao `git worktree
remove`/`rm -rf`, ali je bridge odbio brisanje ("Operation not permitted") jer
Cowork podrazumevano blokira brisanje u povezanom folderu dok se eksplicitno ne
odobri — ovo je zaštita bridge-a, ne mana tvog koda.

**Kontrolni test na običnom fajl-sistemu** (`/tmp`, brisanje dozvoljeno): ista
trka — git-ov interni ref-lock je uhvatio sudar, OBA pokušaja su čisto pukla, bez
siročeta. Znači: čist pad na tvom terminalu je verovatnije ishod nego korupcija —
ali dalje stoji da **ništa u skripti namerno ne sprečava dupli konkurentni spawn**,
oslanjanje na git-ov interni lock je bilo nenamerno i netestirano, i na bridge-u
(gde stvarno i radiš deo ovog posla) taj oslonac vidljivo puca.

## Dodatna potvrda — port izolacija nikad implementirana

`agentic-loop-engineer-analiza.md` (Domen 1) eksplicitno traži dodelu port-range-a
po task-id-u za zadatke koji dižu dev server. Pretraga (`grep -rni port`) kroz
ceo isporučeni paket potvrđuje: **ovo postoji samo kao rečenica u analizi, nikad
nije ušlo u kod.** Nije relevantno za sadašnje demo zadatke (ne dižu server), ali
je stvaran, dosad neprimećen razmak između analize i implementacije.

---

## Ispravka (primenjena i retestirana)

Dodata atomična rezervacija task-id-a PRE bilo kakve git operacije:

```bash
CLAIM_DIR="${REPO_ROOT}/.agent-orchestrator/claims"
mkdir -p "${CLAIM_DIR}"
if ! mkdir "${CLAIM_DIR}/${TASK_ID}" 2>/dev/null; then
  echo "GREŠKA: task-id '${TASK_ID}' je već zauzet..." >&2
  exit 1
fi
release_claim() { rmdir "${CLAIM_DIR}/${TASK_ID}" 2>/dev/null || true; }
```

`mkdir` je atomičan na POSIX fajl-sistemima — gubitnik trke sad otkazuje ODMAH,
PRE nego što dotakne git, bez ijedne git operacije, bez zavisnosti od toga da li
je brisanje dozvoljeno. `release_claim` se zove i u `cleanup_on_failure` trap-u i
posle uspešnog završetka.

**Retest posle ispravke (isti scenario, isti bridge):** jedan proces odbijen
odmah, čisto, sa jasnom porukom, BEZ ijedne git operacije; drugi proces uspeo
potpuno (registry verzija 3, ispravno serijalizovano posle Test 1). Nula
siročadi, nula git lock-contention poruka (pošto samo jedan proces ikad dotakne
git za dati task-id).

---

## Šta NIJE urađeno u ovom krugu (svesno, ne propust)

- **Port izolacija ostaje neimplementirana.** Predlažem da se ne gradi
  unapred za hipotetički slučaj — dodati kad se prvi put pojavi pravi zadatak
  koji diže dev server/test-runner na portu.
- **Ispravka je primenjena u radnoj kopiji** (`agentic-loop-demo/agentic-loop-engineer/scripts/spawn-worktree-agent.sh`
  na tvom Mac-u, ona koju demo/pilot koristi) — **NIJE još upakovana** nazad u
  distributivni `agentic-loop-engineer.skill` fajl. To ide preko tvog postojećeg
  `package_skill.py` workflow-a (isti kao u `PAKETOVANJE-finalni-izvestaj.md`) —
  radim to na tvoj signal.

## Runda 2 — nezavisna adversarijalna provera (Checker), pa dodatne ispravke

Na Bukyjev zahtev, pre prelaska na stavku #5, pokrenuta je potpuno nezavisna
provera (svež subagent bez konteksta o gorenavedenom radu, isti obrazac kao
`VERIFIKACIJA-treci-krug.md`) — nije verovala nijednoj tvrdnji na reč, sama je
čitala kod i sama ponovo izvodila testove preko device_bash na istom uređaju.

**Nalaz 1 — Test 2 gore POTCENJUJE ozbiljnost.** Nezavisna provera je testirala
NEISPRAVLJENU verziju (iz `.skill` fajla) i pokazala da ishod nije samo "nevidljivo
siroče" nego **stvarna korupcija**: pošto ime grane koristi `$(date +%s)`
(rezolucija sekunde), dva konkurentna spawn-a ISTOG task-id-a u istoj sekundi mogu
dobiti IDENTIČNO ime grane; gubitnik trke, u svom cleanup-u, može obrisati granu
koju je POBEDNIK već preuzeo — pobednikov worktree ostaje registrovan kao uspešan,
ali sa pokvarenim HEAD-om i **nestalim fajlovima**. Ovo je gora, ne blaža,
manifestacija istog osnovnog nedostatka (nema dedup zaštite) nego što je prvobitno
opisano — retroaktivno ispravljeno ovde.

**Nalaz 2 — zaglavljen claim posle `kill -9`/pada procesa (nov, nepomenut rizik).**
Skripta trap-uje samo `ERR`, ne signale — `kill -9` posle uspešnog claim-a a pre
`release_claim` ostavlja claim TRAJNO zaglavljenim, bez automatskog oporavka.
**Ispravljeno**: claim sad nosi PID + vreme preuzimanja; sledeći pokušaj proverava
da li je vlasnik i dalje živ (`kill -0`) i da li je claim mlađi od 1h — ako nije,
zaostali claim se preuzima automatski, uz jasnu poruku.

**Nalaz 3 — sitan race u pisanju `.git/info/exclude`** kod dva RAZLIČITA task-id-a
konkurentno (provera-pa-append nije atomična) — bezopasno funkcionalno (git
ignore radi i sa dupliranim linijama), ali stvaran race. **Ispravljeno**: isti
`mkdir`-lock obrazac (ne `flock` — nije garantovano dostupan na macOS-u, gde Buky
stvarno pokreće ovo van bridge-a; `mkdir`/`kill -0`/`date +%s` su POSIX-portabilni
bez spoljne zavisnosti).

**Nalaz 4 — samo-otkrivena regresija UNUTAR ispravke za Nalaz 2** (isti obrazac kao
`VERIFIKACIJA-treci-krug.md` C.2: i ispravka napravljena tokom rigorozne provere
može uneti novu grešku). Prva verzija PID+vreme provere je imala TOCTOU prozor:
`mkdir` (pobednik) uspeva, ali `pid`/`claimed_at` fajlovi se pišu POSLE, kao dva
odvojena koraka. Gubitnik koji proveri claim BAŠ u tom prozoru je čitao
prazan/nepostojeći `pid` i stari kod je to (pogrešno) tretirao kao "zaostalo" pa
REKLAMIRAO tuđi, aktivan claim — oba procesa su onda nastavljala do git-a
istovremeno, ISTA korupcija koju je claim trebalo da spreči. Otkriveno sopstvenim
retestom (regresija se pojavila na prvom ponovnom pokretanju posle "uspešnog"
prvog testa), ne od strane nezavisne provere. **Ispravljeno**: logika je sad
fail-CLOSED — claim se reklamira SAMO kad su i `pid` i `claimed_at` prisutni,
brojčani, I dokazano mrtvi/prestari; ako podaci nedostaju (claim je "u fazi
preuzimanja"), pokušaj se čisto odbija, ne reklamira.

**Stress-retest posle svih ispravki**: 15 uzastopnih rundi konkurentnog spawn-a
ISTOG task-id-a (svaka sa svežim task-id-om) — u svih 15, tačno jedan pobednik,
`README.md` netaknut, nula korupcije. Ponovljeni ciljani testovi: mrtav PID →
ispravno preuzet; živ mlad PID → ispravno odbijen; prazni/nepostojeći meta podaci
(simulacija TOCTOU prozora) → ispravno odbijen bez reklamiranja.

**Nalaz 5 — zaostalo smeće iz RANIJE runde** (ne iz ovog rada): u
`worktrees/worktrees/cirilica-history-cleanup` postoji neregistrovan, `prunable`
worktree iz ranijeg demoa (~13. septembar), ista vrsta problema kao ono što je
ovde ispravljeno, samo starije. Nije dirano — Buky treba da odluči da li da se
počisti.

## Zaključak

Stavka #1 (paralelizam) je testirana, i to dvoslojno: prvo sopstvenim testovima,
zatim nezavisnom adversarijalnom proverom koja je otkrila da je originalni bag
ozbiljniji nego što je prvobitno opisano, plus dva dodatna, manja concurrency
propusta. Sva četiri nalaza (uključujući jedan koji je moja sopstvena ispravka
unela usput) su ispravljena i ponovo testirana, sa dokazom u ovom dokumentu —
ne samo pročitana kao "izgleda ispravno". Port izolacija ostaje svesno
neimplementirana (nema još pravog zadatka koji je zahteva). Distributivni
`.skill` fajl **i dalje nije ažuriran** — sve ispravke su samo u radnoj kopiji
na Mac-u (`agentic-loop-demo/agentic-loop-engineer/scripts/spawn-worktree-agent.sh`);
repakovanje čeka Bukyjev signal.

**Sledeće u dogovorenom redosledu: stavka #5 — most `sdd-workflow` → `agentic-loop-engineer` (nikad testiran).**
