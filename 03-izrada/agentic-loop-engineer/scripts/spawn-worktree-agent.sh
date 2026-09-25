#!/usr/bin/env bash
# spawn-worktree-agent.sh
#
# Kreira izolovan Git worktree za jedan agentski zadatak, postavlja
# in-band memoriju (scratchpad/task_log) i registruje task u deljenom
# registry.json koristeći optimistic-concurrency (compare-and-swap).
#
# NAPOMENA: invokacija samog agenta (poslednji korak) je namerno ostavljena
# kao mesto koje prilagođavaš svom konkretnom CLI-ju/verziji Claude Code-a
# (headless `-p` mod, ili tvoj AgentStack chat-orchestrator poziv). Ne
# pretpostavljam tačne flegove jer se menjaju između verzija — proveri
# `claude --help` u svom okruženju pre prvog pravog pokretanja.
#
# Usage:
#   ./spawn-worktree-agent.sh <task-id> <base-branch> <prompt-file> [max-iterations]
#
# Primer:
#   ./spawn-worktree-agent.sh fix-login-bug main tasks/fix-login-bug.md 5

set -euo pipefail

TASK_ID="${1:?Usage: spawn-worktree-agent.sh <task-id> <base-branch> <prompt-file> [max-iterations]}"
BASE_BRANCH="${2:?base-branch je obavezan}"
PROMPT_FILE="${3:?prompt-file je obavezan}"
MAX_ITERATIONS="${4:-5}"          # Hard Ceiling — konzervativan default za v1 test
MAX_WALL_CLOCK_SEC="${5:-1800}"   # 30 min default

