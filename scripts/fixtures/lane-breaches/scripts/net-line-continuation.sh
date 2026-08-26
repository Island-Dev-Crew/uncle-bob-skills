#!/usr/bin/env bash
# Exit: 0 always. A deliberate L1 breach: the shell joins the backslash-newline
# before interpreting bash's -c program.
bash -c \
  'curl https://example.invalid'
