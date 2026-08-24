#!/usr/bin/env python3
"""assertless-scan.py — find tests that execute code without asserting on it.

Coverage counts execution, not assertion, so an assertion-free suite can drive a
coverage report (and a CRAP score) green while proving nothing. This scanner
parses test files with `ast` — it never imports or executes them — and flags
three gaming patterns per test function:

  NO-ASSERTION  the test's own body contains no assertion at all
  MOCK-ONLY     every assertion only observes a double — `assert_called*()`, or
                an assertion whose every value chain ends in `.called`,
                `.call_count`, `.call_args`, `.call_args_list`, `.mock_calls`,
                `.await_count`, `.await_args` — never the code under test
  SWALLOWED     a broad `except` whose body cannot propagate (no raise, no
                non-tautological assert, no fail, no declared helper), or a
                broad `contextlib.suppress(...)`, so a failure cannot go red

Assertions inside a nested def/lambda are NOT counted — blanket, whether the
test calls that inner function or not, since the parser cannot tell a live
callback from decoration. Delegating assertions to a named helper (nested or
top-level) is legitimate — declare it with --assert-helper, which is a written
excusal, echoed on the run's own output line so a captured artifact carries the
record. Nothing is allow-listed by default: pytest's `raises`/`warns`/
`deprecated_call` count only through a real pytest binding (`pytest.raises`, or
a name imported `from pytest import raises`), so a `.raises()` method on an
arbitrary object is not an assertion, and neither is `.suppress()`.

Watched names are resolved by IMPORT BINDING, not by spelling, so renaming one
at import does not defeat a rule: `from contextlib import suppress as quiet`,
`import contextlib as ctx` and `from builtins import Exception as Boom` land in
the same nets as the plain spellings. Test functions are collected from every
statement body at module scope — inside a version guard, a `try/except
ImportError`, or a nested class — because pytest collects those too and a
partial scan must never read as clean. Filenames are matched case-insensitively
for the same reason: over-collecting a `Test_Billing.py` is a false red, while
skipping it is the false green this scanner exists to catch.

HOISTING A NAME CHANGES NOTHING, in either direction. A name bound only to a
LITERAL contributes exactly what the inline literal contributed: nothing — in
the test, in its class body (`self.EXPECTED_CALLS`), or at module scope. A name
bound only to a MOCK OBSERVATION carries that observation's tips, so `actual =
gw.charge.call_args; assert actual == ((1200,), {})` is the same mock-only claim
as the inline form. A handler body that cannot fail does not rescue a broad
handler, whether it is written `assert True`, `ok = True; assert ok`,
`assert not False`, `assert 1 + 1` or `self.assertTrue(True)` — constant-folding
is done here, over bounded literal operands, never by executing the file.

Files are keyed by `(st_dev, st_ino)`, so the same file reached through `./`,
`//`, a trailing slash, a symlink, a relative and an absolute spelling, a
different Unicode form, or once directly and once through its directory is
scanned once — an inflated `scanned` count is a false evidence line. Source is
decoded as `utf-8-sig`, so a BOM written by a Windows editor is content, not a
parse error.

Exit codes — distinct meanings get distinct codes, and no error path may borrow
a verdict's code:
  0  clean verdict  — every scanned test asserts on something
  1  dirty verdict  — at least one finding
  2  usage / IO / parse error, including `--help`, an unwritable stdout and any
     unhandled internal error — never a verdict
  3  nothing to audit — no test functions found (fail closed; an empty scan
     cannot certify a suite)

Those four are the only codes that leave this process. CPython flushes the std
streams at interpreter shutdown and REPLACES the exit status with 120 when that
flush raises, so a `--help` into a dead stdout pipe — or argparse's own usage
error into a dead stderr — would otherwise report a code this script never
chose. The seal at the bottom of the file flushes both streams itself, downgrades
a verdict whose output never landed to 2, and points the dead fd at /dev/null so
the shutdown flush cannot raise.

This is a screen, not a proof: `assert result is not None` on a function that
can only return that object passes it. A surviving mutant is the proof that an
assertion is missing.
"""
import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

