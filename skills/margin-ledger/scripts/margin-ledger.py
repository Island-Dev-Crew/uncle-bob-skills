#!/usr/bin/env python3
"""margin-ledger.py — deterministic margin arithmetic for the gate stack (C5).

Reads TSV rows (stdin or a file arg): story <TAB> gated_minutes <TAB> human_minutes
Prints per-story margin (human / gated) with a band verdict, then the aggregate.
Bands: LOST < floor <= THIN < 2 <= IN-BAND <= 4 < WIDE.

Exit codes, and these four are the whole set: 0 every story and the aggregate at or
above the floor; 1 any margin below the floor (the game is lost, C5); 2 fail-closed on
empty or malformed ledger CONTENT (an empty ledger proves nothing); 3 the ledger could
not be read or decoded at all, or the invocation was wrong. 2 and 3 must not share a
code — run from the wrong directory, a path error exiting 2 is indistinguishable from a
real fail-closed verdict. Nothing here exits 1 except a margin below the floor: an
unhandled exception used to, and a crash reading as LOST is a verdict this tool never
reached.
"""
import argparse
import io
import math
import os
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
        if not line.strip():
            continue
        parts = line.split("\t")
        # A comment is a line that CANNOT be a row. Testing for a leading `#` before the
        # split swallowed `#123<TAB>10<TAB>1` — an issue-number story id, which is how
        # software writes them — so its 0.10x breach vanished, the aggregate printed
        # IN-BAND and the gate exited 0. A row that parses is data, whatever it starts with.
        if len(parts) != 3 and line.lstrip().startswith("#"):
            continue
        if len(parts) != 3:
            die(f"line {n}: expected 3 tab-separated fields, got {len(parts)}")
        story, gated_s, human_s = (p.strip() for p in parts)
        try:
            gated, human = float(gated_s), float(human_s)
        except ValueError:
            die(f"line {n}: minutes must be numeric ('{gated_s}', '{human_s}')")
        # float() accepts nan/inf, and any literal past ~1e308 silently becomes inf —
        # which a spreadsheet or timing script writing a divide-by-zero cell produces on
        # its own. Every comparison below is False against NaN, so such a row sailed
        # through the positivity check and printed WIDE at exit 0: a false green.
        if not (math.isfinite(gated) and math.isfinite(human)):
            die(f"line {n}: minutes must be finite ('{gated_s}', '{human_s}')")
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
    # A NaN floor is the worst of these: every `m < floor` is False, so it disables the
    # breach test wholesale and a real 0.80x story exits 0. Reject at the invocation code.
    if not math.isfinite(args.floor) or args.floor <= 0:
        die(f"--floor must be positive and finite, got {args.floor}", code=3)

    # Both inputs decode strictly, and a decode failure is exit 3 — the ledger could not
    # be read at all. Two bugs met here: the file path let UnicodeDecodeError escape
    # uncaught, and an uncaught exception exits 1, which is this gate's LOST verdict; while
    # stdin took its error handler from the locale (`surrogateescape` on a UTF-8 locale),
    # so undecodable bytes became surrogates and were SCORED. Same bytes, two different
    # wrong answers, neither of them a refusal.
    try:
        if args.ledger:
            with open(args.ledger, encoding="utf-8") as fh:
                rows = parse_rows(fh)
        else:
            with io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="strict") as fh:
                rows = parse_rows(fh)
    except OSError as e:
        die(str(e), code=3)
    except UnicodeDecodeError as e:
        die(f"{args.ledger or '<stdin>'}: not valid UTF-8 ({e})", code=3)

    breach = False
    for story, gated, human in rows:
        m = human / gated
        if not math.isfinite(m):
            die(f"line for '{story}': margin overflows (gated={gated:g}, human={human:g})")
        b = band(m, args.floor)
        breach = breach or m < args.floor
        print(f"{b:<8} {m:6.2f}x  gated={gated:g}m  human={human:g}m  {story}")

    agg = sum(h for _, _, h in rows) / sum(g for _, g, _ in rows)
    if not math.isfinite(agg):
        die("aggregate margin overflows — the ledger's minutes are out of range")
    agg_band = band(agg, args.floor)
    breach = breach or agg < args.floor
    print(f"aggregate {agg:.2f}x {agg_band} over {len(rows)} stories, floor {args.floor:g}")
    return 1 if breach else 0


if __name__ == "__main__":
    # The exit-code contract has to survive the interpreter's own shutdown. CPython flushes
    # the std streams after main() returns, and if that flush raises — a pipe whose reader
    # has already gone, which is the ordinary `gate.py … | head` idiom — it REPLACES the
    # status this script chose with 120, a code no table here names. An unhandled exception
    # is the other leak, and the worse one: it exits 1, and 1 is a VERDICT here, so a crash
    # would be read as a real finding about the code under test.
    try:
        _code = main()
    except SystemExit as _exc:                 # argparse raises this from inside
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
    except KeyboardInterrupt:
        _code = 3
    except BaseException as _exc:              # an exception is not a verdict
        try:
            print(f"error: internal failure: {type(_exc).__name__}: {_exc}", file=sys.stderr)
        except BaseException:
            pass
        _code = 3
    for _stream, _fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if _stream is not None:
                _stream.flush()
        except BaseException:
            if _code in (0, 1):                # output that never landed is not a verdict
                _code = 3
            try:                               # so the shutdown flush cannot raise again
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
