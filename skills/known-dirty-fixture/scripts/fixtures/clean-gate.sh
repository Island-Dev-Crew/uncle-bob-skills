#!/usr/bin/env bash
# KNOWN-CLEAN fixture for prove-gate.sh: a real checker.
# Rule: no TODO marker may remain in a shipped file.
# Red on sample-bad.txt, green on sample-good.txt, so prove-gate.sh MUST accept it (exit 0).
grep -q 'TODO' "$1" && { echo "TODO marker left in $1" >&2; exit 1; }
exit 0
