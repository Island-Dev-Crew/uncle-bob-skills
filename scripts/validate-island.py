#!/usr/bin/env python3
"""validate-island.py — deterministic mechanical gate for Uncle Bob Pack islands.

Usage: python3 validate-island.py <island-dir> [<island-dir> ...]
Exit 0 iff every island passes every enforced check. Prints OK/FAIL per check.

Enforced checks (each can go red — a gate that cannot fail is not a gate):
  F1  SKILL.md exists
  F2  frontmatter block present (--- ... ---) and parses as YAML
  F3  frontmatter has non-empty name and description, both actual YAML strings
  F4  name == folder basename, ^[a-z0-9]+(-[a-z0-9]+)*$, <=64 chars
  F5  no '<' or '>' anywhere in the frontmatter block
  F6  description is a string of length 60..1024 chars
  F7  agents/openai.yaml exists, parses to a mapping, and interface.display_name +
      interface.short_description are both non-blank strings
  F8  body cites the concept ledger (>=1 match of C1..C28)
  F9  body states the evidence discipline: contains both 'enforced' and 'advisory'.
      A PRESENCE test, not a truth test — it cannot tell a real enforced/advisory split
      from an island that merely spells both words. Whether a label is honest is a
      judgement no substring check makes; that is what the human review and the other
      gates (which run the scripts behind the labels) are for.
  F10 body <=250 lines (one-concern proxy)
  F11 scripts/*.sh pass bash -n; scripts/*.py pass py_compile
Advisory (warn only): W1 references/*.md linking to sibling .md files (one-level rule).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

C_CITE = re.compile(r"\bC(?:[1-9]|1[0-9]|2[0-8])\b")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MD_LINK = re.compile(r"\]\((?!https?://)([^)#]+\.md)")


def is_text(v) -> bool:
    """A metadata field only counts when YAML handed back an actual non-blank string.

    YAML will just as happily hand back a list, a mapping, an int, a bool, or None for
    `name:` or `description:`, and every check below used to launder those through
    bool()/str(): a mapping description measured as 130 characters of prose, an int
    description measured as 70, and a list display_name counted as 'present'. The
    field is then not the field the check names, so the check is not the check.
    """
    return isinstance(v, str) and bool(v.strip())


def shape(v) -> str:
    """Name what a rejected field actually carried, so FAIL says why and not just that."""
    if v is None:
        return "missing"
    if isinstance(v, str):
        return "blank"
    return f"{type(v).__name__}, not a string"


def check(results, island, cid, ok, detail=""):
    results.append((island, cid, ok, detail))
    tag = "OK  " if ok else "FAIL"
    print(f"{tag} {island} {cid} {detail}")
    return ok


def validate(d: Path, results) -> None:
    island = d.name
    skill = d / "SKILL.md"
    if not check(results, island, "F1", skill.is_file(), "SKILL.md exists"):
        return
    text = skill.read_text(encoding="utf-8")

    m = re.match(r"\A---\n(.*?)\n---\n?(.*)\Z", text, re.DOTALL)
    if not check(results, island, "F2", bool(m), "frontmatter block present"):
        return
    fm_text, body = m.group(1), m.group(2)
    try:
        fm = yaml.safe_load(fm_text)
        parsed = isinstance(fm, dict)
    except yaml.YAMLError as e:
        fm, parsed = None, False
        check(results, island, "F2", False, f"frontmatter YAML error: {e}")
        return
    check(results, island, "F2", parsed, "frontmatter parses as YAML mapping")
    if not parsed:
        return

    name, desc = fm.get("name"), fm.get("description")
    name_ok, desc_ok = is_text(name), is_text(desc)
    bad = [f"{k} is {shape(v)}" for k, v, ok in (("name", name, name_ok), ("description", desc, desc_ok)) if not ok]
    check(results, island, "F3", name_ok and desc_ok,
          "; ".join(bad) if bad else "name+description non-empty strings")
    check(
        results, island, "F4",
        name_ok and name == island and bool(NAME_RE.match(name)) and len(name) <= 64,
        f"name '{name}' matches folder + regex" if name_ok else f"name is {shape(name)}",
    )
    check(results, island, "F5", "<" not in fm_text and ">" not in fm_text, "no angle brackets in frontmatter")
    check(results, island, "F6", desc_ok and 60 <= len(desc) <= 1024,
          f"description length {len(desc)} in 60..1024" if desc_ok else f"description is {shape(desc)}")

    sidecar = d / "agents" / "openai.yaml"
    side_ok, side_detail = False, "agents/openai.yaml missing"
    if sidecar.is_file():
        try:
            sc = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
            # isinstance, not `or {}`: a sidecar whose `interface:` parsed as a list used
            # to reach .get() and take the whole run down with an AttributeError, so the
            # island was never validated at all rather than reported malformed.
            iface = sc.get("interface") if isinstance(sc, dict) else None
            if not isinstance(iface, dict):
                side_detail = f"sidecar interface is {type(iface).__name__}, not a mapping" if iface is not None else "sidecar has no interface mapping"
            else:
                dn, sd = iface.get("display_name"), iface.get("short_description")
                side_ok = is_text(dn) and is_text(sd)
                side_detail = ("sidecar interface complete" if side_ok else
                               "; ".join(f"sidecar {k} is {shape(v)}"
                                         for k, v in (("display_name", dn), ("short_description", sd))
                                         if not is_text(v)))
        except yaml.YAMLError as e:
            side_detail = f"sidecar YAML error: {e}"
    check(results, island, "F7", side_ok, side_detail)

    check(results, island, "F8", bool(C_CITE.search(body)), "body cites ledger (C1..C28)")
    low = body.lower()
    # Presence, not truth (see the docstring): a substring test cannot audit whether the
    # labels are earned — only that the vocabulary is on the page for a human to check.
    check(results, island, "F9", "enforced" in low and "advisory" in low, "body names enforced vs advisory (presence only)")
    nlines = body.count("\n") + 1
    check(results, island, "F10", nlines <= 250, f"body {nlines} lines <=250")

    script_ok, script_detail = True, "no scripts"
    sdir = d / "scripts"
    if sdir.is_dir():
        details = []
        for f in sorted(sdir.iterdir()):
            if f.suffix == ".sh":
                r = subprocess.run(["bash", "-n", str(f)], capture_output=True, text=True)
                if r.returncode != 0:
                    script_ok = False
                    details.append(f"{f.name}: bash -n failed: {r.stderr.strip()[:120]}")
            elif f.suffix == ".py":
                # In-process compile(), never py_compile: py_compile's purpose IS to
                # write bytecode, so neither -B nor PYTHONDONTWRITEBYTECODE suppresses
                # it, and it would litter the island being validated with
                # scripts/__pycache__/ that the fleet installer then copies to every
                # seat. compile() checks syntax with zero filesystem writes.
                #
                # It is handed BYTES, never decoded text. Forcing utf-8 here made F11
                # reject a valid module carrying a PEP 263 coding cookie — the very
                # file `python3 -m py_compile` accepts — so the check was not the one
                # this docstring names. compile() on bytes applies the cookie and the
                # UTF-8 BOM exactly as py_compile's own reader does, and still raises
                # on undeclared non-UTF-8 source, an unknown encoding, and a NUL byte.
                try:
                    compile(f.read_bytes(), str(f), "exec")
                except (SyntaxError, ValueError) as e:
                    script_ok = False
                    details.append(f"{f.name}: syntax error: {str(e)[:120]}")
        script_detail = "; ".join(details) if details else "scripts syntax-clean"
    check(results, island, "F11", script_ok, script_detail)

    rdir = d / "references"
    if rdir.is_dir():
        for f in sorted(rdir.glob("*.md")):
            for link in MD_LINK.findall(f.read_text(encoding="utf-8")):
                if not link.startswith(".."):
                    print(f"WARN {island} W1 references/{f.name} links onward to '{link}' (one-level rule)")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    results = []
    for arg in sys.argv[1:]:
        d = Path(arg)
        if not d.is_dir():
            # Usage, not a verdict. Recording this as a failed F1 made "I could not find
            # this path" indistinguishable from "this island is malformed", so a typo or a
            # wrong working directory reported an island as broken. Exit 2 is the code this
            # tool already uses for being called wrong.
            print(f"validate-island: not a directory: {d}", file=sys.stderr)
            return 2
        validate(d, results)
    fails = [r for r in results if not r[2]]
    print(f"\n{len(results)} checks, {len(fails)} failed, islands: {len(set(r[0] for r in results))}")
    return 1 if fails else 0


if __name__ == "__main__":
    # The exit-code contract has to survive the interpreter's own shutdown. CPython flushes
    # the std streams after main() returns, and if that flush raises — a pipe whose reader
    # has already gone, which is the ordinary `gate.py … | head` idiom — it REPLACES the
    # status this script chose with 120, a code no table here names. An unhandled exception
    # is the other leak, and the worse one: it exits 1, and 1 is a VERDICT here, so a crash
    # would be read as a real finding about the code under test.
    try:
        _code = main()
    except SystemExit as _exc:                 # argparse raises this from inside
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
    except KeyboardInterrupt:
        _code = 2
    except BaseException as _exc:              # an exception is not a verdict
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
            if _code in (0, 1):                # output that never landed is not a verdict
                _code = 2
            try:                               # so the shutdown flush cannot raise again
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
