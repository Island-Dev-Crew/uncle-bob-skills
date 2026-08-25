#!/usr/bin/env python3
"""check-destination.py — enforced preflight for where an arch-lens build may write.

Usage: python3 check-destination.py <mode> <dest-dir> <repo-root> [--overwrite]
       mode is 'look' (read-only view, renders OUT of the target tree) or
       'instrument' (authorized install, renders INTO tools/arch-lens/ in the tree)

Exit 0 iff every check passes, exit 1 on a breach, exit 2 on usage or IO error - an
error path never borrows the verdict's code. Each check prints OK/FAIL and can go red.
  D1 mode is exactly 'look' or 'instrument'                        (else exit 2)
  D2 destination lane: a 'look' destination resolves strictly OUTSIDE the repo root;
     an 'instrument' destination resolves strictly INSIDE it, never the root itself.
     Symlinks are resolved first, so a link out of the tree does not launder the lane.
  D3 collision: the destination holds no existing lens artifact (graph.json, graph.js,
     index.html, extract.*) unless --overwrite is passed. A reserved name worn by anything
     other than a regular file - a directory, or a symlink live or dangling - is a breach
     --overwrite does NOT clear: the renderer cannot create its artifact over it, and
     clearing it means deleting a subtree this gate never looked into or writing through a
     link to a path that may sit outside the destination entirely. A destination that
     exists and is not a directory is a breach too. Other names are ignored.

What it does NOT do, stated rather than implied: it never creates, writes, or deletes
anything, and it cannot tell whether the human authorized the mode it was handed - the
mode is the caller's claim. It gates the destination, not the intent.
"""
import os
import sys
from pathlib import Path

LENS_FILES = ("graph.json", "graph.js", "index.html")
LENS_STEM = "extract"


def check(cid: str, ok: bool, detail: str) -> bool:
    print(("OK  " if ok else "FAIL") + f" {cid} {detail}")
    return ok


def occupants(dest: Path):
    """Entries directly inside dest wearing a reserved lens name, split by what they are.

    A regular file is a lens artifact and --overwrite can authorize replacing it. Anything
    else wearing one of those names is an OBSTRUCTION, and the two need different answers.
    A renderer cannot create graph.json over a directory called graph.json, and over a
    symlink it does not create a file at all - it writes THROUGH the link to wherever that
    link points, which is how a look reaches back inside the tree D2 just kept it out of.
    is_symlink() is asked first because a link to a directory answers yes to both questions.
    """
    files, obstructions = [], []
    for entry in sorted(dest.iterdir()):
        if entry.name not in LENS_FILES and entry.stem != LENS_STEM:
            continue
        if entry.is_symlink():
            obstructions.append(f"{entry.name} (symlink)")
        elif entry.is_dir():
            obstructions.append(f"{entry.name} (directory)")
        elif entry.is_file():
            files.append(entry.name)
        else:
            obstructions.append(f"{entry.name} (not a regular file)")
    return files, obstructions


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--overwrite"]
    overwrite = "--overwrite" in sys.argv[1:]
    if len(argv) != 3:
        print(__doc__)
        return 2
    mode, dest_arg, root_arg = argv
    if mode not in ("look", "instrument"):
        check("D1", False, f"unknown mode {mode!r}; expected 'look' or 'instrument'")
        return 2
    check("D1", True, f"mode {mode!r}")
    root = Path(root_arg)
    if not root.is_dir():
        print(f"check-destination: repo root is not a directory: {root_arg}", file=sys.stderr)
        return 2
    try:
        root = root.resolve()
        dest = Path(dest_arg).resolve()
    except OSError as e:
        print(f"check-destination: cannot resolve a path: {e}", file=sys.stderr)
        return 2

    inside = dest == root or dest.is_relative_to(root)
    if mode == "look":
        ok = check("D2", not inside,
                   f"{dest_arg} resolves outside the target repo" if not inside
                   else f"a look may not write inside the repo it renders: {dest} is under {root}")
    else:
        ok = check("D2", inside and dest != root,
                   f"{dest_arg} resolves strictly inside the target repo" if inside and dest != root
                   else f"an instrument install must land strictly inside {root}, not at {dest}")

    if dest.exists() and not dest.is_dir():
        ok &= check("D3", False, f"destination exists and is not a directory: {dest}")
    elif not dest.is_dir():
        ok &= check("D3", True, "destination does not exist yet; nothing to overwrite")
    else:
        try:
            held, blocked = occupants(dest)
        except OSError as e:
            print(f"check-destination: cannot read destination: {e}", file=sys.stderr)
            return 2
        if blocked:
            detail = "reserved lens name the renderer cannot write: " + ", ".join(blocked)
            if held:
                detail += "; alongside lens file(s): " + ", ".join(held)
            ok &= check("D3", False, detail + " - clear it by hand; --overwrite authorizes"
                        " replacing a lens, not deleting a subtree or writing through a link")
        elif held and not overwrite:
            ok &= check("D3", False,
                        "destination already holds a lens: " + ", ".join(held)
                        + " - pass --overwrite only when the human authorized replacing it")
        elif held:
            ok &= check("D3", True, "overwrite authorized for: " + ", ".join(held))
        else:
            ok &= check("D3", True, "destination holds no lens artifact")
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
