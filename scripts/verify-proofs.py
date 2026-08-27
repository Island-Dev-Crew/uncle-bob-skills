#!/usr/bin/env python3
"""verify-proofs.py — re-run every command an island states an exit code for, and check it.

Usage: python3 scripts/verify-proofs.py [--strict] [island-dir ...]   (default: skills/*/)

Each island's SKILL.md carries a red/green proof block: shell commands with the exit
code they produced, written as an annotation. This tool extracts those pairs, runs each
command from the island's own directory, and compares. It is the pack's own law turned
on its documentation - a proof block that no longer reproduces is a claim, not evidence.

THE PROOF GRAMMAR, one definition rather than a list of habits. A *candidate* is a line
inside a ```bash / ```sh fence whose leading token is on the allowlist below; a `$ ` prompt
may precede it. A candidate becomes a *proof* when an exit code is stated for it, either
inline or on the exit-report line that follows its output:

    python3 scripts/x.py fixture   # exit 1          inline
    python3 scripts/x.py fixture   # → EXIT=1        inline
    scripts/x.sh fixture           # exit 1          inline, bare island-relative script
    $ python3 scripts/x.py fixture                   report line, below the output:
    | ...output...
    $ rc=$?; echo "EXIT=$rc"       # → EXIT=1
    $ echo $?                      # → 1

Allowlisted leading tokens: `python3`, `bash`, `sh`, `printf` (the shipped
`printf … | python3 gate.py` stdin form), `./…`, and a relative path that names a directory
and ends `.sh`/`.py` (`scripts/probe.sh`; a script in the island root needs its `./`).
A candidate whose arguments contain a `<placeholder>` is a usage
template, reported as TEMPLATE and not run. A fenced command whose leading token is off
the allowlist is reported as SKIPPED rather than silently dropped.

An exit-report line is exactly `echo $?` or `rc=$?; echo "EXIT=$rc"` before its trailing
annotation. That whole-line rule is load-bearing: a pipe, a second semicolon command, or an extra
operand makes the row an independent command boundary, never a report that can annotate the row
above it.

Exit 0 iff at least one proof ran AND every one reproduced its documented code. Exit 1 on
a mismatch or a refusal, 2 on usage or IO, and 3 when nothing was executed at all - a
verifier that ran nothing has verified nothing, and saying PASS there is the same failure
as a gate that scans zero files. A candidate that is neither a proof nor a template is
reported as PENDING, one line each, and never guessed at; `--strict` makes any PENDING
exit 4, so a caller that wants full coverage can demand it, and 4 OUTRANKS 3 when both are
true: an island whose every candidate is PENDING ran nothing, and answering the coverage
question with the same code an island holding no proof block at all returns tells the
caller who asked the less specific of two true things. PENDING is the failure
direction of every ambiguity here: an output line that could pass for a command ends the
search for a report line, which leaves a proof unverified rather than pairing a command
with a code that is not its own.

That boundary is lexical and host-independent. An unprompted output row and an off-allowlist
command can be identical shell text; the verifier does not use the host's `PATH` to guess which
one the author meant. Every nonempty unmarked non-comment row terminates report search and is
classified independently, including a row with malformed quotes or escapes. `| ` is the grammar's
explicit output prefix and is the one exception. If unmarked proof output precedes a separate
`echo $?`, the proof is conservatively `PENDING` and the ambiguous row may be `SKIPPED`; mark
output with `| ` or put the exit annotation inline on the proof command. A code is never borrowed
across a row merely because its apparent executable is absent from this machine or cannot be
tokenized.

TRUST BOUNDARY, stated rather than implied. This tool RUNS commands taken out of the
repository it is checking. That is inherent to re-running a documented proof, not an
oversight — a proof block that is never executed is a claim again. So it is only safe to
point at a repository you trust: a fork, a pull request, or an untrusted clone can put a
command in a fenced block and this tool will run it. Two mitigations, neither a substitute
for that sentence: the leading token must be on the allowlist above, and a command carrying
a network, privilege-escalation, or device-destructive primitive is REFUSED rather than run,
by the name the KERNEL would resolve rather than the characters on the page - `/usr/bin/curl`
and `../../sbin/dd` are refused with the bare words, and so are the spellings only a shell
resolves (`cur\\l`, `'cur'l`, `c''url`, `CURL`, `$'cur\\x6c'`), because ANSI-C words are decoded
and the line is parsed into words the way Bash parses it before those words are judged. Executable
source inside `$()`, `<()`, `>()`, and backticks is inspected recursively without being run. What
this static walk does NOT reach is a name assembled
at run time: `C=cur\\l; bash -c '$C x'` carries no forbidden word in any word it has, and is run.
That is the trust sentence above, restated about one narrower case rather than argued away. The
allowlist
widened when the grammar was written down — it now admits a bare island-relative script and a
`printf` stdin pipe — so it constrains the first token only, never the rest of the line.

KNOWN LIMITS, stated rather than discovered. Each annotated command runs from the island's
directory, preceded by the steps of its own block that this tool can replay verbatim: the
supported block-local variable assignments, and the earlier unannotated commands that build the
block's fixtures. A supported assignment is `NAME=one-shell-word`; quoted spaces and command or
process substitutions inside that word are accepted, as are semicolon-separated rows of the same
shape. Braced parameter (`${...}`) and arithmetic (`$((...))` / `$[...]`) expansions are
deliberately outside this small grammar because both can assign another shell variable as a side
effect; an unbraced value expansion such as `$OTHER` is accepted. Assignments that redirect
command lookup or inject interpreter startup (`PATH`,
`*PATH`, loader variables, and the named shell/interpreter hooks below) are refused whether or
not the author wrote `export`. A function definition (`name ()` or `function name`) masquerading
as an allowlisted invocation is refused whether or not it carries an exit annotation, including
inside executable substitutions and literal Bash/sh `-c` source. Literal child commands exposed
through recognized BSD/GNU `xargs` options are inspected on the same boundary; unknown or
runtime-computed launcher grammar is refused, as is an `xargs`-supplied shell option or source
operand. Function-shaped text passed only as ordinary data remains ordinary data. Actual
command-position `eval`, `source`, `.`, state-setting `trap`, imported `BASH_FUNC_*%%`
environment entries, and
Bash/sh invocations that read their program from stdin, environment hooks, interactive/login
profiles, explicit startup files, or the debugger profile are refused too: externally provided
source can establish the same state, so a literal-only scan could not certify them. Those words
remain ordinary data when they are arguments to another command, and no-exec/immediate-exit shell
options do not pretend to execute their `-c` operands. Literal child-shell source containing an
active heredoc is refused as unsupported: the payload is data, but this deliberately small static
reader cannot promise to separate every delimiter form from later commands. Here strings, quoted
`<<` text, arithmetic shifts, and conditional operands are not caught by that rule. Direct,
literal Bash `printf -v` and `%n` setup forms are refused because they write shell variables by a
second grammar. Accepted assignments and allowlisted locale/encoding exports remain in the proof
shell; an assignment mixed with another command is gapped rather than executed as setup.
Earlier runnable fixture builders run in child shells: their filesystem effects persist, but
their functions, command hash, traps, options, and other shell state cannot replace the later
proof command. Thus `D=$(mktemp -d)` is re-evaluated, a child builds fixtures inside that
directory, and the annotated command sees the same `D` without inheriting the builder's shell.

Three shapes still cannot be replayed, and all are handled by saying so rather than by
guessing:
  - a heredoc (`python3 - <<'EOF'`), whose body is not captured with its first line
  - a step whose leading token is off the allowlist (a `cd`, a `(subshell)`)
  - an assignment outside the grammar above (`ARGS=(one two)`, any braced parameter/arithmetic
    expansion, or an assignment mixed with a command)
When one of those precedes a command, that command's block is GAPPED: it still runs, a
mismatch is still reported, but a MATCH is reported as UNSEQUENCED and NOT counted as a
verified proof — the scenario it was pointed at may never have been built. Counting a pass
whose setup never ran is the same false green this tool exists to catch in the islands.

An island can retire a gap on its side: state the working directory inside the command
(`bash -c 'cd scripts && ./gate.sh fixture'`) rather than in a sentence above the block,
and write a probe as a one-line `python3 -c` that EXITS with the code it reports instead of
a heredoc that only prints it. Both were real islands here; both now reproduce.

A mismatch is still a prompt to go look before it is a verdict — check it by running the
block as a whole.
"""
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

# Refused outright rather than executed. Not a sandbox — a `python3 -c` can still do
# anything — but it closes the shapes that exfiltrate or escalate, which are the ones a
# hostile proof block would reach for first. Re-measured after the refusal learned to read the
# line as words rather than as text, which is the reading that could newly catch an innocent
# argument: zero candidates in this repo match, so it costs no false red today. Re-measure
# rather than trust this sentence — `grep -c REFUSED` on a full run is the check.
FORBIDDEN_NAMES = frozenset("""
curl wget nc ncat netcat telnet ssh scp sftp rsync
sudo doas chown chgrp shutdown reboot mkfs dd
""".split())
# The bare-word spelling. The lookbehind is what keeps `scripts/dd-helper.py` from reading as
# `dd` — and it is also why this pattern alone cannot see a program named by path.
FORBIDDEN = re.compile(r"(?<![\w./-])(?:" + "|".join(sorted(FORBIDDEN_NAMES)) + r")(?![\w./-])")
# A word that names a program by path rather than by bare name: `/usr/bin/curl`, `../../sbin/dd`.
PATH_WORD = re.compile(r"[A-Za-z0-9_.~-]*(?:/[A-Za-z0-9_.~-]+)+")
# The interpreters whose `-c` operand is shell source in its own right rather than data, so a
# word inside it is a program the kernel will reach and not an argument being passed along.
SHELL_INTERPRETERS = frozenset({"bash", "sh"})

# `# exit N`, `# -> EXIT=N`, `# → EXIT=N`, tolerating surrounding prose in the comment.
ANNOT = re.compile(r"#.*?(?:exit\s*=?\s*|EXIT=)(\d+)", re.IGNORECASE)
PROMPT = re.compile(r"^\s*\$\s+(.*)$")
# The allowlist that defines a candidate. The fourth alternative is the shipped bare form -
# `scripts/diff-scope.sh HEAD~1 HEAD` - which the extractor used to skip outright, so two
# islands' entire red/green pair went unread and the run reported "0 documented" at exit 0.
RUNNABLE = re.compile(
    r"^(?:python3\s|bash\s|sh\s|printf\s|\./"
    r"|(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:sh|py)(?:\s|$))"
)
# An exit-report line is a whole command, not a familiar prefix. Letting `echo $? | gate` or
# `rc=$?; echo ...; gate` match here lends the compound row's annotation to the candidate above.
# Prompts and comments are removed by the caller before this expression is judged.
REPORT = re.compile(
    r'^(?:echo[ \t]+\$\?|rc=\$\?;[ \t]*echo[ \t]+"EXIT=\$rc")[ \t]*$'
)
# Explicit proof output. Every other nonempty unmarked row is a possible command and therefore a
# report boundary, even when malformed; the pipe marker is invalid as a standalone command and
# removes that ambiguity deliberately rather than by consulting the host's executable inventory.
OUTPUT = re.compile(r"^\s*\|\s")
# The code a report line states, anchored at its comment: `# → 1`, `# -> EXIT=1`, `# 2`.
ARROW = re.compile(r"\s*(?:[-=]*>|→)?\s*(?:EXIT\s*=\s*)?(\d+)\b")
# An inline arrow on an independent command. Unlike ARROW, used after a known report line, this
# requires the arrow marker so an arbitrary numeric prose comment cannot become an exit claim.
INLINE_ARROW = re.compile(r"\s*(?:[-=]*>|→)\s*(?:EXIT\s*=\s*)?(\d+)\b")


def is_runnable(cmd):
    return bool(RUNNABLE.match(cmd.strip()))


def is_report(line):
    """Whether `line` is one complete accepted exit-report command."""
    return bool(REPORT.fullmatch(split_comment(line)[0].strip()))


def decode_ansi_c_content(text):
    """Decode the literal escapes Bash accepts inside one ANSI-C quoted word."""
    simple = {
        "a": "\a", "b": "\b", "e": "\x1b", "E": "\x1b", "f": "\f",
        "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\",
        "'": "'", '"': '"', "?": "?",
    }
    out = []
    i = 0
    while i < len(text):
        if text[i] != "\\" or i + 1 >= len(text):
            out.append(text[i])
            i += 1
            continue
        escape = text[i + 1]
        if escape in simple:
            out.append(simple[escape])
            i += 2
            continue
        if escape in "01234567":
            end = i + 2
            while end < len(text) and end < i + 4 and text[end] in "01234567":
                end += 1
            out.append(chr(int(text[i + 1:end], 8)))
            i = end
            continue
        widths = {"x": 2, "u": 4, "U": 8}
        if escape in widths:
            end = i + 2
            limit = end + widths[escape]
            while end < len(text) and end < limit and text[end] in "0123456789abcdefABCDEF":
                end += 1
            if end > i + 2:
                try:
                    out.append(chr(int(text[i + 2:end], 16)))
                except (ValueError, OverflowError):
                    return None
                i = end
                continue
        if escape == "c" and i + 2 < len(text):
            control = text[i + 2]
            out.append(chr(127 if control == "?" else ord(control.upper()) & 31))
            i += 3
            continue
        out.extend(("\\", escape))
        i += 2
    # Bash variables and argv cannot carry NUL; ANSI-C quoting truncates there.
    return "".join(out).split("\0", 1)[0]


