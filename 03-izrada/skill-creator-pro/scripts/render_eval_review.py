#!/usr/bin/env python3
# Part of a derivative work of anthropics/skills@b29e7cf6 (skills/skill-creator), by
# buky <webdevcom01@gmail.com>, 2026-07-30. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md.
"""Safely render assets/eval_review.html with real skill data.

Replaces the three placeholders in the template
(__SKILL_NAME_PLACEHOLDER__, __SKILL_DESCRIPTION_PLACEHOLDER__,
__EVAL_DATA_PLACEHOLDER__) the way SKILL.md's "Description Optimization"
step describes, but does the substitution safely instead of leaving it to a
manual, unescaped text replace:

- name/description are inserted into HTML text nodes, so they're run through
  html.escape() first. This matters because a not-yet-validated draft
  description (this page is often shown before the first quick_validate.py
  pass) could contain '<' or '>' and corrupt the page's HTML structure.
- the eval data is inserted as a raw JS object literal inside a <script>
  block. A JSON string is *not* automatically safe there: the HTML parser
  looks for "</script" as plain text, independent of JS string quoting, so
  if any eval query happens to contain that substring (eval queries are
  freeform natural-language text, often copied from real user scenarios —
  entirely plausible), it would prematurely close the <script> tag and let
  the rest of the "JSON" be interpreted as raw HTML/script. This is fixed
  with the standard mitigation: escape every "</" as "<\\/" in the JSON
  text, which is a no-op for JSON semantics (JSON explicitly allows \\/ as
  an escaped '/') but is never parsed as a closing tag by the HTML parser.

Usage:
    python render_eval_review.py --skill-name my-skill \
        --skill-description "..." --eval-data eval_queries.json \
        --output /tmp/eval_review_my-skill.html
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

from scripts.utils import load_json_arg

TEMPLATE_PATH = Path(__file__).parent.parent / "assets" / "eval_review.html"

_PLACEHOLDER_RE = re.compile(
    "__SKILL_NAME_PLACEHOLDER__"
    "|__SKILL_DESCRIPTION_PLACEHOLDER__"
    "|__EVAL_DATA_PLACEHOLDER__"
)


def escape_script_json(data: object) -> str:
    """Serialize data as JSON safe to embed inside a <script> block.

    Escaping "</" as "<\\/" is valid, semantics-preserving JSON (the JSON
    spec allows \\/ as an escaped '/') and prevents the HTML parser from
    ever seeing a literal "</script" (or any other closing tag) inside the
    embedded data, regardless of what text the eval queries contain.
    """
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def render(skill_name: str, skill_description: str, eval_data: list[dict]) -> str:
    template = TEMPLATE_PATH.read_text()

    if not isinstance(eval_data, list):
        raise ValueError("eval_data must be a JSON array of {query, should_trigger} items")

    substitutions = {
        "__SKILL_NAME_PLACEHOLDER__": html.escape(skill_name),
        "__SKILL_DESCRIPTION_PLACEHOLDER__": html.escape(skill_description),
        "__EVAL_DATA_PLACEHOLDER__": escape_script_json(eval_data),
    }
    # One pass, so substituted text is never itself scanned for placeholders.
    # This used to be three sequential .replace() calls, and each later call
    # searched the text the earlier ones had just inserted. html.escape() does
    # not touch '_', so a placeholder token survived escaping intact and three
    # pairs leaked: a description containing __EVAL_DATA_PLACEHOLDER__ became
    # the eval JSON (N-34 as recorded), and a name containing either of the two
    # later tokens became the eval JSON or the description (found by walking the
    # full matrix rather than the one recorded example).
    #
    # The replacement must be a callable: with a string replacement, re.sub
    # gives '\' and '\g' special meaning, so a description containing a
    # backslash would raise or be silently mangled.
    return _PLACEHOLDER_RE.sub(lambda m: substitutions[m.group(0)], template)


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely render eval_review.html for a skill")
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--skill-description", required=True)
    parser.add_argument("--eval-data", required=True, help="Path to a JSON file with the eval query array (or - for stdin)")
    parser.add_argument("--output", required=True, help="Path to write the rendered HTML")
    args = parser.parse_args()

    eval_data = load_json_arg(args.eval_data, what="eval data")

    try:
        html_out = render(args.skill_name, args.skill_description, eval_data)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_out)
    print(f"Rendered eval review to: {output_path}")


if __name__ == "__main__":
    main()
