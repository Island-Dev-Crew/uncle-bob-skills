#!/usr/bin/env python3
"""Watched-red integration tests for scripts/verify-release.py.

The tests create real temporary Git repositories and invoke the shipped
verifier as a command.  They intentionally avoid importing its internals: the
public exit codes, diagnostics, generated digest, and committed-object
behaviour are the contract.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path


VERIFIER = Path(__file__).with_name("verify-release.py").resolve()
SELF_TEST = Path(__file__).resolve()
INNER_ARG = "--internal-no-meta"


class TestFailure(AssertionError):
    pass


class HarnessError(RuntimeError):
    pass


class UsageError(ValueError):
    pass


def command(
    argv: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    process_env = {
        **os.environ,
        "LC_ALL": "C.UTF-8",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    if env:
        process_env.update(env)
    return subprocess.run(
        argv,
        cwd=cwd,
        env=process_env,
        text=True,
        capture_output=True,
        check=False,
    )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = command(["git", *args], repo)
    if result.returncode != 0:
        raise HarnessError(
            f"git {' '.join(args)} exited {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def verify(
    repo: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return command([sys.executable, str(VERIFIER), *args], repo, env=env)


def verify_with_closed_fd(
    repo: Path,
    fd: int,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    launcher = (
        "import os,sys; "
        "fd=int(sys.argv[1]); "
        "os.close(fd); "
        "os.execv(sys.executable,[sys.executable,*sys.argv[2:]])"
    )
    return command(
        [sys.executable, "-c", launcher, str(fd), str(VERIFIER), *args],
        repo,
    )


def command_with_closed_fd(
    repo: Path,
    fd: int,
    argv: list[str],
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    launcher = (
        "import os,sys; "
        "fd=int(sys.argv[1]); "
        "os.close(fd); "
        "os.execv(sys.argv[2],[*sys.argv[2:]])"
    )
    return command(
        [sys.executable, "-c", launcher, str(fd), *argv],
        repo,
        env=env,
    )


def expect_result(
    result: subprocess.CompletedProcess[str],
    code: int,
    needle: str,
) -> None:
    combined = result.stdout + result.stderr
    if result.returncode != code or needle not in combined:
        raise TestFailure(
            f"expected exit {code} containing {needle!r}; got {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def new_repo(parent: Path, name: str) -> Path:
    repo = parent / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Release Verifier Self-Test")
    git(repo, "config", "user.email", "release-verifier@example.invalid")
    (repo / "payload.txt").write_text("alpha\n", encoding="utf-8")
    git(repo, "add", "payload.txt")
    git(repo, "commit", "--no-gpg-sign", "--no-verify", "-q", "-m", "payload")
    return repo


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "--no-gpg-sign", "--no-verify", "-q", "-m", message)


def write_and_commit_digest(repo: Path) -> None:
    expect_result(verify(repo, "--write"), 0, "wrote RELEASE-DIGEST.txt")
    commit_all(repo, "publish digest")


def test_uncommitted_digest_does_not_mask_absence(parent: Path) -> None:
    """Fails if verification accepts a digest absent from HEAD."""
    repo = new_repo(parent, "absent")
    expect_result(verify(repo, "--write"), 0, "wrote RELEASE-DIGEST.txt")
    expect_result(verify(repo), 3, "NO PUBLISHED DIGEST")


def test_malformed_committed_digest_is_non_verdict(parent: Path) -> None:
    """Fails if malformed published data is treated as a content mismatch."""
    repo = new_repo(parent, "malformed")
    (repo / "RELEASE-DIGEST.txt").write_text(
        "format: uncle-bob-skills-release-digest-v1\n"
        "files: one\n"
        "manifest-sha256: not-a-sha256\n",
        encoding="utf-8",
    )
    commit_all(repo, "publish malformed digest")
    expect_result(verify(repo), 2, "MALFORMED PUBLISHED DIGEST")


def test_worktree_tampering_cannot_change_verdict(parent: Path) -> None:
    """Fails if either candidate content or the digest is read from the worktree."""
    repo = new_repo(parent, "worktree-tamper")
    write_and_commit_digest(repo)
    (repo / "payload.txt").write_text("dirty replacement\n", encoding="utf-8")
    (repo / "RELEASE-DIGEST.txt").write_text("forged worktree digest\n", encoding="utf-8")
    expect_result(verify(repo), 0, "MATCH committed content manifest")


def test_stale_committed_digest_refuses_forged_worktree_digest(parent: Path) -> None:
    """Fails if a dirty digest can hide a committed content mismatch."""
    repo = new_repo(parent, "content-mismatch")
    write_and_commit_digest(repo)
    (repo / "payload.txt").write_text("beta\n", encoding="utf-8")
    commit_all(repo, "change published content without its digest")

    # This generates a worktree digest for the new HEAD.  Verification must
    # ignore it and compare against the stale digest still published in HEAD.
    expect_result(verify(repo, "--write"), 0, "wrote RELEASE-DIGEST.txt")
    expect_result(verify(repo), 1, "MISMATCH manifest-sha256")


def test_replace_ref_cannot_forge_match(parent: Path) -> None:
    """Fails if Git replacement objects can substitute the release snapshot."""
    repo = new_repo(parent, "replace-ref")
    write_and_commit_digest(repo)
    valid_release = git(repo, "rev-parse", "HEAD").stdout.strip()

    (repo / "payload.txt").write_text("beta\n", encoding="utf-8")
    commit_all(repo, "change published content without its digest")
    stale_release = git(repo, "rev-parse", "HEAD").stdout.strip()
    expect_result(verify(repo), 1, "MISMATCH manifest-sha256")

    git(repo, "replace", stale_release, valid_release)
    result = verify(repo)
    expect_result(result, 1, "MISMATCH manifest-sha256")
    if f"observed HEAD (not stored in digest): {stale_release}" not in result.stdout:
        raise TestFailure("verifier did not report the unreplaced HEAD identity")


def test_corrupt_reachable_object_is_nonverdict(parent: Path) -> None:
    """Fails if a hash-path mismatch can retain a MATCH verdict."""
    repo = new_repo(parent, "corrupt-object")
    write_and_commit_digest(repo)
    object_id = git(repo, "rev-parse", "HEAD:payload.txt").stdout.strip()
    object_path = repo / ".git" / "objects" / object_id[:2] / object_id[2:]
    if not object_path.is_file():
        raise HarnessError("payload fixture was not stored as a loose object")
    object_path.chmod(0o644)
    object_path.write_bytes(zlib.compress(b"blob 6\0omega\n"))
    expect_result(verify(repo), 2, "object store integrity check failed")


def test_generated_digest_is_self_consistent_after_commit(parent: Path) -> None:
    """Fails if the generated digest embeds its pre-commit HEAD or tree."""
    repo = new_repo(parent, "self-consistent")
    expect_result(verify(repo, "--write"), 0, "wrote RELEASE-DIGEST.txt")
    generated = (repo / "RELEASE-DIGEST.txt").read_text(encoding="utf-8")
    forbidden = [line for line in generated.splitlines() if line.startswith(("head:", "tree:"))]
    if forbidden:
        raise TestFailure(f"digest embeds self-referential identity: {forbidden}")
    commit_all(repo, "publish digest")
    expect_result(verify(repo), 0, "MATCH committed content manifest")


def test_published_digest_symlink_is_nonverdict(parent: Path) -> None:
    """Fails if a mode-120000 digest entry can publish a verdict."""
    repo = new_repo(parent, "digest-mode-symlink")
    expect_result(verify(repo, "--write"), 0, "wrote RELEASE-DIGEST.txt")
    digest = repo / "RELEASE-DIGEST.txt"
    content = digest.read_text(encoding="utf-8")
    digest.unlink()
    digest.symlink_to(content)
    commit_all(repo, "publish symlink digest")
    expect_result(
        verify(repo),
        2,
        "RELEASE-DIGEST.txt must be a root 100644 blob; found 120000 blob",
    )


def test_published_digest_executable_is_nonverdict(parent: Path) -> None:
    """Fails if a mode-100755 digest entry can publish a verdict."""
    repo = new_repo(parent, "digest-mode-executable")
    expect_result(verify(repo, "--write"), 0, "wrote RELEASE-DIGEST.txt")
    (repo / "RELEASE-DIGEST.txt").chmod(0o755)
    commit_all(repo, "publish executable digest")
    expect_result(
        verify(repo),
        2,
        "RELEASE-DIGEST.txt must be a root 100644 blob; found 100755 blob",
    )


def test_dead_stdout_maps_match_to_non_verdict(parent: Path) -> None:
    """Fails if a verdict whose stdout cannot be delivered exits 0 or 120."""
    repo = new_repo(parent, "dead-stdout")
    write_and_commit_digest(repo)
    result = verify_with_closed_fd(repo, 1)
    if result.returncode != 2:
        raise TestFailure(f"dead stdout must exit 2, got {result.returncode}")


def test_dead_stderr_maps_bad_usage_to_non_verdict(parent: Path) -> None:
    """Fails if an undeliverable usage diagnostic leaks exit 1 or 120."""
    repo = new_repo(parent, "dead-stderr-usage")
    result = verify_with_closed_fd(repo, 2, "--not-an-option")
    if result.returncode != 2:
        raise TestFailure(f"bad usage with dead stderr must exit 2, got {result.returncode}")


def test_dead_stderr_maps_missing_digest_to_non_verdict(parent: Path) -> None:
    """Fails if an undeliverable no-digest diagnostic retains verdict code 3."""
    repo = new_repo(parent, "dead-stderr-missing")
    result = verify_with_closed_fd(repo, 2)
    if result.returncode != 2:
        raise TestFailure(f"missing digest with dead stderr must exit 2, got {result.returncode}")


def test_write_does_not_follow_committed_digest_symlink(parent: Path) -> None:
    """Fails if --write follows RELEASE-DIGEST.txt outside the repository."""
    repo = new_repo(parent, "digest-symlink")
    outside = parent / "outside-digest-target.txt"
    sentinel = "outside file must remain unchanged\n"
    outside.write_text(sentinel, encoding="utf-8")
    digest = repo / "RELEASE-DIGEST.txt"
    digest.symlink_to(outside)
    commit_all(repo, "publish digest symlink")

    result = verify(repo, "--write")
    if result.returncode not in (0, 2):
        raise TestFailure(f"symlink-safe write must replace or refuse, got {result.returncode}")
    if outside.read_text(encoding="utf-8") != sentinel:
        raise TestFailure("--write followed the digest symlink and changed an outside file")
    if result.returncode == 0 and (digest.is_symlink() or not digest.is_file()):
        raise TestFailure("successful --write did not atomically replace the symlink with a file")
    if result.returncode == 2 and not digest.is_symlink():
        raise TestFailure("refused --write mutated the committed digest symlink")
    leftovers = list(repo.glob(".RELEASE-DIGEST.txt.*"))
    if leftovers:
        raise TestFailure(f"temporary digest files were not cleaned up: {leftovers}")


def test_head_movement_cannot_mix_release_snapshot(parent: Path) -> None:
    """Fails if one run mixes identity, digest, or manifest from two HEADs."""
    repo = new_repo(parent, "head-movement")
    write_and_commit_digest(repo)
    head_a = git(repo, "rev-parse", "HEAD").stdout.strip()

    (repo / "payload.txt").write_text("beta\n", encoding="utf-8")
    commit_all(repo, "second release candidate")
    head_b = git(repo, "rev-parse", "HEAD").stdout.strip()
    git(repo, "reset", "-q", "--hard", head_a)

    real_git = shutil.which("git")
    if not real_git:
        raise TestFailure("git executable not found")
    wrapper_dir = parent / "head-movement-bin"
    wrapper_dir.mkdir()
    marker = parent / "head-movement-triggered"
    wrapper = wrapper_dir / "git"
    wrapper.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib, subprocess, sys\n"
        "args = sys.argv[1:]\n"
        "marker = pathlib.Path(os.environ['MOVE_MARKER'])\n"
        "if any(arg.endswith('^{tree}') for arg in args) and not marker.exists():\n"
        "    marker.write_text('moved\\n', encoding='utf-8')\n"
        "    moved = subprocess.run([os.environ['REAL_GIT'], 'update-ref', 'HEAD', "
        "os.environ['MOVE_TO']], check=False)\n"
        "    if moved.returncode != 0:\n"
        "        sys.exit(moved.returncode)\n"
        "os.execv(os.environ['REAL_GIT'], [os.environ['REAL_GIT'], *args])\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    env = {
        "PATH": str(wrapper_dir) + os.pathsep + os.environ.get("PATH", ""),
        "REAL_GIT": real_git,
        "MOVE_TO": head_b,
        "MOVE_MARKER": str(marker),
    }
    result = verify(repo, env=env)
    expect_result(result, 0, "MATCH committed content manifest")
    if f"observed HEAD (not stored in digest): {head_a}" not in result.stdout:
        raise TestFailure("verifier did not report the single captured HEAD")
    if git(repo, "rev-parse", "HEAD").stdout.strip() != head_b:
        raise TestFailure("HEAD movement fixture did not fire")


def test_self_test_dead_stdout_maps_to_non_verdict(parent: Path) -> None:
    """Fails if the self-test loses stdout but exits success, failure, or 120."""
    result = command_with_closed_fd(
        parent,
        1,
        [sys.executable, str(SELF_TEST), INNER_ARG],
    )
    if result.returncode != 2:
        raise TestFailure(f"self-test with dead stdout must exit 2, got {result.returncode}")


def test_self_test_broken_stdout_pipe_maps_to_nonverdict(parent: Path) -> None:
    """Fails if a dead stdout reader leaks CPython's shutdown exit 120."""
    process_env = {**os.environ, "LC_ALL": "C.UTF-8"}
    process = subprocess.Popen(
        [sys.executable, str(SELF_TEST), INNER_ARG],
        cwd=parent,
        env=process_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdout is None or process.stderr is None:
        process.kill()
        raise TestFailure("could not create self-test pipe fixture")
    process.stdout.close()
    stderr = process.stderr.read()
    code = process.wait()
    if code != 2:
        raise TestFailure(
            f"self-test with broken stdout pipe must exit 2, got {code}; stderr={stderr!r}"
        )


def test_self_test_ignores_hostile_global_commit_config(parent: Path) -> None:
    """Fails if host signing policy can turn fixture setup into false failures."""
    hostile_config = parent / "hostile-gitconfig"
    hostile_config.write_text(
        "[commit]\n"
        "\tgpgsign = true\n"
        "[gpg]\n"
        "\tprogram = /usr/bin/false\n",
        encoding="utf-8",
    )
    result = command(
        [sys.executable, str(SELF_TEST), INNER_ARG],
        parent,
        env={
            "GIT_CONFIG_GLOBAL": str(hostile_config),
            "GIT_CONFIG_NOSYSTEM": "1",
        },
    )
    expect_result(result, 0, "tests, 0 failures")


def test_self_test_internal_git_fault_maps_to_nonverdict(parent: Path) -> None:
    """Fails if broken fixture infrastructure is reported as a test verdict."""
    wrapper_dir = parent / "broken-git-bin"
    wrapper_dir.mkdir()
    wrapper = wrapper_dir / "git"
    wrapper.write_text("#!/bin/sh\nexit 17\n", encoding="utf-8")
    wrapper.chmod(0o755)
    result = command(
        [sys.executable, str(SELF_TEST), INNER_ARG],
        parent,
        env={"PATH": str(wrapper_dir)},
    )
    expect_result(result, 2, "self-test-verify-release: internal failure")


def test_self_test_selection_ignores_environment(parent: Path) -> None:
    """Fails if ambient environment can silently select a reduced suite."""
    del parent
    legacy_name = "VERIFY_RELEASE_SELF_TEST_INNER_RUN"
    previous = os.environ.get(legacy_name)
    os.environ[legacy_name] = "1"
    try:
        selector = globals().get("selected_tests")
        if selector is None:
            raise TestFailure("explicit argv-only test selection is not implemented")
        selected, label = selector([])
    finally:
        if previous is None:
            os.environ.pop(legacy_name, None)
        else:
            os.environ[legacy_name] = previous
    if selected != TESTS or label != "full":
        raise TestFailure("no-argument selection did not retain the full suite")


def test_self_test_invalid_argument_is_nonverdict(parent: Path) -> None:
    """Fails if an unknown self-test mode is ignored or treated as a verdict."""
    result = command(
        [sys.executable, str(SELF_TEST), "--not-a-mode"],
        parent,
    )
    expect_result(result, 2, "usage: self-test-verify-release.py")


TESTS = (
    test_uncommitted_digest_does_not_mask_absence,
    test_malformed_committed_digest_is_non_verdict,
    test_worktree_tampering_cannot_change_verdict,
    test_stale_committed_digest_refuses_forged_worktree_digest,
    test_replace_ref_cannot_forge_match,
    test_corrupt_reachable_object_is_nonverdict,
    test_generated_digest_is_self_consistent_after_commit,
    test_published_digest_symlink_is_nonverdict,
    test_published_digest_executable_is_nonverdict,
    test_dead_stdout_maps_match_to_non_verdict,
    test_dead_stderr_maps_bad_usage_to_non_verdict,
    test_dead_stderr_maps_missing_digest_to_non_verdict,
    test_write_does_not_follow_committed_digest_symlink,
    test_head_movement_cannot_mix_release_snapshot,
    test_self_test_dead_stdout_maps_to_non_verdict,
    test_self_test_broken_stdout_pipe_maps_to_nonverdict,
    test_self_test_ignores_hostile_global_commit_config,
    test_self_test_internal_git_fault_maps_to_nonverdict,
    test_self_test_selection_ignores_environment,
    test_self_test_invalid_argument_is_nonverdict,
)


def selected_tests(argv: list[str]) -> tuple[tuple, str]:
    """Select the full public suite or the explicit recursive child subset."""
    if not argv:
        return TESTS, "full"
    if argv == [INNER_ARG]:
        return (
            tuple(test for test in TESTS if not test.__name__.startswith("test_self_test_")),
            "internal-subset",
        )
    raise UsageError(
        f"usage: self-test-verify-release.py [{INNER_ARG}]"
    )


def main() -> int:
    failures = []
    try:
        tests, label = selected_tests(sys.argv[1:])
    except UsageError as exc:
        emit_error(str(exc))
        return 2
    with tempfile.TemporaryDirectory(prefix="verify-release-self-test-") as tmp:
        parent = Path(tmp)
        for test in tests:
            try:
                test(parent)
            except TestFailure as exc:
                failures.append((test.__name__, exc))
                print(f"not ok - {test.__name__}: {exc}")
            else:
                print(f"ok - {test.__name__}")
    print(f"\n{len(tests)} {label} tests, {len(failures)} failures")
    return 1 if failures else 0


def emit_error(message: str) -> None:
    """Write an internal-failure diagnostic without falling back to stdout."""
    if sys.stderr is None:
        raise OSError("stderr is unavailable")
    print(message, file=sys.stderr)


def seal_streams(code: int) -> int:
    """Flush test output and prevent CPython's shutdown-time exit 120."""
    required = {
        1: code in (0, 1),
        2: code == 2,
    }
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
        return main()
    except KeyboardInterrupt:
        return 2
    except BaseException as exc:
        try:
            emit_error(
                "self-test-verify-release: internal failure: "
                f"{type(exc).__name__}: {exc}"
            )
        except BaseException:
            pass
        return 2


if __name__ == "__main__":
    sys.exit(seal_streams(entrypoint()))
