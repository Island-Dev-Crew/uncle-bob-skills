#!/usr/bin/env python3
"""lane-check.py — assert every shipped skill script stays in its lane.

Usage: python3 scripts/lane-check.py [skills-dir]        (default: skills)

A user copies a skill folder into their agent's skills directory, so the scripts under
`skills/*/scripts/` run on their machine. This gate turns "they behave" from an observation
into a checked claim. Four lanes, each a refusal:

  L1  no network      — no socket/urllib/http/requests/ftplib/smtplib import, no curl/wget/
                        nc/ssh/scp/telnet invocation
  L2  no arbitrary execution — no os.system, no subprocess(..., shell=True), no exec()/eval()
                        (ast.literal_eval is explicitly allowed: it evaluates literals only)
  L3  no unscoped destruction — an `rm -rf` target must be a variable or a path under a temp
                        root, never a bare absolute path
  L4  exit codes documented — the file states what its exit codes mean, so a caller is never
                        guessing what a number meant

SCOPE, stated so it is not mistaken for more: this covers the SHIPPED skill scripts, which
are what a user installs. Repo-level tooling under `scripts/` is not shipped as a skill and
carries its own stated trust boundary (see verify-proofs.py, which by design runs commands
out of the repository it checks).

It is a STATIC check. It reads source; it never imports or executes what it reads, so it
cannot be defeated by anything at runtime and equally cannot see a lane crossed through
indirection it has no way to resolve. That limit is real and stated rather than discovered.

Exit 0 iff every scanned script holds every lane. Exit 1 on a breach, exit 2 on usage or IO
error — an error path never borrows the verdict's code.
"""
import ast
import os
import re
import sys
from pathlib import Path

NET_MODULES = {"socket", "urllib", "http", "requests", "ftplib", "smtplib", "telnetlib",
               "httplib", "urllib2", "aiohttp", "httpx"}
NET_SHELL = re.compile(r"(?<![\w./-])(?:curl|wget|nc|ncat|netcat|telnet|ssh|scp|sftp)(?![\w./-])")
# An rm -rf whose target is a bare absolute path. A "$var" target or a temp root is the
# ordinary trap-cleanup idiom every probe script here uses and is not a breach.
RM_ABS = re.compile(r"\brm\s+-[rRf]{1,2}[a-zA-Z]*\s+[\"']?(/(?!tmp/|private/tmp/|var/folders/)\S*)")
# `Exit:` with a colon is how these files actually write it, and requiring whitespace
# straight after "exit" made this gate go RED on three correct scripts — a false red
# from the checker, not a breach in the checked.
EXIT_DOC = re.compile(r"exit\s*(?:code|status)|exits?\s*:?\s*\d|Exit\s*\|",
                      re.IGNORECASE)


def check_python(path, src):
    """Lane breaches in one Python file, found through the parse tree rather than by grep."""
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [f"L0 unparseable: {exc}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in NET_MODULES:
                    out.append(f"L1 network import '{a.name}' (line {node.lineno})")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in NET_MODULES:
                out.append(f"L1 network import from '{node.module}' (line {node.lineno})")
        elif isinstance(node, ast.Call):
            f = node.func
            name = getattr(f, "attr", None) or getattr(f, "id", None)
            if name == "system" and getattr(getattr(f, "value", None), "id", "") == "os":
                out.append(f"L2 os.system (line {node.lineno})")
            if name in ("exec", "eval") and isinstance(f, ast.Name):
                out.append(f"L2 {name}() (line {node.lineno})")
            for kw in node.keywords or []:
                if kw.arg == "shell" and getattr(kw.value, "value", False) is True:
                    out.append(f"L2 shell=True (line {node.lineno})")
    return out


def strip_shell_comment(line):
    """Drop a trailing shell comment without cutting a hash that lives inside a quote.

    Cutting at the first hash reads like comment-stripping and is not: a quoted hash — a colour
    literal, a `sed` script, a regex — truncated the line, and everything after it went
    unscanned. Nothing in this pack hides a breach behind one today (measured: fifteen lines
    carry a quoted hash, none with a lane primitive after it), but a scanner that silently reads
    less than it claims is the false green this tool exists to prevent, and the same defect was
    just found in verify-proofs.py, where it truncated a command that was then executed.
    """
    out = []
    quote = None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (not out or out[-1].isspace()):
            break
        else:
            out.append(ch)
    return "".join(out)


def check_shell(path, src):
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        bare = strip_shell_comment(line)
        m = NET_SHELL.search(bare)
        if m:
            out.append(f"L1 network invocation {m.group(0)!r} (line {i})")
        m = RM_ABS.search(bare)
        if m:
            out.append(f"L3 rm -rf on a bare absolute path {m.group(1)!r} (line {i})")
    return out


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "skills")
    if not root.is_dir():
        print(f"lane-check: not a directory: {root}", file=sys.stderr)
        return 2
    scanned = breaches = 0
    for path in sorted(root.glob("*/scripts/*")):
        # Only a file whose IMMEDIATE parent is `fixtures` is skipped. Testing the
        # whole path excluded any tree with "fixtures" anywhere above it, which is
        # how this gate scanned zero files and reported green over its own red test.
        if path.suffix not in (".py", ".sh") or path.parent.name == "fixtures":
            continue
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"lane-check: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        scanned += 1
        found = check_python(path, src) if path.suffix == ".py" else check_shell(path, src)
        if not EXIT_DOC.search(src):
            found.append("L4 exit codes not documented in the file")
        for f in found:
            breaches += 1
            print(f"BREACH {path}: {f}")
    print(f"\n{scanned} shipped skill scripts scanned, {breaches} lane breach(es)")
    return 1 if breaches else 0


if __name__ == "__main__":
    try:
        code = main()
    except BaseException as exc:
        print(f"lane-check: internal failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        code = 2
    for stream, fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if stream is not None:
                stream.flush()
        except BaseException:
            if code in (0, 1):
                code = 2
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), fd)
            except BaseException:
                pass
    sys.exit(code)
