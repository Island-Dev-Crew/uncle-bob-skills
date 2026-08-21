#!/usr/bin/env python3
"""surface-check.py - verdict on a review-surface manifest.

A manifest declares the criticality tier of one change and the artifacts a human
actually reads before signing off. This script checks that the declared surface
matches what the tier requires - in BOTH directions: a dangerous change reviewed
without its code, and a routine change whose reviewer opened the diff anyway.

Manifest grammar (one key per line, '#' comments and blank lines ignored):

    tier: routine | elevated | critical     (exactly one, required)
    spec: <path>                            (exactly one, required)
    qa:   <path>                            (exactly one, required)
    code: <path>                            (zero or more; tier decides)

A line is what a human sees as a line. The manifest's BYTES are decoded here, not
read through Python's universal-newline translation, which would rewrite a bare
'\\r' into '\\n' during decode and split a line the reader sees as one; the text
is then split on '\\n' alone, with one trailing '\\r' per line tolerated and a
single leading BOM stripped, so the manifest a Windows editor writes still parses.
TAB is the one control character a line may carry ANYWHERE in it (KEY_RE and
COMMENT_RE both allow it as a separator); a single trailing '\\r' is the one
other tolerance, stripped as a CRLF ending above before the check runs. EVERY
other control character - the whole C0 and C1 range plus U+007F, which includes
the separators str.splitlines() would ALSO break on: U+000B U+000C U+000D
U+001C-U+001E U+0085 - and the Unicode line/paragraph separators U+2028 U+2029,
is malformed input, because a line the parser and the reader disagree about is
how a 'code:' declaration hides inside what looks like a comment. Refuse it;
never reroute. A CR anywhere but at end-of-line is refused like the rest.

Paths are RELATIVE, resolved against the MANIFEST's own directory, never the
cwd; declared_path() is the single place that join happens. An absolute value is
malformed rather than silently rerouted: it ignores the manifest's directory
entirely, so the same manifest would judge different files on different machines.
A relative value that climbs with '..' is still relative and still allowed.

Prose artifacts (spec, qa) take TWO size ceilings, because one is evadable:
a newline count alone passes a 24 KB QA procedure whose steps are packed one
per line, which is an ordinary markdown-list shape and exactly the "nominally
reviewed, actually skimmed" artifact the budget exists to catch. --max-lines
sets the line ceiling; --max-bytes sets the absolute one and defaults to
max_lines * 80 (an 80-column line) so the two move together.

Exit codes - distinct meanings, never shared, and no fourth the script can RETURN
(a death by signal is still the OS's status, not this gate's):
    0  every manifest clears its tier's surface requirement
    1  VERDICT: at least one surface breach (the gate saying no)
    2  usage / IO / malformed manifest, an unexpected internal error, or a
       verdict that could not be reported - nothing was judged or nothing was
       delivered, fail closed
The seal at the bottom of this file is what makes 'no fourth' a fact rather than
an intention: it catches BaseException and flushes BOTH streams while an error
can still be caught, so neither an unhandled exception (1) nor a failed
interpreter-shutdown flush (120) can substitute a code this table does not name.
"""
import os
import re
import sys
import unicodedata
from pathlib import Path

# Anchored, no interpolation: only these four keys are legal, anywhere in a
# manifest. An unrecognised key is malformed input (exit 2), never a silent
# skip - a typo'd 'cod:' must not let a critical change through with no code.
KEY_RE = re.compile(r"^(tier|spec|qa|code)[ \t]*:[ \t]*(\S.*?)[ \t]*$")
COMMENT_RE = re.compile(r"^[ \t]*(#.*)?$")

# Every control character except TAB - the whole C0 range bar \t and \n, plus
# U+007F and the C1 range U+0080-U+009F (U+0085 NEL lives there) - and the two
# Unicode separators U+2028/U+2029. \n never reaches here: it is the splitter.
# Checked BEFORE the comment rule, so a '#' line can never carry a hidden second
# line past the reader.
CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f\u2028\u2029]")

# code policy per tier. The ladder is the island's construction (advisory);
# this table is the only place it is encoded.
TIERS = {"routine": "forbidden", "elevated": "optional", "critical": "required"}

