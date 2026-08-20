#!/usr/bin/env python3
"""margin-ledger.py — deterministic margin arithmetic for the gate stack (C5).

Reads TSV rows (stdin or a file arg): story <TAB> gated_minutes <TAB> human_minutes
Prints per-story margin (human / gated) with a band verdict, then the aggregate.
Bands: LOST < floor <= THIN < 2 <= IN-BAND <= 4 < WIDE.

Exit codes: 0 every story and the aggregate at or above the floor;
1 any margin below the floor (the game is lost, C5);
2 fail-closed on empty or malformed input (an empty ledger proves nothing).
"""
import argparse
import sys


def band(margin: float, floor: float) -> str:
    if margin < floor:
        return "LOST"
    if margin < 2.0:
        return "THIN"
    if margin <= 4.0:
        return "IN-BAND"
    return "WIDE"


def die(msg: str, code: int = 2) -> None:
    """Exit 2 = fail-closed on ledger CONTENT (empty/malformed rows).

    Exit 3 = the ledger could not be read at all, or the invocation was wrong.
    The two must not share a code: run from the wrong directory, a path error
    exiting 2 is indistinguishable from a legitimate fail-closed verdict, so a
    broken command reads as a real result.
    """
    print(f"margin-ledger: {msg}", file=sys.stderr)
    sys.exit(code)


def parse_rows(lines):
    rows = []
    for n, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            die(f"line {n}: expected 3 tab-separated fields, got {len(parts)}")
        story, gated_s, human_s = (p.strip() for p in parts)
        try:
            gated, human = float(gated_s), float(human_s)
        except ValueError:
            die(f"line {n}: minutes must be numeric ('{gated_s}', '{human_s}')")
        if not story:
            die(f"line {n}: empty story name")
        if gated <= 0 or human <= 0:
            die(f"line {n}: minutes must be positive (gated={gated}, human={human})")
        rows.append((story, gated, human))
    if not rows:
        die("no data rows — an empty ledger cannot pass")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ledger", nargs="?", help="TSV file (default: stdin)")
    ap.add_argument("--floor", type=float, default=1.0,
                    help="margin below this loses the game (default 1.0)")
    args = ap.parse_args()
    if args.floor <= 0:
        die(f"--floor must be positive, got {args.floor}", code=3)

    if args.ledger:
        try:
            with open(args.ledger, encoding="utf-8") as fh:
                rows = parse_rows(fh)
        except OSError as e:
            die(str(e), code=3)
    else:
        rows = parse_rows(sys.stdin)

    breach = False
    for story, gated, human in rows:
        m = human / gated
        b = band(m, args.floor)
        breach = breach or m < args.floor
        print(f"{b:<8} {m:6.2f}x  gated={gated:g}m  human={human:g}m  {story}")

    agg = sum(h for _, _, h in rows) / sum(g for _, g, _ in rows)
    agg_band = band(agg, args.floor)
    breach = breach or agg < args.floor
    print(f"aggregate {agg:.2f}x {agg_band} over {len(rows)} stories, floor {args.floor:g}")
    return 1 if breach else 0


if __name__ == "__main__":
    sys.exit(main())
