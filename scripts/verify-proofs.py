#!/usr/bin/env python3
"""verify-proofs.py — re-run every command an island documents and check its exit code.

Usage: python3 scripts/verify-proofs.py [island-dir ...]      (default: skills/*/)

Each island's SKILL.md carries a red/green proof block: shell commands with the exit
code they produced, written as an annotation. This tool extracts those pairs, runs each
command from the island's own directory, and compares. It is the pack's own law turned
on its documentation - a proof block that no longer reproduces is a claim, not evidence.

Recognised annotation shapes (the ones the islands actually use):
    python3 scripts/x.py fixture   # exit 1
    python3 scripts/x.py fixture   # → EXIT=1
    $ rc=$?; echo "EXIT=$rc"       # → EXIT=1     (annotates the command above)

Exit 0 iff every extracted command reproduced its documented code. Commands that carry
no exit annotation are counted and reported, never guessed at.

KNOWN LIMITS, stated rather than discovered. This runs each annotated command with the
variable assignments seen earlier in its block, from the island's directory. It does NOT
replay other setup, so three shapes report a mismatch that is this tool's fault and not
the island's, and each must be checked by running the block as a whole before it is
believed:
  - a block that builds fixtures with `printf`/`mkdir` into a temp dir (the assignment
    carries, the file-creation does not, so the command meets an empty directory)
  - a heredoc (`python3 - <<'EOF'`), whose body is not captured with its first line
  - a block that `cd`s once and then uses paths relative to the new directory
A mismatch here is a prompt to go look, not a verdict.
"""
import re
import subprocess
import sys
from pathlib import Path

# `# exit N`, `# -> EXIT=N`, `# → EXIT=N`, tolerating surrounding prose in the comment.
ANNOT = re.compile(r"#.*?(?:exit\s*=?\s*|EXIT=)(\d+)", re.IGNORECASE)
PROMPT = re.compile(r"^\s*\$\s+(.*)$")
# A continuation of a shell command broken across lines with a trailing backslash.
CONT = re.compile(r"\\\s*$")


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
    """
    lines = block.splitlines()
    setup = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        m = PROMPT.match(raw)
        bare = raw.strip()
        runnable = bare.startswith(("python3 ", "bash ", "./"))
        # A bare `VAR=value` line is block context and must be picked up here; the
        # extractor used to skip it as "not a command" and then every later command
        # ran with the variable empty, which read as the island being broken.
        cmd = m.group(1) if m else (raw if runnable or ASSIGN.match(bare.split("#")[0]) else None)
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
        # Look ahead for an `rc=$?` line carrying the annotation instead.
        if expected is None:
            for look in lines[i + 1:i + 3]:
                if re.search(r"rc=\$\?|echo\s+\"?EXIT", look):
                    nxt = ANNOT.search(look)
                    if nxt:
                        expected = int(nxt.group(1))
                    break
        if cmd and not PLACEHOLDER.search(cmd):
            yield cmd, expected, list(setup)
        i += 1


def main() -> int:
    args = sys.argv[1:] or sorted(str(p) for p in Path("skills").glob("*/"))
    total = ran = mismatched = unannotated = 0
    for arg in args:
        d = Path(arg)
        skill = d / "SKILL.md"
        if not skill.is_file():
            continue
        for block in blocks(skill.read_text(encoding="utf-8")):
            for cmd, expected, setup in commands(block):
                if not (cmd.startswith("python3 ") or cmd.startswith("bash ") or cmd.startswith("./")):
                    continue
                total += 1
                if expected is None:
                    unannotated += 1
                    continue
                ran += 1
                script = "; ".join(setup + [cmd]) if setup else cmd
                try:
                    p = subprocess.run(script, shell=True, cwd=d, capture_output=True, timeout=120)
                    actual = p.returncode
                except subprocess.TimeoutExpired:
                    actual = "TIMEOUT"
                if actual != expected:
                    mismatched += 1
                    print(f"MISMATCH {d.name}: expected {expected}, got {actual}")
                    print(f"         {cmd}")
    print(f"\n{total} documented commands, {ran} with an exit annotation, "
          f"{unannotated} unannotated, {mismatched} mismatched")
    return 1 if mismatched else 0


if __name__ == "__main__":
    sys.exit(main())
