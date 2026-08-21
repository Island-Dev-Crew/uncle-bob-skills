#!/usr/bin/env python3
"""interface-comment-lint.py — every exported symbol carries a caller-facing interface comment.

Usage: python3 interface-comment-lint.py FILE.py [FILE.py ...]

Exported surface = every name in __all__ when a module declares one, accumulated over
every module-level assignment to it ('__all__ = [...]', '__all__ += [...]', and '+'
concatenations of literals); else every public module-level name bound to a def/class in
ANY of its bindings, plus the public names that alias-resolve to one — a name bound only
to an import or a value stays out. A definition bound inside a block that runs in the
ENCLOSING scope — if/else, try/except/finally, with, for, while, match — is a name in
that scope at runtime and is one here, at module level and inside a class body alike.
Public methods and public nested classes of an exported class are checked too, at any
nesting depth, and so are the public class attributes bound there by ALIAS
('render = _render'), which resolve against the class body first and the enclosing scope
second. A public member that reaches no def — a class constant, a class-body import, a
'staticmethod(_impl)' wrapper whose value is a call rather than a name — is outside the
nested surface by the same narrowing the module-level fallback states.

The two surface rules differ on purpose. The __all__ path judges a DECLARATION, so every
declared name is accounted for whatever it is bound to. The fallback path judges
DEFINITIONS and the public names that reach them, so a bare 'import os' or 'TIMEOUT = 30'
in a module with no __all__ is not a finding; that narrowing is named in the island's
advisory section rather than hidden.

A name bound more than once — a def in each branch of a version gate, a 'try:' def
shadowed by an 'except:' import, an alias in each branch — keeps EVERY binding, and
every alias on every branch is followed, so each def the name can hold is judged (either
undocumented branch fires) and the name is counted once. This holds at module level and
in a class body alike: both run the same collect_bindings walk and the same resolve, so
branch order never decides the verdict in either scope.

Name key: a symbol is matched by the identifier the parser produced (already NFKC-folded
by Python itself) compared exactly against the __all__ string literal. A spelling that
does not match is reported UNJUDGED, never quietly rerouted to a lenient branch — which
is also what 'from m import *' does with it at runtime. Input paths are deduplicated by
path_key() — the file's (st_dev, st_ino), not its spelling, because realpath folds '.',
'..' and symlinks but neither letter case nor Unicode normalization form — so one file
passed under two spellings is judged, and counted, once.

An __all__ entry that is not itself a def/class is followed through simple module-level
aliases (Name = _Name) to the def/class it names. When it cannot be followed — a
re-export bound to an import, a module-level constant, a name that does not exist —
the symbol is reported UNJUDGED rather than skipped, so the package-facade shape
cannot pass by being invisible.

Comments are folded to one line-shape before the leak vocabulary reads them — whitespace
runs collapsed, NFKC applied, format characters (U+FEFF, U+200B) dropped — so a phrasing
broken by an ordinary line wrap or by a posted zero-width character still matches.

Verdicts (each names the symbol and the reason):
  MISSING   exported symbol has no interface comment at all
  LEAKS     the comment names implementation the caller must not depend on
  RESTATES  the comment adds no word the symbol name did not already carry
  UNJUDGED  the exported name reached no def/class the lint could judge

The summary line prints the export surface and the nested public members separately, so
the count is checkable against the declared __all__ instead of asserted. Symbols are
counted by distinct qualified name.

Exit 0  at least one exported symbol checked, no verdicts
Exit 1  at least one verdict — the ONLY meaning exit 1 ever carries
Exit 2  usage error; a source that cannot be read, decoded or parsed; a report that
        cannot be delivered (fd 1 closed at startup, or open but unwritable — the
        report is flushed inside the guarded region so a broken pipe exits 2, not the
        interpreter's shutdown-flush 120); zero exported symbols; an __all__ that
        cannot be reduced to a fixed list of names; or any unexpected internal failure
"""
import ast
import os
import re
import sys
import unicodedata

