#!/usr/bin/env bash
# KNOWN-DIRTY fixture for prove-gate.sh: a rubber stamp.
# It ignores its input and always consents. prove-gate.sh MUST reject it
# (non-zero) — a gate that cannot say no guards nothing.
exit 0
