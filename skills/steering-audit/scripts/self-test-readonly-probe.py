#!/usr/bin/env python3
"""Exercise readonly-probe.py from a source copy with no writable repository bytes.

The release-review clone is deliberately read-only. This regression test recreates that
condition, runs the normal proof and every watched-red mutation, and requires the documented
0/1 verdicts. It also verifies that the read-only source copy itself remains byte-, type-,
link-, and mode-identical across the run.

Exit 0 when all five cases return their documented codes and the source copy is unchanged;
1 on a behavioral mismatch; 2 on usage, IO, or an internal test-harness failure.
"""
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ISLAND = Path(__file__).resolve().parent.parent


def entry_state(path: Path) -> str:
    info = path.lstat()
    mode = oct(stat.S_IMODE(info.st_mode))
    if stat.S_ISLNK(info.st_mode):
        return f"symlink {mode} -> {os.readlink(path)}"
    if stat.S_ISDIR(info.st_mode):
        return f"dir {mode}"
    if stat.S_ISREG(info.st_mode):
        return f"file {mode} {hashlib.sha256(path.read_bytes()).hexdigest()}"
    return f"{stat.S_IFMT(info.st_mode):#o} {mode}"


def tree_state(root: Path) -> dict[str, str]:
    state = {".": entry_state(root)}
    stack = [root]
    while stack:
        parent = stack.pop()
        for child in sorted(parent.iterdir()):
            state[str(child.relative_to(root))] = entry_state(child)
            if child.is_dir() and not child.is_symlink():
                stack.append(child)
    return state


def set_owner_writable(root: Path, writable: bool) -> None:
    """Toggle only owner-write on real entries; never follow a fixture symlink."""
    paths = [root]
    stack = [root]
    while stack:
        parent = stack.pop()
        for child in parent.iterdir():
            paths.append(child)
            if child.is_dir() and not child.is_symlink():
                stack.append(child)
    for path in reversed(paths) if not writable else paths:
        if path.is_symlink():
            continue
        mode = stat.S_IMODE(path.lstat().st_mode)
        if writable:
            mode |= stat.S_IWUSR
            if path.is_dir():
                mode |= stat.S_IXUSR
        else:
            mode &= ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
        path.chmod(mode)


def main() -> int:
    if len(sys.argv) != 1:
        print(__doc__)
        return 2
    cases = [
        ("normal", [], 0),
        ("append", ["--red"], 1),
        ("mkdir", ["--red=mkdir"], 1),
        ("chmod", ["--red=chmod"], 1),
        ("symlink", ["--red=symlink"], 1),
    ]
    failures = []
    with tempfile.TemporaryDirectory(prefix="steering-audit-readonly-source-") as tmp:
        clone = Path(tmp) / "steering-audit"
        shutil.copytree(ISLAND, clone)
        try:
            set_owner_writable(clone, False)
            before = tree_state(clone)
            probe = clone / "scripts" / "readonly-probe.py"
            for label, args, expected in cases:
                result = subprocess.run(
                    [sys.executable, str(probe), *args],
                    cwd=clone,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                print(f"{label}: exit {result.returncode} (expected {expected})")
                if result.returncode != expected:
                    failures.append((label, expected, result))
            after = tree_state(clone)
            if after != before:
                failures.append(("source-tree-mutated", 0, None))
        finally:
            # TemporaryDirectory cannot remove a deliberately read-only tree on every platform.
            if clone.exists():
                set_owner_writable(clone, True)

    for label, expected, result in failures:
        if result is None:
            print("FAIL read-only source copy changed", file=sys.stderr)
            continue
        print(
            f"FAIL {label}: readonly-probe exited {result.returncode}, expected {expected}",
            file=sys.stderr,
        )
        if result.stdout:
            print(result.stdout, end="", file=sys.stderr)
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    print(f"{len(cases)} read-only-source case(s), {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        _code = main()
    except KeyboardInterrupt:
        _code = 2
    except BaseException as _exc:
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
            if _code in (0, 1):
                _code = 2
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