# Leak vocabulary. Anchored on word boundaries because these are phrases inside
# prose, not whole lines. Every pattern is a literal in this file — nothing from
# the checked source or the argv is ever interpolated into a regex.
#
# 'internal' and 'recursive' are also ordinary caller-facing words ("internal rate
# of return", "yields recursively, depth-first"), so neither bare adjective fires:
# each is required to sit next to something that is unmistakably about the body.
LEAK_PATTERNS = [
    # Fires on the two commonest spellings as well as the bare one: a dotted
    # reference (store._pending_rows) and a name-mangled helper (__parse_row).
    # Case-blind after the underscore, so _Engine and _MAX_ROWS are private
    # symbols here exactly as they are to the interpreter. A dunder that opens
    # and closes (__enter__) is caller-facing protocol, not a private symbol, so
    # the trailing lookbehind keeps it out.
    ("private-symbol", re.compile(r"(?<!\w)_{1,2}[A-Za-z][A-Za-z0-9_]*(?<!__)\b")),
    ("internally", re.compile(
        r"\binternally\b"
        r"|\binternal\s+(?:helper|helpers|state|buffer|cache|representation|implementation"
        r"|detail|details|structure|format|method|methods|function|functions|module|class"
        r"|api|call|calls)\b", re.I)),
    ("under-the-hood", re.compile(r"\bunder the hood\b", re.I)),
    ("implemented-as", re.compile(r"\bimplemented\s+(?:as|by|using|with|in\s+terms\s+of)\b", re.I)),
    ("implementation-detail", re.compile(r"\bimplementation detail\b", re.I)),
    ("loop-shape", re.compile(r"\b(?:for|while)(?:\s+|-)loop\b", re.I)),
    ("recursion", re.compile(
        r"\brecursion\b"
        r"|\brecursive\s+(?:call|calls|helper|helpers|descent|implementation|algorithm|function|step|pass)\b"
        r"|\b(?:implemented|implement|computed|done|performed|resolved|built|processed|expanded"
        r"|works|work|operates|operate)\s+recursiv(?:e|ely)\b", re.I)),
    ("behind-the-scenes", re.compile(r"\bbehind the scenes\b", re.I)),
]

STOPWORDS = {"a", "an", "the", "this", "that", "of", "for", "to", "and", "or",
             "is", "are", "it", "its", "in", "on", "from", "with", "given"}
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]*")
CAMEL = re.compile(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])")
DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

# Compound statements whose bodies execute in the ENCLOSING scope. def/class are
# absent on purpose: they open a new scope, so a name bound inside one is not a
# name of the scope that contains it. Match/TryStar are looked up by name so this
# runs unchanged on Pythons that predate them.
SAME_SCOPE_BLOCKS = tuple(
    t for t in (getattr(ast, n, None) for n in
                ("If", "Try", "TryStar", "With", "AsyncWith", "For", "AsyncFor", "While", "Match"))
    if t is not None
)

UNJUDGED_REASON = {
    "import": "exported name is bound to an import — a re-export this lint cannot judge",
    "value": "exported name is bound to a module-level value, not a def or class",
    "undefined": "exported name is not defined in this module",
    "cycle": "exported name resolves through an alias cycle",
}
UNJUDGED_FALLBACK = "exported name reaches no definition this lint can judge"


def sub_bodies(node):
    """Every statement list `node` runs in its enclosing scope, or [] if it runs none."""
    if not isinstance(node, SAME_SCOPE_BLOCKS):
        return []
    out = [getattr(node, "body", []), getattr(node, "orelse", []), getattr(node, "finalbody", [])]
    out.extend(h.body for h in getattr(node, "handlers", []))
    out.extend(c.body for c in getattr(node, "cases", []))
    return [b for b in out if b]


def stem(word):
    """Crude plural/third-person fold so 'parses' and 'parse' compare equal."""
    low = word.lower()
    if len(low) > 4 and low.endswith("ies"):
        return low[:-3] + "y"
    if len(low) > 3 and low.endswith("s") and not low.endswith("ss"):
        return low[:-1]
    return low


