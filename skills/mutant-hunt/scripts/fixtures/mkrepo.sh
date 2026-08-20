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
