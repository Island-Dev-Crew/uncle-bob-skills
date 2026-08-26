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
      ...output...
    $ rc=$?; echo "EXIT=$rc"       # → EXIT=1
    $ echo $?                      # → 1

Allowlisted leading tokens: `python3`, `bash`, `sh`, `printf` (the shipped
`printf … | python3 gate.py` stdin form), `./…`, and a relative path that names a directory
and ends `.sh`/`.py` (`scripts/probe.sh`; a script in the island root needs its `./`).
A candidate whose arguments contain a `<placeholder>` is a usage
template, reported as TEMPLATE and not run. A fenced command whose leading token is off
the allowlist is reported as SKIPPED rather than silently dropped.

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

TRUST BOUNDARY, stated rather than implied. This tool RUNS commands taken out of the
repository it is checking. That is inherent to re-running a documented proof, not an
oversight — a proof block that is never executed is a claim again. So it is only safe to
point at a repository you trust: a fork, a pull request, or an untrusted clone can put a
command in a fenced block and this tool will run it. Two mitigations, neither a substitute
for that sentence: the leading token must be on the allowlist above, and a command carrying
a network, privilege-escalation, or device-destructive primitive is REFUSED rather than run,
by the name the KERNEL would resolve rather than the characters on the page - `/usr/bin/curl`
and `../../sbin/dd` are refused with the bare words, and so are the spellings only a shell
resolves (`cur\\l`, `'cur'l`, `c''url`, `CURL`), because the line is parsed into words the way
bash parses it before those words are judged. What a word parse does NOT reach is a name assembled
at run time: `C=cur\\l; bash -c '$C x'` carries no forbidden word in any word it has, and is run.
That is the trust sentence above, restated about one narrower case rather than argued away. The
allowlist
widened when the grammar was written down — it now admits a bare island-relative script and a
`printf` stdin pipe — so it constrains the first token only, never the rest of the line.

KNOWN LIMITS, stated rather than discovered. Each annotated command runs from the island's
directory, preceded by the steps of its own block that this tool can replay verbatim: the
variable assignments, and the earlier unannotated commands that build the block's fixtures.
The whole prefix runs in one shell with the command, so `D=$(mktemp -d)` is re-evaluated
and the fixtures are rebuilt inside the directory it just made.

Two shapes still cannot be replayed, and both are handled by saying so rather than by
guessing:
  - a heredoc (`python3 - <<'EOF'`), whose body is not captured with its first line
  - a step whose leading token is off the allowlist (a `cd`, a `(subshell)`)
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
# A continuation of a shell command broken across lines with a trailing backslash.
CONT = re.compile(r"\\\s*$")

# The allowlist that defines a candidate. The fourth alternative is the shipped bare form -
# `scripts/diff-scope.sh HEAD~1 HEAD` - which the extractor used to skip outright, so two
# islands' entire red/green pair went unread and the run reported "0 documented" at exit 0.
RUNNABLE = re.compile(
    r"^(?:python3\s|bash\s|sh\s|printf\s|\./"
    r"|(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:sh|py)(?:\s|$))"
)
# An exit-report line: `rc=$?; echo "EXIT=$rc"` or `echo $?`, with or without a `$ ` prompt.
REPORT = re.compile(r"^(?:rc=\$\?|echo\s+(?:\$\?|\"?EXIT|\"?\$\{?rc))")
# The code a report line states, anchored at its comment: `# → 1`, `# -> EXIT=1`, `# 2`.
ARROW = re.compile(r"\s*(?:[-=]*>|→)?\s*(?:EXIT\s*=\s*)?(\d+)\b")


def is_runnable(cmd):
    return bool(RUNNABLE.match(cmd.strip()))


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
        words = shlex.split(script)
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


def forbidden_primitive(script):
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
    unbalanced enough that there are no words to read.
    """
    bare = FORBIDDEN.search(script)
    if bare:
        return bare.group(0)
    for word in PATH_WORD.findall(script):
        if os.path.basename(word) in FORBIDDEN_NAMES:
            return word
    for word in shell_words(script):
        if os.path.basename(word).lower() in FORBIDDEN_NAMES:
            return word
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
        m = PROMPT.match(raw)
        body = m.group(1).strip() if m else stripped
        if REPORT.match(body):
            found = ANNOT.search(body)
            if found:
                return int(found.group(1))
            if "#" in body:
                tail = ARROW.match(body.split("#", 1)[1])
                if tail:
                    return int(tail.group(1))
            return None
        if m or is_runnable(body) or ASSIGN.match(split_comment(body)[0]) or command_shaped(body):
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

    A hash only opens a shell comment at the start of a word, so one welded to a previous
    character stays part of the command, as does every hash inside a quote.
    """
    out = []
    quote = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            out.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(line):
                i += 1
                out.append(line[i])
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (not out or out[-1].isspace()):
            return "".join(out), line[i:]
        else:
            out.append(ch)
        i += 1
    return "".join(out), ""


def blocks(text):
    """Yield the contents of each ```bash fenced block."""
    for m in re.finditer(r"```(?:bash|sh)\n(.*?)```", text, re.DOTALL):
        yield m.group(1)