def name_tokens(name):
    return {stem(p) for part in name.split("_") if part for p in CAMEL.findall(part)}


def restates(doc, name):
    """True when the WHOLE comment adds no word the symbol name did not already carry.

    Judged over every line, not the summary line alone: a PEP 257 docstring whose
    first line is a terse restatement but whose body states the contract is not a
    restatement, and failing it would push authors to degrade correct comments.
    """
    words = {stem(w) for w in WORD.findall(doc)} - STOPWORDS
    return not words or words <= name_tokens(name)


def fold(doc):
    """Normalize a comment to ONE line-shape before the vocabulary reads it.

    Three folds, each closing a way a named phrasing slips past a literal pattern:
    every whitespace run becomes one space, so a docstring wrapped at 88 columns
    ('under the\\nhood') matches exactly as the unwrapped one does — the commonest
    input there is, and a false green before this; NFKC, the same fold Python already
    applies to identifiers, so a ligature or full-width spelling matches; and format
    characters (category Cf — U+FEFF, U+200B) are dropped so a zero-width character
    cannot be posted inside a phrase to break it. Word content is untouched.
    """
    folded = unicodedata.normalize("NFKC", doc)
    folded = "".join(c for c in folded if unicodedata.category(c) != "Cf")
    return re.sub(r"\s+", " ", folded)


def leaks(doc):
    return [label for label, pat in LEAK_PATTERNS if pat.search(doc)]


def judge(node, where, name, findings):
    doc = ast.get_docstring(node)
    if doc is None or not doc.strip():
        findings.append(("MISSING", where, "no interface comment"))
        return
    doc = fold(doc)
    hits = leaks(doc)
    if hits:
        findings.append(("LEAKS", where, "names " + ", ".join(hits)))
    elif restates(doc, name):
        findings.append(("RESTATES", where, "adds no word beyond the symbol name"))


def public_members(body, outer):
    """Public members this class body binds, as (name, defs) in source order, plus its scope.

    Same `collect_bindings` walk and same `resolve` the module surface uses, so a method
    bound inside an `if sys.version_info` or a `try:` is a public attribute here exactly as
    it is at runtime — and so is one bound by ALIAS ('render = _render', 'warm = _impl'),
    which a def-only walk never saw. Names resolve against the class body first and the
    enclosing scope second, the order Python itself reads a class body in.

    A public member that reaches no def — a class constant, a class-body import, a
    'staticmethod(_impl)' wrapper whose value is a call and not a name — is outside this
    surface by the same narrowing the module-level fallback states, named in the island's
    advisory section rather than hidden. Members of a private nested class are not public
    and that whole subtree is never entered.
    """
    inner, order = {}, {}
    collect_bindings(body, inner, order)
    scope = dict(outer)
    scope.update(inner)
    members = []
    for name in sorted((n for n in inner if not n.startswith("_")), key=lambda n: order[n]):
        defs, _, _ = resolve(name, scope)
        if defs:
            members.append((name, defs))
    return members, scope


def inherited_members(node, outer, seen):
    """Public members a class inherits from same-module bases, nearest base first.

    A caller holding an `Engine()` sees `Engine.price` whether that method was written
    in Engine's body or in a base it extends, so the inherited names are part of the
    subclass's interface and are judged as such. Walking only the class body meant the
    most ordinary refactor there is — move the methods to a base class — turned a red
    verdict green without a single comment being added.

    Only a same-module base spelled as a bare name is resolvable here. An imported base
    or a dotted one (`mod.Base`) is outside this file's surface; its members are judged
    where that class is defined, and the island's advisory section names the boundary.
    `seen` carries the classes already on this walk so a base cycle terminates.
    """
    out = []
    for base in node.bases:
        if not isinstance(base, ast.Name):
            continue
        base_defs, _, _ = resolve(base.id, outer)
        for bnode in base_defs:
            if not isinstance(bnode, ast.ClassDef) or id(bnode) in seen:
                continue
            deeper = seen + (id(bnode),)
            members, _ = public_members(bnode.body, outer)
            out.extend(members)
            out.extend(inherited_members(bnode, outer, deeper))
    return out