DEFAULT_MAX_LINES = 120  # human-facing prose budget; code is never budgeted
BYTES_PER_LINE = 80  # derives the absolute ceiling from the line one: 120 lines -> 9600 bytes
MAX_BUDGET = 10**9  # explicit ceiling on --max-lines/--max-bytes; see take_int_flag()


class Malformed(Exception):
    """Manifest cannot be parsed into a verdict. Exit 2, not a verdict."""


def parse(path: Path) -> dict:
    try:
        # read_BYTES, not read_text: read_text opens with newline=None, so universal
        # -newline translation rewrites a bare '\r' into '\n' during decode - the
        # parser would split a line the reader sees as one, and CONTROL_RE would
        # never get to see the CR. Decode ourselves; strip only a leading BOM, which
        # a Windows editor writes and no reader ever sees.
        text = path.read_bytes().decode("utf-8")
        if text.startswith("\ufeff"):
            text = text[1:]
    except UnicodeDecodeError as e:
        # A ValueError, not an OSError: without this it escapes main()'s handler and
        # crashes with exit 1 - the code reserved for a VERDICT. Nothing was judged
        # here, so it must fail closed on 2 like every other unreadable manifest.
        raise Malformed(f"{path}: manifest is not valid UTF-8 ({e})")
    keys: dict = {"tier": [], "spec": [], "qa": [], "code": []}
    for n, raw in enumerate(text.split("\n"), 1):
        line = raw[:-1] if raw.endswith("\r") else raw
        bad = CONTROL_RE.search(line)
        if bad:
            raise Malformed(
                f"{path}:{n}: control character U+{ord(bad.group()):04X} in line - the parser "
                f"and the reader would see different lines here -> {line.strip()!r}"
            )
        if COMMENT_RE.match(line):
            continue
        m = KEY_RE.match(line)
        if not m:
            raise Malformed(f"{path}:{n}: not a 'key: value' line -> {line.strip()!r}")
        keys[m.group(1)].append(m.group(2))
    for single in ("tier", "spec", "qa"):
        if len(keys[single]) > 1:
            raise Malformed(f"{path}: duplicate '{single}:' line ({len(keys[single])} found)")
    if not keys["tier"]:
        raise Malformed(f"{path}: no 'tier:' line - an unlabelled surface cannot pass")
    if keys["tier"][0] not in TIERS:
        raise Malformed(f"{path}: unknown tier {keys['tier'][0]!r}; expected one of {sorted(TIERS)}")
    return keys


def declared_path(label: str, value: str, base: Path) -> Path:
    """The ONE place a declared value becomes a filesystem path.

    Absolute values are refused rather than rerouted: they ignore `base` entirely, so
    the same manifest would judge different files on different machines. Relative is
    the whole contract here - containment is NOT claimed, '..' resolves as written.
    A path the OS cannot even name (an embedded NUL raises ValueError, an over-long
    one raises OSError) is malformed input, not a breach - nothing was judged, so it
    must land on 2 like every other unreadable manifest, never on the VERDICT code."""
    if value.startswith("/") or Path(value).is_absolute():
        raise Malformed(f"{label} {value!r}: absolute path - declare it relative to the manifest")
    try:
        return (base / value).resolve()
    except (OSError, ValueError) as e:
        raise Malformed(f"{label} {value!r}: unusable path ({e})")


def has_substance(data: bytes) -> bool:
    """True when the file carries one character that is neither whitespace nor Cf.

    bytes.strip() knows only the seven ASCII blanks, so a file of non-breaking
    spaces - or the three bytes a Windows editor writes when it saves a file with
    nothing in it, U+FEFF - used to count as content and clear the critical tier.
    Decode first, then reject BOTH Unicode whitespace (str.isspace(): U+00A0,
    U+2007, U+3000 ...) and the format characters str.isspace() does not count -
    Unicode category Cf, which is the BOM, the zero-width space/joiners, the word
    joiner, the soft hyphen and the bidi marks. Undecodable bytes become U+FFFD,
    a visible character: a binary file has substance, it is just not prose.

    The rule is mechanical and so is its LIMIT, which is disclosed rather than
    patched: a codepoint that is neither whitespace nor Cf counts as substance
    even when it renders blank - braille-blank U+2800 (So) and the Hangul fillers
    (Lo) do. fixtures/limit-blank-glyph-critical.manifest ships PASSING to hold
    that edge as a run. Do not read this helper as 'nothing invisible gets by'."""
    return any(
        not ch.isspace() and unicodedata.category(ch) != "Cf"
        for ch in data.decode("utf-8", "replace")
    )


