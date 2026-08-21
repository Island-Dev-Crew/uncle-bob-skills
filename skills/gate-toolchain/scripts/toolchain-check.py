#!/usr/bin/env python3
"""toolchain-check.py — gate a per-language gate-toolchain manifest.

Checks three things per declared gate, and only these three:
  1. the tool is the mapped implementation for that language + gate;
  2. the command actually names that tool — matched on whole squashed segments,
     so `echo --changed -Dcapital=1` cannot satisfy `pit` by burying `pit`
     inside `capital`, while `cargo mutants` still satisfies `cargo-mutants`
     and `org.pitest:pitest-maven` still satisfies `pitest`;
  3. the loop invocation carries a flag-shaped scoping argument that is present
     in the command and not negated (incremental/diff mode, never whole-repo).
     Negation is caught in either column, wins wherever it sits, and is read
     however the scope column is spelled: every token sharing the declared
     flag's head is inspected, so `--incremental --incremental=false` and
     `--incremental=true --incremental=false` are both disabled in either order
     (fail closed — an ambiguous command is not a scoped run), and a scope whose
     own declared value is falsey is rejected too. Negation means an '='-valued
     spelling (`=false`/`=off`/`=none`/a value that reads as zero); a
     space-separated `--incremental false` is NOT read as negation — see the
     limit fixture. The whole-repo DENY_SCOPE heads are likewise rejected in
     either column: declared, or merely sitting in the command that runs.
     Shell comments are stripped before the scan, so a flag parked behind '#'
     does not count as present.

Quoting has one model, POSIX shell's, applied twice over the same rules:
strip_comment finds the first unquoted WORD-INITIAL '#' honouring backslash
escapes (so `'it'\''s # 1'` and `"it\"s # ok"` are arguments, and `fix#123` is
not a comment), then shlex splits the surviving prefix, resolving quotes and
escapes the way a shell does before any variable or glob expansion. One key
function normalises every token exactly once (_nfc): NFC, plus
the U+FEFF byte-order mark an editor may leave behind. So `"--whole-repo"`,
`--whole"-"repo`, an NFD-pasted flag and a BOM-prefixed one all join the same
key their bare spellings do.

Input:  TSV rows on stdin or from a file. Blank lines and '#' comments skipped.
        A comment is a '#' in the first column (leading spaces allowed, tabs
        not): a '#' sitting after a tab is a data row with an empty first field
        and is reported malformed, never dropped.
        language<TAB>gate<TAB>tool<TAB>scope_arg<TAB>command
Output: one verdict line per row, then a summary line.
Exit:   0 every row mapped and diff-scoped (also: --help printed usage)
        1 verdict — at least one row breaches a rule
        2 usage / IO / closed or unflushable stdout / closed stdin / undecodable
          / malformed or empty manifest / any other internal error (fail closed
          — no error path may borrow the verdict codes)
      130 interrupted — KeyboardInterrupt is caught only to re-signal it as 130,
          so a kill reads as a kill and never as a verdict.
        These four are the only codes this script returns: the tail below seals
        every exit, including argparse's SystemExit and the interpreter's own
        shutdown flush, so a dead output pipe cannot swap in CPython's 120.

Maps are transcribed from the pack's research briefs
(research/crap-metric.md, research/mutation-testing.md); nothing else is claimed.
"""
import argparse
import os
import re
import shlex
import sys
import unicodedata

CRAP_MAP = {
    "java": {"crap4java"}, "go": {"crap4go"}, "clojure": {"crap4clj"},
    "javascript": {"js-crap-score"}, "typescript": {"js-crap-score"},
    "python": {"crap4py", "coco"}, "php": {"phpunit"}, "rust": {"cargo-crap"},
    "csharp": {"crap4dotnet", "ndepend"}, "dotnet": {"crap4dotnet", "ndepend"},
}
MUTATION_MAP = {
    "java": {"pitest"}, "kotlin": {"pitest"}, "scala": {"pitest"}, "jvm": {"pitest"},
    "javascript": {"stryker"}, "typescript": {"stryker"},
    "csharp": {"stryker"}, "dotnet": {"stryker"},
    "python": {"mutmut", "cosmic-ray"}, "rust": {"cargo-mutants"},
    "go": {"gremlins", "go-mutesting"},
}
GATES = {"crap": CRAP_MAP, "mutation": MUTATION_MAP}
ALIASES = {"pit": "pitest", "stryker-js": "stryker", "strykerjs": "stryker",
           "stryker-net": "stryker", "qt-coco": "coco", "cosmicray": "cosmic-ray"}
DENY_SCOPE = {"--all", "--full", "--everything", "--whole-repo", "--all-files",
              "--repo", "--entire-repo", "--no-incremental"}
