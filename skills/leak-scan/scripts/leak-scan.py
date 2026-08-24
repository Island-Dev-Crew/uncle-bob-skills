#!/usr/bin/env python3
"""leak-scan.py — cross-module duplicate-knowledge scanner.

Reports literal FACTS (string and numeric constants) that appear in two or more
DISTINCT files, so each one is either given a single owner or recorded in a
waiver ledger with a reason.

The comparison key is the fact, not the source token. A string keys on its inner
text NFC-normalised, so "X-Idc-Signature", 'X-Idc-Signature' and
`X-Idc-Signature` are one fact and an NFC and an NFD spelling of "café" are one
fact; a number keys on its parsed value, so 300, 300.0, 0x12C and 3_00 are one
fact — and a quoted scalar that IS a number folds onto that value too, so the
"300" of a JSON/YAML config meets the bare 300 of code. Waiver keys are
normalised the same way at load time, so a ledger entry covers every spelling.
Comments (including PHP's '#', which does NOT eat a '#[' attribute), /* */
blocks, Ruby =begin/=end blocks and Python triple-quoted blocks are blanked
before lexing, so prose *about* a fact is not counted as a site.

Detects the literal shape of information leakage only; mirrored schemas and
parallel switches remain human review work.

Usage:
  leak-scan.py [--waivers F] [--ext .py,.ts] [--allow-root D] PATH [PATH ...]

A directory argument is walked with symlinked subdirectories FOLLOWED (guarded
against link loops by directory identity), because os.walk's default skips them
in silence and a shared package reached through a link is exactly where the
counterpart module lives. Followed only INSIDE the authorized roots, though: the
canonical target of every directory walked and every file read must lie under a
PATH argument or under a --allow-root (repeatable). A link that leaves them all
is refused BY NAME (exit 2) rather than read, because a scan is authorized over
what the caller named and a link in the tree can name anything on the machine.

Exit codes — distinct meanings get distinct codes, and 0/1/2/3 are the only codes
this script produces (the interpreter's own 120, from a std-stream flush failing
at shutdown, is sealed off at the bottom of this file). Only 0/1/3 are verdicts;
every usage, IO, decode or internal fault exits 2, so a CI consumer never records
a verdict this scanner did not compute:
  0  clean        every cross-file literal is waived with a reason, or none
                  exist. `--help` also exits 0 by convention: it prints usage
                  and computes no verdict, so do not read a 0 from a run that
                  never scanned as a clean tree
  1  leakage      at least one unwaived literal appears in >= 2 files
  2  usage/IO     bad arguments, unreadable path or directory, a symlink whose
                  target leaves every authorized root, undecodable or malformed
                  waiver ledger, a closed or broken stdout — including
                  a --help or usage message that could not be written — fewer
                  than 2 distinct files to compare (fail-closed: a single-file
                  scan cannot detect cross-module leakage), an interrupt, or any
                  unexpected fault
  3  stale waiver the ledger waives a fact that IS present in the scanned set but
                  no longer leaks across it, or a waiver whose fact is absent
                  from the scanned set entirely. --no-stale suppresses both (it
                  is the only stale flag; there is no --strict-stale)
"""
import argparse
import math
import os
import re
import sys
import unicodedata
from collections import defaultdict

EXIT_CLEAN, EXIT_LEAK, EXIT_USAGE, EXIT_STALE = 0, 1, 2, 3

DEFAULT_EXTS = (".py", ".js", ".ts", ".tsx", ".go", ".java", ".rb", ".rs",
                ".php", ".cs", ".kt", ".sql", ".json", ".yaml", ".yml")

