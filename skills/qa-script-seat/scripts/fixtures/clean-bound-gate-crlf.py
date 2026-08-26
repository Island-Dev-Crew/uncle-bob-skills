#!/usr/bin/env python3
# Known-CLEAN CRLF fixture for qa-bind-check.sh: the same binding as
# clean-bound-gate.sh, saved the way a generated script comes off a Windows editor.
# The headers are correct, so qa-bind-check.sh must accept it (exit 0) — a line
# ending is not a verdict. This twin is Python and not shell for a real reason: a
# CRLF .sh dies at `bash -n` wherever a brace group has to close (`foo() {\r` is a
# syntax error), and that red would mask the one this file is asking about. Python's
# tokenizer reads CRLF natively, so the CR here reaches the binding check alone. The
# shell half of the question is dirty-crlf-gate.sh, which binds and then goes red.
# STORY: STORY-42
# QA-DOC: scripts/fixtures/qa-procedure.md
# QA-SHA256: e4db3ca26474b84f9080cec5b75ebe5230cb814f2bf5971e6a7634e43eb3d0aa
import sys


def checkpoint_login_form_visible(page):
    if 'id="password"' not in page:
        sys.exit("FAIL login form not visible")


def checkpoint_wrong_password_rejected(page):
    if "Incorrect email or password" not in page:
        sys.exit("FAIL no rejection message")


with open(sys.argv[1], encoding="utf-8") as handle:
    rendered = handle.read()
checkpoint_login_form_visible(rendered)
checkpoint_wrong_password_rejected(rendered)
print("PASS STORY-42")
