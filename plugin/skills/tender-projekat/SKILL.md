---
name: tender-projekat
description: >-
  Radni protokol i kontinuitet projekta "tender-sistem" — anti-halucinacionog sistema za
  praćenje tendera za vodu/kanalizaciju u Srbiji (Portal javnih nabavki, TED, EBRD ECEPP,
  planovi nabavki). Use this skill whenever the user mentions the tender project in any
  form: "tender projekat", "tenderi", "javne nabavke", "Portal javnih nabavki", "stigao
  je email sa Portala", "uradi analizu kompletnosti", "nova verzija isporuke", "nastavi
  tender projekat", "proveri tendere", "GM tender", "Stara Pazova", "isporuka", or wants
  to continue, check, extend, or hand over the Serbian water/sewerage tender monitoring
  system — even if the request seems small. The skill carries the project's verification
  constitution and recurring workflows; skipping it loses the discipline that caught
  every real bug so far.
---

# Tender-projekat — radni protokol

## Šta je ovo

Projekat "tender-sistem": Python sistem koji za građevinsku firmu (klijenta korisnika)
prati tendere za vodu/kanalizaciju u Srbiji na svim kanalima finansiranja i garantuje
dve stvari — nijedan tender/izmena se ne propušta, i nijedna informacija nije izmišljena
(svaki uslov nosi doslovan citat iz izvora). Sistem NE donosi Go/No-Go odluke — čovek
odlučuje. Korisnik (buky) nije tenderski ekspert — objašnjavaj jasno, bez žargona.

## PRVI KORAK U SVAKOJ SESIJI — pročitaj stanje, ne pretpostavljaj

Izvor istine je folder `Desktop/tender` na korisnikovom računaru (preko device bridge-a;
u kontejneru kopija može biti ZASTARELA ili ne postojati). Pre bilo kakvog rada pročitaj:

1. `UPUTSTVO.md` — trenutna verzija sistema, raspored, komande
2. Najnoviji `Izvestaj_*.md` (po datumu izmene) — šta je poslednje urađeno
3. Najnoviju `Analiza_*.md` / `Portal_status_*.md` — otvorene stavke

Jedina važeća isporuka je NAJNOVIJI `isporuka_vX.Y.Z.zip` — sve starije verzije su
prevaziđene. Ako kontejner nema kod projekta, otpakuj taj zip i radi nad njim.

## Ustav projekta (nepregovorljivo — korisnik ovo traži u skoro svakoj poruci)

1. **Svaka tvrdnja proverena PRE implementacije** — izvršno kad god je moguće (pokreni
   kod, pročitaj živi izvor, izlistaj folder), nikad iz sećanja. Ako se ne može
   proveriti, tvrdnju označi kao NEPROVERENU — to je legitiman, pošten ishod.
2. **Fail-closed**: nejasno → alarm/NA_PREGLED, nikad tiho odbacivanje. Prazan
   dokaz/citat NIJE dokaz.
3. **Negativan nalaz je nalaz** — "traženo, nije nađeno" se zapisuje sa opsegom pretrage.
4. **Nikad lažno umirenje**: "nema novih" sme da se kaže SAMO za stvarno proveren kanal;
   neproveren kanal se prijavljuje kao NEPROVEREN/KVAR.
5. **Svaki deliverable** ide korisniku (SendUserFile) I u tender folder na disk
   (device_commit_files). Ako je veza sa računarom pukla, reci to i snimi kad se vrati.
6. **Greška se priznaje otvoreno** i ispravlja sa regresijskim testom — u ovom projektu
   je i sopstvena pogrešna tvrdnja nalaz (presedan: broj očekivanja "178" ispravljen u
   mašinski izbrojanih 166).

## Mapa projekta

