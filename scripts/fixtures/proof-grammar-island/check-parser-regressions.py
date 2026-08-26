#!/usr/bin/env python3
"""Proof grammar parser checks plus safe integration replays over hostile fixtures."""

from __future__ import annotations

import importlib.util
import os
import shlex
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

    provenance_cases = {
        r'''bash '/dev/std?n' ''': ("/dev/std?n", False),
        r'''bash /dev/std\?n ''': ("/dev/std?n", False),
        r'''bash "\\?" ''': (r"\?", False),
        r'''bash "\$SOURCE" ''': ("$SOURCE", False),
        r'''bash "$SOURCE" ''': ("$SOURCE", True),
        r'''bash "$(printf /dev/stdin)" ''': ("$(printf /dev/stdin)", True),
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
    if (verifier.returncode != 1 or "4 refused" not in verifier.stdout
            or "4 unsequenced" not in verifier.stdout
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
            or "4 refused" not in closed.stdout
            or "4 refusal-gapped" not in closed.stdout):
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
