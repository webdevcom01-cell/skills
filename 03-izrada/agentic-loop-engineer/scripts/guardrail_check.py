#!/usr/bin/env python3
"""
guardrail_check.py

STVARNI enforcement mehanizam za config/guardrails.yaml - ovo je nedostajalo
u prvoj verziji v2 paketa (SKILL.md je tvrdio da "orkestrator proverava svaku
komandu", ali nijedna skripta to nije radila). Implementiran je kao pravi
Claude Code PreToolUse hook, po zvaničnoj shemi:
https://code.claude.com/docs/en/hooks (verifikovano tokom audita, 2026-09,
i PONOVO nezavisno verifikovano u trećem krugu provere - vidi napomenu ispod).

Wiring (vidi hooks/settings.snippet.json):
  .claude/settings.json -> hooks.PreToolUse -> matcher "*" (ili "" / omit)
  -> command: python3 .../guardrail_check.py

Ulaz (stdin, JSON, šalje ga Claude Code):
  {"tool_name": "Bash", "tool_input": {"command": "..."}, "cwd": "...", ...}
  ili za MCP alate: {"tool_name": "mcp__Gmail__send_message", "tool_input": {...}, ...}

Izlaz (stdout, JSON) kad pravilo pogodi:
  {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                           "permissionDecision": "deny",
                           "permissionDecisionReason": "..."}}
Bez izlaza (exit 0) kad ništa ne pogodi - normalan permission flow se primenjuje.

ISPRAVKA POSLE TREĆEG KRUGA PROVERE (nezavisna verifikacija otkrila grešku
iz drugog kruga): `permissionDecision` U STVARI PODRŽAVA "ask" vrednost
("allow"/"deny"/"ask" - "ask" prisiljava prompt čoveku, nezavisno od
permission mode-a). Prethodna tvrdnja u ovom fajlu da "ask" ne postoji je
bila POGREŠNA - nastala je zbog toga što je alat za dohvatanje dokumentacije
(WebFetch) skratio dugačku stranicu pre relevantne sekcije, dva puta
zaredom, i oba puta "popunio prazninu" pogrešnim zaključkom. Trećim,
ciljanim pokušajem (traženje TAČNO te sekcije, verbatim) dobijen je tačan
odgovor. Pouka: kad izvor za bitnu tehničku tvrdnju daje kratak/sumiran
odgovor na dugačku stranicu, ciljati na TAČAN pod-odeljak pre nego što se
tvrdnja uzme kao potvrđena.

ZAŠTO IPAK NE KORISTIMO "ask" kao primarni mehanizam za `require_human`:
Anthropic-ov zvanični inženjerski blog o "auto mode" (anthropic.com/
engineering/claude-code-auto-mode) eksplicitno kaže: "In headless mode
(claude -p) there is no UI to ask the human, so we instead terminate the
process." Dakle "ask" u headless/autonomnoj petlji (tačno naš ciljani
slučaj - agent bez čoveka po ciklusu) NE čeka odgovor, nego GASI proces -
gubi se mogućnost da se petlja kasnije nastavi kad čovek stigne da
pregleda. Zato ovaj skript i dalje koristi "deny + pending-approval +
approve.sh" kao PRIMARNI mehanizam (radi identično i u interaktivnoj i u
headless sesiji, i dozvoljava asinhroni nastavak), ali ovo je sad SVESNA
inženjerska odluka zasnovana na tačnoj premisi, ne posledica pogrešnog
uverenja da "ask" ne postoji. Ako znaš da UVEK radiš interaktivno, "ask"
je jednostavnija alternativa - vidi SKILL.md sekciju 7.

DRUGA ISPRAVKA (treći krug): matching je sad case-insensitive I
multi-line-safe (re.DOTALL) - nezavisan test je pokazao da je
`git\\s+push\\s+.*--force` promašio komandu razbijenu bash line-continuation-om
(`git push \\` + newline + `--force ...`, legitimna, ne-adversarijalna
sintaksa) jer `.` bez DOTALL ne prelazi preko novog reda.

TREĆA ISPRAVKA (treći krug): cela logika po pravilu je sad u try/except
koji fail-closed-uje (deny) SAMO za tekući tool poziv ako nešto neočekivano
pukne (npr. tool_input nije dict, loš regex) - prethodna verzija je to
ostavljala da probije nezahvaćeno, što bi (po hook exit-code semantici,
"ostali exit kodovi se ignorišu bez validnog JSON izlaza") značilo FAIL-OPEN
na baš toj komandi, suprotno nameri.

ČETVRTA ISPRAVKA (stavka #2 ojačavanja, 16-17. sept 2026 - regex guardrail
bypass, svesno prihvaćen rizik iz guardrails.yaml napomene, sad dopunjen
drugim slojem): regex na SIROVOM tekstu komande ne vidi kroz:
  (a) jeftine whitespace-obfuskacije koje razbijaju "\s+" adjacency u
      postojećim pravilima (backslash-escaped razmak, $IFS umesto razmaka);
  (b) mehanizme indirekcije čiji je CILJ upravo da stvaran sadržaj ne bude
      čitljiv u tekstu komande (eval, command/process substitution kao prva
      reč, alias definicija, base64/hex/openssl decode, ANSI-C $'...' hex
      escape);
  (c) promenljivu ili alias definisan u JEDNOM Bash pozivu i iskorišćen u
      SLEDEĆEM (svaki poziv hook-a je do sada bio potpuno bez pamćenja
      prethodnih poziva u istoj sesiji/cwd-u).
Dokazano baseline testiranjem PRE ove ispravke (svih 6 varijanti realno
zaobilazi postojeća pravila - vidi OJACAVANJE-stavka2-guardrail-indirekcija.md).
Ispravka za (a): normalize_command() pre regex provere. Ispravka za (b):
nova "indirect-*" pravila u guardrails.yaml koja hvataju SAM MEHANIZAM kao
sumnjiv (require_human), ne pokušavaju da dekodiraju sadržaj (opšte
nemoguće protiv proizvoljnog kodiranja - pogrešan cilj). Ispravka za (c):
lagano, best-effort praćenje "NAME=vrednost" i "alias NAME=vrednost" dodela
po cwd-u (.agent/guardrail_var_state.json), sa supstitucijom PRE regex
provere. Supstitucija SAMO DODAJE tekst (nikad ne skida) - ne može uvesti
novi false-negative u odnosu na staro ponašanje; kvar u state fajlu se
hvata odvojenim try/except i pada nazad na normalizovan-ali-nesupstituisan
tekst, da ne obori OSNOVNU, već dokazanu regex proveru zbog kvara u OVOM
dopunskom sloju. I dalje VAŽI napomena iz guardrails.yaml: ovo je nužna ali
NE dovoljna odbrana - vidi taj fajl za listu preostalih, namerno
nezatvorenih rizika (npr. "napiši skriptu pa je izvrši" - to je posao
Checker sloja, ne ovog hook-a).

PETA ISPRAVKA (isti dan, nezavisan adversarijalan review ČETVRTE ispravke -
2 stvarna, dosad nenađena baga u samom cross-call praćenju):

  KRITIČAN: `learn_assignments()` se do sada zvala BEZUSLOVNO, pre nego što
  se zna da li će TEKUĆI poziv uopšte biti dozvoljen. Rezultat: čak i ODBIJENA
  (nikad odobrena) `alias git=...`/`X=...` definicija je i dalje TIHO upisivala
  tu dodelu u state - iako je prava ljuska NIKAD nije izvršila (hook je
  odbio poziv pre izvršenja). Jedan pokušaj `alias rm="echo safe"` (odbijen
  od strane `indirect-alias-define`, nikad odobren) je bio dovoljan da
  supstitucija posle toga tiho prepiše SVAKI budući doslovni `rm -rf ...`
  poziv u `echo safe -rf ...` PRE regex provere - onesposobljavajući
  POSTOJEĆE `rm-rf-outside-worktree` pravilo (i analogno za git-* pravila),
  ne samo nove "indirect-*" provere. Ispravka: učenje je sada odloženo do
  trenutka kad je DOKAZANO da će komanda stvarno biti izvršena - ili nijedno
  pravilo nije pogodilo (kraj petlje), ili je baš OVAJ poziv upravo odobren
  (`allow()` posle potrošenog jednokratnog odobrenja). Odbijena/blokirana
  komanda više NIKAD ne ostavlja trag u state-u, tačno kao što je prava
  ljuska nikad nije ni pokrenula.

  VISOK: `learn_assignments()` je čuvala SIROVU desnu stranu dodele
  (`B="$A"` → state["B"] = "$A", doslovno, ne razrešeno) - lanac dodela
  preko VIŠE od `MAX_SUBSTITUTION_PASSES` (3) ODVOJENIH Bash poziva
  (A="git"; pa B="$A"; pa C="$B"; pa D="$C"; pa `$D push --force...`) je
  ostajao delimično nerazrešen i promašivao proveru - potpuno bez ikakve
  obfuskacije, samo dubina lanca preko poziva. Ispravka: `learn_assignments()`
  sad ODMAH razrešava `$VAR` reference unutar desne strane kroz VEĆ POZNATO
  stanje pre upisa (deljena `_resolve_var_refs()` pomoćna funkcija) - svaka
  zapamćena vrednost je od tog trenutka UVEK potpuno ravna (flat) literal,
  ne pokazivač na drugo ime. Ovo čini dubinu lanca preko poziva irelevantnom
  (svaki novi hop čita već razrešenu vrednost prethodnog).

  Dodatni nalaz (nije bag, stvaran ali svestan gap): `curl ... | bash` i
  `bash <(curl ...)` (proces substitution kao ARGUMENT, ne na poziciji
  komande) i dalje prolaze - klasičan "fetch-and-run" idiom, van dometa
  postojećeg `indirect-command-substitution-as-command` pravila (koje hvata
  SAMO poziciju komande). Zatvoreno sada sa dva nova pravila:
  `indirect-pipe-to-shell` (cev u sh/bash/zsh/dash) i
  `indirect-process-substitution` (`<(` bilo gde u tekstu).
"""
import sys
import os
import json
import re
import hashlib
import time

