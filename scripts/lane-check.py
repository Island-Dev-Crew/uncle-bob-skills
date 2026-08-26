#!/usr/bin/env python3
"""lane-check.py — assert every shipped skill script stays in its lane.

Usage: python3 scripts/lane-check.py [skills-dir]        (default: skills)
Regression: python3 scripts/fixtures/lane-breaches/check-regressions.py

A user copies a skill folder into their agent's skills directory, so the scripts under
`skills/*/scripts/` run on their machine. This gate turns "they behave" from an observation
into a checked claim. Four lanes, each a refusal:

  L1  no network      — no socket/urllib/http/requests/ftplib/smtplib import, no curl/wget/
                        nc/ssh/scp/telnet invocation, named bare or by absolute path. Shell
                        and Python launchers are read as commands: command-taking wrappers and
                        literal shell `-c` programs are unwrapped, while ordinary arguments
                        named `curl` remain data
  L2  no arbitrary execution — no os.system/os.popen, no exec()/eval() (ast.literal_eval is
                        explicitly allowed: it evaluates literals only), and no call passing a
                        TRUTHY LITERAL `shell=`, since `shell=1` starts the same shell that
                        `shell=True` does. A `shell=` whose value is a variable is not read.
                        Import aliases are resolved first, so `import os as _o` then
                        `_o.system(...)` is the same breach under a different spelling
  L3  no unscoped destruction — an `rm` told to recurse or force must aim EVERY operand at a
                        variable, a scoped relative name, or a path under a temp root, never
                        at a bare non-temporary absolute path, `.`, `..`, or `~`. Flags are
                        read as flags wherever they sit, so `-rf`, `-r -f`,
                        `--recursive --force` and a trailing `-rf` are one rule, and the
                        temp-root prefix is tested on the normalised path so `/tmp/../etc`
                        does not pass as temporary. In Python the same reading is applied to
                        an `rm` handed to a launcher and to shutil.rmtree
  L4  exit codes documented — the file states what its exit codes mean IN ITS HEADER: the
                        leading comment block, plus the module docstring for Python. A caller
                        reads the contract at the top of the file, which is where this lane
                        requires it to be

SCOPE, stated so it is not mistaken for more: this covers the SHIPPED skill scripts, which
are what a user installs. Repo-level tooling under `scripts/` is not shipped as a skill and
carries its own stated trust boundary (see verify-proofs.py, which by design runs commands
out of the repository it checks).

It is a STATIC check. It reads source; it never imports or executes what it reads, so it
cannot be defeated by anything at runtime and equally cannot see a lane crossed through
indirection it has no way to resolve — a getattr(os, "system"), a launcher reached through a
variable, an argv splatted from a dict, a program name built by .format() or "".join(). A
literal is read as a literal wherever the grammar hides one, so an f-string and a `+` of two
constants are both read, but the moment a name's last segment comes from a value this file
cannot see, it stops claiming to know what runs. That limit is real and stated rather than
discovered, and none of these lanes is a sandbox: they are a refusal to SHIP the primitive,
enforced over source text, not a guarantee about a running process.

Three narrower limits, stated for the same reason. L3 reads one logical command line at a time,
trusts a target held in a variable (that IS the sanctioned cleanup idiom), and normalises a
path lexically — a symlink, or a $TMPDIR pointing somewhere else, still lands where this file
cannot look. L3 also assumes GNU's option permutation when flags follow the operand; see
rm_targets. L4 is narrower still: it requires at least one numeric status-to-meaning mapping in
the header, not a bare phrase such as `# exit code`. It does not prove the mapping is complete:
a header naming 0 and 1 over code that also returns 3 still holds L4, and reconciling those two
is a different check than this one.

Exit 0 iff at least one script was scanned and every scanned script holds every lane. Exit 1
on a breach, naming each. Exit 2 on usage or IO error — an error path never borrows the
verdict's code. Exit 3 when zero scripts were scanned: a checker that checked nothing has
verified nothing, and this pack does not report that as a pass.
"""
import ast
import os
import posixpath
import re
import shlex
import sys
from pathlib import Path

NET_MODULES = {"socket", "urllib", "http", "requests", "ftplib", "smtplib", "telnetlib",
               "httplib", "urllib2", "aiohttp", "httpx"}
NET_BINARIES = {"curl", "wget", "nc", "ncat", "netcat", "telnet", "ssh", "scp", "sftp"}
SUBPROCESS_LAUNCHERS = {"subprocess.run", "subprocess.call", "subprocess.check_call",
                        "subprocess.check_output", "subprocess.Popen"}
SUBPROCESS_SHELL_LAUNCHERS = {"subprocess.getoutput", "subprocess.getstatusoutput"}
EXECV_LAUNCHERS = {"os.execv", "os.execve", "os.execvp", "os.execvpe"}
EXECL_LAUNCHERS = {"os.execl", "os.execle", "os.execlp", "os.execlpe"}
SPAWNV_LAUNCHERS = {"os.spawnv", "os.spawnve", "os.spawnvp", "os.spawnvpe"}
SPAWNL_LAUNCHERS = {"os.spawnl", "os.spawnle", "os.spawnlp", "os.spawnlpe"}
ASYNC_EXEC_LAUNCHERS = {"asyncio.create_subprocess_exec"}
ASYNC_SHELL_LAUNCHERS = {"asyncio.create_subprocess_shell"}
SHELL_TEXT_LAUNCHERS = ({"os.system", "os.popen"} | SUBPROCESS_SHELL_LAUNCHERS |
                        ASYNC_SHELL_LAUNCHERS)