| Šta | Gde |
|---|---|
| Jedina važeća isporuka | `isporuka_vX.Y.Z.zip` (najnoviji; kod + dosijei + planovi + skripte automatike) |
| Priručnik | `UPUTSTVO.md` (koren foldera i koren zip-a) |
| Kod | `tender_sistem/` — 12 modula; ulazna tačka `pokreni.py` (kanali+zdravlje+SHA-256+izveštaj) |
| Testovi | `tender_sistem/dod_test*.py` — 11 paketa; broj očekivanja PREBROJ pre citiranja (raste; 15.08.2026: 170) |
| Email obaveštenja | folder `emailovi/` pored paketa — .txt emailovi koje parser pokupi |
| Dnevni izveštaj | `izvestaji/izvestaj_poslednji.html` + `dnevni_log.txt` |
| Istorija projekta | svi `*.md` u tender folderu — NE brisati |
| Dnevna automatika | launchd/cron skripte u paketu + Cowork zakazani zadatak "Tender — dnevna provera Portal obaveštenja (Gmail)" |

## Ponovljivi tokovi

### "Uradi analizu kompletnosti" (korisnikov ritual — svaka dosadašnja je našla stvarne nalaze)
1. Baseline: svi dod_test paketi ×2 zaredom (ponovljivost je deo garancije).
2. Izaberi uglove koje PRETHODNE analize nisu pokrile (pročitaj postojeće Analiza_*.md).
3. Svaku sumnju dokaži IZVRŠNO (simulacija, živi upit, grep) — bez dokaza nema nalaza.
4. Nalazi po ozbiljnosti (OZBILJNO/SREDNJE/MALO), svaki sa reprodukcijom i posledicom.
5. Ispravke tek uz saglasnost korisnika, UVEK sa regresijskim testom.
6. Izveštaj (Analiza_*.md) → korisniku + tender folder.

### "Stigao je email sa Portala"
1. Gmail pretraga OBAVEZNO sa `in:anywhere` — Portal emailovi završavaju u SPAM-u
   (potvrđeno 14.08.2026); spam se briše posle 30 dana, zato je hitno.
2. `get_thread` (PLAIN_TEXT) → sačuvaj doslovan tekst kao .txt u `emailovi/` (preko
   device bridge-a, ili uputi korisnika).
3. Parser `email_obavestenja.py` veže događaj za tender po ID-u iz linka
   `tender-eo/<ID>` i klasifikuje; najava izmene dokumentacije = MENJA_SPREMNOST.
4. Ako je stigla IZMENA dokumentacije: nova dokumenta se preuzimaju RUČNO kroz browser
   (na zahtev, nikad pozadinski), pa Sloj A diff protiv prethodne verzije.

### "Nova verzija isporuke"
1. Svi testovi ×2 → zeleno.
2. Simulacija čiste mašine: otpakuj zip u /tmp, `env -i` pokreni sve testove — tek to
   dokazuje da paket radi kod klijenta.
3. Zip `isporuka_vX.Y+1.zip` (UPUTSTVO + kod + dosijei + planovi + skripte automatike;
   bez .db i __pycache__) → SendUserFile + tender folder → reci korisniku TAČNO koje
   stare fajlove briše (brisanje na uređaju ne možeš ti — samo korisnik, ili `mv`).

## Ograničenja koja se NE krše

- Portal javnih nabavki: isključivo ručno/na zahtev kroz browser — NIKAD zakazano
  skrapovanje (uslovi korišćenja). Email obaveštenja su legalni automatski kanal.
- Kredencijale unosi ISKLJUČIVO korisnik; nikad ih ne tražiti ni čuvati.
- Bez plaćenih alata — sve besplatno/samostalno izgrađeno.
- Ne obećavati funkcije bez izvršnog dokaza da rade.

## Kontekst koji zastareva (proveri, ne prepisuj slepo)

Stanje na dan 15.08.2026 — pri čitanju OBAVEZNO proveri šta se promenilo: praćeni
tenderi GM 62/26 (Portal ID 385190, rok 24.08.2026 10:00, najavljena izmena
dokumentacije) i SP 404-28/26 (ID 382894, čeka odluku); Portal nalog буку007 odobren;
preostalo: KfW/GTAI kanal (čeka MyGTAI nalog), profil firme (čekaju klijentovi dokazi),
dugme "proveri Portal sada", OCR keširanje.
