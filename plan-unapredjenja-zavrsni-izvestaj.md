# Skills repo — plan unapređenja: završni izveštaj

**Repo:** `webdevcom01-cell/skills` (privatan, `main` grana)
**Period:** 22.08.2026, jedna sesija rada
**Status:** svih 20 stavki iz plana zatvoreno

---

## 1. Polazno stanje

Sesija je krenula od forenzičke analize repoa u tom trenutku: 54 skilla u `plugin/skills/`, jedna
distributable celina koja je mešala četiri različita sloja — opšte-upotrebljive alate, interne
Agent Studio/AgentStack alate, konsalting sloj izgrađen na tim alatima, i dva skilla hardkodovana
na konkretne klijentske angažmane. Analiza je izbacila nekoliko konkretnih problema: četiri skilla
su nosila Anthropic-ovu restriktivnu licencu a sedela u paketu koji se deli dalje; devet mutirajućih
skillova se oslanjalo isključivo na prozu ("pitaj korisnika pre...") umesto na tehničku ogradu;
četiri `SKILL.md` fajla su prelazila repoov sopstveni limit veličine (500 linija / ~5000 tokena) bez
`references/` foldera za izmeštanje detalja; metadata (verzije, changelog-ovi) je bila neusklađena
kroz repo. Iz toga je proizašao plan od 20 konkretnih stavki, podeljenih u faze A–F.

## 2. Šta je urađeno

Rad je išao u nekoliko talasa, svaki zatvoren i proveren pre prelaska na sledeći.

**Licenciranje (faza A1).** `docx`, `pdf`, `pptx`, `xlsx` uklonjeni iz `plugin/skills/` — Claude
Code/Cowork ih već isporučuje nativno, pa se ništa funkcionalno ne gubi, a pravni rizik nestaje.
Kasnije u istoj sesiji otkrivena su i dva skilla sa sopstvenom "all rights reserved" licencom
(`market-research-navigator`, `system-teardown`) koja je eksplicitno zabranjivala redistribuciju —
tvoja odluka je bila da zadržiš autorska prava netaknuta, ali da ih izbaciš iz deljivog plugina.
Oba ostaju u faznim folderima za ličnu upotrebu. Uz to, 8 skillova je imalo Apache 2.0 licencu sa
nepopunjenim `Copyright [yyyy] [name of copyright owner]` placeholderom — popunjeno stvarnim
nosiocem autorskih prava.

**Bezbednost (faza A2).** Dvanaest skillova koji stvarno mutiraju stanje (`as_patch_node_field`,
`as_create_agent`, `obsidian_update_note` i slično) dobilo je `allowed-tools` ogradu u frontmatteru,
umesto da se oslanjaju samo na tekstualno upozorenje. Provera specijalizovanim alatom
(`find_mutating_without_allowed_tools.py`) na kraju sesije potvrđuje: nula skillova u repou pominje
mutirajući alat ili destruktivan jezik bez tehničke ograde.

**D1 i D2 talas — veličina SKILL.md fajlova.** Petnaest skillova je prekoračivalo ili se
približavalo repoovom limitu veličine. Metod je bio identičan za sve: pronaći samostalnu/detaljnu
sekciju u telu (IF-THEN tabele, template-i, rubrici za gradere, edge case-ovi), izvući je verbatim u
`references/*.md` sa kratkim uvodom koji kaže odakle je učitana i kada je čitati, ostaviti u telu
kratak pokazivač umesto punog sadržaja, podići verziju gde je postojalo polje za to. Svaka izmena je
provaerena `diff`-om bajt-po-bajt protiv originala pre i posle premeštanja — nijedno pravilo,
prag, formula ili primer nije izmenjen ili skraćen, samo premešten. Obuhvaćeni skillovi:
`pipeline-debug`, `agent-scaffolder`, `soma-run`, `soma-eval-harness` (D1), zatim
`prospect-discovery`, `soma-performance-review`, `agent-health-check`, `pipeline-input-validator`,
`soma-agent-debugger`, `instincts-updater`, `kb-sync`, `soma-memory-fix`, `winners-log-logger`,
`algorithmic-art`, `doc-coauthoring` (D2). Jedini izuzetak je `skill-creator-pro` — namerno
preskočen na tvoju odluku jer prati upstream Anthropic fork i mehaničko cepanje bi otežalo buduću
sinhronizaciju; ostaje jedini skill u repou koji je i dalje preko limita, po dizajnu.

