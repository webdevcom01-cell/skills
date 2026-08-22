# Eval set — prospect-discovery

Ovo je **prvi eval set** za skill `prospect-discovery` (faza 05-isporuka). Skill dosad nije imao evale; ovaj set od 6 slučajeva pokriva pravila iz `SKILL.md` koja su najlakše pogrešiti — pragove, grananja i razlike između sličnih stanja koje skill eksplicitno navodi.

## Šta set testira

Svaki od 6 slučajeva cilja jedno konkretno, eksplicitno pravilo iz `SKILL.md`:

1. **Step 0 — rad bez nadzora ne sme da blokira posao.** Kada korisnik nije dostupan pre prvog fetch-a, agent mora nastaviti (ne čekati/prekinuti) i staviti oba Step 0 pitanja na vrh *covering note*-a, rešena pre zakazivanja poziva — ne pre postojanja dosijea. Lako se meša "gde" (dosije vs covering note) i "kada" (pre dosijea vs pre poziva).
2. **Step 1 — nesiguran identitet je fatalan, nedostupan registar je samo gap.** "Dva verovatna poklapanja" zaustavljaju rad; nedostupan/plaćen/blokiran registar ne zaustavlja rad (degraded mode: nastaviti na trgovačkom identitetu, obeležiti NOT FOUND). Ova dva stanja se lako pomešaju jer oba "izgledaju" kao problem sa registrom.
3. **Step 1b — nazivi polja u intake bloku ostaju na engleskom bez obzira na jezik paketa.** Jedini izuzetak od pravila "piši na jeziku poziva" — lako se previdi jer je suprotan opštem principu istog koraka, a greška (prevod naziva polja) tiho kvari handoff ka `team-enablement-program`.
4. **Step 3 — checker se pokreće na tri fajla, ne na jedan, i exit 0 ≠ sadržajno tačno.** `check_sources.py --strict` ide na dosije, PA na proposal skeleton, PA na intake blok — redosled i obuhvat se lako preskoče. Dodatno, proposal skeleton je najskuplji za grešku jer je jedini client-facing.
5. **Retention linija — dvograno pravilo sa konkretnim brojem (90 dana).** Linija mora imati i pravilo ("90 dana od poziva") i izračunat rezervni datum ("istraživanje + 90 dana") jer poziv u trenutku pisanja nije zakazan — i mora ići u svih pet fajlova, ne samo dosije.
6. **Adverse findings — eskalacija je obavezna, nedostupnost korisnika NE izuzima ovo pravilo.** Za razliku od Step 0, gde bez-nadzorni rad znači "nastavi i zapiši za kasnije", ovde enforcement/sanctions/insolvency nalaz zaustavlja istraživanje i postaje pitanje za korisnika — čak i kad korisnik trenutno nije dostupan. Ovo je namerno postavljeno odmah posle slučaja 1 da se testira da li agent generalizuje "kad nema korisnika, samo nastavi" tamo gde to pravilo eksplicitno ne važi.

## Šta set namerno NE testira

- **Kvalitet samog istraživanja** (da li je agent pronašao tačne činjenice o pravoj kompaniji) — skill radi sa živim web pretragama i spoljnim registrima kojima ovde nemamo pristup, pa nijedan eval ne traži da agent stvarno nešto istraži. Svaki prompt je samostalan hipotetički scenario sa svim potrebnim brojevima/činjenicama već datim, rešiv čistim rezonovanjem iz `SKILL.md`.
- **`references/*.md` fajlove i `scripts/check_sources.py` sadržaj** — u ovom repo snapshotu postoji samo `SKILL.md` (nema `references/` ni `scripts/` poddirektorijuma), pa set ne tvrdi ništa o tačnom formatu koji ti fajlovi propisuju, samo o onome što `SKILL.md` sam kaže o njima (npr. da checker treba pokrenuti na tri fajla, redosled).
- **Format/strukturu samih pet izlaznih fajlova** (tačan Markdown izgled dosijea, agende itd.) — to je opisano u `references/dossier.md` i sličnim fajlovima, van dosega ovog seta.
- **Nejasnu/kontradiktornu rečenicu u Step 7** ("Two of the four files are internal and two are client-facing", što se ne poklapa jasno sa tabelom od pet redova) — namerno izostavljeno jer nismo sigurni da li je to namerna formulacija ili omaška u samom `SKILL.md`, pa bi eval izgrađen na tome testirao dvosmislenost teksta, a ne jasno pravilo.

## Format

Isti format kao `skill-creator-pro/evals/evals.json`: svaki slučaj ima `id`, `prompt` (samostalan scenario), `expected_output` (tačan zaključak + citat/parafraza pravila iz `SKILL.md`) i `expectations` (lista konkretnih, proverljivih tvrdnji o tome šta agentov odgovor mora da sadrži — pogodno za automatsko ili ručno ocenjivanje).

## Ograničenje i sledeći korak

Ovaj set proverava da li agent **zna i ispravno primenjuje** pravila kad mu se scenario servira gotov — ne proverava da li agent **sam prepoznaje** kada je, recimo, identitet kompanije dvosmislen usred stvarnog istraživanja sa pravim (bučnim) izvorima. Sledeći korak bi bio drugi eval sloj, sa simuliranim/fixture web sadržajem, koji testira ponašanje skilla u punom end-to-end toku, uključujući da li agent uopšte primeti edge case pre nego što se pravilo mora primeniti.