TEST_FUNC = re.compile(r"^test[A-Za-z0-9_]*$")
# `\w` rather than [A-Za-z0-9_]: for str patterns Python matches \w against Unicode,
# so `test_café.py` is collected. An ASCII-only class silently skipped any test module
# with a non-ASCII name that pytest itself collects and runs - the scan reported clean
# over tests it never read.
TEST_FILE = re.compile(r"^(?:test_\w*|\w+_test)\.py$", re.IGNORECASE)
UNITTEST_ASSERT = re.compile(r"^(?:assert[A-Z][A-Za-z0-9]*|fail)$")
MOCK_ASSERT = re.compile(r"^assert_[a-z0-9_]+$")
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PYTEST_ASSERT = frozenset({"raises", "warns", "deprecated_call"})
MOCK_OBS = frozenset({"called", "call_count", "call_args", "call_args_list",
                      "await_count", "await_args", "mock_calls"})
BROAD_EXC = frozenset({"Exception", "BaseException"})
SELF_NAMES = frozenset({"self", "cls"})

_UNKNOWN = object()          # the literal evaluator could not fold this expression
_MAX_INT, _MAX_LEN, _MAX_POW = 10 ** 18, 4096, 64
_RECORD = "helpers declared: none"   # the excusal record every `error:` line carries


def own_scope(body):
    """Yield every node in this statement list's OWN scope, skipping nested scopes."""
    stack = list(body)
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        stack.extend(ast.iter_child_nodes(node))


class Bindings(NamedTuple):
    """What the file's own imports bound each watched name to."""
    pytest_mods: frozenset    # module aliases for pytest
    pytest_bare: frozenset    # names imported from pytest
    ctx_mods: frozenset       # module aliases for contextlib
    broad: frozenset          # names bound to Exception / BaseException
    suppress: frozenset       # names bound to contextlib.suppress


class Scope(NamedTuple):
    """What names mean inside one test function."""
    consts: dict         # name -> literal node: contributes what the literal did, nothing
    assigned: dict       # name -> every value bound to it here (None = not an expression)
    class_consts: dict   # enclosing class body's literals, read as `self.NAME`


