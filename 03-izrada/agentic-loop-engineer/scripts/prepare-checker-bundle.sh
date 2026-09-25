#!/usr/bin/env bash
# prepare-checker-bundle.sh
#
# Sprovodi Maker-Checker izolaciju KROZ KONSTRUKCIJU FAJLOVA, ne samo kroz
# uputstvo u SKILL.md. Pravi poseban direktorijum koji sadrži SAMO ono što
# Checker sme da vidi - task_spec.md, git diff, i deterministički verify
# rezultat. Namerno NE kopira scratchpad.md ni task_log.md (Maker-ovo
# rezonovanje i istorija pokušaja) - upravo to razdvajanje sprečava da
# Checker "pozajmi" Maker-ovu racionalizaciju.
#
# Usage:
#   ./prepare-checker-bundle.sh <worktree-dir> <base-branch>
#
# Posle ovoga, pokreni Checker na JEDAN od dva načina:
#   (a) Headless, potpuno nov proces, cwd = bundle dir (ne worktree!):
#         cd <worktree-dir>/.agent/checker_bundle && \
#         claude -p "Pročitaj task_spec.md, diff.patch i verify_result.json u
#         ovom direktorijumu. Ne pretpostavljaj ništa van njih. Vrati verdikt
#         CONFIRMED ili PLAUSIBLE (nikad oboje) sa obrazloženjem." --permission-mode ask
#   (b) Unutar interaktivne Claude Code sesije, kao odvojen subagent (Task/Agent
#       tool) sa fresh kontekstom, eksplicitno mu proslediš SAMO sadržaj bundle-a
#       (ne link ka celom worktree-u - subagent koji dobije pristup celom
#       worktree-u može slučajno pročitati scratchpad.md i time poništiti izolaciju).

set -euo pipefail

WT_DIR="${1:?Usage: prepare-checker-bundle.sh <worktree-dir> <base-branch>}"
BASE_BRANCH="${2:?base-branch je obavezan (za git diff)}"

BUNDLE_DIR="${WT_DIR}/.agent/checker_bundle"
rm -rf "${BUNDLE_DIR}"
mkdir -p "${BUNDLE_DIR}"

if [[ ! -f "${WT_DIR}/.agent/task_spec.md" ]]; then
  echo "GREŠKA: ${WT_DIR}/.agent/task_spec.md ne postoji - pokreni spawn-worktree-agent.sh prvo." >&2
  exit 1
fi
cp "${WT_DIR}/.agent/task_spec.md" "${BUNDLE_DIR}/task_spec.md"

if [[ -f "${WT_DIR}/.agent/verify_result.json" ]]; then
  cp "${WT_DIR}/.agent/verify_result.json" "${BUNDLE_DIR}/verify_result.json"
else
  echo '{"deterministic_status": "NOT_RUN", "note": "checker-verify.sh nije pokrenut pre bundle-a - pokreni ga prvo."}' \
    > "${BUNDLE_DIR}/verify_result.json"
fi

