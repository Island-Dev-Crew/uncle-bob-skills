#!/usr/bin/env python3
"""Watched-red verdict tests for scripts/validate-island.py."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-island.py"
ENV = {
    **os.environ,
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONIOENCODING": "utf-8",
}


class TestFailure(RuntimeError):
    pass


def expect(name: str, args: list[str], code: int, needles: tuple[str, ...]) -> None:
    result = subprocess.run(args, cwd=ROOT, env=ENV, text=True, capture_output=True)
    output = result.stdout + result.stderr
    if result.returncode != code:
        raise TestFailure(f"{name}: expected exit {code}, got {result.returncode}\n{output}")
    missing = [needle for needle in needles if needle not in output]
    if missing:
        raise TestFailure(f"{name}: missing {missing!r}\n{output}")
    print(f"OK   {name} exit={code}")


def main() -> int:
    py = sys.executable
    cases = (
        (
            "green-island",
            [py, str(VALIDATOR), "scripts/fixtures/good-island"],
            0,
            ("12 checks, 0 failed, islands: 1",),
        ),
        (
            "known-bad-island",
            [py, str(VALIDATOR), "scripts/fixtures/bad-island"],
            1,
            ("FAIL bad-island",),
        ),
        (
            "nonstring-metadata",
            [py, str(VALIDATOR), "scripts/fixtures/bad-island/nonstring-metadata"],
            1,
            ("F3", "F6", "F7"),
        ),
        (
            "missing-scope",
            [py, str(VALIDATOR), "scripts/fixtures/does-not-exist"],
            2,
            ("not a directory",),
        ),
        (
            "missing-arguments",
            [py, str(VALIDATOR)],
            2,
            ("Usage:",),
        ),
        (
            "missing-pyyaml",
            [py, "-S", str(VALIDATOR), "scripts/fixtures/good-island"],
            2,
            ("missing PyYAML", "requirements.txt"),
        ),
        (
            "broken-pyyaml",
            [
                py,
                "-c",
                "import builtins,runpy,sys\n"
                "real_import=builtins.__import__\n"
                "def hooked(name,*args,**kwargs):\n"
                "    if name == 'yaml': raise RuntimeError('broken install')\n"
                "    return real_import(name,*args,**kwargs)\n"
                "builtins.__import__=hooked\n"
                "target=sys.argv[1]\n"
                "sys.argv=[target,*sys.argv[2:]]\n"
                "runpy.run_path(target,run_name='__main__')",
                str(VALIDATOR),
                "scripts/fixtures/good-island",
            ],
            2,
            ("could not initialize PyYAML", "RuntimeError", "requirements.txt"),
        ),
    )
    for case in cases:
        expect(*case)
    print(f"\n{len(cases)} validate-island self-tests, 0 failures")
    return 0


if __name__ == "__main__":
    try:
        _code = main()
    except KeyboardInterrupt:
        _code = 2
    except BaseException as _exc:
        try:
            print(
                f"self-test-validate-island: internal failure: "
                f"{type(_exc).__name__}: {_exc}",
                file=sys.stderr,
            )
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
