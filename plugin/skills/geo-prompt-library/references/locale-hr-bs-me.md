# SR → HR/BS/ME transformacija

Koristi ovaj fajl kad je `locale` ulazni parametar `hr-HR`, `bs-BA`, ili kad `sr-ME` treba varijantu bližu crnogorskom standardu. Četiri sistemska pravila nose više ROI-ja od bilo koje leksičke liste — primeni ih prva, pre reči-po-reč zamena.

Ova pravila su i osnova G14 gate-a (`locale čistoća za HR/BS` u SKILL.md) — G14 proverava odsustvo SR markera (stop-liste ispod) kad je `locale.primary` `hr-HR` ili `bs-BA`.

## Sadržaj

1. [4 sistemska pravila](#4-sistemska-pravila)
2. [Meseci i transkripcija imena](#meseci-i-transkripcija-imena)
3. [Leksička mapa — sekundarna, delom nepotvrđena](#leksička-mapa--sekundarna-delom-nepotvrđena)

---

## 4 sistemska pravila

### 1. `-irati` (HR/BS) vs `-isati`/`-ovati` (SR/ME)

Najveći pojedinačni ROI — potpuno automatizovano, pogađa čitave klase glagola.

| SR/ME | HR/BS |
|---|---|
| organizovati | organizirati |
| informisati | informirati |
| kontrolisati | kontrolirati |
| definisati | definirati |

G14 stop-lista (`SR_ISATI_OVATI_STOPLIST` u `scripts/validate_library.py`) trenutno pokriva ove 4 osnove (i njihove oblike) — nije iscrpna, proveri protiv stvarnog teksta pre nego što je tretiraš kao potpunu.

### 2. Infinitiv (HR) vs `da` + prezent (SR/ME)

Menja površinski oblik velikog dela prirodnih promptova, ne samo pojedinačne reči.

- SR/ME: "želim **da nađem** dobavljača"
- HR: "želim **naći** dobavljača"

Za HR generisanje: izbegavaj `da + prezent` konstrukcije, koristi infinitiv gde god je gramatički prirodno.

### 3. Ijekavica (HR/BS/ME) vs ekavica (SR)

| Ekavica (SR) | Ijekavica (HR/BS/ME) |
|---|---|
| vreme | vrijeme |
| prevoz | prijevoz |
| cena | cijena |

⚠️ **`cijena`/`cena` pogađa celu `pricing` kategoriju** — svaki HR/BS pricing upit koji koristi "cena" umesto "cijena" je odmah locale leak. G14 stop-lista (`SR_EKAVICA_STOPLIST`) uključuje `cena/cene/cenovnik/cenom` upravo zbog ove kategorije.

### 4. Upitna partikula

HR propisuje `Možeš li?` (glagol + li, bez "da"). SR dopušta i `Da li…` konstrukciju. **`Da li` je jak srpski registar-marker** — G14 ga hvata kao samostalan signal (`"da li" in text_lower` u skripti), nezavisno od ostalih pravila.

---

## Meseci i transkripcija imena

**Meseci:** SR (`januar`, `februar`, ...) razlikuju se od HR (`siječanj`, `veljača`, ...). G14 stop-lista (`SR_MONTHS`) hvata srpske oblike u HR/BS tekstu.

**Transkripcija stranih imena — kritično za downstream parsing, ne samo stil:** SR fonetski transkribuje strana imena (`Microsoft` → `Majkrosoft`), HR zadržava original. Ovo ide u `company.aliases` (vidi `schema.md`) bez obzira na locale, jer downstream skill koji parsira AI odgovore mora prepoznati OBA oblika da bi izmerio pominjanje brenda ispravno.

---

## Leksička mapa — sekundarna, delom nepotvrđena

Manji ROI od 4 sistemska pravila iznad. **Deo ovih parova nije potvrđen u dohvaćenom izvoru pri istraživanju brief-a — tretiraj kao nepotvrđeno, proveri pre nego što ga koristiš kao pravilo, ne kao činjenicu.**

| SR | HR |
|---|---|
| firma | tvrtka |
| preduzeće | poduzeće |
| hiljada | tisuća |
| kancelarija | ured |

Ovaj fajl namerno ne pokušava biti iscrpan rečnik — 4 sistemska pravila iznad hvataju većinu površine teksta automatski; leksička mapa je dopuna za specifične imenice koje sistemska pravila ne dotiču.
