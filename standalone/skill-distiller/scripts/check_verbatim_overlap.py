#!/usr/bin/env python3
"""
check_verbatim_overlap.py — detects long verbatim word-sequences shared
between a source document and a distilled skill's output files.

Usage: python3 check_verbatim_overlap.py <source_file> <skill_folder> [--threshold N]

Default threshold: 15 consecutive words (matches this system's own
copyright citation limit elsewhere, kept consistent).
"""
import re
import sys
from pathlib import Path


def tokenize(text):
    # Lowercase word tokens, punctuation stripped, for robust matching.
    return re.findall(r"[a-z0-9']+", text.lower())


def longest_common_run(source_tokens, target_tokens, threshold):
    """Find all runs of >= threshold consecutive tokens shared between
    source and target. Returns list of (length, source_start) tuples."""
    source_set_index = {}
    for i, tok in enumerate(source_tokens):
        source_set_index.setdefault(tok, []).append(i)

    findings = []
    j = 0
    n = len(target_tokens)
    while j < n:
        tok = target_tokens[j]
        candidates = source_set_index.get(tok, [])
        best_len = 0
        best_src = None
        for src_i in candidates:
            length = 0
            while (src_i + length < len(source_tokens)
                   and j + length < n
                   and source_tokens[src_i + length] == target_tokens[j + length]):
                length += 1
            if length > best_len:
                best_len = length
                best_src = src_i
        if best_len >= threshold:
            findings.append((best_len, best_src, j))
            j += best_len
        else:
            j += 1
    return findings


def main():
    if len(sys.argv) < 3:
        print("Usage: check_verbatim_overlap.py <source_file> <skill_folder> [--threshold N]")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    skill_path = Path(sys.argv[2])
    threshold = 15
    if "--threshold" in sys.argv:
        threshold = int(sys.argv[sys.argv.index("--threshold") + 1])

    source_text = source_path.read_text()
    source_tokens = tokenize(source_text)

    target_files = list(skill_path.glob("SKILL.md")) + list(skill_path.glob("references/*.md"))
    any_findings = False

    for tf in target_files:
        target_text = tf.read_text()
        target_tokens = tokenize(target_text)
        findings = longest_common_run(source_tokens, target_tokens, threshold)
        if findings:
            any_findings = True
            for length, src_i, tgt_i in findings:
                snippet = " ".join(target_tokens[tgt_i:tgt_i + min(length, 20)])
                print(f"[FLAG] {tf}: {length}-word verbatim run — \"{snippet}...\"")

    if not any_findings:
        print(f"No verbatim runs >= {threshold} words found.")
    return 1 if any_findings else 0


if __name__ == "__main__":
    sys.exit(main())