try:
    import yaml
except ImportError:
    print("guardrail_check.py: nedostaje PyYAML (`pip install pyyaml --break-system-packages`)."
          " Fail-closed: blokiram poziv dok se ne instalira.", file=sys.stderr)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "guardrail_check.py ne moze da ucita pravila (nedostaje PyYAML) - fail-closed."
        }
    }))
    sys.exit(0)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(SCRIPT_DIR, "..", "config", "guardrails.yaml")

# --- Stavka #2: normalizacija jeftinih whitespace-obfuskacija -------------
IFS_TOKEN_RE = re.compile(r'\$\{?IFS\}?(?:\$\{?9\}?)?')
BACKSLASH_WS_RE = re.compile(r'\\([ \t\n])')


def normalize_command(text: str) -> str:
    """Poništava jeftine whitespace-obfuskacione trikove PRE regex provere,
    bez pokušaja pune bash tokenizacije - ne menja semantiku VEĆ TAČNIH
    pravila, samo vraća razmak tamo gde bi bash inače video razmak."""
    if not text:
        return text
    text = IFS_TOKEN_RE.sub(' ', text)
    text = BACKSLASH_WS_RE.sub(r'\1', text)
    return text


# --- Stavka #2: lagano cross-call praćenje promenljivih/alias-a -----------
STATE_FILENAME = "guardrail_var_state.json"
MAX_TRACKED_NAMES = 50
MAX_SUBSTITUTION_PASSES = 3
MAX_VALUE_LEN = 2000
MAX_TEXT_LEN = 20000

