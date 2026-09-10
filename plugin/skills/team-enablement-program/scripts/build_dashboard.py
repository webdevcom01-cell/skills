#!/usr/bin/env python3
"""Render a self-contained HTML progress tracker from an enablement program markdown file.

Parses week sections out of the program document and renders 14 cards grouped by phase.
Single file, inline CSS, no external requests - so it survives being emailed or dropped
on a shared drive.

Usage:
  python3 build_dashboard.py --program acme-enablement-program.md \
      --client "Acme" --output acme-program-dashboard.html

If parsing finds nothing usable, the script says so rather than emitting an empty page.
"""

import argparse
import html
import re
import sys

WEEK_HEADING = re.compile(
    # The number must not be followed by a letter: "Week 1b" is a sub-session, not a
    # second Week 1, and reading it as one silently dropped its content.
    r"^\s{0,3}#{2,4}\s*(?:Week|Nedelja|Nedjelja)\s*(\d{1,2})(?![0-9A-Za-z])\s*[-–—:.]?\s*(.*?)\s*$",
    re.IGNORECASE,
)
# Matches "**Objective.** text", "- **Objective:** text", "* Cilj. text" and friends.
# The leading list-marker branch matters: writing the program as a bullet list is a
# completely natural choice, and without it every card silently rendered empty.
FIELD = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.)]\s+)?(?:\*\*|__)?\s*(Objective|Exercise|Deliverable|Completion check|Check|"
    r"Cilj|Vje[zž]ba|Ve[zž]ba|Isporuka|Provjera|Provera)\s*[:.]?\s*(?:\*\*|__)?\s*[:.]?\s*(.*)$",
    re.IGNORECASE,
)

# Sections outside any week that must survive into the dashboard. The dashboard is the
# artefact most likely to be printed and circulated, and an earlier version rendered only
# the four parsed fields - which silently dropped every prohibition and every condition of
# engagement from the copy the team actually reads.
KEY_SECTION = re.compile(
    r"^\s{0,3}#{1,3}\s*.*?(condition|rule|scope|limit|not include|non-negotiable|"
    r"uslov|pravil|opseg|ograni[čc]|ne uklju[čc])", re.IGNORECASE)
ANY_HEADING = re.compile(r"^\s{0,3}#{1,4}\s*(.+?)\s*$")
# "Week 1b" and friends: deliberate sub-sessions the week parser cannot number.
SUBWEEK = re.compile(r"^\s{0,3}#{1,4}\s*(?:Week|Nedelja|Nedjelja)\s*\d{1,2}[A-Za-z]", re.I)

FIELD_ALIASES = {
    "objective": "objective", "cilj": "objective",
    "exercise": "exercise", "vjezba": "exercise", "vežba": "exercise",
    "vezba": "exercise", "vježba": "exercise",
    "deliverable": "deliverable", "isporuka": "deliverable",
    "completion check": "check", "check": "check",
    "provjera": "check", "provera": "check",
}

PHASES = [
    (range(0, 1), "Week 0", "Baseline", "#8B5E3C"),
    (range(1, 5), "Month 1", "Use it", "#1F6F8B"),
    (range(5, 9), "Month 2", "Make it yours", "#2E6B4F"),
    (range(9, 13), "Month 3", "Build with it", "#6A4C93"),
    (range(13, 14), "Week 13", "Handoff", "#A8443B"),
]
# Weeks past 13 are a deliberate extension, not an error - but they must be
# labelled, because a card with a blank phase reads as a rendering fault.
EXTRA_PHASE = ("Extension", "Added week", "#5A6773")


def normalise(label):
    return FIELD_ALIASES.get(label.strip().lower().rstrip(".:"), None)