# Per-extension noise profile. VALUES ARE REGEX FRAGMENTS matching a comment
# OPENER, not literal tokens, because one language's opener is another's data:
# PHP 8 attributes start '#[' and are exactly where route paths and queue names
# live, so PHP's '#' rule is anchored to refuse '#[' rather than deleting the
# line. An extension absent from every table below gets no comment stripping at
# all — that limitation is stated in SKILL.md.
LINE_COMMENTS = {
    ".py": ("#",), ".rb": ("#",), ".yaml": ("#",), ".yml": ("#",),
    ".sql": ("--",), ".php": ("//", r"#(?!\[)"),
    ".js": ("//",), ".ts": ("//",), ".tsx": ("//",), ".go": ("//",),
    ".java": ("//",), ".rs": ("//",), ".cs": ("//",), ".kt": ("//",),
}
TRIPLE_STRING_EXTS = frozenset({".py"})
BACKTICK_EXTS = frozenset({".js", ".ts", ".tsx", ".go"})

_TRIPLE = r'"""[\s\S]*?"""' + r"|'''[\s\S]*?'''"
_BLOCK_C = r"/\*[\s\S]*?\*/"
# Ruby's block comment. Line-anchored (re.M) because =begin/=end are only
# comment markers in column 0. Without it, .rb documentation counts as a site.
_BLOCK_RUBY = r"^=begin[\s\S]*?^=end[^\n]*"
BLOCK_COMMENTS = {ext: _BLOCK_C for ext in (".js", ".ts", ".tsx", ".go",
                                            ".java", ".rs", ".cs", ".kt",
                                            ".php", ".sql")}
BLOCK_COMMENTS[".rb"] = _BLOCK_RUBY
_QUOTED = r'"(?:[^"\\\n]|\\.)*"' + r"|'(?:[^'\\\n]|\\.)*'"
_BACKTICK = r"`(?:[^`\\]|\\.)*`"

# Numbers reject any neighbouring identifier/dot character, so sha256 and 1.2.3
# contribute nothing. Hex and _-separated spellings fold onto the same value.
_NUM_BODY = r"0[xX][0-9a-fA-F][0-9a-fA-F_]*|\d[\d_]*(?:\.\d[\d_]*)?"
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_.])(?:" + _NUM_BODY + r")(?![A-Za-z0-9_.])")
_NUM_WHOLE = re.compile(r"(?:" + _NUM_BODY + r")\Z")

MIN_STRING_CHARS = 3   # inner length; "", "/", "ok" are below the floor
MIN_NUMBER_CHARS = 2   # canonical decimal spelling; single digits are below it
TRIVIAL_NUMBERS = (0, 1)
# Ceiling on numeric size. Python's default int<->str limit is 4300 digits
# (CVE-2020-10735 mitigation) and raising it past a bound would invite quadratic
# conversion, so the bound is declared here rather than inherited: a token whose
# canonical decimal spelling is longer than this is refused as a CANDIDATE —
# never parsed to inf (which collides distinct giants onto one key) and never
# crashed on. Stated as a named blind spot in SKILL.md.
MAX_NUMBER_DIGITS = 20000
try:
    sys.set_int_max_str_digits(MAX_NUMBER_DIGITS)
except AttributeError:      # Python < 3.11 has no limit to raise
    pass

# Directories never walked: VCS metadata and dependency/build caches, which hold
# no reviewable source. Every OTHER dot-directory IS walked, so a fact restated
# in .github/workflows/ is a site like any other.
SKIPPED_DIRS = frozenset({
    ".git", ".hg", ".svn", "__pycache__",
    ".venv", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
})

_noise_cache, _string_cache = {}, {}


def die(msg):
    print(f"leak-scan: {msg}", file=sys.stderr)
    raise SystemExit(EXIT_USAGE)