def judge_tree(node, path, qualname, findings, judged, outer, open_classes=()):
    """Judge one def/class and, for a class, every public member its body can bind.

    `open_classes` holds the classes already on this walk, so a member aliased back to a
    class that contains it ('class E: self = E') is judged once and terminates instead of
    descending forever.
    """
    judge(node, f"{path}:{node.lineno}:{qualname}", qualname.rsplit(".", 1)[-1], findings)
    judged.add((path, qualname))
    if not isinstance(node, ast.ClassDef) or id(node) in open_classes:
        return
    members, scope = public_members(node.body, outer)
    inside = open_classes + (id(node),)
    for name, defs in members:
        for sub in defs:
            judge_tree(sub, path, f"{qualname}.{name}", findings, judged, scope, inside)
    # Then whatever this class inherits and does not override. An overriding member was
    # already judged above, so the name is skipped here; nearest base wins among the rest,
    # and `judged` keeps a member reached by two routes from being judged twice.
    covered = {name for name, _ in members}
    for name, defs in inherited_members(node, outer, inside):
        if name in covered or (path, f"{qualname}.{name}") in judged:
            continue
        covered.add(name)
        for sub in defs:
            judge_tree(sub, path, f"{qualname}.{name}", findings, judged, scope, inside)


def targets_all(node):
    """True when this assignment binds the module's __all__ name (not one of its slots)."""
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets)


def mutates_all(node):
    """True when this statement edits __all__ in place — '.extend(...)' or '[i] = ...'."""
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        fn = node.value.func
        return isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "__all__"
    if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for t in targets:
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == "__all__":
                return True
    return False


def reduce_all(node):
    """Reduce an __all__ expression to its string constants, or None when it cannot be.

    Handles the two shapes a package facade actually writes: a list/tuple literal,
    and '+' concatenations of them. Anything else — a comprehension, a call, a name,
    a starred element, a non-string element — is irreducible, and the caller fails
    closed on it.
    """
    if isinstance(node, (ast.List, ast.Tuple)):
        out = []
        for e in node.elts:
            if not (isinstance(e, ast.Constant) and isinstance(e.value, str)):
                return None
            out.append(e.value)
        return out
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = reduce_all(node.left), reduce_all(node.right)
        return None if left is None or right is None else left + right
    return None


def declared_all(tree, path):
    """Every name in __all__, in declaration order, or None when the module declares none.

    Accumulates across all module-level assignments — '__all__ = [...]' rebinds,
    '__all__ += [...]' extends — because a surface split over several statements is
    the standard package idiom, not an exotic input. Any __all__ this cannot reduce
    to a fixed list of strings (a mutation call at any depth, a conditional assignment,
    a computed value) exits 2 rather than silently reverting to the weaker fallback
    surface: an unreadable surface is an empty gate, and an empty gate cannot pass.
    """
    for node in ast.walk(tree):
        if mutates_all(node):
            die(f"error: {path}:{node.lineno}: __all__ mutated in place — "
                "surface cannot be reduced to a fixed list of names")
    names, declared, handled = [], False, set()
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) or not targets_all(node):
            continue
        declared = True
        handled.add(node.lineno)
        extend = isinstance(node, ast.AugAssign)
        value = node.value if not extend or isinstance(node.op, ast.Add) else None
        reduced = reduce_all(value) if value is not None else None
        if reduced is None:
            die(f"error: {path}:{node.lineno}: __all__ is not a list of string literals — "
                "surface cannot be reduced to a fixed list of names")
        names = names + reduced if extend else list(reduced)
    for node in ast.walk(tree):
        if (isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
                and targets_all(node) and node.lineno not in handled):
            die(f"error: {path}:{node.lineno}: __all__ assigned outside the module body — "
                "surface cannot be reduced to a fixed list of names")
    if not declared:
        return None
    seen, ordered = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered


