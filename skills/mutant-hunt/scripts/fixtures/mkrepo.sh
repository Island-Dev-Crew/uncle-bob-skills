#!/usr/bin/env bash
# mkrepo.sh — materialize a diff-scope fixture as a throwaway two-commit git repo.
# diff-scope.sh's input is a git history, so the pair ships as file states:
#   base/ is the BASE commit (shared); clean-head/ and dirty-head/ are the HEAD commit.
#   clean-head = one modified line + a 3-line insertion  -> scope emitted, gate exits 0.
#   dirty-head = deletions only, nothing mutable         -> empty scope, gate exits 1.
# Usage: mkrepo.sh <clean|dirty> [dest-dir]   # prints the repo path on stdout
# Exit codes: 0 repo built · 2 usage error.
set -euo pipefail

usage() { echo "usage: mkrepo.sh <clean|dirty> [dest-dir]" >&2; exit 2; }
[ $# -ge 1 ] && [ $# -le 2 ] || usage
case $1 in clean|dirty) kind=$1 ;; *) usage ;; esac

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
dest=${2:-$(mktemp -d)}

# A destination the caller named is guarded before anything is written to it. Given a real
# repository this script used to overwrite pricing.js, sweep untracked files into a commit
# via `git add -A`, append two fixture commits onto the user's history — and exit 0. A
# fixture builder that can damage the tree it is pointed at is not a fixture builder.
if [ $# -eq 2 ]; then
  if [ -e "$dest" ] && [ -n "$(ls -A "$dest" 2>/dev/null)" ]; then
    echo "mkrepo.sh: refusing a non-empty destination: $dest" >&2
    exit 2
  fi
  if parent=$(cd -- "$(dirname -- "$dest")" 2>/dev/null && pwd) \
     && git -C "$parent" rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "mkrepo.sh: refusing a destination inside an existing work tree: $dest" >&2
    exit 2
  fi
fi
mkdir -p "$dest"

g() { git -C "$dest" -c user.name=fixture -c user.email=fixture@invalid -c commit.gpgsign=false "$@"; }

git -c init.defaultBranch=main init -q "$dest"
cp "$here/base/pricing.js" "$dest/pricing.js"
g add -A
g commit -qm base
cp "$here/$kind-head/pricing.js" "$dest/pricing.js"
g add -A
g commit -qm head
printf '%s\n' "$dest"
