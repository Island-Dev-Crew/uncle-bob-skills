#!/usr/bin/env python3
"""pilot-gate.py - refuse a parallel fan-out until one pilot slice is evidenced.

Usage
    python3 pilot-gate.py PILOT_RECORD

Consents only when every declared pipeline stage carries exactly one walked entry
whose recorded exit code is 0 and whose artifact is an existing, non-empty regular
file that no other stage cites.

Record grammar - UTF-8 (a leading BOM is stripped), one record per line, CRLF or
LF, no comment syntax by design, leading/trailing whitespace on a line ignored,
blank lines skipped:

    slice=NAME                      exactly once, non-empty
    stage=NAME                      at least MIN_STAGES of them, each distinct
    walked=STAGE|EXITCODE|ARTIFACT  at most one per stage

Any other line is malformed. Stage names join through norm() - NFC, stripped,
casefolded. A variant inside that fold (letter case, NFD against NFC, an
indented line) joins; a variant outside it (a compatibility spelling, an
embedded zero-width or soft hyphen) misses its join and lands in the strict
branch, refused twice over - as an unwalked stage and as evidence for an
undeclared one. Two declared stages colliding under the key are malformed,
never silently merged. Artifact paths resolve against the record's own
directory unless absolute, and artifact identity is the (device, inode) pair,
so two spellings of one file are still one file.

Exit codes
    0  CONSENT - every declared stage walked at exit 0 with its own non-empty
       artifact. `--help` also prints usage and exits 0.
    1  REFUSE - fewer than MIN_STAGES stages, a declared stage never walked,
       evidence for an undeclared stage, a recorded non-zero exit, or an
       artifact that is missing, empty, not a regular file, or shared.
    2  ERROR - usage, unreadable or undecodable record, malformed record, an
       artifact that cannot be stat'ed for any reason other than absence, a dead
       stdout (closed outright, so print() would discard the verdict, or broken
       so the flush raises), or an internal failure. An error is never a verdict.

What this gate cannot see: it reads the record and stats the artifacts. It never
re-runs the pilot and never reads artifact content, so (a) a complete record over
fabricated files consents - see scripts/fixtures/fabricated/ - and (b) because
identity is (device, inode), two byte-identical copies of one log are two files
and the shared-artifact check is defeated by cp - see scripts/fixtures/copied/.
Both holes are shipped as consenting fixtures rather than hidden.
"""
import argparse
import os
import re
import stat
import sys
import unicodedata

KEYS = ("slice", "stage", "walked")
# A stage name is one line, no field separator, bounded length.
STAGE_RE = re.compile(r"\A[^|\r\n\x00]{1,64}\Z")
# A bounded integer literal: no unbounded int() conversion, no NaN, no inf.
EXIT_RE = re.compile(r"\A-?[0-9]{1,5}\Z")
MIN_STAGES = 2


class Malformed(Exception):
    """The record is not a record. Exit 2, never a verdict."""


def norm(name):
    """The one documented key function for stage names."""
    return unicodedata.normalize("NFC", name).strip().casefold()


def read_record(path):
    """Return the decoded text of the record, BOM stripped."""
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8")


def parse(text):
    """Return (slice_name, stage_order, stages, walked). Raise Malformed."""
    slice_name = None
    stage_order = []          # normalized keys, declaration order
    stages = {}               # key -> as written
    walked = {}               # key -> (as written, exit code, artifact, line no)
    for lineno, physical in enumerate(text.split("\n"), start=1):
        line = physical.rstrip("\r").strip()
        if not line:
            continue
        if "\r" in line or "\x00" in line:
            raise Malformed(f"line {lineno}: embedded control character")
        key, sep, value = line.partition("=")
        if not sep or key not in KEYS:
            raise Malformed(
                f"line {lineno}: not a record (expected slice=, stage= or walked=)"
            )
        if key == "slice":
            if slice_name is not None:
                raise Malformed(f"line {lineno}: slice declared twice")
            if not value.strip():
                raise Malformed(f"line {lineno}: slice name is empty")
            slice_name = value.strip()
        elif key == "stage":
            if not STAGE_RE.match(value):
                raise Malformed(f"line {lineno}: bad stage name")
            skey = norm(value)
            if not skey:
                raise Malformed(f"line {lineno}: stage name is empty")
            if skey in stages:
                raise Malformed(
                    f"line {lineno}: stage '{value}' collides with an earlier "
                    f"declaration of '{stages[skey]}'"
                )
            stages[skey] = value
            stage_order.append(skey)
        else:
            parts = value.split("|", 2)
            if len(parts) != 3:
                raise Malformed(
                    f"line {lineno}: walked needs STAGE|EXITCODE|ARTIFACT"
                )
            wname, wexit, wart = parts
            if not STAGE_RE.match(wname) or not norm(wname):
                raise Malformed(f"line {lineno}: bad stage name in walked")
            if not EXIT_RE.match(wexit.strip()):
                raise Malformed(
                    f"line {lineno}: exit code '{wexit}' is not a bounded integer"
                )
            if not wart.strip():
                raise Malformed(f"line {lineno}: artifact path is empty")
            wkey = norm(wname)
            if wkey in walked:
                raise Malformed(
                    f"line {lineno}: stage '{wname}' walked twice - ambiguous evidence"
                )
            walked[wkey] = (wname, int(wexit.strip()), wart.strip(), lineno)
    if slice_name is None:
        raise Malformed("no slice= record")
    return slice_name, stage_order, stages, walked