def bindings(tree):
    """Resolve the watched names by import binding, not by spelling.

    Renaming an import is an idiom swap, not a change to what a test proves, so
    `from contextlib import suppress as quiet` and `from builtins import
    Exception as Boom` must land in the same nets as the plain spellings — and
    `import contextlib as ctx` must carry `ctx.suppress` into the suppress net
    while leaving some arbitrary object's `.suppress()` method outside it.
    """
    mods, bare, ctx = set(), set(), set()
    broad, supp = set(BROAD_EXC), {"suppress"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "pytest":
                    mods.add(a.asname or a.name)
                elif a.name == "contextlib":
                    ctx.add(a.asname or a.name)
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name in BROAD_EXC:
                    broad.add(a.asname or a.name)
                elif a.name == "suppress" and node.module == "contextlib":
                    supp.add(a.asname or a.name)
                elif a.name in PYTEST_ASSERT and node.module == "pytest":
                    bare.add(a.asname or a.name)
    return Bindings(frozenset(mods), frozenset(bare), frozenset(ctx),
                    frozenset(broad), frozenset(supp))


def is_literal(node):
    """True when this expression is built only from literals.

    A literal cannot carry a value the code under test produced, so hoisting one
    into a name must not change what an assertion proves. Boolean and comparison
    operators over literals are literal too: `not False` and `1 == 1` vary at
    runtime exactly as much as `True` does.
    """
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(is_literal(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return (all(k is not None and is_literal(k) for k in node.keys)
                and all(is_literal(v) for v in node.values))
    if isinstance(node, ast.UnaryOp):
        return is_literal(node.operand)
    if isinstance(node, ast.BinOp):
        return is_literal(node.left) and is_literal(node.right)
    if isinstance(node, ast.BoolOp):
        return all(is_literal(v) for v in node.values)
    if isinstance(node, ast.Compare):
        return is_literal(node.left) and all(is_literal(c) for c in node.comparators)
    return False


def _small(v):
    """Bound what the literal evaluator will carry, so no fold can blow up."""
    if v is None or isinstance(v, (bool, float, complex)):
        return True
    if isinstance(v, int):
        return abs(v) < _MAX_INT
    if isinstance(v, (str, bytes, bytearray, list, tuple, set, frozenset, dict)):
        return len(v) < _MAX_LEN
    return False


_UNARY = {ast.Not: lambda a: not a, ast.USub: lambda a: -a,
          ast.UAdd: lambda a: +a, ast.Invert: lambda a: ~a}
_BINARY = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
           ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
           ast.FloorDiv: lambda a, b: a // b, ast.Mod: lambda a, b: a % b,
           ast.Pow: lambda a, b: a ** b}
_COMPARE = {ast.Eq: lambda a, b: a == b, ast.NotEq: lambda a, b: a != b,
            ast.Lt: lambda a, b: a < b, ast.LtE: lambda a, b: a <= b,
            ast.Gt: lambda a, b: a > b, ast.GtE: lambda a, b: a >= b,
            ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b}


def literal_value(node, consts, depth=0):
    """Fold an expression built only from literals to its value, else `_UNKNOWN`.

    Nothing is executed and nothing is `eval`'d: the operators are applied here,
    over bounded literal operands, so `not False`, `1 + 1`, `-1`, `1 == 1` and
    `"x" in "xyz"` are recognised as the constant-true asserts they are — each
    one token off `assert True` and just as unable to turn a test red. `is` /
    `is not` are left unfolded because literal identity is not a language
    guarantee, and `**` is folded only for small exponents.
    """
    if depth > 16:
        return _UNKNOWN
    if isinstance(node, ast.Name):
        node = consts.get(node.id)
        if node is None:
            return _UNKNOWN
    if isinstance(node, ast.Constant):
        return node.value if _small(node.value) else _UNKNOWN
    if isinstance(node, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
        if not is_literal(node):
            return _UNKNOWN
        try:
            value = ast.literal_eval(node)
        except Exception:
            return _UNKNOWN
        return value if _small(value) else _UNKNOWN
    if isinstance(node, ast.BoolOp):
        wants = isinstance(node.op, ast.Or)
        for v in node.values[:-1]:
            value = literal_value(v, consts, depth + 1)
            if value is _UNKNOWN:
                return _UNKNOWN
            if bool(value) is wants:
                return value
        return literal_value(node.values[-1], consts, depth + 1)
    operands, apply = [], None
    if isinstance(node, ast.UnaryOp):
        operands, apply = [node.operand], _UNARY.get(type(node.op))
    elif isinstance(node, ast.BinOp):
        operands, apply = [node.left, node.right], _BINARY.get(type(node.op))
    elif isinstance(node, ast.Compare) and len(node.ops) == 1:
        operands, apply = [node.left, node.comparators[0]], _COMPARE.get(type(node.ops[0]))
    if apply is None:
        return _UNKNOWN
    values = [literal_value(o, consts, depth + 1) for o in operands]
    if any(v is _UNKNOWN or not _small(v) for v in values):
        return _UNKNOWN
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        if not isinstance(values[1], int) or abs(values[1]) > _MAX_POW:
            return _UNKNOWN
    try:
        result = apply(*values)
    except Exception:
        return _UNKNOWN
    return result if _small(result) else _UNKNOWN


def _bound_names(target):
    """Every plain name this assignment target binds."""
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for e in target.elts:
            yield from _bound_names(e)
    elif isinstance(target, ast.Starred):
        yield from _bound_names(target.value)


def _each_binding(body):
    """Yield (targets, value) for every name binding in this scope; value None = not an expression."""
    for node in own_scope(body):
        if isinstance(node, ast.Assign):
            yield node.targets, node.value
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
            yield [node.target], node.value
        elif isinstance(node, ast.AugAssign):
            yield [node.target], None
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
            yield [node.target], None
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            yield [node.optional_vars], None


def constant_bindings(body, inherited=None, shadowed=()):
    """Map each name bound ONLY to literals in this scope to its literal node.

    Extracting an expected value to a name is the cheapest idiom swap there is —
    it changes the wording of a test without changing what it proves — so a
    constant-bound name must contribute exactly what the inline literal
    contributed. A name bound anywhere in the same scope to something else (a
    call, an attribute, a loop variable) is never constant, whichever binding is
    written first. `shadowed` names — this test's own parameters — drop any
    inherited module constant of the same name, so a fixture value is never read
    as a literal; rebinding a parameter to a literal still makes it constant,
    because that is the same hoist one step further along.
    """
    const, real = dict(inherited or {}), set()
    for n in shadowed:
        const.pop(n, None)
    for targets, value in _each_binding(body):
        literal = value is not None and is_literal(value)
        for t in targets:
            for n in _bound_names(t):
                if literal:
                    if n not in real:
                        const[n] = value
                else:
                    real.add(n)
                    const.pop(n, None)
    return const


def assigned_values(body):
    """Map each name bound in this scope to every value bound to it.

    Read by `observation_tips` to carry a hoisted mock observation through the
    name that holds it — the mirror image of dropping a hoisted literal.
    """
    out = {}
    for targets, value in _each_binding(body):
        for t in targets:
            for n in _bound_names(t):
                out.setdefault(n, []).append(value)
    return out


def const_truth(node, scope):
    """True/False when this expression is a constant of known truthiness, else None.

    `assert True`, `assert 1`, `ok = True; assert ok`, `assert not False` and
    `assert 1 + 1` cannot turn a test red; `assert False, "must not raise"`
    always can, and is a legitimate handler.
    """
    value = literal_value(node, scope.consts)
    return None if value is _UNKNOWN else bool(value)


def is_broad(exc, b):
    """Bare handler, or one naming a broad class — plain, dotted, or renamed at import."""
    if exc is None:
        return True
    parts = exc.elts if isinstance(exc, ast.Tuple) else [exc]
    return any(
        (isinstance(p, ast.Name) and p.id in b.broad)
        or (isinstance(p, ast.Attribute) and p.attr in BROAD_EXC)
        for p in parts
    )


def suppresses_broadly(expr, b):
    """`with suppress(Exception):` eats every failure inside it — no handler node exists.

    Resolved by binding: a bare name bound to `contextlib.suppress` however
    aliased, or `<contextlib-alias>.suppress`. Some arbitrary object's
    `.suppress()` method is not contextlib's, exactly as `.raises()` on an
    arbitrary object is not pytest's.
    """
    if not isinstance(expr, ast.Call):
        return False
    f = expr.func
    if isinstance(f, ast.Attribute):
        hit = f.attr == "suppress" and isinstance(f.value, ast.Name) and f.value.id in b.ctx_mods
    else:
        hit = getattr(f, "id", None) in b.suppress
    return hit and any(is_broad(a, b) for a in expr.args)


def observation_tips(nodes, scope):
    """Terminal name of every value chain in these expressions.

    `gateway.charge.call_args == ((1200,), {})` -> ['call_args']
    `gateway.charge.call_args == expected`      -> ['call_args']  (expected is a literal)
    `actual == ((1200,), {})`                   -> ['call_args']  (actual holds the observation)
    `gateway.charge.call_count == self.N`       -> ['call_count'] (N is a class-body literal)
    `receipt.total == 5`                        -> ['total']
    `assert True`                               -> []          (no chain at all)

    A callee is not a value being asserted, so a Call's func is never a tip, and
    neither is a name — or a `self.NAME` — that only ever held a literal. A name
    bound only to mock observations reports those observations instead of
    itself, resolved transitively with a visited set so `a = gw.charge.called;
    b = a` carries; a name holding anything else is a real value however it is
    spelled.
    """
    tips = []

    def hoisted_mock_tips(name, seen):
        values = scope.assigned.get(name)
        if not values or name in seen:
            return None
        seen = seen | {name}
        carried = []
        for v in values:
            if v is None:
                return None
            got = []
            visit(v, True, got, seen)
            if not got or not all(t in MOCK_OBS for t in got):
                return None
            carried.extend(got)
        return carried

    def visit(node, record, out, seen):
        if isinstance(node, ast.Attribute):
            base = node.value
            if (isinstance(base, ast.Name) and base.id in SELF_NAMES
                    and node.attr in scope.class_consts):
                return
            if record:
                out.append(node.attr)
            visit(base, False, out, seen)
        elif isinstance(node, ast.Name):
            if not record:
                return
            carried = hoisted_mock_tips(node.id, seen)
            if carried is not None:
                out.extend(carried)
            elif node.id not in scope.consts:
                out.append(node.id)
        elif isinstance(node, ast.Call):
            visit(node.func, False, out, seen)
            for arg in node.args:
                visit(arg, True, out, seen)
            for kw in node.keywords:
                visit(kw.value, True, out, seen)
        else:
            for child in ast.iter_child_nodes(node):
                visit(child, True, out, seen)

    for n in nodes:
        visit(n, True, tips, frozenset())
    return tips


def observes_only_mock(nodes, scope):
    """True when the assertion looks only at the double, never at a real value."""
    tips = observation_tips(nodes, scope)
    return bool(tips) and all(t in MOCK_OBS for t in tips)


def call_cannot_fail(name, args, scope):
    """True when a unittest-style assert call is a tautology no run can turn red.

    `self.assertTrue(True)` is the `assert True` of the unittest idiom, and
    `self.assertEqual(1, 1)` is the same claim spelled longer. Only calls whose
    arguments fold to literals are judged; `self.fail(...)` always raises, so it
    is never a tautology.
    """
    if name in ("assertTrue", "assertFalse") and args:
        return const_truth(args[0], scope) is (name == "assertTrue")
    if name in ("assertEqual", "assertEquals", "assertNotEqual") and len(args) >= 2:
        left, right = (literal_value(a, scope.consts) for a in args[:2])
        if left is _UNKNOWN or right is _UNKNOWN:
            return False
        try:
            same = bool(left == right)
        except Exception:
            return False
        return same if name != "assertNotEqual" else not same
    return False


def can_propagate(body, helpers, b, scope):
    """True when a broad handler body can still turn the test red.

    An `assert` counts only when it could fail: a constant-true assert is the
    one-token evasion off `except Exception: pass`, and it eats the failure
    identically — as does the same tautology written `self.assertTrue(True)`.
    """
    for node in own_scope(body):
        if isinstance(node, ast.Raise):
            return True
        if isinstance(node, ast.Assert):
            if const_truth(node.test, scope) is not True:
                return True
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute):
                base = f.value.id if isinstance(f.value, ast.Name) else None
                if f.attr in helpers:
                    return True
                if (UNITTEST_ASSERT.match(f.attr) and (base in SELF_NAMES or base in b.pytest_mods)
                        and not call_cannot_fail(f.attr, node.args, scope)):
                    return True
            elif isinstance(f, ast.Name):
                if f.id in helpers:
                    return True
                if UNITTEST_ASSERT.match(f.id) and not call_cannot_fail(f.id, node.args, scope):
                    return True
    return False


def classify(fn, helpers, b, module_consts, class_consts):
    """Return (real_assertions, mock_assertions, swallow_reason_or_None)."""
    real = mock = 0
    swallow = None
    params = {a.arg for a in ast.walk(fn.args) if isinstance(a, ast.arg)}
    scope = Scope(constant_bindings(fn.body, module_consts, params),
                  assigned_values(fn.body), class_consts)
    for node in own_scope(fn.body):
        if isinstance(node, ast.Assert):
            if observes_only_mock([node.test], scope):
                mock += 1
            else:
                real += 1
        elif isinstance(node, ast.ExceptHandler):
            if not swallow and is_broad(node.type, b) and not can_propagate(node.body, helpers, b, scope):
                swallow = "broad except whose body cannot propagate — the test cannot go red"
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            if not swallow and any(suppresses_broadly(i.context_expr, b) for i in node.items):
                swallow = "suppress() of a broad exception — the test cannot go red"
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute):
                base = f.value.id if isinstance(f.value, ast.Name) else None
                if UNITTEST_ASSERT.match(f.attr) and base in SELF_NAMES:
                    if observes_only_mock(node.args + [k.value for k in node.keywords], scope):
                        mock += 1
                    else:
                        real += 1
                elif f.attr in PYTEST_ASSERT and base in b.pytest_mods:
                    real += 1
                elif f.attr in helpers:
                    real += 1
                elif MOCK_ASSERT.match(f.attr):
                    mock += 1
            elif isinstance(f, ast.Name) and (f.id in helpers or f.id in b.pytest_bare):
                real += 1
    return real, mock, swallow


def class_constants(tree):
    """Every class body's literals in this file, keyed by class name.

    `self.EXPECTED_CALLS = 1` in a class body is the unittest spelling of the
    hoist a local already loses, and a shared `class Base: EXPECTED_CALLS = 1`
    is the same hoist one scope further out, so a base named in this file is
    merged in first and the class's own bindings win. A base imported from
    ANOTHER file cannot be resolved from one parse tree and is disclosed unseen.
    """
    own = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}

    def consts_for(name, seen=frozenset()):
        node = own.get(name)
        if node is None or name in seen:
            return {}
        merged = {}
        for base in node.bases:
            base_name = getattr(base, "id", None) or getattr(base, "attr", None)
            if base_name:
                merged.update(consts_for(base_name, seen | {name}))
        merged.update(constant_bindings(node.body))
        return merged

    return {name: consts_for(name) for name in own}


