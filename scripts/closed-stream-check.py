#!/usr/bin/env python3
"""closed-stream-check.py — no gate may answer a dead output stream with a verdict.

Usage: python3 scripts/closed-stream-check.py [island-dir ...]   (default: skills/*/)

Every gate in this pack states a closed set of exit codes, and a caller reads that set to
decide whether the code under test passed. Two shutdown paths break that promise without
touching a single line of gate logic:

  120  CPython replaces the status a script chose when its own shutdown flush hits a dead
       stdout — the ordinary `gate.py … | head` idiom is enough to trigger it.
  141  a shell gate killed by SIGPIPE, which is 128+13 and likewise names no verdict.

Neither is in any island's table, so either one is a code the caller cannot interpret —
and the failure is silent, because the gate did its work and only died on the way out.

WHAT IT DOES. It re-runs the commands the islands already document as proofs — the same
grammar `verify-proofs.py` reads — with stdout connected to a pipe whose reader is already
closed, then with stderr the same way. A gate that survives both with its own documented
code or the pack-wide exit-2 IO seal is sealed. This probes the REAL verdict paths rather
than `--help`, which is the distinction that matters: an early usage exit often survives a
dead pipe while the path
that actually prints a report does not.

Exit 0 when every probed invocation kept its documented code or used the exit-2 IO seal,
1 when any leaked, 2 on usage, IO, a refused proof step, or a candidate downstream of refusal,
and 3 when nothing was probed at all — a harness that ran nothing has proven nothing, which is
the failure this pack names as its worst gate shape. Refusal outranks "nothing probed": it says
why the harness could not produce a verdict.

LIMITS, stated rather than discovered.

It can only probe what the islands document. A gate path with no documented invocation is not
covered here, and this file is not evidence about it. It also inherits `verify-proofs.py`'s
trust boundary — including its refusal, which both tools now take from one function so they
cannot disagree about what is too dangerous to run: it RUNS commands taken from the repository
it is checking, so point it only at a tree you trust.

The shared grammar's `REFUSE` and gap-cause metadata are binding here. A refused setup is not
silently omitted, and no proof whose setup could not be replayed is probed as a different script.
An ordinary unreplayable gap is counted and excluded under the same eligibility semantics as
`verify-proofs.py`; it does not make a sweep with other eligible proofs fail. A refusal, or a
candidate downstream of one, makes the harness return non-verdict 2 after reporting its count.

What a dead stream is allowed to cost a gate is a judgment, and it is spelled out at the
acceptance rule below rather than left to the reader. A probe may keep the command's documented
code or use the pack-wide exit-2 IO seal. Nothing else is accepted, even when another command in
the same island documents that code. The summary counts how many probes rested on the IO seal
rather than on their documented result surviving.
"""
import importlib.util
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

# What a probe is allowed to return when its output stream is dead. Two things are fine, and
# nothing else is.
#
#   - the code the command DOCUMENTS: its verdict survived the closed stream intact.
#   - 2: the one code every tool and gate in this pack seals an internal or IO fault to, its own
#     `__main__` block included. A report that cannot be written IS an IO fault, so 2 is an
#     honest answer to a dead stream from any of them and needs no further declaration.
#
# An island-wide declaration is not sufficient. A gate documenting 1 — a breach — can answer
# 3, "nothing was checked", while a separate empty-input command in the same SKILL.md honestly
# documents 3. Accepting the island's vocabulary launders the breach. Each probe is therefore
# bound to its own documented code, with only the universal exit-2 IO seal as an alternative.
#
# Everything else is a leak: a shutdown code (CPython's 120, a shell's 141), a signal, a
# TIMEOUT — OR, the dangerous one this check exists for, a DIFFERENT verdict than documented.
# A gate that documents 1 (a breach) and returns 0 (a clean pass) when its pipe dies is a
# breach silently reported as clean, and the previous rule — membership in a pack-wide union
# {0,1,2,3,4} — passed it, because 0 was in the set. The union was also justified as "measured",
# which was false: three islands document 130. This compares against the command's own code.
ALWAYS_FAIL_CLOSED = 2    # the pack-wide IO seal; honest from anything, declared or not

def leaked(rc, expected):
    """A probe result is a leak unless the verdict survived or the gate fail-closed."""
    return rc not in (expected, ALWAYS_FAIL_CLOSED)


