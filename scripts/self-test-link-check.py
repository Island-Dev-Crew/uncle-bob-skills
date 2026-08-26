#!/usr/bin/env python3
"""Watched-red integration tests for scripts/link-check.py.

The checker reads committed bytes, so every case is built as a tiny real Git
repository.  Exit 0 means all cases produced the expected gate verdict; exit 1
means at least one regression; exit 2 means the self-test itself could not run.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


CHECKER = Path(__file__).with_name("link-check.py").resolve()
SELF = Path(__file__).resolve()
ROOT = CHECKER.parent.parent
INNER_ARG = "--internal-subset"
GIT_ENV = {
    **{name: value for name, value in os.environ.items() if not name.startswith("GIT_")},
    "GIT_AUTHOR_NAME": "link-check self-test",
    "GIT_AUTHOR_EMAIL": "self-test@example.invalid",
    "GIT_COMMITTER_NAME": "link-check self-test",
    "GIT_COMMITTER_EMAIL": "self-test@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONIOENCODING": "utf-8",
}


class TestFailure(RuntimeError):
    pass


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=GIT_ENV, text=True, capture_output=True)


def make_repo(root: Path, markdown: str, targets: tuple[str, ...] = ()) -> None:
    git_prefix = ["git", "-c", f"core.hooksPath={os.devnull}"]
    result = run([*git_prefix, "init", "-q"], root)
    if result.returncode:
        raise TestFailure(f"git init failed: {result.stderr.strip()}")
    (root / "README.md").write_text(markdown, encoding="utf-8")
    for target in targets:
        path = root / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    for args in (
        [*git_prefix, "add", "."],
        [*git_prefix, "commit", "--no-gpg-sign", "--no-verify", "-qm", "fixture"],
    ):
        result = run(list(args), root)
        if result.returncode:
            raise TestFailure(f"{' '.join(args)} failed: {result.stderr.strip()}")


def expect_case(
    parent: Path,
    name: str,
    markdown: str,
    expected: int,
    targets: tuple[str, ...] = (),
    needle: str | None = None,
) -> None:
    root = parent / name
    root.mkdir()
    make_repo(root, markdown, targets)
    result = run([sys.executable, str(CHECKER)], root)
    output = result.stdout + result.stderr
    if result.returncode != expected:
        raise TestFailure(
            f"{name}: expected exit {expected}, got {result.returncode}\n{output}"
        )
    if needle is not None and needle not in output:
        raise TestFailure(f"{name}: missing {needle!r}\n{output}")
    print(f"OK   {name} exit={expected}")


def run_with_closed_stream(args: list[str], stream: str) -> int:
    """Run a child with one output descriptor already pointing at a dead pipe."""
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    kwargs = {
        "cwd": ROOT,
        "env": GIT_ENV,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    kwargs[stream] = write_fd
    try:
        return subprocess.run(args, check=False, **kwargs).returncode
    finally:
        os.close(write_fd)


def main(argv: list[str]) -> int:
    if argv not in ([], [INNER_ARG]):
        print(f"usage: self-test-link-check.py [{INNER_ARG}]", file=sys.stderr)
        return 2
    internal_subset = argv == [INNER_ARG]
    with tempfile.TemporaryDirectory(prefix="link-check-self-test-") as tmp:
        parent = Path(tmp)
        cases = (
            ("plain-dead", "[plain](missing.md)\n", 1, (), "DEAD README.md -> missing.md"),
            (
                "nested-label-dead",
                "[link [foo [bar]]](missing.md)\n",
                1,
                (),
                "DEAD README.md -> missing.md",
            ),
            (
                "escaped-label-dead",
                "[link \\] ok](missing.md)\n",
                1,
                (),
                "DEAD README.md -> missing.md",
            ),
            (
                "balanced-destination-dead",
                "[balanced](missing(1).md)\n",
                1,
                (),
                "DEAD README.md -> missing(1).md",
            ),
            (
                "reference-forms-dead",
                "[full][deep-label] [collapsed][] [shortcut]\n\n"
                "[deep-label]: missing-full.md\n"
                "[collapsed]: missing-collapsed.md\n"
                "[shortcut]: missing-shortcut.md\n",
                1,
                (),
                "3 dead",
            ),
            (
                "complex-green",
                "[nested [label]](docs/target(1).md \"title\")\n"
                "[escaped \\] label](docs/escaped.md)\n"
                "[reference][deep-label]\n"
                "[deep-label]: docs/reference.md \"title\"\n",
                0,
                ("docs/target(1).md", "docs/escaped.md", "docs/reference.md"),
                "0 dead",
            ),
            (
                "nested-inner-dead",
                "[outer [inner](missing.md)](present.md)\n",
                1,
                ("present.md",),
                "DEAD README.md -> missing.md",
            ),
            (
                "image-inside-link-dead",
                "[![alt](missing.png)](present.md)\n",
                1,
                ("present.md",),
                "DEAD README.md -> missing.png",
            ),
            (
                "code-span-label-dead",
                "[foo `]` bar](missing.md)\n\n[control](present.md)\n",
                1,
                ("present.md",),
                "DEAD README.md -> missing.md",
            ),
            (
                "raw-html-label-dead",
                "[foo <span title=\"]\">bar</span>](missing.md)\n\n"
                "[control](present.md)\n",
                1,
                ("present.md",),
                "DEAD README.md -> missing.md",
            ),
            (
                "multiline-label-dead",
                "[foo\nbar](missing.md)\n\n[control](present.md)\n",
                1,
                ("present.md",),
                "DEAD README.md -> missing.md",
            ),
            (
                "srcset-comma-filename-green",
                '<img srcset="assets/asset,one.png 1x">\n',
                0,
                ("assets/asset,one.png",),
                "1 relative targets checked at HEAD (0 links, 1 images), 0 dead",
            ),
            (
                "srcset-comma-filename-dead",
                '<img srcset="assets/missing,one.png 1x">\n',
                1,
                (),
                "DEAD README.md -> assets/missing,one.png",
            ),
            (
                "srcset-data-url-green",
                '<img srcset="data:image/svg+xml,%3Csvg%3E 1x, assets/present.webp 2x">\n',
                0,
                ("assets/present.webp",),
                "1 relative targets checked at HEAD (0 links, 1 images), 0 dead",
            ),
            (
                "srcset-multiple-candidates-dead",
                '<source srcset="assets/present.webp 1x, assets/missing.webp 2x">\n',
                1,
                ("assets/present.webp",),
                "DEAD README.md -> assets/missing.webp",
            ),
            (
                "srcset-malformed-fails-closed",
                '<img srcset="assets/present.webp 1q">\n',
                1,
                ("assets/present.webp",),
                "MALFORMED README.md -> srcset: assets/present.webp 1q",
            ),
            (
                "raw-html-asset-dead",
                "<picture><source srcset=\"missing-small.webp 1x, present.webp 2x\">"
                "<img src=\"missing.webp\"></picture>\n"
                "[control](present.md)\n",
                1,
                ("present.md", "present.webp"),
                "2 dead",
            ),
        )
        for case in cases:
            expect_case(parent, *case)
        dependency_repo = parent / "missing-dependency"
        dependency_repo.mkdir()
        make_repo(dependency_repo, "[control](present.md)\n", ("present.md",))
        result = run([sys.executable, "-I", "-S", str(CHECKER)], dependency_repo)
        output = result.stdout + result.stderr
        if result.returncode != 2 or "missing markdown-it-py" not in output:
            raise TestFailure(
                "missing-dependency: expected fail-closed exit 2 and install diagnostic\n"
                + output
            )
        print("OK   missing-dependency exit=2")
        broken_import = (
            "import builtins,runpy,sys\n"
            "real_import=builtins.__import__\n"
            "def hooked(name,*args,**kwargs):\n"
            "    if name == 'markdown_it': raise RuntimeError('broken install')\n"
            "    return real_import(name,*args,**kwargs)\n"
            "builtins.__import__=hooked\n"
            "target=sys.argv[1]\n"
            "sys.argv=[target]\n"
            "runpy.run_path(target,run_name='__main__')"
        )
        result = run([sys.executable, "-c", broken_import, str(CHECKER)], dependency_repo)
        output = result.stdout + result.stderr
        if result.returncode != 2 or "could not initialize markdown-it-py" not in output:
            raise TestFailure(
                "broken-dependency: expected fail-closed exit 2 and initialization diagnostic\n"
                + output
            )
        print("OK   broken-dependency exit=2")
    extra = 0
    if not internal_subset:
        with tempfile.TemporaryDirectory(prefix="link-hostile-git-env-") as raw:
            hostile_root = Path(raw)
            hostile_env = {
                **os.environ,
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "commit.gpgsign",
                "GIT_CONFIG_VALUE_0": "true",
                "GIT_DIR": str(hostile_root / "not-a-repository"),
                "GIT_WORK_TREE": str(hostile_root / "not-a-worktree"),
            }
            hostile = subprocess.run(
                [sys.executable, str(SELF), INNER_ARG],
                cwd=ROOT,
                env=hostile_env,
                text=True,
                capture_output=True,
                check=False,
            )
        hostile_output = hostile.stdout + hostile.stderr
        if hostile.returncode != 0 or "internal link-check self-tests, 0 failures" not in hostile_output:
            raise TestFailure(
                "self-hostile-git-env: inherited Git controls changed the self-test\n"
                + hostile_output
            )
        print("OK   self-hostile-git-env exit=0")
        extra += 1

        dead_stdout = run_with_closed_stream(
            [sys.executable, str(SELF), INNER_ARG], "stdout"
        )
        if dead_stdout != 2:
            raise TestFailure(
                f"self-dead-stdout: expected fail-closed exit 2, got {dead_stdout}"
            )
        print("OK   self-dead-stdout exit=2")
        extra += 1

        dead_stderr = run_with_closed_stream(
            [sys.executable, str(SELF), "--invalid"], "stderr"
        )
        if dead_stderr != 2:
            raise TestFailure(
                f"self-dead-stderr: expected fail-closed exit 2, got {dead_stderr}"
            )
        print("OK   self-dead-stderr exit=2")
        extra += 1

    label = "internal" if internal_subset else "full"
    print(f"\n{len(cases) + 2 + extra} {label} link-check self-tests, 0 failures")
    return 0


def seal_streams(code: int) -> int:
    """Flush output and prevent CPython's shutdown-time exit 120."""
    required = {1: code in (0, 1), 2: code == 2}
    for stream, descriptor in ((sys.stdout, 1), (sys.stderr, 2)):
        if stream is None:
            if required[descriptor]:
                code = 2
            continue
        try:
            stream.flush()
        except BaseException:
            code = 2
            try:
                null_descriptor = os.open(os.devnull, os.O_WRONLY)
                try:
                    os.dup2(null_descriptor, descriptor)
                finally:
                    os.close(null_descriptor)
            except BaseException:
                pass
    return code


def entrypoint() -> int:
    try:
        return main(sys.argv[1:])
    except KeyboardInterrupt:
        return 2
    except BaseException as exc:
        try:
            print(
                f"self-test-link-check: internal failure: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
        except BaseException:
            pass
        return 2


if __name__ == "__main__":
    sys.exit(seal_streams(entrypoint()))