# NAPOMENA (nalaz iz PRVOG UŽIVO end-to-end pilota): `git diff A...B` (dve
# tačke sa TRI tacke, dva ref-a) poredi SAMO commit-ovanu istoriju - ne vidi
# ništa iz radnog direktorijuma koje Maker nije komitovao. Ni SKILL.md ni
# ijedan skript u ovom paketu do sada nije EKSPLICITNO nalagao "komituj posle
# svake iteracije" - Think→Act→Observe→Verify ciklus (Domen 3) opisuje Act
# kao "izmeni fajlove", ne "izmeni i komituj". Rezultat: Maker koji ne
# komituje (potpuno realan slučaj - mnogi agenti komituju tek na kraju, ili
# uopšte ne dok Checker ne potvrdi) bi proizveo PRAZAN diff.patch dok
# verify_result.json istovremeno pokazuje PASS - Checker bi video "nema
# izmena, ali testovi prolaze" umesto stvarne izmene, i to je TAČNO
# rationalizacija-rizik koji je cela ova izolacija trebalo da spreči, samo u
# obrnutom smeru (prazan dokaz + PASS signal je lakše pogrešno pomešati sa
# "sve u redu" nego stvaran diff). Ispravka: `git diff <base>` (JEDAN ref,
# ne opseg) poredi vrh base-branch-a sa TRENUTNIM radnim direktorijumom
# (staged + unstaged + komitovano) - hvata SVE izmene bez obzira da li su
# komitovane, bez menjanja tuđe konvencije o tome KADA da se komituje.
# NAPOMENA (nalaz iz live demo testa - ćirilica-konverter, uhvatio ga sam
# Checker u svežoj sesiji, ne checker-verify.sh): ispravka iznad (single-ref
# `git diff <base>`) rešava SAMO slučaj "izmenjen POSTOJEĆI tracked fajl nije
# komitovan". `git diff` (u BILO kom obliku - jedan ref, dva ref, tri tačke)
# NIKAD ne prikazuje potpuno NOVE, untracked fajlove - to je git-ova osnovna
# semantika, ne bag ove skripte per se, ali posledica je bila identična onoj
# iz C.3.a: Maker je napravio cirilica.py i test_cirilica.py (novi fajlovi,
# nikad `git add`-ovani), checker-verify.sh ih je VIDEO i ispravno pokrenuo
# pytest nad njima (PASS/CONFIRMED, jer radi direktno na disku, ne kroz git),
# ali diff.patch je bio PRAZAN za njih - sadržao je SAMO nevezanu izmenu u
# checker-verify.sh. Checker je ovo ispravno prepoznao (PLAUSIBLE sa jakom
# rezervom: "diff ne pokriva nijednu stavku iz spec-a") umesto da poveruje
# lažno-umirujućem verify_result.json-u - upravo scenario zbog kog Domen 2
# uopšte postoji, samo što je do sada u ovom projektu SVAKI testni zadatak
# menjao POSTOJEĆE fajlove (sandbox-pilot-repo je unapred imao tracked kod),
# pa se ova specifična praznina (Maker pravi fajlove OD NULE) nikad nije
# pojavila pre ovog demoa.
#
# Ispravka: `git add -N/--intent-to-add` pre diff-a - obeležava untracked
# fajlove kao "namera da se dodaju" BEZ da stvarno stage-uje njihov sadržaj
# (ne menja Maker-ov budući `git add`/commit tok, samo čini da se u diff-u
# vide kao pun dodatak). I dalje poštuje .git/info/exclude (C.3.b ispravka),
# tako da .agent/__pycache__/.venv/node_modules ostaju isključeni.
git -C "${WT_DIR}" add -N -A 2>/dev/null || true

git -C "${WT_DIR}" diff "${BASE_BRANCH}" > "${BUNDLE_DIR}/diff.patch" || {
  echo "NAPOMENA: git diff prazan ili base-branch nije dostupan u ovom worktree-u - proveri ručno." >&2
}
if [[ ! -s "${BUNDLE_DIR}/diff.patch" ]]; then
  echo "UPOZORENJE: diff.patch je PRAZAN - ili Maker nije napravio nijednu izmenu, ili je nešto pošlo po zlu. NE prosleđuj Checker-u bundle sa praznim diff-om kao da je normalan slučaj - proveri ručno pre nego što nastaviš." >&2
fi

cat > "${BUNDLE_DIR}/README-CHECKER.md" <<'EOF'
# Checker instrukcije

Vidiš task_spec.md, diff.patch, verify_result.json, i - ako je task potekao
iz sdd-workflow-a - specs/<feature-slug>/{spec,plan,tasks}.md. Ne dobijaš
Maker-ovo rezonovanje niti istoriju pokušaja (scratchpad.md, task_log.md) -
to je namerno izostavljeno da bi tvoja procena bila nezavisna, ne
racionalizacija tuđeg rada. specs/ fajlovi (ako postoje) NISU to rezonovanje
- to je ugovor dogovoren PRE nego što je Maker počeo, slobodno ih koristi kao
osnovu za proveru acceptance criteria.

Zadatak: proceni da li diff.patch ispravno i potpuno implementira ono što
task_spec.md traži, uzimajući u obzir verify_result.json.

Vrati TAČNO jedan od dva verdikta:
- CONFIRMED - deterministički dokazano (verify_result.json status PASS
  I diff pokriva sve stavke iz spec-a I ima odgovarajuće test izmene)
- PLAUSIBLE - izgleda ispravno ali nema punog determinističkog dokaza
  (npr. verify_result.json kaže max_confidence PLAUSIBLE ili NO_APPLICABLE_CHECKS,
  ili logika je promenjena bez test pokrića)

Nikad ne vraćaj samo "izgleda dobro" bez jednog od ova dva labela.
EOF

