#!/usr/bin/env bash
# prove-gate.sh — accept a gate only after it fails RED on a known-bad fixture
# and passes GREEN on a known-good one. A gate that cannot fail guards nothing.
#
# Usage: prove-gate.sh <bad-fixture> <good-fixture> -- <gate-command> [args...]
# The gate command is run twice, with each fixture path appended as its final
# argument. Exit 0 iff gate(bad) is non-zero AND gate(good) is zero.
set -u

usage() { sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

[ $# -ge 4 ] || usage
bad=$1; good=$2; shift 2
[ "$1" = "--" ] || usage
shift

[ -e "$bad" ]  || { echo "MISSING red fixture: $bad" >&2; exit 1; }
[ -e "$good" ] || { echo "MISSING green fixture: $good" >&2; exit 1; }

"$@" "$bad" >/dev/null 2>&1; red=$?
"$@" "$good" >/dev/null 2>&1; green=$?

status=0
if [ "$red" -eq 0 ]; then
  echo "FAIL red: gate passed the known-bad fixture ($bad) — it cannot fail, so it guards nothing"
  status=1
else
  echo "OK   red: gate failed the known-bad fixture (exit $red)"
fi
if [ "$green" -ne 0 ]; then
  echo "FAIL green: gate rejected the known-good fixture ($good, exit $green)"
  status=1
else
  echo "OK   green: gate passed the known-good fixture"
fi
[ "$status" -eq 0 ] && echo "ACCEPTED: red/green proven — this gate may guard"
exit "$status"
