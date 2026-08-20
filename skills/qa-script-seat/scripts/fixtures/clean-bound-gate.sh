#!/usr/bin/env bash
# Known-CLEAN fixture for qa-bind-check.sh: a generated QA gate bound to the
# CURRENT QA procedure. qa-bind-check.sh must accept it (exit 0).
# STORY: STORY-42
# QA-DOC: scripts/fixtures/qa-procedure.md
# QA-SHA256: e4db3ca26474b84f9080cec5b75ebe5230cb814f2bf5971e6a7634e43eb3d0aa
set -euo pipefail

checkpoint_login_form_visible() {
  grep -q 'id="password"' "$1" || { echo "FAIL login form not visible" >&2; exit 1; }
}

checkpoint_wrong_password_rejected() {
  grep -q "Incorrect email or password" "$1" || { echo "FAIL no rejection message" >&2; exit 1; }
}

checkpoint_login_form_visible "${1:?usage: clean-bound-gate.sh <rendered-page>}"
checkpoint_wrong_password_rejected "$1"
echo "PASS STORY-42"
