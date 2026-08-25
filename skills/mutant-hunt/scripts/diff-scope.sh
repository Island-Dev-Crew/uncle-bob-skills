#!/usr/bin/env bash
# diff-scope.sh — deterministic mutation scope: the new-side line ranges of a diff.
# Usage: diff-scope.sh <base-ref> [head-ref=HEAD] [repo-dir=.]
# Emits one "path:start-end" per added/modified hunk (new-side numbering).
# Pure deletions carry no mutable lines and are skipped; binary files emit no hunks.
# Known v0 limit: paths containing tab characters are unsupported.
# Exit codes: 0 scope emitted · 1 scope empty (nothing to mutate) · 2 usage or git error.
# A dead stdout must not become the verdict. `gate.sh … | head` closes the pipe early, the next
# write takes SIGPIPE, and the shell dies at 128+13 = 141 — a code this script's table does not
# name, arriving after the work was already done correctly. Handling the signal turns that into
# the usage/IO code 2, the one that means "no verdict here".
trap 'exit 2' PIPE
set -euo pipefail

if [ $# -lt 1 ] || [ $# -gt 3 ]; then
  echo "usage: diff-scope.sh <base-ref> [head-ref] [repo-dir]" >&2
  exit 2
fi
base=$1
head=${2:-HEAD}
repo=${3:-.}

diff_out=$(git -C "$repo" diff --unified=0 --diff-filter=ACMR "$base" "$head" --) || exit 2

scope=$(printf '%s\n' "$diff_out" | awk '
  /^\+\+\+ / {
    file = substr($0, 5)            # strip "+++ "
    sub(/\t.*$/, "", file)          # strip git quoting suffix if present
    sub(/^b\//, "", file)
  }
  /^@@ / {
    plus = $3                       # "+start,count" or "+start"
    sub(/^\+/, "", plus)
    n = split(plus, p, ",")
    start = p[1]
    count = (n > 1) ? p[2] : 1
    if (count > 0 && file != "/dev/null")
      printf "%s:%d-%d\n", file, start, start + count - 1
  }
')

if [ -z "$scope" ]; then
  echo "diff-scope: empty scope — no added/changed lines between $base and $head" >&2
  exit 1
fi
printf '%s\n' "$scope"
