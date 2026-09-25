#!/usr/bin/env bash
# portable-repo-transfer.sh
#
# Nalaz iz DEPLOY runde 8 (PILOT-runda8-DEPLOY-live-railway.md, "Put do GitHub repoa"):
# jednostavan `tar czf` nad jednim git *worktree* direktorijumom NE proizvodi prenosiv git
# repo -- worktree-ov `.git` je TEKSTUALNI FAJL-POKAZIVAČ (`gitdir: /apsolutna/putanja/do/
# glavnog/repoa/.git/worktrees/<ime>`), ne folder. Na drugoj mašini (ili posle raspakivanja
# negde drugde) ta putanja ne postoji, pa `git status`/`git push`/bilo šta puca sa
# `fatal: not a git repository`. Ovo je REPRODUKOVANO uživo u rundi 8 i koštalo je nekoliko
# krugova pokušaja pre nego što je otkriveno.
#
# Ovaj skript rešava to jednom komandom (`git bundle`) umesto ručnim `git clone
# --no-hardlinks` + tar + prenos + raspakivanje, koji je bio ad-hoc ispravka u rundi 8.
# `git bundle` je JEDAN samostalan binarni fajl koji sadrži KOMPLETNU istoriju (svi komiti,
# sve grane koje eksplicitno navedeš) -- nema `.git` folder, nema pokazivače na druge
# putanje, radi identično bilo gde se otvori. To je git-ov ugrađen, prvorazredan mehanizam
# za ovo -- ne treba mu nikakva posebna alatka da bi bio "prenosiv".
#
# === Runda 6 (18. sept 2026) — dve ispravke posle OCENA-sistema-posle-runde-10-11 ===
#
# ISPRAVKA #1 — "git bundle verify" cwd-zavisnost (bag viđen UŽIVO 3 puta: import u rundi
# 10, export DVA puta u rundi 11, dokumentovano i u full-agentic-loop skillovom "Known
# gotcha #1"). `git bundle verify <fajl>` zahteva da se komanda izvrši IZ NEKOG git repoa —
# nije da bundle fajl mora biti "unutra", nego sam `git` binarni alat odbija svaku komandu
# van repoa. Kad se ovaj skript pozivao iz običnog foldera (ne iz repoa), verify je pucao sa
# "fatal: not a git repository" ČAK I KAD JE BUNDLE POTPUNO ISPRAVAN — lažni negativni nalaz.
# Ispravka: `bundle_verify_anywhere()` ispod pravi JEDNOKRATAN, prazan scratch git repo u
# `mktemp -d`, izvršava verify UNUTAR NJEGA (`git -C "$scratch" bundle verify ...`), pa ga
# briše — potpuno nezavisno od toga odakle je skript pozvan. `import`/`sync` koji već rade
# na postojećem ciljnom repou i dalje mogu (i dodatno) da provere i preko njega, ali export/
# import scratch-put je sad DEFAULT, ne pretpostavka o pozivnom cwd-u.
#
# ISPRAVKA #2 — nova `sync` podkomanda. `import` je oduvek radio SAMO fresh `git clone` u
# NEPOSTOJEĆI folder — nema inkrementalni režim. Za drugi/treći krug promena u repo koji već
# postoji na cilju (tačno situacija iz runde 11, urađena DVA PUTA ručno: `git bundle verify`
# pa `git fetch <bundle> <grana>:refs/tmp-incoming` pa `git merge --ff-only refs/tmp-incoming`
# pa `git update-ref -d refs/tmp-incoming`), ta ista sekvenca je sad `sync` podkomanda —
# automatizovana, sa jedinstvenim privremenim ref imenom (uključuje PID, da se ne kosi ako
# se dva transfera pokrenu paralelno na istom cilju) i garantovanim čišćenjem tog ref-a i u
# uspešnom i u neuspešnom slučaju (fast-forward odbijen -> jasna greška, ref ipak obrisan,
# ciljni repo netaknut).
#
# Upotreba:
#   ./portable-repo-transfer.sh export <repo-ili-worktree-dir> <izlazni-fajl.bundle> [grana]
#     - Pravi bundle sa KOMPLETNOM istorijom navedene grane (default: trenutna grana).
#     - ODMAH proverava integritet bundle-a (`git bundle verify`, cwd-nezavisno) PRE nego
#       što ga proglasi gotovim -- ne veruje da je `git bundle create` uspeo samo zato što je
#       vratio exit 0.
#
#   ./portable-repo-transfer.sh import <fajl.bundle> <ciljni-dir>
#     - `git clone` iz bundle-a u ciljni direktorijum -- pravi PRAVI, samostalan `.git`
#       folder (ne pokazivač), odmah proverljivo sa `git log`/`git status`.
#     - Ciljni direktorijum NE SME već postojati (git clone to i inače odbija -- ovo samo
#       daje jasniju grešku unapred).
#
#   ./portable-repo-transfer.sh sync <fajl.bundle> <ciljni-dir> [grana]
#     - Za DRUGI/TREĆI+ krug promena kad ciljni repo VEĆ POSTOJI (import radi samo prvi put).
#     - Fetch + fast-forward-only merge iz bundle-a u ciljni repo, preko privremenog ref-a
#       koji se uvek čisti (uspeh ili neuspeh). Odbija (bez izmene ciljnog repoa) ako merge
#       nije čist fast-forward -- ne pokušava rebase/force, to ostaje ljudska odluka.
#     - Ciljni direktorijum MORA već biti pravi git repo (napravljen ranije preko `import`).
#
# Namerno NE radi remote/push/autentifikaciju -- to ostaje odvojen, eksplicitan korak (vidi
# napomenu u PILOT-runda8-DEPLOY-live-railway.md o tome da git push mora ići kroz KORISNIKOV
# pravi terminal zbog macOS Keychain-a, ne kroz device-bridge šel).

