#!/usr/bin/env python3
"""Deterministic SR orthographic variants: diacritic -> ASCII, and Latin <-> Cyrillic.

Single source of truth for the s/z/c/c/dj folding used by G15 in validate_library.py
(the fold is not invertible: c and c both collapse to c) and by the generation step
that fills queries[].variants for sr rows.
"""

import sys
import json
import argparse

_ASCII_MAP = str.maketrans({
    "š": "s", "Š": "S",
    "ž": "z", "Ž": "Z",
    "č": "c", "Č": "C",
    "ć": "c", "Ć": "C",
    "đ": "dj", "Đ": "Dj",
})

# Latin -> Cyrillic needs digraph handling before single-char mapping, so it is
# done as ordered find/replace passes. Two unrelated reasons a Latin digraph
# maps to one Cyrillic letter:
# - native Serbian digraphs (lj, nj, dž) that are one sound in the alphabet.
# - unadapted foreign digraphs (ch, sh, th, ph) that Serbian speakers already
#   pronounce/transliterate as a single sound (c/s/t/f), even though the
#   Latin spelling keeps the English digraph in nautical/tech jargon -- e.g.
#   "charter" transliterates as one c-sound + "arter", not as separate c and
#   h letters. Without this pass the single-char loop below maps c -> c and
#   h -> x independently, producing the wrong two-letter cluster.
_DIGRAPHS = [
    ("Lj", "Љ"), ("LJ", "Љ"), ("lj", "љ"),
    ("Nj", "Њ"), ("NJ", "Њ"), ("nj", "њ"),
    ("Dž", "Џ"), ("DŽ", "Џ"), ("dž", "џ"),
    ("Ch", "Ч"), ("CH", "Ч"), ("ch", "ч"),
    ("Sh", "Ш"), ("SH", "Ш"), ("sh", "ш"),
    ("Th", "Т"), ("TH", "Т"), ("th", "т"),
    ("Ph", "Ф"), ("PH", "Ф"), ("ph", "ф"),
]

_LATIN_TO_CYRILLIC_SINGLE = {
    "a": "а", "b": "б", "v": "в", "g": "г", "d": "д", "đ": "ђ", "e": "е",
    "ž": "ж", "z": "з", "i": "и", "j": "ј", "k": "к", "l": "л", "m": "м",
    "n": "н", "o": "о", "p": "п", "r": "р", "s": "с", "t": "т", "ć": "ћ",
    "u": "у", "f": "ф", "h": "х", "c": "ц", "č": "ч", "š": "ш",
}


def to_ascii(text):
    """Deterministic diacritic fold used for query.variants.ascii (G15)."""
    return text.translate(_ASCII_MAP)


def to_cyrillic(text):
    """Best-effort Latin -> Cyrillic transliteration for query.variants.cyrillic."""
    result = text
    for latin, cyr in _DIGRAPHS:
        result = result.replace(latin, cyr)
    out_chars = []
    for ch in result:
        lower = ch.lower()
        if lower in _LATIN_TO_CYRILLIC_SINGLE:
            cyr = _LATIN_TO_CYRILLIC_SINGLE[lower]
            out_chars.append(cyr.upper() if ch.isupper() else cyr)
        else:
            out_chars.append(ch)
    return "".join(out_chars)


def variants_for(text, script="latin"):
    """queries[].variants payload for one sr-family query row."""
    if script != "latin":
        return {}
    return {"ascii": to_ascii(text), "cyrillic": to_cyrillic(text)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?", help="Text to convert. Reads stdin if omitted.")
    parser.add_argument("--json", action="store_true", help="Print {ascii, cyrillic} as JSON.")
    args = parser.parse_args()

    text = args.text if args.text is not None else sys.stdin.read().strip()
    payload = variants_for(text)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print("ascii:   ", payload["ascii"])
        print("cyrillic:", payload["cyrillic"])


if __name__ == "__main__":
    main()
