# Srpski jezički sloj (Faza 5)

Ovaj fajl je referenca za formulisanje SR upita (`sr-RS`, `sr-ME`). Za HR/BS transformaciju vidi `locale-hr-bs-me.md`.

## Sadržaj

1. [Konverzacioni oblik, ne keyword string](#1-konverzacioni-oblik-ne-keyword-string)
2. [Dužina](#2-dužina)
3. [Padeži — obeležena hipoteza](#3-padeži--obeležena-hipoteza)
4. [Mešani kod za tech/B2B](#4-mešani-kod-za-techb2b)
5. [Modifikatori — tabela](#5-modifikatori--tabela)
6. [Šta nikad ne sme u finalni tekst](#6-šta-nikad-ne-sme-u-finalni-tekst)

---

## 1. Konverzacioni oblik, ne keyword string

AI prompt ≠ Google upit. Ljudi ne kucaju "crm cena beograd" u ChatGPT — pišu punu rečenicu: "koliko košta CRM ako sam u Beogradu". Piši sve SR upite kao pun rečenični, konverzacijski oblik sa ispravnim padežima, ne kao lančić keyword-ova.

Dobro: "koja je najbolja ordinacija za implantologiju u Novom Sadu"
Loše: "najbolja ordinacija implantologija Novi Sad"

## 2. Dužina

5–16 reči (G9 gate proverava 4–20, ali cilj je 5–16). Izvor: Nectiv — ChatGPT-generisani search upiti prosečno 5.48 reči; Peec — fan-out upiti rastu sa ~6 na ~12 reči kroz 4 meseca praćenja; korisnički promptovi u AI chat-u su znatno duži od klasičnih Google upita. Raspon 5–16 pokriva realan opseg bez guranja u ekstremne kratke ili duge formulacije.

## 3. Padeži — obeležena hipoteza

**Nema objavljene studije o padežima u srpskim AI-search upitima.** Preporuka da se piše u ispravnom rečeničnom padežu ("u Novom Sadu", ne "Novi Sad" kao golo ime) je obrazložena hipoteza — prirodnije zvuči korisniku, konzistentno je sa "pun rečenični oblik" pravilom iz sekcije 1 — ali nije merena. Ne prezentuj ovo korisniku kao dokazanu činjenicu. Vidi `research-basis.md` za punu listu praznina.

## 4. Mešani kod za tech/B2B

Za tech/B2B vertikale koristi **mešani kod**: srpski rečenični okvir + engleski termin kategorije. Primer: "kako da odaberem CRM za mali biznis", "najbolji project management alat za male timove".

Zašto: anglosrpski je dokumentovan registar u regionu (Netokracija — anglicizmi u savremenom poslovanju), ne veštački konstrukt. Prevođenje cele liste na čist srpski ("softver za upravljanje odnosima sa klijentima" umesto "CRM") sistemski promašuje kako ljudi stvarno pišu.

**Upozorenje modelu koji piše upite:** ne meri "koliko je upit srpski" po broju srpskih REČI — mešani kod prirodno ima više engleskih sadržajnih reči (imenice kategorije, imena proizvoda) nego srpskih. Meri po prisustvu srpskih FUNKCIJSKIH reči (vidi tabelu ispod i G8 u SKILL.md) — "najbolji project management alat za male timove" ima samo jednu srpsku sadržajnu reč ("za") ali je nesumnjivo srpska rečenica.

## 5. Modifikatori — tabela

| EN | SR | Napomena |
|---|---|---|
| best | `najbolji/najbolja/najbolje` | mora se slagati u rodu i broju sa imenicom |
| price / how much | `cena` (jedan artikal) \| `cene` (tržišni pregled) \| `cenovnik` \| `koliko košta` | tri različita intenta, ne sinonimi — ne biraj proizvoljno |
| reviews | `recenzije`, `utisci`, `ocene` | |
| experiences | `iskustva`, `[brend] iskustva` | nema čist engleski ekvivalent, izuzetno frekventno u regionu |
| recommendation | `preporuka`, `preporučite mi` | `preporučite mi…` je prirodan imperativ za AI prompt |
| which is better | `koji je bolji`, `šta je bolje` | |
| X vs Y | `X ili Y` (prirodnije u rečenici), `razlika između X i Y` | |
| near me | `blizu mene`, `u mojoj blizini`, `najbliži` | |
| in Belgrade | `u Beogradu` (lokativ u rečenici), `Beograd` (keyword forma — izbegavaj, vidi sekciju 1) | |
| is it worth it | `da li se isplati`, `vredi li` | jak commercial-investigation signal |
| how to choose | `kako izabrati`, `na šta obratiti pažnju` | klasičan solution-aware obrazac |

## 6. Šta nikad ne sme u finalni tekst

Nikad placeholder u finalnom tekstu: `[brend]`, `{grad}`, `XXX`, `vaš brend/proizvod`. G6 gate ovo hvata regex-om — vidi `PLACEHOLDER_RE` u `scripts/validate_library.py` za tačan pattern. Ako informacija nije poznata (grad, konkurent, cena), intent ide u fallback (Faza 2, `references/workflow.md`) ili se briše iz matrice, ne popunjava se placeholder-om koji korisnik treba da menja ručno.