set -euo pipefail

usage() {
  echo "Usage:" >&2
  echo "  $0 export <repo-ili-worktree-dir> <izlazni-fajl.bundle> [grana]" >&2
  echo "  $0 import <fajl.bundle> <ciljni-dir>" >&2
  echo "  $0 sync <fajl.bundle> <ciljni-dir> [grana]" >&2
  exit 1
}

# ISPRAVKA #1: proverava bundle integritet iz JEDNOKRATNOG scratch repoa, tako da rezultat
# nikad ne zavisi od toga odakle je ovaj skript pozvan. Vraća isti exit status kao
# `git bundle verify` samo (stdout/stderr bundle-verify-a se gutaju, isto kao ranije).
bundle_verify_anywhere() {
  local bundle_file="$1"
  local scratch
  scratch="$(mktemp -d)"
  # trap ograničen na ovu funkciju (bash: RETURN trap) -- čisti scratch čak i ako verify
  # padne pod `set -e` kontekstom pozivaoca (pozivalac i dalje hvata neuspeh preko `||`).
  local status=0
  git -C "$scratch" init -q
  git -C "$scratch" bundle verify "$bundle_file" >/dev/null 2>&1 || status=$?
  rm -rf "$scratch"
  return "$status"
}

cmd="${1:-}"
[ -n "$cmd" ] || usage

