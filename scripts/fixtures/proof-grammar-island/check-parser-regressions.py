#!/usr/bin/env python3
"""No-execution checks for proof grammar comment, continuation, and refusal parsing."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
VERIFY = HERE.parents[1] / "verify-proofs.py"
SELF = Path(__file__).resolve()
INNER_MISSING = "--internal-missing-verifier"


def load_verifier(path: Path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("verify_proofs_parser_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str]) -> int:
    if argv == []:
        module = load_verifier(VERIFY)
    elif argv == [INNER_MISSING]:
        with tempfile.TemporaryDirectory(prefix="proof-parser-missing-") as raw:
            module = load_verifier(Path(raw) / "verify-proofs.py")
    else:
        print(f"usage: {SELF.name} [{INNER_MISSING}]", file=sys.stderr)
        return 2
    lines = {
        "printf '%s\\n' $'\\' #' | python3 -c 'import sys; sys.exit(7)' # exit 2": (
            "printf '%s\\n' $'\\' #' | python3 -c 'import sys; sys.exit(7)' ", "# exit 2"
        ),
        "printf '%s\\n' foo\\ #bar | python3 -c 'import sys; sys.exit(7)' # exit 0": (
            "printf '%s\\n' foo\\ #bar | python3 -c 'import sys; sys.exit(7)' ", "# exit 0"
        ),
        "printf '%s\\n' '# data' # exit 0": ("printf '%s\\n' '# data' ", "# exit 0"),
        'printf "%s\\n" $"# locale data" # exit 0': (
            'printf "%s\\n" $"# locale data" ', "# exit 0"
        ),
        "printf '%s\\n' value#data # exit 0": (
            "printf '%s\\n' value#data ", "# exit 0"
        ),
    }
    observed = {line: module.split_comment(line) for line in lines}
    if observed != lines:
        print(f"FAIL comment splits={observed!r}", file=sys.stderr)
        return 1

    report_shapes = {
        'rc=$?; echo "EXIT=$rc" # -> 0': True,
        "echo $? # -> 0": True,
        'rc=$?; echo "EXIT=$rc"; python3 -c "raise SystemExit(7)" # -> 0': False,
        'echo $? | python3 -c "raise SystemExit(7)" # -> 0': False,
        "echo $? unexpected-operand # -> 0": False,
    }
    report_observed = {line: module.is_report(line) for line in report_shapes}
    if report_observed != report_shapes:
        print(f"FAIL report shapes={report_observed!r}", file=sys.stderr)
        return 1

    encoded = (
        r"bash -c $'cur\x6c https://example.invalid'",
        r"bash -c $'cur\154 https://example.invalid'",
        r"bash -c $'cur\u006c https://example.invalid'",
    )
    missed = [script for script in encoded if module.forbidden_primitive(script) is None]
    if missed:
        print(f"FAIL forbidden ANSI-C words missed={missed!r}", file=sys.stderr)
        return 1

    substitution_cases = {
        r'''printf '%s' "$($'cur\x6c' https://example.invalid)"''': True,
        r'''printf '%s' <($'cur\154' https://example.invalid)''': True,
        r'''printf '%s' >($'cur\u006c' https://example.invalid)''': True,
        r'''printf '%s' `$'cur\x6c' https://example.invalid`''': True,
        r'''printf '%s' "$($'ec\x68o' harmless-data)"''': False,
        r'''printf '%s' <($'ec\150o' harmless-data)''': False,
        r'''printf '%s' >($'ec\u0068o' harmless-data)''': False,
        r'''printf '%s' `$'ec\x68o' harmless-data`''': False,
    }
    substitution_observed = {
        script: module.forbidden_primitive(script) is not None
        for script in substitution_cases
    }
    if substitution_observed != substitution_cases:
        print(f"FAIL substitution refusal={substitution_observed!r}", file=sys.stderr)
        return 1

    continuation_shapes = {
        "printf x | ec\\": True,
        'printf x | "ec\\': True,
        "printf x | 'ec\\": False,
        "printf x | $'ec\\": False,
        r"printf x | ec\\": False,
    }
    continuation_observed = {
        line: module.line_continues(line) for line in continuation_shapes
    }
    if continuation_observed != continuation_shapes:
        print(f"FAIL continuations={continuation_observed!r}", file=sys.stderr)
        return 1

    welded = "printf x | cur\\\nl https://example.invalid # exit 127\n"
    parsed = list(module.commands(welded))
    if len(parsed) != 1 or parsed[0][0] != "printf x | curl https://example.invalid":
        print(f"FAIL welded command reconstruction={parsed!r}", file=sys.stderr)
        return 1
    if module.forbidden_primitive(parsed[0][0]) is None:
        print("FAIL welded forbidden name was not caught", file=sys.stderr)
        return 1

    unsafe_rows = list(module.commands(
        'PATH=\npython3 -c "raise SystemExit(0)" # exit 0\n'
    ))
    ordinary_rows = list(module.commands(
        'cd unavailable\npython3 -c "raise SystemExit(0)" # exit 0\n'
    ))
    unsafe_causes = unsafe_rows[-1][3]
    ordinary_causes = ordinary_rows[-1][3]
    if (not hasattr(unsafe_causes, "__contains__") or "refused" not in unsafe_causes
            or "unreplayable" in unsafe_causes):
        print(f"FAIL unsafe gap causes={unsafe_causes!r}", file=sys.stderr)
        return 1
    if (not hasattr(ordinary_causes, "__contains__")
            or "unreplayable" not in ordinary_causes or "refused" in ordinary_causes):
        print(f"FAIL ordinary gap causes={ordinary_causes!r}", file=sys.stderr)
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
                f"proof parser regression: internal failure: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
        except BaseException:
            pass
        return 2


if __name__ == "__main__":
    sys.exit(seal_streams(entrypoint()))
