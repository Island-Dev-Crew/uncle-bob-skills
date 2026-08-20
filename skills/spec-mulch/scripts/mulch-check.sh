#!/usr/bin/env bash
# mulch-check.sh — the mulch gate: red while any mulch-marked spec file survives.
#
# A story spec carries the marker line `MULCH-ON-MERGE: <story-id>` at line
# start. Run this from the target repo at merge time: green means every
# launched story's scaffolding is gone; red lists the survivors.
#
# Usage: mulch-check.sh [dir]              # whole tree (default: .)
#        mulch-check.sh [dir] <story-id>   # only specs marked for one story
#
# Exit 0 green · 1 red (survivors listed) · 2 usage error.
set -euo pipefail

dir="${1:-.}"
story="${2:-}"

[ -d "$dir" ] || { echo "mulch-check: not a directory: $dir" >&2; exit 2; }

# Line-start anchor keeps prose that merely *mentions* the marker out of scope.
# Every text file is scanned regardless of extension (.md, .txt, .rst, .adoc,
# ...); -I skips binaries, .git is excluded.
survivors="$(grep -rIl --exclude-dir=.git -E '^MULCH-ON-MERGE:' "$dir" || true)"

if [ -n "$story" ] && [ -n "$survivors" ]; then
  filtered=""
  while IFS= read -r f; do
    # Whole-token match: story-4 must not catch story-42's spec. The id is escaped
    # first — interpolated raw, a metacharacter makes the filter a pattern rather
    # than a literal, and 'story-1.2' silently matched a 'story-142' spec.
    story_esc="$(printf '%s' "$story" | sed 's/[^a-zA-Z0-9_-]/\\&/g')"
    if grep -qE "^MULCH-ON-MERGE:[[:space:]]*${story_esc}[[:space:]]*$" "$f"; then
      filtered="${filtered}${f}"$'\n'
    fi
  done <<< "$survivors"
  survivors="$(printf '%s' "$filtered")"
fi

if [ -n "$survivors" ]; then
  echo "MULCH RED — spec scaffolding survives past its story:"
  while IFS= read -r f; do
    [ -n "$f" ] && echo "  $f"
  done <<< "$survivors"
  echo "Fold anything durable into gherkin / tests / the fence, delete the file, re-run."
  exit 1
fi

echo "MULCH GREEN — no marked spec files remain under ${dir}${story:+ for story $story}"
