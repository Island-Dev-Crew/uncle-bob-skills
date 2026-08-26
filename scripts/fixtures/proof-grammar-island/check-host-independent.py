#!/usr/bin/env python3
"""Prove report ownership is identical with an off-list command absent or on PATH."""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
VERIFY = HERE.parents[1] / "verify-proofs.py"
SELF = Path(__file__).resolve()
INNER_MISSING = "--internal-missing-verifier"
BLOCK = """\
python3 -c "import sys; sys.exit(127)"
seat3-offlist-no-script-operand --mode
echo $? # -> 127
"""
EXPECTED = [
    ('python3 -c "import sys; sys.exit(127)"', None),
    ("seat3-offlist-no-script-operand --mode", 127),
]


def load_verifier(path: Path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("verify_proofs_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def projection(module, search_path: Path):
    prior = os.environ.get("PATH")
    os.environ["PATH"] = str(search_path)
    try:
        return [(command, expected) for command, expected, _setup, _gap in module.commands(BLOCK)]
    finally:
        if prior is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = prior


def main(argv: list[str]) -> int:
    if argv == []:
        module = load_verifier(VERIFY)
    elif argv == [INNER_MISSING]:
        with tempfile.TemporaryDirectory(prefix="proof-host-missing-") as raw:
            module = load_verifier(Path(raw) / "verify-proofs.py")
    else:
        print(f"usage: {SELF.name} [{INNER_MISSING}]", file=sys.stderr)
        return 2
    shapes = {
        "seat3-offlist-no-script-operand --mode": True,
        "seat3:offlist --mode": True,
        "LEAKS output-shaped-but-ambiguous": True,
        "seat3-offlist 'unterminated": True,
        'seat3-offlist "unterminated': True,
        "seat3-offlist " + "\\": True,
        "| explicit proof output": False,
    }
    observed = {line: module.command_shaped(line) for line in shapes}
    if observed != shapes:
        print(f"FAIL command shapes={observed!r}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="proof-host-independence-") as raw:
        root = Path(raw)
        absent = root / "absent"
        present = root / "present"
        absent.mkdir()
        present.mkdir()
        fake = present / "seat3-offlist-no-script-operand"
        fake.write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

        without_tool = projection(module, absent)
        with_tool = projection(module, present)
        if without_tool != EXPECTED or with_tool != EXPECTED:
            print(f"FAIL absent={without_tool!r} present={with_tool!r}", file=sys.stderr)
            return 1
    if not argv:
        child = subprocess.run(
            [sys.executable, str(SELF), INNER_MISSING],
            cwd=HERE.parents[2],
            text=True,
            capture_output=True,
            check=False,
        )
        if child.returncode != 2 or "internal failure" not in child.stderr:
            print(
                f"FAIL missing verifier must be non-verdict 2, got {child.returncode}",
                file=sys.stderr,
            )
            return 1
        read_fd, write_fd = os.pipe()
        os.close(read_fd)
        try:
            dead = subprocess.run(
                [sys.executable, str(SELF), INNER_MISSING],
                cwd=HERE.parents[2],
                stdout=subprocess.DEVNULL,
                stderr=write_fd,
                check=False,
            )
        finally:
            os.close(write_fd)
        if dead.returncode != 2:
            print(
                f"FAIL missing verifier with dead stderr must exit 2, got {dead.returncode}",
                file=sys.stderr,
            )
            return 1
    return 0


def seal_streams(code: int) -> int:
    for stream, descriptor in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if stream is not None:
                stream.flush()
        except BaseException:
            if code in (0, 1):
                code = 2
            try:
                null_descriptor = os.open(os.devnull, os.O_WRONLY)
                try:
                    os.dup2(null_descriptor, descriptor)
                finally:
                    os.close(null_descriptor)
            except BaseException:
                pass
    return code


def entrypoint() -> int:
    try:
        return main(sys.argv[1:])
    except KeyboardInterrupt:
        return 2
    except BaseException as exc:
        try:
            print(
                f"proof host regression: internal failure: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
        except BaseException:
            pass
        return 2


if __name__ == "__main__":
    sys.exit(seal_streams(entrypoint()))
