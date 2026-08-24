#!/usr/bin/env python3
"""error-paths.py — count the error paths an interface exposes, before vs after.

Usage:
  error-paths.py MODULE.py            inventory (DIAGNOSE) — the worklist, no verdict
  error-paths.py BEFORE.py AFTER.py   the gate (REPAIR) — the before/after delta is the verdict

An error path is a place a caller can observe a failure. Counted from the AST,
never from grep (a grep for 'raise' also matches comments and string literals):
  raise   — every `raise` site, bare re-raises included
  except  — every `except` handler, i.e. a failure case the design still admits
  assert  — every `assert`, the same failure wearing a different statement

Counting handlers is the point: wrapping a case in one more `try` — or swallowing
it with `except: pass` — leaves the count where it was or raises it. The only
move that lowers the count is deleting the case from the design.

Exit codes for the gate (distinct meanings, never shared):
  0  PASS   — AFTER exposes strictly fewer error paths than BEFORE
  1  FAIL   — AFTER exposes the same number or more, or BEFORE exposed none
  2  USAGE  — bad arguments, unreadable or undecodable file, unparseable source,
              a BEFORE that declares no top-level def/class, or an AFTER missing
              any top-level def/class BEFORE declared

Inventory mode grades nothing, so it never returns 1:
  0  the worklist printed — a worklist of zero is a report, never a PASS
  2  bad arguments, unreadable or undecodable file, unparseable source
Inventory opens one file for reading and prints; it writes nothing. A diagnostic
complaint buys a reading, not a rewrite.

Only `def`/`async def`/`class` at module level count as definitions: an
assignment of the same name (`Window = "unrelated"`) is a name, not a
definition, and can never stand in for the one it replaced.
"""
import ast
import os
import sys
from pathlib import Path


def die(msg):
    print(f"usage-error: {msg}", file=sys.stderr)
    raise SystemExit(2)


def parse(path):
    # Read bytes, not text: `ast` honours a PEP 263 coding cookie, while
    # read_text(encoding="utf-8") dies on a legitimate latin-1 module.
    try:
        src = Path(path).read_bytes()
    except OSError as exc:
        die(f"cannot read {path} ({exc})")
    try:
        return ast.parse(src, filename=str(path))
    except (SyntaxError, ValueError) as exc:
        # ValueError covers undecodable bytes and NUL bytes — a binary file is
        # misuse (exit 2), never a verdict.
        die(f"{path} is not parseable Python ({exc})")


def sites(tree):
    """Every raise site, except handler, and assert, tagged with its scope."""
    found = []

    def walk(node, scope):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                walk(child, scope + [child.name])
                continue
            if isinstance(child, ast.Raise):
                found.append((child.lineno, "raise ", ".".join(scope) or "(module)"))
            elif isinstance(child, ast.ExceptHandler):
                found.append((child.lineno, "except", ".".join(scope) or "(module)"))
            elif isinstance(child, ast.Assert):
                found.append((child.lineno, "assert", ".".join(scope) or "(module)"))
            walk(child, scope)

    walk(tree, [])
    return sorted(found)


def top_defs(tree):
    """Module-level `def`/`async def`/`class` names — definitions, not names.

    An `ast.Assign` target is deliberately excluded: `Window = "unrelated"`
    would otherwise satisfy a lost `class Window`.
    """
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def report(label, path, found):
    print(f"{label} {path} — {len(found)} error path(s)")
    for lineno, kind, scope in found:
        print(f"  L{lineno:<4} {kind}  {scope}")
    if not found:
        print("  (none)")


def inventory(path):
    """DIAGNOSE: the worklist for one module, and no verdict at all.

    A complaint ("this API throws too much") authorises a reading, not a rewrite,
    and a reading cannot supply an AFTER nobody has written yet. Running the gate
    against an unchanged working copy answers a diagnosis with FAIL (n → n), which
    is a verdict on work no one has done. This mode is that missing command.
    """
    found = sites(parse(path))
    report("INVENTORY", path, found)
    print(
        f"\n{len(found)} error path(s) on the worklist — no verdict: inventory reports, "
        "it does not grade. The gate is `error-paths.py BEFORE.py AFTER.py`."
    )
    return 0


def main(argv):
    if len(argv) not in (2, 3) or any(a.startswith("-") for a in argv[1:]):
        die(
            "error-paths.py MODULE.py  (inventory, no verdict)  |  "
            "error-paths.py BEFORE.py AFTER.py  (the gate) — no flags, "
            "the before/after delta is the only verdict"
        )
    if len(argv) == 2:
        return inventory(argv[1])
    before_path, after_path = argv[1], argv[2]
    before_tree, after_tree = parse(before_path), parse(after_path)
    before_defs, after_defs = top_defs(before_tree), top_defs(after_tree)
    # Module identity is anchored on the whole top-level definition set, not on
    # the error-bearing subset: a redesign of one module does not delete its
    # unrelated siblings, so a single shared name is not an interface match.
    # A BEFORE with no top-level definition has nothing to anchor on at all —
    # module-scope error paths included, which is why that is misuse, not a pass.
    if not before_defs:
        die(
            f"{before_path} declares no top-level def/class — nothing anchors the "
            "two files to one module (module-scope error paths need a named definition)"
        )
    dropped = sorted(before_defs - after_defs)
    if dropped:
        die(
            "AFTER is missing top-level definition(s) BEFORE declared: "
            f"{', '.join(dropped)} — a deletion or an unrelated file, not a redesign"
        )

    before_sites, after_sites = sites(before_tree), sites(after_tree)

    report("BEFORE", before_path, before_sites)
    report("AFTER ", after_path, after_sites)
    before_n, after_n = len(before_sites), len(after_sites)
    print(
        f"\n{before_n} → {after_n} error path(s) (delta {after_n - before_n:+d}); "
        f"retained interface: {', '.join(sorted(before_defs))}"
    )

    if before_n == 0:
        print("FAIL: BEFORE exposes 0 error paths — nothing to define out, the pass is a no-op")
        return 1
    if after_n >= before_n:
        print(f"FAIL: {after_n} >= {before_n} — error paths were handled or added, not defined out")
        return 1
    print(f"PASS: {before_n - after_n} error path(s) defined out of existence")
    return 0


if __name__ == "__main__":
    # The exit-code contract has to survive the interpreter's own shutdown. CPython
    # flushes the std streams after main() returns, and if that flush raises - a pipe
    # whose reader has gone, the ordinary `| head` idiom - it REPLACES the status with
    # 120, a code no table here names. argparse is the other leak: it raises SystemExit
    # from inside, so a usage error would skip any seal placed after a bare call.
    try:
        _code = main(sys.argv)
    except SystemExit as _exc:                 # argparse usage errors and --help
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
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