LAUNCHERS = (SUBPROCESS_LAUNCHERS | SHELL_TEXT_LAUNCHERS | EXECV_LAUNCHERS |
             EXECL_LAUNCHERS | SPAWNV_LAUNCHERS | SPAWNL_LAUNCHERS |
             ASYNC_EXEC_LAUNCHERS)
SHELL_EXEC = {"os.system", "os.popen"} | ASYNC_SHELL_LAUNCHERS
# The Python spelling of a recursive delete. `os.remove`/`unlink` are deliberately absent: they
# remove one named file and cannot recurse, which is the plain `rm` this lane already permits.
RECURSIVE_DELETE = {"shutil.rmtree"}
# A "$var" target or a temp root is the ordinary trap-cleanup idiom every probe script here
# uses and is not a breach.
TEMP_ROOTS = ("/tmp/", "/private/tmp/", "/var/folders/")
# A meaningful contract binds a numeric status to an explanation. Merely carrying the phrase
# "exit code" says nothing a caller can act on and therefore does not satisfy L4.
EXIT_INLINE = re.compile(
    r"\b(?:(?:exit|exits)\s+with\s+status|exit\s+(?:code|status)|exit|exits)"
    r"\s*:?\s*(?:is\s*)?(?P<code>[0-9]{1,3})\b"
    r"\s*(?:[-—:=|·,;()]\s*)?(?:iff\b|when\b|on\b|always\b|means?\b|[A-Za-z]{2,})",
    re.IGNORECASE,
)
EXIT_HEADING = re.compile(r"\bexit\s+codes?\b", re.IGNORECASE)
EXIT_ROW = re.compile(
    r"^\s*(?:#\s*)?\|?\s*(?P<code>[0-9]{1,3})"
    r"(?:\s*\|\s*|\s*[-—:=]\s*|\s+)(?P<meaning>\S.*)$"
)
EXIT_SAME_LINE = re.compile(
    r"(?:^|[:;—-])\s*(?P<code>[0-9]{1,3})"
    r"(?:\s*\|\s*|\s*[-—:=]\s*|\s+)(?P<meaning>\S+)"
)
EXIT_NEGATION = re.compile(
    r"(?:\bnot|\bnever|\bno|\bcannot|\bcan't|\bdoesn't|\bwon't)\s*$",
    re.IGNORECASE,
)


def basename(word):
    """The program a word names, stripped of the directory it was hiding behind.

    Testing the literal token `curl` reads `/usr/bin/curl` as innocent while the binary is the
    same one. Comparing the basename makes the lane about the program rather than about how
    the caller chose to spell the path to it.
    """
    for sep in ("/", "\\"):
        word = word.rsplit(sep, 1)[-1]
    return word[:-4] if word.lower().endswith(".exe") else word


def import_aliases(tree):
    """Every local name in the file mapped back to the module member it came from.

    `import os as _o` binds the whole os module to a name the old test never looked for, so
    `_o.system("...")` crossed L2 in plain sight. Resolving the bindings first means the lane
    is about what is being called, not about what the caller named it.
    """
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    aliases[a.asname] = a.name
                else:
                    head = a.name.split(".")[0]
                    aliases[head] = head
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for a in node.names:
                aliases[a.asname or a.name] = f"{node.module}.{a.name}"
    return aliases


def dotted_name(func, aliases):
    """The dotted origin of a called name, or None when it cannot be resolved statically."""
    parts = []
    node = func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    parts.reverse()
    return ".".join([aliases.get(parts[0], parts[0])] + parts[1:])


UNRESOLVED = "\x00"  # a character no path or program name holds, standing in for a runtime value


def spelled(word):
    """A word as a breach report should show it, with runtime pieces named as such.

    The placeholder is a NUL because no filename holds one; printing it raw would put `\\x00` in
    a report a human has to act on, so it is shown as the hole it stands for.
    """
    return word.replace(UNRESOLVED, "{...}")


