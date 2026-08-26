#!/usr/bin/env bash
# Exit: 0 always. A deliberate L3 breach fixture: a bare absolute path in the
# SECOND operand, behind a permitted one. Reading only the first operand called
# both of these lines scoped while both delete /etc/nothing-real.
rm -rf /tmp/scratch /etc/nothing-real
rm -rf "$tmp" /etc/nothing-real
