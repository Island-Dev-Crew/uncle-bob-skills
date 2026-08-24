#!/usr/bin/env python3
"""fence-check.py — the dependency-fence direction gate.

Usage: fence-check.py <fence.json> <edges.json>

fence.json  {"layers": ["outermost", ..., "innermost"],
             "modules": {"path-prefix": "layer", ...}}
edges.json  [{"from": "src/a/x.ts", "to": "src/b/y.ts"}, ...]
            (repo-internal source edges only; filter externals at extraction)

Exit 0 (GREEN) iff every edge points inward or stays inside its own layer.
Exit 1 (RED)  on any outward edge, or any endpoint no prefix maps (fails closed).
Exit 2        on a malformed spec or unreadable input.
"""
import json
import os
import sys


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"SPEC ERROR {path}: {e}")
        sys.exit(2)


def layer_of(path, modules):
    """Longest-prefix match so a nested mapping overrides its parent."""
    best = None
    for prefix, layer in modules.items():
        p = prefix.rstrip("/")
        if path == p or path.startswith(p + "/"):
            if best is None or len(p) > len(best[0]):
                best = (p, layer)
    return best[1] if best else None


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    fence, edges = load(sys.argv[1]), load(sys.argv[2])
    layers = fence.get("layers") or []
    modules = fence.get("modules") or {}
    if not layers or not modules or not isinstance(edges, list):
        print("SPEC ERROR: need non-empty 'layers' + 'modules' and an edge list")
        return 2
    rank = {name: i for i, name in enumerate(layers)}  # higher index = more inward
    for prefix, layer in modules.items():
        if layer not in rank:
            print(f"SPEC ERROR: module '{prefix}' names unknown layer '{layer}'")
            return 2
    red = []
    for e in edges:
        src, dst = str(e.get("from", "")), str(e.get("to", ""))
        ls, ld = layer_of(src, modules), layer_of(dst, modules)
        if ls is None or ld is None:
            gap = src if ls is None else dst
            red.append(f"UNMAPPED {gap}  (declare it in the fence spec; the fence fails closed)")
        elif rank[ld] < rank[ls]:
            red.append(f"OUTWARD  {src} ({ls}) -> {dst} ({ld})")
    if red:
        for line in red:
            print(f"RED {line}")
        print(f"\nRED: {len(red)} violation(s). Exactly three sanctioned repairs (C14):")
        print("  1. invert the dependency   2. insert an interface   3. split the module in half")
        print("Editing the fence spec is a human redesign decision, not a repair.")
        return 1
    print(f"GREEN: {len(edges)} edge(s) obey the declared direction.")
    return 0


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
        _code = 2
    except BaseException as _exc:              # an exception is not a verdict
        try:
            print(f"error: internal failure: {type(_exc).__name__}: {_exc}", file=sys.stderr)
        except BaseException:
            pass
        _code = 2
    for _stream, _fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if _stream is not None:
                _stream.flush()
        except BaseException:
            if _code in (0, 1):                # output that never landed is not a verdict
                _code = 2
            try:                               # so the shutdown flush cannot raise again
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