# Konzervativno: uči SAMO doslovne (string-literal) dodele na početku
# komande ili posle ;/&&/||/newline separatora. Ako je desna strana sama
# command substitution ($(...) ili `...`), NE može se statički razrešiti pa
# se PRESKAČE (bolje ne znati nego uneti pogrešnu vrednost).
VAR_ASSIGN_RE = re.compile(
    r'(?:^|[;\n]|&&|\|\|)\s*([A-Za-z_][A-Za-z0-9_]*)=(?:"([^"]*)"|\'([^\']*)\'|(\S+))'
)
ALIAS_ASSIGN_RE = re.compile(
    r'\balias\s+([A-Za-z_][A-Za-z0-9_]*)=(?:"([^"]*)"|\'([^\']*)\'|(\S+))'
)
VAR_REF_RE = re.compile(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?')


def _state_path(cwd: str) -> str:
    return os.path.join(cwd, ".agent", STATE_FILENAME)


def load_indirection_state(cwd: str) -> dict:
    path = _state_path(cwd)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"vars": {}, "aliases": {}}
        data.setdefault("vars", {})
        data.setdefault("aliases", {})
        if not isinstance(data["vars"], dict):
            data["vars"] = {}
        if not isinstance(data["aliases"], dict):
            data["aliases"] = {}
        return data
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        return {"vars": {}, "aliases": {}}