def normalize_ansi_c_quotes(text):
    """Turn static Bash ANSI-C/locale words into equivalent ordinary shell literals.

    ``shlex`` understands neither Bash's ``$'...'`` nor ``$"..."`` prefixes. Leaving the
    locale prefix in place changes an executable or ``-c`` operand from ``bash``/``function``
    to ``$bash``/``$function`` in the static argv and can hide the command being inspected.
    Locale quotes otherwise follow double-quote parsing, so dropping only their leading dollar
    preserves the relevant word boundary and source bytes.
    """
    out = []
    quote = None
    i = 0
    while i < len(text):
        char = text[i]
        if quote:
            out.append(char)
            if char == "\\" and quote == '"' and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            if char == quote:
                quote = None
            i += 1
            continue
        if char == "\\" and i + 1 < len(text):
            out.append(text[i:i + 2])
            i += 2
            continue
        if text.startswith('$"', i):
            out.append('"')
            quote = '"'
            i += 2
            continue
        if char in "'\"":
            quote = char
            out.append(char)
            i += 1
            continue
        if not text.startswith("$'", i):
            out.append(char)
            i += 1
            continue
        end = i + 2
        encoded = []
        while end < len(text):
            if text[end] == "\\" and end + 1 < len(text):
                encoded.append(text[end:end + 2])
                end += 2
                continue
            if text[end] == "'":
                break
            encoded.append(text[end])
            end += 1
        if end >= len(text):
            # Leave malformed source malformed. Its row is still a report boundary, and Bash
            # will reject it if it is itself an annotated allowlisted candidate.
            out.append(char)
            i += 1
            continue
        decoded = decode_ansi_c_content("".join(encoded))
        out.append(text[i:end + 1] if decoded is None else shlex.quote(decoded))
        i = end + 1
    return "".join(out)


def shell_words(script, depth=0):
    """Every word this script hands the kernel, with quoting and escaping already resolved.

    `shlex.split` performs the same word parse the shell does, which is the whole point: it is
    the one reading under which `cur\\l`, `'cur'l`, `"cur"l` and `c''url` stop being four
    strings and become one word, `curl`. A nested `bash -c` operand is walked too, the way
    `closed-stream-check.py`'s `self_probe` walks it, because that operand is shell source again
    and a spelling this parse resolves here can hide behind one more quote inside it. Depth is
    capped for the reason that cap exists there: a proof block does not nest interpreters three
    deep, and a runaway parse would be a worse failure than a word this never sees.

    A line `shlex` refuses — an unbalanced quote — yields nothing, and the caller falls back to
    reading it as text.
    """
    try:
        words = shlex.split(normalize_ansi_c_quotes(script))
    except ValueError:
        return
    for i, word in enumerate(words):
        yield word
        if depth >= 3 or os.path.basename(word).lower() not in SHELL_INTERPRETERS:
            continue
        for j in range(i + 1, len(words)):
            if words[j] == "-c" and j + 1 < len(words):
                yield from shell_words(words[j + 1], depth + 1)
                break


def matching_substitution_paren(text, opening):
    """Index of the parenthesis closing a command/process substitution, or None."""
    word_closers = []
    quote = None
    in_comment = False
    at_word_start = True
    i = opening
    while i < len(text):
        ch = text[i]
        if in_comment:
            if ch == "\n":
                in_comment = False
                at_word_start = True
            i += 1
            continue
        if quote:
            if ch == "\\" and quote in ('"', "locale", "ansi", "backtick"):
                i += 2
                continue
            if ((quote == "single" and ch == "'")
                    or (quote in ('"', "locale") and ch == '"')
                    or (quote == "ansi" and ch == "'")
                    or (quote == "backtick" and ch == "`")):
                quote = None
            i += 1
            continue
        if ch == "\\":
            at_word_start = False
            i += 2
            continue
        if text.startswith("$'", i):
            quote = "ansi"
            at_word_start = False
            i += 2
            continue
        if text.startswith('$"', i):
            quote = "locale"
            at_word_start = False
            i += 2
            continue
        if ch == "'":
            quote = "single"
            at_word_start = False
        elif ch == '"':
            quote = '"'
            at_word_start = False
        elif ch == "`":
            quote = "backtick"
            at_word_start = False
        elif ch == "#" and at_word_start:
            in_comment = True
        elif ch == "(":
            word_closers.append(i > 0 and text[i - 1] in "$<>?*+@!")
            at_word_start = True
        elif ch == ")":
            word_closer = word_closers.pop() if word_closers else False
            if not word_closers:
                return i
            at_word_start = not word_closer
        else:
            at_word_start = ch.isspace() or ch in ";|&<>\n"
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


def nested_backtick_source(body):
    """Expose legacy backticks escaped only to survive an enclosing backtick pair."""
    return body.replace(r"\`", "`")


def executable_substitutions(text):
    """Yield shell source executed by command, process, and backtick substitutions.

    These bodies execute even though an outer `shlex` parse sees them as parts of an argument.
    Single and ANSI-C quotes suppress substitutions; command substitution and backticks remain
    active inside double/locale quotes, while process substitution is active only unquoted.
    Malformed, unterminated syntax yields no body because Bash cannot execute it either.
    """
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote in ("single", "ansi"):
            if ch == "\\" and quote == "ansi":
                i += 2
                continue
            if (quote == "single" and ch == "'") or (quote == "ansi" and ch == "'"):
                quote = None
            i += 1
            continue
        if quote in ('"', "locale"):
            if ch == "\\":
                i += 2
                continue
            if text.startswith("$((", i):
                end = matching_substitution_paren(text, i + 1)
                if end is not None:
                    yield from executable_substitutions(text[i + 3:end - 1])
                    i = end + 1
                    continue
            if text.startswith("$(", i):
                end = matching_substitution_paren(text, i + 1)
                if end is not None:
                    yield text[i + 2:end]
                    i = end + 1
                    continue
            if ch == "`":
                end = matching_backtick(text, i)
                if end is not None:
                    yield nested_backtick_source(text[i + 1:end])
                    i = end + 1
                    continue
            if ch == '"':
                quote = None
            i += 1
            continue
        if ch == "\\":
            i += 2
            continue
        if text.startswith("$'", i):
            quote = "ansi"
            i += 2
            continue
        if text.startswith('$"', i):
            quote = "locale"
            i += 2
            continue
        if ch == "'":
            quote = "single"
            i += 1
            continue
        if ch == '"':
            quote = '"'
            i += 1
            continue
        if text.startswith("$((", i):
            end = matching_substitution_paren(text, i + 1)
            if end is not None:
                yield from executable_substitutions(text[i + 3:end - 1])
                i = end + 1
                continue
        if text.startswith("$(", i):
            end = matching_substitution_paren(text, i + 1)
            if end is not None:
                yield text[i + 2:end]
                i = end + 1
                continue
        if text.startswith(("<(", ">("), i):
            end = matching_substitution_paren(text, i + 1)
            if end is not None:
                yield text[i + 2:end]
                i = end + 1
                continue
        if ch == "`":
            end = matching_backtick(text, i)
            if end is not None:
                yield nested_backtick_source(text[i + 1:end])
                i = end + 1
                continue
        i += 1


def forbidden_primitive(script, depth=0):
    """The network, privilege-escalation or device-destructive primitive this script would
    reach, however it is spelled — or None.

    Three readings are needed because three spellings reach the same binary. `curl x` is caught
    by the bare-word pattern; the lookbehind that keeps `scripts/dd-helper.py` from reading as
    `dd` also blinds that pattern to `/usr/bin/curl x`, which executes the identical program, so
    a word naming a path is judged by its basename — the name the kernel resolves. Neither
    pattern sees the third spelling, and that is not a matter of a missing character class:
    both read the line as text, and the shell does not. `cur\\l`, `'cur'l`, `"cur"l` and `c''url`
    are ordinary quoting, bash resolves every one to `curl`, and a documented proof carrying any
    of them was RUN — by this tool and then four more times by the harness that shares this
    test. So the line is also read as the shell parses it, and the resulting words are compared
    case-insensitively, because on a case-insensitive volume `CURL` and `/usr/bin/CURL` execute
    the same binary as their lowercase spellings.

    The patterns run first and run always, not only when `shlex` refuses the line. They cover
    what a word parse cannot — a name welded to other syntax, and a line whose quoting is
    unbalanced enough that there are no words to read. Command substitution, both process
    substitutions, and backticks are executable shell source too, even when they sit inside one
    outer argument. Their bodies are walked recursively and never executed by this inspection.
    """
    bare = FORBIDDEN.search(script)
    if bare:
        return bare.group(0)
    for word in PATH_WORD.findall(script):
        if os.path.basename(word).lower() in FORBIDDEN_NAMES:
            return word
    for word in shell_words(script):
        if os.path.basename(word).lower() in FORBIDDEN_NAMES:
            return word
    if depth < 8:
        for body in executable_substitutions(script):
            nested = forbidden_primitive(body, depth + 1)
            if nested:
                return nested
    return None


def reported_code(rest):
    """Read the exit code stated by the report line belonging to the command above it.

    A proof block usually shows the command, then the output it produced, then a line that
    reports `$?`. The report is therefore several lines below the command it annotates, and
    a fixed two-line lookahead missed every one of them - twenty-five real proofs across
    three islands read as unannotated and were never re-run. So walk forward through the
    output to the first line that is itself a command or a report. Only a report annotates;
    anything command-shaped ends the search and leaves the command PENDING, which is the
    safe direction: an unverified proof, never a code borrowed from a different command.
    """
    for raw in rest:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if OUTPUT.match(raw):
            continue
        m = PROMPT.match(raw)
        body = m.group(1).strip() if m else stripped
        if is_report(body):
            found = ANNOT.search(body)
            if found:
                return int(found.group(1))
            if "#" in body:
                tail = ARROW.match(body.split("#", 1)[1])
                if tail:
                    return int(tail.group(1))
            return None
        code = split_comment(body)[0]
        if (m or is_runnable(body) or ASSIGN.match(code) or EXPORT.match(code)
                or command_shaped(body)):
            return None
    return None


def replayable(cmd):
    """Can this step be replayed verbatim in front of a later command?

    Only if it is one whole command. The extractor reads a fence line by line, so a
    heredoc body and the tail of a multi-line quoted string are NOT captured with their
    opening line. Replaying such a fragment does not rebuild a fixture — it leaves an
    unterminated quote that swallows whatever is appended after it. A step that fails this
    test is left out of the prefix and the block is marked gapped, which is a smaller lie
    than a prefix that silently eats the command it was meant to set up.
    """
    if "<<" in cmd:
        return False
    try:
        shlex.split(cmd)
    except ValueError:
        return False
    return True


def split_comment(line):
    """Split a fenced line into (command, trailing comment), respecting quotes.

    Cutting a line at its first hash looked like comment-stripping and was not. A hash inside a
    quoted argument — `printf "#9001 900\\n" | gate.py` — truncated the command to
    `bash -c 'printf "`, and that FRAGMENT was then executed and its exit code compared against
    the documented one. An unterminated quote makes bash exit 2, and the block in question
    documents exit 2, so the truncated command MATCHED and was counted as a verified proof while
    running nothing at all. Fifteen documented lines in this pack carry a hash inside quotes.

    A hash only opens a shell comment at the start of an unescaped word. That makes the word
    boundary semantic: the space in `foo\\ #bar` is data and the hash stays in the same word.
    ANSI-C quotes have their own escape rules (`$'\\' #'` contains a protected hash), while
    locale quotes (`$"...") behave like double quotes. The lexer keeps the original bytes; it
    only identifies the point where an actual shell comment starts.
    """
    out = []
    quote = None
    at_word_start = True
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            out.append(ch)
            if ch == "\\" and quote in ('"', "locale", "ansi", "backtick") and i + 1 < len(line):
                i += 1
                out.append(line[i])
            elif ((quote == "single" and ch == "'")
                  or (quote in ('"', "locale") and ch == '"')
                  or (quote == "ansi" and ch == "'")
                  or (quote == "backtick" and ch == "`")):
                quote = None
        elif ch == "\\" and i + 1 < len(line):
            out.append(ch)
            i += 1
            out.append(line[i])
            at_word_start = False
        elif line.startswith("$'", i):
            out.extend(("$", "'"))
            i += 1
            quote = "ansi"
            at_word_start = False
        elif line.startswith('$"', i):
            out.extend(("$", '"'))
            i += 1
            quote = "locale"
            at_word_start = False
        elif ch == "'":
            quote = "single"
            out.append(ch)
            at_word_start = False
        elif ch == '"':
            quote = '"'
            out.append(ch)
            at_word_start = False
        elif ch == "`":
            quote = "backtick"
            out.append(ch)
            at_word_start = False
        elif ch == "#" and at_word_start:
            return "".join(out), line[i:]
        else:
            out.append(ch)
            if ch.isspace() or ch in ";|&()<>\n":
                at_word_start = True
            else:
                at_word_start = False
        i += 1
    return "".join(out), ""


def mask_shell_comments(text):
    """Blank active shell comments without changing source offsets or newlines.

    Recursive ``bash -c`` and substitution bodies are shell source again. Feeding their
    comment bytes to the function/evaluator scanners made data after ``#`` look executable;
    deleting the comment outright, on the other hand, would join tokens across a newline and
    miss a definition whose body begins on the next row. Keep every byte position stable and
    preserve newlines while applying the same word-boundary and quoting rules as
    ``split_comment``.
    """
    out = list(text)
    quote = None
    at_word_start = True
    in_comment = False
    word_closers = []
    index = 0
    while index < len(text):
        char = text[index]
        if in_comment:
            if char == "\n":
                in_comment = False
                at_word_start = True
            else:
                out[index] = " "
            index += 1
            continue
        if quote:
            if (char == "\\" and quote in ('"', "locale", "ansi", "backtick")
                    and index + 1 < len(text)):
                index += 2
                continue
            if ((quote == "single" and char == "'")
                    or (quote in ('"', "locale") and char == '"')
                    or (quote == "ansi" and char == "'")
                    or (quote == "backtick" and char == "`")):
                quote = None
            index += 1
            continue
        if char == "\\" and index + 1 < len(text):
            at_word_start = False
            index += 2
            continue
        if text.startswith("$'", index):
            quote = "ansi"
            at_word_start = False
            index += 2
            continue
        if text.startswith('$"', index):
            quote = "locale"
            at_word_start = False
            index += 2
            continue
        if char == "'":
            quote = "single"
            at_word_start = False
        elif char == '"':
            quote = '"'
            at_word_start = False
        elif char == "`":
            quote = "backtick"
            at_word_start = False
        elif char == "(":
            word_closers.append(index > 0 and text[index - 1] in "$<>?*+@!")
            at_word_start = True
        elif char == ")":
            word_closer = word_closers.pop() if word_closers else False
            at_word_start = not word_closer
        elif char == "#" and at_word_start:
            out[index] = " "
            in_comment = True
        else:
            at_word_start = char.isspace() or char in ";|&()<>\n"
        index += 1
    return "".join(out)


