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
exit 4, so a caller that wants full coverage can demand it. PENDING is the failure
direction of every ambiguity here: an output line that could pass for a command ends the
search for a report line, which leaves a proof unverified rather than pairing a command
with a code that is not its own.

TRUST BOUNDARY, stated rather than implied. This tool RUNS commands taken out of the
repository it is checking. That is inherent to re-running a documented proof, not an
oversight — a proof block that is never executed is a claim again. So it is only safe to
point at a repository you trust: a fork, a pull request, or an untrusted clone can put a
command in a fenced block and this tool will run it. Two mitigations, neither a substitute
for that sentence: the leading token must be on the allowlist above, and a command carrying
a network, privilege-escalation, or device-destructive primitive is REFUSED rather than run.
The allowlist widened when the grammar was written down — it now admits a bare
island-relative script and a `printf` stdin pipe — so it constrains the first token only,
never the rest of the line.

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
import re
import shlex
import subprocess
import sys
from pathlib import Path

# Refused outright rather than executed. Not a sandbox — a `python3 -c` can still do
# anything — but it closes the shapes that exfiltrate or escalate, which are the ones a
# hostile proof block would reach for first. Re-measured after the grammar widened the
# allowlist: zero candidates in this repo match, so it costs no false red today. Re-measure
# rather than trust this sentence — `grep -c REFUSED` on a full run is the check.
FORBIDDEN = re.compile(
    r"(?<![\w./-])(?:curl|wget|nc|ncat|netcat|telnet|ssh|scp|sftp|rsync"
    r"|sudo|doas|chown|chgrp|shutdown|reboot|mkfs|dd)(?![\w./-])"
)

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
        if m or is_runnable(body) or ASSIGN.match(body.split("#")[0]):
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


def blocks(text):
    """Yield the contents of each ```bash fenced block."""
    for m in re.finditer(r"```(?:bash|sh)\n(.*?)```", text, re.DOTALL):
        yield m.group(1)


ASSIGN = re.compile(r"^\s*\$?\s*([A-Za-z_][A-Za-z0-9_]*)=(\S.*?)\s*$")
PLACEHOLDER = re.compile(r"<[a-z][a-z0-9._-]*>", re.IGNORECASE)


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
        claims = ANNOT.search(raw) and not raw.startswith(" ")
        cmd = m.group(1) if m else (
            raw if runnable or claims or ASSIGN.match(bare.split("#")[0]) else None)
        if not cmd or not cmd.strip():
            i += 1
            continue
        # Join backslash continuations.
        while CONT.search(cmd) and i + 1 < len(lines):
            i += 1
            cmd = CONT.sub(" ", cmd) + lines[i].strip()
        # An `rc=$?` line only re-states the previous command's code; skip it as a
        # command but let its annotation attach to what came before.
        if re.match(r"^\s*rc=\$\?", cmd):
            i += 1
            continue
        # A bare assignment is context for what follows, not a command to check.
        assigned = ASSIGN.match(cmd.split("#")[0])
        if assigned and not cmd.split("#")[0].strip().startswith(("python3", "bash", "./")):
            setup.append(f"{assigned.group(1)}={assigned.group(2)}")
            i += 1
            continue
        found = ANNOT.search(cmd)
        expected = int(found.group(1)) if found else None
        cmd = cmd.split("#")[0].strip()
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
            elif not is_runnable(cmd):
                gapped = True
        i += 1


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--strict"]
    strict = "--strict" in sys.argv[1:]
    args = args or sorted(str(p) for p in Path("skills").glob("*/"))
    total = ran = mismatched = pending = refused = template = skipped = 0
    unsequenced = 0
    for arg in args:
        d = Path(arg)
        skill = d / "SKILL.md"
        if not skill.is_file():
            continue
        for block in blocks(skill.read_text(encoding="utf-8")):
            for cmd, expected, setup, gapped in commands(block):
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
                bad = FORBIDDEN.search(script)
                if bad:
                    refused += 1
                    print(f"REFUSED {d.name}: {bad.group(0)!r} is not run by this tool")
                    print(f"         {cmd}")
                    continue
                ran += 1
                try:
                    p = subprocess.run(script, shell=True, cwd=d, capture_output=True, timeout=120)
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
    print(f"\n{total} candidates, {ran} proofs run, {pending} pending, "
          f"{template} templates, {skipped} skipped, {refused} refused, "
          f"{unsequenced} unsequenced, {mismatched} mismatched")
    if mismatched or refused:
        # A refusal outranks "nothing ran": it is a finding, not an absence. Reporting a
        # block that had to be refused as exit 3 read as "nothing to check" when the truth
        # was "something here was too dangerous to run".
        return 1
    if ran == 0:
        # A verifier that ran nothing has verified nothing. Reporting success here let an
        # island whose proof block the extractor could not recognise — or which has none —
        # read as green, which is the same "passes by looking at nothing" failure this pack
        # names as its worst gate shape. Exit 3: distinct from a real mismatch (1) and from
        # a usage or IO fault (2), so a caller can tell "nothing to check" from "all clear".
        print("NOTHING VERIFIED - no annotated command was executed; this is not a pass",
              file=sys.stderr)
        return 3
    if strict and pending:
        print(f"STRICT: {pending} candidate(s) carry no documented exit code",
              file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
