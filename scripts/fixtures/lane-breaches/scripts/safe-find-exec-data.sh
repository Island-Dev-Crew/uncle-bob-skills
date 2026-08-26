#!/usr/bin/env bash
# Exit: 0 always. Green controls: command arguments named curl are data, and an
# unterminated find action is rejected before it can execute its apparent command.
find . -maxdepth 0 -exec echo curl https://example.invalid {} \;
find . -maxdepth 0 -execdir printf '%s\n' curl {} +
find . -maxdepth 0 -exec curl https://example.invalid {}
find . -maxdepth 0 -exec echo {} \; curl https://example.invalid
find . -maxdepth 0 -ok echo curl https://example.invalid {} \;
find . -maxdepth 0 -okdir printf '%s\n' curl {} \;
find . -maxdepth 0 -ok curl https://example.invalid {} +
find . -maxdepth 0 -okdir curl https://example.invalid {} +
:
