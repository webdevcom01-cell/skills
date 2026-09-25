#!/usr/bin/env bash
# checker-verify.sh
#
# Deterministički Verify sloj. Pokreće se KAO ODVOJEN PROCES od Maker-a
# (nikad u istom kontekstu/sesiji) - to je ono što sprečava Verification Gap.
#
# Redosled provera je namerno od jeftinijeg ka skupljem: čim jedan sloj
# padne, staje se odmah (fail-fast), ne troši se vreme/tokeni na sledeće.
#
# Usage:
#   ./checker-verify.sh <worktree-dir> [base-branch]
#
# [base-branch] je OPCIONO (nazad-kompatibilno - stariji pozivi sa samo
# <worktree-dir> i dalje rade), ali VRLO preporučeno - vidi STAVKA #3
# napomenu ispod za zašto. Kad je izostavljen, skripta pokušava "main" pa
# "master" kao lokalne grane; ako NI JEDNA ne postoji, pada nazad na staro
# ponašanje (git diff HEAD) uz glasno upozorenje na stderr i u samom
# izveštaju - to staro ponašanje ima poznat, ozbiljan gap (vidi ispod).
#
# Output: strukturisan JSON verdikt na stdout, npr:
#   {"deterministic_status": "FAIL", "layer_failed": "unit_tests", ...}
#
# Exit codes:
#   0 = svi deterministički slojevi prošli (i dalje treba nezavisni
#       review pre CONFIRMED - vidi napomenu na dnu)
#   1 = neki sloj pao (FAIL) - vrati agentu u sledeću iteraciju
#   2 = nema primenljivih determinističkih provera za ovaj projekat/zadatak
#       (agent mora eksplicitno tražiti human review, ne tiho CONFIRMED)

set -uo pipefail

WT_DIR="${1:?Usage: checker-verify.sh <worktree-dir> [base-branch]}"
cd "${WT_DIR}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RESULT_FILE=".agent/verify_result.json"
LAYERS_RUN=()
LAYER_FAILED=""
STATUS="PASS"
HAS_ANY_CHECK="false"

# STAVKA #3 OJAČAVANJA (16. sept 2026 - gruba heuristika za "test pokriva
# promenu"): otkriveno je da je originalna gruba heuristika (BILO KOJI test
# fajl dotaknut) bila NAJMANJI problem. Stvaran, ozbiljniji bag: ceo diff se
# računao preko `git diff --name-only HEAD` - jedan ref, poredi radni
# direktorijum sa POSLEDNJIM COMMIT-OM na TEKUĆOJ grani. Ako Maker komituje
# progresivno posle svake iteracije (upravo ono što je preporučeno i drugde
# u ovom projektu - vidi checker-verify.sh header note o Think→Act→Observe
# ciklusu i prepare-checker-bundle.sh-ovu sopstvenu istoriju ispravki), do
# trenutka kad se OVA skripta pokrene radni direktorijum je ČIST - `git diff
# HEAD` vraća PRAZNO, TOUCHES_LOGIC i TOUCHES_TEST ostaju oboje `false`, i
# MAX_CONFIDENCE tiho ostaje "CONFIRMED" (default), bez obzira koliko je
# logike zaista promenjeno na toj grani niti da li ijedan test postoji za
# nju. Dokazano na sintetičkom repou: grana koja dodaje potpuno netestiranu,
# baggy `divide()` funkciju (bez provere deljenja nulom), sve komitovano -
# `checker-verify.sh` je vratio `"max_confidence": "CONFIRMED"`.
# Ispravka: `git diff --name-only <base-branch>` (single-ref protiv BAZNE
# grane, ne HEAD-a trenutne) - isti obrazac kao već audit-ovana ispravka u
# `prepare-checker-bundle.sh`. Dopunjeno sa `git add -N -A` PRE diff-a (isto
# tako već ustanovljeno u prepare-checker-bundle.sh) da POTPUNO NOVI,
# nikad `git add`-ovani fajlovi takođe budu vidljivi - bez ovoga, `git diff`
# ih ne prikazuje UOPŠTE, čak ni protiv baze.
BASE_BRANCH="${2:-}"
if [[ -z "${BASE_BRANCH}" ]]; then
  if git show-ref --verify --quiet refs/heads/main; then
    BASE_BRANCH="main"
  elif git show-ref --verify --quiet refs/heads/master; then
    BASE_BRANCH="master"
  else
    echo "UPOZORENJE: base-branch nije prosleđen i ni 'main' ni 'master' ne postoje lokalno - padam nazad na staro 'git diff HEAD' ponašanje, koje NE VIDI komitovane izmene cele grane (samo neposlednji-komitovane). Prosledi eksplicitan drugi argument da ovo izbegneš." >&2
  fi