def noise_re(ext):
    """Regex whose blanking groups are comments and whose keep groups are
    strings — strings are matched only so a '#' or '//' inside one survives."""
    if ext in _noise_cache:
        return _noise_cache[ext]
    # Order is load-bearing: a triple-quoted block opens with a quote, so it
    # must precede the plain string alternative or '"""' is consumed as the
    # empty string '""'. Everything else is disambiguated by start position.
    parts, n = [], 0
    if ext in TRIPLE_STRING_EXTS:
        parts.append(f"(?P<c{n}>{_TRIPLE})")
        n += 1
    parts.append(f"(?P<k0>{_QUOTED})")
    if ext in BACKTICK_EXTS:
        parts.append(f"(?P<k1>{_BACKTICK})")
    blank = ([BLOCK_COMMENTS[ext]] if ext in BLOCK_COMMENTS else []) + \
            [p + r"[^\n]*" for p in LINE_COMMENTS.get(ext, ())]
    for pattern in blank:
        parts.append(f"(?P<c{n}>{pattern})")
        n += 1
    # re.M so a line-anchored block comment (Ruby's =begin/=end) can say so; no
    # other alternative in this set uses ^ or $.
    rx = re.compile("|".join(parts), re.M) if n else None
    _noise_cache[ext] = rx
    return rx


def string_re(ext):
    if ext not in _string_cache:
        alts = [_BACKTICK, _QUOTED] if ext in BACKTICK_EXTS else [_QUOTED]
        _string_cache[ext] = re.compile("|".join(alts))
    return _string_cache[ext]


def strip_noise(text, ext):
    rx = noise_re(ext)
    if rx is None:
        return text
    out, pos = [], 0
    for m in rx.finditer(text):
        if (m.lastgroup or "").startswith("k"):
            continue
        out.append(text[pos:m.start()])
        out.append(re.sub(r"[^\n]", " ", m.group(0)))
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)


def number_text(value):
    """Canonical decimal spelling of a parsed value, or None past the declared
    digit ceiling. Nothing else in this script calls str() on a parsed number,
    so an oversized token can never raise."""
    try:
        return str(value)
    except ValueError:
        return None


def number_key(tok):
    """Exact parsed value of a numeric token, or None when the token is not a
    finite, in-range number. 300, 300.0, 0x12C, 3_00 -> 300. Integer spellings
    parse with int(), never float(), so two distinct 400-digit constants stay two
    facts instead of folding onto inf."""
    t = tok.replace("_", "")
    try:
        if t[:2].lower() == "0x":
            value = int(t, 16)
        elif "." in t:
            val = float(t)
            if not math.isfinite(val):
                return None
            value = int(val) if val.is_integer() else val
        else:
            value = int(t)
    except ValueError:
        return None          # not a number, or past MAX_NUMBER_DIGITS
    return value if number_text(value) is not None else None


def number_ok(value):
    """A parsed value clears the numeric floor and is not 0 or 1."""
    text = None if value is None else number_text(value)
    return (text is not None and value not in TRIVIAL_NUMBERS
            and len(text.lstrip("-")) >= MIN_NUMBER_CHARS)


def scalar_key(inner):
    """Key one bare scalar. A whole numeric spelling folds onto its value, so a
    config file's "900" and a module's bare 900 are the same fact; anything else
    keys on its NFC-normalised text. NFC folding is the same hazard the path side
    folds in file_identity(): macOS hands back NFD routinely, so one fact written
    in two normal forms would otherwise be two keys and its leak invisible. This
    is THE key function — the lexer and waiver_key() both route through it, so
    ledger and scan can never key differently."""
    s = inner.strip()
    if _NUM_WHOLE.match(s):
        value = number_key(s)
        if value is not None:
            return ("n", value)
    return ("s", unicodedata.normalize("NFC", inner))


def display(key):
    kind, value = key
    return f'"{value}"' if kind == "s" else str(value)


def file_identity(path):
    """THE key that decides whether two spellings name one file: (device, inode).
    It folds every spelling variant onto one entry — letter case on a
    case-insensitive filesystem (APFS, NTFS), Unicode NFC vs NFD (routine on
    macOS), './', '../' and '//' segments, absolute vs relative, trailing
    slashes, symlinks and hard links. Path-string comparison folds none of those,
    and counting one file twice would report every literal in it as a cross-file
    leak. Falls back to the case-normalised real path only where inodes are
    unavailable (st_ino == 0 on some Windows filesystems)."""
    try:
        st = os.stat(path)
    except OSError as e:
        die(f"cannot stat {path}: {e}")
    return (st.st_dev, st.st_ino) if st.st_ino else \
        os.path.normcase(os.path.realpath(path))