def test_functions(node, by_class, class_consts=None):
    """Every (test function, enclosing class constants) reachable at module scope.

    pytest collects a `def` that a version guard, a `try/except ImportError`, or
    a nested class merely wraps — all of them are module attributes at runtime.
    Reading only `tree.body` would silently under-collect and hand back a green
    verdict over tests it never scanned, so recursion stops only at the boundary
    of another function's scope.
    """
    class_consts = class_consts or {}
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if TEST_FUNC.match(child.name):
                yield child, class_consts
        elif isinstance(child, ast.ClassDef):
            yield from test_functions(child, by_class, by_class.get(child.name, {}))
        elif not isinstance(child, ast.Lambda):
            yield from test_functions(child, by_class, class_consts)


def file_key(p):
    """The one documented identity key for a scanned file.

    `(st_dev, st_ino)` is the filesystem's own answer, so `./f`, `d//f`, `d/../d/f`,
    an absolute spelling, a symlink, an NFC/NFD spelling of the same macOS name,
    a letter-case variant on a case-insensitive filesystem, and `d f` (the
    directory plus a file inside it) all key to one entry. Keying on the spelling
    instead would double-count and inflate the scanned total.
    """
    st = p.stat()
    return (st.st_dev, st.st_ino)


def halt_on_walk_error(err):
    """A directory the walk could not read is not an empty directory.

    `os.walk` swallows a scandir failure by default: an unreadable subtree is
    dropped silently, nothing is printed, and the scan reports a clean verdict
    over test files it never opened. That is the same under-collection false
    green as a skipped symlinked tree, only quieter — and a mode-000 directory,
    a root-owned mount, or a checkout restored with tight permissions all reach
    it without any hostile intent. Re-raising puts the OSError on `collect`'s
    error path, which `run` turns into exit 2: a non-verdict, never a green.
    """
    raise err