**Root LICENSE i CHANGELOG (#17/#18).** Plugin kao celina prethodno nije imao ni jedno ni drugo.
Dodat `LICENSE` (MIT tekst preuzet iz `geo-prompt-library`, jedine već kompletne i tvoje licence u
repou) i `CHANGELOG.md` koji prati Keep a Changelog format i sumira izmene od 22.08.2026 nadalje.

**Podela plugina na dva paketa (#16).** Najveća arhitektonska promena u sesiji. Pročitan je opis
svih tadašnjih 50 skillova da bi podela bila zasnovana na stvarnoj zavisnosti, ne na nagađanju po
imenu. Rezultat, potvrđen tvojom odlukom:

| Paket | Sadržaj | Broj skillova |
|---|---|---|
| `plugin/` | Opšti alati, bez zavisnosti od Agent Studio/AgentStack/SOMA/tvog Obsidian vault-a | 21 |
| `plugin-soma-ops/` | SOMA content pipeline (TI→HW→CR→Score Analyzer), Agent Studio infrastruktura, konsalting sloj izgrađen na njoj | 27 → 28 (posle #15) |

`tender-projekat` (hardkodovan na jedan klijentski ugovor) i `plugin-sync` (meta-alat za održavanje
ovog repoa) su izbačeni iz oba paketa — korisni su samo tebi, ostaju u faznim folderima. Novi
`plugin-soma-ops/` je dobio punu sopstvenu strukturu: `plugin.json`, `README.md`, `LICENSE`,
`CHANGELOG.md`. `catalog_sync_check.py` je generalizovan (`--package-dir` argument) da isti skript
proverava katalog bilo kog od dva paketa protiv sopstvenog `skills/` foldera.

**`compatibility:` polje (#14).** Pre pisanja, provereno je kako se polje već koristi u repou —
zatečeno na 5 skillova kao slobodan tekst koji opisuje stvarne zavisnosti (MCP alati, Python
paketi, ponašanje kad zavisnost nedostaje), ne kao strukturisana šema. Isti stil primenjen na
preostalih 26 skillova u `plugin-soma-ops/`, svaki opis izveden iz stvarnog `allowed-tools` bloka i
sadržaja `scripts/`/`references/` foldera tog konkretnog skilla — ne generička fraza.

**`vault-schema-reference` (#15) — nov skill.** Izgrađen od nule uz tvoj sadržajni input: dokumentuje
strukturu tvog Obsidian vault-a (`agents/{slug}/`, `Insights/`, `shared/`, `system/`) tako da drugi
skillovi mogu da citiraju jedan izvor istine umesto da nagađaju putanje. Dva polja su prvobitno
ostala označena kao "unconfirmed" (`system/soma-rules.md`, `system/config.md`) jer se dva postojeća
skilla nisu slagala oko toga da li `system/` folder uopšte ima sadržaj. Danas, u nastavku sesije,
oba fajla su potvrđena da postoje direktnim, uživo čitanjem vault-a (`obsidian_list_folders`,
`obsidian_search_notes`) — folder ima 13 nota, ne nula, uključujući oba tražena fajla plus
nedokumentovani `system/vault-standard.md`. Referenca je ažurirana da to odražava (`1.0.0` →
`1.1.0`), i uveden je u `plugin-soma-ops/` katalog (27 → 28 skillova).

## 3. Status svih 20 stavki plana

| # | Stavka | Status |
|---|---|---|
| 1 | Licenciranje docx/pdf/pptx/xlsx | ✅ |
| 2 | `allowed-tools` za mutirajuće skillove | ✅ (12 skillova, potvrđeno alatom da nema više gap-a) |
| 3 | README katalog: `plugin-sync` + tačan broj | ✅ |
| 4 | `agent-scaffolder` ↔ `safe-agent-builder` disambiguacija | ✅ |
| 5 | `geo-prompt-library`: requirements.txt + CHANGELOG | ✅ |
| 6 | `prospect-discovery`: dodati `version:` | ✅ |
| 7 | `soma-performance-review`: skratiti description | ✅ (lažni alarm — bio je ispod limita) |
| 8 | Izgraditi `skill-lint` | ✅ |
| 9 | Izgraditi `license-compliance-guard` | ✅ (deo `skill-lint`-a) |
| 10 | Izgraditi/proširiti `skill-catalog-sync` | ✅ (`plugin-sync` + `catalog_sync_check.py`) |
| 11 | Izgraditi `skill-security-review` | ✅ |
| 12 | D1 — skratiti 4 skilla preko 500 linija | ✅ |
| 13 | D2 — hijerarhija za skillove u zoni 300–500 | ✅ (spojeno sa 3 tvrda SIZE nalaza) |
| 14 | `compatibility:` polje za SOMA-skillove | ✅ (26 skillova) |
| 15 | `vault-schema-reference` (nov skill) | ✅ (uključujući potvrdu `system/` sadržaja) |
| 16 | Podela plugina (soma-ops / opšti toolkit) | ✅ |
| 17 | Root `CHANGELOG.md` za plugin | ✅ |
| 18 | Root `LICENSE` za plugin | ✅ |
| 19 | `plugin.json` verzija | ✅ |
| 20 | `roast`/`rls-rollout` otkrivljivost | ✅ (već rešeno, samo potvrđeno) |

Uz plan, usput su otkrivena i rešena dva nalaza koja nisu bila na originalnoj listi: dve restriktivne
"all rights reserved" licence (§2, opisano gore) i pogrešna brojka skillova u README/`plugin.json`
posle dodavanja `skill-lint`/`skill-security-review`.

## 4. Šta smo dobili

Dva odvojena, čista distributable plugin paketa, svaki sa sopstvenim `plugin.json`, `README.md`,
`LICENSE`, `CHANGELOG.md`:

- **`plugin/`** (21 skill) — opšti alati bez zavisnosti od tvoje specifične infrastrukture. Bezbedan
  za deljenje sa bilo kim: klijentom, javno, kroz Cowork/Claude Code marketplace.
- **`plugin-soma-ops/`** (28 skillova) — tvoja Agent Studio/AgentStack/SOMA pipeline infrastruktura i
  konsalting sloj izgrađen na njoj, uključujući referentnu dokumentaciju vault-a.

Uz to: automatizovani alati za održavanje (`skill-lint` sa tri provere — veličina, licence,
katalog; `skill-security-review` za mutirajuće alate; `plugin-sync` za sinhronizaciju i pakovanje),
sređena metadata kroz ceo repo, i manji/čitljiviji `SKILL.md` fajlovi sa detaljima izmeštenim u
`references/` na zahtev.

## 5. Vrednost

`plugin/` se sada može deliti bez pravnog rizika — nijedna restriktivna ili nepopunjena licenca nije
više unutra. `plugin-soma-ops/` je organizovan odvojeno, što znači da se može verzionisati, širiti
ili čak deliti sa timom bez mešanja sa opštim alatima. Svaki skill koji nešto mutira ima tehničku
ogradu, ne samo obećanje u tekstu. Budući rad na skillovima je jeftiniji: nova referenca vault-a
smanjuje šansu da neki novi skill pogodi pogrešnu putanju, a lint skriptovi hvataju licencu, veličinu
i bezbednosnu rupu automatski, umesto da se otkrije tek kad nešto pukne.

## 6. Šta ostaje

- Ručno brisanje `_to_delete/` foldera u `moji_skillovi/` (sadrži sve fajlove/foldere premeštene
  tokom sesije koje `device_bash` nije mogao direktno da obriše) — na tebi kad budeš zadovoljan/na.
- **`instincts.md` konvergencija** — dokumentovano u `vault-schema-reference` kao trenutno stanje,
  ne rešeno: format se razlikuje po agentu (Content Repurposer ima QGF sekciju, Score Analyzer ima
  YAML frontmatter, Trend Intelligence i Hook Writer nemaju ni jedno). Sledeći zadatak.
- `skill-creator-pro` ostaje jedini skill preko veličinskog limita — namerno, dok se ne odluči
  drugačije (prati upstream fork).