def remove_shell_line_continuations(text):
    """Apply Bash's unquoted backslash-newline removal to recursive source.

    Fence extraction already joins physical continuation rows, but a literal ``bash -c``
    operand can introduce new shell source through ANSI-C decoding. Bash removes a
    backslash-newline pair before tokenization outside single/ANSI-C quotes (and inside double,
    locale, and backtick quotes). A pair inside an active comment is inert and remains until the
    comment masker handles it.
    """
    out = []
    quote = None
    in_comment = False
    at_word_start = True
    word_closers = []
    index = 0
    while index < len(text):
        char = text[index]
        if in_comment:
            out.append(char)
            if char == "\n":
                in_comment = False
                at_word_start = True
            index += 1
            continue
        if quote:
            if (char == "\\" and index + 1 < len(text)
                    and text[index + 1] == "\n"
                    and quote in ('"', "locale", "backtick")):
                index += 2
                continue
            out.append(char)
            if (char == "\\" and quote in ('"', "locale", "ansi", "backtick")
                    and index + 1 < len(text)):
                out.append(text[index + 1])
                index += 2
                continue
            if ((quote == "single" and char == "'")
                    or (quote in ('"', "locale") and char == '"')
                    or (quote == "ansi" and char == "'")
                    or (quote == "backtick" and char == "`")):
                quote = None
            index += 1
            continue
        if char == "#" and at_word_start:
            out.append(char)
            in_comment = True
            index += 1
            continue
        if char == "\\" and index + 1 < len(text):
            if text[index + 1] == "\n":
                index += 2
                continue
            out.extend(text[index:index + 2])
            at_word_start = False
            index += 2
            continue
        if text.startswith("$'", index):
            out.extend("$'")
            quote = "ansi"
            at_word_start = False
            index += 2
            continue
        if text.startswith('$"', index):
            out.extend('$"')
            quote = "locale"
            at_word_start = False
            index += 2
            continue
        out.append(char)
        if char == "'":
            quote = "single"
            at_word_start = False
        elif char == '"':
            quote = '"'
            at_word_start = False
        elif char == "`":
            quote = "backtick"
            at_word_start = False
        elif char == "(":
            word_closers.append(index > 0 and text[index - 1] in "$<>?*+@!")
            at_word_start = True
        elif char == ")":
            word_closer = word_closers.pop() if word_closers else False
            at_word_start = not word_closer
        else:
            at_word_start = char.isspace() or char in ";|&()<>\n"
        index += 1
    return "".join(out)


def line_continues(line):
    """Whether Bash removes this physical row's final backslash-newline.

    The backslash must be the final character, unescaped, and outside ordinary single or ANSI-C
    quotes. It remains active inside double quotes. A backslash in a shell comment is data Bash
    never parses, so that row does not continue.
    """
    code, comment = split_comment(line)
    if comment or not code.endswith("\\"):
        return False
    trailing = len(code) - len(code.rstrip("\\"))
    if trailing % 2 == 0:
        return False
    quote = None
    i = 0
    # Exclude the final, candidate continuation backslash from the state scan.
    while i < len(code) - 1:
        ch = code[i]
        if quote:
            if ch == "\\" and quote in ('"', "locale", "ansi", "backtick") and i + 1 < len(code) - 1:
                i += 2
                continue
            if ((quote == "single" and ch == "'")
                    or (quote in ('"', "locale") and ch == '"')
                    or (quote == "ansi" and ch == "'")
                    or (quote == "backtick" and ch == "`")):
                quote = None
            i += 1
            continue
        if ch == "\\" and i + 1 < len(code) - 1:
            i += 2
            continue
        if code.startswith("$'", i):
            quote = "ansi"
            i += 2
            continue
        if code.startswith('$"', i):
            quote = "locale"
            i += 2
            continue
        if ch == "'":
            quote = "single"
        elif ch == '"':
            quote = '"'
        elif ch == "`":
            quote = "backtick"
        i += 1
    return quote not in ("single", "ansi")


def blocks(text):
    """Yield the contents of each ```bash fenced block."""
    for m in re.finditer(r"```(?:bash|sh)\n(.*?)```", text, re.DOTALL):
        yield m.group(1)


# Empty is a value, not an absence of grammar. `PATH=` must be refused like every other unsafe
# binding, while `D=` must replay and clear an earlier block-local value. Requiring `\S` here
# dropped both lines and let the next command run in an environment the block did not state.
ASSIGN = re.compile(r"^\s*\$?\s*([A-Za-z_][A-Za-z0-9_]*)=(.*?)\s*$")
PLACEHOLDER = re.compile(r"<[a-z][a-z0-9._-]*>", re.IGNORECASE)
# `export NAME=value` sets the environment and runs nothing, so an accepted form is replayed
# verbatim rather than treated as a step this tool had to skip.
EXPORT = re.compile(r"^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)=(.*?)\s*$")
# A documented `export` is replayed into the shell that runs the proof. That is safe only for
# variables that change the INPUT/decoding channel (a locale, a Python encoding) — never one
# that redirects which code runs. `export PATH=./fake` in a SKILL.md forged a verified proof by
# shimming the very `python3` the block then invoked; the allowlist the docstring names as
# mitigation #1 was bypassed because `export` is off it. The bare form is handled separately:
# an inherited exported variable keeps that attribute after `PATH=...`, so omitting the keyword
# changes no security property. Replay a safe export name with a safe (metacharacter-free) value;
# REFUSE anything else and report it.
SAFE_ENV = frozenset("""
LANG LANGUAGE LC_ALL LC_CTYPE LC_COLLATE LC_MESSAGES LC_NUMERIC LC_TIME LC_MONETARY
PYTHONUTF8 PYTHONIOENCODING PYTHONLEGACYWINDOWSFSENCODING
""".split())
SAFE_EXPORT_VALUE = re.compile(r"^[A-Za-z0-9_.:@=+/-]*$")
REFUSE = "__REFUSE__"      # sentinel in the `expected` slot: main refuses and reports it

# A bare assignment is not automatically local. Bash preserves the export attribute of an
# inherited variable, so `PATH=./fake:$PATH` changes both command lookup in this shell and the
# environment of the command it launches even though the line contains no `export`. These names
# can redirect which code the proof reaches or inject startup code into a child interpreter.
# Ordinary block-local fixture handles (`D`, `G`, `F`) remain replayable.
UNSAFE_ASSIGNMENT_NAMES = frozenset({
    "BASH_ENV", "CDPATH", "ENV", "GIT_EXEC_PATH", "IFS", "NODE_OPTIONS",
    "PERL5OPT", "PYTHONHOME", "RUBYOPT",
})
UNSAFE_ASSIGNMENT_PREFIXES = ("LD_", "DYLD_")
# These are the two Bash-only spellings, admitted by the `printf` leading-token rule, that can
# mutate the current shell rather than merely write fixture bytes. A function definition can
# replace the later allowlisted command itself; `printf -v` and `%n` can reach the same unsafe
# lookup/startup variables as a bare assignment.
FUNCTION_COMMAND_PREFIX = (
    r"(?:(?:(?:if|elif|while|until|then|else|do)|!|time(?:[ \t]+-p)?|\{)[ \t]+)*"
)
COMMAND_POSITION = re.compile(
    r"(?:^|[;\n()&|])[ \t]*" + FUNCTION_COMMAND_PREFIX + r"$"
)
FOR_ARITHMETIC_POSITION = re.compile(r"(?:^|[;\n()&|])[ \t]*for[ \t]*$")
FUNCTION_SETUP = re.compile(
    r"(?:^|[;\n()&|])[ \t]*" + FUNCTION_COMMAND_PREFIX
    + r"[^\s(){};&|=]+[ \t]*\([ \t]*\)"
)
FUNCTION_KEYWORD_SETUP = re.compile(
    r"(?:^|[;\n()&|])[ \t]*" + FUNCTION_COMMAND_PREFIX
    + r"function[ \t]+[^\s(){};&|=]+(?:[ \t]*\([ \t]*\))?[ \t]*"
    + r"(?:\s*\{|\s*[(]|\s*\[\[|\s*if\b|\s*while\b|\s*until\b|\s*for\b|"
    + r"\s*select\b|\s*case\b)"
)
PRINTF_FLAGS = frozenset("-+ #0'")
PRINTF_LENGTH_MODIFIERS = frozenset("hlLjzt")
PRINTF_CONVERSIONS = frozenset("diouxXfFeEgGaAcsbqTn")


def safe_export(name, value):
    """Only a locale/encoding export with a plain value may enter a proof's environment."""
    return name in SAFE_ENV and bool(SAFE_EXPORT_VALUE.match(value))


def unsafe_assignment(name):
    """Whether a bare assignment can redirect lookup or inject child startup behavior."""
    return (
        name == "PATH"
        or name.endswith("PATH")
        or name in UNSAFE_ASSIGNMENT_NAMES
        or name.startswith(UNSAFE_ASSIGNMENT_PREFIXES)
    )


def printf_argument_roles(format_text):
    """Return one bool per argument consumed by a literal Bash printf format.

    True is a `%n` target; False is an ordinary value (including `*` width/precision). The
    caller only needs to know whether any variable-writing role exists.
    """
    roles = []
    i = 0
    while i < len(format_text):
        if format_text[i] != "%":
            i += 1
            continue
        if i + 1 < len(format_text) and format_text[i + 1] == "%":
            i += 2
            continue
        j = i + 1
        while j < len(format_text) and format_text[j] in PRINTF_FLAGS:
            j += 1
        if j < len(format_text) and format_text[j] == "*":
            roles.append(False)
            j += 1
        else:
            while j < len(format_text) and format_text[j].isdigit():
                j += 1
        if j < len(format_text) and format_text[j] == ".":
            j += 1
            if j < len(format_text) and format_text[j] == "*":
                roles.append(False)
                j += 1
            else:
                while j < len(format_text) and format_text[j].isdigit():
                    j += 1
        while j < len(format_text) and format_text[j] in PRINTF_LENGTH_MODIFIERS:
            j += 1
        if j < len(format_text) and format_text[j] in PRINTF_CONVERSIONS:
            roles.append(format_text[j] == "n")
            i = j + 1
        else:
            # Malformed/extended syntax cannot establish a target in this small static reading.
            i += 1
    return roles


def shell_syntax_view(text):
    """Keep shell syntax outside quotes while masking syntax-shaped quoted data.

    Bash permits quoted and escaped function names, so their ordinary characters stay visible;
    parentheses and command separators inside a quoted Python/string payload do not. Command,
    process, and backtick substitutions run in child contexts, so this outer view masks them;
    ``shell_function_definition`` inspects their executable bodies separately and recursively.
    """
    out = []
    quote = None
    i = 0
    syntax = frozenset("(){};&|[]<>\n")
    while i < len(text):
        if quote == "backtick":
            if text[i] == "\\" and i + 1 < len(text):
                out.extend("  ")
                i += 2
            elif text[i] == "`":
                out.append(" ")
                quote = None
                i += 1
            else:
                out.append(" ")
                i += 1
            continue
        if quote:
            ch = text[i]
            closing = "'" if quote in ("single", "ansi") else '"'
            if ch == "\\" and quote == "ansi" and i + 1 < len(text):
                out.extend("  ")
                i += 2
            elif ch == closing:
                out.append(ch)
                quote = None
                i += 1
            elif ch == "\\" and quote not in ("single", "ansi") and i + 1 < len(text):
                out.append(" ")
                out.append(" " if text[i + 1] in syntax else text[i + 1])
                i += 2
            else:
                out.append(" " if ch in syntax else ch)
                i += 1
            continue
        if text.startswith(("$(", "<(", ">("), i):
            end = matching_substitution_paren(text, i + 1)
            if end is not None:
                out.extend(" " * (end + 1 - i))
                i = end + 1
                continue
        if text.startswith("$'", i):
            out.extend("$'")
            quote = "ansi"
            i += 2
            continue
        if text.startswith('$"', i):
            out.extend('$"')
            quote = "locale"
            i += 2
            continue
        if text[i] == "'":
            out.append(text[i])
            quote = "single"
        elif text[i] == '"':
            out.append(text[i])
            quote = "double"
        elif text[i] == "`":
            out.append(" ")
            quote = "backtick"
        elif text[i] == "\\" and i + 1 < len(text):
            out.append(text[i])
            out.append(" " if text[i + 1] in syntax else text[i + 1])
            i += 2
            continue
        else:
            out.append(text[i])
        i += 1
    return "".join(out)


def mask_span(chars, start, end):
    """Blank one non-command grammar region without moving later source offsets."""
    for index in range(start, end):
        if chars[index] != "\n":
            chars[index] = " "


def data_closer_tables(text):
    """Precompute every data-context closer used by the shell masker in linear time."""
    paired = {opener: [None] * len(text) for opener in "({["}
    openings = {opener: [] for opener in paired}
    closer_to_opener = {")": "(", "}": "{", "]": "["}
    for index, char in enumerate(text):
        if char in openings:
            openings[char].append(index)
        elif char in closer_to_opener:
            opener = closer_to_opener[char]
            if openings[opener]:
                paired[opener][openings[opener].pop()] = index

    line_brackets = [None] * len(text)
    exact_double_brackets = [None] * len(text)
    next_line_bracket = None
    next_double_bracket = None
    for index in range(len(text) - 1, -1, -1):
        if text[index] == "\n":
            next_line_bracket = None
        elif text[index] == "]":
            next_line_bracket = index
        line_brackets[index] = next_line_bracket
        if index + 1 < len(text) and text[index:index + 2] == "]]":
            next_double_bracket = index
        exact_double_brackets[index] = next_double_bracket

    paired["line]"] = line_brackets
    paired["]]"] = exact_double_brackets
    return paired


