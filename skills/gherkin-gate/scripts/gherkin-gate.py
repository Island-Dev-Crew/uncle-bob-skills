#!/usr/bin/env python3
"""gherkin-gate.py - bind a story's Gherkin scenarios to red-before-green evidence.

Usage:
  gherkin-gate.py STORY-ID FEATURE-FILE LEDGER-TSV

Ledger records are tab-separated, five fields, in run order:
  phase<TAB>exit_code<TAB>story<TAB>feature_sha256<TAB>scenario
A line is a RECORD if it splits into 5 tab-separated fields whose first field is
'red' or 'green'; record-shape is tested BEFORE the comment rule, so a data row
can never vanish into the '#' skip. Anything else whose first non-space
character is '#', and any blank line, is a comment.

feature_sha256 is the sha256 of the feature file's RAW BYTES; produce it with
  shasum -a 256 FEATURE      (BSD/macOS)
  sha256sum FEATURE          (GNU)

Exit codes (distinct meanings, never shared):
  0  gate consents  - every scenario in the feature is bound to this story and
                      ran red first, green last, against the feature's current sha256
  1  gate refuses   - a real verdict: no red, red after green, still red, stale
                      sha, absent/conflicting/mismatched story binding, orphan or
                      missing record, scenario head prefixed with a trimmable
                      character other than ' ' or '\t', feature declaring a
                      non-English dialect
  2  usage or input error - unreadable or non-UTF-8 file, malformed ledger line,
                      no scenarios, no records, unwritable stdout, or ANY
                      unexpected exception. Fail-closed: never a pass, and never
                      the refusal code, so a wrapper branching on `1 = refuse`
                      can never read an IO fault as a story that failed.
These three are the only statuses this script's own paths produce. CPython
flushes BOTH std streams at interpreter shutdown and overrides the process
status with 120 if either flush raises, so the tail below flushes each stream
itself and points the failing fd at the null device before exiting - a dead
stdout pipe AND a dead stderr pipe both land on 2. A fault before main() is
entered (a failed interpreter start) is Python's own and still exits 1.
"""
import hashlib
import os
import re
import sys
import unicodedata
from pathlib import Path

# Anchored, whole-line patterns only: an unanchored match would let a scenario
# name hide inside a step line, or a story header inside prose. All four Gherkin
# spellings of an ENGLISH scenario head are recognised - 'Example:' is the
# language's own synonym for 'Scenario:', so matching only the latter would
# render a real scenario invisible and let it ship with no evidence demanded.
# Longest alternative first; 'Examples:' (the Outline data table) cannot match
# because the colon must follow immediately. The name is captured as (.*) - an
# empty name is a scenario the ledger cannot bind to, refused below, not ignored.
#
# Gherkin is i18n by design: '# language: de' swaps these keywords wholesale
# ('Szenario:', 'Beispiel:', accented 'Scenario:'), and a localized head this
# class cannot see is a scenario a real runner executes with no evidence
# demanded - consent, the worst failure direction. The gate does not carry the
# dialect table; it REFUSES any feature declaring a dialect other than 'en'
# (DIALECT_RE below), so its accepted input space is exactly the one where these
# four spellings are the complete set of scenario keywords.
#
# The head prefix is matched with TRIMMABLE, deliberately WIDER than Python's
# whitespace class. Deriving detection from `\s` alone was the round-2 hole: a
# head prefixed by a character Python does not call whitespace but a real runner
# trims matched NEITHER regex below, so no disagreement fired and the head was
# dropped instead of refused - consent, the worst direction. The class covers
# every character a shipping Gherkin runner strips off a head:
#   - Unicode horizontal whitespace (U+00A0/U+2007/U+3000 - what a paste out of
#     Jira, Confluence or Docs carries, and what a sibling seat's model emits);
#   - C0 controls and DEL, because Java's String.trim() strips every codepoint
#     <= U+0020 and gherkin-java matches keywords against lineText.trim();
#   - the zero-width/BOM family plus U+180E, because U+FEFF is in ECMAScript's
#     WhiteSpace production (so gherkin-javascript's GherkinLine trims it and
#     cucumber-js executes the scenario) and U+180E was Zs before Unicode 6.3,
#     so an older engine trims that too.
# Line terminators are absent by construction - splitlines() has already removed
# every character Python breaks lines on, U+2028/U+2029 included.
# The class is ENUMERATED from the two trim rules named above - ECMAScript's
# WhiteSpace production and Java's String.trim() - not derived from a
# specification and not surveyed across every runner. That is its disclosed
# edge: a head prefixed by something outside it (U+202A and the bidi controls,
# say) is dropped silently rather than refused. Neither of those two rules trims
# a bidi control, so neither of those runners executes such a head; what happens
# under a runner this island did not read is NOT established here, and
# scripts/fixtures/limit-bidi-head.feature captures the drop as a run.
HSPACE = r"[^\S\r\n]"
TRIMMABLE = r"(?:[^\S\r\n]|[\x00-\x08\x0e-\x1f\x7f]|[\u180e\u200b-\u200f\u2060-\u2064\ufeff])"
SCENARIO_KEYWORDS = r"(?:Scenario Outline|Scenario Template|Scenario|Example):"
SCENARIO_RE = re.compile(rf"^({TRIMMABLE}*){SCENARIO_KEYWORDS}(.*)$")
# The ASCII-only twin exists to detect disagreement, never to decide: a head the
# wide class sees and this one does not is ambiguous across parsers, and is
# refused (exit 1, a verdict) rather than silently normalised.
SCENARIO_ASCII_RE = re.compile(rf"^[ \t]*{SCENARIO_KEYWORDS}")
STORY_RE = re.compile(rf"^{TRIMMABLE}*#{TRIMMABLE}*STORY:{TRIMMABLE}*(\S+){TRIMMABLE}*$")
# Deliberately wider than Gherkin's own `([a-zA-Z\-_]+)`, and built on TRIMMABLE
# for the same reason the head is: every extra thing this matches is one more
# file refused rather than silently gated in a dialect whose keywords this script
# does not know. cucumber-js honours a `# language:` line prefixed with U+FEFF.
DIALECT_RE = re.compile(
    rf"^{TRIMMABLE}*#{TRIMMABLE}*language{TRIMMABLE}*:{TRIMMABLE}*(\S+){TRIMMABLE}*$", re.I)