FALSEY = {"false", "0", "no", "off", "none", ""}
FLAG_RE = re.compile(r"^--?[A-Za-z0-9][A-Za-z0-9._-]*(=.*)?$")
SQUASH_RE = re.compile(r"[^a-z0-9]+")


def _nfc(text: str) -> str:
    """The one key function: Unicode NFC with the BOM dropped.

    An NFD paste joins its NFC twin, and a U+FEFF an editor left at the head of
    the file (or smuggled inside a token) joins the bare spelling instead of
    becoming a new word.
    """
    return unicodedata.normalize("NFC", text).replace("﻿", "")


def _say(message: str) -> None:
    """Best-effort stderr note — a dead stderr must not become the verdict."""
    try:
        print(message, file=sys.stderr)
    except BaseException:
        pass


def _peel(token: str) -> str:
    """Strip surrounding quote pairs — the fallback for unbalanced quoting."""
    while len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        token = token[1:-1]
    return token


def parse_rows(src):
    """Return (rows, errors). A row is (lineno, lang, gate, tool, scope, cmd)."""
    rows, errors = [], []
    for n, line in enumerate(src, 1):
        raw = line.rstrip("\n").rstrip("\r")
        if "\t" not in raw and not raw.strip():
            continue                                    # a truly blank line
        if raw.lstrip(" ").startswith("#"):
            continue                                    # anchored to column 1
        parts = raw.split("\t")
        if len(parts) != 5:
            errors.append(f"line {n}: expected 5 tab-separated fields, got {len(parts)}")
            continue
        lang, gate, tool, scope, cmd = (_nfc(p.strip()) for p in parts)
        if not all([lang, gate, tool, scope, cmd]):
            errors.append(f"line {n}: empty field")
            continue
        rows.append((n, lang.lower(), gate.lower(), tool.lower(), scope, cmd))
    return rows, errors


def strip_comment(cmd: str) -> str:
    """Drop an unquoted shell comment — a '#' that starts a word outside quotes.

    Same escape model shlex then applies, so the two agree on the argv bash
    builds: a backslash outside single quotes escapes the next character, so
    `'it'\\''s # 1'` stays one argument; a '#' that does not start a word
    (`fix#123`) is not a comment; and a trailing flag after either survives.
    """
    quote, word_start, i = "", True, 0
    while i < len(cmd):
        ch = cmd[i]
        if quote == "'":
            if ch == "'":
                quote = ""
            word_start = False
        elif quote == '"':
            if ch == "\\" and i + 1 < len(cmd):
                i += 1
            elif ch == '"':
                quote = ""
            word_start = False
        elif ch == "\\" and i + 1 < len(cmd):
            i += 1
            word_start = False
        elif ch in "\"'":
            quote = ch
            word_start = False
        elif ch.isspace():
            word_start = True
        elif ch == "#" and word_start:
            return cmd[:i]
        else:
            word_start = False
        i += 1
    return cmd


def tokenize(cmd: str) -> list:
    """Split a command the way a shell would, keying every token through _nfc."""
    try:
        return [_nfc(t) for t in shlex.split(cmd)]
    except ValueError:                                   # unbalanced quoting
        return [_peel(_nfc(t)) for t in cmd.split()]


def _segments(text: str) -> list:
    return [s for s in SQUASH_RE.split(text.lower()) if s]


def tool_named(tool: str, canon: str, tokens: list) -> bool:
    """True when the command names the tool as a run of whole squashed segments.

    Anchored, not substring: `pit` is not satisfied by `capital`. Still loose
    across separators and token joins on purpose — `cargo mutants` must satisfy
    `cargo-mutants` and `org.pitest:pitest-maven` must satisfy `pitest`. It
    proves the command names the tool, never that the tool is the process
    that runs.
    """
    hay = []
    for t in tokens:
        hay.extend(_segments(t))
    for name in (tool, canon):
        need = _segments(name)
        if not need:
            continue
        if any(hay[i:i + len(need)] == need for i in range(len(hay) - len(need) + 1)):
            return True
    return False


def scope_status(scope: str, tokens: list) -> str:
    """present | disabled | absent — exact token match, whole command scanned.

    Every token sharing the declared flag's head is inspected before answering,
    however the scope column is spelled, and negation wins wherever it sits: a
    command carrying both `--flag` and `--flag=false` — or both `--flag=true`
    and `--flag=false` — is `disabled` in either order. Fail closed: a command
    that both enables and disables its own scope is not a scoped run. Only an
    '='-valued negation counts; `--flag false` is two tokens, not a negation.
    """
    head = scope.split("=", 1)[0]
    valued = "=" in scope
    present = disabled = False
    for token in tokens:
        if token.split("=", 1)[0] != head:
            continue
        if "=" in token and falsey_value(token):
            disabled = True
        elif token == scope or not valued:
            present = True
    if disabled:
        return "disabled"
    return "present" if present else "absent"