def canonical(path):
    """The one spelling a containment test may compare: fully resolved and
    case-folded. Every '.', '..', '//' segment and every symlink component is
    gone, so a prefix test on it is a statement about the filesystem rather than
    about the string the caller typed."""
    return os.path.normcase(os.path.realpath(path))


def require_inside(path, roots):
    """PATH AUTHORITY: this scan may read exactly what the caller named. Every
    directory the walk descends into and every file it reads must resolve inside
    an authorized root — a PATH argument, or a --allow-root. A symlink inside a
    walked tree can point at a sibling checkout, ~/.ssh or /etc, and following
    one made this scanner read, and PRINT lines from, files nobody authorized it
    to open; documenting that behaviour is not authority to take it. An escape is
    refused BY NAME and fail-closes (exit 2) — reading it is unauthorized, and
    pruning it in silence would be the same false green os.walk's followlinks
    default already produced once. --allow-root is how a caller expands the scan
    deliberately, which is a decision they make rather than one a link makes for
    them. Not a sandbox: a HARD link, or a bind mount, is a real entry inside the
    tree and no path test can see through it."""
    real = canonical(path)
    for r in roots:
        if real == r or real.startswith(r.rstrip(os.sep) + os.sep):
            return
    die(f"{path} resolves to {os.path.realpath(path)}, outside every authorized "
        f"root — pass --allow-root to authorize that target, or take the link "
        f"out of the scanned tree")


def collect_files(paths, exts, allow_roots=()):
    roots = [canonical(p) for p in paths]
    for r in allow_roots:
        if not os.path.exists(r):
            die(f"--allow-root {r}: no such path")
        roots.append(canonical(r))
    found = []
    for p in paths:
        if os.path.isdir(p):
            # BOTH os.walk defaults would change a verdict in silence, so both
            # are overridden here.
            #   onerror: the default SWALLOWS every OSError and yields nothing
            #     for that subtree, so an unreadable directory made the gate
            #     certify a tree it never read (exit 0) instead of fail-closing.
            #   followlinks: the default SKIPS a symlinked subdirectory whole,
            #     with no error at all. That is the ordinary monorepo layout — a
            #     service reaching its shared package through a link (workspaces,
            #     vendor/, a checked-in link to a sibling repo) — and the whole
            #     counterpart module went unread, so the leak between it and the
            #     client came back 0. A false GREEN on realistic input.
            # Following links needs a cycle guard or a link loop walks forever,
            # so each directory is entered once per (device, inode) — the same
            # identity the file dedupe below already keys on.
            def walk_error(e, _p=p):
                die(f"cannot walk {getattr(e, 'filename', None) or _p}: {e}")

            walked = set()
            for root, dirs, names in os.walk(p, onerror=walk_error,
                                             followlinks=True):
                ident = file_identity(root)
                if ident in walked:
                    dirs[:] = []        # a link loop back into a walked subtree
                    continue
                walked.add(ident)
                kept = []
                for d in dirs:
                    if d in SKIPPED_DIRS:
                        continue
                    require_inside(os.path.join(root, d), roots)
                    kept.append(d)
                dirs[:] = kept
                for n in sorted(names):
                    # Extensions are compared case-folded: a leak stated in
                    # SERVER.PY must not be invisible to a --ext .py walk.
                    if n.lower().endswith(exts):
                        f = os.path.join(root, n)
                        require_inside(f, roots)
                        found.append(f)
        elif os.path.isfile(p):
            found.append(p)
        else:
            die(f"no such path: {p}")
    seen, uniq = set(), []
    for f in found:
        ident = file_identity(f)
        if ident not in seen:
            seen.add(ident)
            uniq.append(f)
    return sorted(uniq)