ASSIGN = re.compile(r"^\s*\$?\s*([A-Za-z_][A-Za-z0-9_]*)=(\S.*?)\s*$")
PLACEHOLDER = re.compile(r"<[a-z][a-z0-9._-]*>", re.IGNORECASE)
# `export NAME=value` sets the environment and runs nothing, so it is replayed verbatim rather
# than treated as a step this tool had to skip.
EXPORT = re.compile(r"^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)=(\S.*?)\s*$")
# A documented `export` is replayed into the shell that runs the proof, so it is the one thing
# a proof block can put into the environment of an allowlisted command. That is safe only for
# variables that change the INPUT/decoding channel (a locale, a Python encoding) — never one
# that redirects which code runs. `export PATH=./fake` in a SKILL.md forged a verified proof by
# shimming the very `python3` the block then invoked; the allowlist the docstring names as
# mitigation #1 was bypassed because `export` is off it. So: replay a safe name with a safe
# (metacharacter-free) value; REFUSE anything else and report it.
SAFE_ENV = frozenset("""
LANG LANGUAGE LC_ALL LC_CTYPE LC_COLLATE LC_MESSAGES LC_NUMERIC LC_TIME LC_MONETARY
PYTHONUTF8 PYTHONIOENCODING PYTHONLEGACYWINDOWSFSENCODING
""".split())
SAFE_EXPORT_VALUE = re.compile(r"^[A-Za-z0-9_.:@=+/-]*$")
REFUSE = "__REFUSE__"      # sentinel in the `expected` slot: main refuses and reports it


def safe_export(name, value):
    """Only a locale/encoding export with a plain value may enter a proof's environment."""
    return name in SAFE_ENV and bool(SAFE_EXPORT_VALUE.match(value))

# Words that make a line a COMMAND even though its leading token is off the run allowlist.
# Two different bugs needed this. A report line's lookahead walked straight PAST `node setup.js`
# and attached the `echo $?` below it to the command ABOVE — a code borrowed from a different
# run. And a bare `cd scripts` was dropped so quietly that the next command counted as verified
# with its working directory never replayed. Deliberately a small, named list rather than a
# shape test: output lines look command-shaped too (`LOST 0.10x gated=10m ...`), and treating
# those as boundaries would strand real proofs as PENDING.
SHELL_WORDS = frozenset("""
cd pushd popd export set unset source exec eval trap umask shift read wait
echo printf cat head tail sed awk grep rg find sort uniq cut tr tee xargs
mkdir rmdir touch cp mv ln chmod chown rm true false test exit return
git node npm npx yarn pnpm bunx uvx pipx go cargo make docker
""".split())


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
    head = code.split()[0].split("=")[0]
    return head in SHELL_WORDS





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
    prefix and the command run in one shell: the substitution is re-evaluated, and the
    fixtures are rebuilt inside the directory it just made.

    Each candidate carries `gapped`: true when some earlier step of its block could not be
    replayed (off the allowlist, or not one whole command). A match after a gap is reported,
    but never counted as a verified proof.
    """
    lines = block.splitlines()
    setup = []
    gapped = False
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
            or EXPORT.match(split_comment(bare)[0]) else None)
        if not cmd or not cmd.strip():
            # Dropping a line here used to be silent, so a bare `cd scripts` — a real step, with
            # no annotation and an unlisted leading token — left no trace, and the command after
            # it was reported as a verified proof although its working directory was never
            # replayed. That is the exact false green the UNSEQUENCED class exists to prevent.
            if command_shaped(bare):
                gapped = True
            i += 1
            continue
        # Join backslash continuations.
        while CONT.search(cmd) and i + 1 < len(lines):
            i += 1
            cmd = CONT.sub(" ", cmd) + lines[i].strip()
        # A report line (`rc=$?`, `echo $?`, `echo "EXIT=$rc"`) only re-states the previous
        # command's code. Skip it as a command and let its annotation attach to what came
        # before — and, critically, do NOT let it mark the block gapped. `echo` is off the run
        # allowlist, so every `$ echo $? # → N` report was being counted as an unreplayable
        # step, and every later proof in that block was demoted to UNSEQUENCED. All nineteen
        # UNSEQUENCED results in this pack were that false positive, not a real gap.
        if REPORT.match(cmd.strip()) or re.match(r"^\s*rc=\$\?", cmd):
            i += 1
            continue
        # A bare assignment is context for what follows, not a command to check.
        exported = EXPORT.match(split_comment(cmd)[0])
        if exported:
            name, value = exported.group(1), exported.group(2)
            step = f"export {name}={value}"
            if safe_export(name, value):
                yield step, None, list(setup), gapped
                setup.append(step)
            else:
                # Not replayed. Refused and reported, and everything after it is gapped, because
                # a block that tried to poison the environment is not a block whose later proofs
                # can be trusted to have run in the environment they document.
                yield step, REFUSE, list(setup), gapped
                gapped = True
            i += 1
            continue
        assigned = ASSIGN.match(split_comment(cmd)[0])
        if assigned and not split_comment(cmd)[0].strip().startswith(("python3", "bash", "./")):
            setup.append(f"{assigned.group(1)}={assigned.group(2)}")
            i += 1
            continue
        found = ANNOT.search(split_comment(cmd)[1])
        expected = int(found.group(1)) if found else None
        cmd = split_comment(cmd)[0].strip()
        # No inline annotation: the code may be stated by a report line below the output.
        if expected is None:
            expected = reported_code(lines[i + 1:])
        if cmd:
            yield cmd, expected, list(setup), gapped
            # An unannotated step states no code, so it verifies nothing - but the block
            # needs it to build what the next command is pointed at.
            if expected is None and is_runnable(cmd) and not PLACEHOLDER.search(cmd):
                if replayable(cmd):
                    setup.append(cmd)
                else:
                    gapped = True
            elif not is_runnable(cmd) and command_shaped(cmd):
                gapped = True
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
                    print(f"REFUSED {d.name}: unsafe environment export, not replayed")
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
                script = "; ".join(setup + [cmd]) if setup else cmd
                bad = forbidden_primitive(script)
                if bad:
                    refused += 1
                    print(f"REFUSED {d.name}: {bad!r} is not run by this tool")
                    print(f"         {cmd}")
                    continue
                ran += 1
                try:
                    p = subprocess.run(["bash", "-c", script], cwd=d, capture_output=True, timeout=120)
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