fi
DIFF_REF="${BASE_BRANCH:-HEAD}"

run_layer() {
  local name="$1"; shift
  echo "-- Verify sloj: ${name} --" >&2
  if "$@" > ".agent/verify_${name}.log" 2>&1; then
    LAYERS_RUN+=("${name}:PASS")
    return 0
  else
    LAYERS_RUN+=("${name}:FAIL")
    LAYER_FAILED="${name}"
    STATUS="FAIL"
    return 1
  fi
}

# NAPOMENA (nalaz iz PRVOG UŽIVO pilota na realnom uređaju, ne samo cloud
# sandbox-u): bare `pytest -q` / `ruff check .` / `mypy .` pretpostavljaju da
# je alat na PATH-u u ljusci koja poziva ovaj skript. To NIJE pouzdano za
# Python projekte upravljane sa `uv` (uv sync pravi izolovan .venv, i alat
# nije na PATH-u dok se venv eksplicitno ne aktivira), niti kad je alat
# instaliran samo kao pip user-install (kao u ovom istom pilotu - pytest je
# instaliran, ali `pip install`-ova sopstvena poruka kaže "not on PATH", pa
# je bare `pytest -q` pukao sa "command not found" - checker.sh je to
# tiho prijavio kao "unit_tests:FAIL", NEODVOJIVO od stvarnog pada testova).
# To je opasno baš zato što je Checker sloj mišljen kao objektivna istina -
# lažan "testovi padaju" izveštaj bi naveo agenta da "popravlja" nešto što
# nije ni pokrenuto.
#
# Ispravka: `run_py_tool` pokuša REDOM (1) `uv run <alat>` ako projekat ima
# pyproject.toml i `uv` je dostupan (najtačnije - koristi projekat-ov
# zaključan .venv), (2) ako TAJ pokušaj propadne SPECIFIČNO zato što alat
# nije deklarisan kao dependency projekta (prepoznato po poruci u izlazu,
# ne po golom exit kodu - exit 1 od uv run i exit 1 od stvarnog pada testova
# izgledaju isto), probaj `python3 -m <alat>` kao fallback (radi kad god je
# alat uvoziv iz trenutno aktivnog python3, npr. pip user-install kao ovde),
# (3) ako ni jedno ni drugo, bare `<alat>` kao poslednji pokušaj. Rezultat
# DRUGOG/TREĆEG pokušaja se tretira kao stvaran verdikt; poruka o "alat
# nedostaje" iz PRVOG pokušaja se ne meša sa stvarnim rezultatom testova.
run_py_tool() {
  local layer_name="$1" module="$2"; shift 2
  local log=".agent/verify_${layer_name}.log"
  if [[ -f "pyproject.toml" ]] && command -v uv >/dev/null 2>&1; then
    if uv run "${module}" "$@" > "${log}" 2>&1; then
      LAYERS_RUN+=("${layer_name}:PASS"); return 0
    fi
    if grep -qiE "no module named ${module}|does not contain a package named ${module}|failed to spawn|No such file or directory.*${module}" "${log}"; then
      echo "NAPOMENA: 'uv run ${module}' nije naslo '${module}' kao dependency projekta - probam 'python3 -m ${module}' kao fallback (ovo NIJE stvaran rezultat testova, samo signal da alat nije deklarisan)." >&2
      if python3 -m "${module}" "$@" > "${log}" 2>&1; then
        LAYERS_RUN+=("${layer_name}:PASS"); return 0
      fi
    fi
  elif python3 -m "${module}" "$@" > "${log}" 2>&1; then
    LAYERS_RUN+=("${layer_name}:PASS"); return 0
  elif command -v "${module}" >/dev/null 2>&1 && "${module}" "$@" > "${log}" 2>&1; then
    LAYERS_RUN+=("${layer_name}:PASS"); return 0
  fi
  LAYERS_RUN+=("${layer_name}:FAIL"); LAYER_FAILED="${layer_name}"; STATUS="FAIL"
  return 1
}