def literals(path):
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as e:
        die(f"cannot read {path}: {e}")
    srx = string_re(ext)
    out = []
    # split("\n"), never splitlines(): splitlines() also breaks on U+2028, \x0b
    # and \x0c, which would cut a string literal containing one of them in half
    # so neither half lexes — a fact made invisible by a character no editor
    # shows. A line here is what a '\n' count calls a line.
    for lineno, line in enumerate(strip_noise(text, ext).split("\n"), 1):
        masked = list(line)
        for m in srx.finditer(line):
            inner = m.group(0)[1:-1]
            key = scalar_key(inner)
            if key[0] == "n":
                if number_ok(key[1]):
                    out.append((key, lineno))
            elif len(inner) >= MIN_STRING_CHARS and inner.strip():
                out.append((key, lineno))
            for i in range(m.start(), m.end()):
                masked[i] = " "
        for m in NUMBER_RE.finditer("".join(masked)):
            value = number_key(m.group(0))
            if number_ok(value):
                out.append((("n", value), lineno))
    return out


def waiver_key(raw):
    """Normalise a ledger entry onto the same fact key the lexer produces."""
    s = raw.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'`":
        return scalar_key(s[1:-1])
    return scalar_key(s)


# Line-breaking control characters a source literal can never contain (a quoted
# literal cannot span a newline, and an escape like \r is backslash-r in the
# source text). In a ledger they are unreadable, so they are refused rather
# than folded into a key nothing can match.
CONTROL_IN_LITERAL = ("\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e",
                      "\x85", "\u2028", "\u2029")