case "$cmd" in
  export)
    SRC_DIR="${2:?Usage: $0 export <repo-ili-worktree-dir> <izlazni-fajl.bundle> [grana]}"
    OUT_FILE="${3:?Usage: $0 export <repo-ili-worktree-dir> <izlazni-fajl.bundle> [grana]}"
    BRANCH="${4:-}"

    [ -d "$SRC_DIR" ] || { echo "GREŠKA: '$SRC_DIR' ne postoji ili nije direktorijum." >&2; exit 1; }

    # Radi i za obične repoe i za worktree-ove -- `git -C <dir>` razrešava worktree-ov
    # gitdir-pokazivač automatski, isto kao svaka druga git komanda pokrenuta unutra.
    git -C "$SRC_DIR" rev-parse --git-dir >/dev/null 2>&1 || {
      echo "GREŠKA: '$SRC_DIR' nije git repo (ni worktree)." >&2
      exit 1
    }

    if [ -z "$BRANCH" ]; then
      BRANCH="$(git -C "$SRC_DIR" branch --show-current)"
      [ -n "$BRANCH" ] || { echo "GREŠKA: nisi na imenovanoj grani i nisi naveo [grana] argument (detached HEAD?)." >&2; exit 1; }
    fi

    git -C "$SRC_DIR" show-ref --verify --quiet "refs/heads/$BRANCH" || {
      echo "GREŠKA: grana '$BRANCH' ne postoji u '$SRC_DIR'." >&2
      exit 1
    }

    mkdir -p "$(dirname "$OUT_FILE")"

    # VAŽNO: mora da uključi i `HEAD` (ne samo ime grane) u listu refova -- inače `git bundle`
    # ne upiše HEAD-symref u bundle, pa `git clone` na drugom kraju puca sa "remote HEAD refers
    # to nonexistent ref" / "fatal: ambiguous argument 'HEAD'" (nema checkout, nema `git log`).
    # OVO JE UŽIVO REPRODUKOVANO pri testiranju ovog skripta (bez `HEAD` u listi) pre nego što je
    # ispravljeno -- ne izostavljaj `HEAD` ovde.
    git -C "$SRC_DIR" bundle create "$OUT_FILE" HEAD "$BRANCH"

    # NE VERUJ da je create uspeo samo zato što je exit 0 -- proveri integritet bundle-a
    # kao poseban, eksplicitan korak (isti princip kao svuda drugde u ovom skillu: dokaz,
    # ne pretpostavka). Cwd-nezavisno (ISPRAVKA #1) -- radi bilo odakle je skript pozvan.
    bundle_verify_anywhere "$OUT_FILE" || {
      echo "GREŠKA: git bundle verify je pao -- bundle je oštećen ili nepotpun. NE šalji ga dalje." >&2
      exit 1
    }

    COMMIT_COUNT="$(git -C "$SRC_DIR" rev-list --count "$BRANCH")"
    echo "OK: '$OUT_FILE' napravljen i proveren -- grana '$BRANCH', $COMMIT_COUNT komit(a)."
    echo "Prenesi ovaj JEDAN fajl (device_stage_files / SendUserFile / bilo koji način) -- sam je dovoljan, ne treba mu .git folder ni ostatak direktorijuma."
    ;;

  import)
    BUNDLE_FILE="${2:?Usage: $0 import <fajl.bundle> <ciljni-dir>}"
    TARGET_DIR="${3:?Usage: $0 import <fajl.bundle> <ciljni-dir>}"

    [ -f "$BUNDLE_FILE" ] || { echo "GREŠKA: '$BUNDLE_FILE' ne postoji." >&2; exit 1; }
    [ -e "$TARGET_DIR" ] && { echo "GREŠKA: '$TARGET_DIR' već postoji -- izaberi drugu putanju (git clone ne piše preko postojećeg foldera), ili koristi 'sync' ako je ovo VEĆ uvezeni repo koji samo treba da dobije nove komite." >&2; exit 1; }

    # Cwd-nezavisno (ISPRAVKA #1) -- ranije je ovo pucalo kad se skript pozivao iz običnog
    # foldera umesto iz postojećeg repoa.
    bundle_verify_anywhere "$BUNDLE_FILE" || {
      echo "GREŠKA: '$BUNDLE_FILE' ne prolazi 'git bundle verify' -- oštećen ili nepotpun fajl, ne pokušavaj clone." >&2
      exit 1
    }

    git clone "$BUNDLE_FILE" "$TARGET_DIR"

    COMMIT_COUNT="$(git -C "$TARGET_DIR" rev-list --count HEAD)"
    echo "OK: '$TARGET_DIR' je pravi, samostalan git repo ($COMMIT_COUNT komit(a)) -- SPREMAN za 'git remote add origin ...' i push, bez dodatnih koraka."
    ;;

  sync)
    # ISPRAVKA #2: automatizuje sekvencu koja je u rundi 11 rađena ručno DVA PUTA (vidi
    # header komentar) -- inkrementalni transfer novih komita u repo koji VEĆ postoji na
    # cilju, bez ponovnog `git clone` (koji `import` odbija za postojeći folder).
    BUNDLE_FILE="${2:?Usage: $0 sync <fajl.bundle> <ciljni-dir> [grana]}"
    TARGET_DIR="${3:?Usage: $0 sync <fajl.bundle> <ciljni-dir> [grana]}"
    BRANCH="${4:-}"

    [ -f "$BUNDLE_FILE" ] || { echo "GREŠKA: '$BUNDLE_FILE' ne postoji." >&2; exit 1; }
    [ -d "$TARGET_DIR" ] || { echo "GREŠKA: '$TARGET_DIR' ne postoji -- 'sync' je za repo koji VEĆ postoji (napravljen preko 'import'). Za prvi transfer koristi 'import'." >&2; exit 1; }
    git -C "$TARGET_DIR" rev-parse --git-dir >/dev/null 2>&1 || {
      echo "GREŠKA: '$TARGET_DIR' nije git repo -- 'sync' zahteva postojeći repo (napravljen preko 'import')." >&2
      exit 1
    }

    # Verify PROTIV ciljnog repoa (koji već postoji) -- ekvivalentno cwd-nezavisnoj proveri,
    # i ujedno potvrđuje da git uopšte može da čita bundle pre fetch-a.
    git -C "$TARGET_DIR" bundle verify "$BUNDLE_FILE" >/dev/null || {
      echo "GREŠKA: '$BUNDLE_FILE' ne prolazi 'git bundle verify' -- oštećen ili nepotpun fajl, ne pokušavaj fetch." >&2
      exit 1
    }

    if [ -z "$BRANCH" ]; then
      # Prva ne-HEAD-simbolička grana navedena u bundle-u (isti format kao `git ls-remote`:
      # "<sha> <ref>" po liniji; `git bundle create` uvek upisuje i HEAD i ime grane -- vidi
      # export gore -- pa filtriramo tačno "HEAD" liniju i uzimamo prvi refs/heads/* ostatak).
      BRANCH="$(git -C "$TARGET_DIR" bundle list-heads "$BUNDLE_FILE" | awk '$2 != "HEAD" { sub("refs/heads/", "", $2); print $2; exit }')"
      [ -n "$BRANCH" ] || { echo "GREŠKA: ne mogu da odredim granu iz bundle-a -- navedi je eksplicitno kao treći argument." >&2; exit 1; }
    fi

    TMP_REF="refs/tmp-incoming-$$-$(date +%s)"

    # Garantovano čišćenje privremenog ref-a -- i na uspeh i na neuspeh (npr. ff-only odbijen).
    # `|| true` jer je moguće da fetch nikad nije ni stigao do kreiranja ref-a.
    cleanup_tmp_ref() {
      git -C "$TARGET_DIR" update-ref -d "$TMP_REF" >/dev/null 2>&1 || true
    }
    trap cleanup_tmp_ref EXIT

    git -C "$TARGET_DIR" fetch "$BUNDLE_FILE" "$BRANCH:$TMP_REF"

    BEFORE_SHA="$(git -C "$TARGET_DIR" rev-parse HEAD)"

    if ! git -C "$TARGET_DIR" merge --ff-only "$TMP_REF"; then
      echo "GREŠKA: fast-forward merge odbijen -- ciljna grana je otišla u stranu (divergirala) od bundle-a." >&2
      echo "Ciljni repo je NETAKNUT (samo je privremeni ref '$TMP_REF' bio postavljen, sad je obrisan)." >&2
      echo "Ovo namerno NE pokušava rebase/force -- to je ljudska odluka, ne automatska." >&2
      exit 1
    fi

    AFTER_SHA="$(git -C "$TARGET_DIR" rev-parse HEAD)"
    NEW_COMMITS="$(git -C "$TARGET_DIR" rev-list --count "$BEFORE_SHA..$AFTER_SHA")"
    echo "OK: '$TARGET_DIR' ažuriran fast-forward-om, +$NEW_COMMITS novi(h) komit(a) ($BEFORE_SHA -> $AFTER_SHA)."
    ;;

  *)
    usage
    ;;
esac
