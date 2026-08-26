#!/usr/bin/env python3
"""Require both benign nested-substitution bypass fixtures to be caught."""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE.parents[1] / "closed-stream-check.py"
FIXTURE = HERE / "nested-substitution"


def main() -> int:
    if len(sys.argv) != 1:
        print(__doc__)
        return 2
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), str(FIXTURE)],
            cwd=HERE.parents[2],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"nested-substitution regression could not run: {exc}", file=sys.stderr)
        return 2
    leaks = [
        line for line in result.stdout.splitlines()
        if line.startswith("LEAK nested-substitution:")
    ]
    summary = next(
        (line for line in result.stdout.splitlines() if "closed-stream probes over" in line),
        "",
    )
    expected_summary = (
        "8 closed-stream probes over 1 island(s), 3 leak(s) "
        "(0 fail-closed to the pack-wide exit-2 seal; 0 candidate(s) not re-probed: "
        "they close a stream themselves)"
    )
    if result.returncode != 1 or len(leaks) != 3 or summary != expected_summary:
        print(
            "FAIL nested substitutions did not leave all three outer gates eligible for probing",
            file=sys.stderr,
        )
        print(result.stdout, end="", file=sys.stderr)
        print(result.stderr, end="", file=sys.stderr)
        return 1
    print("OK all three nested-substitution outer gates were probed and leaked")
    return 0


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