def inspect_artifact(base, artifact):
    """Return (identity, problem). identity is (dev, ino) or None."""
    path = artifact if os.path.isabs(artifact) else os.path.join(base, artifact)
    try:
        info = os.stat(path)
    except (FileNotFoundError, NotADirectoryError):
        return None, f"artifact '{artifact}' does not exist"
    except OSError as exc:                     # unreadable: an error, not a verdict
        raise Malformed(f"cannot stat artifact '{artifact}': {exc}") from exc
    if not stat.S_ISREG(info.st_mode):
        return None, f"artifact '{artifact}' is not a regular file"
    if info.st_size == 0:
        return None, f"artifact '{artifact}' is empty - an empty file is not evidence"
    return (info.st_dev, info.st_ino), None


def judge(record_path, stage_order, stages, walked):
    """Return the list of refusal reasons, in a stable order."""
    base = os.path.dirname(os.path.abspath(record_path))
    problems = []
    if len(stage_order) < MIN_STAGES:
        problems.append(
            f"pipeline declares {len(stage_order)} stage(s); "
            f"fewer than {MIN_STAGES} is not an end-to-end slice"
        )
    seen = {}
    for skey in stage_order:
        written = stages[skey]
        if skey not in walked:
            problems.append(f"stage '{written}' declared but never walked")
            continue
        _, code, artifact, _ = walked[skey]
        if code != 0:
            problems.append(f"stage '{written}' recorded exit {code} - the slice did not walk")
        identity, problem = inspect_artifact(base, artifact)
        if problem:
            problems.append(f"stage '{written}': {problem}")
            continue
        if identity in seen:
            problems.append(
                f"stage '{written}' cites the same file as stage '{seen[identity]}' - "
                f"one artifact cannot be evidence for two stages"
            )
            continue
        seen[identity] = written
    for wkey in sorted(walked):
        if wkey not in stages:
            problems.append(
                f"evidence for undeclared stage '{walked[wkey][0]}' "
                f"(line {walked[wkey][3]})"
            )
    return problems


def main():
    if sys.stdout is None:
        # fd 1 closed before exec: CPython leaves sys.stdout None and builtin
        # print() silently returns, so a verdict here would go nowhere at all.
        # A verdict with nowhere to print is an error, never a silent 0.
        print(
            "error: stdout is closed - a verdict with nowhere to print is not a verdict",
            file=sys.stderr,
        )
        return 2
    parser = argparse.ArgumentParser(
        prog="pilot-gate.py",
        description="Refuse a parallel fan-out until one pilot slice is evidenced.",
    )
    parser.add_argument("record", help="path to the pilot record")
    args = parser.parse_args()
    try:
        text = read_record(args.record)
        slice_name, stage_order, stages, walked = parse(text)
        problems = judge(args.record, stage_order, stages, walked)
    except Malformed as exc:
        print(f"error: {args.record}: {exc}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as exc:
        print(f"error: {args.record} is not valid UTF-8: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if problems:
        print(f"REFUSE: pilot slice '{slice_name}' is not evidenced - do not fan out")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(
        f"CONSENT: pilot slice '{slice_name}' walked {len(stage_order)} stages, "
        f"each at exit 0 with its own non-empty artifact"
    )
    print("  (the record and its artifacts were checked; the run itself was not re-executed)")
    return 0


if __name__ == "__main__":
    try:
        _code = main()
    except SystemExit as _exc:          # argparse usage errors and --help
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
    except BaseException as _exc:       # an exception is not a verdict
        try:
            print(f"error: internal failure: {type(_exc).__name__}: {_exc}", file=sys.stderr)
        except BaseException:
            pass
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