def load_waivers(path):
    waivers, first_line = {}, {}
    try:
        # utf-8-sig, not utf-8: a BOM is what every Windows editor and Excel
        # writes, and under plain utf-8 it survives as U+FEFF on the literal of
        # row 1 — str.strip() does not remove it — silently rerouting that row to
        # a key nothing can match. -sig strips a leading BOM and is a no-op
        # otherwise. A non-UTF-8 byte still raises and still exits 2 below.
        with open(path, encoding="utf-8-sig") as fh:
            raw = fh.read()
    except (OSError, UnicodeDecodeError, UnicodeError) as e:
        # A decode fault is an IO fault, not a verdict. UnicodeDecodeError is a
        # ValueError, so without this arm it escaped to the interpreter and the
        # process exited 1 — the code reserved for 'leakage found'.
        die(f"cannot read waiver ledger {path}: {e}")
    # Text mode already folded \r\n and a lone \r onto \n, so a CRLF ledger reads
    # normally and a bare CR mid-row splits it — caught below as a row with no
    # TAB (exit 2), never a silent mis-key. split("\n") rather than splitlines()
    # for the reason literals() gives: splitlines() ALSO breaks on \x0b, \x0c and
    # U+2028, which would cut a row apart on a character no editor shows. Those
    # survive here instead, and CONTROL_IN_LITERAL refuses them out loud.
    lines = raw.split("\n")
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        # ONE anchored rule, so no data row can ever vanish unannounced: a ledger
        # comment is a line whose first non-blank character is '#' AND that holds
        # no TAB. A '#' line that DOES hold a tab is ambiguous — comment, or a
        # waiver for a fact whose text starts with '#' — so it is refused out
        # loud (exit 2) rather than guessed at. Facts starting with '#' (a colour
        # token, '# nosec') are waivable in their quoted spelling, which does not
        # start with '#' and is read as data like any other row.
        head = line.lstrip()
        if head.startswith("#"):
            if "\t" not in line:
                continue
            die(f"{path}:{n} ambiguous — a '#' line holding a TAB is neither a "
                f"comment nor a readable waiver. Drop the tab to comment, or "
                f'quote the literal ("#0B5FFF") to waive a fact starting with #')
        if "\t" not in line:
            die(f"{path}:{n} malformed — expected LITERAL, TAB, reason")
        lit, reason = line.split("\t", 1)
        lit, reason = lit.strip(), reason.strip()
        if not lit or not reason:
            die(f"{path}:{n} malformed — empty literal or empty reason")
        bad = next((c for c in CONTROL_IN_LITERAL if c in lit), None)
        if bad is not None:
            die(f"{path}:{n} malformed — literal holds control character "
                f"U+{ord(bad):04X}; no source literal can contain one, so this "
                f"row could only key onto a fact that does not exist")
        key = waiver_key(lit)
        if key == ("s", ""):
            die(f"{path}:{n} malformed — literal is empty once unquoted")
        if key in waivers:
            # 'no data row is ever dropped in silence' has to hold here too: two
            # rows for one fact (often two SPELLINGS of it — 300 and 0x12C) used
            # to let the last one win and the first vanish unmentioned.
            die(f"{path}:{n} duplicate waiver for {display(key)} — already "
                f"waived at line {first_line[key]}; one fact gets one row")
        first_line[key] = n
        waivers[key] = reason
    return waivers


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", help="files or directories to scan")
    ap.add_argument("--waivers", help="TSV ledger: literal, TAB, reason")
    ap.add_argument("--ext", default=",".join(DEFAULT_EXTS),
                    help="comma-separated extensions walked inside directories")
    ap.add_argument("--allow-root", action="append", default=[], metavar="DIR",
                    help="authorize ONE more root the walk may follow a symlink "
                         "into (repeatable). Without it, a link whose target "
                         "leaves every PATH argument is refused, not read")
    ap.add_argument("--no-stale", action="store_true",
                    help="changed-set runs: report leakage only, never stale "
                         "waivers (exit 3 becomes impossible). Staleness is a "
                         "claim about the whole tree the ledger governs, which "
                         "a scan of a changed pair cannot see")
    args = ap.parse_args(argv)

    if not args.paths:
        die("no paths given")
    exts = tuple(e.lower() if e.startswith(".") else "." + e.lower()
                 for e in (s.strip() for s in args.ext.split(",")) if e)
    if not exts:
        die("--ext resolved to an empty extension set")

    files = collect_files(args.paths, exts, args.allow_root)
    if len(files) < 2:
        die(f"{len(files)} comparable file(s) — fewer than two modules cannot "
            f"exhibit cross-module leakage, so this scan cannot pass. Widen the "
            f"scope to the counterpart modules the changed file talks to")

    sites = defaultdict(list)
    for f in files:
        for key, ln in literals(f):
            sites[key].append((f, ln))
    leaks = {k: sorted(set(locs)) for k, locs in sites.items()
             if len({f for f, _ in locs}) >= 2}

    waivers = load_waivers(args.waivers) if args.waivers else {}
    unwaived = sorted(k for k in leaks if k not in waivers)
    applied = sorted(set(waivers) & set(leaks))
    # Staleness is scope-sensitive and says so. A stale verdict is only sound
    # when the scan covers the whole tree the ledger governs: over a changed
    # PAIR, a waiver looks dead simply because its other site was not scanned.
    # So the report distinguishes the two shapes instead of asserting the strong
    # one for both, and --no-stale drops the question entirely for changed-set
    # runs — which is what makes 'exit 0 over the changed pair' and 'zero stale
    # entries' two satisfiable boxes rather than one contradiction.
    stale, absent = [], []
    if not args.no_stale:
        stale = sorted(k for k in waivers if k in sites and k not in leaks)
        absent = sorted(k for k in waivers if k not in sites)

    print(f"scanned {len(files)} files, exts {','.join(exts)}")
    for key in unwaived:
        print(f"LEAK  {display(key)}  in {len({f for f, _ in leaks[key]})} files")
        for f, ln in leaks[key]:
            print(f"        {f}:{ln}")
    for key in applied:
        print(f"waived {display(key)}  — {waivers[key]}")
    for key in stale:
        n_files = len({f for f, _ in sites[key]})
        print(f"STALE  {display(key)}  waived, but stated in only {n_files} "
              f"scanned file{'' if n_files == 1 else 's'} — no longer leaking "
              f"across this scan")
    for key in absent:
        print(f"STALE  {display(key)}  waived, but absent from the scanned set "
              f"— stale if this scan covers the tree the ledger governs, "
              f"otherwise merely out of scope (re-run with --no-stale)")
    print(f"{len(leaks)} cross-file literals, {len(unwaived)} unwaived, "
          f"{len(applied)} waivers applied, {len(stale) + len(absent)} stale "
          f"({len(absent)} of them absent from the scan)")

    if unwaived:
        return EXIT_LEAK
    if stale or absent:
        return EXIT_STALE
    return EXIT_CLEAN


