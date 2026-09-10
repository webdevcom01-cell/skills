#!/usr/bin/env python3
"""
lint_skill.py — advisory, non-blocking checks for a distilled skill.

Implements the exact thresholds documented and adversarially verified from
Hermes Agent's skill_linter.py (see the project's Hermes research), so these
checks are enforced mechanically instead of depending on the authoring
model's discretion alone. Every check here WARNS; none of them fail the
build — a human (or the authoring agent) decides what to do with the finding.

Usage: python3 lint_skill.py <path/to/skill-folder>
"""
import re
import sys
from pathlib import Path

INCIDENT_REF_MIN = 4
INCIDENT_REF_PER_KCHAR = 0.5
MAX_REFERENCE_FILES = 60
BODY_LINE_SOFT_LIMIT = 500
BODY_TOKEN_SOFT_LIMIT = 5000  # approx, via chars/4 — see note in output
DESCRIPTION_MAX_CHARS = 1024

# Matches "#1234", "PR #1234", "issue 1234" — same pattern documented from
# Hermes' skill_linter.py, case-insensitive.
INCIDENT_REF_PATTERN = re.compile(
    r'(?<![\w/])#\d{3,6}\b|\b(?:PR|issue)\s*#?\d{3,6}\b',
    re.IGNORECASE,
)
CODE_BLOCK_PATTERN = re.compile(r'```.*?```', re.DOTALL)


def strip_code_blocks(text):
    return CODE_BLOCK_PATTERN.sub('', text)


def extract_frontmatter(text):
    """Return the raw frontmatter block (between the first two '---' lines),
    or None if not found. Deliberately not a full YAML parser (keeps this
    script dependency-free) — handles plain and block-scalar description
    values, which covers every style observed in practice."""
    match = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    return match.group(1) if match else None


def extract_description(frontmatter):
    """Extract the description field's effective character count from raw
    frontmatter text. Handles a plain single-line value and YAML block
    scalars ('>', '>-', '|', '|-'). Returns None if no description field is
    found at all — that's quick_validate.py's job to catch, not lint's."""
    lines = frontmatter.split('\n')
    for i, line in enumerate(lines):
        m = re.match(r'^description:\s*(.*)$', line)
        if not m:
            continue
        rest = m.group(1).strip()
        if rest and rest[0] not in ('>', '|'):
            # Plain single-line value — strip matching quotes if present.
            if len(rest) >= 2 and rest[0] == rest[-1] and rest[0] in ('"', "'"):
                rest = rest[1:-1]
            return rest
        # Block scalar (">", ">-", "|", "|-", or bare "|"/">"): collect
        # subsequent indented lines until indentation returns to column 0.
        folded = rest.startswith('>')
        collected = []
        for cont in lines[i + 1:]:
            if cont == '' or cont.startswith(' ') or cont.startswith('\t'):
                collected.append(cont.strip() if folded else cont)
            else:
                break
        joined = ' '.join(collected) if folded else '\n'.join(collected)
        return joined
    return None


def check_description_length(skill_md_path, text):
    frontmatter = extract_frontmatter(text)
    if frontmatter is None:
        return True  # not this script's job — quick_validate.py catches missing/malformed frontmatter
    description = extract_description(frontmatter)
    if description is None:
        return True
    length = len(description)
    if length > DESCRIPTION_MAX_CHARS:
        print(
            f"[WARN] description-length — {skill_md_path}: {length} characters "
            f"(spec limit: {DESCRIPTION_MAX_CHARS}). This is checked here so it "
            "doesn't depend on skill-creator-pro's quick_validate.py being "
            "reachable — count manually or shorten before finalizing."
        )
        return False
    return True


def check_incident_log_shape(path, label, text):
    prose = strip_code_blocks(text)
    matches = INCIDENT_REF_PATTERN.findall(prose)
    count = len(matches)
    kchars = max(len(prose) / 1000, 0.001)
    density = count / kchars
    if count >= INCIDENT_REF_MIN and density >= INCIDENT_REF_PER_KCHAR:
        print(
            f"[WARN] incident-log-shape — {label}: {count} ticket/PR/issue "
            f"references, density {density:.2f}/1000 chars (threshold: "
            f"{INCIDENT_REF_MIN}+ refs AND {INCIDENT_REF_PER_KCHAR}+/1000 chars). "
            "Test: delete every ticket/PR/date from the surrounding sentence — "
            "does the rule still stand on its own? If not, distill the RULE, "
            "not the incident. See references/quality-checks.md."
        )
        return False
    return True


def check_references_sprawl(references_dir):
    if not references_dir.is_dir():
        return True
    files = [
        f for f in references_dir.glob('*.md')
        if not f.name.startswith('_')
    ]
    if len(files) > MAX_REFERENCE_FILES:
        print(
            f"[WARN] references-sprawl — {len(files)} files under references/ "
            f"(threshold: {MAX_REFERENCE_FILES}). Check whether file names "
            "describe TOPICS (aws-deployment.md) or EVENTS "
            "(session-2026-08-14.md). If it's the latter, merge same-topic "
            "files instead of deleting — see references/quality-checks.md."
        )
        return False
    return True


def check_body_budget(skill_md_path, text):
    body = re.sub(r'^---.*?---\n', '', text, count=1, flags=re.DOTALL)
    lines = body.count('\n') + 1
    approx_tokens = len(body) // 4  # rough char/4 heuristic, not a real tokenizer
    ok = True
    if lines > BODY_LINE_SOFT_LIMIT:
        print(f"[WARN] SKILL.md body is {lines} lines (soft limit {BODY_LINE_SOFT_LIMIT}).")
        ok = False
    if approx_tokens > BODY_TOKEN_SOFT_LIMIT:
        print(
            f"[WARN] SKILL.md body is ~{approx_tokens} tokens by a char/4 "
            f"estimate (soft limit {BODY_TOKEN_SOFT_LIMIT}). This is NOT checked "
            "by quick_validate.py — this script is currently the only place "
            "this gets measured, so don't skip it. Estimate is approximate; "
            "if it's close to the limit, verify with a real tokenizer."
        )
        ok = False
    return ok


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 lint_skill.py <path/to/skill-folder>")
        sys.exit(1)

    skill_path = Path(sys.argv[1])
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        print(f"[ERROR] {skill_md} not found.")
        sys.exit(1)

    text = skill_md.read_text()
    all_clean = True

    all_clean &= check_description_length(skill_md, text)
    all_clean &= check_incident_log_shape(skill_md, 'SKILL.md', text)
    all_clean &= check_body_budget(skill_md, text)

    references_dir = skill_path / 'references'
    if references_dir.is_dir():
        for ref_file in sorted(references_dir.glob('*.md')):
            ref_text = ref_file.read_text()
            all_clean &= check_incident_log_shape(
                ref_file, f'references/{ref_file.name}', ref_text
            )
        all_clean &= check_references_sprawl(references_dir)

    if all_clean:
        print("No advisory findings.")
    else:
        print("\nAll findings above are advisory — review, don't auto-block on them.")


if __name__ == '__main__':
    main()
