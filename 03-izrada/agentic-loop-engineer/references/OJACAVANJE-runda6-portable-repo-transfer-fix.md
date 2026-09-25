# Ojačavanje runda 6: `portable-repo-transfer.sh` cwd-zavisnost + inkrementalni transfer

**Kontekst:** `scripts/portable-repo-transfer.sh` je dodat u rundi 5 (`export`/`import`
podkomande preko `git bundle`) da reši nalaz iz DEPLOY runde 8 — `tar`-ovanje jednog git
worktree direktorijuma ne proizvodi prenosiv repo, jer je worktree-ov `.git` tekstualni
fajl-pokazivač na apsolutnu putanju koja na drugoj mašini ne postoji. Skript je uveden i
dokazan uživo u rundi 5, u dva odvojena okruženja (cloud sandbox i Buky-jev Mac).

Ova ojačavanja dolaze iz prve PRAVE produkcione upotrebe tog skripta (QR Kod Menadžer pilot,
runde 10-11), ne iz sintetičkog testa — dva nalaza koja su se ponovila više puta uživo.

## Nalaz #1 [OZBILJAN] — `git bundle verify` cwd-zavisnost, lažni negativni nalaz

**Simptom:** `export` i `import` prijavljuju `GREŠKA: git bundle verify je pao` ILI direktno
`fatal: not a git repository (or any of the parent directories): .git`, iako je sam `.bundle`
fajl potpuno ispravan.

**Root cause:** `git bundle verify <fajl>` (kao i skoro svaka `git` potkomanda) zahteva da se
komanda izvrši IZNUTRA nekog git repoa — ne zato što bi mu bila potrebna bilo koja sadržina
tog repoa (naš bundle je uvek pun/samostalan, bez prerequisite komita), nego zato što `git`
CLI to zahteva strukturno, bez obzira na potkomandu. Originalna verzija skripta je pozivala
`git bundle verify "$OUT_FILE"` golo, bez `-C` i bez ikakve pretpostavke o pozivnom cwd-u —
radilo je SAMO ako je pozivalac slučajno bio unutar nekog repoa.

**Viđeno uživo (ne teorijski):** tačno ovaj bag, tri odvojena puta - `import` u rundi 10,
`export` DVA puta u rundi 11. Svaki put je trošio vreme na dijagnozu jer je poruka
("bundle je oštećen") navodila na pogrešan trag (integritet fajla), a stvarni problem je
bio isključivo odakle je skript pozvan.

**Ispravka:** nova `bundle_verify_anywhere()` funkcija pravi JEDNOKRATAN, prazan scratch git
repo (`mktemp -d` + `git init -q`), izvršava verify UNUTAR NJEGA (`git -C "$scratch" bundle
verify ...`), pa scratch briše — rezultat više ne zavisi od pozivnog cwd-a. `export` i
`import` sada oba koriste ovu funkciju.

**Dokaz (ova runda, ne pretpostavka):** `export`/`import` pozvani iz namerno praznog,
NE-git direktorijuma (`/tmp/prt-test/plain-cwd`, potvrđeno `git rev-parse --git-dir` puca
tamo) - oba prošla čisto, gde bi stara verzija pukla.

## Nalaz #2 [FUNKCIONALNI GAP] — nema inkrementalnog transfera u postojeći repo

**Simptom:** `import` radi ISKLJUČIVO fresh `git clone` u NEPOSTOJEĆI ciljni direktorijum -
za drugi/treći krug promena (repo na cilju već postoji od prvog `import`-a), `import` samo
odbija sa "već postoji".

**Viđeno uživo:** u rundi 11, ovo je zaobiđeno RUČNO, DVA puta, istom sekvencom
(`git bundle verify` pa `git fetch <bundle> <grana>:refs/tmp-incoming` pa
`git merge --ff-only refs/tmp-incoming` pa `git update-ref -d refs/tmp-incoming`) - ispravno,
ali van skripta, pa nedokumentovano i podložno grešci pri sledećem ponavljanju.

**Ispravka:** nova `sync <fajl.bundle> <ciljni-dir> [grana]` potkomanda automatizuje tačno tu
sekvencu:
- Zahteva da ciljni dir VEĆ bude pravi git repo (jasna greška ako nije - uputi na `import`).
- Auto-detektuje granu iz bundle-a (`git bundle list-heads`) ako nije eksplicitno data.
- Fetch u JEDINSTVENI privremeni ref (`refs/tmp-incoming-<pid>-<timestamp>`, da se ne kosi
  sa paralelnim sync pozivima na isti cilj).
- Fast-forward-only merge; na odbijanje (prava divergencija), ciljni repo ostaje NETAKNUT i
  privremeni ref se svejedno briše - nikad tiho rebase/force.
- Čišćenje privremenog ref-a garantovano preko `trap ... EXIT`, i na uspeh i na neuspeh.

**Dokaz (ova runda):**
1. `sync` sa auto-detekcijom grane, iz namerno ne-git pozivnog cwd-a: 2 nova komita prenesena
   fast-forward, tačan broj (`+2 novi(h) komit(a)`), tačan pre/posle SHA u izlazu.
2. Namerno izazvana divergencija (lokalni commit u ciljnom repou koji bundle nema) + novi
   commit u izvoru + `sync`: odbijeno sa jasnom porukom, exit kod 1, ciljni `git log`
   PRE i POSLE pokušaja bit-za-bit identičan (potvrđeno string-poređenjem), privremeni ref
   obrisan (potvrđeno `for-each-ref` posle, prazno).
3. `bash -n` sintaksna provera prošla; `--help`/bez-argumenata izlaz prikazuje sve tri
   potkomande.

## Napomena o poreklu ove ispravke

Ova runda je urađena u cloud sesiji čija je lokalna sync-kopija `agentic-loop-engineer`
skilla zastarela u odnosu na ono što je stvarno instalirano (rundom 5 dodat
`scripts/portable-repo-transfer.sh` i originalni `references/OJACAVANJE-stavka5-...md` nisu
bili prisutni u toj sync-kopiji). Sam skript je rekonstruisan iz kopije koja je u ISTOJ sesiji
ranije stvarno korišćena za pravi DEPLOY transfer (QR Kod Menadžer, runda 10-11) - dakle
autentičan, produkcijom-dokazan sadržaj, ne rekreacija iz sećanja - ali originalni
`OJACAVANJE-stavka5-portable-repo-transfer.md` tekst (tačan dokaz sa cloud/Mac testova iz
runde 5) nije bio dostupan da se sačuva reč-po-reč; ovaj dokument pokriva istu materiju iz
runde 5 ukratko (u sekciji "Kontekst" iznad) plus pune detalje za ISPRAVKE iz runde 6. Ako
originalni `OJACAVANJE-stavka5-...md` fajl postoji na Buky-jevom Mac instaliranom skillu,
vredi ga zadržati uz ovaj (ne brisati) - ne dupliraju se, stavka5 pokriva rundu 5 nalaze
(worktree-tar problem + HEAD-u-bundle problem), ovaj fajl pokriva rundu 6 nalaze
(cwd-zavisnost + sync).