def _run():
    """Every fault that is not a verdict leaves through EXIT_USAGE. Without this
    arm an unexpected exception exits 1 — 'leakage found' — and a CI consumer
    records a verdict that was never computed."""
    if sys.stdout is None:
        # fd 1 already closed at startup (`>&-`): CPython sets sys.stdout to
        # None, every print() silently becomes a no-op, and the old code then
        # raised AttributeError on .flush() — twice, once inside the handler —
        # so the exception escaped to the interpreter and the process exited 1.
        # A verdict nobody can read is not a verdict: refuse, out loud, on 2.
        print("leak-scan: no verdict computed — stdout is closed, so the report "
              "cannot be written", file=sys.stderr)
        return EXIT_USAGE
    try:
        rc = main()
        sys.stdout.flush()      # inside the guard: a closed pipe fails HERE,
        return rc               # not at shutdown, where the code would be 120
    except SystemExit:
        raise
    except (Exception, KeyboardInterrupt) as e:     # noqa: BLE001 - deliberate
        # Nothing may reach the interpreter's own handler, which exits 1 (or 120
        # on a pipe fault at shutdown flush) — both codes belong to verdicts this
        # run never computed. Detach stdout first so the shutdown flush is
        # silent; that detach must not be able to raise a SECOND time, so it
        # catches the AttributeError/ValueError a None or closed stdout gives.
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except (OSError, AttributeError, ValueError):
            pass
        if isinstance(e, KeyboardInterrupt):
            kind = "interrupted before the verdict was computed"
        elif isinstance(e, (BrokenPipeError, ValueError)):
            kind = "stdout closed before the report finished"
        else:
            kind = f"internal fault: {type(e).__name__}: {e}"
        print(f"leak-scan: no verdict computed — {kind}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    # The seal. _run() covers everything that reaches IT, but two things route
    # around it: argparse's usage-exit and --help raise SystemExit before any of
    # its handlers, and CPython flushes std streams at interpreter SHUTDOWN,
    # after this module is done. If that shutdown flush raises — a pipe whose
    # reader is gone (`--help | head -1`), a closed fd — the interpreter REPLACES
    # the status with 120, a code this script's table does not name and no CI
    # consumer can read. So the exit is taken here, with the flush forced first.
    try:
        _code = _run()
    except SystemExit as _e:          # argparse usage errors and --help
        _code = _e.code if isinstance(_e.code, int) else (0 if _e.code is None else 1)
    except BaseException as _e:       # no unexpected error may wear a verdict's code
        try:
            print(f"leak-scan: no verdict computed — internal fault: "
                  f"{type(_e).__name__}: {_e}", file=sys.stderr)
        except BaseException:
            pass
        _code = EXIT_USAGE
    for _stream, _fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if _stream is not None:
                _stream.flush()
        except BaseException:
            if _code in (EXIT_CLEAN, EXIT_LEAK):   # output that never landed is
                _code = EXIT_USAGE                 # not a verdict
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
