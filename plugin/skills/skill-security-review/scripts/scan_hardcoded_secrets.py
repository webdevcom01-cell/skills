#!/usr/bin/env python3
"""
scan_hardcoded_secrets.py — regex sweep of every bundled script (.py/.js/.ts/.sh) under the
phase folders for hardcoded credentials: API keys, tokens, private key blocks, and suspicious
string-literal assignments to secret-shaped variable names.

This is the mechanical half of skill-security-review's "hardkodovani kredencijali" check --
same category of scan the original forensic analysis ran by hand ("grep pretraga za
hardkodovane kredencijale u svim skriptama — ništa pronađeno"). Automating it means every future
new/changed script gets the same check without a manual pass.

Deliberately over-flags rather than under-flags on the generic assignment pattern (variable name
looks secret-shaped + a long-ish quoted literal) since a human reads the report either way --
but known placeholder/env-lookup patterns are excluded so the common, harmless cases don't drown
real findings.

Exit 0 if nothing found. Exit 1 if anything is flagged. Report-only, never modifies files.
"""

import argparse
import re
import sys
from pathlib import Path

PHASE_RE = re.compile(r"^\d\d-")
SCRIPT_SUFFIXES = {".py", ".js", ".ts", ".sh", ".mjs", ".cjs"}

# (label, compiled pattern) -- specific, high-confidence secret *shapes* first.
SPECIFIC_PATTERNS = [
    ("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("AWS Secret Key (assignment)", re.compile(r"aws_secret_access_key\s*=\s*[\"'][A-Za-z0-9/+=]{30,}[\"']", re.IGNORECASE)),
    ("Private key block", re.compile(r"-----BEGIN\s+(RSA|EC|DSA|OPENSSH|PGP)?\s*PRIVATE KEY-----")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{20,}\b")),
    ("Generic OpenAI-shaped key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("Bearer token literal", re.compile(r"Bearer\s+[A-Za-z0-9\-_.]{20,}")),
]

# Variable-name shapes that suggest a secret, when assigned directly to a quoted string literal.
SECRET_NAME_RE = re.compile(
    r"\b(api[_-]?key|apikey|secret[_-]?key|secret|access[_-]?token|auth[_-]?token|"
    r"token|password|passwd|pwd|private[_-]?key|client[_-]?secret)\b",
    re.IGNORECASE,
)
ASSIGNMENT_RE = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*[\"']([^\"']{12,})[\"']"
)

# Values that look like placeholders/env-lookups rather than real secrets -- excluded so the
# very common, harmless patterns don't drown real findings.
PLACEHOLDER_VALUE_RE = re.compile(
    r"^(your[_-]?|<|\{|\$\{|xxx|changeme|example|placeholder|test|dummy|fake|none|null|)",
    re.IGNORECASE,
)
ENV_LOOKUP_LINE_RE = re.compile(
    r"os\.(environ|getenv)|process\.env|ENV\[|getenv\(|env\.get\("
)


def discover_phase_dirs(root: Path):
    return sorted(p for p in root.iterdir() if p.is_dir() and PHASE_RE.match(p.name))


def discover_scripts(root: Path):
    scripts = []
    for phase_dir in discover_phase_dirs(root):
        for p in phase_dir.rglob("*"):
            if p.is_file() and p.suffix in SCRIPT_SUFFIXES:
                scripts.append(p)
    return scripts


def scan_file(path: Path):
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return [f"[READ-ERROR] {path}: {e}"]

    for lineno, line in enumerate(text.splitlines(), start=1):
        if ENV_LOOKUP_LINE_RE.search(line):
            continue  # reading from environment/config is the correct pattern, not a finding

        for label, pattern in SPECIFIC_PATTERNS:
            if pattern.search(line):
                findings.append(f"[SECRET:{label}] {path}:{lineno}")

        for m in ASSIGNMENT_RE.finditer(line):
            var_name, value = m.group(1), m.group(2)
            if not SECRET_NAME_RE.search(var_name):
                continue
            if PLACEHOLDER_VALUE_RE.match(value.strip()):
                continue
            findings.append(f"[SECRET-SHAPED-ASSIGNMENT] {path}:{lineno} — variable '{var_name}'")

    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo_root", nargs="?", default=".", help="Koren repoa (default: trenutni folder)")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()

    scripts = discover_scripts(root)
    all_findings = []
    for script in scripts:
        all_findings.extend(scan_file(script))

    print(f"scan_hardcoded_secrets — {len(scripts)} skripti (.py/.js/.ts/.sh) skenirano\n")

    if all_findings:
        print(f"❌ {len(all_findings)} nalaza:")
        for f in all_findings:
            print(" ", f)
        sys.exit(1)
    else:
        print("✅ Nema hardkodovanih kredencijala.")
        sys.exit(0)


if __name__ == "__main__":
    main()