def load_grammar():
    """Reuse the proof grammar rather than re-implementing it.

    A second copy of "what counts as a documented command" would drift from the first, and
    then this harness would quietly probe a different set than the one the pack reports.
    """
    here = Path(__file__).resolve().parent / "verify-proofs.py"
    # A checker must not modify the tree it is checking. Importing by path compiles the
    # module and drops `scripts/__pycache__/verify-proofs.*.pyc` into the repo — the same
    # class of defect this pack caught in v1.0, when a syntax check wrote a byte-cache into
    # every island it validated. It is gitignored and would never ship, which is exactly why
    # it would have gone unnoticed.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("verify_proofs", here)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# A redirection that closes a stream (`>&-`, `1>&-`, `2>&-`). Shell SYNTAX, and an ordinary
# pair of characters inside a quote.
CLOSES_STREAM = re.compile(r"\d*>&-")
# `$?` where a command acts on its OWN status rather than merely carrying the two characters
# somewhere: it assigns the status, or reports it, or exits with it. Anchored at the start of a
# simple command, because the position is the whole distinction — `rc=$?` is control flow and
# `g.py "exit was $?"` is an argument, and the two differ in nothing else.
OWN_STATUS = re.compile(
    r"^(?:[A-Za-z_][A-Za-z0-9_]*=\$\?"
    r"|(?:echo|printf|exit|return)\b.*\$\?)")
# The interpreters whose `-c` operand is shell source in its own right rather than data.
SHELL_INTERPRETERS = frozenset({"bash", "sh"})


def segments(text):
    """Split `text` into (chunk, quote) pairs, where quote is None, `'` or `"`.

    Quoting is the whole question here, so it is answered once rather than approximated at each
    call site: `>&-` closes a stream only where the shell reads it as syntax, and a `;` or `|`
    ends a command only there too. `simple_commands` below is the other reader of this split.
    """
    out = []
    buf = []
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\" and quote == '"' and i + 1 < len(text) and text[i + 1] in "$`\"\\":
                i += 1                    # escaped inside double quotes: data, not syntax
            elif ch == quote:
                out.append(("".join(buf), quote))
                buf = []
                quote = None
            else:
                buf.append(ch)
        elif ch in "\"'":
            out.append(("".join(buf), None))
            buf = []
            quote = ch
        elif ch == "\\" and i + 1 < len(text):
            i += 1                        # an escaped character is data wherever it sits
        else:
            buf.append(ch)
        i += 1
    out.append(("".join(buf), quote))
    return out


def simple_commands(text):
    """Split `text` into the simple commands a shell would see, quotes removed.

    Built on `segments` so the quoting question stays answered in one place: a `;`, `|`, `&` or
    newline separates commands only where no quote covers it, and everything inside a quote
    belongs to the command it sits in. A `$` inside SINGLE quotes is blanked, because there it is
    a dollar sign and never an expansion — without that, `echo 'EXIT=$?'`, which prints those
    characters and reads no status at all, would read as a status report.

    A bracket is deliberately NOT a separator, though a shell treats one as a command boundary.
    `$(…)` opens with the same character a subshell does, so splitting there turned the argument
    in `g.py $(echo $?)` into a command of its own and read the gate as its own probe — the very
    exemption this file had just finished narrowing. Splitting only at the separators that cannot
    also open a substitution costs nothing: a bracket that really does open a group is followed by
    commands the remaining separators still divide, and the caller strips the opening bracket off
    the front of each piece.
    """
    out = []
    buf = []
    for chunk, quote in segments(text):
        if quote == "'":
            buf.append(chunk.replace("$", "\0"))
            continue
        if quote is not None:
            buf.append(chunk)
            continue
        pieces = re.split(r"[;|&\n]", chunk)
        buf.append(pieces[0])
        for piece in pieces[1:]:
            out.append("".join(buf))
            buf = [piece]
    out.append("".join(buf))
    return out