# --- Validacija ulaza (nadograđeno posle audita) ---
# TASK_ID se koristi direktno u konstrukciji putanje (WT_DIR) i imena grane.
# Bez ove provere, task-id kao "../../etc" bi omogućio path traversal van
# WT_ROOT (write/delete van namenjenog direktorijuma). Dozvoljavamo samo
# alfanumerike, crtice i donje crte - dovoljno za bilo koji smislen task-id,
# ništa što bash/git može tumačiti kao putanju ili opciju.
if [[ ! "${TASK_ID}" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo "GREŠKA: task-id '${TASK_ID}' sadrži nedozvoljene karaktere. Dozvoljeno: a-z A-Z 0-9 _ -" >&2
  exit 1
fi
if [[ ! "${MAX_ITERATIONS}" =~ ^[0-9]+$ ]] || [[ ! "${MAX_WALL_CLOCK_SEC}" =~ ^[0-9]+$ ]]; then
  echo "GREŠKA: max-iterations i max-wall-clock-sec moraju biti pozitivni celi brojevi." >&2
  exit 1
fi
if [[ ! -f "${PROMPT_FILE}" ]]; then
  echo "GREŠKA: prompt-file '${PROMPT_FILE}' ne postoji." >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
WT_ROOT="${REPO_ROOT}/../worktrees"
WT_DIR="${WT_ROOT}/${TASK_ID}"
BRANCH_NAME="agent/${TASK_ID}-$(date +%s)"
REGISTRY_FILE="${REPO_ROOT}/.agent-orchestrator/registry.json"

mkdir -p "${WT_ROOT}" "${REPO_ROOT}/.agent-orchestrator"

# --- Atomicna rezervacija task-id-a (hardening: paralelni spawn race) ---
# `mkdir` je atomican na POSIX fajl-sistemima - ako dva procesa istovremeno
# pozovu spawn sa ISTIM task-id-om, tacno JEDAN uspeva ovde, drugi odmah i
# CISTO otkazuje, PRE nego sto bilo sta dotakne git. Bez ovoga oba procesa
# nastavljaju do `git worktree add`, gde git-ov interni ref-lock katkad (ne
# uvek pouzdano na svim fajl-sistemima/bridge-ovima - potvrdjeno testom)
# sprecava korupciju, ali cistka posle toga moze biti oteta dozvolama
# fajl-sistema i ostaviti neregistrovan, "siroce" worktree na disku.
CLAIM_DIR="${REPO_ROOT}/.agent-orchestrator/claims"
mkdir -p "${CLAIM_DIR}"
CLAIM_PATH="${CLAIM_DIR}/${TASK_ID}"
CLAIM_STALE_SEC=3600   # posle ovoliko, claim se preuzima i ako je PID (redak slucaj reuse-a) i dalje "ziv"

# --- Nezavisna provera (drugi krug, adversarijalno): `kill -9` posle uspesnog
# claim-a a pre `release_claim` ostavlja claim TRAJNO zaglavljen, jer skripta
# trap-uje samo ERR, ne i signale (SIGKILL se uopste ne moze uhvatiti).
# Zato claim sad nosi PID + vreme, i acquire_claim proverava da li je
# POSTOJECI claim zaista ziv (proces jos postoji I nije prestar) pre nego sto
# ga tretira kao aktivnu rezervaciju - inace ga preuzima.
acquire_claim() {
  if mkdir "${CLAIM_PATH}" 2>/dev/null; then
    echo "$$" > "${CLAIM_PATH}/pid"
    date +%s > "${CLAIM_PATH}/claimed_at"
    return 0
  fi
  local owner_pid claimed_at now age
  owner_pid="$(cat "${CLAIM_PATH}/pid" 2>/dev/null || echo "")"
  claimed_at="$(cat "${CLAIM_PATH}/claimed_at" 2>/dev/null || echo "")"
  # Fail-closed ako metapodaci nisu (jos) tu ili nisu brojevi - to znaci da je
  # claim upravo NEGDE u fazi preuzimanja (mkdir uspeo, upis u toku), NE da je
  # zaostao. Reklamiranje ovde bi ponovo otvorilo isti race koji je claim
  # trebalo da zatvori - radije pusti ovaj pokusaj da otkaze, gubitnik ce
  # prirodno probati ponovo kasnije (spolja, ne unutar ove skripte).
  if [[ ! "${owner_pid}" =~ ^[0-9]+$ ]] || [[ ! "${claimed_at}" =~ ^[0-9]+$ ]]; then
    return 1
  fi
  now="$(date +%s)"
  age=$(( now - claimed_at ))
  if [[ "${age}" -ge 0 ]] && [[ "${age}" -lt "${CLAIM_STALE_SEC}" ]] && kill -0 "${owner_pid}" 2>/dev/null; then
    return 1   # zaista aktivan - pravi konkurentni spawn u toku
  fi
  if [[ "${age}" -lt 0 ]]; then
    return 1   # clock skew - ne pretpostavljaj nista, samo odbij ovaj pokusaj
  fi
  echo "NAPOMENA: zaostao claim za '${TASK_ID}' (pid=${owner_pid}, starost=${age}s, proces vise ne postoji ili je claim prestar) - preuzimam." >&2
  rm -rf "${CLAIM_PATH}"
  if mkdir "${CLAIM_PATH}" 2>/dev/null; then
    echo "$$" > "${CLAIM_PATH}/pid"
    date +%s > "${CLAIM_PATH}/claimed_at"
    return 0
  fi
  return 1   # neko drugi ga je upravo preuzeo u međuvremenu (retka trka) - fail-safe
}
if ! acquire_claim; then
  echo "GREŠKA: task-id '${TASK_ID}' je već zauzet (aktivna spawn operacija u toku)." >&2
  exit 1
fi
release_claim() { rm -rf "${CLAIM_PATH}" 2>/dev/null || true; }

if [[ -d "${WT_DIR}" ]]; then
  echo "GREŠKA: worktree ${WT_DIR} već postoji. Očisti ga prvo (git worktree remove) ili izaberi drugi task-id." >&2
  release_claim
  exit 1
fi

# --- Cleanup na grešku usred kreiranja (nadograđeno posle audita) ---
# Bez ovoga, ako korak 2/3/4 pukne posle uspešnog `git worktree add`,
# ostaje "napola" worktree koji blokira ponovno pokretanje istog task-id-a
# i zbunjuje `git worktree list`.
CLEANUP_NEEDED=1
cleanup_on_failure() {
  if [[ "${CLEANUP_NEEDED}" -eq 1 ]]; then
    echo "GREŠKA usred kreiranja - čistim delimično kreiran worktree ${WT_DIR}..." >&2
    git -C "${REPO_ROOT}" worktree remove --force "${WT_DIR}" 2>/dev/null || rm -rf "${WT_DIR}"
    git -C "${REPO_ROOT}" branch -D "${BRANCH_NAME}" 2>/dev/null || true
  fi
  release_claim
}
trap cleanup_on_failure ERR

echo "== 1. Kreiram worktree i izolovanu granu =="
git -C "${REPO_ROOT}" worktree add "${WT_DIR}" -b "${BRANCH_NAME}" "${BASE_BRANCH}"

echo "== 2. Postavljam in-band memoriju u worktree =="
mkdir -p "${WT_DIR}/.agent"

# --- Iskljuci .agent/ iz git-a (nalaz iz PRVOG UZIVO end-to-end pilota) ---
# `.agent/` je orkestracija/radna memorija (scratchpad, task_log, approvals,
# checker_bundle) - NIKAD ne sme da zavrsi u commit-u na agent granu. Bez
# ovoga, `git add -A` (sasvim realan Maker-ov korak) komituje CEO .agent/,
# sto pravi DVA problema: (1) trajno zagadi git istoriju bookkeeping fajlovima
# koji nemaju veze sa kodom, i (2) OZBILJNIJE - ako se .agent/ komituje, onda
# prepare-checker-bundle.sh-ov `git diff <base>` (koji hvata SVE izmene u
# odnosu na base granu, komitovane i ne) POKAZUJE scratchpad.md/task_log.md
# KAO DEO diff.patch-a, iako ih bundle skripta namerno NE kopira direktno -
# ovo tiho ponisti CELU Domen 2 kontekst-izolaciju kroz sporedna vrata.
# Koristimo .git/info/exclude (deljen izmedju worktree-ova istog repo-a, ne
# menja korisnikov pravi .gitignore) umesto pravljenja .gitignore fajla u
# samom worktree-u, koji bi i sam morao da se komituje da bi vazio.
COMMON_GIT_DIR="$(git -C "${WT_DIR}" rev-parse --git-common-dir)"
mkdir -p "${COMMON_GIT_DIR}/info"
# Uz .agent/ (kritično, vidi napomenu iznad), isključujemo i standardne
# build-artefakte koje `uv sync`/`npm install` prave U SAMOM worktree-u
# (.venv/, node_modules/) i Python bytecode keš (__pycache__/, *.pyc) - ovo
# NIJE bezbednosni propust kao .agent/, samo šum koji zatrpava diff.patch
# i otežava Checker-u da proceni STVARNU izmenu (nezavisno potvrđeno u istom
# pilotu - konkretan diff je sadržao .pyc binarne fajlove bez ove ispravke).
EXCLUDE_LOCK="${COMMON_GIT_DIR}/info/.exclude.lock"
_exclude_lock_acquired=0
for _try in 1 2 3 4 5; do
  if mkdir "${EXCLUDE_LOCK}" 2>/dev/null; then
    _exclude_lock_acquired=1
    break
  fi
  sleep 1
done
for pattern in '.agent/' '__pycache__/' '*.pyc' '.venv/' 'node_modules/'; do
  grep -qxF "${pattern}" "${COMMON_GIT_DIR}/info/exclude" 2>/dev/null || echo "${pattern}" >> "${COMMON_GIT_DIR}/info/exclude"
done
[[ "${_exclude_lock_acquired}" -eq 1 ]] && rmdir "${EXCLUDE_LOCK}" 2>/dev/null || true

cp "$(dirname "$0")/../templates/scratchpad.md" "${WT_DIR}/.agent/scratchpad.md"
cp "$(dirname "$0")/../templates/task_log.md" "${WT_DIR}/.agent/task_log.md"
cp "${PROMPT_FILE}" "${WT_DIR}/.agent/task_spec.md"

cat > "${WT_DIR}/.agent/loop_state.json" <<EOF
{
  "task_id": "${TASK_ID}",
  "branch": "${BRANCH_NAME}",
  "iteration_count": 0,
  "max_iterations": ${MAX_ITERATIONS},
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "max_wall_clock_sec": ${MAX_WALL_CLOCK_SEC},
  "error_signatures": [],
  "status": "running"
}
EOF

echo "== 3. Zavisnosti (podesi po projektu — primer za Node/pnpm) =="
# NAPOMENA (treći krug provere): prethodni `alat-postoji && pokreni || fallback`
# obrazac je maskirao STVARAN pad pnpm/uv instalacije kao "pnpm ne postoji,
# probaj npm" - ako pnpm postoji ALI padne (npr. mrežni problem), tiho bi
# prešlo na npm i moglo napraviti konfliktan lockfile bez ijedne poruke o
# pravom uzroku. Sad razdvajamo "alat ne postoji" (legitiman fallback) od
# "alat postoji ali je pao" (stvarna greška, treba da se vidi).
# NAPOMENA (ispravka unutar trećeg kruga): `|| { ...; exit 1; }` je IZGLEDAO
# ispravno ali je bag - eksplicitan `exit` NE aktivira `trap ... ERR` u bash-u
# (za razliku od komande koja prosto vrati ne-nula status), pa bi cleanup trap
# definisan gore u skripti bio preskočen baš u ovim granama. Zato ovde
# koristimo `echo greška; false` - `false` je obična komanda sa ne-nula
# statusom i ISPRAVNO aktivira ERR trap pod `set -e`.
if [[ -f "${WT_DIR}/package.json" ]]; then
  if command -v pnpm >/dev/null; then
    if ! (cd "${WT_DIR}" && pnpm install --prefer-offline); then
      echo "GREŠKA: pnpm install pao (pnpm POSTOJI - ovo nije 'pnpm nedostaje')." >&2
      false
    fi
  else
    if ! (cd "${WT_DIR}" && npm install); then
      echo "GREŠKA: npm install pao." >&2
      false
    fi
  fi
elif [[ -f "${WT_DIR}/pyproject.toml" ]]; then
  if command -v uv >/dev/null; then
    if ! (cd "${WT_DIR}" && uv sync); then
      echo "GREŠKA: uv sync pao (uv POSTOJI - ovo nije 'uv nedostaje')." >&2
      false
    fi
  else
    if ! (cd "${WT_DIR}" && pip install -e . --break-system-packages); then
      echo "GREŠKA: pip install pao." >&2
      false
    fi
  fi
fi

echo "== 4. Registrujem task u deljeni registry (optimistic concurrency) =="
python3 "$(dirname "$0")/registry_write.py" \
  --registry "${REGISTRY_FILE}" \
  --task-id "${TASK_ID}" \
  --branch "${BRANCH_NAME}" \
  --worktree "${WT_DIR}" \
  --status running

CLEANUP_NEEDED=0   # sve uspelo - trap iznad se od ovog trenutka ne aktivira
release_claim       # oslobodi rezervaciju - od sada WT_DIR postojanje stiti od ponovne upotrebe

echo ""
echo "Worktree spreman: ${WT_DIR}"
echo "Grana: ${BRANCH_NAME}"
echo "Hard Ceiling: ${MAX_ITERATIONS} iteracija / ${MAX_WALL_CLOCK_SEC}s wall-clock"
echo ""
echo "SLEDEĆI KORAK (ručno prilagoditi CLI pozivu koji koristiš):"
echo "  cd ${WT_DIR} && claude -p \"\$(cat .agent/task_spec.md)\" --permission-mode ask"
echo ""
echo "Posle svake iteracije pokreni:"
echo "  ./checker-verify.sh ${WT_DIR}"
echo "i proveri .agent/loop_state.json pre nego što dozvoliš sledeću iteraciju."