# Two comment rules, on purpose. HEADER_COMMENT_RE keeps the dialect window open
# across a prefixed comment line - narrower here would end the header scan and
# hide the very directive that must refuse. COMMENT_RE stays narrow for the
# LEDGER, where widening what counts as a comment would widen what is skipped.
HEADER_COMMENT_RE = re.compile(rf"^{TRIMMABLE}*#")
# "Blank" for the header scan means blank to a runner that trims: a line holding
# only trimmable characters must not end the window either, or a lone \x01 on
# line 1 would close it before the '# language:' line 2 that Java's trim() honours.
HEADER_BLANK_RE = re.compile(rf"^{TRIMMABLE}*$")
COMMENT_RE = re.compile(rf"^{HSPACE}*#")
PHASES = ("red", "green")

EXIT_OK, EXIT_REFUSE, EXIT_INPUT = 0, 1, 2


def key(text: str) -> str:
    """The ONE join key, applied identically to both sides of every comparison.

    str.strip() so a character can never be whitespace to one half of the gate
    and content to the other, then NFC so a macOS-decomposed record ("e"+U+0301)
    joins the composed head (U+00E9) it names instead of being reported as an
    orphan record for a scenario spelled identically on screen. Case is NOT
    folded: two scenarios differing only in case are two scenarios.
    """
    return unicodedata.normalize("NFC", text.strip())


def unwritable(exc: OSError) -> int:
    """Report an unwritable stdout as EXIT_INPUT, and make that status survive.

    Returning is not enough. The verdict lines are still in sys.stdout's buffer;
    CPython flushes it again at interpreter shutdown, the same BrokenPipeError
    fires there, and the interpreter overrides the process status with 120 - a
    fourth exit code this gate does not define and a CI wrapper branching 0/1/2
    reads as its undefined else. `gate ... | head -1` is the ordinary way to
    reach it. Pointing fd 1 at the null device lets that shutdown flush succeed,
    so the chosen 2 is what the process actually exits. If even that fails,
    leave through os._exit, which skips the shutdown flush entirely.
    """
    try:  # stderr may be dead too; losing the diagnostic must not lose the status
        print(f"input-error: cannot write verdict: {exc}", file=sys.stderr)
    except OSError:
        pass
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)
    except OSError:
        try:
            sys.stderr.flush()
        finally:
            os._exit(EXIT_INPUT)
    return EXIT_INPUT


def die(msg: str) -> None:
    print(f"input-error: {msg}", file=sys.stderr)
    raise SystemExit(EXIT_INPUT)