def save_indirection_state(cwd: str, state: dict) -> None:
    path = _state_path(cwd)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for key in ("vars", "aliases"):
            items = list(state.get(key, {}).items())
            if len(items) > MAX_TRACKED_NAMES:
                state[key] = dict(items[-MAX_TRACKED_NAMES:])
        tmp_path = f"{path}.tmp{os.getpid()}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp_path, path)
    except OSError:
        # Praćenje kroz pozive je DOPUNSKI sloj - greška ovde (npr. disk
        # pun, permisije) ne sme srušiti osnovnu, već dokazanu proveru.
        pass


def _resolve_var_refs(text: str, variables: dict, max_passes: int = MAX_SUBSTITUTION_PASSES) -> str:
    """Zameni $VAR/${VAR} reference u `text` poznatim vrednostima iz
    `variables`, u ograničenom broju prolaza (hvata i lanac referenci
    UNUTAR jednog stringa, npr. desna strana koja i sama sadrži $DRUGO_IME).
    Deljena između substitute_tracked() (ceo tekst komande) i
    learn_assignments() (samo desna strana NOVE dodele - vidi PETA ISPRAVKA
    u modul-docstring-u: dodele se sad čuvaju već RAZREŠENE, ne kao sirovi
    pokazivač na drugo ime, čime dubina lanca PREKO poziva postaje
    irelevantna)."""
    if not variables:
        return text

    def _sub(m):
        return variables.get(m.group(1), m.group(0))

    for _ in range(max_passes):
        new_text = VAR_REF_RE.sub(_sub, text)
        if new_text == text:
            break
        text = new_text
    return text


def learn_assignments(raw_text: str, state: dict) -> None:
    """Upisuje NOVE `NAME=vrednost`/`alias NAME=vrednost` dodele u state.
    POZIVA SE SAMO kad je već dokazano da će `raw_text` stvarno biti
    izvršen od strane prave ljuske (vidi PETA ISPRAVKA) - nikad za komandu
    koju je neko pravilo odbilo/blokiralo."""
    for m in VAR_ASSIGN_RE.finditer(raw_text):
        name = m.group(1)
        value = m.group(2) if m.group(2) is not None else (
            m.group(3) if m.group(3) is not None else m.group(4))
        if value is None or '$(' in value or '`' in value:
            continue
        # Razreši $VAR reference unutar desne strane KROZ VEĆ POZNATO stanje
        # (uklj. dodele naučene ranije u OVOM istom raw_text-u, jer
        # finditer ide levo-desno i state["vars"] se menja u hodu) - vrednost
        # se pamti UVEK potpuno ravna (flat), ne kao pokazivač na drugo ime.
        resolved_value = _resolve_var_refs(value, state["vars"])
        state["vars"][name] = resolved_value[:MAX_VALUE_LEN]
    for m in ALIAS_ASSIGN_RE.finditer(raw_text):
        name = m.group(1)
        value = m.group(2) if m.group(2) is not None else (
            m.group(3) if m.group(3) is not None else m.group(4))
        if value is None or '$(' in value or '`' in value:
            continue
        resolved_value = _resolve_var_refs(value, state["vars"])
        state["aliases"][name] = resolved_value[:MAX_VALUE_LEN]


def substitute_tracked(text: str, state: dict) -> str:
    """Zameni poznate alias-e (samo na početku (pod)komande, kako shell
    zaista širi alias-e) i $VAR/${VAR} reference (bilo gde) njihovim
    poslednjim poznatim vrednostima, u ograničenom broju prolaza. Ovo NIKAD
    ne uklanja tekst, samo ga dopunjuje - ne može uvesti novi
    false-negative u odnosu na trenutno ponašanje bez ovog sloja."""
    aliases = state.get("aliases") or {}
    variables = state.get("vars") or {}

    if aliases:
        alias_re = re.compile(
            r'(^|[;\n]|&&|\|\||\|)(\s*)(' +
            '|'.join(re.escape(a) for a in sorted(aliases, key=len, reverse=True)) +
            r')\b'
        )

        def _alias_sub(m):
            return f"{m.group(1)}{m.group(2)}{aliases[m.group(3)]}"

        for _ in range(MAX_SUBSTITUTION_PASSES):
            new_text = alias_re.sub(_alias_sub, text)
            if new_text == text:
                break
            text = new_text

    text = _resolve_var_refs(text, variables)
    return text[:MAX_TEXT_LEN]


