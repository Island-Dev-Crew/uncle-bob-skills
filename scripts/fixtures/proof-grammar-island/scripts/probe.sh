#!/usr/bin/env bash
# Fixture gate. Exits 1 on "dirty", 0 on anything else. Nothing else happens here.
set -u
[ "${1:-}" = "dirty" ] && exit 1
exit 0