def read_feature(path: str):
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        die(f"cannot read feature file {path}: {exc}")
    # The content binding hashes the file's RAW BYTES, so `shasum -a 256 FEATURE`
    # (or `sha256sum`) reproduces the ledger field exactly. Hashing decoded text
    # instead would apply universal-newline translation and silently forgive a
    # CRLF checkout - "exact bytes" would then be a claim the check does not make.
    digest = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        # A UTF-16 or latin-1 save is a routine editor artifact, not a verdict:
        # an undecodable file must reach die() and exit 2, never crash into the
        # refusal code and be read by a wrapper as "the story failed".
        die(f"cannot read feature file {path}: {exc}")
    # A leading BOM is the same class of editor artifact. It is no longer
    # load-bearing - U+FEFF is inside TRIMMABLE, so every pattern above sees
    # through one on any line, not just character 0 - but the strip stays because
    # it also keeps the BOM out of a first-line scenario NAME. Parsing only: the
    # digest above still covers every byte, BOM included.
    if text.startswith("\ufeff"):
        text = text[1:]
    scenarios, declared, refusals, in_header = [], [], [], True
    for num, line in enumerate(text.splitlines(), 1):
        if in_header:
            if not HEADER_BLANK_RE.match(line) and not HEADER_COMMENT_RE.match(line):
                in_header = False  # the dialect directive only precedes content
            else:
                hit = DIALECT_RE.match(line)
                if hit and key(hit.group(1)).casefold() != "en":
                    refusals.append(
                        f"{path}:{num}: '# language: {hit.group(1)}' declares a non-English "
                        f"Gherkin dialect - this gate recognises only the four English "
                        f"scenario keywords, so a localized head would be invisible to it "
                        f"and demand no evidence; normalise the file to 'en' before gating"
                    )
        hit = SCENARIO_RE.match(line)
        if hit:
            indent, name = hit.group(1), key(hit.group(2))
            scenarios.append((num, name))
            if not SCENARIO_ASCII_RE.match(line):
                odd = next((ch for ch in indent if ch not in " \t"), "?")
                refusals.append(
                    # NOT "non-ASCII": the class holds the C0 controls, and DEL,
                    # which are ASCII. The property that matters is the one the
                    # ASCII twin actually tested - neither ' ' nor '\t'.
                    f"{path}:{num}: scenario head prefixed with a trimmable "
                    f"character (U+{ord(odd):04X}) that is neither ' ' nor '\\t' - "
                    f"normalise it; a parser that splits on [ \\t] cannot see this "
                    f"scenario at all"
                )
            continue
        hit = STORY_RE.match(line)
        if hit:
            declared.append((num, key(hit.group(1))))
    if not scenarios:
        die(f"{path} declares no Scenario: - an empty acceptance file cannot pass")
    return digest, scenarios, declared, refusals


def read_ledger(path: str):
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        die(f"cannot read ledger {path}: {exc}")
    records = []
    for num, line in enumerate(raw.splitlines(), 1):
        fields = line.split("\t")
        # Record-shape FIRST, comment rule second. A '#'-leading skip applied to
        # a field whose value could start with '#' silently deletes evidence, and
        # a dropped record is a false green; testing record-shape first makes
        # that impossible rather than merely unlikely.
        looks_like_record = len(fields) == 5 and fields[0].strip() in PHASES
        if not looks_like_record and (not line.strip() or COMMENT_RE.match(line)):
            continue
        if len(fields) != 5:
            die(f"{path}:{num}: expected 5 tab-separated fields, got {len(fields)}")
        phase, code, story, sha, scenario = (f.strip() for f in fields)
        if phase not in PHASES:
            die(f"{path}:{num}: phase must be red or green, got {phase!r}")
        try:
            code_int = int(code)
        except ValueError:  # non-numeric, or past CPython's int-conversion digit cap
            die(f"{path}:{num}: exit_code must be an integer, got {code[:40]!r}")
        records.append({"line": num, "phase": phase, "code": code_int,
                        "story": key(story), "sha": sha.lower(), "scenario": key(scenario)})
    if not records:
        die(f"{path} holds no records - an empty ledger is not evidence")
    return records