def resolve_bash_text(raw_cmd: str, cwd: str):
    """Vraća (tekst za regex proveru, state dict ili None) za dati sirovi
    Bash tekst: tekst je normalizovan i (best-effort) supstituisan poznatim
    promenljivim/alias-ima iz PRETHODNIH poziva u istom cwd-u. NE uči nove
    dodele ovde - to radi caller (evaluate()) tek kad je dokazano da će
    komanda stvarno biti izvršena, vidi PETA ISPRAVKA u modul-docstring-u.
    state je None ako je dopunski sloj pukao (state fajl nečitljiv i sl.) -
    u tom slučaju se vraća normalizovan-ali-nesupstituisan tekst, a caller
    ne pokušava da uči/upiše (nema šta bezbedno da uradi bez state-a)."""
    normalized = normalize_command(raw_cmd)
    try:
        state = load_indirection_state(cwd)
        resolved = substitute_tracked(normalized, state)
        return resolved, state
    except Exception:
        # Dopunski sloj je pukao - padni nazad na normalizovan (ali
        # nesupstituisan) tekst, ne obaraj proveru koja je već dokazana.
        return normalized, None


def load_rules(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("rules", [])


def match_text_for_scope(scope: str, tool_name: str, tool_input) -> str:
    """Vraća tekst za regex proveru, ili None ako scope ne odgovara ovom pozivu.
    tool_input možda NIJE dict (odbrambeno - Claude Code bi trebalo uvek da
    šalje dict, ali ne pretpostavljamo to bez provere posle nalaza iz audita)."""
    if not isinstance(tool_input, dict):
        tool_input = {}
    if scope == "bash":
        if tool_name != "Bash":
            return None
        return str(tool_input.get("command", ""))
    if scope == "tool_name":
        return tool_name
    if scope == "any":
        return f"{tool_name} {json.dumps(tool_input, ensure_ascii=False)}"
    return None


def approval_token(rule_id: str, match_text: str) -> str:
    h = hashlib.sha256(f"{rule_id}:{match_text}".encode("utf-8")).hexdigest()
    return h[:16]


def deny(reason: str):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))
    sys.exit(0)


def allow(reason: str):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))
    sys.exit(0)