def falsey_value(arg: str) -> bool:
    """True when 'arg' carries an '=' whose value reads as off/false/empty/zero."""
    if "=" not in arg:
        return False
    val = arg.split("=", 1)[1].strip("\"' ").lower()
    if val in FALSEY:
        return True
    try:
        return float(val) == 0.0        # 0, 00, 0.0, -0, 0e9 all read as off
    except (ValueError, OverflowError):
        return False                    # nan/inf/words are not zero


def denied_in_command(tokens: list, declared_head: str) -> list:
    """Whole-repo DENY_SCOPE heads sitting in the command, in first-seen order.

    The declared head is skipped: when the scope column itself is deny-listed
    the declared-scope rule already names it, and one breach deserves one line.
    """
    found = []
    for token in tokens:
        head = token.split("=", 1)[0].lower()
        if head in DENY_SCOPE and head != declared_head and head not in found:
            found.append(head)
    return found


def judge(row):
    """Return a list of breach reasons for one row (empty list == pass)."""
    _, lang, gate, tool, scope, raw_cmd = row
    tokens = tokenize(strip_comment(raw_cmd))
    reasons = []
    table = GATES.get(gate)
    if table is None:
        reasons.append(f"unknown gate '{gate}' (expected one of: {', '.join(sorted(GATES))})")
    else:
        canon = ALIASES.get(tool, tool)
        mapped = table.get(lang)
        if mapped is None:
            reasons.append(f"no mapped {gate} tool for language '{lang}'")
        elif canon not in mapped:
            reasons.append(f"'{tool}' is not the {gate} tool for {lang} (mapped: {', '.join(sorted(mapped))})")
        if not tool_named(tool, canon, tokens):
            reasons.append(f"command does not name '{tool}' (whole-segment match)")
    declared_head = scope.lower().split("=", 1)[0]
    if declared_head in DENY_SCOPE:
        reasons.append(f"scope '{scope}' is a whole-repo run — forbidden inside the loop")
    elif not FLAG_RE.match(scope):
        reasons.append(f"scope '{scope}' is not a flag-shaped argument (expected -x or --xyz[=value])")
    elif falsey_value(scope):
        reasons.append(f"declared scope '{scope}' is itself negated — a scope switched off is no scope")
    else:
        status = scope_status(scope, tokens)
        if status == "disabled":
            reasons.append(f"declared scope '{scope}' is negated in the command")
        elif status == "absent":
            reasons.append(f"declared scope '{scope}' is absent from the command (comments stripped, match is token-exact)")
    for head in denied_in_command(tokens, declared_head):
        reasons.append(f"command runs whole-repo flag '{head}' — forbidden inside the loop")
    return reasons


def main() -> int:
    if sys.stdout is None:   # verdict lines would vanish unannounced
        _say("input error: stdout is closed — a verdict nobody can read is not a verdict")
        return 2
    ap = argparse.ArgumentParser(description="Gate a per-language gate-toolchain manifest.")
    ap.add_argument("manifest", nargs="?", help="TSV manifest (default: stdin)")
    args = ap.parse_args()
    try:                     # a console that cannot encode a row must not abort the run
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError, OSError):
        pass
    try:
        if args.manifest:
            src = open(args.manifest, encoding="utf-8-sig")   # tolerate an editor's BOM
        elif sys.stdin is None:
            print("input error: stdin is closed — nothing to read", file=sys.stderr)
            return 2
        else:
            src = sys.stdin
        with src:
            rows, errors = parse_rows(src)
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print(f"input error: {e}", file=sys.stderr)
        return 2
    if errors:
        for e in errors:
            print(f"malformed: {e}", file=sys.stderr)
        return 2
    if not rows:
        print("empty manifest — nothing declared, nothing proven", file=sys.stderr)
        return 2
    breaches = 0
    for row in rows:
        n, lang, gate, tool, scope, _ = row
        reasons = judge(row)
        if reasons:
            breaches += 1
            for r in reasons:
                print(f"BREACH  line {n}  {lang}/{gate} {tool}: {r}")
        else:
            print(f"ok      line {n}  {lang}/{gate} {tool}  scope={scope}")
    print(f"{len(rows)} declarations, {breaches} breaching")
    return 1 if breaches else 0


if __name__ == "__main__":
    try:
        _code = main()
    except SystemExit as _exc:            # argparse's usage exit and --help land here
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
    except KeyboardInterrupt:             # caught only to re-signal it: a kill reads as a kill
        _code = 130
    except BrokenPipeError:               # IO, never a verdict
        _code = 2
    except BaseException as _exc:         # encode / anything: never a verdict
        _say(f"internal error - {type(_exc).__name__}: {_exc}")
        _code = 2
    for _stream, _fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:                              # the shutdown flush is where CPython swaps in 120
            if _stream is not None:
                _stream.flush()
        except BaseException:
            if _code in (0, 1):           # output that never landed is not a verdict
                _code = 2
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