def collect_bindings(body, bindings, order=None):
    """Record EVERY way each name in this scope is bound; `order` gets its first position.

    A list per name, never one binding: a name is rebound as a matter of routine — a
    version gate with a def in each branch, a 'try:' def shadowed by an 'except:' import,
    a def in one branch and an alias in the other — and only one of those branches runs.
    Overwriting would let branch ORDER decide the verdict.

    ONE walk serves both scopes. A class body binds names through the same statements a
    module body does — defs, imports, assignments, and any of them inside an enclosing-scope
    block — so 'render = _render' in a class body is a public attribute of that class at
    runtime, exactly as it is a public module name at module scope.
    """
    def record(name, entry, node):
        bindings.setdefault(name, []).append(entry)
        if order is not None and name not in order:
            order[name] = (node.lineno, node.col_offset)

    for node in body:
        if isinstance(node, DEF_NODES):
            record(node.name, ("def", node), node)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                record(a.asname or a.name.split(".")[0], ("import", a.name), node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            flat = []
            for t in targets:
                flat.extend(t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t])
            for t in flat:
                if not isinstance(t, ast.Name):
                    continue
                if isinstance(node.value, ast.Name) and len(flat) == 1:
                    record(t.id, ("alias", node.value.id), node)
                else:
                    record(t.id, ("value", type(node.value).__name__), node)
        else:
            for branch in sub_bodies(node):
                collect_bindings(branch, bindings, order)


def resolve(name, bindings):
    """Every def/class `name` can hold, plus the kind reported when it can hold none.

    Returns (defs, kind, detail). EVERY alias on EVERY branch is followed, not only the
    last one bound: 'if FLAG: warmup = _fast' / 'else: warmup = _slow' binds two aliases
    to one name, static reading cannot know which branch ran, and judging only the last
    would let branch order decide the verdict. The reason reported when the name reaches
    no def at all follows the last binding — the one an importer of this module sees.
    """
    defs, seen, queue = [], set(), [name]
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        for kind, detail in bindings.get(current, ()):
            if kind == "def":
                defs.append(detail)
            elif kind == "alias":
                queue.append(detail)
    walked, current = set(), name
    while current not in walked:
        walked.add(current)
        chain = bindings.get(current)
        if not chain:
            return defs, "undefined", current
        kind, detail = chain[-1]
        if kind != "alias":
            return defs, kind, detail
        current = detail
    return defs, "cycle", current


def mute(fd):
    """Point one std descriptor at os.devnull so a shutdown flush cannot override the code.

    CPython flushes sys.stdout and sys.stderr AFTER sys.exit has chosen a code; a flush
    that fails there is reported as 'Exception ignored' and the process exits 120
    instead. With the descriptor repointed, that last flush succeeds into nothing.
    """
    try:
        null = os.open(os.devnull, os.O_WRONLY)
        os.dup2(null, fd)
        os.close(null)
    except OSError:
        pass


def die(message):
    """Exit 2 — a usage/IO verdict must never share an exit code with a real one."""
    if sys.stdout is not None:
        try:
            sys.stdout.flush()
        except (OSError, ValueError):
            mute(1)
    if sys.stderr is not None:
        try:
            print(message, file=sys.stderr)
            sys.stderr.flush()
        except (OSError, ValueError):
            mute(2)
    sys.exit(2)


def account(name, where, path, bindings, findings, judged, surface):
    """Account for one exported name: judge EVERY def it reaches, or report why it reaches none.

    Both surface rules funnel through here, so a name bound in two branches of one 'if'
    is judged in both — either undocumented branch fires — and counted once, because
    `judged` and `surface` are keyed on (path, qualname).
    """
    surface.add((path, name))
    judged.add((path, name))
    defs, kind, _ = resolve(name, bindings)
    for node in defs:
        judge_tree(node, path, name, findings, judged, bindings)
    if not defs:
        findings.append(("UNJUDGED", where, UNJUDGED_REASON.get(kind, UNJUDGED_FALLBACK)))