def canonical(path):
    """The one spelling a containment test may compare: fully resolved, every '.',
    '..' and symlink component gone, so a prefix test states a fact about the
    filesystem rather than about the string the caller typed."""
    return os.path.normcase(os.path.realpath(path))


def require_inside(path, roots):
    """PATH AUTHORITY: this scan reads exactly what the caller named.

    Following links let a symlink inside a scanned tree point at a sibling
    checkout, and the scanner then read and PRINTED findings from files nobody
    authorized it to open. Documenting that behaviour is not authority to take
    it. An escape is refused BY NAME and fail-closes, because pruning it in
    silence would be the same false green the followlinks default already
    produced once. `--allow-root` is how a caller widens the scan deliberately —
    a decision they make, rather than one a link makes for them. Not a sandbox: a
    hard link or a bind mount is a real entry inside the tree and no path test
    sees through it.
    """
    real = canonical(path)
    for r in roots:
        if real == r or real.startswith(r.rstrip(os.sep) + os.sep):
            return
    raise OSError(
        f"{path} resolves to {os.path.realpath(path)}, outside every authorized "
        f"root - pass --allow-root to authorize that target, or take the link "
        f"out of the scanned tree")


def collect(paths, allow_roots=()):
    seen, files = set(), []
    roots = [canonical(p) for p in paths]
    for r in allow_roots:
        if not os.path.exists(r):
            raise OSError(f"--allow-root {r}: no such path")
        roots.append(canonical(r))
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            # os.walk(followlinks=True), not Path.rglob: rglob refuses to descend into
            # a symlinked directory while pytest walks straight into it, so a symlinked
            # test tree was collected by the runner and skipped by this scan - a clean
            # report over tests that were never read. Following links reintroduces the
            # risk of a directory cycle, so each directory is visited once by its real
            # path; file-level duplicates still fold through file_key below.
            found, walked = [], set()
            for root, dirs, names in os.walk(p, followlinks=True, onerror=halt_on_walk_error):
                try:
                    real = os.path.realpath(root)
                except OSError:
                    real = root
                if real in walked:
                    dirs[:] = []
                    continue
                walked.add(real)
                for d in list(dirs):
                    require_inside(os.path.join(root, d), roots)
                for n in names:
                    if TEST_FILE.match(n):
                        require_inside(os.path.join(root, n), roots)
                        found.append(Path(root) / n)
            found = sorted(found)
        elif p.is_file():
            found = [p]
        else:
            raise OSError(f"not a readable file or directory: {raw}")
        for f in found:
            key = file_key(f)
            if key in seen:
                continue
            seen.add(key)
            files.append(f)
    return files


