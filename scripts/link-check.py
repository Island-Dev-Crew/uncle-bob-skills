#!/usr/bin/env python3
"""link-check.py — every relative markdown link in the COMMITTED tree must resolve.

Usage: python3 scripts/link-check.py [rev]        (default: HEAD)

The pack published "765 committed relative links, 0 dead" with no instrument behind it — a
number a reader could not re-derive from any command in the repository, in a pack whose first
law is that no claim outranks its evidence. This is that instrument.

It reads the COMMITTED tree (`git ls-tree`, `git show`), never the worktree, because the
worktree is where this pack's own history hides things: two dead links shipped in v1.0 because
the check ran against a working copy whose files never got committed, and an untracked
transcript later made a whole proof block green only on the author's machine.

A link is checked when it is relative; http(s)/mailto and pure #fragments are not this tool's
concern. A target resolves when it is a tracked file, or a tracked directory (a prefix of some
tracked path). Fragments are stripped — anchor validity is a different check with different
rules (GitHub's slugger), and claiming it here would overstate.

Exit 0 when every relative link resolves AND at least one was checked; 1 when any is dead,
listing each; 2 on usage or a git error; 3 when zero links were found — a checker that
checked nothing has verified nothing, and this pack does not report that as a pass.
"""
import os
import posixpath
import re
import subprocess
import sys

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def git(args, rev_ok=False):
    r = subprocess.run(["git"] + args, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", errors="replace").strip())
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        print(__doc__, file=sys.stderr)
        return 2
    rev = argv[0] if argv else "HEAD"
    try:
        tracked = set(t for t in git(["ls-tree", "-r", "--name-only", rev]).split("\n") if t)
    except RuntimeError as exc:
        print(f"link-check: {exc}", file=sys.stderr)
        return 2
    checked = 0
    dead = []
    for f in sorted(t for t in tracked if t.endswith(".md")):
        body = git(["show", f"{rev}:{f}"])
        for target in LINK.findall(body):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#")[0].split("?")[0]
            if not path:
                continue
            checked += 1
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(f), path))
            if resolved in tracked:
                continue
            if any(t.startswith(resolved.rstrip("/") + "/") for t in tracked):
                continue                       # a directory link
            dead.append((f, target))
    for f, target in dead:
        print(f"DEAD {f} -> {target}")
    print(f"\n{checked} relative links checked at {rev}, {len(dead)} dead")
    if dead:
        return 1
    if checked == 0:
        print("NOTHING CHECKED - no relative links found; this is not a pass", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    try:
        _code = main()
    except KeyboardInterrupt:
        _code = 2
    except BaseException as _exc:
        print(f"error: internal failure: {type(_exc).__name__}: {_exc}", file=sys.stderr)
        _code = 2
    for _stream, _fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if _stream is not None:
                _stream.flush()
        except BaseException:
            if _code in (0, 1):
                _code = 2
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