# NAPOMENA (drugi nalaz iz istog uživo pilota): prvi pokušaj ove ispravke je
# koristio `command -v uv` kao (delimičan) uslov za "da li da pokušam lint/
# typecheck", na osnovu pretpostavke "uv je tu, možda je ruff/mypy dependency
# projekta". To je pogrešno - `uv` biti prisutan NE znači da OVAJ projekat
# uopšte koristi ruff/mypy, i pravilo je odmah lažno prijavilo "lint:FAIL"
# na sandbox projektu koji ruff/mypy uopšte ne pominje. Ispravljeno da se
# lint/typecheck pokušavaju SAMO kad postoji stvaran trag da ih projekat
# koristi (alat na PATH-u, uvoziv iz python3, ili pomenut u pyproject.toml -
# poslednje hvata uv-managed dependency koji još nije instaliran u .venv).
ruff_in_use() {
  command -v ruff >/dev/null 2>&1 && return 0
  python3 -c "import ruff" >/dev/null 2>&1 && return 0
  [[ -f "pyproject.toml" ]] && grep -qi "ruff" pyproject.toml
}
mypy_in_use() {
  command -v mypy >/dev/null 2>&1 && return 0
  python3 -c "import mypy" >/dev/null 2>&1 && return 0
  [[ -f "pyproject.toml" ]] && grep -qi "mypy" pyproject.toml
}
# STAVKA #3: isti obrazac kao ruff_in_use/mypy_in_use - koristi se za jak
# (measured), ne samo heuristički, coverage signal ispod. `pytest-cov`-ov
# uvozivi paket je `pytest_cov` (donja crta, ne crtica).
pytest_cov_available() {
  python3 -c "import pytest_cov" >/dev/null 2>&1
}

# 1. Lint / format
if [[ -f "package.json" ]] && grep -q '"lint"' package.json; then
  HAS_ANY_CHECK="true"
  run_layer "lint" npm run lint || true
elif [[ -f "pyproject.toml" ]] && ruff_in_use; then
  HAS_ANY_CHECK="true"
  run_py_tool "lint" ruff check . || true
fi

# 2. Type check (samo ako lint nije već pao)
if [[ "${STATUS}" == "PASS" ]]; then
  if [[ -f "tsconfig.json" ]]; then
    HAS_ANY_CHECK="true"
    run_layer "typecheck" npx tsc --noEmit || true
  elif [[ -f "pyproject.toml" ]] && mypy_in_use; then
    HAS_ANY_CHECK="true"
    run_py_tool "typecheck" mypy . || true
  fi
fi