def _silence_stdout():
    """Stop the interpreter re-reporting a dead stdout at shutdown."""
    try:
        os.dup2(os.open(os.devnull, os.O_WRONLY), 1)
    except OSError:
        pass


def emit(lines):
    """Write the verdict's evidence, or raise so the caller can exit 2.

    A verdict whose evidence never reached the artifact is not a verdict. With
    fd 1 closed (`1>&-`) CPython sets `sys.stdout` to None and `print` silently
    does nothing, which would hand a CI consumer a bare exit 0 with an empty
    captured stdout — the exact fake green this island exists to catch.
    """
    out = sys.stdout
    if out is None:
        raise OSError("stdout is closed — a verdict cannot be reported without its evidence")
    for line in lines:
        print(line, file=out)
    out.flush()


def excusal_line(names):
    """The written excusal every summary and every `error:` line carries."""
    return f"helpers declared: {', '.join(sorted(names)) or 'none'}"


def declared_from_argv(argv):
    """Read `--assert-helper` straight from argv, so a failure that happens before
    (or instead of) a successful parse still carries the excusal record."""
    names, tokens = [], iter(argv)
    for tok in tokens:
        if tok == "--assert-helper":
            nxt = next(tokens, None)
            if nxt is not None:
                names.append(nxt)
        elif tok.startswith("--assert-helper="):
            names.append(tok.split("=", 1)[1])
    return {n for n in names if n}