def substance_breach(label: str, value: str, p: Path) -> str:
    """The ONE exist-and-has-content test every declared artifact takes - spec, qa and
    code alike. 'Non-empty' means at least one non-whitespace, non-format character
    (has_substance, limit and all), not 'splitlines() returned something' and not
    'some byte survived bytes.strip()': `touch`ing
    a file must not satisfy the critical tier's demand for a real implementation path,
    three blank lines are not a Gherkin spec, and neither is a screenful of invisible
    Unicode. Returns '' when the artifact has substance."""
    if not p.is_file():
        return f"{label} '{value}' does not exist - nothing to review"
    if not has_substance(p.read_bytes()):
        return f"{label} '{value}' has no visible content - nothing to review"
    return ""


def prose_breaches(label: str, values: list, base: Path, cap: int, byte_cap: int) -> list:
    """spec/qa: the shared substance test, plus BOTH size ceilings a human budget needs.

    Newlines alone are not a size: prose packed onto few long lines - a numbered list
    with no blank lines between items is the ordinary case - sails under any line cap
    while carrying tens of kilobytes. The byte ceiling is what makes the claim absolute;
    the line ceiling is what keeps a merely wide artifact honest. Both are reported."""
    if not values:
        return [f"no '{label}:' artifact declared - the human surface is incomplete"]
    p = declared_path(label, values[0], base)
    hollow = substance_breach(label, values[0], p)
    if hollow:
        return [hollow]
    out = []
    n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
    if n > cap:
        out.append(f"{label} '{values[0]}' is {n} lines, over the {cap}-line human budget")
    size = len(p.read_bytes())
    if size > byte_cap:
        out.append(
            f"{label} '{values[0]}' is {size} bytes on {n} line(s), over the "
            f"{byte_cap}-byte human budget - packed prose is still prose"
        )
    return out


def judge(path: Path, cap: int, byte_cap: int) -> list:
    keys = parse(path)
    base = path.resolve().parent
    tier = keys["tier"][0]
    policy = TIERS[tier]
    out = prose_breaches("spec", keys["spec"], base, cap, byte_cap)
    out += prose_breaches("qa", keys["qa"], base, cap, byte_cap)
    code = keys["code"]
    if policy == "forbidden" and code:
        out.append(
            f"tier '{tier}' lists {len(code)} code path(s) - reading implementation at this "
            "tier re-imposes the slowness the architecture removes; raise the tier or drop it"
        )
    if policy == "required" and not code:
        out.append(f"tier '{tier}' requires at least one 'code:' path; none declared")
    for c in code:
        hollow = substance_breach("code", c, declared_path("code", c, base))
        if hollow:
            out.append(hollow)
    return out


def take_int_flag(args: list, flag: str):
    """Pull '<flag> N' out of args in place. Returns None when absent; raises
    Malformed (exit 2) on a missing or non-positive value - a budget nobody can
    parse must not silently fall back to a default and print a verdict. The upper
    bound is explicit rather than borrowed from the interpreter: a 5000-digit
    argument raises ValueError under CPython's int_max_str_digits, but that limit
    is tunable, so MAX_BUDGET is what makes the refusal the same on every box."""
    if flag not in args:
        return None
    i = args.index(flag)
    try:
        v = int(args[i + 1])
        if not 1 <= v <= MAX_BUDGET:
            raise ValueError
    except (IndexError, ValueError):
        raise Malformed(f"usage error: {flag} needs an integer in 1..{MAX_BUDGET}")
    del args[i : i + 2]
    return v


