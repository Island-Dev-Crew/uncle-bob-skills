#!/usr/bin/env python3
"""readonly-probe.py — prove this island's REPORT toolkit cannot mutate what it reads.

Usage:
  readonly-probe.py           run inventory.py extract + check over a sandbox copy of
                              scripts/fixtures/ and assert the tree came back untouched
  readonly-probe.py --red[=KIND]
                              run scripts/fixtures/mutating-stub.py under the same
                              harness instead; KIND picks the mutation it makes - append
                              (the default), mkdir, chmod, or symlink - and the probe
                              must fail on every one

An audit invoked observationally (REPORT) may print anything and must change nothing.
That claim is worth no more than the run behind it, so this probe copies the fixtures
into a temp tree, records (relative path, fingerprint) for every entry in it, runs the
commands against the copy, records again, and diffs the two manifests. Created, deleted,
and modified paths are all breaches and all named.

The fingerprint is what the path IS, not only what bytes it holds - entry type, mode
bits, symlink target, and for a regular file the sha256 of its contents. Hashing bytes
alone would leave whole classes of mutation invisible: a created or deleted empty
directory, a chmod, a symlink (a dangling one has no bytes to hash at all).

Deterministic: same fixtures, same verdict; no model, no network, no shell.

Exit codes:
  0  every probed command ran and the sandbox tree came back unchanged - same
     entries, same types, same modes, same link targets, same bytes
  1  the tree changed - each created/deleted/modified path is printed
  2  usage error, IO error, or a probed command that could not be launched at all
     (a probe that ran nothing has proven nothing, so that is never a pass)
"""
import hashlib
import shutil
import stat
import subprocess
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
INVENTORY = HERE / "inventory.py"
STUB = FIXTURES / "mutating-stub.py"


def fingerprint(p: Path) -> str:
    """Everything about one path that a mutation could move, as a comparable string."""
    st = p.lstat()                             # lstat: describe the link, not its target
    mode = oct(stat.S_IMODE(st.st_mode))
    if stat.S_ISLNK(st.st_mode):
        return f"symlink {mode} -> {os.readlink(p)}"
    if stat.S_ISDIR(st.st_mode):
        return f"dir {mode}"
    if stat.S_ISREG(st.st_mode):
        return f"file {mode} {hashlib.sha256(p.read_bytes()).hexdigest()}"
    return f"{stat.S_IFMT(st.st_mode):#o} {mode}"


def walk(root: Path):
    """Every path under root, never following a symlink back out of the sandbox.

    Path.rglob descended into symlinked directories before Python 3.13, so a probed
    command that dropped a link to `.` could spin this walk forever and the verdict would
    never arrive. Descending only into real directories keeps it reachable everywhere.
    """
    stack = [root]
    while stack:
        for child in sorted(stack.pop().iterdir()):
            yield child
            if child.is_dir() and not child.is_symlink():
                stack.append(child)


def manifest(root: Path):
    """(relative path -> fingerprint) for every entry under root, deterministic.

    The root itself is entry "." so that a chmod of the tree top is a breach like any
    other; the callers below know it is there and do not count it as a probed path.
    """
    out = {".": fingerprint(root)}
    for p in walk(root):
        out[str(p.relative_to(root))] = fingerprint(p)
    return out


def make_sandbox_writable(root: Path) -> None:
    """Make only the disposable copy owner-writable, never following a symlink.

    `copytree` preserves source modes. That is normally useful, but a release-review clone is
    deliberately read-only, so its copied fixture root and files also became read-only. The red
    controls then failed before mutating anything and proved no detection path. This sandbox is
    scratch space created for those commands; normalising it before the baseline fingerprint
    lets every watched-red mutation execute without touching or weakening the source tree.
    """
    for path in (root, *walk(root)):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            continue
        mode = stat.S_IMODE(info.st_mode) | stat.S_IWUSR
        if stat.S_ISDIR(info.st_mode):
            mode |= stat.S_IXUSR
        path.chmod(mode)


def main() -> int:
    red = None
    for arg in sys.argv[1:]:
        if arg == "--red":
            red = "append"
        elif arg.startswith("--red=") and len(arg) > len("--red="):
            red = arg[len("--red="):]
        else:
            print(__doc__)
            return 2
    if not FIXTURES.is_dir() or not INVENTORY.is_file():
        print(f"readonly-probe: missing {FIXTURES} or {INVENTORY}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="steering-audit-probe-") as tmp:
        sandbox = Path(tmp) / "fixtures"
        shutil.copytree(FIXTURES, sandbox)
        make_sandbox_writable(sandbox)
        if red is not None:
            if not STUB.is_file():
                print(f"readonly-probe: missing red fixture {STUB}", file=sys.stderr)
                return 2
            cmds = [[sys.executable, str(STUB), red]]
        else:
            cmds = [
                [sys.executable, str(INVENTORY), "extract", "prompt.md"],
                [sys.executable, str(INVENTORY), "check", "prompt.md", "audit-complete.md"],
            ]
        before = manifest(sandbox)
        if not cmds or len(before) < 2:     # "." alone means an empty sandbox
            print("readonly-probe: nothing to probe; this is not a pass", file=sys.stderr)
            return 2
        for cmd in cmds:
            try:
                p = subprocess.run(cmd, cwd=sandbox, capture_output=True, timeout=60)
            except (OSError, subprocess.SubprocessError) as exc:
                print(f"readonly-probe: cannot run {cmd[1:]}: {exc}", file=sys.stderr)
                return 2
            print(f"ran {' '.join(Path(c).name for c in cmd[1:])} -> exit {p.returncode}")
            if red is not None and p.returncode != 0:
                # A red fixture that could not make its mutation leaves nothing to catch,
                # and a green verdict there would be the probe passing its own blind spot.
                sys.stderr.write(p.stderr.decode("utf-8", "replace"))
                print(f"readonly-probe: red fixture made no {red!r} mutation; "
                      "nothing was proven", file=sys.stderr)
                return 2
        after = manifest(sandbox)

    breaches = []
    for path in sorted(set(before) | set(after)):
        if path not in after:
            breaches.append(f"DELETED  {path}")
        elif path not in before:
            breaches.append(f"CREATED  {path}")
        elif before[path] != after[path]:
            breaches.append(f"MODIFIED {path}")
    for line in breaches:
        print(line)
    print(f"\n{len(before) - 1} entries probed, {len(breaches)} mutation(s)")
    return 1 if breaches else 0


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