COMMAND_PREFIX_TOKENS = (
    "if", "elif", "while", "until", "then", "else", "do", "!", "time", "{",
)
COMMAND_PREFIX_INITIAL = frozenset({"between"})
FOR_PREFIX_INITIAL = "leading"


def advance_command_prefix(states, char):
    """Advance the finite recognizer for ``COMMAND_POSITION`` by one character.

    A regex over the whole suffix made every unmatched ``[[`` rescan all preceding bytes.
    The prefix language is regular, so retaining its possible states makes each position an
    O(1) update.  ``time`` has two live interpretations after whitespace: a completed prefix
    token, or the start of its optional ``-p`` operand.
    """
    advanced = set()
    for state in states:
        if state == "between":
            if char in " \t":
                advanced.add("between")
                continue
            for token in COMMAND_PREFIX_TOKENS:
                if char != token[0]:
                    continue
                if len(token) == 1:
                    advanced.add("needs-space")
                else:
                    advanced.add((token, 1))
        elif isinstance(state, tuple):
            token, offset = state
            if char == token[offset]:
                offset += 1
                if offset == len(token):
                    advanced.add(
                        "time-needs-space" if token == "time" else "needs-space"
                    )
                else:
                    advanced.add((token, offset))
        elif state == "needs-space":
            if char in " \t":
                advanced.add("between")
        elif state == "time-needs-space":
            if char in " \t":
                advanced.update({"between", "time-option-space"})
        elif state == "time-option-space":
            if char in " \t":
                advanced.add("time-option-space")
            elif char == "-":
                advanced.add("time-option-dash")
        elif state == "time-option-dash" and char == "p":
            advanced.add("needs-space")
    return frozenset(advanced)


def advance_for_prefix(state, char):
    """Advance the finite recognizer for ``FOR_ARITHMETIC_POSITION``."""
    if state == "leading":
        if char in " \t":
            return state
        return "f" if char == "f" else "dead"
    if state == "f":
        return "fo" if char == "o" else "dead"
    if state == "fo":
        return "done" if char == "r" else "dead"
    if state == "done":
        return state if char in " \t" else "dead"
    return "dead"


def advance_command_context(command_states, for_state, char):
    """Advance both command-prefix recognizers, restarting after a shell boundary."""
    if char in ";\n()&|":
        return COMMAND_PREFIX_INITIAL, FOR_PREFIX_INITIAL
    return (
        advance_command_prefix(command_states, char),
        advance_for_prefix(for_state, char),
    )


def advance_masked_context(command_states, for_state, chars, start, end):
    """Advance prefix recognizers across an already blanked non-command region."""
    for index in range(start, end):
        command_states, for_state = advance_command_context(
            command_states, for_state, chars[index]
        )
    return command_states, for_state


def array_assignment_opening(text, start, closing_brackets):
    """Opening ``(`` for an array assignment beginning at ``start``, or None.

    This is the bounded equivalent of matching ``NAME[anything]+=(...``. Looking for a missing
    subscript closer from every word start made ``a[a[a[...``
    rescan the whole remaining line at each ``a``. The precomputed closer table keeps every
    lookup constant-time while preserving the old first-``]`` and same-line grammar.
    """
    index = start + 1
    while index < len(text) and (
            text[index] == "_" or (text[index].isascii() and text[index].isalnum())):
        index += 1
    if index < len(text) and text[index] == "[":
        closing = closing_brackets[index]
        if closing is None:
            return None
        index = closing + 1
    if text.startswith("+=", index):
        index += 2
    elif index < len(text) and text[index] == "=":
        index += 1
    else:
        return None
    while index < len(text) and text[index] in " \t":
        index += 1
    return index if index < len(text) and text[index] == "(" else None


def mask_noncommand_contexts(syntax):
    """Mask Bash regions whose punctuation is data, not a command boundary.

    ``shell_syntax_view`` has already hidden quotes and executable substitutions. Arrays,
    arithmetic commands, and ``[[ ... ]]`` regex/conditional operands are the remaining places
    where an unquoted ``(``, ``)``, or function-shaped word is data rather than shell command
    grammar. Keeping this distinction here prevents safe argv and array fixtures from being
    refused while leaving subshell and case-branch boundaries visible.
    """
    chars = list(syntax)
    closers = data_closer_tables(syntax)
    command_states = COMMAND_PREFIX_INITIAL
    for_state = FOR_PREFIX_INITIAL
    index = 0
    while index < len(chars):
        if syntax.startswith("${", index):
            end = closers["{"][index + 1]
            if end is not None:
                mask_span(chars, index, end + 1)
                command_states, for_state = advance_masked_context(
                    command_states, for_state, chars, index, end + 1
                )
                index = end + 1
                continue
        if syntax.startswith("$[", index):
            end = closers["["][index + 1]
            if end is not None:
                mask_span(chars, index, end + 1)
                command_states, for_state = advance_masked_context(
                    command_states, for_state, chars, index, end + 1
                )
                index = end + 1
                continue
        array_word_start = (
            syntax[index] in "_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            and (index == 0 or not (
                syntax[index - 1].isalnum() or syntax[index - 1] == "_"
            ))
        )
        opening = (
            array_assignment_opening(syntax, index, closers["line]"])
            if array_word_start else None
        )
        if opening is not None:
            end = closers["("][opening]
            if end is not None:
                mask_span(chars, opening, end + 1)
                index = end + 1
                # An array assignment can prefix a following command (`ARGS=(x) tool`).
                # Treat the resolved assignment as the start boundary for that command's
                # position; declaration builtins merely make the same conservative masking
                # classify their later operands as data.
                command_states = COMMAND_PREFIX_INITIAL
                for_state = FOR_PREFIX_INITIAL
                continue
        if (index + 1 < len(chars) and syntax[index] in "?*+@!"
                and syntax[index + 1] == "("):
            end = closers["("][index + 1]
            if end is not None:
                mask_span(chars, index, end + 1)
                command_states, for_state = advance_masked_context(
                    command_states, for_state, chars, index, end + 1
                )
                index = end + 1
                continue
        if (syntax.startswith("[[", index)
                and "between" in command_states):
            end = closers["]]"][index + 2] if index + 2 < len(syntax) else None
            if end is not None:
                mask_span(chars, index, end + 2)
                index = end + 2
                command_states = COMMAND_PREFIX_INITIAL
                for_state = FOR_PREFIX_INITIAL
                continue
        if (syntax.startswith("((", index)
                and ("between" in command_states or for_state == "done")):
            end = closers["("][index]
            if end is not None:
                mask_span(chars, index, end + 1)
                index = end + 1
                command_states = COMMAND_PREFIX_INITIAL
                for_state = FOR_PREFIX_INITIAL
                continue
        command_states, for_state = advance_command_context(
            command_states, for_state, chars[index]
        )
        index += 1
    return "".join(chars)


def has_active_heredoc(text):
    """Whether source contains a real heredoc operator outside inert shell data.

    A literal child program can carry arbitrarily shaped heredoc payload rows. This verifier
    intentionally refuses that grammar instead of scanning payload bytes as commands. Here
    strings (``<<<``), quoted text, arithmetic shifts, and conditional operands are not
    heredocs and remain admissible.
    """
    source = mask_shell_comments(remove_shell_line_continuations(text))
    syntax = mask_noncommand_contexts(shell_syntax_view(source))
    return re.search(r"(?<!<)<<-?(?!<)", syntax) is not None


def shell_command_segments(text):
    """Yield outer simple-command source spans while preserving quoted argv bytes."""
    syntax = mask_noncommand_contexts(shell_syntax_view(text))
    start = 0
    index = 0
    while index < len(syntax):
        char = syntax[index]
        separator = char in ";|()\n"
        if char == "|" and index > 0 and syntax[index - 1] == ">":
            separator = False
        if char == "&":
            separator = not (
                (index > 0 and syntax[index - 1] in "<>")
                or (index + 1 < len(syntax) and syntax[index + 1] == ">")
            )
        if separator:
            if start < index:
                yield text[start:index]
            start = index + 1
        index += 1
    if start < len(text):
        yield text[start:]


COMMAND_PREFIX_WORDS = frozenset({
    "{", "if", "elif", "while", "until", "then", "else", "do", "!", "coproc",
})
DYNAMIC_SHELL_CHARS = frozenset("$`*?[]{}~()")
BRACE_SEQUENCE_CHARS = frozenset(
    ",.+-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
)
SHELL_MARKER_ESCAPE = "\ue000"
SHELL_MARKER_CODES = tuple(chr(0xE100 + index) for index in range(256))
BRACE_SEQUENCE_BASIC = re.compile(
    r"(?:[+-]?[0-9]+\.\.[+-]?[0-9]+|[A-Za-z]\.\.[A-Za-z])\Z"
)
BRACE_SEQUENCE_INCREMENT = re.compile(
    r"(?:[+-]?[0-9]+\.\.[+-]?[0-9]+|[A-Za-z]\.\.[A-Za-z])"
    r"\.\.[+-]?[0-9]+\Z"
)


def resolve_shell_executable(name):
    """Absolute shell invocation path selected at startup, or ``None``.

    Validate the resolved target but preserve the selected pathname. Invocation basename can
    change shell compatibility behavior (notably Bash reached as ``sh``), so replacing a
    startup-selected symlink with its target would probe a different mode than replay uses.
    """
    selected = shutil.which(name)
    if selected is None or not os.path.isabs(selected):
        return None
    # Preserve the exact absolute spelling that the OS will execute. Textual normalization of
    # ``alias/../bash`` is not execution-equivalent when ``alias`` is a symlink: the kernel
    # resolves the symlink before ``..``. Collapsing it here can bind the probe to one shell and
    # later classify a different shell as exact.
    invocation = selected
    try:
        resolved = Path(invocation).resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        return None
    return invocation


BASH_EXECUTABLE = resolve_shell_executable("bash")
SH_EXECUTABLE = resolve_shell_executable("sh")


def replay_bash_environment():
    """Environment shared by the semantic probe and every proof-shell execution.

    Inherited startup hooks or exported functions can rewrite a non-interactive Bash before
    the repository command runs. Interpreter/module search variables can similarly replace a
    proof executable without appearing in the document. Preserve the caller's executable PATH
    and ordinary inputs, but remove ambient code-injection channels so the fixed probe and the
    replay have the same clean startup boundary.
    """
    blocked = {
        "BASHOPTS", "BASH_COMPAT", "BASH_ENV", "BASH_XTRACEFD", "CDPATH", "ENV",
        "GLOBIGNORE", "NODE_OPTIONS", "PERL5OPT", "POSIXLY_CORRECT", "PYTHONHOME",
        "RUBYOPT", "SHELLOPTS",
    }
    environment = {}
    for name, value in os.environ.items():
        if name in blocked or name.startswith(("BASH_FUNC_", "LD_", "DYLD_")):
            continue
        if name != "PATH" and name.endswith("PATH"):
            continue
        environment[name] = value
    return environment


BASH_REPLAY_ENV = replay_bash_environment()


