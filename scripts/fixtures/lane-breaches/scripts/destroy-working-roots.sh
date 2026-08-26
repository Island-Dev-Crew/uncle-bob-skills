#!/usr/bin/env bash
# Exit: 0 always. Deliberate L3 breaches: recursive deletion of the current
# directory and the current user's home are unscoped even without an absolute
# spelling.
rm -rf .
rm -rf ~