def command_sources(text):
    """Split shell source at unquoted command separators while preserving quotes.

    `simple_commands` deliberately removes quote syntax for status-position matching. Shell
    interpreter recursion needs the opposite representation: the final command's original
    quoting, so `bash -c 'echo $?'` remains one operand. Keeping both views prevents a `bash`
    token carried as Python argv, or a status-reporting producer before a pipe, from being
    mistaken for the actual gate command.
    """
    out = []
    buf = []
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(text):
                i += 1
                buf.append(text[i])
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == "\\" and i + 1 < len(text):
            buf.append(ch)
            i += 1
            buf.append(text[i])
        # `>&-`, `<&-`, `2>&1` and `&>` are redirections inside one command, not
        # command separators. Splitting at their ampersand hid the very syntax this parser
        # exists to recognise and re-probed every genuine closed-stream self-test.
        elif ch == "&" and ((i > 0 and text[i - 1] in "<>") or
                            (i + 1 < len(text) and text[i + 1] == ">")):
            buf.append(ch)
        elif ch == "|" and i > 0 and text[i - 1] == ">":
            buf.append(ch)
        elif ch in ";|&\n":
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    out.append("".join(buf))
    return out


def matching_shell_paren(text, opening):
    """Index of the shell parenthesis balancing `opening`, or None."""
    depth = 0
    quote = None
    i = opening
    while i < len(text):
        ch = text[i]
        if ch == "\\" and quote != "'":
            i += 2
            continue
        if quote:
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "'\"`":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def matching_backtick(text, opening):
    """Index of the unescaped backtick closing `opening`, or None."""
    i = opening + 1
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "`":
            return i
        i += 1
    return None


