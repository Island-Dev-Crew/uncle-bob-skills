#!/usr/bin/env bash
# Known-DIRTY fixture for qa-bind-check.sh: identical gate, but its QA-SHA256 is
# the hash of an EARLIER revision of the QA procedure — the procedure moved and
# this gate did not. qa-bind-check.sh must reject it (non-zero exit).
# STORY: STORY-42
# QA-DOC: scripts/fixtures/qa-procedure.md
# QA-SHA256: 824ee0622c500d74ff2f10feda4b14f12c604fe47178a4b89087c22e84cde87c
set -euo pipefail

checkpoint_login_form_visible() {
  grep -q 'id="password"' "$1" || { echo "FAIL login form not visible" >&2; exit 1; }
}

checkpoint_wrong_password_rejected() {
  grep -q "Incorrect email or password" "$1" || { echo "FAIL no rejection message" >&2; exit 1; }
}

checkpoint_login_form_visible "${1:?usage: dirty-stale-binding.sh <rendered-page>}"
checkpoint_wrong_password_rejected "$1"
echo "PASS STORY-42"