# 3. Unit testovi (samo ako prethodno prošlo)
#
# NAPOMENA (nalaz iz live demo testa - ćirilica-konverter zadatak): originalni
# uslov je zahtevao `pyproject.toml` ili `pytest.ini` kao dokaz da je ovo
# pytest projekat. Sasvim legitiman, čest slučaj - mali skript + test fajl,
# BEZ formalnog packaging fajla (upravo ono što je Maker ovde napravio, po
# task spec-u koji je eksplicitno tražio "nema spoljnih zavisnosti") - je
# potpuno promakao ovoj proveri: `test_cirilica.py` sa 15 prolaznih testova
# je postojao, ali checker-verify.sh je vratio NO_APPLICABLE_CHECKS
# (deterministic_status), pytest NIKAD nije ni pozvan. Ovo je opasno u ISTOM
# smeru kao C.1 iz PRVI-ZIVI-PILOT.md - Checker sloj je mišljen kao
# objektivna istina, a "nema provere" je tiho progutalo stvaran, prolazan
# test suite.
#
# Ispravka: dodatni signal - postojanje bar jednog `test_*.py`/`*_test.py`
# fajla (do 3 nivoa dubine, van node_modules/.venv) - pytest sam po sebi ne
# traži nikakav config fajl da bi radio (auto-discovery po imenu fajla), pa
# ni ova provera ne treba da ga zahteva.
HAS_PY_TEST_FILES="false"
if find . -maxdepth 3 \( -name 'test_*.py' -o -name '*_test.py' \) \
     -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/__pycache__/*' \
     2>/dev/null | grep -q .; then
  HAS_PY_TEST_FILES="true"
fi

IS_PY_PROJECT="false"
if [[ -f "pyproject.toml" ]] || [[ -f "pytest.ini" ]] || [[ -f "setup.cfg" ]] || [[ "${HAS_PY_TEST_FILES}" == "true" ]]; then
  IS_PY_PROJECT="true"
fi

# STAVKA #3: kad je pytest-cov dostupan, tražimo coverage JSON izveštaj U
# ISTOM prolazu kao unit testovi (ne pokrećemo testove dvaput) - ovo je ono
# što liniju-nivo coverage_check.py ispod koristi kao JAK signal umesto
# heuristike. Ako `--cov` flegovi puknu (pytest-cov NIJE zapravo instaliran
# uprkos import provere, ili je verzija nekompatibilna), padamo nazad na
# goli `pytest -q` - NE tretiramo taj specifičan neuspeh kao "testovi padaju"
# (ista lekcija kao run_py_tool-ova uv/PATH ispravka iznad).
COVERAGE_JSON=".agent/coverage.json"
PYTEST_COV_USED="false"
if [[ "${STATUS}" == "PASS" ]]; then
  if [[ -f "package.json" ]] && grep -q '"test"' package.json; then
    HAS_ANY_CHECK="true"
    run_layer "unit_tests" npm test -- --ci || true
  elif [[ "${IS_PY_PROJECT}" == "true" ]]; then
    HAS_ANY_CHECK="true"
    if pytest_cov_available; then
      rm -f "${COVERAGE_JSON}"
      if run_py_tool "unit_tests" pytest -q "--cov=." "--cov-report=json:${COVERAGE_JSON}"; then
        [[ -f "${COVERAGE_JSON}" ]] && PYTEST_COV_USED="true"
      else
        # Moglo je da padne zbog `--cov` flega samog (npr. inkompatibilna
        # verzija) umesto stvarnog pada testova - probaj JOŠ JEDNOM bez
        # coverage flegova pre nego što se preda na FAIL, da ne pomešamo
        # "coverage alat nije radio" sa "testovi padaju".
        if grep -qiE "unrecognized arguments.*--cov|unrecognized arguments.*--cov-report" ".agent/verify_unit_tests.log" 2>/dev/null; then
          echo "NAPOMENA: '--cov' flegovi nisu prepoznati uprkos uvozivom pytest_cov-u (verovatno inkompatibilna verzija) - probam goli 'pytest -q' bez coverage-a." >&2
          # NEZAVISAN REVIEW (16. sept, Runda review stavke #3) - nalaz B5:
          # LAYER_FAILED se ovde NIJE resetovao, pa je ostajao "zaglavljen" na
          # "unit_tests" i posle USPESNOG recovery-ja (STATUS vracen na PASS),
          # dajuci samoprotivrecan izlaz (deterministic_status:PASS ali
          # layer_failed:unit_tests). Ispravka: resetuj i LAYER_FAILED ovde -
          # run_py_tool ce ga ponovo ispravno postaviti AKO retry stvarno padne.
          STATUS="PASS"; LAYER_FAILED=""; LAYERS_RUN=("${LAYERS_RUN[@]:0:$((${#LAYERS_RUN[@]}-1))}")  # ukloni pogresan FAIL zapis
          run_py_tool "unit_tests" pytest -q || true
        fi
      fi
    else
      run_py_tool "unit_tests" pytest -q || true
    fi
  fi
fi

# 4. Provera da li je Maker dodao/menjao testove za promenu ponašanja.
#
# STAVKA #3 OJAČAVANJA - dva sloja, jači ima prednost:
#   (a) MERENA pokrivenost linija (coverage_check.py) - kad je Python
#       projekat SA pytest-cov izveštajem, proveravamo da li su STVARNO
#       IZMENJENE linije u ne-test .py fajlovima STVARNO izvršene tokom
#       testova - ne samo da li test fajl postoji negde u diff-u.
#   (b) heuristika po imenu fajla (TOUCHES_LOGIC/TOUCHES_TEST) - fallback
#       kad (a) nije primenljivo (nije Python, nema pytest-cov, coverage
#       run nije uspeo). I OVA heuristika je ispravljena u odnosu na
#       original: redosled provere je sad doc/config PRE test-pattern
#       (originalni redosled je značio da `*.md`/`*.json` fajl čije ime
#       SLUČAJNO sadrži "test" kao podstring - npr. "contest_notes.md",
#       "latest_changes.md" - biva pogrešno klasifikovan kao TOUCHES_TEST
#       umesto ignorisan kao dokumentacija, PRE nego što petlja uopšte
#       stigne do doc/config grane), I test-pattern se sad proverava po
#       IMENU FAJLA na definisanim pozicijama (test_*.py, *_test.py,
#       *.test.js, *Test.java, itd, ili /tests//  direktorijum), ne kao
#       slepo "sadrži 'test' bilo gde u putanji" - originalni obrazac je
#       netačno klasifikovao npr. "attestation.py" (sadrži "test" kao
#       podstring: a-TTEST-ation) kao test fajl, iako je to stvarna,
#       netestirana logika. Oba nalaza dokazana na sintetičkom repou pre
#       ispravke.
# NEZAVISAN REVIEW (16. sept, Runda review stavke #3) - nalaz B2: git po
# default-u (core.quotePath=true) kvotuje/oktalno-eskejpuje putanje sa
# ne-ASCII karakterima (npr. cirilica - direktno pogadja ovaj projekat, koji
# ima zive cirilica-konverter/cirilica-history-cleanup demo worktree-ove) u
# `git diff` izlazu, sto lomi i ovo ime-fajla poredjenje i, jos ozbiljnije,
# coverage_check.py-jevo parsiranje `+++ ` header-a (vidi tamo). Ispravka:
# `-c core.quotePath=false` na SVAKOM git diff pozivu koji cita putanje
# (ovde i u coverage_check.py) da se ne-ASCII imena ispisu kao sirov UTF-8.
DIFF_FILES=$(git add -N -A 2>/dev/null; git -c core.quotePath=false diff --name-only "${DIFF_REF}" 2>/dev/null || true)
TOUCHES_LOGIC="false"
TOUCHES_TEST="false"
classify_file() {
  local f="$1" base
  base="$(basename -- "$f")"
  case "$f" in
    *.md|*.json|*.yaml|*.yml|*.lock|*.txt|*.toml|*/LICENSE|LICENSE|*/LICENSE.*|LICENSE.*|*.gitignore|.gitignore)
      echo "doc"; return ;;
  esac
  case "$base" in
    test_*.py|*_test.py|*.test.js|*.test.ts|*.test.jsx|*.test.tsx|*.spec.js|*.spec.ts|*.spec.jsx|*.spec.tsx|*_test.go|*_test.rb|spec_*.rb|Test*.java|*Test.java|Test*.cs|*Test.cs|Test*.kt|*Test.kt)
      echo "test"; return ;;
  esac
  case "$f" in
    */tests/*|*/test/*|*/__tests__/*|*/spec/*|tests/*|test/*|__tests__/*|spec/*)
      echo "test"; return ;;
  esac
  echo "logic"
}
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  cls="$(classify_file "$f")"
  case "$cls" in
    test) TOUCHES_TEST="true" ;;
    logic) TOUCHES_LOGIC="true" ;;
  esac
done <<< "${DIFF_FILES}"

COVERAGE_CHECK_JSON="{}"
COVERAGE_CHECK_USED="false"
MAX_CONFIDENCE="CONFIRMED"
CONFIDENCE_BASIS="nema_izmena_logike"

if [[ "${PYTEST_COV_USED}" == "true" && -n "${BASE_BRANCH}" ]]; then
  COVERAGE_CHECK_JSON="$(python3 "${SCRIPT_DIR}/coverage_check.py" "${BASE_BRANCH}" "${COVERAGE_JSON}" 2>/dev/null || echo '{"checked": false, "reason": "coverage_check.py nije uspeo da se pokrene"}')"
  COVERAGE_CHECKED="$(echo "${COVERAGE_CHECK_JSON}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('checked', False))" 2>/dev/null || echo "False")"
  if [[ "${COVERAGE_CHECKED}" == "True" ]]; then
    COVERAGE_CHECK_USED="true"
    ALL_COVERED="$(echo "${COVERAGE_CHECK_JSON}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('all_changed_lines_covered', False))")"
    if [[ "${ALL_COVERED}" == "True" ]]; then
      MAX_CONFIDENCE="CONFIRMED"
      CONFIDENCE_BASIS="merena_linija_pokrivenost"
    else
      MAX_CONFIDENCE="PLAUSIBLE"
      CONFIDENCE_BASIS="merena_linija_pokrivenost"
      echo "NAPOMENA: merena coverage analiza pokazuje IZMENJENE linije koje NISU izvršene tokom testova - max verdikt je PLAUSIBLE, ne CONFIRMED (vidi ${COVERAGE_JSON} i coverage_check izlaz u ${RESULT_FILE})." >&2
    fi
  fi
fi

if [[ "${COVERAGE_CHECK_USED}" == "false" ]]; then
  CONFIDENCE_BASIS="heuristika_po_imenu_fajla"
  if [[ "${TOUCHES_LOGIC}" == "true" && "${TOUCHES_TEST}" == "false" ]]; then
    MAX_CONFIDENCE="PLAUSIBLE"
    echo "NAPOMENA: promenjena je logika bez odgovarajućih test izmena (heuristika po imenu fajla, ne merena pokrivenost) - max verdikt je PLAUSIBLE, ne CONFIRMED." >&2
  elif [[ "${TOUCHES_LOGIC}" == "true" ]]; then
    CONFIDENCE_BASIS="heuristika_po_imenu_fajla_slaba"
  fi
fi

if [[ "${HAS_ANY_CHECK}" == "false" ]]; then
  cat > "${RESULT_FILE}" <<EOF
{
  "deterministic_status": "NO_APPLICABLE_CHECKS",
  "layers_run": [],
  "max_confidence": "NONE",
  "requires_human_review": true,
  "note": "Nema determinističke provere za ovaj projekat/zadatak - subjektivna ocena nije dovoljna, potreban je human review pre merge-a."
}
EOF
  cat "${RESULT_FILE}"
  exit 2
fi

LAYERS_JSON=$(printf '"%s",' "${LAYERS_RUN[@]}" | sed 's/,$//')
cat > "${RESULT_FILE}" <<EOF
{
  "deterministic_status": "${STATUS}",
  "layer_failed": "${LAYER_FAILED}",
  "layers_run": [${LAYERS_JSON}],
  "max_confidence": "${MAX_CONFIDENCE}",
  "confidence_basis": "${CONFIDENCE_BASIS}",
  "coverage_check": ${COVERAGE_CHECK_JSON},
  "requires_human_review": $( [[ "${MAX_CONFIDENCE}" == "PLAUSIBLE" ]] && echo true || echo false )
}
EOF
cat "${RESULT_FILE}"

# NAPOMENA: ovaj skript daje samo deterministički sloj. Nezavisni
# Checker-review (svež kontekst/subagent, samo diff + spec, BEZ Maker-ovog
# rezonovanja) je i dalje obavezan pre finalnog CONFIRMED verdikta -
# vidi Domen 2 analize i postojeći `adversarial-verify` obrazac.

if [[ "${STATUS}" == "FAIL" ]]; then
  exit 1
fi
exit 0