def literal_text(node):
    """The text a string expression is known to hold, or None when it holds no known text.

    `f"/usr/bin/curl"` is a literal to every reader and to the interpreter, but it parses to
    ast.JoinedStr rather than ast.Constant, so a test that accepted only Constant read it as
    unknowable — one character away from the fixture it was written to catch. The pieces of an
    f-string or a `+` concatenation that ARE known are joined, and each piece that is not is
    replaced by a character no path contains. That keeps `f"{bindir}/curl"` readable as a curl
    invocation while `f"cur{tail}"` stays honestly unresolvable.
    """
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return node.value
        if isinstance(node.value, bytes):
            # `subprocess.run([b"/usr/bin/curl", ...])` executes exactly as the str spelling does —
            # the exec family takes bytes paths — so reading only str let a one-character prefix
            # walk past every Python lane. Decoded permissively: a byte sequence that is not text
            # is not a program name worth reading, and `errors="replace"` turns it into one that
            # matches nothing rather than raising inside a checker.
            return node.value.decode("utf-8", errors="replace")
        return None
    if isinstance(node, ast.JoinedStr):
        pieces = [literal_text(value) for value in node.values]
        return "".join(UNRESOLVED if piece is None else piece for piece in pieces)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = literal_text(node.left), literal_text(node.right)
        if left is None and right is None:
            return None
        return (UNRESOLVED if left is None else left) + (UNRESOLVED if right is None else right)
    return None


def literal_sequence(node):
    """A literal argv sequence without flattening individual arguments into commands.

    Flattening `["echo", "curl"]` to words and scanning every word calls data a network
    invocation. Keeping argv boundaries lets the command parser inspect only executable
    positions, while still retaining known pieces of a concatenated literal list.
    """
    if isinstance(node, (ast.List, ast.Tuple)):
        values = []
        for element in node.elts:
            if isinstance(element, ast.Starred):
                expanded = literal_sequence(element.value)
                values.extend(expanded or [UNRESOLVED])
                continue
            value = literal_text(element)
            values.append(UNRESOLVED if value is None else value)
        return values
    value = literal_text(node)
    if value is not None:
        return [value]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return literal_sequence(node.left) + literal_sequence(node.right)
    return []


def literal_call_arguments(arguments):
    """Literal positional arguments, expanding a statically visible starred sequence."""
    values = []
    for argument in arguments:
        if isinstance(argument, ast.Starred):
            expanded = literal_sequence(argument.value)
            values.extend(expanded or [UNRESOLVED])
        else:
            values.append(literal_text(argument) or UNRESOLVED)
    return values


def expanded_call_nodes(arguments):
    """Positional AST expressions after expanding a literal call-level `*sequence`."""
    expanded = []
    for argument in arguments:
        if isinstance(argument, ast.Starred) and isinstance(argument.value, (ast.List, ast.Tuple)):
            expanded.extend(expanded_call_nodes(argument.value.elts))
        else:
            expanded.append(argument)
    return expanded


def literal_truth(node):
    """The truth of a literal expression, or None when runtime evaluation is required."""
    if node is None:
        return None
    try:
        return bool(ast.literal_eval(node))
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        text = literal_text(node)
        if text is None:
            return None
        if UNRESOLVED in text:
            return True if text.replace(UNRESOLVED, "") else None
        return bool(text)


def keyword_value(call, name):
    """Return one explicitly named keyword expression, if present."""
    return next((kw.value for kw in call.keywords or [] if kw.arg == name), None)


def unscoped(target):
    """True when a literal deletion target can denote a broad working root.

    Absolute non-temporary paths retain the original refusal. Lexical normalisation also catches
    `/tmp/../etc`, `.`, `foo/..`, and parent-relative paths. A literal tilde denotes a home tree.
    Runtime values remain outside this static gate's claim, matching the documented variable
    cleanup allowance.
    """
    if not target or target.startswith("$") or target.startswith(UNRESOLVED):
        return False
    normal = posixpath.normpath(target)
    if normal in (".", "..") or normal.startswith("../"):
        return True
    if target == "~" or target.startswith("~/") or re.match(r"^~[^/]+(?:/|$)", target):
        return True
    return target.startswith("/") and not normal.startswith(TEMP_ROOTS)


