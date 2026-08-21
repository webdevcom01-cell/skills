# Modified from anthropics/skills@b29e7cf6 (skills/skill-creator) by
# buky <webdevcom01@gmail.com>, 2026-07-30. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md.
"""Shared utilities for skill-creator scripts."""

import json
import re
import sys
from pathlib import Path


def load_json_arg(source, *, what: str):
    """Read JSON from a path (or "-" for stdin), failing with a readable message.

    Every script here takes a JSON file path on the command line, and five of them
    called json.loads on it bare: a malformed file or a typo'd path produced a raw
    traceback instead of a sentence, on the very first thing the script does. The
    other two — aggregate_benchmark.py and generate_review.py — already wrapped
    theirs, so the codebase disagreed with itself about its own convention (N-45).

    Deliberately still exits 1 rather than inventing a new exit code: distinct
    codes per failure type is a separate contract change across all nine scripts
    (N-17), and doing it in five of them would trade one inconsistency for another.
    """
    try:
        raw = sys.stdin.read() if source == "-" else Path(source).read_text()
    except OSError as e:
        origin = "stdin" if source == "-" else f"'{source}'"
        print(f"Error: cannot read {what} from {origin}: {e.strerror}", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        origin = "stdin" if source == "-" else f"'{source}'"
        print(f"Error: {what} from {origin} is not valid JSON "
              f"(line {e.lineno}, column {e.colno}): {e.msg}", file=sys.stderr)
        sys.exit(1)


# agentskills.io/specification, `name`: lowercase letters, digits and hyphens,
# max 64 characters, and it must match the parent directory name.
SKILL_NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")


def validate_skill_name(name: str) -> str:
    """Return `name` if it is a spec-legal skill name, else raise ValueError.

    `name` comes straight out of another skill's SKILL.md frontmatter, and
    parse_skill_md does not validate it. Callers that build a filesystem path
    from it were therefore building that path from unvalidated input: a name
    of "../../pwned" wrote the temp command file two levels above
    .claude/commands/, and an absolute name ("/tmp/x") escaped the base
    entirely, because an absolute right-hand side discards the left in
    pathlib. The same unvalidated value also reaches Path.glob during the
    stale-file sweep, where an absolute pattern raises NotImplementedError.
    One rule, checked before either path is touched (N-33).
    """
    if not isinstance(name, str) or not SKILL_NAME_RE.match(name):
        raise ValueError(
            f"Invalid skill name {name!r}. A skill name must be 1-64 characters "
            f"of lowercase letters, digits and hyphens (see the `name` field in "
            f"the skill's SKILL.md frontmatter)."
        )
    return name


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text()
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            # Handle YAML multiline indicators (>, |, >-, |-)
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (frontmatter_lines[i].startswith("  ") or frontmatter_lines[i].startswith("\t")):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content