def evaluate(hook_input: dict, rules: list):
    """Sva logika po pravilu, izdvojena da bi cela mogla biti pod jednim
    try/except u main() - bilo koji neočekivan izuzetak ovde treba da
    fail-closed-uje SAMO ovaj tool poziv (deny), ne da probije nezahvaćen."""
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    cwd = hook_input.get("cwd") or os.getcwd()

    approvals_dir = os.path.join(cwd, ".agent", "approvals")
    pending_dir = os.path.join(cwd, ".agent", "pending_human_approval")

    # Stavka #2: za PRAVE Bash pozive, računamo prošireni (normalizovan +
    # supstituisan) tekst JEDNOM ovde i koristimo ga za svako "scope: bash"
    # pravilo ispod - vidi resolve_bash_text() i modul-level napomenu.
    raw_cmd = None
    resolved_bash_text = None
    indirection_state = None
    if tool_name == "Bash" and isinstance(tool_input, dict):
        raw_cmd = str(tool_input.get("command", ""))
        resolved_bash_text, indirection_state = resolve_bash_text(raw_cmd, cwd)

    def commit_learned_state():
        """PETA ISPRAVKA: poziva se SAMO na mestima gde je dokazano da će
        TEKUĆA bash komanda stvarno biti izvršena od prave ljuske (nijedno
        pravilo je nije odbilo/blokiralo, ili je upravo odobrena) - nikad za
        odbijenu/blokiranu komandu, čije dodele prava ljuska nikad nije
        primenila. Vidi modul-docstring, KRITIČAN nalaz nezavisnog review-a."""
        if raw_cmd is None or indirection_state is None:
            return
        try:
            learn_assignments(raw_cmd, indirection_state)
            save_indirection_state(cwd, indirection_state)
        except Exception:
            # Dopunski sloj - greška ovde ne sme uticati na već donetu
            # odluku o TEKUĆEM pozivu (ova funkcija se zove POSLE odluke).
            pass

    for rule in rules:
        scope = rule.get("scope", "bash")
        pattern = rule.get("pattern", "")
        if scope == "bash" and resolved_bash_text is not None:
            text = resolved_bash_text
        else:
            text = match_text_for_scope(scope, tool_name, tool_input)
        if text is None:
            continue
        # re.DOTALL: komanda može legitimno sadržati nove redove (bash line
        # continuation, heredoc, itd) - '.' mora preći preko njih da bi
        # pravilo pogodilo komandu razbijenu preko više redova.
        if not re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            continue

        rule_id = rule.get("id", "unknown-rule")
        action = rule.get("action", "require_human")
        reason = rule.get("reason", "Guardrail pravilo pogođeno.")
        token = approval_token(rule_id, text)

        if action == "block":
            deny(f"[BLOCKED - {rule_id}] {reason}. Ova kategorija akcija se ne odobrava kroz agenta - "
                 f"čovek mora ovo izvršiti sam, van agentske petlje.")

        # action == require_human
        approval_file = os.path.join(approvals_dir, f"{token}.json")
        if os.path.exists(approval_file):
            with open(approval_file, "r", encoding="utf-8") as f:
                approval = json.load(f)
            if approval.get("approved") and not approval.get("consumed"):
                approval["consumed"] = True
                approval["consumed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                with open(approval_file, "w", encoding="utf-8") as f:
                    json.dump(approval, f, indent=2, ensure_ascii=False)
                # Ova komanda ce STVARNO biti izvrsena sada (covek je
                # odobrio) - bezbedno je uciti njene dodele. Vidi PETA
                # ISPRAVKA.
                commit_learned_state()
                allow(f"[{rule_id}] Jednokratno odobreno od strane čoveka (token {token}), sada potrošeno.")

        os.makedirs(pending_dir, exist_ok=True)
        pending_file = os.path.join(pending_dir, f"{token}.json")
        if not os.path.exists(pending_file):
            with open(pending_file, "w", encoding="utf-8") as f:
                json.dump({
                    "token": token,
                    "rule_id": rule_id,
                    "reason": reason,
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }, f, indent=2, ensure_ascii=False)

        deny(f"[{rule_id}] {reason}. Ovo zahteva ljudsko odobrenje. Zaustavi se, NE pokušavaj "
             f"zaobilazan pristup istom cilju, i obavesti da je potrebna potvrda za token {token} "
             f"(zapis u .agent/pending_human_approval/{token}.json). Nastavi tek pošto čovek pokrene "
             f"`approve.sh {token}` i ti ponovo pošalješ TAČNO istu akciju.")

    # Nijedno pravilo nije pogođeno - bez odluke, normalan permission flow -
    # komanda CE stvarno biti izvrsena, bezbedno je uciti njene dodele sada.
    commit_learned_state()


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Ovo bi značilo da Claude Code šalje nešto što ne odgovara
        # sopstvenom dokumentovanom hook ugovoru - u praksi se ne dešava.
        # Namerno NE fail-closed-ujemo ovde (za razliku od greške unutar
        # evaluate()): to bi blokiralo SVAKI tool poziv u sesiji na osnovu
        # greške u ulazu koju ne kontrolišemo, umesto da fail-closed bude
        # ograničen na tool pozive koje smo stvarno uspeli da protumačimo.
        sys.exit(0)

    config_path = os.environ.get("GUARDRAILS_CONFIG", DEFAULT_CONFIG)
    try:
        rules = load_rules(config_path)
    except (FileNotFoundError, yaml.YAMLError) as e:
        deny(f"guardrail_check.py ne moze da ucita {config_path} ({e}) - fail-closed dok se ne popravi.")
        return

    try:
        evaluate(hook_input, rules)
    except SystemExit:
        raise  # deny()/allow() koriste sys.exit(0) namerno - to nije greška
    except Exception as e:
        # Bilo šta neočekivano unutar evaluacije JEDNOG tool poziva -
        # fail-closed SAMO za taj poziv, ne ostavljati da probije kao
        # nezahvaćen traceback (što bi po hook exit-code semantici bilo
        # fail-open, suprotno nameri celog mehanizma).
        deny(f"guardrail_check.py interna greška ({type(e).__name__}: {e}) - fail-closed dok se ne istraži.")

    sys.exit(0)


if __name__ == "__main__":
    main()