def check_file(path, findings, judged, surface):
    """Judge one file's exported surface, recording every symbol accounted for."""
    try:
        # utf-8-sig, not utf-8: a leading BOM is what every Windows editor writes and
        # what CPython's own source reader strips, so a BOM must not turn a readable
        # module into an exit 2. Without a BOM it decodes exactly as utf-8 does.
        with open(path, encoding="utf-8-sig") as fh:
            src = fh.read()
    except OSError as e:
        die(f"error: cannot read {path}: {e}")
    except UnicodeDecodeError as e:
        die(f"error: cannot decode {path} as UTF-8: {e}")
    try:
        tree = ast.parse(src, filename=path)
    except (SyntaxError, ValueError) as e:
        die(f"error: cannot parse {path}: {e}")
    except (RecursionError, MemoryError) as e:
        die(f"error: cannot parse {path}: source too deeply nested to read ({type(e).__name__})")

    bindings = {}
    collect_bindings(tree.body, bindings)
    exported = declared_all(tree, path)
    if exported is None:
        # Same recursive walk and the same `account` both surface rules use, so a def
        # bound inside an 'if', 'try', 'with', 'for', 'while' or 'match' — a version
        # gate, an optional-dependency fallback — is a public module-level name here
        # exactly as it is at runtime, and so is a public name aliased to a private def
        # ('public = _impl'). A name that is a def in ANY of its bindings is in the
        # fallback surface even when a later branch rebinds it to an import or a value.
        for name, chain in list(bindings.items()):
            if name.startswith("_"):
                continue
            if not any(kind in ("def", "alias") for kind, _ in chain):
                continue
            account(name, f"{path}:{name}", path, bindings, findings, judged, surface)
        return

    for name in exported:
        account(name, f"{path}:__all__:{name}", path, bindings, findings, judged, surface)


def path_key(path):
    """Identity key for input dedupe: the file the kernel sees, never the spelling given.

    realpath folds '.', '..', '//' and symlinks, but neither letter case nor Unicode
    normalization form — and on a case-insensitive, NFD-preserving volume both of those
    are ordinary spellings of one file, which would then be read, judged and COUNTED
    twice under a sentence promising once. (st_dev, st_ino) is the identity the kernel
    itself uses, so every spelling of one file folds to one key.
    """
    try:
        st = os.stat(path)
    except OSError as e:
        die(f"error: cannot read {path}: {e}")
    return (st.st_dev, st.st_ino)


def deliver():
    """Force the report out while a delivery failure can still be converted into exit 2.

    The `sys.stdout is None` guard catches only fd 1 CLOSED at startup. A fd 1 that is
    open but unwritable — a pipe whose reader has exited, a full device — leaves the
    report in the buffer and fails at the shutdown flush, outside every handler here.
    Flushing now moves that failure inside the guarded region.
    """
    try:
        sys.stdout.flush()
    except (OSError, ValueError):
        die("error: report could not be delivered — a verdict that cannot be delivered is not a verdict")


def main(argv):
    if not argv:
        die(__doc__.strip())
    if sys.stdout is None:
        die("error: stdout is closed — a verdict that cannot be delivered is not a verdict")
    findings, judged, surface, seen = [], set(), set(), set()
    for path in argv:
        key = path_key(path)
        if key in seen:
            continue
        seen.add(key)
        check_file(path, findings, judged, surface)
    for verdict, where, why in findings:
        print(f"{verdict:<9} {where} — {why}")
    if not judged:
        die("error: 0 exported symbols found — an empty gate cannot pass")
    print(f"{len(judged)} judged ({len(surface)} exported, {len(judged - surface)} nested), "
          f"{len(findings)} without a usable interface comment")
    deliver()
    return 1 if findings else 0


if __name__ == "__main__":
    try:
        code = main(sys.argv[1:])
    except SystemExit:
        raise
    except BaseException as exc:  # an internal failure must never wear a verdict's code
        try:
            sys.stdout.flush()
        except (OSError, ValueError, AttributeError):
            mute(1)
        try:
            print(f"error: internal failure: {type(exc).__name__}: {exc}", file=sys.stderr)
            sys.stderr.flush()
        except Exception:
            mute(2)
        sys.exit(2)
    sys.exit(code)