def main(argv) -> int:
    if sys.stdout is None:  # an unwritable verdict is an IO error, not a pass
        print("input-error: stdout is closed - the gate cannot write its verdict", file=sys.stderr)
        return EXIT_INPUT
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return EXIT_INPUT
    story_id, feature_path, ledger_path = key(argv[1]), argv[2], argv[3]
    digest, scenarios, declared, refusals = read_feature(feature_path)
    records = read_ledger(ledger_path)

    if not declared:
        refusals.append(f"{feature_path} carries no '# STORY: id' header - unbound acceptance file")
    elif len({sid for _, sid in declared}) > 1:
        where = ", ".join(f"line {n}: {sid!r}" for n, sid in declared)
        refusals.append(f"{feature_path} declares conflicting stories ({where}) - ambiguous binding")
    elif declared[0][1] != story_id:  # exact equality on the key: never substring or regex
        refusals.append(f"{feature_path} declares story {declared[0][1]!r}, gate invoked for {story_id!r}")

    seen = set()
    for num, name in scenarios:
        if not name:
            refusals.append(f"{feature_path}:{num}: scenario head with no name - nothing for a record to bind to")
            continue  # never enters `seen`: a record naming '' is an orphan, not evidence
        if name in seen:
            refusals.append(f"{feature_path}:{num}: duplicate Scenario name {name!r} - evidence cannot bind unambiguously")
        seen.add(name)

    mine = [r for r in records if r["story"] == story_id]  # exact equality again
    if not mine:
        refusals.append(f"no ledger record binds story {story_id!r} - no evidence at all")

    runs = {}
    for rec in mine:
        where = f"{ledger_path}:{rec['line']}"
        if rec["scenario"] not in seen:
            refusals.append(f"{where}: orphan record for unknown scenario {rec['scenario']!r}")
        elif rec["sha"] != digest:
            # Full 64 hex both sides, never a prefix: the verdict compares the
            # whole digest, so a pair differing only past character 12 would
            # otherwise print two identical values while refusing them as
            # different - a diagnostic that contradicts its own verdict.
            refusals.append(f"{where}: stale evidence - sha {rec['sha']} vs feature {digest}")
        elif rec["phase"] == "red" and rec["code"] == 0:
            refusals.append(f"{where}: red record exited 0 - it never went red")
        elif rec["phase"] == "green" and rec["code"] != 0:
            refusals.append(f"{where}: green record exited {rec['code']} - not green")
        else:
            runs.setdefault(rec["scenario"], []).append(rec)

    lines = []
    for _, name in scenarios:
        if not name:
            continue  # already refused as unnamed; no ledger key can bind to it
        seq = runs.get(name, [])
        if not seq:
            refusals.append(f"scenario {name!r}: no valid red/green evidence")
        elif seq[0]["phase"] != "red":
            refusals.append(f"scenario {name!r}: first run is green (line {seq[0]['line']}) - never proved red")
        elif seq[-1]["phase"] != "green":
            refusals.append(f"scenario {name!r}: last run is red (line {seq[-1]['line']}) - not green yet")
        else:
            lines.append(f"RED->GREEN  red L{seq[0]['line']} -> green L{seq[-1]['line']}  {name}")

    lines += [f"REFUSED  {msg}" for msg in refusals]
    # A 12-char digest HERE is a label on one value, not a comparison of two;
    # the stale-evidence refusal above prints both digests in full.
    lines.append(f"{len(scenarios)} scenarios, {len(refusals)} refusals, story {story_id}, sha {digest[:12]}")
    try:
        # Every write and the flush share one guard. EPIPE can surface at either
        # - print() raises only when the buffer happens to spill - so catching
        # just the flush left the mid-write case falling through to the
        # catch-all with a half-flushed buffer.
        for line in lines:
            print(line)
        sys.stdout.flush()  # a verdict nobody could read is an IO error, not a verdict
    except OSError as exc:
        return unwritable(exc)
    return EXIT_REFUSE if refusals else EXIT_OK


if __name__ == "__main__":
    try:
        rc = main(sys.argv)
    except SystemExit as exc:  # die() already chose EXIT_INPUT
        rc = exc.code if isinstance(exc.code, int) else EXIT_INPUT
    except BaseException as exc:  # noqa: BLE001 - deliberate catch-all
        # Python exits 1 on an unhandled exception, and 1 is this gate's REFUSAL
        # code. Left uncaught, a crash would be recorded by CI as a story that
        # failed its acceptance bar. Every error path exits its own code. The
        # report itself is guarded: a dead stderr here would otherwise escape the
        # handler as a SECOND exception and take the status with it.
        try:
            print(f"input-error: {type(exc).__name__}: {exc}", file=sys.stderr)
        except BaseException:  # noqa: BLE001
            pass
        rc = EXIT_INPUT
    # Flush both streams HERE, while a status can still be chosen. CPython
    # re-flushes stdout and stderr at shutdown and replaces the process status
    # with 120 if EITHER raises - that is how `gate ... | head -1` used to exit
    # 120, and how a usage error written to a hung-up stderr still did after fd 1
    # alone was covered. Pointing the failing fd at the null device lets the
    # shutdown flush succeed, so the status chosen above is the one that leaves.
    for stream, fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if stream is not None:
                stream.flush()
        except BaseException:  # noqa: BLE001 - closed, detached or hung up
            if rc in (EXIT_OK, EXIT_REFUSE):
                rc = EXIT_INPUT  # a verdict that never landed is not a verdict
            try:
                devnull = os.open(os.devnull, os.O_WRONLY)
                os.dup2(devnull, fd)
                os.close(devnull)
            except OSError:
                os._exit(rc)  # last resort: skip the shutdown flush entirely
    sys.exit(rc)