def probe_shell_brace_profile(executable):
    """Measure fixed brace semantics for one startup-bound shell executable.

    Bash releases disagree at two security-relevant boundaries. Legacy releases stop the
    entire word at the first malformed sequence candidate; intermediate releases continue in
    its postamble; newer releases validate a candidate before selecting it and can therefore
    reach a nested candidate. Bash 3.2 also predates sequence increments. Version strings do
    not describe those boundaries reliably, so a fixed, data-independent probe is stronger
    than a version table and never evaluates repository-supplied text.

    ``unknown`` is a conservative profile used only if an interpreter cannot be measured safely.
    The classifier takes the union of the three known policies rather than risk a false clean.
    Normal proof execution uses the exact probed executable and scrubbed environment.
    """
    script = (
        "printf 'A:%s\\n' {foo..bar}{1..2}; "
        "printf 'B:%s\\n' {foo..{1..2}}; "
        "printf 'C:%s\\n' {1..3..2}; "
        "printf 'D:%s\\n' {a,b}"
    )
    if executable is None:
        return "unknown", True
    try:
        completed = subprocess.run(
            [executable, "-c", script],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=BASH_REPLAY_ENV,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown", True
    if completed.returncode != 0 or completed.stderr:
        return "unknown", True
    try:
        rows = completed.stdout.decode("utf-8").splitlines()
    except UnicodeError:
        return "unknown", True
    if any(len(row) < 2 or row[0] not in "ABCD" or row[1] != ":" for row in rows):
        return "unknown", True
    groups = {
        label: [row[2:] for row in rows if row.startswith(label + ":")]
        for label in "ABCD"
    }
    legacy_a = ["{foo..bar}{1..2}"]
    expanded_a = ["{foo..bar}1", "{foo..bar}2"]
    literal_b = ["{foo..{1..2}}"]
    expanded_b = ["{foo..1}", "{foo..2}"]
    if groups["D"] == ["{a,b}"]:
        if (groups["A"] == legacy_a and groups["B"] == literal_b
                and groups["C"] == ["{1..3..2}"]):
            return "disabled", False
        return "unknown", True
    if groups["D"] != ["a", "b"]:
        return "unknown", True
    if groups["A"] == legacy_a and groups["B"] == literal_b:
        mode = "legacy"
    elif groups["A"] == expanded_a:
        if groups["B"] == literal_b:
            mode = "postamble"
        elif groups["B"] == expanded_b:
            mode = "validated"
        else:
            mode = "unknown"
    else:
        mode = "unknown"
    increment = groups["C"] == ["1", "3"]
    if groups["C"] not in (["1", "3"], ["{1..3..2}"]):
        mode = "unknown"
        increment = True
    if mode == "unknown":
        increment = True
    return mode, increment


def probe_bash_brace_profile():
    """Compatibility entry point for the fixed proof-shell brace probe."""
    return probe_shell_brace_profile(BASH_EXECUTABLE)


BASH_BRACE_MODE, BASH_BRACE_INCREMENT = probe_bash_brace_profile()
SH_BRACE_MODE, SH_BRACE_INCREMENT = probe_shell_brace_profile(SH_EXECUTABLE)


class ShellWord(str):
    """A resolved static argv word that remembers whether Bash expands its source spelling."""

    def __new__(cls, value, *, dynamic=False):
        instance = super().__new__(cls, value)
        instance.dynamic = dynamic
        return instance


def shell_marker_maps():
    """Return quoted/escaped sentinels, their decode table, and the empty-quote marker."""
    originals = "<>|" + "".join(sorted(DYNAMIC_SHELL_CHARS | BRACE_SEQUENCE_CHARS))
    needed = 2 * len(originals) + 1
    if needed > len(SHELL_MARKER_CODES):
        raise RuntimeError("shell-token provenance alphabet is too small")
    quoted_codes = SHELL_MARKER_CODES[:len(originals)]
    escaped_codes = SHELL_MARKER_CODES[len(originals):2 * len(originals)]
    protected_quoted = {
        original: SHELL_MARKER_ESCAPE + code
        for original, code in zip(originals, quoted_codes)
    }
    protected_escaped = {
        original: SHELL_MARKER_ESCAPE + code
        for original, code in zip(originals, escaped_codes)
    }
    restored = {
        code: original
        for codes in (quoted_codes, escaped_codes)
        for original, code in zip(originals, codes)
    }
    quote_code = SHELL_MARKER_CODES[2 * len(originals)]
    restored[quote_code] = ""
    return (
        protected_quoted,
        protected_escaped,
        restored,
        SHELL_MARKER_ESCAPE + quote_code,
        frozenset(quoted_codes),
    )


def protect_quoted_redirections(text, protected_redirections):
    """Keep quoted/escaped ``<`` and ``>`` distinguishable from redirection operators."""
    syntax = shell_syntax_view(text)
    out = list(text)
    for index, char in enumerate(out):
        if syntax[index] != " ":
            continue
        if char in protected_redirections:
            out[index] = protected_redirections[char]
    return "".join(out)


def protect_inert_shell_expansions(
        text, protected_quoted, protected_escaped, protected_quote):
    """Hide quoted/escaped expansion grammar while leaving active spelling visible.

    ``shlex`` returns the correct resolved characters but discards the very quote and escape
    provenance needed to distinguish a literal ``'/dev/std?n'`` from the glob ``/dev/std?n``.
    Brace sequences need the same bit for their comma, dots, signs, digits, endpoints, and even
    an empty quote boundary: ``{a\",\"b}``, ``{1..'3'}``, and ``{a''..z}`` are data, not
    expansions. Private-use sentinels preserve that provenance through tokenization and restore
    the empty-quote marker to no output bytes. ANSI-C words have already been normalized to
    static single-quoted text; locale words have become double-quoted text, whose dollar and
    backtick expansions correctly remain active.
    """
    out = []
    quote = None
    brace_depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if quote == "single":
            if char == "'":
                quote = None
                out.append(char)
            else:
                inert = DYNAMIC_SHELL_CHARS
                if brace_depth:
                    inert |= BRACE_SEQUENCE_CHARS
                out.append(protected_quoted[char] if char in inert else char)
            index += 1
            continue
        if quote == "double":
            if char == '"':
                quote = None
                out.append(char)
                index += 1
                continue
            if char == "\\" and index + 1 < len(text):
                escaped = text[index + 1]
                if escaped in "$`":
                    out.append(protected_escaped[escaped])
                    index += 2
                    continue
                double_inert = DYNAMIC_SHELL_CHARS - frozenset("$`")
                if brace_depth:
                    double_inert |= BRACE_SEQUENCE_CHARS
                if escaped in double_inert:
                    # In double quotes Bash preserves this backslash as data. Protect the
                    # following punctuation without changing the resolved word itself.
                    out.extend((char, protected_escaped[escaped]))
                    index += 2
                    continue
                out.extend((char, escaped))
                index += 2
                continue
            double_inert = DYNAMIC_SHELL_CHARS - frozenset("$`")
            if brace_depth:
                double_inert |= BRACE_SEQUENCE_CHARS
            out.append(protected_quoted[char] if char in double_inert else char)
            index += 1
            continue
        if char == "\\" and index + 1 < len(text):
            escaped = text[index + 1]
            if (escaped in DYNAMIC_SHELL_CHARS
                    or (brace_depth and escaped in BRACE_SEQUENCE_CHARS)):
                out.append(protected_escaped[escaped])
            else:
                out.extend((char, escaped))
            index += 2
            continue
        if char == "'":
            if brace_depth:
                out.append(protected_quote)
            quote = "single"
        elif char == '"':
            if brace_depth:
                out.append(protected_quote)
            quote = "double"
        elif char == "{":
            brace_depth += 1
        elif char == "}" and brace_depth:
            brace_depth -= 1
        out.append(char)
        index += 1
    return "".join(out)


def restore_shell_markers(word, restored_markers):
    """Decode provenance sentinels without deciding whether the source word is dynamic."""
    restored = []
    index = 0
    while index < len(word):
        char = word[index]
        if char != SHELL_MARKER_ESCAPE or index + 1 >= len(word):
            restored.append(char)
            index += 1
            continue
        code = word[index + 1]
        if code == SHELL_MARKER_ESCAPE:
            restored.append(SHELL_MARKER_ESCAPE)
        elif code in restored_markers:
            restored.append(restored_markers[code])
        else:
            # The encoder doubles every literal escape character, so this cannot be its
            # output. Preserve an unexpected pair instead of deleting source bytes.
            restored.extend((SHELL_MARKER_ESCAPE, code))
        index += 2
    return "".join(restored)


def shell_word_has_brace_expansion(
        word, restored_markers, quoted_marker_codes,
        brace_mode=None, brace_increment=None):
    """Whether an unquoted shell word contains Bash brace-expansion grammar.

    Bare balanced braces are ordinary data: ``{X}``, ``{{}}``, and the conventional xargs
    replacement words ``-I{X}``/``-I{{}}`` do not expand. Bash first *selects* a candidate whose
    own level contains an unquoted comma or an active ``..`` pair. Only then does it validate a
    sequence. That ordering is load-bearing: on Bash 3.2, ``{foo..bar}{1..3}`` is one literal
    word because the malformed first candidate blocks the later valid one, while
    ``{a'.'.c}{1..3}`` expands the later range because its protected dot never formed an active
    delimiter. Quoted/escaped braces and sequence characters have already become provenance
    markers before this scan.

    The fixed startup probe records which of Bash's three shipped continuation policies the
    local interpreter implements and whether it supports sequence increments. Candidate
    metadata and body slices are collected in one pass; every body is sliced at most once and
    every candidate is visited once, preserving the regression suite's linear bound.
    """
    brace_mode = BASH_BRACE_MODE if brace_mode is None else brace_mode
    brace_increment = (
        BASH_BRACE_INCREMENT if brace_increment is None else brace_increment
    )

    # A command invoked as ``sh`` follows the POSIX shell contract and does not perform
    # Bash-style brace expansion. Keep this as an explicit profile instead of borrowing the
    # outer Bash release or the conservative cross-Bash union: both choices can turn inert
    # ``sh -c`` data into a false refusal.
    if brace_mode == "disabled":
        return False

    # After Bash has selected a sequence-shaped candidate, older releases inspect its complete
    # amble for a comma after quote removal. A quoted comma therefore counts there, while an
    # escaped comma remains escaped and does not. Prefix counts make that whole-span question
    # constant-time without copying nested bodies.
    postquote_comma_prefix = [0] * (len(word) + 1)
    comma_count = 0
    marker_index = 0
    while marker_index < len(word):
        char = word[marker_index]
        comma = char == ","
        if (char == SHELL_MARKER_ESCAPE and marker_index + 1 < len(word)):
            code = word[marker_index + 1]
            comma = (
                code in quoted_marker_codes
                and restored_markers.get(code) == ","
            )
        if comma:
            comma_count += 1
        postquote_comma_prefix[marker_index + 1] = comma_count
        marker_index += 1
    for marker_index in range(1, len(postquote_comma_prefix)):
        if postquote_comma_prefix[marker_index] == 0:
            postquote_comma_prefix[marker_index] = postquote_comma_prefix[marker_index - 1]

    stack = []
    candidates = {}
    opening_order = []
    index = 0
    while index < len(word):
        char = word[index]
        if char == "{":
            opening_order.append(index)
            if stack:
                stack[-1]["nested"] = True
            stack.append({
                "open": index,
                "start": index + 1,
                "comma": False,
                "nested": False,
                "dots": None,
            })
        elif char == "}" and stack:
            candidate = stack.pop()
            candidate["close"] = index
            if not candidate["nested"]:
                candidate["body"] = word[candidate["start"]:index]
            candidate["sequence"] = (
                candidate["dots"] is not None
                and candidate["dots"] + 2 != index
            )
            candidate["postquote_comma"] = (
                postquote_comma_prefix[index]
                > postquote_comma_prefix[candidate["start"]]
            )
            candidates[candidate["open"]] = candidate
        elif stack and char == ",":
            stack[-1]["comma"] = True
        elif (stack and char == "." and index + 1 < len(word)
                and word[index + 1] == "." and stack[-1]["dots"] is None):
            stack[-1]["dots"] = index
        index += 1

    def sequence_is_valid(candidate, increment_supported):
        body = candidate.get("body")
        if body is None:
            return False
        if BRACE_SEQUENCE_BASIC.fullmatch(body):
            return True
        return bool(
            increment_supported
            and BRACE_SEQUENCE_INCREMENT.fullmatch(body)
        )

    def evaluate(mode, increment_supported):
        minimum_opening = -1
        for opening in opening_order:
            if opening <= minimum_opening or opening not in candidates:
                continue
            candidate = candidates[opening]
            if candidate["comma"]:
                return True
            if not candidate["sequence"]:
                continue
            # Validated-candidate Bash tests the sequence before selecting it. Older releases
            # select first; once selected, even a nested or quoted comma in the amble changes
            # the word before an invalid sequence can block it.
            if mode != "validated" and candidate["postquote_comma"]:
                return True
            if sequence_is_valid(candidate, increment_supported):
                return True
            if mode == "legacy":
                return False
            if mode == "postamble":
                # Intermediate Bash releases resume only after the malformed candidate's
                # closing brace; nested candidates are part of the literal prefix.
                minimum_opening = candidate["close"]
            # Validated Bash continues at the next opening, including a nested one.
        return False

    if brace_mode == "unknown":
        # Unknown child interpreters are evaluated as the union of the three measured Bash
        # policies. This refuses a word that any supported family could expand without turning
        # every isolated malformed sequence into a false positive.
        return any(
            evaluate(mode, True)
            for mode in ("legacy", "postamble", "validated")
        )
    return evaluate(brace_mode, brace_increment)


def restore_shell_word(
        word, restored_markers, quoted_marker_codes,
        brace_mode=None, brace_increment=None):
    """Restore protected data and retain whether the source word expands at runtime."""
    non_brace_dynamic = DYNAMIC_SHELL_CHARS - frozenset("{}")
    dynamic = (
        any(char in non_brace_dynamic for char in word)
        or shell_word_has_brace_expansion(
            word,
            restored_markers,
            quoted_marker_codes,
            brace_mode,
            brace_increment,
        )
    )
    return ShellWord(restore_shell_markers(word, restored_markers), dynamic=dynamic)


def skip_leading_redirection(words, index):
    """Index after one command-prefix redirection, or the unchanged index."""
    if index >= len(words):
        return index
    operators = {"<", ">", "|"}
    if (words[index] == "&" and index + 1 < len(words)
            and set(words[index + 1]) <= operators
            and any(char in "<>" for char in words[index + 1])):
        index += 1
    if (index + 1 < len(words)
            and (words[index].isdigit() or re.fullmatch(r"\{[A-Za-z_][A-Za-z0-9_]*\}", words[index]))
            and words[index + 1] and set(words[index + 1]) <= operators
            and any(char in "<>" for char in words[index + 1])):
        index += 1
    if (index >= len(words) or not words[index]
            or not set(words[index]) <= operators
            or not any(char in "<>" for char in words[index])):
        return index
    if (words[index] in {"<", ">"} and index + 1 < len(words)
            and words[index + 1] == "&"):
        return min(len(words), index + 3)
    # Every redirection operator here consumes one following word: path, descriptor, delimiter,
    # or here-string payload. Malformed source with none cannot execute a hidden command either.
    return min(len(words), index + 2)


def without_shell_redirections(words):
    """Remove syntax redirections and their operands wherever Bash permits them in argv."""
    out = []
    index = 0
    while index < len(words):
        redirected = skip_leading_redirection(words, index)
        if redirected != index:
            index = redirected
            continue
        out.append(words[index])
        index += 1
    return out


def shell_segment_argv(
        segment, preserve_assignments=False, brace_mode=None, brace_increment=None):
    """The executable-position argv in one outer shell segment, or an empty list.

    Leading assignment words normally are shell syntax rather than child argv. The unsafe-state
    evaluator can ask to retain them long enough to inspect names such as ``BASH_ENV`` and
    ``PATH``; wrapper unwrapping removes them again before interpreting the child command.
    """
    try:
        normalized = normalize_ansi_c_quotes(segment)
        (
            protected_quoted,
            protected_escaped,
            restored_markers,
            protected_quote,
            quoted_marker_codes,
        ) = shell_marker_maps()
        protected_redirections = {
            char: protected_quoted[char] for char in "<>|"
        }
        protected_quoted_inert = {
            char: protected_quoted[char]
            for char in DYNAMIC_SHELL_CHARS | BRACE_SEQUENCE_CHARS
        }
        protected_escaped_inert = {
            char: protected_escaped[char]
            for char in DYNAMIC_SHELL_CHARS | BRACE_SEQUENCE_CHARS
        }
        escaped = normalized.replace(SHELL_MARKER_ESCAPE, SHELL_MARKER_ESCAPE * 2)
        protected = protect_inert_shell_expansions(
            protect_quoted_redirections(escaped, protected_redirections),
            protected_quoted_inert,
            protected_escaped_inert,
            protected_quote,
        )
        lexer = shlex.shlex(
            protected,
            posix=True,
            punctuation_chars="<>|",
        )
        lexer.whitespace_split = True
        lexer.commenters = ""
        words = list(lexer)
    except ValueError:
        return []
    index = 0
    leading_assignments = []
    while index < len(words):
        word = words[index]
        if ASSIGN.fullmatch(word):
            if preserve_assignments:
                leading_assignments.append(word)
            index += 1
            continue
        if word in COMMAND_PREFIX_WORDS:
            index += 1
            continue
        if word == "time":
            index += 1
            if index < len(words) and words[index] == "-p":
                index += 1
            continue
        redirected = skip_leading_redirection(words, index)
        if redirected != index:
            index = redirected
            continue
        break
    argv = leading_assignments + without_shell_redirections(words[index:])
    return [
        restore_shell_word(
            word,
            restored_markers,
            quoted_marker_codes,
            brace_mode,
            brace_increment,
        )
        for word in argv
    ]


XARGS_SHORT_FLAGS = frozenset("0oprtx")
XARGS_SHORT_VALUES = frozenset("adEIJLnPRSs")
XARGS_SHORT_OPTIONAL_VALUES = frozenset("eil")
XARGS_LONG_FLAGS = frozenset({
    "--exit", "--interactive", "--no-run-if-empty", "--null", "--open-tty",
    "--show-limits", "--verbose",
})
XARGS_LONG_VALUES = frozenset({
    "--arg-file", "--delimiter", "--max-args", "--max-chars", "--max-procs",
    "--process-slot-var",
})
XARGS_LONG_OPTIONAL_VALUES = frozenset({"--eof", "--max-lines", "--replace"})
XARGS_TERMINAL_OPTIONS = frozenset({"--help", "--version"})
XARGS_REPLACEMENT_FLAGS = frozenset({"I", "J", "i"})
XARGS_SAFE_LEAF_PROGRAMS = frozenset({"dirname", "printf"})


def xargs_child_argv(argv):
    """Return xargs' literal child argv, or None when its launcher grammar is ambiguous.

    The accepted finite grammar is the union of current BSD and GNU xargs options. Required
    short-option values may be joined or separate; GNU's legacy ``-e``, ``-i``, and ``-l``
    values are optional only when joined. Long required values may use ``=`` or the next word,
    while the three documented optional long values are accepted only with ``=``. Unknown
    options, missing values, and runtime-expanded option words fail closed as ambiguous.

    Only direct Bash/sh children and finite inert data leaves are admitted. In ordinary append
    mode, a direct shell must already have an executable literal ``-c`` operand: an unbounded
    runtime tail can otherwise satisfy a pending ``-O``/``-o``/startup-file option and then
    toggle noexec before supplying source. Child-launching wrappers have the same ambiguity and
    fail closed. Replacement modes retain dynamic provenance on affected words so the
    shell-source classifier refuses a computed script operand.
    """
    argv = list(argv)
    index = 1
    replacement = None
    while index < len(argv):
        option = argv[index]
        if getattr(option, "dynamic", False):
            return None
        option = str(option)
        if option == "--":
            index += 1
            break
        if option == "-" or not option.startswith("-"):
            break
        if option.startswith("--"):
            name, joined, value = option.partition("=")
            if name in XARGS_TERMINAL_OPTIONS:
                return [] if not joined else None
            if name in XARGS_LONG_FLAGS:
                if joined:
                    return None
                index += 1
                continue
            if name in XARGS_LONG_OPTIONAL_VALUES:
                if name == "--replace":
                    marker = value if joined else "{}"
                    if not marker:
                        return None
                    replacement = ("substring", marker)
                index += 1
                continue
            if name not in XARGS_LONG_VALUES:
                return None
            if joined:
                index += 1
            else:
                if index + 1 >= len(argv) or getattr(argv[index + 1], "dynamic", False):
                    return None
                index += 2
            continue

        cluster = option[1:]
        offset = 0
        consumed = False
        while offset < len(cluster):
            flag = cluster[offset]
            if flag in XARGS_SHORT_FLAGS:
                offset += 1
                continue
            if flag in XARGS_SHORT_OPTIONAL_VALUES:
                value = cluster[offset + 1:]
                if flag == "i":
                    marker = value or "{}"
                    replacement = ("substring", marker)
                index += 1
                consumed = True
                break
            if flag not in XARGS_SHORT_VALUES:
                return None
            value = cluster[offset + 1:]
            if value:
                index += 1
            else:
                if index + 1 >= len(argv) or getattr(argv[index + 1], "dynamic", False):
                    return None
                value = str(argv[index + 1])
                index += 2
            if flag in XARGS_REPLACEMENT_FLAGS:
                if not value:
                    return None
                replacement = (
                    "distinct-first" if flag == "J" else "substring",
                    value,
                )
            consumed = True
            break
        if not consumed:
            index += 1

    child = argv[index:]
    if not child:
        return []
    if getattr(child[0], "dynamic", False):
        return None
    affected = set()
    appends_runtime = replacement is None
    if replacement is not None:
        mode, marker = replacement
        if mode == "substring":
            affected = {
                child_index for child_index, word in enumerate(child)
                if marker in str(word)
            }
        else:
            matched = next(
                (child_index for child_index, word in enumerate(child)
                 if str(word) == marker),
                None,
            )
            if matched is None:
                # BSD -J appends input when its marker is absent as a distinct argument.
                appends_runtime = True
            else:
                affected.add(matched)
    if 0 in affected:
        return None
    child_program = os.path.basename(str(child[0]))
    if (child_program not in SHELL_INTERPRETERS
            and child_program not in XARGS_SAFE_LEAF_PROGRAMS):
        return None
    transformed = [
        ShellWord(
            str(word),
            dynamic=(
                getattr(word, "dynamic", False)
                or child_index in affected
            ),
        )
        for child_index, word in enumerate(child)
    ]
    if child_program in SHELL_INTERPRETERS:
        mode, _source, has_c = shell_c_invocation(transformed)
        if mode in {"execute", "terminal"}:
            return transformed
        if mode == "noexec" and (has_c or not appends_runtime):
            return transformed
        if mode == "missing" and not appends_runtime:
            return transformed
        return None
    if appends_runtime:
        # Ordinary append mode and BSD -J without a distinct marker add runtime data after the
        # fixed argv. Preserve one representative dynamic word for admitted inert leaves.
        transformed.append(ShellWord("__xargs_input__", dynamic=True))
    return transformed


def unwrap_shell_command(argv, shell_context=True):
    """Remove literal wrappers, returning None argv for ambiguous launcher grammar."""
    argv = list(argv)
    while True:
        while shell_context and argv and ASSIGN.fullmatch(argv[0]):
            argv.pop(0)
        if not argv:
            return [], shell_context
        program = os.path.basename(argv[0])
        if program == "builtin" and shell_context:
            nested = argv[1:]
            if nested[:1] == ["--"]:
                nested = nested[1:]
            if not nested or nested[0] not in {
                "builtin", "command", "eval", "exec", "source", ".", "trap",
            }:
                return [], shell_context
            argv = nested
            continue
        if program == "command":
            index = 1
            while index < len(argv) and argv[index].startswith("-") and argv[index] != "-":
                if "v" in argv[index][1:] or "V" in argv[index][1:]:
                    return [], shell_context
                if "p" in argv[index][1:]:
                    return None, shell_context
                index += 1
            argv = argv[index:]
            shell_context = True
            continue
        if program == "exec" and shell_context:
            index = 1
            while index < len(argv) and argv[index].startswith("-") and argv[index] != "-":
                if argv[index] == "-a":
                    return None, shell_context
                else:
                    index += 1
            argv = argv[index:]
            continue
        if program == "env":
            argv = env_child_argv(argv)
            if argv is None:
                return None, shell_context
            shell_context = False
            continue
        if program == "nice":
            index = 1
            while index < len(argv) and argv[index].startswith("-") and argv[index] != "-":
                word = argv[index]
                index += 2 if word in {"-n", "--adjustment"} else 1
            argv = argv[index:]
            shell_context = False
            continue
        if program == "stdbuf":
            index = 1
            while index < len(argv) and argv[index].startswith("-") and argv[index] != "-":
                word = argv[index]
                index += 2 if word in {"-i", "--input", "-o", "--output", "-e", "--error"} else 1
            argv = argv[index:]
            shell_context = False
            continue
        if program == "nohup":
            if argv[1:2] and argv[1] in {"--help", "--version"}:
                return [], shell_context
            argv = argv[2:] if len(argv) > 1 and argv[1] == "--" else argv[1:]
            shell_context = False
            continue
        if program == "xargs":
            argv = xargs_child_argv(argv)
            if argv is None:
                return None, shell_context
            shell_context = False
            continue
        break
    return argv, shell_context


def shell_c_invocation(argv):
    """Classify Bash/sh ``-c`` execution and return ``(mode, source, has_c)``.

    ``-O`` and ``-o`` each consume one following word even when combined with ``-c`` (for
    example ``-Oc`` and ``-co``). Both ``-c`` and ``+c`` designate a command string. ``-n`` and
    ``-D`` suppress execution, while ``+n`` can restore it. A runtime-built option or source is
    ambiguous rather than literal.
    """
    index = 1
    noexec_n = False
    noexec_dump = False
    while index < len(argv):
        option = argv[index]
        if getattr(option, "dynamic", False):
            return "ambiguous", None, False
        option = str(option)
        if option in {"--", "-"} or not option.startswith(("-", "+")):
            return (
                ("noexec", None, False)
                if (noexec_n or noexec_dump)
                else ("no-c", None, False)
            )
        if option in {"--help", "--version"}:
            return "terminal", None, False
        if option in {"--dump-strings", "--dump-po-strings"}:
            noexec_dump = True
            index += 1
            continue
        if option.startswith("--"):
            if option in {"--rcfile", "--init-file"}:
                if index + 1 >= len(argv):
                    return "ambiguous", None, False
                index += 2
            else:
                index += 1
            continue
        sign = option[0]
        flags = option[1:]
        if "n" in flags:
            noexec_n = sign == "-"
        noexec_dump = noexec_dump or "D" in flags
        value_count = flags.count("O") + flags.count("o")
        value_end = index + 1 + value_count
        if value_end > len(argv):
            return "ambiguous", None, "c" in flags
        if any(getattr(word, "dynamic", False) for word in argv[index + 1:value_end]):
            return "ambiguous", None, "c" in flags
        if "c" in flags:
            if noexec_n or noexec_dump:
                return "noexec", None, True
            if value_end >= len(argv):
                return "missing", None, True
            source = argv[value_end]
            if getattr(source, "dynamic", False):
                return "ambiguous", None, True
            return "execute", source, True
        index = value_end
    return (
        ("noexec", None, False)
        if (noexec_n or noexec_dump)
        else ("no-c", None, False)
    )


def literal_c_operand(argv):
    """Literal Bash/sh ``-c`` operand when invocation options actually execute it."""
    mode, source, _has_c = shell_c_invocation(argv)
    return source if mode == "execute" else None


def literal_shell_brace_profile(program, brace_mode, brace_increment):
    """Brace profile used by a statically identified literal child shell.

    A bare ``bash`` is resolved by the same frozen PATH used for replay; environment wrappers
    that can redirect that lookup are rejected before this point. The exact startup-bound Bash
    path is likewise the measured interpreter. Bare or exact ``sh`` uses its own startup-bound
    probe because shells—including Bash invoked under that name—do not share one universal
    brace policy. A different absolute shell is not executed merely to identify it and therefore
    keeps the conservative cross-release profile.
    """
    spelling = str(program)
    basename = os.path.basename(spelling)
    if basename not in SHELL_INTERPRETERS:
        return "unknown", True
    if basename == "bash":
        executable = BASH_EXECUTABLE
        profile = (BASH_BRACE_MODE, BASH_BRACE_INCREMENT)
    else:
        executable = SH_EXECUTABLE
        profile = (SH_BRACE_MODE, SH_BRACE_INCREMENT)
    if not os.path.isabs(spelling):
        # Only an unqualified name is selected through the frozen startup PATH. ``./sh`` and
        # ``subdir/bash`` bypass PATH and may name a different interpreter, so they must remain
        # on the conservative profile just like alternate absolute paths.
        if os.sep not in spelling and (os.altsep is None or os.altsep not in spelling):
            return profile
        return "unknown", True
    if executable is not None and spelling == executable:
        return profile
    return "unknown", True


def literal_shell_sources(text, brace_mode=None, brace_increment=None):
    """Yield literal source and profile for command-position Bash/sh ``-c`` execution."""
    for segment in shell_command_segments(text):
        argv, _shell_context = unwrap_shell_command(shell_segment_argv(
            segment,
            brace_mode=brace_mode,
            brace_increment=brace_increment,
        ))
        if argv and os.path.basename(argv[0]) in SHELL_INTERPRETERS:
            source = literal_c_operand(argv)
            if source is not None:
                mode, increment = literal_shell_brace_profile(
                    argv[0], brace_mode, brace_increment
                )
                yield source, mode, increment


IMPORTED_FUNCTION_ENV = re.compile(
    r"^(?:BASH_FUNC_[^=]+%%|[A-Za-z_][A-Za-z0-9_]*)=\(\)[ \t]*\{"
)
ENV_INERT_SHORT_FLAGS = frozenset("iv")
ENV_INERT_LONG_FLAGS = frozenset({"--debug", "--ignore-environment"})
ENV_INERT_SHORT_VALUES = frozenset("u")
ENV_INERT_LONG_VALUES = frozenset({"--unset"})
ENV_UNSAFE_SHORT_OPTIONS = frozenset("PCaS")
ENV_UNSAFE_LONG_OPTIONS = frozenset({
    "--argv0", "--chdir", "--path", "--split-string",
})
ENV_TERMINAL_OPTIONS = frozenset({"--help", "--version"})


def env_child_argv(argv):
    """Return a statically bounded env child argv, or None for unsafe/ambiguous grammar.

    Environment clearing also removes PATH: a later bare child is then searched on the platform
    default rather than the frozen replay path, so that combination fails closed. Removing an
    ordinary variable (or clearing the environment before an absolute child) only subtracts
    ambient state. Explicit search path, chdir, argv0, and split-string options can change which
    program/source is reached and fail closed with unknown or runtime-built option grammar.
    """
    argv = list(argv)
    index = 1
    clears_environment = False
    while index < len(argv):
        option = argv[index]
        if getattr(option, "dynamic", False):
            return None
        option = str(option)
        if option == "--":
            index += 1
            break
        if option == "-":
            # BSD's historical alias for -i clears PATH as well as ambient hooks. A later bare
            # utility is therefore searched on the platform default path, not the frozen replay
            # path. Defer the final decision until the literal child is known.
            clears_environment = True
            index += 1
            continue
        if not option.startswith("-"):
            break
        if option in ENV_TERMINAL_OPTIONS:
            return []
        if option.startswith("--"):
            name, joined, value = option.partition("=")
            if name in ENV_UNSAFE_LONG_OPTIONS:
                return None
            if name in ENV_INERT_LONG_FLAGS:
                if joined:
                    return None
                if name == "--ignore-environment":
                    clears_environment = True
                index += 1
                continue
            if name not in ENV_INERT_LONG_VALUES:
                return None
            if joined:
                if not value:
                    return None
                if name == "--unset" and value == "PATH":
                    return None
                index += 1
            else:
                if index + 1 >= len(argv):
                    return None
                if name == "--unset" and str(argv[index + 1]) == "PATH":
                    return None
                index += 2
            continue

        cluster = option[1:]
        offset = 0
        consumed = False
        while offset < len(cluster):
            flag = cluster[offset]
            if flag in ENV_INERT_SHORT_FLAGS:
                if flag == "i":
                    clears_environment = True
                offset += 1
                continue
            if flag in ENV_UNSAFE_SHORT_OPTIONS:
                return None
            if flag not in ENV_INERT_SHORT_VALUES:
                return None
            value = cluster[offset + 1:]
            if value:
                if flag == "u" and value == "PATH":
                    return None
                index += 1
            else:
                if index + 1 >= len(argv):
                    return None
                if flag == "u" and str(argv[index + 1]) == "PATH":
                    return None
                index += 2
            consumed = True
            break
        if not consumed:
            index += 1

    while index < len(argv):
        word = argv[index]
        if IMPORTED_FUNCTION_ENV.match(word):
            return None
        assignment = ASSIGN.fullmatch(word)
        if not assignment:
            break
        if unsafe_assignment(assignment.group(1)):
            return None
        index += 1
    child = argv[index:]
    if child and getattr(child[0], "dynamic", False):
        return None
    if clears_environment and child and not os.path.isabs(str(child[0])):
        return None
    return child


def unsafe_env_command(argv):
    """Whether command/environment syntax can redirect lookup or import executable state."""
    argv = list(argv)
    index = 0
    while index < len(argv):
        assignment = ASSIGN.fullmatch(argv[index])
        if not assignment:
            break
        if unsafe_assignment(assignment.group(1)):
            return True
        index += 1
    argv = argv[index:]
    while argv:
        program = os.path.basename(argv[0])
        if program == "command":
            index = 1
            while index < len(argv) and argv[index].startswith("-") and argv[index] != "-":
                if "v" in argv[index][1:] or "V" in argv[index][1:]:
                    return False
                if "p" in argv[index][1:]:
                    return True
                index += 1
            argv = argv[index:]
            continue
        if program == "exec":
            index = 1
            while index < len(argv) and argv[index].startswith("-") and argv[index] != "-":
                if argv[index] == "-a":
                    return True
                index += 1
            argv = argv[index:]
            continue
        if program in {"nice", "stdbuf"}:
            index = 1
            value_options = ({"-n", "--adjustment"} if program == "nice" else
                             {"-i", "--input", "-o", "--output", "-e", "--error"})
            while index < len(argv) and argv[index].startswith("-") and argv[index] != "-":
                index += 2 if argv[index] in value_options else 1
            argv = argv[index:]
            continue
        if program == "nohup":
            argv = argv[2:] if len(argv) > 1 and argv[1] == "--" else argv[1:]
            continue
        if program != "env":
            return False
        argv = env_child_argv(argv)
        if argv is None:
            return True
        if not argv:
            return False
    return False


def shell_reads_stdin_source(argv):
    """Whether Bash/sh takes runtime source from stdin, startup hooks, or a computed operand."""
    index = 1
    forced_stdin = False
    noexec_n = False
    noexec_dump = False
    interactive = False
    login = False
    no_rc = False
    no_profile = False
    explicit_startup = False
    debugger = False

    def executable():
        return not (noexec_n or noexec_dump)

    def startup_source():
        # Explicit startup paths and debugger profiles are executable source hooks in their own
        # right. Login and interactive defaults are suppressible only by their documented
        # switches. All are gated by executable() at the return sites so -n/-D stay inert.
        if explicit_startup or debugger:
            return True
        if login:
            return not no_profile
        return interactive and not no_rc

    def stdin_path(word):
        if getattr(word, "dynamic", False):
            return True
        normalized = os.path.normpath(word)
        return bool(
            normalized == "/dev/stdin"
            or re.fullmatch(r"/dev/fd/[^/]+", normalized)
            or re.fullmatch(r"/proc/[^/]+/fd/[^/]+", normalized)
        )

    while index < len(argv):
        option = argv[index]
        if getattr(option, "dynamic", False):
            # A runtime-built word can be either a script operand or an option such as -c/+n.
            # Its effect on execution cannot be established from the literal command.
            return True
        if option.startswith("+") and option != "+":
            flags = option[1:]
            value_count = flags.count("O") + flags.count("o")
            value_end = index + 1 + value_count
            if value_end > len(argv):
                return False
            if any(getattr(word, "dynamic", False) for word in argv[index + 1:value_end]):
                return True
            if "n" in flags:
                noexec_n = False
            noexec_dump = noexec_dump or "D" in flags
            if "s" in flags:
                forced_stdin = False
            if "i" in flags:
                interactive = False
            if "l" in flags:
                login = False
            if "c" in flags:
                return bool(
                    executable()
                    and value_end < len(argv)
                    and (
                        startup_source()
                        or getattr(argv[value_end], "dynamic", False)
                    )
                )
            index = value_end
            continue
        if option == "--":
            if index + 1 >= len(argv):
                return executable()
            return executable() and (
                startup_source() or forced_stdin or stdin_path(argv[index + 1])
            )
        if option == "-":
            return executable()
        if not option.startswith("-"):
            return executable() and (startup_source() or forced_stdin or stdin_path(option))
        if option in {"--help", "--version"}:
            return False
        if option in {"--dump-strings", "--dump-po-strings"}:
            noexec_dump = True
            index += 1
            continue
        if option in {"--rcfile", "--init-file"}:
            explicit_startup = index + 1 < len(argv)
            index += 2
            continue
        if option.startswith(("--rcfile=", "--init-file=")):
            explicit_startup = True
            index += 1
            continue
        if option == "--debugger":
            debugger = True
            index += 1
            continue
        if option == "--login":
            login = True
            index += 1
            continue
        if option == "--norc":
            no_rc = True
            index += 1
            continue
        if option == "--noprofile":
            no_profile = True
            index += 1
            continue
        if option.startswith("--"):
            index += 1
            continue
        flags = option[1:]
        value_count = flags.count("O") + flags.count("o")
        value_end = index + 1 + value_count
        if value_end > len(argv):
            return False
        if any(getattr(word, "dynamic", False) for word in argv[index + 1:value_end]):
            return True
        noexec_n = noexec_n or "n" in flags
        noexec_dump = noexec_dump or "D" in flags
        interactive = interactive or "i" in flags
        login = login or "l" in flags
        if "c" in flags:
            return bool(
                executable()
                and value_end < len(argv)
                and (
                    startup_source()
                    or getattr(argv[value_end], "dynamic", False)
                )
            )
        forced_stdin = forced_stdin or "s" in flags
        index = value_end
    return executable()


def has_dynamic_shell_state_evaluator(
        text, brace_mode=None, brace_increment=None):
    """Whether an actual command position evaluates source in the current shell.

    Eval/source/trap, imported Bash functions, and shell programs supplied over stdin or a
    runtime-computed script operand can define or import a function from runtime-built text.
    There is no static reading that proves such state harmless, so the proof grammar refuses
    these command positions rather than pretending a literal-only scan covers them.
    """
    for segment in shell_command_segments(text):
        raw_argv = shell_segment_argv(
            segment,
            preserve_assignments=True,
            brace_mode=brace_mode,
            brace_increment=brace_increment,
        )
        if unsafe_env_command(raw_argv):
            return True
        argv, shell_context = unwrap_shell_command(raw_argv)
        if argv is None:
            return True
        if not argv:
            continue
        if shell_context and argv[0] in {"eval", "source", "."}:
            return True
        if shell_context and argv[0] == "trap" and argv[1:2] not in ([], ["-p"], ["-l"]):
            return True
        if (os.path.basename(argv[0]) in SHELL_INTERPRETERS
                and shell_reads_stdin_source(argv)):
            return True
    return False


def unsafe_setup_state(cmd):
    """Whether any execution of this runnable can persist unsafe Bash state."""
    if shell_function_definition(cmd):
        return True
    try:
        words = shlex.split(normalize_ansi_c_quotes(cmd))
    except ValueError:
        return False
    if not words or words[0] != "printf" or len(words) < 2:
        return False
    format_index = 1
    target = None
    if words[1] == "--":
        format_index = 2
    elif words[1] == "-v":
        if len(words) < 3:
            return True
        target = words[2]
        format_index = 3
    elif words[1].startswith("-v"):
        target = words[1][2:]
        format_index = 2
    if target is not None:
        # Even a nominally ordinary target can be paired with another `%n` target later in the
        # same format. More importantly, a runnable setup step is isolated below, so promising
        # that any `printf -v` assignment persists would be false. Plain NAME=value is the one
        # supported persistent-variable grammar.
        return True
    if len(words) <= format_index:
        return False
    format_text = words[format_index]
    roles = printf_argument_roles(format_text)
    return True in roles


def shell_function_definition(
        cmd, seen=None, brace_mode=None, brace_increment=None):
    """Whether this source can establish function state before an apparent proof command."""
    brace_mode = BASH_BRACE_MODE if brace_mode is None else brace_mode
    brace_increment = (
        BASH_BRACE_INCREMENT if brace_increment is None else brace_increment
    )
    seen = set() if seen is None else seen
    identity = (cmd, brace_mode, brace_increment)
    if identity in seen:
        return False
    seen.add(identity)
    source = mask_shell_comments(remove_shell_line_continuations(cmd))
    if has_active_heredoc(source):
        return True
    syntax = mask_noncommand_contexts(shell_syntax_view(source))
    if FUNCTION_SETUP.search(syntax) or FUNCTION_KEYWORD_SETUP.search(syntax):
        return True
    if has_dynamic_shell_state_evaluator(source, brace_mode, brace_increment):
        return True
    if any(shell_function_definition(
            body, seen, brace_mode, brace_increment)
            for body in executable_substitutions(source)):
        return True
    # Bare or exact startup-bound Bash and sh each inherit their independently measured profile;
    # an alternate absolute shell stays on the conservative union. No child is executed merely
    # to identify its release.
    return any(shell_function_definition(body, seen, mode, increment)
               for body, mode, increment in literal_shell_sources(
                   source,
                   brace_mode,
                   brace_increment,
               ))


def proof_script(setup, cmd):
    """Compose one proof without inheriting shell state from runnable setup commands."""
    # The setup text is data in the generated outer script. Interpolating it between raw
    # parentheses lets an unmatched `)` close our subshell and resume in the proof shell. Quote
    # it as eval's operand instead: eval parses inside the already-created child, where even
    # malformed/compound syntax cannot escape to mutate the parent.
    prefix = [f"( builtin eval {shlex.quote(step)} )" if is_runnable(step) else step
              for step in setup]
    return "; ".join(prefix + [cmd]) if prefix else cmd


def assignment_value_is_one_word(value):
    """Whether an assignment value is one shell word, allowing quoted/substitution spaces."""
    quote = None
    i = 0
    while i < len(value):
        if quote:
            if quote in ("double", "locale"):
                if value.startswith(("${", "$((", "$["), i):
                    # Parameter assignment and arithmetic assignment still execute inside
                    # double/locale quotes. Treating the quoted spelling as inert let
                    # `SAFE="$((PATH=0))"` poison command lookup in the proof shell.
                    return False
                if value.startswith("$(", i):
                    end = matching_substitution_paren(value, i + 1)
                    if end is None:
                        return False
                    i = end + 1
                    continue
                if value[i] == "`":
                    end = matching_backtick(value, i)
                    if end is None:
                        return False
                    i = end + 1
                    continue
            if value[i] == "\\" and quote != "single" and i + 1 < len(value):
                i += 2
                continue
            closing = "'" if quote in ("single", "ansi") else ('`' if quote == "backtick" else '"')
            if value[i] == closing:
                quote = None
            i += 1
            continue
        if value.startswith(("${", "$((", "$["), i):
            # `${name:=value}` and `$((name=value))` can mutate another variable in this shell;
            # `$[...]` is Bash's legacy spelling of the same arithmetic expansion. Gap all three
            # rather than trying to prove a side-effect-free expression grammar.
            return False
        if value.startswith(("$(", "<(", ">("), i):
            end = matching_substitution_paren(value, i + 1)
            if end is None:
                return False
            i = end + 1
            continue
        if value.startswith("$'", i):
            quote = "ansi"
            i += 2
            continue
        if value.startswith('$"', i):
            quote = "locale"
            i += 2
            continue
        if value[i] == "'":
            quote = "single"
        elif value[i] == '"':
            quote = "double"
        elif value[i] == "`":
            quote = "backtick"
        elif value[i] == "\\" and i + 1 < len(value):
            i += 2
            continue
        elif value[i].isspace() or value[i] in "&|<>":
            return False
        i += 1
    return quote is None


def assignment_sequence(code):
    """Return bindings in the documented one-word assignment grammar, else None."""
    view = shell_syntax_view(code)
    parts = []
    start = 0
    for index, ch in enumerate(view):
        if ch == ";":
            parts.append(code[start:index].strip())
            start = index + 1
    parts.append(code[start:].strip())
    if len(parts) > 1 and not parts[-1]:
        parts.pop()
    if not parts or any(not part for part in parts):
        return None
    bindings = []
    for part in parts:
        matched = ASSIGN.fullmatch(part)
        if not matched or not assignment_value_is_one_word(matched.group(2)):
            return None
        bindings.append((matched.group(1), matched.group(2)))
    return bindings


def command_shaped(body):
    """Is this line a command, even if this tool would not run it?

    A usage TEMPLATE is not one. `cp <prompt.md> <prompt.before.md>` is prose showing the reader
    a shape; nobody ever runs it, and treating it as an unreplayable step demoted every real
    proof below it in the block. An `export VAR=value` is not one either — it is handled as
    replayable setup, because it changes only the environment and the proof below it can depend
    on exactly that (one island sets a strict-decode locale this way).
    """
    body = body.strip()
    if not body or body.startswith("#"):
        return False
    if OUTPUT.match(body):
        return False
    # Judge the command, not its trailing comment. `PLACEHOLDER.search(body)` over the whole
    # line let a single `<word>` in a comment — `cd scripts   # then run <gate.py>` — read as a
    # template and cancel the gap, so the `cd` was dropped and the proof below it counted as
    # verified in the wrong directory: round 2's headline gap fix, defeated by one token.
    code = split_comment(body)[0].strip()
    if not code:
        return False
    if PLACEHOLDER.search(code):
        return False
    if EXPORT.match(code):
        return False
    if code.startswith("(") or code.startswith("{"):     # a subshell or group
        return True
    # Do not require successful tokenization and do not ask whether the apparent executable is
    # installed. A malformed row still consumes shell status, and both guesses previously let
    # the candidate above it borrow a report that belonged to this row.
    return True





def commands(block):
    """Yield (command, expected_code_or_None, setup) from one fenced block.

    A proof block often assigns shell variables once and reuses them (`G=scripts/g.py`,
    then `python3 $G ...`). Running a command without its assignments makes every one of
    them a usage error, so the assignments seen earlier in the block are carried forward
    and prepended - the block is the unit of context, not the line.

    The same is true of the steps that BUILD the block's fixtures. `D=$(mktemp -d)` followed
    by a `printf` into `$D` used to carry the assignment and drop the file-creation, so the
    gate met an empty directory and returned a code the block never claimed - a mismatch the
    island did not earn, and, in the other direction, a proof that could pass while its
    scenario was never built. Earlier unannotated steps now join the prefix, so the whole
    assignment context and command run in one shell: the substitution is re-evaluated, and
    runnable fixture builders run in child shells that inherit `D` while their filesystem
    effects persist. Shell state created by a runnable builder cannot replace the later proof command.

    Each candidate carries an immutable set of gap causes. It is false when empty, preserving
    the original truth test, while distinguishing an ordinary unreplayable step from a refused
    setup state. A match after either gap is reported but never counted as a verified
    proof; downstream harnesses may additionally treat refusal as a non-verdict.
    """
    lines = block.splitlines()
    setup = []
    gap_causes = set()
    i = 0
    while i < len(lines):
        raw = lines[i]
        m = PROMPT.match(raw)
        bare = raw.strip()
        runnable = is_runnable(bare)
        # A bare `VAR=value` line is block context and must be picked up here; the
        # extractor used to skip it as "not a command" and then every later command
        # ran with the variable empty, which read as the island being broken.
        # A bare line that states an exit code is a candidate even when its leading token is
        # off the allowlist — main reports it SKIPPED. Dropping it here is how a documented
        # proof stops being checked with nothing in the output to say so.
        claims = ANNOT.search(split_comment(raw)[1]) and not raw.startswith(" ")
        cmd = m.group(1) if m else (
            raw if runnable or claims or ASSIGN.match(split_comment(bare)[0])
            or EXPORT.match(split_comment(bare)[0]) or command_shaped(bare) else None)
        if not cmd or not cmd.strip():
            # Dropping a line here used to be silent, so a bare `cd scripts` — a real step, with
            # no annotation and an unlisted leading token — left no trace, and the command after
            # it was reported as a verified proof although its working directory was never
            # replayed. That is the exact false green the UNSEQUENCED class exists to prevent.
            if command_shaped(bare):
                gap_causes.add("unreplayable")
            i += 1
            continue
        # Bash removes an active backslash-newline; it does not replace it with a space. The
        # distinction is executable: `ec\` + `ho` names `echo`, while `ec ho` names a different
        # command. Preserve any real whitespace on either side and invent none. A final
        # backslash inside ordinary single quotes is literal and therefore is not joined.
        while line_continues(cmd) and i + 1 < len(lines):
            i += 1
            cmd = cmd[:-1] + lines[i]
        # A report line (`rc=$?`, `echo $?`, `echo "EXIT=$rc"`) only re-states the previous
        # command's code. Skip it as a command and let its annotation attach to what came
        # before — and, critically, do NOT let it mark the block gapped. `echo` is off the run
        # allowlist, so every `$ echo $? # → N` report was being counted as an unreplayable
        # step, and every later proof in that block was demoted to UNSEQUENCED. All nineteen
        # UNSEQUENCED results in this pack were that false positive, not a real gap.
        if is_report(cmd):
            i += 1
            continue
        # A bare assignment is context for what follows, not a command to check.
        exported = EXPORT.match(split_comment(cmd)[0])
        if exported:
            name, value = exported.group(1), exported.group(2)
            step = f"export {name}={value}"
            if safe_export(name, value):
                yield step, None, list(setup), frozenset(gap_causes)
                setup.append(step)
            else:
                # Not replayed. Refused and reported, and everything after it is gapped, because
                # a block that tried to poison the environment is not a block whose later proofs
                # can be trusted to have run in the environment they document.
                yield step, REFUSE, list(setup), frozenset(gap_causes)
                gap_causes.add("refused")
            i += 1
            continue
        assignment_code = split_comment(cmd)[0].strip()
        assigned = assignment_sequence(assignment_code) if ASSIGN.match(assignment_code) else None
        # `rc=$?; echo ...` is assignment-prefixed, but only the exact pure-report form above is
        # a report. A semicolon tail after that prefix is an independent compound command; do not
        # replay it as a block-local assignment or hide its annotation from SKIPPED accounting.
        if assigned and assignment_code.startswith("rc=$?;"):
            assigned = None
        if assigned:
            step = "; ".join(f"{name}={value}" for name, value in assigned)
            if any(unsafe_assignment(name) for name, _value in assigned):
                # As with a refused export, the binding is not replayed and later commands are
                # gapped. `PATH` is inherited-exported in ordinary invocations, so its bare form
                # is the same command-forgery primitive as `export PATH=...`.
                yield step, REFUSE, list(setup), frozenset(gap_causes)
                gap_causes.add("refused")
            else:
                setup.append(step)
            i += 1
            continue
        code, comment = split_comment(cmd)
        found = ANNOT.search(comment)
        report_prefix = code.strip().startswith(("echo $?", "rc=$?;"))
        arrow = (INLINE_ARROW.match(comment[1:])
                 if comment.startswith("#") and report_prefix else None)
        expected = int(found.group(1)) if found else (int(arrow.group(1)) if arrow else None)
        cmd = code.strip()
        # No inline annotation: the code may be stated by a report line below the output.
        if expected is None:
            expected = reported_code(lines[i + 1:])
        if cmd:
            # A function definition, executable startup hook, or variable-writing printf can
            # change what a later allowlisted command reaches. Refuse that state mutation even
            # when this row carries its own exit annotation.
            if unsafe_setup_state(cmd):
                yield cmd, REFUSE, list(setup), frozenset(gap_causes)
                gap_causes.add("refused")
                i += 1
                continue
            # An unannotated step states no code, so it verifies nothing - but the block
            # needs it to build what the next command is pointed at.
            if expected is None and is_runnable(cmd) and not PLACEHOLDER.search(cmd):
                if replayable(cmd):
                    yield cmd, expected, list(setup), frozenset(gap_causes)
                    setup.append(cmd)
                else:
                    yield cmd, expected, list(setup), frozenset(gap_causes)
                    gap_causes.add("unreplayable")
            else:
                yield cmd, expected, list(setup), frozenset(gap_causes)
                if not is_runnable(cmd) and command_shaped(cmd):
                    gap_causes.add("unreplayable")
        i += 1


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--strict"]
    strict = "--strict" in sys.argv[1:]
    # An unrecognised flag used to fall through as an island path, get skipped for having no
    # SKILL.md, and leave the run reporting success over whatever else was named:
    # `verify-proofs.py --bogus skills/crap-gate` exited 0. A misspelt flag is the caller being
    # wrong, and this tool reserves 2 for that.
    unknown = [a for a in args if a.startswith("-")]
    if unknown:
        print(f"verify-proofs: unknown option(s): {' '.join(unknown)}", file=sys.stderr)
        return 2
    if BASH_EXECUTABLE is None:
        print("verify-proofs: cannot resolve an executable Bash at startup", file=sys.stderr)
        return 2
    explicit = bool(args)
    args = args or sorted(str(p) for p in Path("skills").glob("*/"))
    total = ran = mismatched = pending = refused = template = skipped = 0
    unsequenced = examined = 0
    for arg in args:
        d = Path(arg)
        skill = d / "SKILL.md"
        if not skill.is_file():
            # A path the caller NAMED that is not an island is usage (exit 2), not a silent
            # skip that leaves the run reporting success over the other arguments — the same
            # certified-a-scope-it-never-opened defect closed-stream-check.py already fixed.
            # A default sweep may pass over a non-island directory; an explicit target may not.
            if explicit:
                print(f"verify-proofs: not an island (no SKILL.md): {d}", file=sys.stderr)
                return 2
            continue
        examined += 1
        try:
            skill_text = skill.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            # An unreadable island is not a failed proof. Exit 1 is this tool's MISMATCH code,
            # so borrowing it here would report the island as broken; 2 is "no verdict".
            print(f"verify-proofs: cannot read {skill}: {exc}", file=sys.stderr)
            return 2
        for block in blocks(skill_text):
            for cmd, expected, setup, gapped in commands(block):
                if expected == REFUSE:
                    refused += 1
                    print(f"REFUSED {d.name}: unsafe setup state, not replayed")
                    print(f"         {cmd}")
                    continue
                if not is_runnable(cmd):
                    # Off the allowlist. Reported, not dropped: an invisible skip is how a
                    # documented proof stops being checked without anyone noticing.
                    if expected is not None:
                        skipped += 1
                        print(f"SKIPPED {d.name}: leading token is off the allowlist")
                        print(f"         {cmd}")
                    continue
                total += 1
                if PLACEHOLDER.search(cmd):
                    template += 1
                    continue
                if expected is None:
                    pending += 1
                    print(f"PENDING {d.name}: candidate with no documented exit code")
                    print(f"         {cmd}")
                    continue
                script = proof_script(setup, cmd)
                bad = forbidden_primitive(script)
                if bad:
                    refused += 1
                    print(f"REFUSED {d.name}: {bad!r} is not run by this tool")
                    print(f"         {cmd}")
                    continue
                ran += 1
                try:
                    p = subprocess.run(
                        [BASH_EXECUTABLE, "-c", script],
                        cwd=d,
                        capture_output=True,
                        env=BASH_REPLAY_ENV,
                        timeout=120,
                    )
                    actual = p.returncode
                except subprocess.TimeoutExpired:
                    actual = "TIMEOUT"
                if actual != expected:
                    mismatched += 1
                    print(f"MISMATCH {d.name}: expected {expected}, got {actual}")
                    print(f"         {cmd}")
                elif gapped:
                    # It matched, but an earlier step of this block could not be replayed,
                    # so the scenario this command was pointed at may never have been built.
                    # Counting that as a verified proof is the false green this tool exists
                    # to catch elsewhere.
                    ran -= 1
                    unsequenced += 1
                    print(f"UNSEQUENCED {d.name}: matched {expected}, but an earlier step "
                          f"in this block could not be replayed")
                    print(f"         {cmd}")
    print(f"\n{examined} island(s): {total} candidates, {ran} proofs run, {pending} pending, "
          f"{template} templates, {skipped} skipped, {refused} refused, "
          f"{unsequenced} unsequenced, {mismatched} mismatched")
    if mismatched or refused:
        # A refusal outranks "nothing ran": it is a finding, not an absence. Reporting a
        # block that had to be refused as exit 3 read as "nothing to check" when the truth
        # was "something here was too dangerous to run".
        return 1
    if strict and pending:
        # Ordered ahead of the nothing-ran check on purpose. An island whose candidates ALL
        # lack a documented code satisfies both conditions at once, and the docstring's
        # unconditional promise — any PENDING exits 4 under --strict — was false there: it
        # returned the same 3 an island with no proof block at all returns, so the caller who
        # explicitly asked about coverage was told "nothing to check" instead of "here are the
        # candidates that document nothing". 4 is the more specific of two true answers, and
        # --strict is the caller asking for exactly that one.
        print(f"STRICT: {pending} candidate(s) carry no documented exit code",
              file=sys.stderr)
        return 4
    if ran == 0:
        # A verifier that ran nothing has verified nothing. Reporting success here let an
        # island whose proof block the extractor could not recognise — or which has none —
        # read as green, which is the same "passes by looking at nothing" failure this pack
        # names as its worst gate shape. Exit 3: distinct from a real mismatch (1) and from
        # a usage or IO fault (2), so a caller can tell "nothing to check" from "all clear".
        print("NOTHING VERIFIED - no annotated command was executed; this is not a pass",
              file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    # The exit-code contract has to survive the interpreter's own shutdown and any internal
    # fault. This tool exits 1 for a MISMATCH, so a dead-stdout flush leaking CPython's 120 or
    # an uncaught exception exiting 1 would both be read as verdicts about the code under
    # review. 2 is the non-verdict code the other three tools already seal to.
    try:
        _code = main()
    except SystemExit as _exc:
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
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
