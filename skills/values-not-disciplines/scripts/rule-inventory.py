#!/usr/bin/env python3
"""rule-inventory.py — the pack's second law made checkable.

Every quality rule in a harness must NAME the tool that measures it or carry an
explicit `advisory` label. This gate reads a rule inventory and rules on each row.

Usage:
  rule-inventory.py [--root DIR] INVENTORY.tsv
  rule-inventory.py [--root DIR] -              # rows on stdin

Input rows are TSV: `rule <TAB> measure`. `measure` is either the command line
that measures the rule, or the literal label `advisory` / `advisory: reason`.
Blank lines and `#` comments are skipped.

Exit codes are distinct meanings — a broken pipe never reads as a clean harness:
  0  verdict: every rule is MEASURED or ADVISORY
  1  verdict: at least one rule is PROSE-ONLY or NO-OP
  2  usage / IO / malformed input (never a verdict)
"""
import argparse
import importlib.util
import os
import re
import shutil
import sys
from pathlib import Path

# `advisory` or `advisory: <reason>` — anchored, so `advisory-ish prose` is not a label.
ADVISORY_RE = re.compile(r"^advisory(?::[ \t]+\S.*)?$")

# Executables that always exit 0: naming one is prose with extra steps —
# `measure: true` is the classic way to launder an unmeasured rule. This set is
# exactly the list SKILL.md publishes; commands that CAN exit non-zero
# (`test -f x`, `cat report.txt`) are honest measures and are judged on shape.
NO_OP = {"true", ":", "echo", "yes", "pwd"}

# The mirror image: always exits non-zero, so the fix-until-green loop never ends.
CONSTANT_FAIL = {"false"}

# Commands that only launch another command. A no-op wrapped in one of these is
# still a no-op (`env true`), so they are peeled off before judging.
WRAPPERS = {
    "env", "nice", "command", "timeout", "nohup", "stdbuf", "xargs",
    "sudo", "doas", "time", "ionice", "setsid", "exec", "builtin",
}

# English words that are prose even when a same-named binary happens to sit on
# PATH (`code review` must not pass because an editor CLI is installed).
NOT_A_TOOL = {
    "be", "keep", "write", "use", "make", "do", "code", "review", "manual",
    "human", "judgment", "judgement", "common", "follow", "ensure", "avoid",
    "prefer", "none", "n/a", "na", "tbd", "todo", "-", "--", "?",
}

# An interpreter alone measures nothing; it must name a script or an -m module.
INTERPRETERS = {"python", "python3", "bash", "sh", "zsh", "node", "ruby", "perl", "pwsh"}

SCRIPTISH = (".py", ".sh", ".js", ".ts", ".rb", ".pl", ".json", ".toml", ".yaml", ".yml", ".cfg", ".ini")

# Extensions that make a file runnable as the command itself. A `.md` or `.yaml`
# exists but cannot execute, let alone go red — pointing a rule at the style guide
# that states it is the most natural laundering move there is.
EXEC_EXT = (".py", ".sh", ".js", ".ts", ".rb", ".pl")

# Wrapper arguments to skip past: `timeout 60 cmd`, `nice -n 5 cmd`, `env FOO=bar cmd`.
ARGISH_RE = re.compile(r"^\d+(?:\.\d+)?[smhd]?$")
ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def die(msg: str) -> None:
    print(f"rule-inventory: {msg}", file=sys.stderr)
    sys.exit(2)


def looks_like_path(tok: str) -> bool:
    return "/" in tok or tok.endswith(SCRIPTISH)


def resolve_file(tok: str, root: Path) -> bool:
    """True iff `tok` names an existing file *under* root. No CWD fallback, and
    `../` cannot walk out — the harness root is the whole world for a named tool."""
    root_r = root.resolve()
    p = Path(tok)
    cand = p if p.is_absolute() else root / p
    try:
        r = cand.resolve()
    except (OSError, RuntimeError, ValueError):
        return False
    if r != root_r and root_r not in r.parents:
        return False
    return r.is_file()


def is_runnable(tok: str, root: Path) -> bool:
    """True iff the resolved file could actually be executed as the command: the
    exec bit is set, or it carries a script extension an interpreter would honor."""
    p = Path(tok)
    cand = (p if p.is_absolute() else root / p)
    try:
        r = cand.resolve()
    except (OSError, RuntimeError, ValueError):
        return False
    return os.access(r, os.X_OK) or r.name.lower().endswith(EXEC_EXT)


def resolve_module(mod: str, root: Path) -> bool:
    """True iff `-m mod` names something that exists: a module file under --root, or
    an importable top-level module on this host (host-dependent, exactly like PATH).
    Dotted names are resolved under --root only — locating `a.b` would import `a`."""
    if not mod or mod.startswith("-"):
        return False
    rel = mod.replace(".", "/")
    if resolve_file(rel + ".py", root) or resolve_file(rel + "/__init__.py", root):
        return True
    if "." in mod:
        return False
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, AttributeError, ValueError, TypeError):
        return False


def unwrap(tokens):
    """Peel `env`/`nice`/`timeout`/... and their own arguments off the front, so the
    command that actually runs is the one judged. Returns [] if nothing is left."""
    i, peeled = 0, 0
    while i < len(tokens) and peeled < 8:
        if os.path.basename(tokens[i]).lower() not in WRAPPERS:
            break
        peeled += 1
        i += 1
        while i < len(tokens):
            t = tokens[i]
            if t.startswith("-") or ARGISH_RE.match(t) or (ASSIGN_RE.match(t) and not looks_like_path(t)):
                i += 1
                continue
            break
    return tokens[i:]


