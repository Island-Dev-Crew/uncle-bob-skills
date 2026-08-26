#!/usr/bin/env python3
"""Exercise every lane-check red/green fixture and its CLI status contract.

Run from the repository root with:

    python3 scripts/fixtures/lane-breaches/check-regressions.py

Exit 0 when every red fixture has its exact expected lane findings and both
green controls have none, and when the checker emits 0/1/2/3 for clean,
breach, error, and empty-scan inputs respectively. Exit 1 on a behavioral
mismatch. Exit 2 when the checker or a fixture cannot be loaded.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path


EXPECTED = {
    "asyncio-launchers.py": ["L1", "L1", "L2", "L3"],
    "destroy-dotdot-escape.sh": ["L3"],
    "destroy-longform.sh": ["L3"],
    "destroy-rmtree-working-root.py": ["L3"],
    "destroy-rmtree.py": ["L3"],
    "destroy-second-operand.sh": ["L3", "L3"],
    "destroy-split-flags.sh": ["L3"],
    "destroy-trailing-flags.sh": ["L3"],
    "destroy-via-launcher.py": ["L3"],
    "destroy-working-roots.sh": ["L3", "L3"],
    "destroy.sh": ["L3"],
    "exec-alias.py": ["L2"],
    "exec-builtins.py": ["L2", "L2"],
    "exec-list-family.py": ["L1"] * 8 + ["L3", "L3"],
    "exec-shell-int.py": ["L2"],
    "exec-shell-truthy.py": ["L2"] * 6,
    "exec.py": ["L2"],
    "meaningful-exit-equals.sh": [],
    "meaningful-exits-status.sh": [],
    "net-abs-path.py": ["L1"],
    "net-abs-path.sh": ["L1"],
    "net-ansi-c-command.sh": ["L1"],
    "net-command-wrappers.sh": ["L1", "L1", "L1"],
    "net-compound-bodies.sh": ["L1", "L1", "L1"],
    "net-direct-shell-forms.sh": ["L1"] * 11,
    "net-fstring.py": ["L1"],
    "net-keyword-args.py": ["L1"],
    "net-line-continuation.sh": ["L1"],
    "net-multiline-shell-c.sh": ["L1"],
    "net-nested-launcher.py": ["L1", "L1"],
    "net-nested-shell.sh": ["L1"],
    "net-python-overrides.py": ["L1", "L1", "L1", "L1", "L1"],
    "net-shebang-env-s.sh": ["L1"],
    "net.py": ["L1"],
    "negated-exit-header.sh": ["L4"],
    "safe-command-data.py": [],
    "safe-shell-literals.py": [],
    "safe-shell-syntax.sh": [],
    "safe-shell-data.sh": [],
    "undocumented-body-mention.py": ["L4"],
    "undocumented.py": ["L4"],
    "unrelated-exit-row.sh": ["L4"],
    "weak-exit-header.py": ["L4"],
}


def main() -> int:
    fixture_root = Path(__file__).resolve().parent
    checker_path = fixture_root.parents[1] / "lane-check.py"
    try:
        spec = importlib.util.spec_from_file_location("lane_check", checker_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot create module spec for {checker_path}")
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
    except (ImportError, OSError) as exc:
        print(f"lane fixture check: {exc}", file=sys.stderr)
        return 2

    mismatches = 0
    scripts = fixture_root / "scripts"
    discovered = {
        str(path.relative_to(scripts))
        for path in scripts.rglob("*")
        if path.is_file() and path.suffix in (".py", ".sh")
    }
    if discovered != set(EXPECTED):
        missing = sorted(discovered - set(EXPECTED))
        stale = sorted(set(EXPECTED) - discovered)
        print(f"MISMATCH fixture inventory: unwired={missing}, absent={stale}")
        mismatches += 1
    for name, expected in EXPECTED.items():
        path = scripts / name
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERROR {name}: {exc}", file=sys.stderr)
            return 2
        findings = (checker.check_python(path, source) if path.suffix == ".py"
                    else checker.check_shell(path, source))
        header = checker.header_text(path, source)
        if hasattr(checker, "has_exit_contract"):
            documented = checker.has_exit_contract(header)
        else:
            documented = bool(checker.EXIT_DOC.search(header))
        if not documented:
            findings.append("L4 exit codes not documented in the file header")
        observed = [finding.split(maxsplit=1)[0] for finding in findings]
        if observed != expected:
            mismatches += 1
            print(f"MISMATCH {name}: expected {expected}, observed {observed}")

    repo_root = checker_path.parent.parent
    cli_cases = [
        ("clean", [sys.executable, str(checker_path)], 0, "0 lane breach(es)"),
        ("breach", [sys.executable, str(checker_path), "scripts/fixtures"], 1,
         "lane breach(es)"),
        ("usage", [sys.executable, str(checker_path), "skills", "extra"], 2, "Usage:"),
        ("missing", [sys.executable, str(checker_path), "does-not-exist"], 2,
         "not a directory"),
    ]
    with tempfile.TemporaryDirectory(prefix="lane-empty-") as temp:
        empty = Path(temp) / "empty" / "scripts"
        empty.mkdir(parents=True)
        cli_cases.append(("empty", [sys.executable, str(checker_path), temp], 3,
                          "NOTHING SCANNED"))
        for label, command, expected_code, marker in cli_cases:
            result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True,
                                    check=False)
            observed = result.stdout + result.stderr
            if result.returncode != expected_code or marker not in observed:
                mismatches += 1
                print(f"MISMATCH CLI {label}: expected code {expected_code} and {marker!r}, "
                      f"observed code {result.returncode}")

    print(f"{len(EXPECTED)} fixture cases + {len(cli_cases)} CLI cases, "
          f"{mismatches} mismatch(es)")
    return 1 if mismatches else 0


if __name__ == "__main__":
    try:
        code = main()
    except BaseException as exc:
        print(f"lane fixture check: internal failure: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        code = 2
    sys.exit(code)
