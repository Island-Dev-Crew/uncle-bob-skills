#!/usr/bin/env python3
"""Proof grammar parser checks plus safe integration replays over hostile fixtures."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
VERIFY = HERE.parents[1] / "verify-proofs.py"
CLOSED = HERE.parents[1] / "closed-stream-check.py"
STATE_FIXTURE = HERE.parent / "unsafe-export-island" / "setup-state"
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
    unsafe_setup_blocks = {
        "function-brace": (
            'python3 () { return 7; }\n'
            'python3 -c "raise SystemExit(7)" # exit 7\n'
        ),
        "function-subshell": (
            'python3 () ( return 7 )\n'
            'python3 -c "raise SystemExit(7)" # exit 7\n'
        ),
        "function-conditional": (
            'python3 () if true; then return 7; else return 8; fi\n'
            'python3 -c "raise SystemExit(7)" # exit 7\n'
        ),
        "function-loop": (
            'python3 () while false; do return 8; done\n'
            'python3 -c "raise SystemExit(7)" # exit 7\n'
        ),
        "function-missing-body": (
            'python3 ()\n'
            'python3 -c "raise SystemExit(7)" # exit 7\n'
        ),
        "function-after-command": (
            'printf x >/dev/null; python3 () { return 7; }\n'
            'python3 -c "raise SystemExit(7)" # exit 7\n'
        ),
        "function-annotated": (
            'python3 () { return 0; } # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "printf-v": (
            "printf -v PATH '%s' /proof-verifier-no-such-path\n"
            'python3 -c "raise SystemExit(127)" # exit 127\n'
        ),
        "printf-n": (
            "printf x%n PATH\n"
            'python3 -c "raise SystemExit(127)" # exit 127\n'
        ),
        "printf-n-option-terminator": (
            "printf -- '%n' PATH\n"
            'python3 -c "raise SystemExit(127)" # exit 127\n'
        ),
        "printf-n-star-width": (
            "printf '%*n' 0 PATH\n"
            'python3 -c "raise SystemExit(127)" # exit 127\n'
        ),
        "printf-n-length-modifier": (
            "printf '%lln' PATH\n"
            'python3 -c "raise SystemExit(127)" # exit 127\n'
        ),
        "printf-v-safe-target-with-n": (
            "printf -v VALUE 'x%n' PATH\n"
            'python3 -c "raise SystemExit(127)" # exit 127\n'
        ),
        "printf-v-attached": (
            "printf -vPATH '%s' /proof-verifier-no-such-path\n"
            'python3 -c "raise SystemExit(127)" # exit 127\n'
        ),
        "unsafe-later-assignment": (
            "VALUE=ok; PATH=/proof-verifier-no-such-path\n"
            'python3 -c "raise SystemExit(127)" # exit 127\n'
        ),
    }
    for modifier in ("h", "hh", "l", "ll", "L", "j", "z", "t"):
        unsafe_setup_blocks[f"printf-{modifier}-n"] = (
            f"printf '%{modifier}n' PATH\n"
            'python3 -c "raise SystemExit(127)" # exit 127\n'
        )
    unsafe_setup_observed = {}
    for label, block in unsafe_setup_blocks.items():
        rows = list(module.commands(block))
        unsafe_setup_observed[label] = (
            rows[0][1] if rows else None,
            rows[-1][2] if rows else None,
            rows[-1][3] if rows else None,
        )
    unsafe_setup_expected = {
        label: ("__REFUSE__", [], frozenset({"refused"}))
        for label in unsafe_setup_blocks
    }
    if unsafe_setup_observed != unsafe_setup_expected:
        print(f"FAIL unsafe setup replay={unsafe_setup_observed!r}", file=sys.stderr)
        return 1

    replay_controls = {
        "ordinary-assignment": (
            'VALUE=ok\npython3 -c "raise SystemExit(0)" # exit 0\n',
            ["VALUE=ok"],
        ),
        "ordinary-assignment-sequence": (
            'LEFT=one; RIGHT=two\npython3 -c "raise SystemExit(0)" # exit 0\n',
            ["LEFT=one; RIGHT=two"],
        ),
        "ordinary-assignment-trailing-separator": (
            'VALUE=ok;\npython3 -c "raise SystemExit(0)" # exit 0\n',
            ["VALUE=ok"],
        ),
        "quoted-command-substitution": (
            'VALUE="$(printf "%s" "one two")"\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n',
            ['VALUE="$(printf "%s" "one two")"'],
        ),
        "ansi-quoted-assignment-data": (
            "VALUE=$'x\\'; PATH=still-data'\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n',
            ["VALUE=$'x\\'; PATH=still-data'"],
        ),
        "fixture-printf": (
            'D=$(mktemp -d)\nprintf \'%s\\n\' ok > "$D/value"\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n',
            ['D=$(mktemp -d)', 'printf \'%s\\n\' ok > "$D/value"'],
        ),
        "literal-dollar-format": (
            "printf '$%s\\n' ok >/dev/null\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n',
            ["printf '$%s\\n' ok >/dev/null"],
        ),
        "escaped-dollar-format": (
            "printf \\$%s ok >/dev/null\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n',
            ["printf \\$%s ok >/dev/null"],
        ),
        "empty-array-data": (
            "printf x >/dev/null; ARGS=()\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n',
            ["printf x >/dev/null; ARGS=()"],
        ),
        "quoted-paren-data": (
            "printf '()' > /dev/null\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n',
            ["printf '()' > /dev/null"],
        ),
        "escaped-paren-data": (
            "printf \\(\\) > /dev/null\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n',
            ["printf \\(\\) > /dev/null"],
        ),
    }
    replay_observed = {}
    for label, (block, _expected_setup) in replay_controls.items():
        rows = list(module.commands(block))
        replay_observed[label] = (rows[-1][2], rows[-1][3])
    replay_expected = {
        label: (expected_setup, frozenset())
        for label, (_block, expected_setup) in replay_controls.items()
    }
    if replay_observed != replay_expected:
        print(f"FAIL ordinary setup replay={replay_observed!r}", file=sys.stderr)
        return 1

    ansi_function_data = "printf '%s' $'x\\'; python3 ()' >/dev/null"
    if module.unsafe_setup_state(ansi_function_data):
        print("FAIL ANSI-C quoted function-shaped data was refused", file=sys.stderr)
        return 1

    mixed_assignment_rows = list(module.commands(
        'VALUE=ok; hash -p /bin/true python3\n'
        'python3 -c "raise SystemExit(1)" # exit 0\n'
    ))
    if (mixed_assignment_rows[-1][2] != []
            or mixed_assignment_rows[-1][3] != frozenset({"unreplayable"})):
        print(f"FAIL mixed assignment setup replay={mixed_assignment_rows!r}", file=sys.stderr)
        return 1

    for assignment in ("ARGS=(one two)", "VALUE=${MISSING:-one two}",
                       "VALUE=${MISSING:-a;b}", "SAFE=$((PATH=0))", "SAFE=$[PATH=0]",
                       'SAFE="$((PATH=0))"', 'SAFE="$[PATH=0]"',
                       'SAFE="${PATH:=/proof-verifier-no-such-path}"'):
        rows = list(module.commands(
            f'{assignment}\npython3 -c "raise SystemExit(0)" # exit 0\n'
        ))
        if rows[-1][2] != [] or rows[-1][3] != frozenset({"unreplayable"}):
            print(f"FAIL out-of-grammar assignment was replayed: {rows!r}", file=sys.stderr)
            return 1

    isolation_blocks = {
        "dynamic-format": (
            "FORMAT=%n\n"
            'printf "$FORMAT" PATH\n'
            'python3 -c "raise SystemExit(1)" # exit 127\n'
        ),
        "compound-printf": (
            "printf x >/dev/null; printf '%n' PATH\n"
            'python3 -c "raise SystemExit(1)" # exit 127\n'
        ),
        "command-hash": (
            "printf x >/dev/null; hash -p /bin/true python3\n"
            'python3 -c "raise SystemExit(1)" # exit 0\n'
        ),
        "generated-subshell-delimiter": (
            "printf x >/dev/null; ); PATH=/proof-verifier-no-such-path; "
            "( printf y >/dev/null\n"
            'python3 -c "raise SystemExit(1)" # exit 127\n'
        ),
    }
    for label, isolation_block in isolation_blocks.items():
        isolation_rows = list(module.commands(isolation_block))
        isolated_cmd, _expected, isolated_setup, _gaps = isolation_rows[-1]
        isolated = subprocess.run(
            ["bash", "-c", module.proof_script(isolated_setup, isolated_cmd)],
            text=True,
            capture_output=True,
            check=False,
        )
        if isolated.returncode != 1:
            print(
                f"FAIL runnable setup shell state escaped isolation ({label}) "
                f"rc={isolated.returncode} setup={isolated_setup!r}",
                file=sys.stderr,
            )
            return 1

    verifier = subprocess.run(
        [sys.executable, str(VERIFY), str(STATE_FIXTURE)],
        cwd=HERE.parents[2],
        text=True,
        capture_output=True,
        check=False,
    )
    if (verifier.returncode != 1 or "3 refused" not in verifier.stdout
            or "3 unsequenced" not in verifier.stdout
            or "2 proofs run" not in verifier.stdout):
        print(
            "FAIL unsafe setup integration "
            f"rc={verifier.returncode} stdout={verifier.stdout!r} stderr={verifier.stderr!r}",
            file=sys.stderr,
        )
        return 1

    closed = subprocess.run(
        [sys.executable, str(CLOSED), str(STATE_FIXTURE)],
        cwd=HERE.parents[2],
        text=True,
        capture_output=True,
        check=False,
    )
    if (closed.returncode != 2 or "4 closed-stream probes" not in closed.stdout
            or "3 refused" not in closed.stdout
            or "3 refusal-gapped" not in closed.stdout):
        print(
            "FAIL unsafe setup closed-stream inheritance "
            f"rc={closed.returncode} stdout={closed.stdout!r} stderr={closed.stderr!r}",
            file=sys.stderr,
        )
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