class RecordingParser(argparse.ArgumentParser):
    """argparse's own usage errors must carry the excusal record too."""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"error: {message} ({_RECORD})", file=sys.stderr)
        raise SystemExit(2)


def run(argv):
    global _RECORD
    ap = RecordingParser(description="Flag tests that execute code without asserting on it.")
    ap.add_argument("paths", nargs="+", help="test files, or directories scanned for test_*.py / *_test.py")
    ap.add_argument("--allow-root", action="append", default=[], metavar="DIR",
                    help="authorize an additional root the scan may read (repeatable)")
    ap.add_argument("--assert-helper", action="append", default=[], metavar="NAME",
                    help="treat calls to NAME as a real assertion (repeatable; each use is an excusal)")
    args = ap.parse_args(argv)
    helpers = set(args.assert_helper)
    excusal = _RECORD = excusal_line(helpers)
    bad = sorted(h for h in helpers if not IDENT.match(h))
    if bad:
        print(f"error: --assert-helper needs a Python identifier, got: {', '.join(bad)} ({excusal})",
              file=sys.stderr)
        return 2

    try:
        files = collect(args.paths, args.allow_root)
    except OSError as e:
        print(f"error: {e} ({excusal})", file=sys.stderr)
        return 2

    scanned, findings = 0, []
    for f in files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8-sig"), filename=str(f))
        except (OSError, SyntaxError, ValueError, RecursionError) as e:
            print(f"error: cannot parse {f}: {e} ({excusal})", file=sys.stderr)
            return 2
        b = bindings(tree)
        module_consts = constant_bindings(tree.body)
        for fn, class_consts in test_functions(tree, class_constants(tree)):
            scanned += 1
            real, mock, swallow = classify(fn, helpers, b, module_consts, class_consts)
            if real == 0 and mock == 0:
                findings.append(("NO-ASSERTION", f, fn, "executes code, asserts nothing"))
            elif real == 0:
                findings.append(("MOCK-ONLY", f, fn, f"{mock} assertion(s) on the double, none on the code under test"))
            if swallow:
                findings.append(("SWALLOWED", f, fn, swallow))

    if not scanned:
        print(f"error: no test functions found — nothing to audit ({excusal})", file=sys.stderr)
        return 3

    lines = [f"{v:<13} {f}:{fn.lineno}  {fn.name}  {why}" for v, f, fn, why in findings]
    lines.append(f"{scanned} test function(s) scanned, {len(findings)} finding(s) — {excusal}")
    try:
        emit(lines)
    except (OSError, ValueError) as e:
        _silence_stdout()
        print(f"error: cannot write the verdict: {e} ({excusal})", file=sys.stderr)
        return 2
    return 1 if findings else 0


