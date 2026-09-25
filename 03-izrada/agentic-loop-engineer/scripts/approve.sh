#!/usr/bin/env bash
# approve.sh - ČOVEK pokreće ovo ručno da odobri TAČNO JEDNU pending akciju.
#
# Ne odobrava tip komande zauvek, samo tu jednu, tekstualno-identičnu akciju
# (identifikovanu token-om) - sledeći put kad agent pokuša nešto slično ali
# ne bit-za-bit isto, guardrail_check.py će ponovo tražiti odobrenje.
#
# Usage:
#   ./approve.sh <worktree-dir> <token>
#
# Token dolazi iz poruke koju je guardrail_check.py vratio agentu, ili iz
# fajla <worktree-dir>/.agent/pending_human_approval/<token>.json

set -euo pipefail

WT_DIR="${1:?Usage: approve.sh <worktree-dir> <token>}"
TOKEN="${2:?token je obavezan (vidi .agent/pending_human_approval/*.json)}"

PENDING_FILE="${WT_DIR}/.agent/pending_human_approval/${TOKEN}.json"
APPROVALS_DIR="${WT_DIR}/.agent/approvals"

if [[ ! -f "${PENDING_FILE}" ]]; then
  echo "GREŠKA: nema pending zahteva za token '${TOKEN}' u ${PENDING_FILE}" >&2
  exit 1
fi

echo "== Pending zahtev =="
cat "${PENDING_FILE}"
echo ""
read -r -p "Odobravaš TAČNO ovu akciju, jednokratno? (da/ne): " CONFIRM
if [[ "${CONFIRM}" != "da" ]]; then
  echo "Otkazano - odobrenje NIJE upisano."
  exit 0
fi

mkdir -p "${APPROVALS_DIR}"
python3 - "${APPROVALS_DIR}/${TOKEN}.json" <<'EOF'
import json, sys, time
path = sys.argv[1]
with open(path, "w", encoding="utf-8") as f:
    json.dump({
        "approved": True,
        "consumed": False,
        "approved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, f, indent=2)
EOF

echo "Odobreno jednokratno - token ${TOKEN}. Reci agentu da ponovo pošalje TAČNO istu akciju."