def parse_program(text):
    """Extract ({week_number: {...}}, [duplicate_week_numbers], [key_sections])."""
    weeks = {}
    duplicates = []
    key_sections = []
    skipped_headings = []
    current = None
    pending_field = None
    capturing_key = None

    for raw in text.splitlines():
        line = raw.rstrip()

        m = WEEK_HEADING.match(line)
        if not m:
            head = ANY_HEADING.match(line)
            if head:
                if capturing_key and capturing_key["body"]:
                    key_sections.append(capturing_key)
                capturing_key = None
                if KEY_SECTION.match(line):
                    capturing_key = {"title": clean(head.group(1)), "body": []}
                    current = None
                    pending_field = None
                    continue
                # Any other heading ends the current week. Without this, a heading the
                # week parser does not recognise — "### Week 1b" — left the previous
                # week open, and its fields were silently overwritten by the next ones.
                if current is not None:
                    sub = SUBWEEK.match(line)
                    if sub:
                        skipped_headings.append(clean(head.group(1)))
                    current = None
                    pending_field = None
            elif capturing_key is not None and line.strip():
                capturing_key["body"].append(clean(line))
                continue
            elif capturing_key is not None:
                continue

        if m:
            if capturing_key and capturing_key["body"]:
                key_sections.append(capturing_key)
            capturing_key = None
            num = int(m.group(1))
            title = m.group(2).strip().lstrip("-–—:").strip()
            title = re.sub(r"\*\*|__|`", "", title)
            if num in weeks:
                # Keeping the first occurrence and reporting it. The previous
                # behaviour overwrote silently, so a copy-paste slip deleted a
                # week's content from the deliverable with no trace.
                duplicates.append(num)
                current = None
                pending_field = None
                continue
            current = num
            pending_field = None
            weeks[num] = {"title": title, "objective": "", "exercise": "",
                          "deliverable": "", "check": "", "notes": ""}
            continue

        if current is None:
            continue

        fm = FIELD.match(line)
        if fm:
            key = normalise(fm.group(1))
            if key:
                pending_field = key
                weeks[current][key] = clean(fm.group(2))
                continue

        # Continuation of the previous field: an indented or plain line, not a new heading.
        if pending_field and line.strip() and not line.strip().startswith(("#", "|", "---")):
            existing = weeks[current][pending_field]
            bullet = bool(re.match(r"^\s*[-*+]\s+", line))
            addition = clean(line)
            if addition:
                joiner = " • " if (bullet and existing) else " "
                weeks[current][pending_field] = (existing + joiner + addition).strip()
        elif not line.strip():
            pending_field = None
        elif line.strip() and not line.strip().startswith(("#", "|", "---")):
            # Prose inside a week that is not one of the four fields. Previously discarded,
            # which is how the restrictions ("WhatsApp is deliberately not connected",
            # "sits behind a login") vanished from the copy people actually read.
            addition = clean(line)
            if addition:
                weeks[current]["notes"] = (weeks[current]["notes"] + " " + addition).strip()

    if capturing_key and capturing_key["body"]:
        key_sections.append(capturing_key)

    return weeks, duplicates, key_sections, skipped_headings


def clean(s):
    s = re.sub(r"\*\*|__|`", "", s)
    s = re.sub(r"^\s*[-*]\s+", "", s)
    return s.strip()


def phase_for(week):
    for rng, label, name, colour in PHASES:
        if week in rng:
            return label, name, colour
    return EXTRA_PHASE


