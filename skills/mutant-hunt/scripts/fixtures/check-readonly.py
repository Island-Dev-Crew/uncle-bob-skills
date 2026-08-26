#!/usr/bin/env python3
"""Exercise mkrepo.sh from a source tree whose committed bytes are read-only."""

from __future__ import annotations

import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
DIFF_SCOPE = HERE.parent / "diff-scope.sh"


def make_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        mode = path.stat().st_mode
        path.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    mode = root.stat().st_mode
    root.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def restore_owner_write(root: Path) -> None:
    if not root.exists():
        return
    root.chmod(root.stat().st_mode | stat.S_IWUSR | stat.S_IXUSR)
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        bits = stat.S_IWUSR | (stat.S_IXUSR if path.is_dir() else 0)
        path.chmod(path.stat().st_mode | bits)


def fail(message: str, process: subprocess.CompletedProcess[str] | None = None) -> int:
    print(f"FAIL {message}", file=sys.stderr)
    if process is not None:
        if process.stdout:
            print(process.stdout.rstrip(), file=sys.stderr)
        if process.stderr:
            print(process.stderr.rstrip(), file=sys.stderr)
    return 1


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="mutant-hunt-readonly-"))
    frozen = root / "fixtures"
    try:
        shutil.copytree(HERE, frozen)
        make_read_only(frozen)

        cases = {
            "dirty": (1, ""),
            "clean": (0, "pricing.js:3-3\npricing.js:6-8\n"),
        }
        for kind, (want_code, want_stdout) in cases.items():
            repo = root / f"repo-{kind}"
            built = subprocess.run(
                ["bash", str(frozen / "mkrepo.sh"), kind, str(repo)],
                text=True,
                capture_output=True,
                check=False,
            )
            if built.returncode != 0 or built.stdout != f"{repo}\n":
                return fail(f"{kind} fixture did not build from read-only source", built)

            checked = subprocess.run(
                ["bash", str(DIFF_SCOPE), "HEAD~1", "HEAD", str(repo)],
                text=True,
                capture_output=True,
                check=False,
            )
            if checked.returncode != want_code or checked.stdout != want_stdout:
                return fail(f"{kind} fixture produced the wrong scope verdict", checked)

        return 0
    finally:
        restore_owner_write(root)
        shutil.rmtree(root)


if __name__ == "__main__":
    raise SystemExit(main())
