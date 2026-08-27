#!/usr/bin/env python3
"""Proof grammar parser checks plus safe integration replays over hostile fixtures."""

from __future__ import annotations

import importlib.util
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
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

    # The startup probe is part of the parser's security boundary. Exercise every accepted
    # structural profile plus the two malformed-output cases that must fall back conservatively.
    probe_rows = {
        "legacy-no-increment": (
            "A:{foo..bar}{1..2}\nB:{foo..{1..2}}\n"
            "C:{1..3..2}\nD:a\nD:b\n",
            ("legacy", False),
        ),
        "legacy-increment": (
            "A:{foo..bar}{1..2}\nB:{foo..{1..2}}\n"
            "C:1\nC:3\nD:a\nD:b\n",
            ("legacy", True),
        ),
        "postamble": (
            "A:{foo..bar}1\nA:{foo..bar}2\nB:{foo..{1..2}}\n"
            "C:1\nC:3\nD:a\nD:b\n",
            ("postamble", True),
        ),
        "validated": (
            "A:{foo..bar}1\nA:{foo..bar}2\nB:{foo..1}\nB:{foo..2}\n"
            "C:1\nC:3\nD:a\nD:b\n",
            ("validated", True),
        ),
        "disabled": (
            "A:{foo..bar}{1..2}\nB:{foo..{1..2}}\n"
            "C:{1..3..2}\nD:{a,b}\n",
            ("disabled", False),
        ),
        "missing-b": (
            "A:{foo..bar}{1..2}\nC:{1..3..2}\nD:a\nD:b\n",
            ("unknown", True),
        ),
    }
    original_probe_run = module.subprocess.run
    probe_mismatches = {}
    try:
        for label, (stdout, expected) in probe_rows.items():
            module.subprocess.run = lambda *_args, _stdout=stdout, **_kwargs: (
                subprocess.CompletedProcess([], 0, _stdout.encode("utf-8"), b"")
            )
            observed = {
                "bash": module.probe_bash_brace_profile(),
                "sh": module.probe_shell_brace_profile(module.SH_EXECUTABLE),
            }
            if any(value != expected for value in observed.values()):
                probe_mismatches[label] = {"observed": observed, "expected": expected}
        module.subprocess.run = lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 0, b"A:\xff\n", b""
        )
        observed = {
            "bash": module.probe_bash_brace_profile(),
            "sh": module.probe_shell_brace_profile(module.SH_EXECUTABLE),
        }
        if any(value != ("unknown", True) for value in observed.values()):
            probe_mismatches["non-utf8"] = {
                "observed": observed,
                "expected": ("unknown", True),
            }
    finally:
        module.subprocess.run = original_probe_run
    if probe_mismatches:
        print(f"FAIL Bash brace probe profiles={probe_mismatches!r}", file=sys.stderr)
        return 1
    if module.BASH_EXECUTABLE is None or not Path(module.BASH_EXECUTABLE).is_absolute():
        print(
            f"FAIL Bash executable is not startup-bound={module.BASH_EXECUTABLE!r}",
            file=sys.stderr,
        )
        return 1
    if module.SH_EXECUTABLE is None or not Path(module.SH_EXECUTABLE).is_absolute():
        print(
            f"FAIL sh executable is not startup-bound={module.SH_EXECUTABLE!r}",
            file=sys.stderr,
        )
        return 1
    with tempfile.TemporaryDirectory(prefix="proof-bash-binding-") as raw:
        root = Path(raw)
        startup = root / "startup"
        island = root / "island"
        startup.mkdir()
        island.mkdir()
        (startup / "bash").symlink_to(module.BASH_EXECUTABLE)
        (island / "SKILL.md").write_text(
            "---\nname: bash-binding-fixture\n"
            "description: A temporary fixed Bash binding fixture with enough explanatory text.\n"
            "---\n\n```bash\nprintf x >/dev/null # exit 0\n```\n",
            encoding="utf-8",
        )
        bound_environment = os.environ.copy()
        bound_environment["PATH"] = str(startup)
        hook_marker = root / "ambient-hook-ran"
        hook = root / "ambient-bash-env"
        hook.write_text(
            "builtin printf x > " + shlex.quote(str(hook_marker)) + "\n",
            encoding="utf-8",
        )
        bound_environment["BASH_ENV"] = str(hook)
        bound_environment["BASH_FUNC_printf%%"] = "() { return 7; }"
        completed = subprocess.run(
            [sys.executable, str(VERIFY), str(island)],
            cwd=startup,
            env=bound_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if (completed.returncode != 0
                or "1 proofs run" not in completed.stdout
                or hook_marker.exists()):
            print(
                "FAIL startup Bash was re-resolved after proof cwd changed "
                f"rc={completed.returncode} stdout={completed.stdout!r} "
                f"stderr={completed.stderr!r}",
                file=sys.stderr,
            )
            return 1
        relative_environment = os.environ.copy()
        relative_environment["PATH"] = "."
        relative = subprocess.run(
            [sys.executable, str(VERIFY), str(island)],
            cwd=startup,
            env=relative_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if relative.returncode != 2 or "cannot resolve an executable Bash" not in relative.stderr:
            print(
                "FAIL relative PATH Bash was executed instead of refused "
                f"rc={relative.returncode} stderr={relative.stderr!r}",
                file=sys.stderr,
            )
            return 1
        no_bash = root / "no-bash"
        no_bash.mkdir()
        missing_environment = os.environ.copy()
        missing_environment["PATH"] = str(no_bash)
        for checker in (VERIFY, CLOSED):
            missing = subprocess.run(
                [sys.executable, str(checker), str(island)],
                cwd=startup,
                env=missing_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if missing.returncode != 2 or "cannot resolve an executable Bash" not in missing.stderr:
                print(
                    f"FAIL missing Bash contract checker={checker.name} "
                    f"rc={missing.returncode} stdout={missing.stdout!r} "
                    f"stderr={missing.stderr!r}",
                    file=sys.stderr,
                )
                return 1

    def run_fixed_bash(command, **kwargs):
        """Run a fixed fixture command with the exact probed replay interpreter/environment."""
        return subprocess.run(
            [module.BASH_EXECUTABLE, "-c", command],
            env=module.BASH_REPLAY_ENV,
            **kwargs,
        )

    def run_fixed_sh(command, **kwargs):
        """Run a fixed fixture command with the exact startup-bound sh/environment."""
        return subprocess.run(
            [module.SH_EXECUTABLE, "-c", command],
            env=module.BASH_REPLAY_ENV,
            **kwargs,
        )
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

    provenance_cases = {
        r'''bash '/dev/std?n' ''': ("/dev/std?n", False),
        r'''bash /dev/std\?n ''': ("/dev/std?n", False),
        r'''bash "\\?" ''': (r"\?", False),
        r'''bash "\$SOURCE" ''': ("$SOURCE", False),
        r'''bash "$SOURCE" ''': ("$SOURCE", True),
        r'''bash "$(printf /dev/stdin)" ''': ("$(printf /dev/stdin)", True),
        r'''bash {} ''': ("{}", False),
        r'''bash \{\} ''': ("{}", False),
        r'''bash {X} ''': ("{X}", False),
        r'''bash {{}} ''': ("{{}}", False),
        r'''bash -I{X} ''': ("-I{X}", False),
        r'''bash -I{{}} ''': ("-I{{}}", False),
        r'''bash {a,b} ''': ("{a,b}", True),
        r'''bash {1..2} ''': ("{1..2}", True),
    }
    provenance_observed = {}
    for source in provenance_cases:
        argv = module.shell_segment_argv(source)
        provenance_observed[source] = (
            str(argv[1]) if len(argv) > 1 else None,
            getattr(argv[1], "dynamic", None) if len(argv) > 1 else None,
        )
    if provenance_observed != provenance_cases:
        print(f"FAIL shell word provenance={provenance_observed!r}", file=sys.stderr)
        return 1

    literal_pua = "".join(map(chr, (0xE011, 0xE012, 0xE018, 0xE019)))
    literal_pua_source = "bash -c " + shlex.quote(
        f"true{literal_pua[:2]} {literal_pua[2]} :; {literal_pua[3]}; true"
    )
    pua_argv = module.shell_segment_argv(literal_pua_source)
    if (len(pua_argv) < 3
            or str(pua_argv[2]) != shlex.split(literal_pua_source)[2]
            or module.shell_function_definition(literal_pua_source)):
        print(
            f"FAIL literal private-use data collided with provenance markers={pua_argv!r}",
            file=sys.stderr,
        )
        return 1

    all_private_use = (
        "".join(map(chr, range(0xE000, 0xF900)))
        + "".join(map(chr, range(0xF0000, 0xFFFFE)))
        + "".join(map(chr, range(0x100000, 0x10FFFE)))
    )
    private_use_inner = 'eval "$SOURCE" ' + shlex.quote("#" + all_private_use)
    private_use_source = "bash -c " + shlex.quote(private_use_inner)
    private_use_argv = module.shell_segment_argv(private_use_source)
    if (len(private_use_argv) < 3
            or str(private_use_argv[2]) != private_use_inner
            or not module.shell_function_definition(private_use_source)):
        print(
            "FAIL complete private-use range exhausted or bypassed provenance markers",
            file=sys.stderr,
        )
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

    array_mask_timings = {}
    for repetitions in (8 * 1024, 32 * 1024):
        source = "printf '%s\\n' " + "a[" * repetitions
        started = time.perf_counter()
        masked = module.mask_noncommand_contexts(module.shell_syntax_view(source))
        array_mask_timings[repetitions] = time.perf_counter() - started
        if masked != source:
            print(
                f"FAIL unmatched array-shaped data was changed at {repetitions} repetitions",
                file=sys.stderr,
            )
            return 1
    small = array_mask_timings[8 * 1024]
    large = array_mask_timings[32 * 1024]
    if large > 2.0 or large > max(0.75, small * 8):
        print(
            "FAIL unmatched array-shaped data scan is not bounded "
            f"8K={small:.3f}s 32K={large:.3f}s",
            file=sys.stderr,
        )
        return 1

    array_paren_timings = {}
    for repetitions in (1024, 4096):
        source = "printf '%s\\n' " + "a=(" * repetitions
        started = time.perf_counter()
        masked = module.mask_noncommand_contexts(module.shell_syntax_view(source))
        array_paren_timings[repetitions] = time.perf_counter() - started
        if masked != source:
            print(
                f"FAIL unmatched array parens were changed at {repetitions} repetitions",
                file=sys.stderr,
            )
            return 1
    small = array_paren_timings[1024]
    large = array_paren_timings[4096]
    if large > 1.0 or large > max(0.20, small * 8):
        print(
            "FAIL unmatched array paren scan is not bounded "
            f"1K={small:.3f}s 4K={large:.3f}s",
            file=sys.stderr,
        )
        return 1

    unclosed_context_shapes = {
        "parameter": ("${", 1024, 4096, 0.15),
        "legacy-arithmetic": ("$[", 1024, 4096, 0.15),
        "extglob": ("?(", 8192, 32768, 0.20),
        "arithmetic-command": (";((", 8192, 32768, 0.20),
        "conditional": (";[[", 8192, 32768, 0.15),
        "raw-conditional": ("[[", 8192, 32768, 0.20),
        "word-conditional": ("x[[", 8192, 32768, 0.20),
    }
    for label, (fragment, small_count, large_count, floor) in unclosed_context_shapes.items():
        timings = {}
        for repetitions in (small_count, large_count):
            source = "printf '%s\\n' " + fragment * repetitions
            started = time.perf_counter()
            masked = module.mask_noncommand_contexts(module.shell_syntax_view(source))
            timings[repetitions] = time.perf_counter() - started
            if masked != source:
                print(
                    f"FAIL unmatched {label} data changed at {repetitions} repetitions",
                    file=sys.stderr,
                )
                return 1
        small = timings[small_count]
        large = timings[large_count]
        if large > 1.0 or large > max(floor, small * 8):
            print(
                f"FAIL unmatched {label} scan is not bounded "
                f"small={small:.3f}s large={large:.3f}s",
                file=sys.stderr,
            )
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

    expected_xargs_constants = {
        "short-flags": frozenset("0oprtx"),
        "short-values": frozenset("adEIJLnPRSs"),
        "short-optional-values": frozenset("eil"),
        "long-flags": frozenset({
            "--exit", "--interactive", "--no-run-if-empty", "--null", "--open-tty",
            "--show-limits", "--verbose",
        }),
        "long-values": frozenset({
            "--arg-file", "--delimiter", "--max-args", "--max-chars", "--max-procs",
            "--process-slot-var",
        }),
        "long-optional-values": frozenset({"--eof", "--max-lines", "--replace"}),
        "terminal-options": frozenset({"--help", "--version"}),
        "replacement-flags": frozenset({"I", "J", "i"}),
    }
    observed_xargs_constants = {
        "short-flags": module.XARGS_SHORT_FLAGS,
        "short-values": module.XARGS_SHORT_VALUES,
        "short-optional-values": module.XARGS_SHORT_OPTIONAL_VALUES,
        "long-flags": module.XARGS_LONG_FLAGS,
        "long-values": module.XARGS_LONG_VALUES,
        "long-optional-values": module.XARGS_LONG_OPTIONAL_VALUES,
        "terminal-options": module.XARGS_TERMINAL_OPTIONS,
        "replacement-flags": module.XARGS_REPLACEMENT_FLAGS,
    }
    if observed_xargs_constants != expected_xargs_constants:
        print(
            f"FAIL xargs option constants={observed_xargs_constants!r}",
            file=sys.stderr,
        )
        return 1

    xargs_value_samples = {
        "a": "input", "d": ":", "E": "STOP", "I": "{}", "J": "{}",
        "L": "1", "n": "1", "P": "1", "R": "1", "S": "1", "s": "1",
        "--arg-file": "input", "--delimiter": ":", "--max-args": "1",
        "--max-chars": "1", "--max-procs": "1", "--process-slot-var": "SLOT",
        "e": "STOP", "i": "{}", "l": "1", "--eof": "STOP",
        "--max-lines": "1", "--replace": "{}",
    }
    xargs_option_sources = {
        **{
            f"short-flag-{flag}": f"-{flag}"
            for flag in sorted(expected_xargs_constants["short-flags"])
        },
        "short-flag-cluster": "-0oprtx",
        **{
            f"short-required-joined-{flag}": f"-{flag}{xargs_value_samples[flag]}"
            for flag in sorted(expected_xargs_constants["short-values"])
        },
        **{
            f"short-required-separate-{flag}": f"-{flag} {xargs_value_samples[flag]}"
            for flag in sorted(expected_xargs_constants["short-values"])
        },
        **{
            f"short-optional-bare-{flag}": f"-{flag}"
            for flag in sorted(expected_xargs_constants["short-optional-values"])
        },
        **{
            f"short-optional-joined-{flag}": f"-{flag}{xargs_value_samples[flag]}"
            for flag in sorted(expected_xargs_constants["short-optional-values"])
        },
        **{
            f"long-flag-{option}": option
            for option in sorted(expected_xargs_constants["long-flags"])
        },
        **{
            f"long-required-joined-{option}": f"{option}={xargs_value_samples[option]}"
            for option in sorted(expected_xargs_constants["long-values"])
        },
        **{
            f"long-required-separate-{option}": f"{option} {xargs_value_samples[option]}"
            for option in sorted(expected_xargs_constants["long-values"])
        },
        **{
            f"long-optional-bare-{option}": option
            for option in sorted(expected_xargs_constants["long-optional-values"])
        },
        **{
            f"long-optional-joined-{option}": f"{option}={xargs_value_samples[option]}"
            for option in sorted(expected_xargs_constants["long-optional-values"])
        },
    }
    xargs_option_failures = {}
    for label, option_source in xargs_option_sources.items():
        argv = module.shell_segment_argv(
            f"xargs {option_source} bash -c 'printf safe'"
        )
        child = module.xargs_child_argv(argv)
        if (not child or str(child[0]) != "bash"
                or module.literal_c_operand(child) != "printf safe"):
            xargs_option_failures[label] = (
                [(str(word), getattr(word, "dynamic", False)) for word in argv],
                None if child is None else [
                    (str(word), getattr(word, "dynamic", False)) for word in child
                ],
            )
    if len(xargs_option_sources) != 60 or xargs_option_failures:
        print(
            "FAIL parsed xargs recognized-option matrix "
            f"count={len(xargs_option_sources)} failures={xargs_option_failures!r}",
            file=sys.stderr,
        )
        return 1

    xargs_ambiguous_sources = {
        "unknown-short": "xargs -z bash -c 'printf safe'",
        "unknown-long": "xargs --definitely-unknown bash -c 'printf safe'",
        "joined-long-flag-value": "xargs --verbose=yes bash -c 'printf safe'",
        "joined-terminal-value": "xargs --help=yes bash -c 'printf safe'",
        "missing-short-value": "xargs -n",
        "missing-long-value": "xargs --max-args",
        "empty-short-replacement": "xargs -I '' bash -c 'printf safe'",
        "empty-long-replacement": "xargs --replace= bash -c 'printf safe'",
        "dynamic-option": "xargs \"$OPTIONS\" bash -c 'printf safe'",
        "dynamic-option-value": "xargs -n \"$COUNT\" bash -c 'printf safe'",
        "dynamic-child": "xargs \"$PROGRAM\" -c 'printf safe'",
    }
    xargs_ambiguous_observed = {
        label: module.xargs_child_argv(module.shell_segment_argv(source))
        for label, source in xargs_ambiguous_sources.items()
    }
    if any(child is not None for child in xargs_ambiguous_observed.values()):
        print(
            f"FAIL parsed xargs ambiguous-option matrix={xargs_ambiguous_observed!r}",
            file=sys.stderr,
        )
        return 1
    xargs_terminal_observed = {
        option: module.xargs_child_argv(module.shell_segment_argv(
            f"xargs {option} bash -c 'printf safe'"
        ))
        for option in sorted(expected_xargs_constants["terminal-options"])
    }
    if xargs_terminal_observed != {
            option: [] for option in expected_xargs_constants["terminal-options"]}:
        print(f"FAIL parsed xargs terminal options={xargs_terminal_observed!r}", file=sys.stderr)
        return 1

    xargs_dynamic_shell_values = {
        "enable-shopt": "xargs -I X bash -O X -c 'printf safe'",
        "disable-shopt": "xargs -I X bash +O X -c 'printf safe'",
        "enable-shell-option": "xargs -I X bash -o X -c 'printf safe'",
        "disable-shell-option": "xargs -I X bash +o X -c 'printf safe'",
        "rcfile": "xargs -I X bash --rcfile X -i -c 'printf safe'",
        "init-file": "xargs -I X bash --init-file X -i -c 'printf safe'",
    }
    xargs_dynamic_value_observed = {}
    for label, source in xargs_dynamic_shell_values.items():
        child = module.xargs_child_argv(module.shell_segment_argv(source))
        xargs_dynamic_value_observed[label] = (
            child is None or bool(child and module.shell_reads_stdin_source(child))
        )
    if xargs_dynamic_value_observed != {
            label: True for label in xargs_dynamic_shell_values}:
        print(
            f"FAIL dynamic Bash option values={xargs_dynamic_value_observed!r}",
            file=sys.stderr,
        )
        return 1

    startup_source_commands = {
        "static-rcfile": (
            "bash --rcfile /dev/fd/3 -i -c 'bash -c false' "
            "3<<< 'function bash { return 0; }'"
        ),
        "static-init-file": (
            "bash --init-file /dev/fd/3 -i -c 'bash -c false' "
            "3<<< 'function bash { return 0; }'"
        ),
        "dynamic-rcfile": (
            "bash --rcfile \"$(printf /dev/fd/3)\" -i -c 'bash -c false' "
            "3<<< 'function bash { return 0; }'"
        ),
        "dynamic-init-file": (
            "bash --init-file \"$(printf /dev/fd/3)\" -i -c 'bash -c false' "
            "3<<< 'function bash { return 0; }'"
        ),
        "debugger-profile": "bash --debugger -c 'printf safe'",
        "leading-bash-env": (
            "BASH_ENV=/dev/fd/3 bash -c 'bash -c false' "
            "3<<< 'function bash { return 0; }'"
        ),
        "env-bash-env": (
            "env BASH_ENV=/dev/fd/3 bash -c 'bash -c false' "
            "3<<< 'function bash { return 0; }'"
        ),
        "leading-sh-env": (
            "ENV=/dev/fd/3 sh -i -c 'sh -c false' "
            "3<<< 'sh() { return 0; }'"
        ),
        "env-sh-env": (
            "env ENV=/dev/fd/3 sh -i -c 'sh -c false' "
            "3<<< 'sh() { return 0; }'"
        ),
        "leading-path": "PATH=/proof-verifier-no-such-path bash -c 'printf safe'",
        "env-path": "env PATH=/proof-verifier-no-such-path bash -c 'printf safe'",
        "env-clear-alias": (
            "env - bash -c 'function bash { return 0; }; bash -c false'"
        ),
        "nohup-trailing-help-data": (
            "nohup bash -c 'function bash { return 0; }; bash -c false' --help"
        ),
    }
    startup_source_observed = {
        label: module.shell_function_definition(command)
        for label, command in startup_source_commands.items()
    }
    if startup_source_observed != {
            label: True for label in startup_source_commands}:
        print(
            f"FAIL startup source classification={startup_source_observed!r}",
            file=sys.stderr,
        )
        return 1

    env_option_unsafe = {
        "search-path": "env -P /tmp bash -c 'printf safe'",
        "joined-search-path": "env -P/tmp bash -c 'printf safe'",
        "long-search-path": "env --path /tmp bash -c 'printf safe'",
        "joined-long-search-path": "env --path=/tmp bash -c 'printf safe'",
        "chdir": "env -C /tmp bash -c 'printf safe'",
        "joined-chdir": "env -C/tmp bash -c 'printf safe'",
        "long-chdir": "env --chdir /tmp bash -c 'printf safe'",
        "joined-long-chdir": "env --chdir=/tmp bash -c 'printf safe'",
        "argv0": "env -a custom bash -c 'printf safe'",
        "joined-argv0": "env -acustom bash -c 'printf safe'",
        "long-argv0": "env --argv0 custom bash -c 'printf safe'",
        "joined-long-argv0": "env --argv0=custom bash -c 'printf safe'",
        "split-string": "env -S 'bash -c true'",
        "joined-split-string": "env -Sbash\\ -c\\ true",
        "long-split-string": "env --split-string 'bash -c true'",
        "joined-long-split-string": "env --split-string='bash -c true'",
        "unknown-short": "env -Z bash -c 'printf safe'",
        "unknown-long": "env --unknown bash -c 'printf safe'",
        "dynamic-option": "env \"$OPTION\" bash -c 'printf safe'",
        "missing-unset-value": "env -u",
        "clear-alias-bare-lookup": "env - bash -c 'printf safe'",
        "ignore-environment-bare-lookup": "env -i bash -c 'printf safe'",
        "long-ignore-environment-bare-lookup": (
            "env --ignore-environment bash -c 'printf safe'"
        ),
        "unset-path": "env -u PATH bash -c 'printf safe'",
        "joined-unset-path": "env -uPATH bash -c 'printf safe'",
        "long-unset-path": "env --unset PATH bash -c 'printf safe'",
        "joined-long-unset-path": "env --unset=PATH bash -c 'printf safe'",
        "command-default-path": "command -p bash -c 'printf safe'",
        "exec-custom-argv0": "exec -a sh bash -c 'printf safe'",
    }
    env_option_unsafe_observed = {
        label: module.shell_function_definition(command)
        for label, command in env_option_unsafe.items()
    }
    if env_option_unsafe_observed != {label: True for label in env_option_unsafe}:
        print(
            f"FAIL unsafe env option grammar={env_option_unsafe_observed!r}",
            file=sys.stderr,
        )
        return 1

    env_option_controls = {
        "clear-alias-absolute": (
            "env - " + shlex.quote(module.BASH_EXECUTABLE) + " -c 'printf safe'"
        ),
        "ignore-environment-absolute": (
            "env -i " + shlex.quote(module.BASH_EXECUTABLE) + " -c 'printf safe'"
        ),
        "long-ignore-environment-absolute": (
            "env --ignore-environment " + shlex.quote(module.BASH_EXECUTABLE)
            + " -c 'printf safe'"
        ),
        "verbose": "env -v bash -c 'printf safe'",
        "unset": "env -u BASH_ENV bash -c 'printf safe'",
        "joined-unset": "env -uBASH_ENV bash -c 'printf safe'",
        "long-unset": "env --unset BASH_ENV bash -c 'printf safe'",
        "joined-long-unset": "env --unset=BASH_ENV bash -c 'printf safe'",
        "help": "env --help bash -c 'function bash { return 0; }'",
        "version": "env --version bash -c 'function bash { return 0; }'",
    }
    env_option_control_observed = {
        label: module.shell_function_definition(command)
        for label, command in env_option_controls.items()
    }
    if any(env_option_control_observed.values()):
        print(
            f"FAIL inert env option grammar={env_option_control_observed!r}",
            file=sys.stderr,
        )
        return 1

    env_inert_child_sources = {
        "clear-alias": "env - bash -c 'function bash { return 0; }'",
        "option-terminator": "env -- bash -c 'function bash { return 0; }'",
        "ignore-environment": "env -i bash -c 'function bash { return 0; }'",
        "long-ignore-environment": (
            "env --ignore-environment bash -c 'function bash { return 0; }'"
        ),
        "unset": "env -u BASH_ENV bash -c 'function bash { return 0; }'",
        "joined-unset": "env -uBASH_ENV bash -c 'function bash { return 0; }'",
        "long-unset": "env --unset BASH_ENV bash -c 'function bash { return 0; }'",
        "joined-long-unset": (
            "env --unset=BASH_ENV bash -c 'function bash { return 0; }'"
        ),
    }
    env_inert_child_observed = {
        label: module.shell_function_definition(command)
        for label, command in env_inert_child_sources.items()
    }
    if env_inert_child_observed != {
            label: True for label in env_inert_child_sources}:
        print(
            f"FAIL env inert options hid child source={env_inert_child_observed!r}",
            file=sys.stderr,
        )
        return 1

    nohup_option_cases = {
        "terminal-help": (
            "nohup --help bash -c 'function bash { return 0; }; bash -c false'",
            False,
        ),
        "terminal-version": (
            "nohup --version bash -c 'function bash { return 0; }; bash -c false'",
            False,
        ),
        "trailing-help-data": (
            "nohup bash -c 'function bash { return 0; }; bash -c false' --help",
            True,
        ),
        "terminator-trailing-help-data": (
            "nohup -- bash -c 'function bash { return 0; }; bash -c false' --help",
            True,
        ),
    }
    nohup_option_observed = {
        label: module.shell_function_definition(command)
        for label, (command, _expected) in nohup_option_cases.items()
    }
    nohup_option_expected = {
        label: expected for label, (_command, expected) in nohup_option_cases.items()
    }
    if nohup_option_observed != nohup_option_expected:
        print(f"FAIL nohup option positions={nohup_option_observed!r}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="proof-env-path-") as raw:
        true_path = shutil.which("true")
        if true_path is None:
            print("FAIL true executable is unavailable", file=sys.stderr)
            return 1
        os.symlink(true_path, Path(raw) / "bash")
        env_path_runtime = {
            "search-path": f"env -P {shlex.quote(raw)} bash -c false",
            "chdir": f"env -C {shlex.quote(raw)} ./bash -c false",
        }
        env_path_observed = {
            label: (
                run_fixed_bash(command, capture_output=True, timeout=10).returncode,
                module.shell_function_definition(command),
            )
            for label, command in env_path_runtime.items()
        }
        if env_path_observed != {
                label: (0, True) for label in env_path_runtime}:
            print(f"FAIL env path-context runtime={env_path_observed!r}", file=sys.stderr)
            return 1

    exact_startup_runtime = {
        label: command
        for label, command in startup_source_commands.items()
        if label in {
            "static-rcfile", "static-init-file", "leading-bash-env",
            "env-bash-env", "leading-sh-env", "env-sh-env",
        }
    }
    exact_startup_runtime_observed = {
        label: run_fixed_bash(command, capture_output=True, timeout=10).returncode
        for label, command in exact_startup_runtime.items()
    }
    if exact_startup_runtime_observed != {
            label: 0 for label in exact_startup_runtime}:
        print(
            f"FAIL exact startup source runtime={exact_startup_runtime_observed!r}",
            file=sys.stderr,
        )
        return 1

    startup_source_noexec_controls = {
        "rcfile-noexec": (
            "bash --rcfile /dev/fd/3 -in -c "
            "'function bash { return 0; }; bash -c false' "
            "3<<< 'function bash { return 0; }'"
        ),
        "init-file-dump": (
            "bash --init-file /dev/fd/3 -iD -c "
            "'function bash { return 0; }; bash -c false' "
            "3<<< 'function bash { return 0; }'"
        ),
        "dynamic-rcfile-noexec": (
            "bash --rcfile \"$(printf /dev/fd/3)\" -in -c "
            "'function bash { return 0; }; bash -c false' "
            "3<<< 'function bash { return 0; }'"
        ),
        "dynamic-init-file-dump": (
            "bash --init-file \"$(printf /dev/fd/3)\" -iD -c "
            "'function bash { return 0; }; bash -c false' "
            "3<<< 'function bash { return 0; }'"
        ),
        "debugger-noexec": (
            "bash --debugger -n -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "interactive-norc": (
            "bash --norc -i -c 'printf safe'"
        ),
        "login-noprofile": (
            "bash --noprofile --login -c 'printf safe'"
        ),
        "interactive-login-noprofile": (
            "bash --noprofile -li -c 'printf safe'"
        ),
        "literal-c": "bash -c 'printf safe'",
    }
    startup_noexec_observed = {
        label: module.shell_function_definition(command)
        for label, command in startup_source_noexec_controls.items()
    }
    if any(startup_noexec_observed.values()):
        print(
            f"FAIL inert startup source controls={startup_noexec_observed!r}",
            file=sys.stderr,
        )
        return 1

    with tempfile.TemporaryDirectory(prefix="proof-startup-source-") as raw:
        startup_home = Path(raw)
        (startup_home / ".bashrc").write_text(
            "function bash { return 0; }\n", encoding="utf-8"
        )
        (startup_home / ".bash_profile").write_text(
            "function bash { return 0; }\n", encoding="utf-8"
        )
        startup_runtime_cases = {
            "interactive": (
                f"env HOME={shlex.quote(raw)} bash -i -c 'bash -c false'",
                0,
                True,
            ),
            "login-short": (
                f"env HOME={shlex.quote(raw)} bash -l -c 'bash -c false'",
                0,
                True,
            ),
            "login-long": (
                f"env HOME={shlex.quote(raw)} bash --login -c 'bash -c false'",
                0,
                True,
            ),
            "interactive-norc": (
                f"env HOME={shlex.quote(raw)} bash --norc -i -c 'bash -c false'",
                1,
                False,
            ),
            "login-noprofile": (
                f"env HOME={shlex.quote(raw)} bash --noprofile -l -c 'bash -c false'",
                1,
                False,
            ),
        }
        startup_runtime_observed = {}
        for label, (command, expected_rc, expected_unsafe) in startup_runtime_cases.items():
            completed = run_fixed_bash(command, capture_output=True, timeout=10)
            startup_runtime_observed[label] = (
                completed.returncode,
                module.shell_function_definition(command),
            )
        startup_runtime_expected = {
            label: (expected_rc, expected_unsafe)
            for label, (_command, expected_rc, expected_unsafe) in startup_runtime_cases.items()
        }
        if startup_runtime_observed != startup_runtime_expected:
            print(
                f"FAIL startup source runtime matrix={startup_runtime_observed!r}",
                file=sys.stderr,
            )
            return 1

    xargs_shell_commands = {
        "no-options": (
            "printf x | xargs bash -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "option-terminator": (
            "printf x | xargs -- bash -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "joined-max-args": (
            "printf x | xargs -n1 bash -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "separate-max-args": (
            "printf x | xargs -n 1 bash -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "joined-replacement": (
            "printf x | xargs -I{} bash -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "separate-bsd-replacement": (
            "printf x | xargs -J {} bash -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "nul-separator": (
            "printf x | xargs -0 bash -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "separate-gnu-delimiter": (
            "printf x | xargs -d x bash -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "replacement-built-source": (
            "printf '%s\\n' 'function bash { return 0; }; bash -c false' "
            "| xargs -I{} bash -c '{}'"
        ),
        "protected-dot-delimiter-exposes-replacement-source": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 -I{a'.'.c}{x,y} bash -c '{a..c}y'"
        ),
        "escaped-dot-delimiter-exposes-replacement-source": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 -I{a\\.\\.c}{x,y} bash -c '{a..c}y'"
        ),
        "nested-comma-exposes-replacement-source": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 -I{foo..{x,y}} bash -c 'foo..y'"
        ),
        "bsd-j-replacement-built-source": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 -J % bash -c %"
        ),
        "appended-c-operand": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -c"
        ),
        "appended-combined-cap-o-c-operand": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -Oc extglob"
        ),
        "appended-combined-c-cap-o-operand": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -cO extglob"
        ),
        "appended-combined-lower-o-c-operand": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -oc posix"
        ),
        "appended-combined-c-lower-o-operand": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -co posix"
        ),
        "appended-combined-plus-cap-o-c-operand": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash +Oc extglob"
        ),
        "appended-cap-o-option-tail": (
            "printf '%s\\0' extglob +n -c "
            "'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -n -O"
        ),
        "appended-lower-o-option-tail": (
            "printf '%s\\0' posix +n -c "
            "'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -n -o"
        ),
        "appended-rcfile-option-tail": (
            "printf '%s\\0' /dev/null -n +n -c "
            "'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash --rcfile"
        ),
        "appended-init-file-option-tail": (
            "printf '%s\\0' /dev/null -n +n -c "
            "'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash --init-file"
        ),
        "appended-noexec-toggle": (
            "printf '%s\\0' +n -c "
            "'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -n"
        ),
        "replacement-built-c-option": (
            "printf c | xargs -I X bash -X "
            "'function bash { return 0; }; bash -c false'"
        ),
        "replacement-built-rcfile-value": (
            "printf /dev/fd/3 | xargs -I X bash --rcfile X -i -c "
            "'bash -c false' 3<<< 'function bash { return 0; }'"
        ),
        "replacement-built-init-file-value": (
            "printf /dev/fd/3 | xargs -I X bash --init-file X -i -c "
            "'bash -c false' 3<<< 'function bash { return 0; }'"
        ),
        "static-rcfile-startup-source": (
            "printf ignored | xargs bash --rcfile /dev/fd/3 -i -c "
            "'bash -c false' 3<<< 'function bash { return 0; }'"
        ),
        "static-init-file-startup-source": (
            "printf ignored | xargs bash --init-file /dev/fd/3 -i -c "
            "'bash -c false' 3<<< 'function bash { return 0; }'"
        ),
        "appended-wrapper-executable": (
            "printf '%s\\0' bash -c "
            "'function bash { return 0; }; bash -c false' | xargs -0 env"
        ),
        "unmodeled-child-wrapper": (
            "printf x | xargs timeout 1 bash -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "appended-child-wrapper-argv": (
            "printf '%s\\0' 1 bash -c "
            "'function bash { return 0; }; bash -c false' | xargs -0 timeout"
        ),
        "split-string-child-wrapper": (
            "printf x | xargs env -S \"timeout 1 bash -c "
            "'function bash { return 0; }; bash -c false'\""
        ),
        "nohup-trailing-terminal-data": (
            "printf x | xargs nohup bash -c "
            "'function bash { return 0; }; bash -c false' --help"
        ),
        "appended-env-option-value": (
            "printf '%s\\0' FOO bash -c "
            "'function bash { return 0; }; bash -c false' | xargs -0 env -u"
        ),
        "appended-nice-option-value": (
            "printf '%s\\0' 1 bash -c "
            "'function bash { return 0; }; bash -c false' | xargs -0 nice -n"
        ),
        "appended-stdbuf-option-value": (
            "printf '%s\\0' 0 bash -c "
            "'function bash { return 0; }; bash -c false' | xargs -0 stdbuf -o"
        ),
        "replacement-built-env-assignment": (
            "printf /dev/fd/3 | xargs -I X env BASH_ENV=X bash -c "
            "'bash -c false' 3<<< 'function bash { return 0; }'"
        ),
        "static-env-startup-source": (
            "printf x | xargs env BASH_ENV=/dev/fd/3 bash -c "
            "'bash -c false' 3<<< 'function bash { return 0; }'"
        ),
        "static-env-wrapper": (
            "printf x | xargs env printf '%s\\n' ordinary-data"
        ),
        "gnu-env-short-argv0-wrapper": (
            "printf x | xargs env -a custom printf '%s\\n' ordinary-data"
        ),
        "gnu-env-long-argv0-wrapper": (
            "printf x | xargs env --argv0 custom printf '%s\\n' ordinary-data"
        ),
        "gnu-env-ignore-alias-wrapper": (
            "printf x | xargs env - printf '%s\\n' ordinary-data"
        ),
        "ordinary-env-assignment-wrapper": (
            "printf x | xargs env ORDINARY=value printf '%s\\n' ordinary-data"
        ),
        "unknown-option-fails-closed": (
            "printf x | xargs --definitely-unknown echo ordinary-data"
        ),
    }
    xargs_shell_observed = {}
    for label, command in xargs_shell_commands.items():
        rows = list(module.commands(
            command + " # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ))
        xargs_shell_observed[label] = (
            rows[0][1] if rows else None,
            rows[-1][3] if rows else None,
        )
    xargs_shell_expected = {
        label: ("__REFUSE__", frozenset({"refused"}))
        for label in xargs_shell_commands
    }
    if xargs_shell_observed != xargs_shell_expected:
        print(
            f"FAIL xargs child shell classification={xargs_shell_observed!r}",
            file=sys.stderr,
        )
        return 1

    # Brace expansion runs before quote removal. Preserve whether the comma, dots, endpoints,
    # and optional increment were quoted/escaped: their resolved bytes can be identical while
    # only the fully unquoted spelling expands. The fixed startup probe binds malformed-candidate
    # continuation and increment support to the same Bash that will execute proofs.
    legacy_braces = module.BASH_BRACE_MODE == "legacy"
    validated_braces = module.BASH_BRACE_MODE == "validated"
    brace_word_cases = {
        "active-comma": ("printf '%s\\n' {a,b}", "{a,b}", True),
        "quoted-comma": ("printf '%s\\n' {a\",\"b}", "{a,b}", False),
        "escaped-comma": ("printf '%s\\n' {a\\,b}", "{a,b}", False),
        "empty-range": ("printf '%s\\n' {..}", "{..}", False),
        "missing-range-end": ("printf '%s\\n' {a..}", "{a..}", False),
        "multi-character-range": (
            "printf '%s\\n' {foo..bar}", "{foo..bar}", False
        ),
        "active-letter-range": ("printf '%s\\n' {a..z}", "{a..z}", True),
        "active-integer-range": ("printf '%s\\n' {-1..+3}", "{-1..+3}", True),
        "active-range-increment": (
            "printf '%s\\n' {1..9..2}",
            "{1..9..2}",
            module.BASH_BRACE_INCREMENT,
        ),
        "quoted-range-end": ("printf '%s\\n' {1..'3'}", "{1..3}", False),
        "escaped-range-end": ("printf '%s\\n' {\\a..c}", "{a..c}", False),
        "quoted-range-dot": ("printf '%s\\n' {a.'.'.c}", "{a...c}", False),
        "empty-single-quote-in-range": (
            "printf '%s\\n' {a''..z}", "{a..z}", False
        ),
        "empty-double-quote-in-range": (
            "printf '%s\\n' {a..\"\"z}", "{a..z}", False
        ),
        "empty-quote-after-range": (
            "printf '%s\\n' {a..z}''", "{a..z}", True
        ),
        "non-ascii-digit-range": (
            "printf '%s\\n' {١..٣}", "{١..٣}", False
        ),
        "quoted-range-blocks-adjacent-range": (
            "printf '%s\\n' {a''..c}{1..3}",
            "{a..c}{1..3}",
            not legacy_braces,
        ),
        "escaped-range-blocks-adjacent-range": (
            "printf '%s\\n' {a..\\c}{1..3}",
            "{a..c}{1..3}",
            not legacy_braces,
        ),
        "nested-quoted-range-blocks-adjacent-range": (
            "printf '%s\\n' {{a''..c}{1..3}}",
            "{{a..c}{1..3}}",
            not legacy_braces,
        ),
        "protected-dot-delimiter-allows-adjacent-range": (
            "printf '%s\\n' {a'.'.c}{1..3}", "{a..c}{1..3}", True
        ),
        "escaped-dot-delimiter-allows-adjacent-range": (
            "printf '%s\\n' {a\\.\\.c}{1..3}", "{a..c}{1..3}", True
        ),
        "malformed-range-precedes-adjacent-range": (
            "printf '%s\\n' {foo..bar}{1..3}",
            "{foo..bar}{1..3}",
            not legacy_braces,
        ),
        "non-ascii-range-precedes-adjacent-range": (
            "printf '%s\\n' {١..٣}{1..3}",
            "{١..٣}{1..3}",
            not legacy_braces,
        ),
        "malformed-outer-precedes-nested-range": (
            "printf '%s\\n' {foo..{1..3}}",
            "{foo..{1..3}}",
            validated_braces,
        ),
        "missing-range-end-allows-adjacent-comma": (
            "printf '%s\\n' {a..}{x,y}", "{a..}{x,y}", True
        ),
        "missing-range-start-blocks-adjacent-comma": (
            "printf '%s\\n' {..c}{x,y}",
            "{..c}{x,y}",
            not legacy_braces,
        ),
        "nested-comma-outranks-malformed-outer-range": (
            "printf '%s\\n' {foo..{x,y}}", "{foo..{x,y}}", True
        ),
        "quoted-nested-comma-after-selected-range": (
            "printf '%s\\n' {foo..{x','y}}",
            "{foo..{x,y}}",
            module.BASH_BRACE_MODE != "validated",
        ),
        "escaped-nested-comma-remains-inert": (
            "printf '%s\\n' {foo..{x\\,y}}", "{foo..{x,y}}", False
        ),
        "quoted-nonrange-allows-adjacent-comma": (
            "printf '%s\\n' {a''b}{x,y}", "{ab}{x,y}", True
        ),
        "outer-comma-precedes-blocked-branch": (
            "printf '%s\\n' {x,{a''..c}{1..3}}",
            "{x,{a..c}{1..3}}",
            True,
        ),
        "earlier-comma-precedes-blocked-range": (
            "printf '%s\\n' {a,b}{a''..c}{1..3}",
            "{a,b}{a..c}{1..3}",
            True,
        ),
    }
    brace_word_observed = {}
    for label, (source, expected_word, expected_dynamic) in brace_word_cases.items():
        argv = module.shell_segment_argv(source)
        observed = None
        if argv:
            observed = (str(argv[-1]), getattr(argv[-1], "dynamic", None))
        expected = (expected_word, expected_dynamic)
        if observed != expected:
            brace_word_observed[label] = {
                "observed": observed,
                "expected": expected,
            }
    if brace_word_observed:
        print(f"FAIL brace provenance={brace_word_observed!r}", file=sys.stderr)
        return 1

    # Exercise every profiled continuation branch even when the host supplies only one Bash
    # release. This is a pure parser matrix; the live differential below separately binds the
    # selected branch to the interpreter that will execute proofs.
    original_brace_profile = (
        module.BASH_BRACE_MODE,
        module.BASH_BRACE_INCREMENT,
    )
    profile_cases = {
        "malformed-adjacent": "{foo..bar}{1..2}",
        "malformed-nested": "{foo..{1..2}}",
        "protected-delimiter": "{a'.'.c}{1..2}",
        "protected-endpoint": "{a''..c}{1..2}",
        "missing-end": "{a..}{x,y}",
        "missing-start": "{..c}{x,y}",
        "increment": "{1..3..2}",
        "outer-comma": "{x,{foo..bar}{1..2}}",
        "nested-comma": "{foo..{x,y}}",
        "quoted-nested-comma": "{foo..{x','y}}",
        "escaped-nested-comma": r"{foo..{x\,y}}",
    }
    profile_expectations = {
        ("legacy", False): (
            False, False, True, False, True, False, False, True, True, True, False,
        ),
        ("legacy", True): (
            False, False, True, False, True, False, True, True, True, True, False,
        ),
        ("postamble", True): (
            True, False, True, True, True, True, True, True, True, True, False,
        ),
        ("validated", True): (
            True, True, True, True, True, True, True, True, True, False, False,
        ),
        ("unknown", True): (
            True, True, True, True, True, True, True, True, True, True, False,
        ),
        ("disabled", False): (
            False, False, False, False, False, False, False, False, False, False, False,
        ),
    }
    profile_mismatches = {}
    try:
        for profile, expected_values in profile_expectations.items():
            module.BASH_BRACE_MODE, module.BASH_BRACE_INCREMENT = profile
            observed_values = []
            for word_source in profile_cases.values():
                argv = module.shell_segment_argv("printf '%s\\n' " + word_source)
                observed_values.append(
                    getattr(argv[-1], "dynamic", None) if argv else None
                )
            if tuple(observed_values) != expected_values:
                profile_mismatches[profile] = {
                    "observed": tuple(observed_values),
                    "expected": expected_values,
                }
    finally:
        module.BASH_BRACE_MODE, module.BASH_BRACE_INCREMENT = original_brace_profile
    if profile_mismatches:
        print(f"FAIL brace profile matrix={profile_mismatches!r}", file=sys.stderr)
        return 1

    # The classifier is a security boundary, so compare it directly with the measured Bash
    # rather than proving only hand-maintained expectations. These are fixed fixture words, not
    # repository-supplied source; no untrusted text is evaluated by the differential test.
    brace_runtime_words = (
        "{a,b}",
        "{a\",\"b}",
        r"{a\,b}",
        "{1..3}",
        "{1..3..2}",
        "{foo..bar}{1..3}",
        "{١..٣}{1..3}",
        "{foo..{1..3}}",
        "{a'.'.c}{1..3}",
        r"{a\.\.c}{1..3}",
        "{a''..c}{1..3}",
        r"{a..\c}{1..3}",
        "{a..}{x,y}",
        "{..c}{x,y}",
        "{...}{x,y}",
        "{foo..bar}{x,y}",
        "{x,{foo..bar}{1..3}}",
        "{foo..{x,y}}",
        "{foo..{x','y}}",
        r"{foo..{x\,y}}",
    )
    brace_runtime_mismatches = {}
    for word_source in brace_runtime_words:
        argv = module.shell_segment_argv("printf '%s\\n' " + word_source)
        resolved = str(argv[-1]) if argv else None
        predicted = getattr(argv[-1], "dynamic", None) if argv else None
        completed = run_fixed_bash(
            "printf '%s\\0' " + word_source,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        values = completed.stdout.split(b"\0")
        if values and values[-1] == b"":
            values.pop()
        try:
            decoded = [value.decode("utf-8") for value in values]
        except UnicodeDecodeError:
            decoded = []
        actual = completed.returncode == 0 and decoded != [resolved]
        if completed.returncode != 0 or predicted != actual:
            brace_runtime_mismatches[word_source] = {
                "profile": (
                    module.BASH_BRACE_MODE,
                    module.BASH_BRACE_INCREMENT,
                ),
                "resolved": resolved,
                "predicted": predicted,
                "actual": actual,
                "values": decoded,
                "stderr": completed.stderr.decode("utf-8", "replace"),
            }
    if brace_runtime_mismatches:
        print(
            f"FAIL actual Bash/brace equivalence={brace_runtime_mismatches!r}",
            file=sys.stderr,
        )
        return 1

    xargs_data_controls = {
        "no-options": (
            "printf x | xargs printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'"
        ),
        "known-option": (
            "printf x | xargs -n1 printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'"
        ),
        "empty-eof-marker": (
            "printf x | xargs -E '' printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'"
        ),
        "dirname-leaf": (
            "printf x | xargs -n1 dirname"
        ),
        "replacement-printf-leaf": (
            "printf x | xargs -I{} printf '%s\\n' '{}'"
        ),
        "literal-shell-source": (
            "printf ignored | xargs bash -c 'printf safe >/dev/null'"
        ),
        "noexec-n-shell-source": (
            "printf ignored | xargs bash -n -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "noexec-dump-shell-source": (
            "printf ignored | xargs bash -D -c "
            "'function bash { return 0; }; bash -c false'"
        ),
        "combined-noexec-shell-source": (
            "printf ignored | xargs bash -nc "
            "'function bash { return 0; }; bash -c false'"
        ),
        "literal-braced-replacement-marker": (
            "printf x | xargs -I{X} printf '%s\\n' 'pre{X}suf'"
        ),
        "literal-nested-braced-replacement-marker": (
            "printf x | xargs -I{{}} printf '%s\\n' 'pre{{}}suf'"
        ),
        "quoted-comma-replacement-marker": (
            "printf x | xargs -I{a\",\"b} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'"
        ),
        "escaped-comma-replacement-marker": (
            "printf x | xargs -I{a\\,b} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'"
        ),
        "malformed-range-replacement-marker": (
            "printf x | xargs -I{foo..bar} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'"
        ),
        "empty-quote-range-replacement-marker": (
            "printf x | xargs -I{a''..z} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'"
        ),
        "non-ascii-range-replacement-marker": (
            "printf x | xargs -I{١..٣} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'"
        ),
        "quoted-range-adjacent-comma-replacement-marker": (
            "printf x | xargs -I{a''..c}{x,y} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'"
        ),
        "bsd-j-substring-is-data": (
            "printf x | xargs -J % printf '%s\\n' 'pre%suf'"
        ),
        "bsd-j-missing-distinct-marker-appends": (
            "printf x | xargs -J % bash -c 'printf %s harmless >/dev/null'"
        ),
        "terminal-help-option": (
            "xargs --help bash -c 'function bash { return 0; }; bash -c false'"
        ),
    }
    xargs_data_observed = {}
    for label, command in xargs_data_controls.items():
        rows = list(module.commands(command + " # exit 0\n"))
        xargs_data_observed[label] = (
            rows[0][1] if rows else None,
            rows[0][3] if rows else None,
        )
    xargs_data_expected = {
        label: (0, frozenset()) for label in xargs_data_controls
    }
    if not legacy_braces:
        xargs_data_expected["quoted-range-adjacent-comma-replacement-marker"] = (
            "__REFUSE__",
            frozenset(),
        )
    if xargs_data_observed != xargs_data_expected:
        print(f"FAIL xargs function-shaped data={xargs_data_observed!r}", file=sys.stderr)
        return 1

    profiled_xargs_command = xargs_data_controls[
        "quoted-range-adjacent-comma-replacement-marker"
    ]
    profiled_xargs_mismatches = {}
    original_brace_profile = (
        module.BASH_BRACE_MODE,
        module.BASH_BRACE_INCREMENT,
    )
    try:
        for mode, expected_refusal in (
                ("legacy", False),
                ("postamble", True),
                ("validated", True),
                ("unknown", True)):
            module.BASH_BRACE_MODE = mode
            module.BASH_BRACE_INCREMENT = mode != "legacy"
            rows = list(module.commands(profiled_xargs_command + " # exit 0\n"))
            observed_refusal = bool(rows and rows[0][1] == module.REFUSE)
            if observed_refusal != expected_refusal:
                profiled_xargs_mismatches[mode] = {
                    "observed": observed_refusal,
                    "expected": expected_refusal,
                }
    finally:
        module.BASH_BRACE_MODE, module.BASH_BRACE_INCREMENT = original_brace_profile
    if profiled_xargs_mismatches:
        print(
            f"FAIL profiled xargs brace layer={profiled_xargs_mismatches!r}",
            file=sys.stderr,
        )
        return 1

    alternate_child_source = (
        "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
        "| xargs -0 -I{foo..bar}{x,y} bash -c '{foo..bar}y'"
    )
    if not module.shell_function_definition(
            "/alternate/bash -c " + shlex.quote(alternate_child_source)):
        print(
            "FAIL alternate child Bash was parsed under the outer host profile",
            file=sys.stderr,
        )
        return 1
    if module.shell_function_definition(
            "/alternate/bash -c " + shlex.quote("printf '%s' {foo..bar}")):
        print(
            "FAIL conservative child profile refused isolated malformed brace data",
            file=sys.stderr,
        )
        return 1

    # Bare child Bash and sh each use their independently measured startup profile. Neither
    # borrows an unrelated parent's profile; only an alternate absolute shell keeps the
    # conservative union.
    child_profile_mismatches = {}
    original_brace_profile = (
        module.BASH_BRACE_MODE,
        module.BASH_BRACE_INCREMENT,
        module.SH_BRACE_MODE,
        module.SH_BRACE_INCREMENT,
    )
    try:
        for mode, expected in (
                ("legacy", False),
                ("postamble", True),
                ("validated", True),
                ("unknown", True)):
            module.BASH_BRACE_MODE = mode
            module.BASH_BRACE_INCREMENT = mode != "legacy"
            module.SH_BRACE_MODE = mode
            module.SH_BRACE_INCREMENT = mode != "legacy"
            for child in ("bash", "sh"):
                command = child + " -c " + shlex.quote(alternate_child_source)
                observed = module.shell_function_definition(command)
                if observed != expected:
                    child_profile_mismatches[(mode, child)] = {
                        "observed": observed,
                        "expected": expected,
                    }
    finally:
        (
            module.BASH_BRACE_MODE,
            module.BASH_BRACE_INCREMENT,
            module.SH_BRACE_MODE,
            module.SH_BRACE_INCREMENT,
        ) = original_brace_profile
    if child_profile_mismatches:
        print(
            f"FAIL literal child shell profiles={child_profile_mismatches!r}",
            file=sys.stderr,
        )
        return 1

    # A relative spelling that contains a slash bypasses PATH. It cannot inherit the measured
    # bare-name profile even when its basename is bash or sh; a different release may live at
    # that path. Exact absolute identity is textual on purpose: normalizing ``alias/../bash``
    # before the OS resolves a symlink named alias can equate two different executables. Keep
    # those spellings conservative while an unqualified or byte-exact bound path remains precise.
    relative_child_mismatches = {}
    original_brace_profile = (
        module.BASH_BRACE_MODE,
        module.BASH_BRACE_INCREMENT,
        module.SH_BRACE_MODE,
        module.SH_BRACE_INCREMENT,
    )
    try:
        module.BASH_BRACE_MODE, module.BASH_BRACE_INCREMENT = "legacy", False
        module.SH_BRACE_MODE, module.SH_BRACE_INCREMENT = "legacy", False
        child_identity_cases = {
            "bare-bash": ("bash", False),
            "bare-sh": ("sh", False),
            "exact-bash": (module.BASH_EXECUTABLE, False),
            "exact-sh": (module.SH_EXECUTABLE, False),
            "dot-bash": ("./bash", True),
            "dot-sh": ("./sh", True),
            "subdir-bash": ("subdir/bash", True),
            "parent-sh": ("../other/sh", True),
            "symlink-sensitive-absolute-bash": (
                str(Path(module.BASH_EXECUTABLE).parent / "alias" / ".." / "bash"),
                True,
            ),
            "symlink-sensitive-absolute-sh": (
                str(Path(module.SH_EXECUTABLE).parent / "alias" / ".." / "sh"),
                True,
            ),
        }
        for label, (child, expected) in child_identity_cases.items():
            command = child + " -c " + shlex.quote(alternate_child_source)
            observed = module.shell_function_definition(command)
            if observed != expected:
                relative_child_mismatches[label] = {
                    "observed": observed,
                    "expected": expected,
                }
    finally:
        (
            module.BASH_BRACE_MODE,
            module.BASH_BRACE_INCREMENT,
            module.SH_BRACE_MODE,
            module.SH_BRACE_INCREMENT,
        ) = original_brace_profile
    if relative_child_mismatches:
        print(
            f"FAIL relative child shell profiles={relative_child_mismatches!r}",
            file=sys.stderr,
        )
        return 1

    # Real sh replay must match the profile selected at import. In particular, Bash invoked as
    # sh still performs brace expansion; assuming otherwise converts a replacement-built child
    # source into a false clean. A shell that genuinely leaves braces inert is measured as the
    # explicit disabled profile instead.
    sh_runtime_cases = {
        "ordinary-comma": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 -I{x,y} bash -c 'y'"
        ),
        "malformed-adjacent": alternate_child_source,
    }
    sh_runtime_mismatches = {}
    for label, command in sh_runtime_cases.items():
        completed = run_fixed_sh(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        observed = (completed.returncode, module.shell_function_definition(
            "sh -c " + shlex.quote(command)
        ))
        expected = (
            (1, False) if module.SH_BRACE_MODE == "disabled" else (0, True)
        ) if label == "ordinary-comma" else (
            (1, False) if module.SH_BRACE_MODE in {"disabled", "legacy"} else (0, True)
        )
        if observed != expected:
            sh_runtime_mismatches[label] = {
                "profile": (module.SH_BRACE_MODE, module.SH_BRACE_INCREMENT),
                "observed": observed,
                "expected": expected,
                "stderr": completed.stderr,
            }
    if sh_runtime_mismatches:
        print(
            f"FAIL actual sh/xargs equivalence={sh_runtime_mismatches!r}",
            file=sys.stderr,
        )
        return 1

    # Exercise real Bash and xargs argv construction for the boundary cases above. The option
    # table checks establish our accepted grammar; these replays independently prove where Bash
    # takes its command string and whether the parser refuses only actually executable source.
    xargs_runtime_cases = {
        "combined-cap-o-c": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -Oc extglob",
            0,
            True,
        ),
        "combined-c-cap-o": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -cO extglob",
            0,
            True,
        ),
        "combined-lower-o-c": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -oc posix",
            0,
            True,
        ),
        "combined-c-lower-o": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 bash -co posix",
            0,
            True,
        ),
        "noexec-n": (
            "printf ignored | xargs bash -n -c "
            "'function bash { return 0; }; bash -c false'",
            0,
            False,
        ),
        "noexec-dump": (
            "printf ignored | xargs bash -D -c "
            "'function bash { return 0; }; bash -c false'",
            0,
            False,
        ),
        "literal-braced-marker": (
            "printf x | xargs -I{X} printf '%s\\n' 'pre{X}suf'",
            0,
            False,
        ),
        "literal-nested-braced-marker": (
            "printf x | xargs -I{{}} printf '%s\\n' 'pre{{}}suf'",
            0,
            False,
        ),
        "quoted-comma-braced-marker": (
            "printf x | xargs -I{a\",\"b} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'",
            0,
            False,
        ),
        "escaped-comma-braced-marker": (
            "printf x | xargs -I{a\\,b} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'",
            0,
            False,
        ),
        "malformed-range-braced-marker": (
            "printf x | xargs -I{foo..bar} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'",
            0,
            False,
        ),
        "empty-quote-range-braced-marker": (
            "printf x | xargs -I{a''..z} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'",
            0,
            False,
        ),
        "non-ascii-range-braced-marker": (
            "printf x | xargs -I{١..٣} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'",
            0,
            False,
        ),
        "quoted-range-adjacent-comma-braced-marker": (
            "printf x | xargs -I{a''..c}{x,y} printf '%s\\n' "
            "'function bash { return 0; }; bash -c false'",
            0,
            False,
        ),
        "protected-dot-delimiter-exposes-braced-marker": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 -I{a'.'.c}{x,y} bash -c '{a..c}y'",
            0,
            True,
        ),
        "escaped-dot-delimiter-exposes-braced-marker": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 -I{a\\.\\.c}{x,y} bash -c '{a..c}y'",
            0,
            True,
        ),
        "nested-comma-exposes-braced-marker": (
            "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
            "| xargs -0 -I{foo..{x,y}} bash -c 'foo..y'",
            1 if module.BASH_BRACE_MODE == "validated" else 0,
            True,
        ),
    }
    xargs_runtime_cases["quoted-range-adjacent-comma-braced-marker"] = (
        xargs_runtime_cases["quoted-range-adjacent-comma-braced-marker"][0],
        0,
        not legacy_braces,
    )
    xargs_runtime_observed = {}
    for label, (command, expected_rc, expected_refusal) in xargs_runtime_cases.items():
        completed = run_fixed_bash(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        observed = (completed.returncode, module.shell_function_definition(command))
        expected = (expected_rc, expected_refusal)
        if observed != expected:
            xargs_runtime_observed[label] = {
                "observed": observed,
                "expected": expected,
                "stderr": completed.stderr,
            }

    j_probe = subprocess.run(
        ["xargs", "-J", "%", "printf", "%"],
        input="probe\n",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if j_probe.returncode == 0 and j_probe.stdout == "probe":
        bsd_j_cases = {
            "missing-distinct-marker": (
                "printf x | xargs -J % bash -c "
                "'printf %s harmless >/dev/null'",
                False,
            ),
            "exact-dynamic-source": (
                "printf '%s\\0' 'function bash { return 0; }; bash -c false' "
                "| xargs -0 -J % bash -c %",
                True,
            ),
        }
        for label, (command, expected_refusal) in bsd_j_cases.items():
            completed = run_fixed_bash(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            observed = (completed.returncode, module.shell_function_definition(command))
            expected = (0, expected_refusal)
            if observed != expected:
                xargs_runtime_observed[f"bsd-j-{label}"] = {
                    "observed": observed,
                    "expected": expected,
                    "stderr": completed.stderr,
                }
    if xargs_runtime_observed:
        print(
            f"FAIL actual Bash/xargs equivalence={xargs_runtime_observed!r}",
            file=sys.stderr,
        )
        return 1
    unsafe_setup_blocks = {
        "static-rcfile-startup-source": (
            "bash --rcfile /dev/fd/3 -i -c 'bash -c false' "
            "3<<< 'function bash { return 0; }' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "static-init-file-startup-source": (
            "bash --init-file /dev/fd/3 -i -c 'bash -c false' "
            "3<<< 'function bash { return 0; }' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "dynamic-rcfile-startup-source": (
            "bash --rcfile \"$(printf /dev/fd/3)\" -i -c 'bash -c false' "
            "3<<< 'function bash { return 0; }' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "dynamic-init-file-startup-source": (
            "bash --init-file \"$(printf /dev/fd/3)\" -i -c 'bash -c false' "
            "3<<< 'function bash { return 0; }' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "interactive-startup-source": (
            "bash -i -c 'printf safe' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "login-short-startup-source": (
            "bash -l -c 'printf safe' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "login-long-startup-source": (
            "bash --login -c 'printf safe' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "debugger-startup-source": (
            "bash --debugger -c 'printf safe' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "leading-bash-env-startup-source": (
            "BASH_ENV=/dev/fd/3 bash -c 'bash -c false' "
            "3<<< 'function bash { return 0; }' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "env-bash-env-startup-source": (
            "env BASH_ENV=/dev/fd/3 bash -c 'bash -c false' "
            "3<<< 'function bash { return 0; }' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "leading-sh-env-startup-source": (
            "ENV=/dev/fd/3 sh -i -c 'sh -c false' "
            "3<<< 'sh() { return 0; }' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "env-sh-env-startup-source": (
            "env ENV=/dev/fd/3 sh -i -c 'sh -c false' "
            "3<<< 'sh() { return 0; }' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "leading-path-command-lookup": (
            "PATH=/proof-verifier-no-such-path bash -c 'printf safe' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "env-path-command-lookup": (
            "env PATH=/proof-verifier-no-such-path bash -c 'printf safe' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "env-clear-alias-shell-source": (
            "env - bash -c 'function bash { return 0; }; bash -c false' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "env-search-path-context": (
            "env -P /tmp bash -c 'printf safe' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "env-chdir-context": (
            "env -C /tmp bash -c 'printf safe' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "nohup-trailing-help-data": (
            "nohup bash -c 'function bash { return 0; }; bash -c false' --help "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
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
        "function-keyword-unannotated": (
            'function python3 { return 7; }\n'
            'python3 -c "raise SystemExit(7)" # exit 7\n'
        ),
        "function-keyword-annotated": (
            'function python3 { return 0; } # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-annotated-compound": (
            'printf x >/dev/null; function python3 { return 0; }; '
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-parenthesized": (
            'printf x >/dev/null; function python3 () { return 0; }; '
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-conditional": (
            'printf x >/dev/null; if true; then function python3 { return 0; }; fi; '
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-case-branch": (
            'printf x >/dev/null; case x in x) function python3 { return 0; };; esac; '
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-negated": (
            'printf x >/dev/null; ! function python3 { return 0; }; '
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-timed": (
            'printf x >/dev/null; time function python3 { return 0; }; '
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-posix-timed": (
            'printf x >/dev/null; time -p function python3 { return 0; }; '
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-if-condition": (
            'printf x >/dev/null; if function python3 { return 0; }; then '
            'python3 -c "raise SystemExit(1)"; fi # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-elif-condition": (
            'printf x >/dev/null; if false; then :; elif function python3 { return 0; }; '
            'then python3 -c "raise SystemExit(1)"; fi # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-while-condition": (
            'printf x >/dev/null; while function python3 { return 0; }; do break; done; '
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-until-condition": (
            'printf x >/dev/null; until function python3 { return 0; }; do :; done; '
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-classic-tight-subshell": (
            'printf x >/dev/null; (python3 () { return 0; }; '
            'python3 -c "raise SystemExit(1)") # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-classic-tight-case": (
            'printf x >/dev/null; case x in x)python3 () { return 0; }; '
            'python3 -c "raise SystemExit(1)";; esac # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-quoted-name": (
            "printf x >/dev/null; function 'python3' { return 0; }; "
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-command-substitution": (
            'printf x >/dev/null; X=$(function python3 { return 0; }; '
            'python3 -c "raise SystemExit(1)") # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-classic-command-substitution": (
            'printf x >/dev/null; X=$(python3 () { return 0; }; '
            'python3 -c "raise SystemExit(1)") # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-backtick-substitution": (
            'printf x >/dev/null; X=`function python3 { return 0; }; '
            'python3 -c "raise SystemExit(1)"` # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-nested-substitution": (
            'printf x >/dev/null; X=$(printf "%s" "$(function python3 { return 0; }; '
            'python3 -c \'raise SystemExit(1)\')") # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-deep-substitution": (
            'printf x >/dev/null; X=$(X=$(X=$(X=$(X=$(X=$(X=$(X=$(X=$('
            'function python3 { return 0; }; python3 -c \'raise SystemExit(1)\''
            '))))))))) # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-bash-c": (
            'bash -c \'function bash { return 0; }; bash -c "exit 1"\' # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-classic-bash-c": (
            'bash -c \'bash () { return 0; }; bash -c "exit 1"\' # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-sh-c": (
            'sh -c \'function sh { return 0; }; sh -c "exit 1"\' # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-eval": (
            "printf x >/dev/null; eval 'function python3 { return 0; }'; "
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-classic-builtin-eval": (
            "printf x >/dev/null; builtin eval 'python3 () { return 0; }'; "
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-bash-c-in-substitution": (
            "python3 -c 'import sys; raise SystemExit(int(sys.argv[1]))' "
            '"$(bash -c \'function printf { builtin printf 0; }; printf 1\')" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-eval-in-substitution": (
            "python3 -c 'import sys; raise SystemExit(int(sys.argv[1]))' "
            '"$(eval \'function printf { builtin printf 0; }; printf 1\')" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-nested-backticks": (
            "python3 -c 'import sys; raise SystemExit(int(sys.argv[1]))' "
            '"`echo \\`function printf { builtin printf 0; }; printf 1\\``" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-newline-bash-c": (
            "bash -c $'function python3\\n{ return 0; }; "
            "python3 -c \\\"raise SystemExit(1)\\\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-comment-before-body": (
            "bash -c $'function bash # note\\n{ return 0; }; "
            "bash -c \\\"exit 1\\\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-locale-c-source": (
            "LC_ALL=C bash -c $\"function bash { return 0; }; bash -c 'exit 1'\" "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-locale-program-word": (
            "LC_ALL=C $\"bash\" -c \"function bash { return 0; }; "
            "bash -c 'exit 1'\" # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-plus-n-shell-option": (
            "bash +n -c 'function bash { return 0; }; bash -c \"exit 1\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-disable-then-enable-noexec": (
            "bash -n +n -c 'function bash { return 0; }; bash -c \"exit 1\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-normalized-dev-stdin": (
            "bash /dev/./stdin <<< 'function bash { return 0; }; "
            "bash -c \"exit 1\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-pattern-dev-stdin": (
            "bash /dev/std?n <<< 'function bash { return 0; }; "
            "bash -c \"exit 1\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-pattern-dev-prefix": (
            "bash /d?v/stdin <<< 'function bash { return 0; }; "
            "bash -c \"exit 1\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-brace-dev-prefix": (
            "bash /{dev,tmp}/stdin <<< 'function bash { return 0; }; "
            "bash -c \"exit 1\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-substituted-script-path": (
            "bash \"$(printf /dev/stdin)\" <<< 'function bash { return 0; }; "
            "bash -c \"exit 1\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-process-substitution-script": (
            "bash <(printf '%s\\n' 'function bash { return 0; }' "
            "'bash -c \"exit 1\"') # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-line-continuation": (
            "bash -c $'functio\\\\\\nn bash { return 0; }; "
            "bash -c \\\"exit 1\\\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-commented-substitution-paren": (
            "bash -c $'printf \\'%s\\\\n\\' \"$( # ) inert comment\\n"
            "function bash { return 0; }\\nbash -c \\'exit 1\\'\\n)\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-ansi-adjacent-hash-substitution": (
            "printf '%s' \"$(printf %s $'x'#notcomment; "
            "function bash { return 0; }; bash -c 'exit 1')\" # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-locale-adjacent-hash-substitution": (
            "LC_ALL=C printf '%s' \"$(printf %s $\"x\"#notcomment; "
            "function bash { return 0; }; bash -c 'exit 1')\" # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-nested-substitution-adjacent-hash": (
            "printf '%s' \"$(printf %s x$(printf y)#notcomment; "
            "function bash { return 0; }; bash -c 'exit 1')\" # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-spaced-fd-dup-eval": (
            "2>& 1 eval 'function bash { return 0; }'\n"
            'bash -c "exit 1" # exit 0\n'
        ),
        "literal-child-heredoc-unsupported": (
            "bash -c $'cat >/dev/null <<EOF\\nordinary data\\nEOF\\nexit 0' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "literal-child-split-heredoc-unsupported": (
            "bash -c $'cat >/dev/null <\\\\\\n<EOF\\nordinary data\\nEOF\\nexit 0' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-leading-redirection-eval": (
            "printf x >/dev/null; >/dev/null eval 'function python3 { return 0; }'; "
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-leading-redirection-bash-c": (
            "printf x >/dev/null; >/dev/null bash -c "
            "'function python3 { return 0; }; python3 -c \\\"raise SystemExit(1)\\\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-bash-plus-O": (
            "bash +O extglob -c 'function python3 { return 0; }; "
            "python3 -c \\\"raise SystemExit(1)\\\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-classic-bash-o": (
            "bash -o posix -c 'python3 () { return 0; }; "
            "python3 -c \\\"raise SystemExit(1)\\\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-deep-command-wrapper": (
            "printf x >/dev/null; " + ("command " * 17)
            + "bash -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-nice-wrapper": (
            "printf x >/dev/null; nice -n 5 bash -c "
            "'function bash { return 0; }; bash -c \\\"exit 1\\\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-env-s-wrapper": (
            "printf x >/dev/null; env -S "
            "\"bash -c 'function bash { return 0; }; bash -c \\\\\\\"exit 1\\\\\\\"'\" "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-interspersed-redirection-bash-c": (
            "bash >/dev/null -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-post-c-redirection-bash-c": (
            "bash -c >/dev/null 'function bash { return 0; }; bash -c \\\"exit 1\\\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-here-string-shell-source": (
            "printf x >/dev/null; bash -s <<< "
            "'function bash { return 0; }; bash -c \\\"exit 1\\\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-piped-shell-source": (
            "printf '%s\\n' 'function bash { return 0; }' 'bash -c \\\"exit 1\\\"' "
            "| bash # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-imported-environment": (
            "printf x >/dev/null; env 'BASH_FUNC_bash%%=() { return 0; }' "
            "bash -c 'bash -c \\\"exit 1\\\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-debug-trap": (
            "printf x >/dev/null; trap 'function python3 { return 0; }' DEBUG; "
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-builtin-debug-trap": (
            "printf x >/dev/null; builtin builtin trap "
            "'function python3 { return 0; }' DEBUG; "
            'python3 -c "raise SystemExit(1)" # exit 0\n'
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-after-conditional-data-word": (
            "printf x [[ >/dev/null; function python3 { return 0; }; "
            "python3 -c 'raise SystemExit(1)'; printf ]] >/dev/null # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-dev-stdin-source": (
            "bash /dev/stdin <<< 'function bash { return 0; }; bash -c \\\"exit 1\\\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-dev-fd-source": (
            "bash /dev/fd/0 <<< 'function bash { return 0; }; bash -c \\\"exit 1\\\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-classic-proc-fd-source": (
            "sh /proc/self/fd/0 <<< 'sh () { return 0; }; sh -c \\\"exit 1\\\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-dash-stdin-source": (
            "bash - <<< 'function bash { return 0; }; bash -c \\\"exit 1\\\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-dev-fd3-source": (
            "bash /dev/fd/3 3<<< 'function bash { return 0; }; bash -c \\\"exit 1\\\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-dev-fd9-source": (
            "bash /dev/fd/9 9<<< 'function bash { return 0; }; bash -c \\\"exit 1\\\"' "
            "# exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-stdbuf-imported-environment": (
            "stdbuf -o0 env 'BASH_FUNC_bash%%=() { return 0; }' "
            "bash -c 'bash -c \\\"exit 1\\\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-nested-imported-environment": (
            "env command env 'BASH_FUNC_bash%%=() { return 0; }' "
            "bash -c 'bash -c \\\"exit 1\\\"' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-env-s-escaped-split": (
            "env -S \"bash\\_-c\\_'function bash { return 0; }; "
            "bash -c \\\"exit 1\\\"'\" # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
        ),
        "function-keyword-noclobber-redirection": (
            ">| /dev/null bash -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"' "
            "# exit 0\n"
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
        "printf-v-annotated-compound": (
            "printf -v BASH_ENV '%s' /dev/fd/3; export BASH_ENV; "
            "bash -c 'bash -c false' 3<<< 'function bash { return 0; }' # exit 0\n"
            'python3 -c "raise SystemExit(0)" # exit 0\n'
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
    keyword_function_data = "printf '%s' 'function python3 { return 0; }' >/dev/null"
    if module.unsafe_setup_state(keyword_function_data):
        print("FAIL quoted function-keyword data was refused", file=sys.stderr)
        return 1
    substitution_function_data = (
        "printf '%s' '$(function python3 { return 0; }; python3 -c false)' >/dev/null"
    )
    if module.shell_function_definition(substitution_function_data):
        print("FAIL single-quoted substitution-shaped data was refused", file=sys.stderr)
        return 1
    for marker in ("!", "time", "then", "if", "while", "until"):
        function_argument_data = f"printf '%s\\n' {marker} function python3 {{"
        if module.shell_function_definition(function_argument_data):
            print(
                f"FAIL unquoted function-keyword argument data was refused: {marker}",
                file=sys.stderr,
            )
            return 1
    function_data_controls = {
        "raw-brace-argument": "printf '%s\\n' { function python3 {",
        "welded-brace-argument": "printf '%s\\n' abc{ function python3 {",
        "array-data": "printf x >/dev/null; ARGS=(function python3 {)",
        "array-modifier-data": "printf x >/dev/null; ARGS=(! time function python3 {)",
        "conditional-regex-data": "printf x >/dev/null; [[ foo =~ python3() ]]",
        "shell-source-argv-data": "printf '%s' bash -c 'function bash { return 0; }'",
        "eval-source-argv-data": "printf '%s' eval 'function bash { return 0; }'",
        "python-source-data": "python3 -c 'print(\"function bash { return 0; }\")'",
        "quoted-redirection-command-data": (
            "'>/dev/null' eval 'function bash { return 0; }'"
        ),
        "bash-noexec-source": (
            "bash -n -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "bash-combined-noexec-source": (
            "bash -nc 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "bash-help-source": (
            "bash --help -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "bash-version-source": (
            "bash --version -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "bash-dump-keeps-noexec-after-plus-n": (
            "bash -D +n -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "bash-plus-D-is-dump-noexec": (
            "bash +D -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "bash-noexec-keeps-noexec-after-plus-D": (
            "bash -n +D -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "bash-interactive-combined-noexec": (
            "bash -in -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "bash-interactive-split-noexec": (
            "bash -n -i -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "bash-interactive-dump-noexec": (
            "bash -iD -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "bash-plus-D-interactive-noexec": (
            "bash +D -i -c 'function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "quoted-pattern-device-path": (
            "bash '/dev/std?n' <<< 'function bash { return 0; }'"
        ),
        "escaped-pattern-device-path": (
            "bash /dev/std\\?n <<< 'function bash { return 0; }'"
        ),
        "quoted-variable-device-path": (
            "bash '/dev/$NAME' <<< 'function bash { return 0; }'"
        ),
        "bash-extglob-pattern-data": (
            "bash -O extglob -c 'printf %s @(python3())'"
        ),
        "quoted-redirection-pipe-data": (
            "printf '%s' '>|' bash -c 'function bash { return 0; }'"
        ),
        "child-shell-whole-line-comment": (
            "bash -c '# note; function bash { return 0; }; bash -c \\\"exit 1\\\"'"
        ),
        "child-shell-trailing-comment": (
            "bash -c 'printf x >/dev/null; # note; function bash { return 0; }'"
        ),
        "multiline-quoted-eval-data": (
            "printf '%s' \"first\\neval 'function bash { return 0; }'\\nlast\""
        ),
        "legacy-arithmetic-heredoc-data": "printf '%s\\n' $[1<<2]",
        "arithmetic-heredoc-data": "printf '%s\\n' $((1<<2))",
        "parameter-expansion-heredoc-data": "printf '%s\\n' ${x:-a<<b}",
    }
    refused_controls = [
        label for label, source in function_data_controls.items()
        if module.shell_function_definition(source)
    ]
    if refused_controls:
        print(f"FAIL function-shaped data was refused={refused_controls!r}", file=sys.stderr)
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
        isolated = run_fixed_bash(
            module.proof_script(isolated_setup, isolated_cmd),
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
    if (verifier.returncode != 1 or "5 refused" not in verifier.stdout
            or "5 unsequenced" not in verifier.stdout
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
            or "5 refused" not in closed.stdout
            or "5 refusal-gapped" not in closed.stdout):
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