def render(client, weeks, key_sections=()):
    cards = []
    for num in sorted(weeks):
        w = weeks[num]
        label, phase_name, colour = phase_for(num)
        fields = []
        for key, heading in (("objective", "Objective"), ("exercise", "Exercise"),
                             ("deliverable", "Deliverable"), ("check", "Completion check")):
            if w.get(key):
                fields.append(
                    f'<div class="f"><span class="fl">{heading}</span>'
                    f'<span class="ft">{html.escape(w[key])}</span></div>'
                )
        if w.get("notes"):
            fields.append(
                f'<div class="f note"><span class="fl">Also this week</span>'
                f'<span class="ft">{html.escape(w["notes"])}</span></div>'
            )
        body = "".join(fields) or '<div class="f empty">No detail parsed for this week.</div>'
        cards.append(f"""
      <article class="card" data-week="{num}" style="--accent:{colour}">
        <header>
          <div class="wk">Week {num}</div>
          <h3>{html.escape(w['title']) or 'Untitled'}</h3>
          <div class="phase">{html.escape(phase_name)}</div>
        </header>
        <div class="fields">{body}</div>
        <footer>
          <button class="status" type="button" data-state="0">Not started</button>
        </footer>
      </article>""")

    legend = "".join(
        f'<span class="chip" style="--accent:{c}">{html.escape(n)}</span>'
        for _, _, n, c in [(r, l, n, c) for r, l, n, c in PHASES]
    )

    keys = ""
    if key_sections:
        blocks = "".join(
            f'<details class="keysec"><summary>{html.escape(s["title"])}</summary>'
            f'<p>{html.escape(" ".join(s["body"]))}</p></details>'
            for s in key_sections
        )
        keys = f'<section class="keys"><h2>Rules, scope and limits</h2>{blocks}</section>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(client)} — AI Enablement Program</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2rem 1.25rem 4rem;
    font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
    background: #F7F8FA; color: #16202B;
  }}
  .wrap {{ max-width: 1180px; margin: 0 auto; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 .25rem; letter-spacing: -.01em; }}
  .sub {{ color: #5A6773; margin: 0 0 1.25rem; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1.75rem; }}
  .chip {{
    font-size: .78rem; font-weight: 600; padding: .28rem .7rem; border-radius: 999px;
    color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent);
    border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  }}
  .grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr)); }}
  .card {{
    background: #fff; border: 1px solid #E3E8EE; border-radius: 12px; padding: 1rem 1.05rem 0.85rem;
    border-top: 3px solid var(--accent); display: flex; flex-direction: column;
    box-shadow: 0 1px 2px rgba(16,32,48,.04);
  }}
  .card header {{ margin-bottom: .7rem; }}
  .wk {{ font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }}
  .card h3 {{ font-size: 1.02rem; margin: .15rem 0 .2rem; line-height: 1.3; }}
  .phase {{ font-size: .76rem; color: #7C8894; }}
  .fields {{ flex: 1; }}
  .f {{ margin-bottom: .6rem; }}
  .fl {{ display: block; font-size: .68rem; font-weight: 700; letter-spacing: .06em;
         text-transform: uppercase; color: #94A0AC; margin-bottom: .12rem; }}
  .ft {{ display: block; font-size: .875rem; color: #2C3A47; }}
  .f.empty .f, .f.empty {{ color: #A6B0BA; font-style: italic; font-size: .85rem; }}
  .f.note {{ background: #FFF8E8; border-left: 3px solid #E0B341; padding: .45rem .6rem;
             border-radius: 0 5px 5px 0; }}
  .f.note .fl {{ color: #96700F; }}
  .keys {{ margin-bottom: 1.75rem; background: #fff; border: 1px solid #E3E8EE;
           border-radius: 12px; padding: 1rem 1.15rem; }}
  .keys h2 {{ font-size: .95rem; margin: 0 0 .6rem; letter-spacing: -.01em; }}
  .keysec {{ border-top: 1px solid #EEF1F5; padding: .45rem 0; }}
  .keysec:first-of-type {{ border-top: 0; }}
  .keysec summary {{ cursor: pointer; font-weight: 600; font-size: .87rem; }}
  .keysec p {{ margin: .45rem 0 .2rem; font-size: .85rem; color: #2C3A47; }}
  footer {{ border-top: 1px solid #EEF1F5; padding-top: .6rem; margin-top: .4rem; }}
  .status {{
    font: inherit; font-size: .8rem; font-weight: 600; cursor: pointer;
    border-radius: 6px; padding: .32rem .75rem; border: 1px solid #D5DCE4;
    background: #F4F6F9; color: #5A6773; transition: .12s;
  }}
  .status[data-state="1"] {{ background: #FFF6E3; border-color: #E8CE93; color: #8A6416; }}
  .status[data-state="2"] {{ background: #E9F6EE; border-color: #A5D6BA; color: #1E6B41; }}
  .status:hover {{ filter: brightness(.97); }}
  .foot {{ margin-top: 2.5rem; font-size: .8rem; color: #8A95A1; max-width: 60ch; }}
  @media print {{
    body {{ background: #fff; }} .status {{ display: none; }}
    .card {{ break-inside: avoid; box-shadow: none; }}
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #12171D; color: #E4E9EF; }}
    .card {{ background: #1A2129; border-color: #2A3440; }}
    .ft {{ color: #C3CCD6; }} .sub, .phase {{ color: #8B97A4; }}
    .status {{ background: #232C36; border-color: #33404D; color: #A3AEBA; }}
    .keys {{ background: #1A2129; border-color: #2A3440; }}
    .keysec {{ border-top-color: #2A3440; }} .keysec p {{ color: #C3CCD6; }}
    .f.note {{ background: #2A2418; border-left-color: #8A6A1E; }}
    footer {{ border-top-color: #2A3440; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>{html.escape(client)} — AI Enablement Program</h1>
  <p class="sub">14 weeks. Week 0 measures, Weeks 1–12 train, Week 13 hands over ownership.</p>
  <div class="legend">{legend}</div>
  {keys}
  <div class="grid">{''.join(cards)}
  </div>
  <p class="foot">
    Status buttons are for viewing in this session only — this file holds no saved state,
    so the programme's real record of truth stays the baseline workbook and the Week 13
    ownership register.
  </p>
</div>
<script>
  var LABELS = ["Not started", "In progress", "Done"];
  document.querySelectorAll(".status").forEach(function (b) {{
    b.addEventListener("click", function () {{
      var s = (parseInt(b.dataset.state, 10) + 1) % 3;
      b.dataset.state = s;
      b.textContent = LABELS[s];
    }});
  }});
</script>
</body>
</html>
"""


def main():
    p = argparse.ArgumentParser(description="Render the HTML program tracker.")
    p.add_argument("--program", required=True, help="Path to the enablement program markdown")
    p.add_argument("--client", required=True, help="Client name for the header")
    p.add_argument("--output", required=True, help="Output .html path")
    args = p.parse_args()

    try:
        with open(args.program, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        sys.exit(f"Could not read {args.program}: {exc}")

    weeks, duplicates, key_sections, skipped = parse_program(text)
    if not weeks:
        sys.exit(
            "No week sections found. The parser looks for headings like '### Week 5 — Writing your "
            "first skill' (2 to 4 '#' marks, the word Week or Nedelja, then the number). Check the "
            "program markdown uses that heading form, then re-run."
        )

    # A card with no parsed fields renders as "No detail parsed" - shipping a page of
    # those looks like the consultant sent a broken file. Refuse rather than warn when
    # every card is empty; warn loudly when only some are.
    empty = [n for n, w in weeks.items()
             if not any(w[k] for k in ("objective", "exercise", "deliverable", "check", "notes"))]
    if len(empty) == len(weeks):
        sys.exit(
            f"Parsed {len(weeks)} week heading(s) but no field content, so every card would be "
            "blank. Fields must start a line, optionally as a list item, e.g.\n"
            "    **Objective.** Move from one-line asks to structured prompts.\n"
            "    - **Exercise:** Each participant rewrites one real task.\n"
            "Recognised labels: Objective, Exercise, Deliverable, Completion check "
            "(or Cilj, Vežba, Isporuka, Provera). Fix the program markdown, then re-run."
        )

    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(render(args.client, weeks, key_sections))

    missing = [n for n in range(14) if n not in weeks]
    print(f"Wrote {args.output}  ({len(weeks)} weeks rendered)")
    if empty:
        print(f"  WARNING: {len(empty)} card(s) have no field content and will read "
              f"'No detail parsed': week(s) {', '.join(map(str, sorted(empty)))}. "
              "Do not send the dashboard until these are fixed.")
    # A week carrying only loose prose renders, but it renders as a wall of text with no
    # objective, deliverable or completion check — usable to read, useless to run.
    unstructured = sorted(n for n, w in weeks.items()
                          if w.get("notes")
                          and not any(w[k] for k in ("objective", "exercise", "deliverable", "check")))
    if unstructured:
        print(f"  WARNING: week(s) {', '.join(map(str, unstructured))} have prose but no "
              "Objective / Exercise / Deliverable / Completion check labels. The cards render, "
              "but nobody can run the week from them. Add the field labels shown in the skill.")
    if skipped:
        print(f"  WARNING: heading(s) {', '.join(repr(h) for h in skipped)} use a week number "
              "with a letter. They are not rendered as cards - fold the content into the "
              "numbered week, or give it its own number.")
    if duplicates:
        print(f"  WARNING: week(s) {', '.join(map(str, sorted(set(duplicates))))} appear more than "
              "once. The first occurrence was kept and the later one ignored - check the program "
              "markdown for a duplicated or misnumbered section.")
    if missing:
        print(f"  NOTE: no section found for week(s): {', '.join(map(str, missing))}. "
              "If that is deliberate, ignore; otherwise check the headings.")


if __name__ == "__main__":
    main()