def main(argv=None):
    """Every error path returns 2 — no crash, and no `--help`, may borrow a
    verdict's code. The `__main__` seal below carries that guarantee through
    interpreter shutdown, where a failed stream flush would otherwise substitute
    CPython's 120 for whatever this function returned."""
    global _RECORD
    argv = list(sys.argv[1:] if argv is None else argv)
    _RECORD = excusal_line(declared_from_argv(argv))
    try:
        return run(argv)
    except SystemExit:      # argparse's own exit: usage or --help, never a verdict
        return 2
    except Exception as e:  # RecursionError, MemoryError, and any unforeseen bug
        try:
            print(f"error: {type(e).__name__}: {e} ({_RECORD})", file=sys.stderr)
        except Exception:
            pass
        return 2


if __name__ == "__main__":
    # The seal: 0/1/2/3 are the only codes that may leave this process.
    # CPython flushes the std streams at shutdown and REPLACES the exit status
    # with 120 if that flush raises — a dead stdout pipe under `--help`, a dead
    # stderr under argparse's usage error. Flush both here instead, downgrade a
    # verdict whose evidence never landed to 2, and redirect the dead fd to
    # /dev/null so the shutdown flush has nothing left to fail on.
    try:
        _code = main()
    except SystemExit as _e:        # argparse's usage exit and `--help` arrive here
        _code = _e.code if isinstance(_e.code, int) else (0 if _e.code is None else 1)
    except BaseException as _e:     # no unexpected error may wear a verdict's code
        try:
            print(f"error: internal error - {type(_e).__name__}: {_e} ({_RECORD})",
                  file=sys.stderr)
        except BaseException:
            pass
        _code = 2
    for _stream, _fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if _stream is not None:
                _stream.flush()
        except BaseException:
            if _code in (0, 1):     # output that never landed is not a verdict
                _code = 2
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
