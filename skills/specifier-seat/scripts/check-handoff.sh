#!/usr/bin/env bash
# check-handoff.sh — mechanical gate for the specifier seat's two artifacts.
# Usage: check-handoff.sh <gherkin.feature> <qa-procedure.md>
# Exit 0 iff every check passes; each check can go red (a gate that cannot
# fail is not a gate). Judgment calls (concreteness, declarativeness,
# behavior coverage) stay advisory in SKILL.md — this script never claims them.
set -u

feature="${1:-}"
qa="${2:-}"
fails=0

ok()   { echo "OK   $1"; }
fail() { echo "FAIL $1"; fails=$((fails + 1)); }

if [ -z "$feature" ] || [ -z "$qa" ]; then
  echo "usage: check-handoff.sh <gherkin.feature> <qa-procedure.md>" >&2
  exit 2
fi

# --- Artifact 1: Gherkin acceptance spec ------------------------------------
if [ -f "$feature" ]; then
  ok "feature file exists ($feature)"
  if grep -qE '^[[:space:]]*Feature:' "$feature"; then
    ok "Feature: line present"
  else
    fail "Feature: line missing"
  fi
  if grep -qE '^[[:space:]]*Scenario( Outline)?:' "$feature"; then
    ok "at least one Scenario present"
  else
    fail "Scenario missing"
  fi
  for kw in Given When Then; do
    if grep -qE "^[[:space:]]*${kw} " "$feature"; then
      ok "${kw} step present"
    else
      fail "${kw} step missing"
    fi
  done
else
  fail "feature file missing ($feature)"
fi

# --- Artifact 2: human-viewpoint QA procedure --------------------------------
if [ -f "$qa" ]; then
  ok "QA procedure exists ($qa)"
  if grep -qiE 'you are a human' "$qa"; then
    ok "operator preamble present (you are a human ...)"
  else
    fail "operator preamble missing (must state 'you are a human')"
  fi
  steps=$(grep -cE '^[0-9]+\.' "$qa" || true)
  if [ "${steps:-0}" -ge 1 ]; then
    ok "numbered steps present (${steps})"
  else
    fail "numbered steps missing"
  fi
  if grep -qiE 'expected:' "$qa"; then
    ok "Expected: marker present"
  else
    fail "Expected: marker missing"
  fi
else
  fail "QA procedure missing ($qa)"
fi

# --- Verdict ------------------------------------------------------------------
if [ "$fails" -eq 0 ]; then
  echo "PASS — handoff pair meets the specifier contract"
  exit 0
fi
echo "FAIL — ${fails} check(s) red"
exit 1
