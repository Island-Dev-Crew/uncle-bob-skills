#!/usr/bin/env python3
"""test-name-lint.py — the name floor for a unit suite read as documentation.

A fresh-context agent reads test names to learn what a system does, so a name
that states no behaviour teaches nothing. This lints the NAMES only; whether the
sentence is true stays a human spot-check.

Readability violations, checked in this order - a name reports the FIRST of these
it fails, not all of them. DUPLICATE is orthogonal and co-fires with any of them;
NO-TESTS is the whole-file verdict when there is no name to judge at all:
  UNFOLDABLE    a character survives the fold outside ASCII, so the word split
                cannot read the name (test_bøsic_høppy_pøth, test_проверка)
  THIN-NAME     fewer than --min-words behaviour words after the 'test' prefix
                (test_1, test_it_works - too short to reach PLACEHOLDER)
  PLACEHOLDER   every behaviour word is filler or a digit (test_case_2_works)
  MIRRORS-CODE  name is exactly a callable name in --against (the method, not the behaviour)
  DUPLICATE     two test names collide in one scope — the later silently shadows
  NO-TESTS      file declares no test names (fail closed - deleting tests cannot pass)

Input:  Python test files. A NAME IS A TEST IF IT STARTS WITH 'test' - pytest's own
        default contract (python_functions = test*), so 'testtotal', a module-level
        alias 'test_1 = _impl', a def hidden inside 'if'/'try'/'with', a for target,
        a with-as, a match capture, a walrus, a name declared 'global' inside a
        helper's body, and a name bound by 'from helpers import test_total' are all
        linted, not skipped.
        Collecting narrower than the runner is how a laundered suite goes green.
Exit:   0 clean, 1 violations found, 2 usage/IO/decode/parse/encode/write error
        (never a verdict).

Usage:
  test-name-lint.py [--min-words N] [--against src.py] test_a.py [test_b.py ...]
"""
import argparse
import ast
import os
import re
import sys
import unicodedata

PREFIX = "test"
WORD = re.compile(r"[A-Z][a-z]*|[a-z]+|[0-9]+")
FILLER = frozenset("""a an and basic base bar baz case cases check checks foo func function
happy it main method misc new ok other path run sanity simple stuff temp test testing tests
thing things tmp todo work working works xxx yyy zzz""".split())
# Not statements, but they wrap one: `except` handlers and (3.10+) `match` cases.
BLOCK_WRAPPERS = tuple(c for c in (ast.ExceptHandler, getattr(ast, "match_case", None)) if c)
MATCH_CAPTURE = tuple(c for c in (getattr(ast, "MatchAs", None), getattr(ast, "MatchStar", None)) if c)
MATCH_MAPPING = tuple(c for c in (getattr(ast, "MatchMapping", None),) if c)


def fold(text):
    """The ONE key function every name passes through before it is compared.

    NFKD-decompose and drop combining marks, so a respelling whose accents
    DECOMPOSE keys the same as its ASCII twin: 'test_it_wörks' must not launder
    past the filler set that catches 'test_it_works', and
    'test_rénder_invoice_line' must not launder past MIRRORS-CODE. Python's own
    parser already NFKC-normalizes identifiers, so NFC and NFD spellings of one
    name arrive here identical; this fold is what makes the accented spelling
    and the plain one identical too.

    What NFKD leaves atomic - ø ł đ æ œ ß þ, Cyrillic, Han - this cannot key,
    and it must not be allowed to judge such a name either way: see unfoldable().
    """
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def unfoldable(name):
    """Characters the fold could not reduce to ASCII, deduplicated and sorted.

    The fail-CLOSED half of the fold, and the reason it exists: WORD understands
    only ASCII, so anything left over is silently treated as a word separator.
    That does not merely lose a word, it SHATTERS one - 'test_bøsic_høppy_pøth'
    splits into six fragments ('b','sic','h','ppy','p','th'), none of them in the
    filler set, and a name that states nothing scores six behaviour words. So a
    residue is a violation, not a judgement: an unreadable name is REJECTED
    (UNFOLDABLE) rather than passed. Non-letters count too - a non-ASCII digit or
    connector shatters a word exactly as a stroke letter does.
    """
    return tuple(sorted({c for c in fold(name) if not c.isascii()}))


