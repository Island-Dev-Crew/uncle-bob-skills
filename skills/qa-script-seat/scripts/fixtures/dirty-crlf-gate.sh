#!/usr/bin/env bash
# Known-DIRTY CRLF fixture for qa-bind-check.sh: right binding, wrong line endings.
# Its headers carry a terminal CR and still bind, so this file gets PAST the binding
# check and dies at the syntax one, on the CR that follows the function's opening
# brace. `bash -n` is no line-ending check: it reds a CRLF `.sh` that has to close a
# function body, a `{ }` group, an `if`, a loop or a `case`, and passes one whose
# commands are a flat list. This file is the first shape. Reject it (exit 1), and let
# the message name `bash -n` — a "missing header" failure here would mean the CR
# tolerance broke instead.
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

checkpoint_login_form_visible "${1:?usage: dirty-crlf-gate.sh <rendered-page>}"
checkpoint_wrong_password_rejected "$1"
echo "PASS STORY-42"
