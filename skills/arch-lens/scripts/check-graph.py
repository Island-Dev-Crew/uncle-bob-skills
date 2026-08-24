#!/usr/bin/env python3
"""check-graph.py — enforced gate for an arch-lens graph.json extract.

Usage: python3 check-graph.py <graph.json> [repo-root]
Exit 0 iff every check passes; each check prints OK/FAIL and can go red.
  G1 parses as JSON; 'modules' a non-empty list of objects, 'edges' a list of objects
  G2 module ids are non-empty unique strings
  G3 every 'parent' is null or a declared id, and parent chains terminate (no cycle)
  G4 every edge 'from'/'to' is a declared id; no self-edges
  G5 every module carries a non-empty string 'path'
  G6 with repo-root given, every 'path' resolves to a real file/dir strictly
     inside root - never the root itself, never escaping it (else SKIP)
"""
import json
import os
import sys
from pathlib import Path


def check(cid: str, ok: bool, detail: str) -> bool:
    print(("OK  " if ok else "FAIL") + f" {cid} {detail}")
    return ok


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        check("G1", False, f"unreadable graph: {e}")
        return 1
    modules, edges = data.get("modules"), data.get("edges")
    g1 = (
        isinstance(modules, list) and bool(modules)
        and all(isinstance(m, dict) for m in modules)
        and isinstance(edges, list)
        and all(isinstance(e, dict) for e in edges)
    )
    if not check("G1", g1, "modules non-empty list of objects, edges list of objects"):
        return 1
    ok = True
    ids = [m.get("id") for m in modules]
    idset = set(ids)
    ok &= check(
        "G2",
        all(isinstance(i, str) and i for i in ids) and len(ids) == len(idset),
        f"{len(ids)} module ids unique, non-empty strings",
    )
    parent = {m.get("id"): m.get("parent") for m in modules}
    g3, bad = True, ""
    for mid in idset:
        seen, cur = set(), parent.get(mid)
        while g3 and cur is not None:
            if cur not in idset:
                g3, bad = False, f"module '{mid}' has undeclared parent '{cur}'"
            elif cur in seen:
                g3, bad = False, f"parent cycle at '{cur}'"
            else:
                seen.add(cur)
                cur = parent.get(cur)
        if not g3:
            break
    ok &= check("G3", g3, bad or "parents resolve, chains terminate")
    g4, bad = True, ""
    for e in edges:
        f, t = e.get("from"), e.get("to")
        if f not in idset or t not in idset or f == t:
            g4, bad = False, f"bad edge {f!r} -> {t!r}"
            break
    ok &= check("G4", g4, bad or f"{len(edges)} edges resolve, no self-edges")
    pathless = [str(m.get("id")) for m in modules if not (isinstance(m.get("path"), str) and m.get("path"))]
    ok &= check(
        "G5",
        not pathless,
        ("missing/empty path for: " + ", ".join(pathless[:5])) if pathless else "every module carries a non-empty string path",
    )
    if len(sys.argv) > 2:
        root = Path(sys.argv[2]).resolve()
        bad = []
        for m in modules:
            target = (root / str(m.get("path", ""))).resolve()
            if not (target.exists() and target != root and target.is_relative_to(root)):
                bad.append(str(m.get("id")))
        detail = ("bad paths for: " + ", ".join(bad[:5])) if bad else "all module paths land on real code inside root"
        ok &= check("G6", not bad, detail)
    else:
        print("SKIP G6 no repo-root given; path resolution unchecked")
    return 0 if ok else 1


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
