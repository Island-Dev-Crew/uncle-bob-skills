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

Rendered CommonMark is the boundary. A pinned `markdown-it-py` parser resolves inline and
full/collapsed/shortcut reference links, nested/escaped/multiline link text, code spans and raw
HTML inside link text, balanced destinations, and images. The checker walks the parser's actual
`link_open` and `image` tokens, so an inert outer bracket cannot hide the inner link that a reader
receives, and examples inside fenced code are not invented as live links. Relative `href`, `src`,
and `srcset` targets in rendered raw HTML are checked too. `srcset` candidates follow the WHATWG
tokenization boundary rather than a comma split (commas can be part of URLs); parse errors fail the
gate closed. That keeps a picture-based README hero inside the same evidence boundary as ordinary
Markdown assets.

Exit 0 when every relative link resolves AND at least one was checked; 1 when any is dead or a
`srcset` is malformed, listing each; 2 on usage or a git error; 3 when zero links were found — a checker that
checked nothing has verified nothing, and this pack does not report that as a pass.
"""
import os
import posixpath
import re
import subprocess
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

try:
    from markdown_it import MarkdownIt
except BaseException as _markdown_import_exception:
    MarkdownIt = None
    _markdown_import_error = _markdown_import_exception
else:
    _markdown_import_error = None


ASCII_WHITESPACE = "\t\n\f\r "
FLOATING_POINT = re.compile(
    r"-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z"
)


def _valid_srcset_descriptors(descriptors: list[str]) -> tuple[bool, bool]:
    """Return (candidate-valid, parse-error) for WHATWG srcset descriptors."""
    width = False
    density = False
    future_h = False
    error = False
    parse_error = False
    for descriptor in descriptors:
        number, suffix = descriptor[:-1], descriptor[-1:]  # empty stays invalid below
        if suffix == "w" and number.isascii() and number.isdigit():
            if width or density:
                error = True
            if int(number) == 0:
                error = True
            width = True
        elif suffix == "x" and FLOATING_POINT.fullmatch(number):
            if width or density or future_h:
                error = True
            if float(number) < 0:
                error = True
            density = True
        elif suffix == "h" and number.isascii() and number.isdigit():
            # WHATWG retains this future-compatible descriptor but marks it a parse error.
            parse_error = True
            if future_h or density or int(number) == 0:
                error = True
            future_h = True
        else:
            error = True
    if future_h and not width:
        error = True
    return not error, parse_error or error


def parse_srcset(value: str) -> tuple[list[str], bool]:
    """Extract candidate URLs using WHATWG's srcset splitting/tokenizer states.

    Browsers recover from malformed candidates. A release gate must not turn that
    recovery into a green proof, so the returned flag records every parse error.
    """
    candidates = []
    malformed = False
    position = 0
    length = len(value)
    while True:
        # WHATWG splitting loop: commas here are parse errors, not URL separators.
        while position < length and (
            value[position] in ASCII_WHITESPACE or value[position] == ","
        ):
            malformed = malformed or value[position] == ","
            position += 1
        if position >= length:
            return candidates, malformed

        start = position
        while position < length and value[position] not in ASCII_WHITESPACE:
            position += 1
        url = value[start:position]
        descriptors = []

        if url.endswith(","):
            stripped = url.rstrip(",")
            if len(url) - len(stripped) > 1:
                malformed = True
            url = stripped
        else:
            while position < length and value[position] in ASCII_WHITESPACE:
                position += 1
            current = ""
            state = "descriptor"
            while True:
                char = value[position] if position < length else None
                if state == "descriptor":
                    if char is None:
                        if current:
                            descriptors.append(current)
                        break
                    if char in ASCII_WHITESPACE:
                        if current:
                            descriptors.append(current)
                            current = ""
                        state = "after"
                        position += 1
                    elif char == ",":
                        position += 1
                        if current:
                            descriptors.append(current)
                        break
                    elif char == "(":
                        current += char
                        state = "parens"
                        position += 1
                    else:
                        current += char
                        position += 1
                elif state == "parens":
                    if char is None:
                        descriptors.append(current)
                        break
                    current += char
                    position += 1
                    if char == ")":
                        state = "descriptor"
                else:  # after descriptor
                    if char is None:
                        break
                    if char in ASCII_WHITESPACE:
                        position += 1
                    else:
                        state = "descriptor"

        valid, descriptor_error = _valid_srcset_descriptors(descriptors)
        malformed = malformed or descriptor_error or not url
        if valid and url:
            candidates.append(url)


class HtmlTargets(HTMLParser):
    """Collect navigation and asset targets from rendered raw HTML fragments."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets = []

    def handle_starttag(self, _tag, attrs):
        for name, value in attrs:
            if value is None:
                continue
            if name == "href":
                self.targets.append(("link", value))
            elif name == "src":
                self.targets.append(("image", value))
            elif name == "srcset":
                candidates, malformed = parse_srcset(value)
                self.targets.extend(("image", candidate) for candidate in candidates)
                if malformed:
                    self.targets.append(("malformed-srcset", value))

    handle_startendtag = handle_starttag


def html_targets(fragment: str):
    parser = HtmlTargets()
    parser.feed(fragment)
    parser.close()
    yield from parser.targets


def rendered_targets(body: str):
    """Yield (`link`|`image`, destination) from CommonMark's rendered token tree."""
    parser = MarkdownIt("commonmark")
    for block in parser.parse(body):
        if block.type == "html_block":
            yield from html_targets(block.content)
        for token in block.children or ():
            if token.type == "link_open":
                target = token.attrGet("href")
                if target is not None:
                    yield "link", target
            elif token.type == "image":
                target = token.attrGet("src")
                if target is not None:
                    yield "image", target
            elif token.type == "html_inline":
                yield from html_targets(token.content)


def git(args, rev_ok=False):
    r = subprocess.run(["git"] + args, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", errors="replace").strip())
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    if MarkdownIt is None:
        if isinstance(_markdown_import_error, ModuleNotFoundError) and getattr(
            _markdown_import_error, "name", None
        ) == "markdown_it":
            detail = "missing markdown-it-py"
        else:
            detail = (
                "could not initialize markdown-it-py: "
                f"{type(_markdown_import_error).__name__}: {_markdown_import_error}"
            )
        print(
            f"link-check: {detail}; install the pinned gate dependencies "
            "with `python3 -m pip install -r requirements.txt`",
            file=sys.stderr,
        )
        return 2
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
    counts = {"link": 0, "image": 0}
    dead = []
    malformed = []
    for f in sorted(t for t in tracked if t.endswith(".md")):
        body = git(["show", f"{rev}:{f}"])
        for form, target in rendered_targets(body):
            if form == "malformed-srcset":
                malformed.append((f, target))
                continue
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or target.startswith("#"):
                continue
            path = unquote(parsed.path)
            if not path:
                continue
            counts[form] += 1
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(f), path))
            if resolved in tracked:
                continue
            if any(t.startswith(resolved.rstrip("/") + "/") for t in tracked):
                continue                       # a directory link
            dead.append((f, target))
    checked = counts["link"] + counts["image"]
    for f, target in dead:
        print(f"DEAD {f} -> {target}")
    for f, target in malformed:
        print(f"MALFORMED {f} -> srcset: {target}")
    print(f"\n{checked} relative targets checked at {rev} "
          f"({counts['link']} links, {counts['image']} images), {len(dead)} dead, "
          f"{len(malformed)} malformed srcset")
    if dead or malformed:
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
