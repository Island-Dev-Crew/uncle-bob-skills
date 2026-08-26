#!/usr/bin/env python3
"""Verify HEAD's committed content against its committed release digest.

Usage:
  python3 scripts/verify-release.py            verify HEAD
  python3 scripts/verify-release.py --write    write a digest for HEAD's content

The digest is deliberately a *content manifest*, not a self-referential
commit identity. Its SHA-256 covers every recursively tracked entry in HEAD
except RELEASE-DIGEST.txt. Each canonical record is:

    mode SP type SP git-object-id TAB raw-path NUL

Records are sorted by raw path bytes before hashing. Git object IDs bind blob
contents (and gitlink targets); the outer SHA-256 binds the complete set of
paths, modes, types, and object IDs. Because the digest file is excluded,
`--write` can be run for a content commit and the resulting file can then be
committed without invalidating itself.

Verification reads RELEASE-DIGEST.txt from HEAD's exact root 100644 blob.
Dirty or untracked worktree files therefore cannot forge or disturb the verdict.
Before reading or writing a digest, strict Git object-store verification runs
against the captured HEAD with replacement objects disabled.

What a match proves: HEAD is internally consistent with the content manifest
published inside that same commit. It does *not* prove authorship, provenance,
correctness, or that a mutable tag/repository has not been replaced. Commit
and tree identity stay out of this file; bind those out of band with a signed
tag or a separately authenticated release asset. Tag-signature status below
reports only what local `git verify-tag` can establish and never upgrades an
unsigned or unverifiable tag into an identity claim.

Exit codes:
  0  committed content matches the committed digest
  1  well-formed committed digest does not match committed content
  2  usage, malformed digest, Git failure, or internal failure
  3  RELEASE-DIGEST.txt is absent from HEAD
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


DIGEST = "RELEASE-DIGEST.txt"
DIGEST_BYTES = DIGEST.encode("utf-8")
FORMAT = "uncle-bob-skills-release-digest-v1"
REQUIRED_KEYS = ("format", "files", "manifest-sha256")


class GitError(RuntimeError):
    pass


class DigestFormatError(ValueError):
    pass


def git_environment() -> dict[str, str]:
    """Return an environment that makes Git read literal committed objects."""
    environment = os.environ.copy()
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    return environment


def run_git(args: list[str], *, text: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        check=False,
        env=git_environment(),
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(detail or f"git {' '.join(args)} exited {result.returncode}")
    if text:
        return result.stdout.decode("utf-8", errors="strict")
    return result.stdout


def repository_root() -> Path:
    return Path(str(run_git(["rev-parse", "--show-toplevel"], text=True)).strip())


def captured_identity() -> tuple[str, str]:
    """Resolve HEAD once, then derive every identity from that immutable SHA."""
    head = str(run_git(["rev-parse", "--verify", "HEAD^{commit}"], text=True)).strip()
    tree = str(run_git(["rev-parse", f"{head}^{{tree}}"], text=True)).strip()
    return head, tree


def verify_object_store(head: str) -> None:
    """Reject a verdict when reachable object bytes do not match their IDs."""
    try:
        run_git(["fsck", "--strict", "--no-dangling", head])
    except GitError as exc:
        raise GitError(f"object store integrity check failed: {exc}") from exc


def manifest_sha(rev: str) -> tuple[str, int]:
    """Hash canonical committed-tree records, excluding the digest itself."""
    raw = bytes(run_git(["ls-tree", "-r", "-z", "--full-tree", rev]))
    records: list[tuple[bytes, bytes]] = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        try:
            metadata, path = entry.split(b"\t", 1)
            mode, kind, object_id = metadata.split(b" ", 2)
        except ValueError as exc:
            raise GitError("git ls-tree returned an unparseable record") from exc
        if path == DIGEST_BYTES:
            continue
        record = mode + b" " + kind + b" " + object_id + b"\t" + path + b"\0"
        records.append((path, record))

    records.sort(key=lambda item: item[0])
    digest = hashlib.sha256()
    for _path, record in records:
        digest.update(record)
    return digest.hexdigest(), len(records)


def published_digest_text(rev: str) -> str | None:
    """Return the digest published in the captured commit, never the worktree copy."""
    listing = bytes(run_git(["ls-tree", "-z", "--full-tree", rev, "--", DIGEST]))
    entries = [entry for entry in listing.split(b"\0") if entry]
    if not entries:
        return None
    if len(entries) != 1:
        raise GitError(f"could not resolve exactly one root {DIGEST}")
    try:
        metadata, path = entries[0].split(b"\t", 1)
        mode, kind, object_id = metadata.split(b" ", 2)
    except ValueError as exc:
        raise GitError(f"git ls-tree returned an unparseable {DIGEST} record") from exc
    if path != DIGEST_BYTES:
        raise GitError(f"could not resolve exactly one root {DIGEST}")
    if mode != b"100644" or kind != b"blob":
        rendered_mode = mode.decode("ascii", errors="replace")
        rendered_kind = kind.decode("ascii", errors="replace")
        raise DigestFormatError(
            f"{DIGEST} must be a root 100644 blob; "
            f"found {rendered_mode} {rendered_kind}"
        )
    raw = bytes(run_git(["cat-file", "blob", object_id.decode("ascii", errors="strict")]))
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise DigestFormatError(f"{DIGEST} is not UTF-8") from exc


def parse_digest(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        if ":" not in line:
            raise DigestFormatError(f"line {number}: expected 'key: value'")
        key, value = (part.strip() for part in line.split(":", 1))
        if key not in REQUIRED_KEYS:
            raise DigestFormatError(f"line {number}: unknown field {key!r}")
        if key in values:
            raise DigestFormatError(f"line {number}: duplicate field {key!r}")
        if not value:
            raise DigestFormatError(f"line {number}: empty field {key!r}")
        values[key] = value

    missing = [key for key in REQUIRED_KEYS if key not in values]
    if missing:
        raise DigestFormatError(f"missing field(s): {', '.join(missing)}")
    if values["format"] != FORMAT:
        raise DigestFormatError(f"unsupported format {values['format']!r}")
    if not re.fullmatch(r"0|[1-9][0-9]*", values["files"]):
        raise DigestFormatError("'files' must be a canonical non-negative integer")
    if not re.fullmatch(r"[0-9a-f]{64}", values["manifest-sha256"]):
        raise DigestFormatError("'manifest-sha256' must be 64 lowercase hexadecimal characters")
    return values


def tag_signature_state(head: str) -> str:
    """Describe local tag verification without claiming external identity."""
    try:
        tags = [
            tag
            for tag in str(run_git(["tag", "--points-at", head], text=True)).splitlines()
            if tag
        ]
    except (GitError, UnicodeError):
        return "unknown; local tag enumeration failed"
    if not tags:
        return "no tag points at HEAD"

    states = []
    for tag in tags:
        try:
            object_type = str(
                run_git(["cat-file", "-t", f"refs/tags/{tag}"], text=True)
            ).strip()
        except (GitError, UnicodeError):
            states.append(f"{tag}: unknown; local tag inspection failed")
            continue
        if object_type != "tag":
            states.append(f"{tag}: lightweight tag; no annotated-tag signature")
            continue
        result = subprocess.run(
            ["git", "verify-tag", "--", tag],
            capture_output=True,
            check=False,
            env=git_environment(),
        )
        if result.returncode == 0:
            states.append(f"{tag}: git verify-tag succeeded in this environment")
        else:
            states.append(
                f"{tag}: signature NOT verified by git verify-tag "
                "(unsigned, invalid, or verifier/key unavailable)"
            )
    return "; ".join(states)


def identity_report(head: str, tree: str) -> None:
    print(f"observed HEAD (not stored in digest): {head}")
    print(f"observed tree (not stored in digest): {tree}")
    print("identity binding: out of band; compare a signed tag or authenticated release asset")
    print(f"tag signature: {tag_signature_state(head)}")


def write_digest(root: Path, manifest: str, count: int) -> None:
    content = (
        "# Uncle Bob Skills - committed content manifest\n"
        "# Generated from HEAD by: python3 scripts/verify-release.py --write\n"
        "# Covers every tracked entry except this file. Commit and tree identity\n"
        "# are intentionally out of band; use a signed tag or authenticated release asset.\n"
        f"format: {FORMAT}\n"
        f"files: {count}\n"
        f"manifest-sha256: {manifest}\n"
    ).encode("utf-8")
    descriptor: int | None = None
    temporary: str | None = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{DIGEST}.", dir=root
        )
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError("temporary digest is not a regular file")
        os.fchmod(descriptor, 0o644)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, root / DIGEST)
        temporary = None
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            except OSError:
                pass


def emit_error(message: str) -> None:
    """Write a required diagnostic without falling back to stdout."""
    if sys.stderr is None:
        raise OSError("stderr is unavailable")
    print(message, file=sys.stderr)


def seal_streams(code: int) -> int:
    """Flush claimed output and prevent CPython's shutdown-time exit 120."""
    required = {
        1: code in (0, 1, 3),
        2: code in (2, 3),
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


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv != ["--write"]:
        emit_error(__doc__ or "verify-release: invalid usage")
        return 2

    try:
        root = repository_root()
        head, tree = captured_identity()
        verify_object_store(head)

        if argv == ["--write"]:
            manifest, count = manifest_sha(head)
            write_digest(root, manifest, count)
            print(f"wrote {DIGEST} from HEAD's committed content")
            print(f"  files {count}")
            print(f"  manifest-sha256 {manifest}")
            print("  commit/tree identity intentionally omitted from the digest")
            identity_report(head, tree)
            return 0

        text = published_digest_text(head)
        if text is None:
            emit_error(
                f"NO PUBLISHED DIGEST - {DIGEST} is absent from HEAD; "
                "a worktree copy is not release evidence"
            )
            identity_report(head, tree)
            return 3

        published = parse_digest(text)
        manifest, count = manifest_sha(head)
    except DigestFormatError as exc:
        emit_error(f"MALFORMED PUBLISHED DIGEST - {exc}")
        return 2
    except (GitError, OSError, UnicodeError) as exc:
        emit_error(f"verify-release: {exc}")
        return 2

    checks = (
        ("files", str(count), published["files"]),
        ("manifest-sha256", manifest, published["manifest-sha256"]),
    )
    mismatches = [(key, actual, expected) for key, actual, expected in checks if actual != expected]
    for key, actual, expected in mismatches:
        print(f"MISMATCH {key}\n  published: {expected}\n  computed:  {actual}")
    if not mismatches:
        print("MATCH committed content manifest")
    print(f"{count} committed tracked entries hashed; {len(mismatches)} mismatch(es)")
    identity_report(head, tree)
    return 1 if mismatches else 0


if __name__ == "__main__":
    try:
        _code = main()
    except KeyboardInterrupt:
        _code = 2
    except BaseException as _exc:
        try:
            if sys.stderr is not None:
                print(
                    f"error: internal failure: {type(_exc).__name__}: {_exc}",
                    file=sys.stderr,
                )
        except BaseException:
            pass
        _code = 2
    _code = seal_streams(_code)
    sys.exit(_code)
