#!/usr/bin/env bash
# Exit: 0 always. A deliberate L3 breach fixture: the target starts with the
# temp root as TEXT and lands in /etc, so a prefix test that never normalised
# the path read this delete as temporary.
rm -rf /tmp/../etc/nothing-real