CONTROL_CHARS = set(";&|()\n")
SHELL_RESERVED = {"!", "{", "}", "if", "then", "elif", "else", "fi", "while", "until",
                  "do", "done", "for", "select", "case", "esac", "in"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SHELLS = {"bash", "sh", "dash", "zsh", "ksh"}
ARRAY_ASSIGNMENT = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)\+?=\s*\(")


def normalize_ansi_c_quotes(text):
    """Turn simple Bash ``$'literal'`` words into ordinary quoted literals.

    Python's shlex preserves the leading dollar as part of the token, so ``$'curl'`` becomes
    ``$curl`` and looks like a runtime variable.  With no escape sequences, however, the word
    is fully literal; rewriting only that form keeps dynamic ``$curl`` unknown while exposing
    the command Bash will actually execute.
    """
    out = []
    i = 0
    while i < len(text):
        if not text.startswith("$'", i):
            out.append(text[i])
            i += 1
            continue
        end = i + 2
        while end < len(text) and text[end] != "'" and text[end] != "\\":
            end += 1
        if end < len(text) and text[end] == "'":
            out.append(shlex.quote(text[i + 2:end]))
            i = end + 1
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def matching_paren(text, opening):
    """Index of the shell parenthesis balancing `opening`, or None."""
    depth = 0
    quote = None
    i = opening
    while i < len(text):
        char = text[i]
        if char == "\\" and quote != "'":
            i += 2
            continue
        if quote:
            if char == quote:
                quote = None
            i += 1
            continue
        if char in "'\"`":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def matching_backtick(text, opening):
    """Index of the unescaped backtick closing `opening`, or None."""
    i = opening + 1
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "`":
            return i
        i += 1
    return None


def mask_shell_expansions(text):
    """Mask executable expansions in outer argv and return their command programs.

    Command and process substitutions execute even when they are arguments to `echo`; arithmetic
    expansions do not. Masking both forms keeps shlex from promoting their contents to outer
    command positions, while the returned command programs are recursively checked on their own.
    """
    out = []
    programs = []
    quote = None
    i = 0
    while i < len(text):
        char = text[i]
        if char == "\\" and quote != "'" and i + 1 < len(text):
            out.append(text[i:i + 2])
            i += 2
            continue
        if char == "'":
            if quote is None:
                quote = "'"
            elif quote == "'":
                quote = None
            out.append(char)
            i += 1
            continue
        if char == '"':
            if quote is None:
                quote = '"'
            elif quote == '"':
                quote = None
            out.append(char)
            i += 1
            continue
        if quote != "'" and text.startswith("$((", i):
            end = matching_paren(text, i + 1)
            if end is not None:
                _masked, nested = mask_shell_expansions(text[i + 3:end - 1])
                programs.extend(nested)
                out.append("__lane_arithmetic__")
                i = end + 1
                continue
        if quote != "'" and text.startswith("$(", i):
            end = matching_paren(text, i + 1)
            if end is not None:
                programs.append(text[i + 2:end])
                out.append("__lane_substitution__")
                i = end + 1
                continue
        if quote is None and (text.startswith("<(", i) or text.startswith(">(", i)):
            end = matching_paren(text, i + 1)
            if end is not None:
                programs.append(text[i + 2:end])
                out.append("__lane_process_substitution__")
                i = end + 1
                continue
        if quote != "'" and char == "`":
            end = matching_backtick(text, i)
            if end is not None:
                # Inside an old-style backtick program, an escaped backtick opens/closes a
                # nested substitution after the outer shell removes that escape.
                programs.append(text[i + 1:end].replace("\\`", "`"))
                out.append("__lane_backtick__")
                i = end + 1
                continue
        if quote is None and text.startswith("((", i):
            end = matching_paren(text, i)
            if end is not None:
                _masked, nested = mask_shell_expansions(text[i + 2:end - 1])
                programs.extend(nested)
                out.append("__lane_arithmetic__")
                i = end + 1
                continue
        out.append(char)
        i += 1
    return "".join(out), programs


def mask_array_assignments(text):
    """Replace literal shell array bodies, whose words are data until expanded later."""
    out = []
    i = 0
    while True:
        match = ARRAY_ASSIGNMENT.search(text, i)
        if match is None:
            out.append(text[i:])
            break
        opening = match.end() - 1
        end = matching_paren(text, opening)
        if end is None:
            out.append(text[i:])
            break
        out.append(text[i:match.start()])
        out.append(f"{match.group(1)}=__lane_array__")
        i = end + 1
    return "".join(out)


def shell_commands(text):
    """Split literal shell text into argv-shaped commands without executing it.

    shlex preserves quoted strings as one argument, which is the key distinction between
    `echo "rm -rf ."` and `rm -rf .`. Control operators start a new command; redirection targets
    are discarded so they cannot become deletion operands.
    """
    lexer = shlex.shlex(normalize_ansi_c_quotes(text), posix=True,
                        punctuation_chars=";&|()<>\n")
    # An unquoted newline terminates a command just like `;`. Keep it as punctuation so an
    # inner multi-line `bash -c` program does not collapse into one argv vector. shlex still
    # preserves a newline inside quotes as part of that quoted argument.
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    commands = []
    current = []
    skip_redirection_target = False
    loop_header = False
    function_header = False
    case_state = None

    def finish():
        if current:
            commands.append(current[:])
            current.clear()

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if case_state == "header":
            if token == "in":
                case_state = "pattern"
            i += 1
            continue
        if case_state == "pattern":
            if token == "esac":
                case_state = None
            elif token and all(ch in CONTROL_CHARS for ch in token) and ")" in token:
                case_state = "body"
            i += 1
            continue
        if case_state == "body":
            if token == "esac":
                finish()
                case_state = None
                i += 1
                continue
            if token in (";;", ";&", ";;&"):
                finish()
                case_state = "pattern"
                i += 1
                continue
        if loop_header:
            if token == "do":
                loop_header = False
            i += 1
            continue
        if function_header:
            if token == "{":
                function_header = False
            i += 1
            continue
        if token == "case":
            finish()
            case_state = "header"
            i += 1
            continue
        if token in ("for", "select"):
            finish()
            loop_header = True
            i += 1
            continue
        if token == "function":
            finish()
            function_header = True
            i += 1
            continue
        if (token == "()" and len(current) == 1 and i + 1 < len(tokens) and
                tokens[i + 1] == "{"):
            current.clear()
            i += 1
            continue
        if token and all(ch in CONTROL_CHARS or ch in "<>" for ch in token):
            if "<" in token or ">" in token:
                if current and current[-1].isdigit():
                    current.pop()
                skip_redirection_target = True
            if any(ch in CONTROL_CHARS for ch in token):
                finish()
            i += 1
            continue
        if skip_redirection_target:
            skip_redirection_target = False
            i += 1
            continue
        if token in SHELL_RESERVED:
            finish()
            i += 1
            continue
        current.append(token)
        i += 1
    finish()
    return commands


def after_options(argv, start, takes_value=()):
    """Index of the first non-option, accounting for options with separate values."""
    takes = set(takes_value)
    i = start
    while i < len(argv):
        token = argv[i]
        if token == "--":
            return i + 1
        if not token.startswith("-") or token == "-":
            return i
        name = token.split("=", 1)[0]
        i += 2 if "=" not in token and name in takes else 1
    return i


def env_command(argv):
    """The command executed by env, including GNU env's split-string form."""
    tokens = list(argv[1:])
    i = expansions = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "--":
            i += 1
            break
        split_value = None
        if token in ("-S", "--split-string"):
            if i + 1 >= len(tokens):
                return []
            split_value = tokens[i + 1]
            consumed = 2
        elif token.startswith("--split-string="):
            split_value = token.split("=", 1)[1]
            consumed = 1
        elif token.startswith("-S") and token != "-S":
            split_value = token[2:]
            consumed = 1
        if split_value is not None:
            try:
                split = shlex.split(split_value, posix=True)
            except ValueError:
                return []
            expansions += 1
            if expansions > 64:
                return []
            tokens[i:i + consumed] = split
            continue
        if not token.startswith("-") or token == "-":
            break
        name = token.split("=", 1)[0]
        i += (2 if "=" not in token and name in {
            "-u", "--unset", "-C", "--chdir"
        } else 1)
    while i < len(tokens) and ASSIGNMENT.match(tokens[i]):
        i += 1
    return tokens[i:]


def wrapped_argv(argv):
    """The command argv consumed by a known command-taking wrapper, else None."""
    program = basename(argv[0])
    if program == "nohup":
        return argv[after_options(argv, 1):]
    if program == "exec":
        return argv[after_options(argv, 1, {"-a"}):]
    if program == "command":
        i = 1
        while i < len(argv):
            option = argv[i]
            if option == "--":
                i += 1
                break
            if not option.startswith("-") or option == "-":
                break
            if "v" in option[1:] or "V" in option[1:]:
                return []
            i += 1
        return argv[i:]
    if program == "env":
        return env_command(argv)
    if program == "sudo":
        i = after_options(argv, 1, {"-C", "-D", "-g", "-h", "-p", "-R", "-r", "-t", "-T",
                                    "-u", "--chdir", "--close-from", "--group", "--host",
                                    "--prompt", "--role", "--type", "--user"})
        while i < len(argv) and ASSIGNMENT.match(argv[i]):
            i += 1
        return argv[i:]
    if program == "nice":
        return argv[after_options(argv, 1, {"-n", "--adjustment"}):]
    if program == "timeout":
        i = after_options(argv, 1, {"-k", "--kill-after", "-s", "--signal"})
        return argv[i + 1:] if i < len(argv) else []
    if program == "stdbuf":
        return argv[after_options(argv, 1, {"-i", "--input", "-o", "--output", "-e", "--error"}):]
    if program == "time":
        return argv[after_options(argv, 1, {"-f", "--format", "-o", "--output"}):]
    if program == "xargs":
        return argv[after_options(argv, 1, {"-a", "--arg-file", "-d", "--delimiter", "-E",
                                    "--eof", "-I", "--replace", "-L", "--max-lines", "-n",
                                    "--max-args", "-P", "--max-procs", "-s", "--max-chars"}):]
    return None


def leaf_commands(argv):
    """Commands that an argv vector directly executes after wrappers and literal shell -c."""
    argv = [word for word in argv if word]
    while argv and ASSIGNMENT.match(argv[0]):
        argv = argv[1:]
    if not argv or argv[0] == UNRESOLVED:
        return []
    wrapped = wrapped_argv(argv)
    if wrapped is not None:
        return leaf_commands(wrapped)
    if basename(argv[0]) in SHELLS:
        i = 1
        while i < len(argv):
            option = argv[i]
            if option == "--" or not option.startswith("-") or option == "-":
                return [argv]
            if not option.startswith("--") and "c" in option[1:]:
                if i + 1 >= len(argv):
                    return []
                leaves = []
                for command in shell_commands(argv[i + 1]):
                    leaves.extend(leaf_commands(command))
                return leaves
            i += 2 if option in ("-O", "+O", "--rcfile", "--init-file") else 1
    return [argv]


def rm_targets_argv(argv):
    """Unscoped operands of an actual recursive/forced rm command."""
    if not argv or basename(argv[0]) != "rm":
        return []
    destructive = False
    operands = []
    options_ended = False
    for token in argv[1:]:
        if options_ended or not token.startswith("-") or token == "-":
            operands.append(token)
        elif token == "--":
            options_ended = True
        elif token.startswith("--"):
            name = token[2:].split("=", 1)[0]
            if name and ("recursive".startswith(name) or "force".startswith(name)):
                destructive = True
        else:
            destructive = destructive or any(char in "rRf" for char in token[1:])
    return [target for target in operands if destructive and unscoped(target)]


def command_hazards(argv):
    """Literal network invocations and unscoped deletes reached by one argv."""
    hazards = []
    for leaf in leaf_commands(argv):
        if basename(leaf[0]) in NET_BINARIES:
            hazards.append(("L1", leaf[0]))
        hazards.extend(("L3", target) for target in rm_targets_argv(leaf))
    return hazards


def shell_hazards(text):
    """Hazards in each executable command of literal shell text."""
    hazards = []
    masked, programs = mask_shell_expansions(text)
    for program in programs:
        hazards.extend(shell_hazards(program))
    masked = mask_array_assignments(masked)
    for command in shell_commands(masked):
        hazards.extend(command_hazards(command))
    return hazards


def python_launcher_hazards(called, call):
    """Hazards reached through one supported Python process-launch API."""
    if called in SUBPROCESS_LAUNCHERS:
        positional = expanded_call_nodes(call.args)
        command = keyword_value(call, "args") or (positional[0] if positional else None)
        if command is None:
            return []
        argv = literal_sequence(command)
        executable = literal_text(keyword_value(call, "executable"))
        shell_kw = keyword_value(call, "shell")
        if literal_truth(shell_kw):
            text = literal_text(command)
            hazards = [] if text is None else shell_hazards(text)
            if executable is not None:
                hazards.extend(command_hazards([executable]))
            return hazards
        if executable is not None:
            argv = [executable] + argv[1:] if argv else [executable]
        return command_hazards(argv)
    if called in SHELL_TEXT_LAUNCHERS:
        command = call.args[0] if call.args else keyword_value(call, "cmd")
        text = literal_text(command) if command is not None else None
        hazards = [] if text is None else shell_hazards(text)
        executable = literal_text(keyword_value(call, "executable"))
        if executable is not None:
            hazards.extend(command_hazards([executable]))
        return hazards
    if called in ASYNC_EXEC_LAUNCHERS:
        argv = literal_call_arguments(expanded_call_nodes(call.args))
        executable = literal_text(keyword_value(call, "executable"))
        if executable is not None:
            argv = [executable] + argv[1:] if argv else [executable]
        return command_hazards(argv)
    if called in EXECV_LAUNCHERS and len(call.args) >= 2:
        program = literal_text(call.args[0])
        args = literal_sequence(call.args[1])
        return [] if program is None else command_hazards([program] + args[1:])
    if called in EXECL_LAUNCHERS:
        args = literal_call_arguments(call.args)
        if len(args) < 2:
            return []
        tail = args[2:-1] if called.endswith("e") else args[2:]
        return [] if args[0] == UNRESOLVED else command_hazards([args[0]] + tail)
    if called in SPAWNV_LAUNCHERS and len(call.args) >= 3:
        program = literal_text(call.args[1])
        args = literal_sequence(call.args[2])
        return [] if program is None else command_hazards([program] + args[1:])
    if called in SPAWNL_LAUNCHERS:
        args = literal_call_arguments(call.args)
        if len(args) < 3:
            return []
        tail = args[3:-1] if called.endswith("e") else args[3:]
        return [] if args[1] == UNRESOLVED else command_hazards([args[1]] + tail)
    return []


def check_python(path, src):
    """Lane breaches in one Python file, found through the parse tree rather than by grep."""
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [f"L0 unparseable: {exc}"]
    aliases = import_aliases(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in NET_MODULES:
                    out.append(f"L1 network import '{a.name}' (line {node.lineno})")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in NET_MODULES:
                out.append(f"L1 network import from '{node.module}' (line {node.lineno})")
        elif isinstance(node, ast.Call):
            called = dotted_name(node.func, aliases)
            if called in LAUNCHERS:
                for lane, value in python_launcher_hazards(called, node):
                    if lane == "L1":
                        out.append(f"L1 network invocation {spelled(value)!r} via {called} "
                                   f"(line {node.lineno})")
                    else:
                        out.append(f"L3 recursive/forced rm on unscoped target "
                                   f"{spelled(value)!r} via {called} (line {node.lineno})")
            if called in RECURSIVE_DELETE:
                target_node = node.args[0] if node.args else keyword_value(node, "path")
                target = literal_text(target_node) if target_node is not None else None
                if target is not None and unscoped(target):
                    out.append(f"L3 {called} on unscoped target {spelled(target)!r} "
                               f"(line {node.lineno})")
            if called in SHELL_EXEC:
                out.append(f"L2 {called} (line {node.lineno})")
            if called in ("exec", "eval", "builtins.exec", "builtins.eval"):
                out.append(f"L2 {called}() (line {node.lineno})")
            for kw in node.keywords or []:
                # subprocess tests shell values for truth rather than identity with True. Lists,
                # tuples, mappings, sets, unary numbers, bytes and static f-strings therefore
                # receive the same literal truth test as scalars.
                if kw.arg == "shell" and literal_truth(kw.value):
                    out.append(f"L2 shell={ast.unparse(kw.value)} (line {node.lineno})")
    return out


def strip_shell_comment(line):
    """Drop a trailing shell comment without cutting a hash that lives inside a quote.

    Cutting at the first hash reads like comment-stripping and is not: a quoted hash — a colour
    literal, a `sed` script, a regex — truncated the line, and everything after it went
    unscanned. Nothing in this pack hides a breach behind one today (measured: fifteen lines
    carry a quoted hash, none with a lane primitive after it), but a scanner that silently reads
    less than it claims is the false green this tool exists to prevent, and the same defect was
    just found in verify-proofs.py, where it truncated a command that was then executed.
    """
    out = []
    quote = None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (not out or out[-1].isspace()):
            break
        else:
            out.append(ch)
    return "".join(out)


def line_continues(line):
    """True when the physical line ends in an active backslash-newline."""
    trailing = len(line) - len(line.rstrip("\\"))
    if trailing % 2 == 0:
        return False
    quote = None
    i = 0
    while i < len(line) - 1:
        char = line[i]
        if char == "\\" and quote != "'":
            i += 2
            continue
        if char in "'\"":
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        i += 1
    return quote != "'"


def has_open_shell_quote(text):
    """Whether a logical shell command continues inside a single or double quote."""
    quote = None
    i = 0
    while i < len(text):
        char = text[i]
        if char == "\\" and quote != "'":
            i += 2
            continue
        if char in "'\"":
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        i += 1
    return quote is not None


def heredoc_markers(line):
    """Literal here-document delimiters declared by one command line."""
    lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|()<>")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    markers = []
    i = 0
    while i < len(tokens):
        if tokens[i] != "<<":
            i += 1
            continue
        i += 1
        if i >= len(tokens):
            break
        strip_tabs = False
        delimiter = tokens[i]
        if delimiter == "-" and i + 1 < len(tokens):
            strip_tabs = True
            i += 1
            delimiter = tokens[i]
        elif delimiter.startswith("-"):
            strip_tabs = True
            delimiter = delimiter[1:]
        if delimiter:
            markers.append((delimiter, strip_tabs))
        i += 1
    return markers


def shell_source_lines(src):
    """Logical command lines, excluding here-document bodies that are input data."""
    pending_heredocs = []
    buffered = ""
    start_line = 1
    for number, physical in enumerate(src.splitlines(), 1):
        if pending_heredocs:
            delimiter, strip_tabs = pending_heredocs[0]
            candidate = physical.lstrip("\t") if strip_tabs else physical
            if candidate == delimiter:
                pending_heredocs.pop(0)
            continue
        if not buffered:
            start_line = number
        candidate = buffered + physical
        # Strip comments before asking whether a quote remains open. Apostrophes in prose such
        # as "user's home" are not shell quotes; a hash inside an already-open quoted program
        # remains intact because strip_shell_comment sees that quote state in `buffered`.
        bare_candidate = (candidate[2:] if start_line == 1 and candidate.startswith("#!")
                          else strip_shell_comment(candidate))
        if line_continues(bare_candidate):
            buffered = bare_candidate[:-1]
            continue
        if has_open_shell_quote(bare_candidate):
            buffered = bare_candidate + "\n"
            continue
        logical = bare_candidate
        buffered = ""
        # A shebang is executable metadata, not an ordinary shell comment: the kernel invokes
        # the interpreter it names.  Reading it as argv catches env -S launching a network tool.
        bare = logical
        pending_heredocs.extend(heredoc_markers(bare))
        yield start_line, bare
    if buffered:
        yield start_line, strip_shell_comment(buffered)


COMPOUND_OPENERS = {
    "case": "esac",
    "for": "done",
    "select": "done",
    "while": "done",
    "until": "done",
    "if": "fi",
    "{": "}",
}


def shell_tokens(line):
    """Best-effort shell tokens used only to group multi-line compound syntax."""
    lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|()<>")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return []


def starts_compound(tokens):
    """Whether this line opens syntax whose inert header continues on later lines."""
    if not tokens:
        return False
    if tokens[0] in COMPOUND_OPENERS or tokens[0] == "function":
        return True
    return len(tokens) >= 3 and tokens[1] == "()" and tokens[2] == "{"


def compound_balance(tokens):
    """Net opener/closer counts for supported shell compound statements."""
    counts = {closer: 0 for closer in set(COMPOUND_OPENERS.values())}
    for token in tokens:
        if token in COMPOUND_OPENERS:
            counts[COMPOUND_OPENERS[token]] += 1
        if token in counts:
            counts[token] -= 1
    return counts


def shell_statement_groups(src):
    """Logical lines, joining compound headers so patterns/lists remain inert data."""
    buffered = []
    start = 1
    balances = {}
    for number, line in shell_source_lines(src):
        tokens = shell_tokens(line)
        if not buffered and not starts_compound(tokens):
            yield number, line
            continue
        if not buffered:
            start = number
            balances = {}
        buffered.append(line)
        for closer, delta in compound_balance(tokens).items():
            balances[closer] = balances.get(closer, 0) + delta
        if any(value > 0 for value in balances.values()):
            continue
        yield start, " ; ".join(buffered)
        buffered = []
        balances = {}
    if buffered:
        yield start, " ; ".join(buffered)


def rm_targets(line):
    """Every unscoped target an actual `rm` command was told to recurse over or force.

    The old test was a single regex that required the flags to be spelled `-rf` and to sit
    immediately before the target, so `rm --recursive --force /etc/x` — the same command, GNU's
    own long spelling — walked straight past it, as did `rm -r -f /etc/x`. Reading the flags as
    flags makes the spelling stop mattering. A long option is matched by prefix because GNU
    accepts any unambiguous abbreviation (`--rec`, `--f`).

    Flags and operands are then separated in full before any verdict, because reading only the
    first operand left `rm -rf /tmp/scratch /etc/x` looking scoped while it deleted /etc/x, and
    deciding at the operand left `rm /etc/x -rf` looking harmless because the flags had not been
    read yet. Both are one `rm` deleting one bare absolute path.

    The trailing-flag form is GNU's: glibc permutes options past operands, so `rm /etc/x -rf`
    recurses there. BSD and macOS `rm` stop option parsing at the first operand and would treat
    `-rf` as another file to delete, so on those systems this line is not the command the lane
    names. It is reported anyway — a lane that reads a command differently depending on which
    machine later runs it is not a lane.
    """
    return [value for lane, value in shell_hazards(line) if lane == "L3"]


def check_shell(path, src):
    out = []
    for i, bare in shell_statement_groups(src):
        for lane, value in shell_hazards(bare):
            if lane == "L1":
                out.append(f"L1 network invocation {spelled(value)!r} (line {i})")
            else:
                # Not "rm -rf": the flags may be split, long, or trailed, and a report should
                # not put words in the line's mouth.
                out.append(f"L3 recursive/forced rm on unscoped target "
                           f"{spelled(value)!r} (line {i})")
    return out


def header_text(path, src):
    """The region an exit contract has to live in to count.

    Accepting the word "exit" anywhere in the source let `print("... exit 0 ...")` in the body
    stand in for a contract, so a file documenting nothing held L4 on a string it happened to
    print. A caller looks for the contract at the top of the file; that is where the lane now
    requires it.
    """
    lines = []
    for line in src.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            break
        lines.append(stripped)
    if path.suffix == ".py":
        try:
            doc = ast.get_docstring(ast.parse(src))
        except SyntaxError:
            doc = None
        if doc:
            lines.append(doc)
    return "\n".join(lines)


def has_exit_contract(header):
    """Whether a header maps at least one numeric exit status to a meaning."""
    lines = [re.sub(r"^\s*#\s?", "", line) for line in header.splitlines()]
    for line in lines:
        for match in EXIT_INLINE.finditer(line):
            if int(match.group("code")) <= 255 and not EXIT_NEGATION.search(line[:match.start()]):
                return True
    for index, line in enumerate(lines):
        heading = EXIT_HEADING.search(line)
        if heading is None:
            continue
        tail = line[heading.end():]
        same_line = EXIT_SAME_LINE.search(tail)
        if same_line is not None and int(same_line.group("code")) <= 255:
            return True
        for candidate in lines[index + 1:index + 9]:
            row = EXIT_ROW.match(candidate)
            if row is not None and int(row.group("code")) <= 255:
                return True
    return False


def main() -> int:
    argv = sys.argv[1:]
    # A surplus operand used to be dropped in silence, so `lane-check.py skills scripts/fixtures`
    # scanned the first path and printed a pass the second path never earned.
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(argv[0] if argv else "skills")
    if not root.is_dir():
        print(f"lane-check: not a directory: {root}", file=sys.stderr)
        return 2
    scanned = breaches = 0
    # Recursive under the declared root: a script one directory deeper than the layout this
    # pack happens to use is still a script the user installs.
    for path in sorted(root.glob("*/scripts/**/*")):
        # `fixtures` is skipped only where it sits BELOW the root the caller named. Testing the
        # whole path excluded any tree with "fixtures" anywhere above it, which is how this gate
        # scanned zero files and reported green over its own red test.
        if path.suffix not in (".py", ".sh") or not path.is_file():
            continue
        if "fixtures" in path.relative_to(root).parts:
            continue
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"lane-check: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        scanned += 1
        found = check_python(path, src) if path.suffix == ".py" else check_shell(path, src)
        if not has_exit_contract(header_text(path, src)):
            found.append("L4 exit codes not documented in the file header")
        for f in found:
            breaches += 1
            print(f"BREACH {path}: {f}")
    print(f"\n{scanned} shipped skill scripts scanned, {breaches} lane breach(es)")
    if breaches:
        return 1
    if scanned == 0:
        print(f"NOTHING SCANNED - no shipped skill scripts under {root}; this is not a pass",
              file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except BaseException as exc:
        print(f"lane-check: internal failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        code = 2
    for stream, fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if stream is not None:
                stream.flush()
        except BaseException:
            if code in (0, 1):
                code = 2
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), fd)
            except BaseException:
                pass
    sys.exit(code)