# --- Nalaz iz testiranja mosta sdd-workflow -> agentic-loop-engineer (stavka
# #5 ojacavanja): ako je ovaj task potekao iz sdd-workflow-a, task_spec.md
# moze uputiti Makera/Checkera da procita specs/<slug>/{spec,plan,tasks}.md -
# ali ti fajlovi NISU deo diff.patch-a (postojali su VEC u base commit-u, pre
# grananja), pa bi Checker (koji dobija SAMO bundle direktorijum, ne ceo
# worktree - vidi komentar na vrhu skripte) trazio fajlove koji jednostavno
# nisu tu. spec.md/plan.md/tasks.md NISU Maker-ovo privatno rezonovanje kao
# scratchpad.md/task_log.md - to je UGOVOR dogovoren PRE Implement-a, i
# sdd-workflow-ov sopstveni Converge korak (references/converge-and-verify.md)
# eksplicitno trazi da nezavisni verifier dobije bas spec.md+plan.md+tasks.md+diff.
# Zato ih kopiramo u bundle kad postoje - ovo NE narusava Domen 2 izolaciju,
# samo je dopunjuje onim sto sama sdd-workflow metodologija vec smatra
# checker-vidljivim.
# NAPOMENA (nezavisan review, stavka #5, treći krug): prvobitna ispravka
# ("kopiraj ceo specs/ kad postoji") ima dva stvarna nedostatka, nadjena
# testiranjem, ne teoretski:
#   (a) curenje van scope-a: u repou sa VISE feature-slug-ova (realno stanje
#       posle nekoliko sdd-workflow ciklusa u istom repou), Checker bi dobio
#       specs/ ZA SVE feature-e, ne samo za onaj koji task_spec.md pominje -
#       dodatna zbunjujuca kolicina teksta bez ikakve oznake koji slug je
#       relevantan.
#   (b) `cp -R` ne prati simboličke linkove - ako je specs/ (ili neki slug
#       unutar njega) symlink (plauzibilno u monorepo/deljena-specs
#       setupu), bundle zavrsi sa samim symlink-om, ne njegovim sadrzajem -
#       Checker koji striktno postuje "ne gledaj van bundle direktorijuma"
#       (uputstvo na vrhu ove skripte) dobija mrtvu referencu; Checker koji
#       symlink ipak isprati tiho probija izolaciju koju ceo bundle mehanizam
#       postoji da sprovede.
# Ispravka: izvuci iz task_spec.md koji slug(ovi) se pominju (grep na
# "specs/<slug>") i kopiraj SAMO te poddirektorijume, sa -L (prati linkove,
# kopiraj stvaran sadrzaj). Ako task_spec.md ne pominje nijedan konkretan
# slug (stariji/rucno pisan task_spec bez sdd-workflow porekla), vrati se na
# staro ponasanje (kopiraj sve) - bolje viska konteksta nego Checker koji
# ne dobije nista sto mu treba.
if [[ -d "${WT_DIR}/specs" ]]; then
  mkdir -p "${BUNDLE_DIR}/specs"
  REFERENCED_SLUGS="$(grep -oE 'specs/[A-Za-z0-9_-]+' "${BUNDLE_DIR}/task_spec.md" 2>/dev/null | sed 's#specs/##' | sort -u || true)"
  if [[ -n "${REFERENCED_SLUGS}" ]]; then
    while IFS= read -r slug; do
      [[ -z "${slug}" ]] && continue
      if [[ -d "${WT_DIR}/specs/${slug}" ]]; then
        cp -RL "${WT_DIR}/specs/${slug}" "${BUNDLE_DIR}/specs/${slug}"
      fi
    done <<< "${REFERENCED_SLUGS}"
    echo "Uz to: specs/ kopiran u bundle, ogranicen na slug(ove) koje task_spec.md pominje (${REFERENCED_SLUGS//$'\n'/, }) - ovo je ugovor, ne Makerovo rezonovanje."
  else
    cp -RL "${WT_DIR}/specs/." "${BUNDLE_DIR}/specs/"
    echo "Uz to: specs/ (ceo, jer task_spec.md ne pominje konkretan slug) kopiran u bundle - ovo je ugovor, ne Makerovo rezonovanje."
  fi
fi

echo "Checker bundle spreman: ${BUNDLE_DIR}"
echo "Sadrži SAMO: task_spec.md, diff.patch, verify_result.json, README-CHECKER.md, (opciono) specs/"
echo "NE sadrži: scratchpad.md, task_log.md, loop_state.json (namerno)"