def err(msg: str) -> None:
    """ERROR lines go to stderr and nowhere else, and this NEVER raises.

    Two ways stderr is gone, and both must be swallowed here. (1) fd 2 was closed at
    exec: sys.stderr is None and print() falls back to STDOUT, dropping an ERROR line
    into the middle of the verdict report a CI consumer parses. (2) fd 2 is a pipe whose
    reader is gone: the write raises BrokenPipeError. That one used to escape - err() is
    called from inside main() AND from the seal's own except handler, and an exception
    raised inside an except handler is not caught by its sibling clauses, so it walked
    out past the seal and the interpreter exited 120 on a usage error. Either way the
    exit code carries the refusal on its own; fd 2 is pointed at /dev/null so the
    shutdown flush cannot fail either."""
    if sys.stderr is None:
        return
    try:
        print(msg, file=sys.stderr)
        sys.stderr.flush()
    except BaseException:
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), 2)
        except BaseException:
            pass


def main(argv: list) -> int:
    args = list(argv)
    if sys.stdout is None:
        # A verdict nobody can read is not a verdict. Fail closed on 2 rather than
        # returning a silent 0/1 that a CI consumer would record with no report.
        err("ERROR  stdout is closed - cannot report a verdict")
        return 2
    try:
        cap = take_int_flag(args, "--max-lines") or DEFAULT_MAX_LINES
        byte_cap = take_int_flag(args, "--max-bytes") or cap * BYTES_PER_LINE
    except Malformed as e:
        err(f"ERROR  {e}")
        return 2
    if not args:
        err(__doc__)
        return 2

    breaches = 0
    for a in args:
        p = Path(a)
        try:
            if not p.is_file():
                raise Malformed(f"{a}: manifest not found")
            found = judge(p, cap, byte_cap)
        except Malformed as e:
            err(f"ERROR  {e}")
            return 2
        except (OSError, ValueError) as e:
            # ValueError alongside OSError, and for the same reason the UnicodeDecodeError
            # branch exists: an unusable path or an unreadable file is not a verdict.
            err(f"ERROR  {a}: {e}")
            return 2
        if found:
            breaches += len(found)
            for f in found:
                print(f"BREACH {a}: {f}")
        else:
            print(f"ok     {a}: surface complete for its tier")
    print(f"{len(args)} manifest(s), {breaches} breach(es), budget {cap} lines / {byte_cap} bytes")
    return 1 if breaches else 0


if __name__ == "__main__":
    # THE SEAL. Nothing may leave this script wearing an exit code it did not earn.
    # CPython flushes std streams again at interpreter shutdown, and if THAT flush
    # raises - a pipe whose reader is gone - the interpreter REPLACES our status with
    # 120. An earlier build sealed fd 1 only, so 'surface-check.py --nope' with a dead
    # stderr pipe exited 120: a usage error wearing a code the table never names.
    # Both streams are therefore flushed here, while an exception can still be caught,
    # and each fd is redirected to /dev/null on failure so the shutdown flush cannot
    # fail a second time.
    try:
        rc = main(sys.argv[1:])
        if sys.stdout is not None:  # None when fd 1 was closed; main() already returned 2
            sys.stdout.flush()  # inside the try, so a broken pipe still gets its ERROR line
    except SystemExit as e:
        # No argparse here today, but a usage-exit added later must not vault the seal.
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except (OSError, ValueError) as e:
        # A broken pipe or a full disk mid-report would otherwise leave the interpreter
        # to pick the exit code (1 on an uncaught exception, 120 on a failed flush).
        # Both are lies about a verdict nobody received: report on stderr, exit 2.
        err(f"ERROR  cannot deliver verdict: {e}")
        rc = 2
    except BaseException as e:  # noqa: BLE001 - no unexpected error may wear a verdict's code
        try:
            print(f"internal error - {type(e).__name__}: {e}", file=sys.stderr)
        except BaseException:
            pass
        rc = 2
    for stream, fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if stream is not None:
                stream.flush()
        except BaseException:
            if rc in (0, 1):  # output that never landed is not a verdict
                rc = 2
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), fd)
            except BaseException:
                pass
    sys.exit(rc)