def mask_nested_substitutions(text):
    """Hide substitutions while classifying the stream behavior of the outer command.

    Command and process substitutions run in their own execution context. A redirection or
    status report inside one says nothing about the outer gate's streams or status handling:
    `gate.py $(printf x >&-)` still runs `gate.py` with its ordinary stdout. Leaving the inner
    source visible let that harmless argument buy the outer gate a false self-probe exemption.

    Quotes are preserved so the remaining source still reaches `segments`, `simple_commands`,
    and `shlex` with its outer grammar intact. Unterminated substitutions are left untouched;
    malformed shell source is not grounds for silently exempting a proof.
    """
    out = []
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        # shlex retains the backslash from a `\$(` written inside the outer command's
        # double-quoted `bash -c` operand, while bash consumes that backslash before handing
        # the operand to the inner shell. Treat the escaped spelling as the same nested
        # substitution here. Otherwise its inner `>&-` remains visible and falsely exempts
        # the outer gate; the resolved spelling checked by the recursion below is then safe
        # while this unresolved spelling is not.
        if quote != "'" and text.startswith("\\$(", i):
            end = matching_shell_paren(text, i + 2)
            if end is not None:
                out.append("__closed_stream_substitution__")
                i = end + 1
                continue
        if ch == "\\" and quote != "'" and i + 1 < len(text):
            out.append(text[i:i + 2])
            i += 2
            continue
        if ch == "'":
            if quote is None:
                quote = "'"
            elif quote == "'":
                quote = None
            out.append(ch)
            i += 1
            continue
        if ch == '"':
            if quote is None:
                quote = '"'
            elif quote == '"':
                quote = None
            out.append(ch)
            i += 1
            continue
        if quote != "'" and text.startswith("$(", i):
            end = matching_shell_paren(text, i + 1)
            if end is not None:
                out.append("__closed_stream_substitution__")
                i = end + 1
                continue
        if quote is None and (text.startswith("<(", i) or text.startswith(">(", i)):
            end = matching_shell_paren(text, i + 1)
            if end is not None:
                out.append("__closed_stream_process_substitution__")
                i = end + 1
                continue
        if quote != "'" and ch == "`":
            end = matching_backtick(text, i)
            if end is not None:
                out.append("__closed_stream_backtick__")
                i = end + 1
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def self_probe(cmd, depth=0):
    """Does this command close one of its own streams, or act on its own status, on purpose?

    Such a command is the island's own probe of this very defect; re-closing its stream would
    test the harness rather than the gate. The exclusion used to be `">&-" in cmd or "$?" in
    cmd` — a substring test over the whole line — so a command that merely CONTAINED those
    characters inside a quoted argument (`printf 'exit was $?'`) was dropped from the check it
    exists to run, and a gate could buy its way out of being probed with one argument.

    Stripping quotes is not the fix for `>&-`, and that is why this walks the syntax: four
    islands write a real self-probe as `bash -c '… >&-'`, where the redirection lives inside a
    quote and is nonetheless a redirection, because the `-c` operand is itself shell source. So
    `>&-` is read where no quote covers it — in this command, and recursively in any `-c`
    operand.

    `$?` needed the opposite correction. Reading it wherever a shell would EXPAND it still let
    one keystroke buy the same exemption: `g.py "exit was $?"` expands, so the double-quoted
    twin of the argument that had just been closed off walked straight back out of the probe
    set, and the flipping gate behind it went unseen. Expansion was never the property that
    matters — POSITION is. A command's own control flow is `rc=$?`, `echo $?`, `exit $?`: the
    status becoming the thing the final command does. An earlier pipeline producer and
    shell-looking argv carried by Python are not that command. Anywhere else the two characters
    are a value being carried, and carrying one is no reason to leave a gate unprobed.
    """
    # Mask substitutions before splitting at command separators. A semicolon inside `$(...)`
    # separates the substitution's commands, not the outer command; splitting the raw source
    # first promoted the substitution's final `exit $?` into the gate position and falsely
    # exempted the outer gate.
    masked_cmd = mask_nested_substitutions(cmd)
    positioned = [part for part in command_sources(masked_cmd) if part.strip()]
    if not positioned:
        return False
    gate_source = positioned[-1]
    # A substitution's redirection and status belong to the substitution, not to the outer
    # command whose eligibility is being decided. Mask those nested programs before looking
    # for self-probe syntax; a real nested shell reached through `bash -c` is handled below by
    # recursively classifying the shell operand itself.
    outer_source = gate_source
    parts = segments(outer_source)
    redirect_source = "\n".join(chunk for chunk, q in parts if q is None)
    if CLOSES_STREAM.search(redirect_source):
        return True
    # `lstrip` because a group's opening bracket is not part of the command inside it, and
    # `simple_commands` leaves brackets where it finds them on purpose.
    gate_commands = [simple for simple in simple_commands(outer_source) if simple.strip()]
    if gate_commands and OWN_STATUS.match(gate_commands[-1].strip().lstrip("({ \t")):
        return True
    if depth >= 3:
        return False
    try:
        words = shlex.split(gate_source.strip().lstrip("({ \t"))
    except ValueError:
        return False
    # Only the executable position may open a nested shell. `python gate.py bash -c 'echo $?'`
    # carries those words as Python argv; walking every word treated the data as a command and
    # let a leaking gate opt out of the probe.
    if not words or os.path.basename(words[0]) not in SHELL_INTERPRETERS:
        return False
    for j in range(1, len(words)):
        if words[j] == "-c" and j + 1 < len(words):
            operand = words[j + 1]
            # `shlex` and bash disagree about one escape, and the disagreement is load-
            # bearing here: inside double quotes bash resolves `\$` to `$` and hands the
            # inner shell an expansion, while `shlex` leaves the backslash where it was.
            if any(self_probe(o, depth + 1)
                   for o in (operand, operand.replace("\\$", "$"))):
                return True
            break
    return False


def probe(script, cwd, stream):
    """Run one invocation with `stream` (1 or 2) already closed; return its exit code."""
    r, w = os.pipe()
    os.close(r)                                   # the reader is gone before the write
    kw = {"stdout": w, "stderr": subprocess.DEVNULL} if stream == 1 else \
         {"stderr": w, "stdout": subprocess.DEVNULL}
    try:
        rc = subprocess.run(["bash", "-c", script], cwd=cwd, timeout=60, **kw).returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    finally:
        try:
            os.close(w)
        except OSError:
            pass
    # A child killed by a signal reaches Python as the NEGATIVE signal number, while a shell
    # reports the same death as 128+n. Comparing the raw value against shell-convention
    # constants meant the SIGPIPE half of this tool could never fire on the common path:
    # `bash -c '<one command>'` exec-optimises, so bash IS the gate, and its SIGPIPE death
    # arrived here as -13 while the table was looking for 141. Fourteen real deaths across ten
    # islands were reported as clean, by the very gate built to catch them.
    return 128 - rc if rc < 0 else rc


