#!/usr/bin/env python3
"""zone-lint.py — budget + placement gate for a standing prompt (CLAUDE.md / AGENTS.md).

Usage:
  python3 zone-lint.py <file> [--max-lines N] [--max-tokens N] [--head-lines N]

Checks (each can go red; exit 0 iff all pass):
  Z1  file exists and is non-empty
  Z2  line count <= --max-lines (default 100)
  Z3  approx tokens <= --max-tokens (default 1500); tokens ~= ceil(chars/4), an approximation
  Z4  UPPERCASE hard directives (MUST/ALWAYS/NEVER/CRITICAL/REQUIRED/IMPORTANT/SHALL)
      appear only within the first --head-lines lines (default 40); fenced code blocks skipped

Lowercase directives escape Z4 by design: it is a deterministic proxy, not a semantic judge.
"""
import argparse
import math
import re
import sys
from pathlib import Path

DIRECTIVE = re.compile(r"\b(MUST|ALWAYS|NEVER|CRITICAL|REQUIRED|IMPORTANT|SHALL)\b")


def main() -> int:
    ap = argparse.ArgumentParser(description="Priority-zone budget + placement gate")
    ap.add_argument("file")
    ap.add_argument("--max-lines", type=int, default=100)
    ap.add_argument("--max-tokens", type=int, default=1500)
    ap.add_argument("--head-lines", type=int, default=40)
    args = ap.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"FAIL Z1 {path} is not a file")
        return 1
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        print(f"FAIL Z1 {path} is empty")
        return 1
    print(f"OK   Z1 {path}")

    lines = text.splitlines()
    failures = 0

    n = len(lines)
    ok = n <= args.max_lines
    print(f"{'OK  ' if ok else 'FAIL'} Z2 {n} lines (max {args.max_lines})")
    failures += 0 if ok else 1

    tokens = math.ceil(len(text) / 4)  # chars/4 approximation, stated as such
    ok = tokens <= args.max_tokens
    print(f"{'OK  ' if ok else 'FAIL'} Z3 ~{tokens} tokens, chars/4 approx (max {args.max_tokens})")
    failures += 0 if ok else 1

    in_fence = False
    strays = []
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or i <= args.head_lines:
            continue
        m = DIRECTIVE.search(line)
        if m:
            strays.append((i, m.group(1)))
    if strays:
        for i, word in strays:
            print(f"FAIL Z4 line {i}: '{word}' past head window (first {args.head_lines} lines)")
        failures += 1
    else:
        print(f"OK   Z4 hard directives all within first {args.head_lines} lines")

    print(f"\n{'PASS' if failures == 0 else 'FAIL'} - {failures} check(s) red")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