def behaviour_words(name):
    """Words a test name asserts, or None when the name is not a test.

    Membership follows pytest exactly - the RAW identifier must start with
    'test', which is what pytest fnmatches - and only the remainder is folded
    and split, on underscores AND camel/digit boundaries, so 'testtotal' states
    one word and 'testcase2works' states only filler. Trustworthy only for a
    name unfoldable() calls clean; the caller checks that first.
    """
    if not name.startswith(PREFIX):
        return None
    return [w.lower() for w in WORD.findall(fold(name[len(PREFIX):]))]


def nested_statements(node):
    """Statements one level inside `node`, through every block it owns.

    `node.body` alone is the forge: it stops at the first compound statement, so
    a test def under `if sys.version_info`, inside `try/except/else/finally`, or
    under `with` is never seen while pytest still collects it. Following every
    child statement - and stepping through the except-handler and match-case
    wrappers, which are not statements themselves - reaches all of them, and the
    caller refuses to enter function bodies, where pytest collects nothing.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.stmt):
            yield child
        elif isinstance(child, BLOCK_WRAPPERS):
            yield from nested_statements(child)


def header_bindings(stmt):
    """(name, lineno) for every name this statement's OWN header text binds.

    `=` is not the only binder, and a collector that only knows `=` hands the
    forge a silent pass: `if (test_1 := _impl)`, `for test_total in (_impl,)`,
    `with ctx() as test_it_works`, `case [test_x]`, `except E as test_y`,
    `test_z += _impl` and `import`/`from ... import` all bind a name the file's
    own text spells, and pytest collects each one whose object is callable.
    So this scans every Store-context Name plus the non-Name binders, over the
    statement's header expressions only.

    Three scopes are deliberately NOT entered HERE, because what they bind is
    not bound in this header: the bodies of nested statements (the statement
    walker reaches those itself, including a class body, which it enters and
    scopes by the class name), the bodies of nested defs/classes/lambdas (the
    walker records the def's own name and reads its `global` declarations
    instead - see global_declarations), and a comprehension's own `for` target -
    PEP 572 puts a comprehension walrus in the containing scope but keeps the
    loop target inside the comprehension, and pytest agrees.

    Iterative on purpose: a recursive scan raises RecursionError on a deeply
    nested expression, and an uncaught crash exits 1 - the code reserved for a
    real verdict.
    """
    out, stack = [], [stmt]
    while stack:
        node = stack.pop()
        line = getattr(node, "lineno", stmt.lineno)
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                out.append((node.id, line))
            continue
        if isinstance(node, ast.alias):
            out.append(((node.asname or node.name).split(".")[0], stmt.lineno))
            continue
        if isinstance(node, ast.ExceptHandler):
            if node.name:
                out.append((node.name, line))
            continue  # its body is a statement block
        if isinstance(node, ast.Lambda):
            # Only the defaults evaluate out here; the body binds in its own scope.
            stack.extend(d for d in node.args.defaults if d)
            stack.extend(d for d in node.args.kw_defaults if d)
            continue
        if isinstance(node, ast.comprehension):
            stack.append(node.iter)
            stack.extend(node.ifs)
            continue  # node.target is comprehension-scoped, not bound here
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            stack.extend(node.decorator_list)
            stack.extend(getattr(node, "type_params", None) or [])
            if isinstance(node, ast.ClassDef):
                stack.extend(node.bases)
                stack.extend(node.keywords)
            else:
                stack.append(node.args)
                if node.returns is not None:
                    stack.append(node.returns)
            continue  # the def's own name is recorded by the statement walker
        if MATCH_CAPTURE and isinstance(node, MATCH_CAPTURE) and node.name:
            out.append((node.name, line))
        elif MATCH_MAPPING and isinstance(node, MATCH_MAPPING) and node.rest:
            out.append((node.rest, line))
        for child in ast.iter_child_nodes(node):
            if not isinstance(child, ast.stmt):
                stack.append(child)
    return out


def global_declarations(node):
    """(name, lineno) for every name a `global` inside this def declares.

    A def's body binds in its own scope - unless `global` says otherwise. So
    `def _install(): global test_1; test_1 = _impl`, called at import, binds
    test_1 at MODULE scope and pytest collects it, while a walker that records
    the def's name and refuses to descend sees nothing: the same forge as the
    walrus and the `for` target, moved one indent down behind a keyword. The
    name is spelled in the file's own text, so recording the declaration alone
    is fail-closed - true whether or not the installer is ever called.
    `nonlocal` is deliberately excluded: it rebinds in an enclosing FUNCTION
    scope, which pytest never collects from.

    ast.walk is iterative (a deque), so a pathological nesting cannot raise
    RecursionError here.
    """
    for child in ast.walk(node):
        if isinstance(child, ast.Global):
            for name in child.names:
                yield name, child.lineno


def collect_tests(tree):
    """(scope, name, lineno) for every test name the file's own text binds, scope '' at module level.

    Bindings count, not just defs - see header_bindings for the full list. A
    def-only, body-only, assignment-only collector hands those forges a silent
    pass. Class bodies ARE entered, carrying the class name as the scope, which
    is how `unittest` methods are reached and how DUPLICATE is scoped. Returned
    in textual order so DUPLICATE's "the later shadows the earlier" is true as
    written - which is also why a `global`-declared name is added only when the
    module does not already bind it: one module binding, however many defs
    declare it, so a helper cannot manufacture a false DUPLICATE.
    """
    found, declared = [], []

    def record(into, scope, name, lineno):
        if behaviour_words(name) is not None:
            into.append((scope, name, lineno))

    def walk(node, scope):
        for child in nested_statements(node):
            for name, line in header_bindings(child):
                record(found, scope, name, line)
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                record(found, scope, child.name, child.lineno)
                for name, line in global_declarations(child):
                    record(declared, "", name, line)
            elif isinstance(child, ast.ClassDef):
                walk(child, child.name)
            else:
                walk(child, scope)

    walk(tree, "")
    module_bound = {name for scope, name, _ in found if not scope}
    for scope, name, line in declared:
        if name not in module_bound:
            module_bound.add(name)
            found.append((scope, name, line))
    found.sort(key=lambda item: (item[2], item[0], item[1]))
    return found


def parse_file(path):
    """AST for path. Never imports and never compiles to disk, so no __pycache__.

    utf-8-sig, not utf-8: a BOM is legal in Python source and CPython strips it,
    so decoding it as a literal U+FEFF turned a perfectly good suite into
    'cannot parse input' - an IO code standing in for a verdict the gate could
    have computed. Undecodable bytes still raise UnicodeDecodeError.
    """
    with open(path, encoding="utf-8-sig") as fh:
        return ast.parse(fh.read(), str(path))


def callable_words(path):
    """Normalized word tuples of every callable declared in the module under test.

    Folded through the same key function as the test names, so a respelling
    whose accents decompose cannot miss the join on either side. A source name
    the fold cannot reduce is kept as its shattered fragments rather than
    dropped - the test-name side rejects such a name outright (UNFOLDABLE), so
    keeping it here can only add a match, never hide one.
    """
    names = set()
    for node in ast.walk(parse_file(path)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(tuple(w.lower() for w in WORD.findall(fold(node.name))))
    return names


def lint_file(path, min_words, source_names):
    tests = collect_tests(parse_file(path))
    if not tests:
        return 0, [(path, 1, "NO-TESTS", "file declares no test names")]
    bad, seen = [], set()
    for scope, name, line in tests:
        words = behaviour_words(name)
        where = f"{scope}.{name}" if scope else name
        if (scope, name) in seen:
            bad.append((path, line, "DUPLICATE", f"{where} shadows an earlier test of the same name"))
        seen.add((scope, name))
        strays = unfoldable(name)
        if strays:
            points = " ".join(f"U+{ord(c):04X}" for c in strays)
            bad.append((path, line, "UNFOLDABLE", f"{where} keeps {points} after folding - unreadable, not judged"))
        elif len(words) < min_words:
            bad.append((path, line, "THIN-NAME", f"{where} states {len(words)} word(s), need {min_words}"))
        elif all(w in FILLER or w.isdigit() for w in words):
            bad.append((path, line, "PLACEHOLDER", f"{where} names no behaviour, only filler"))
        elif tuple(words) in source_names:
            bad.append((path, line, "MIRRORS-CODE", f"{where} names the callable, not its behaviour"))
    return len(tests), bad


def warn(message):
    """Diagnostics to stderr, tolerating a closed, missing or narrow fd 2.

    `sys.stderr` is None when the process is started with fd 2 closed, printing
    to a closed one raises OSError, and printing a non-ASCII name to an
    ASCII-encoded one raises UnicodeEncodeError: any of the three, a lost
    diagnostic must not become a crash, because a crash exits 1 - a verdict's
    code.
    """
    try:
        if sys.stderr is not None:
            print(message, file=sys.stderr)
            sys.stderr.flush()
    except (OSError, ValueError):
        pass


def report(checked, files, violations):
    """Print the verdict, or return False if it could not be delivered.

    A verdict nobody can read is not a verdict: a broken stdout raises here and
    a closed fd 1 makes `sys.stdout` None, and either uncaught would exit 1 (or
    120 from the shutdown flush) instead of the IO code. UnicodeEncodeError is
    caught for the same reason: an accented test name printed to a stdout whose
    encoding cannot represent it (PYTHONIOENCODING=ascii) raised a ValueError
    past an OSError-only guard and exited 1 with a half-written verdict. On a write failure sys.stdout is repointed at
    devnull so the flush at interpreter exit cannot overwrite the code we are
    about to return.
    """
    if sys.stdout is None:
        warn("ERROR cannot write verdict - stdout is closed")
        return False
    try:
        for path, line, code, detail in violations:
            print(f"FAIL {path}:{line} {code:<13} {detail}")
        print(f"{checked} test name(s) in {files} file(s), {len(violations)} violation(s)")
        sys.stdout.flush()
        return True
    except (OSError, ValueError) as e:
        sys.stdout = open(os.devnull, "w")
        warn(f"ERROR cannot write verdict - {type(e).__name__}: {e}")
        return False


def main() -> int:
    p = argparse.ArgumentParser(description="Name floor for a unit suite read as documentation.")
    p.add_argument("--min-words", type=int, default=3, help="behaviour words required (default 3)")
    p.add_argument("--against", help="module under test - flags names that mirror a callable")
    p.add_argument("files", nargs="+", help="Python test files to lint")
    args = p.parse_args()
    if args.min_words < 1:
        warn("ERROR --min-words must be >= 1")
        return 2

    try:
        source_names = callable_words(args.against) if args.against else set()
        checked, violations = 0, []
        for path in args.files:
            n, bad = lint_file(path, args.min_words, source_names)
            checked += n
            violations.extend(bad)
    except OSError as e:
        warn(f"ERROR cannot read input - {e}")
        return 2
    except UnicodeDecodeError as e:
        # Subclass of ValueError, so neither arm below catches it: uncaught, the
        # interpreter would exit 1 and an undecodable file would read as a verdict.
        warn(f"ERROR cannot decode input - {e}")
        return 2
    except (SyntaxError, ValueError) as e:
        warn(f"ERROR cannot parse input - {e}")
        return 2
    except (RecursionError, MemoryError) as e:
        # Neither is a ValueError; uncaught, a pathological input would exit 1.
        warn(f"ERROR cannot analyse input - {type(e).__name__}: {e}")
        return 2

    if not report(checked, len(args.files), violations):
        return 2
    return 1 if violations else 0


if __name__ == "__main__":
    # The exit-code contract has to survive the interpreter's own shutdown. CPython
    # flushes the std streams after main() returns, and if that flush raises - a pipe
    # whose reader has gone, the ordinary `| head` idiom - it REPLACES the status with
    # 120, a code no table here names. argparse is the other leak: it raises SystemExit
    # from inside, so a usage error would skip any seal placed after a bare call.
    try:
        _code = main()
    except SystemExit as _exc:                 # argparse usage errors and --help
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
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