def main(argv):
    vp = load_grammar()
    args = argv[1:] or sorted(str(p) for p in Path("skills").glob("*/"))
    probed = 0
    leaks = []
    refused = 0
    unsequenced = 0
    refusal_gapped = 0
    examined = 0
    own_probes = 0
    sealed = 0
    explicit = bool(argv[1:])
    for arg in args:
        d = Path(arg)
        skill = d / "SKILL.md"
        if not skill.is_file():
            # Skipping a path the caller NAMED, and then counting it in the summary, certified a
            # scope this tool never looked at: one real island plus one typo reported "over 2
            # island(s)" and exited 0. A default sweep may pass over a non-island directory; an
            # explicit target that is not one is the caller being wrong.
            if explicit:
                print(f"closed-stream-check: not an island (no SKILL.md): {d}", file=sys.stderr)
                return 2
            continue
        examined += 1
        skill_text = skill.read_text(encoding="utf-8")
        for block in vp.blocks(skill_text):
            for cmd, expected, setup, gapped in vp.commands(block):
                # REFUSE is a grammar verdict about a setup row, not an expected process code.
                # It must be consumed before the runnable filter, because environment bindings
                # are intentionally off the command allowlist. Ignoring it let the later gapped
                # proof run under a different environment than the document states.
                if expected == vp.REFUSE:
                    refused += 1
                    continue
                if expected is None or not vp.is_runnable(cmd):
                    continue
                if vp.PLACEHOLDER.search(cmd):
                    continue
                if gapped:
                    # verify-proofs does not count a matching gapped command as verified. This
                    # harness cannot make a stronger claim by probing the command with the
                    # missing/refused setup silently removed. Cause metadata distinguishes the
                    # pack's disclosed ordinary gaps from a refused environment mutation: both
                    # are excluded, but only refusal makes the whole harness a non-verdict.
                    if "refused" in gapped:
                        refusal_gapped += 1
                    else:
                        unsequenced += 1
                    continue
                # A command that already closes a stream on purpose is the island's own
                # probe of this very defect; re-closing it would test the harness, not it.
                # Counted and printed, not pruned in silence — a quiet prune is the same
                # false green this pack names elsewhere, and 19 candidates land here today.
                if self_probe(cmd):
                    own_probes += 1
                    continue
                script = "; ".join(setup + [cmd]) if setup else cmd
                # The refusal has to cover the whole script that will actually run. Testing only
                # the annotated command left a forbidden primitive in a replayed SETUP line free
                # to execute — twice, once per stream — while verify-proofs.py, reading the same
                # blocks, refused that very script. Two tools disagreeing about what is too
                # dangerous to run is worse than either answer alone.
                if vp.forbidden_primitive(script):
                    refused += 1
                    continue
                for stream in (1, 2):
                    probed += 1
                    rc = probe(script, d, stream)
                    if leaked(rc, expected):
                        leaks.append((d.name, "stdout" if stream == 1 else "stderr",
                                      rc, expected, cmd))
                    elif rc != expected:
                        # Accepted, and counted rather than passed over in silence: this is the
                        # concession the acceptance rule makes, so its size belongs on the summary
                        # line where a reader can see how much of the green rests on it.
                        sealed += 1
    for name, which, rc, expected, cmd in leaks:
        print(f"LEAK {name}: exit {rc} with {which} closed — documented {expected}, "
              f"and {rc} is neither that result nor the pack-wide exit-2 IO seal")
        print(f"      {cmd}")
    tail = ((f", {refused} refused" if refused else "")
            + (f", {refusal_gapped} refusal-gapped" if refusal_gapped else "")
            + (f", {unsequenced} unsequenced" if unsequenced else ""))
    print(f"\n{probed} closed-stream probes over {examined} island(s), {len(leaks)} leak(s){tail}"
          f" ({sealed} fail-closed to the pack-wide exit-2 seal; {own_probes} candidate(s) not "
          f"re-probed: they close a stream themselves)")
    if leaks:
        return 1
    if refused or refusal_gapped:
        print("NON-VERDICT - refused proof steps and their downstream candidates were not probed",
              file=sys.stderr)
        return 2
    if probed == 0:
        print("NOTHING PROBED - this is not a pass", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    try:
        _code = main(sys.argv)
    except KeyboardInterrupt:
        _code = 2
    except BaseException as _exc:
        print(f"error: internal failure: {type(_exc).__name__}: {_exc}", file=sys.stderr)
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