def has_command_shape(tokens, root: Path) -> bool:
    """A command, not a sentence. Resolving on PATH is not enough — `sort out the
    layering` resolves. The measure must also LOOK like an invocation: a tool path,
    a flag, a path operand that resolves under --root, or a single bare tool name."""
    exe, rest = tokens[0], tokens[1:]
    if looks_like_path(exe):
        return True
    if any(t.startswith("-") and len(t) > 1 for t in rest):
        return True
    operands = [t for t in rest if not t.startswith("-")]
    if any(looks_like_path(t) and resolve_file(t, root) for t in operands):
        return True
    return len(operands) <= 1


def judge(measure: str, root: Path):
    """Return (verdict, detail) for one measure field."""
    m = measure.strip()
    if not m:
        return "PROSE-ONLY", "no measure declared"
    if ADVISORY_RE.match(m):
        return "ADVISORY", "labeled advisory"

    raw = m.split()
    if os.path.basename(raw[0]).lower() in NOT_A_TOOL:
        return "PROSE-ONLY", f"prose, not a tool: {raw[0]}"

    tokens = unwrap(raw)
    if not tokens:
        return "PROSE-ONLY", f"wrapper names no command: {m}"
    # Peel budget exhausted with a wrapper still at the head: nine `env`s name no
    # more of a command than one does.
    if os.path.basename(tokens[0]).lower() in WRAPPERS:
        return "PROSE-ONLY", f"wrapper chain names no command: {m}"

    exe = tokens[0]
    base = os.path.basename(exe).lower()
    if base in NOT_A_TOOL:
        return "PROSE-ONLY", f"prose, not a tool: {exe}"
    if base in NO_OP:
        return "NO-OP", f"'{base}' always exits 0 — a gate that cannot go red is not a gate"
    if base in CONSTANT_FAIL:
        return "NO-OP", f"'{base}' always exits non-zero — a gate that cannot go green measures nothing"
    if looks_like_path(exe):
        if not resolve_file(exe, root):
            return "PROSE-ONLY", f"named tool does not resolve under --root: {exe}"
        if not is_runnable(exe, root):
            return "PROSE-ONLY", f"named tool is not executable: {exe}"
    elif shutil.which(exe) is None:
        return "PROSE-ONLY", f"not a resolvable tool: {exe}"

    # `python3 -m pytest` names something to run; `python3 -c "…"` and bare `python3` do not.
    module = None
    if base.startswith("python"):
        for i, t in enumerate(tokens[1:], 1):
            if t == "-m" and i + 1 < len(tokens):
                module = tokens[i + 1]
                break
            if t.startswith("-m") and len(t) > 2:
                module = t[2:]
                break
        if module is not None and not resolve_module(module, root):
            return "PROSE-ONLY", f"-m module does not resolve: {module}"

    # Every path-shaped argument must exist under --root too: `python3 nonexistent.py` names nothing.
    operands = [t for t in tokens[1:] if not t.startswith("-")]
    paths = [t for t in operands if looks_like_path(t)]
    for t in paths:
        if not resolve_file(t, root):
            return "PROSE-ONLY", f"named tool does not resolve under --root: {t}"
    if base in INTERPRETERS and not paths and not module:
        return "PROSE-ONLY", f"{base} names no script or -m module to run"

    if not has_command_shape(tokens, root):
        return "PROSE-ONLY", f"sentence shape, not a command: {m}"
    return "MEASURED", m


def read_rows(path: str):
    if path == "-":
        text = sys.stdin.read()
    else:
        f = Path(path)
        if not f.is_file():
            die(f"no such inventory file: {path}")
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            die(f"cannot read {path}: {e}")
    rows = []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            die(f"line {n}: expected 2 tab-separated fields (rule, measure), got {len(parts)}")
        rows.append((n, parts[0].strip(), parts[1].strip()))
    if not rows:
        die("empty inventory — an empty rule set cannot pass")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Rule-inventory gate: name the measuring tool or say advisory.")
    ap.add_argument("inventory", help="TSV file of `rule <TAB> measure` rows, or - for stdin")
    ap.add_argument("--root", default=".", help="directory that relative tool paths resolve against")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        die(f"--root is not a directory: {args.root}")

    rows = read_rows(args.inventory)
    tally = {"MEASURED": 0, "ADVISORY": 0, "PROSE-ONLY": 0, "NO-OP": 0}
    for _, rule, measure in rows:
        v, detail = judge(measure, root)
        tally[v] += 1
        print(f"{v:<11}{rule}  [{detail}]")

    breaches = tally["PROSE-ONLY"] + tally["NO-OP"]
    print(
        f"{len(rows)} rules, {tally['MEASURED']} measured, {tally['ADVISORY']} advisory, "
        f"{breaches} unmeasured-and-unlabeled"
    )
    return 1 if breaches else 0


if __name__ == "__main__":
    # The exit-code contract has to survive the interpreter's own shutdown. CPython
    # flushes the std streams after main() returns, and if that flush raises - a pipe
    # whose reader has gone, the ordinary `| head` idiom - it REPLACES the status with
    # 120, a code no table here names. argparse is the other leak: it raises SystemExit
    # from inside, so a usage error would skip any seal placed after a bare call.
    try:
        _code = main()
    except SystemExit as _exc:                 # argparse usage errors and --help
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
    except BaseException as _exc:              # an exception is not a verdict
        try:
            print(f"error: internal failure: {{type(_exc).__name__}}: {{_exc}}", file=sys.stderr)
        except BaseException:
            pass
        _code = 2
    for _stream, _fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if _stream is not None:
                _stream.flush()
        except BaseException:
            if _code in (0, 1):                # output that never landed is not a verdict
                _code = 2
            try:                               # so the shutdown flush cannot raise again
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
