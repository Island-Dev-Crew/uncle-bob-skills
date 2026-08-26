#!/usr/bin/env python3
"""link-check.py — every relative markdown link in the COMMITTED tree must resolve.

Usage: python3 scripts/link-check.py [rev]        (default: HEAD)

The pack published "765 committed relative links, 0 dead" with no instrument behind it — a
number a reader could not re-derive from any command in the repository, in a pack whose first
law is that no claim outranks its evidence. This is that instrument.

It reads the COMMITTED tree (`git ls-tree`, `git show`), never the worktree, because the
worktree is where this pack's own history hides things: two dead links shipped in v1.0 because
the check ran against a working copy whose files never got committed, and an untracked
transcript later made a whole proof block green only on the author's machine.

A link is checked when it is relative; http(s)/mailto and pure #fragments are not this tool's
concern. A target resolves when it is a tracked file, or a tracked directory (a prefix of some
tracked path). Fragments are stripped — anchor validity is a different check with different
rules (GitHub's slugger), and claiming it here would overstate.

BOTH markdown link forms are resolved, and the summary line breaks the count down by form so
the number says what it covers. Until v2.0.1 only the inline `[text](target)` form was matched,
so a whole class — `[text][label]`, `[text][]`, `[label]`, each resolved through a
`[label]: target` definition — was never checked while the tool's own docstring presented it as
the instrument behind the pack's "N links, 0 dead". Reference usage is matched CommonMark's way:
a `[label]` only counts when a definition for it exists, which is also what keeps prose brackets
and `- [ ]` checkboxes out of the count.

Two limits, stated rather than papered over. Definitions are read in their common one-line form
(`[label]: dest "title"`, dest optionally in <angle brackets>); a destination carried on the line
BELOW its label is not parsed, and its usages are then treated as undefined text, not as dead.
Definitions are read only OUTSIDE fenced code blocks, because a definition inside a fence is an
example of the syntax rather than a link the rendered page has — counting one made this tool
report a dead link on a page that contains none. Reference USAGES and inline links are still
matched everywhere, including inside fences, which can inflate the checked count but cannot hide
a dead target: a usage whose label has no definition outside a fence is simply not a link.

Exit 0 when every relative link resolves AND at least one was checked; 1 when any is dead,
listing each; 2 on usage or a git error; 3 when zero links were found — a checker that
checked nothing has verified nothing, and this pack does not report that as a pass.
"""
import os
import posixpath
import re
import subprocess
import sys

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# `[label]: dest` at the head of a line, up to CommonMark's three-space indent.
REF_DEF = re.compile(r"(?m)^ {0,3}\[([^\]\n]+)\]:[ \t]*(<[^>\n]*>|\S+)")
FENCE = re.compile(r"(?m)^ {0,3}(`{3,}|~{3,})[^\n]*$")


def outside_fences(body):
    """`body` with fenced code blocks blanked out, line count preserved.

    Only DEFINITIONS are read through this. A reference definition inside a ``` block is an
    example of the syntax, not a definition the rendered page honours — CommonMark does not read
    it, and neither may this tool. Reading them made a page whose only reference syntax sat inside
    one fenced example report a DEAD link that does not exist on it, which is a gate manufacturing
    evidence. The nearest live example was this repository's own CHANGELOG: an entry documenting
    reference-link support, quoting the syntax in a fence, turned the release gate red.

    Lines are blanked rather than removed so the reported line numbers keep matching the file.
    """
    out = []
    fence = None
    for line in body.split("\n"):
        m = FENCE.match(line)
        if fence is None and m:
            fence = m.group(1)[0]
            out.append("")
            continue
        if fence is not None:
            out.append("")
            if m and m.group(1)[0] == fence:
                fence = None
            continue
        out.append(line)
    return "\n".join(out)
# Full `[text][label]` and collapsed `[text][]` — one pattern, blank label means collapsed.
REF_USE = re.compile(r"\[([^\]\n]*)\]\[([^\]\n]*)\]")
# Shortcut `[label]`. The lookahead is what separates it from an inline link, a full
# reference, and a definition line; overlap with the two patterns above is filtered by span.
REF_SHORT = re.compile(r"\[([^\]\n]+)\](?![\[\(:])")


def norm_label(label: str) -> str:
    """CommonMark link-label matching: case-folded, with internal whitespace collapsed."""
    return " ".join(label.split()).casefold()


def reference_targets(body):
    """Yield (label, target) once per reference-style USAGE in `body`.

    Per usage, not per definition: a definition nobody links through is not a link, and
    counting it would put a number in the summary that no reader could point at on a page.
    """
    defs = {}
    for label, dest in REF_DEF.findall(outside_fences(body)):
        defs.setdefault(norm_label(label), dest.strip("<>"))
    if not defs:
        return
    taken = [m.span() for m in LINK.finditer(body)]
    for m in REF_USE.finditer(body):
        taken.append(m.span())
        label = norm_label(m.group(2) or m.group(1))
        if label in defs:
            yield label, defs[label]
    for m in REF_SHORT.finditer(body):
        if any(start <= m.start() < end for start, end in taken):
            continue
        label = norm_label(m.group(1))
        if label in defs:
            yield label, defs[label]


def git(args, rev_ok=False):
    r = subprocess.run(["git"] + args, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", errors="replace").strip())
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        print(__doc__, file=sys.stderr)
        return 2
    rev = argv[0] if argv else "HEAD"
    try:
        tracked = set(t for t in git(["ls-tree", "-r", "--name-only", rev]).split("\n") if t)
    except RuntimeError as exc:
        print(f"link-check: {exc}", file=sys.stderr)
        return 2
    counts = {"inline": 0, "reference": 0}
    dead = []
    for f in sorted(t for t in tracked if t.endswith(".md")):
        body = git(["show", f"{rev}:{f}"])
        links = [("inline", None, t) for t in LINK.findall(body)]
        links += [("reference", label, t) for label, t in reference_targets(body)]
        for form, label, target in links:
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#")[0].split("?")[0]
            if not path:
                continue
            counts[form] += 1
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(f), path))
            if resolved in tracked:
                continue
            if any(t.startswith(resolved.rstrip("/") + "/") for t in tracked):
                continue                       # a directory link
            dead.append((f, target if label is None else f"{target} (reference [{label}])"))
    checked = counts["inline"] + counts["reference"]
    for f, target in dead:
        print(f"DEAD {f} -> {target}")
    print(f"\n{checked} relative links checked at {rev} "
          f"({counts['inline']} inline, {counts['reference']} reference-style), {len(dead)} dead")
    if dead:
        return 1
    if checked == 0:
        print("NOTHING CHECKED - no relative links found; this is not a pass", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    try:
        _code = main()
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
